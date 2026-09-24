from datetime import datetime, timezone
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument


def now():
    return datetime.now(timezone.utc)


class MongoRepository:
    """Mongo-backed implementation with the same small interface as MemoryRepository."""

    def __init__(self, uri: str, database: str):
        self.client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
        self.db = self.client[database]
        self.events = {}

    @staticmethod
    def _public(record):
        if record is not None:
            record.pop("_id", None)
        return record

    async def ensure_indexes(self):
        await self.db.rsvps.create_index([("user_id", 1), ("event_id", 1)], unique=True)
        await self.db.share_links.create_index("code", unique=True)
        await self.db.events_cache.create_index("expires_at", expireAfterSeconds=0)

    async def ping(self):
        await self.client.admin.command("ping")

    async def create_user(self, data):
        user = {"id": str(uuid4()), **data, "created_at": now()}
        await self.db.users.insert_one(user)
        return self._public(user)

    async def find_user(self, user_id):
        return await self.db.users.find_one({"id": user_id}, {"_id": 0})

    async def upsert_rsvp(self, user_id, data):
        key = {"user_id": user_id, "event_id": data["event_id"]}
        record = {**key, **data, "created_at": now()}
        await self.db.rsvps.replace_one(key, record, upsert=True)
        return record

    async def delete_rsvp(self, user_id, event_id):
        result = await self.db.rsvps.find_one_and_delete({"user_id": user_id, "event_id": event_id})
        return result

    async def user_rsvps(self, user_id):
        return [r async for r in self.db.rsvps.find({"user_id": user_id}, {"_id": 0})]

    async def get_rsvp(self, user_id, event_id):
        return await self.db.rsvps.find_one({"user_id": user_id, "event_id": event_id}, {"_id": 0})

    async def create_share(self, data):
        record = {**data, "click_count": 0, "visitor_ids": [], "created_at": now()}
        await self.db.share_links.insert_one(record)
        return self._public(record)

    async def get_share(self, code):
        return await self.db.share_links.find_one({"code": code}, {"_id": 0})

    async def record_visit(self, code, visitor_id):
        share = await self.db.share_links.find_one_and_update(
            {"code": code, "visitor_ids": {"$ne": visitor_id}},
            {"$addToSet": {"visitor_ids": visitor_id}, "$inc": {"click_count": 1}},
            return_document=ReturnDocument.AFTER,
            projection={"_id": 0},
        )
        return share or await self.get_share(code)

    async def friends_count(self, event_id):
        visitors = set()
        async for share in self.db.share_links.find({"event_id": event_id}, {"visitor_ids": 1}):
            visitors.update(share.get("visitor_ids", []))
        return len(visitors)
