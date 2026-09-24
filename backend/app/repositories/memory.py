from collections import defaultdict
from datetime import datetime, timezone
from uuid import uuid4


def now():
    return datetime.now(timezone.utc)


class MemoryRepository:
    def __init__(self):
        self.users = {}
        self.rsvps = {}
        self.shares = {}
        self.events = {}

    async def create_user(self, data):
        user = {"id": str(uuid4()), **data, "created_at": now()}
        self.users[user["id"]] = user
        return user

    async def find_user(self, user_id):
        return self.users.get(user_id)

    async def upsert_rsvp(self, user_id, data):
        key = (user_id, data["event_id"])
        record = {**data, "user_id": user_id, "created_at": now()}
        self.rsvps[key] = record
        return record

    async def delete_rsvp(self, user_id, event_id):
        return self.rsvps.pop((user_id, event_id), None)

    async def user_rsvps(self, user_id):
        return [r for (uid, _), r in self.rsvps.items() if uid == user_id]

    async def get_rsvp(self, user_id, event_id):
        return self.rsvps.get((user_id, event_id))

    async def create_share(self, data):
        self.shares[data["code"]] = {**data, "click_count": 0, "visitor_ids": []}
        return self.shares[data["code"]]

    async def get_share(self, code):
        return self.shares.get(code)

    async def record_visit(self, code, visitor_id):
        share = self.shares.get(code)
        if not share:
            return None
        if visitor_id not in share["visitor_ids"]:
            share["visitor_ids"].append(visitor_id)
            share["click_count"] += 1
        return share

    async def friends_count(self, event_id):
        visitors = set()
        for share in self.shares.values():
            if share["event_id"] == event_id:
                visitors.update(share["visitor_ids"])
        return len(visitors)

    async def all_share_visitors(self, event_id):
        return await self.friends_count(event_id)
