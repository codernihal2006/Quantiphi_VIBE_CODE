from uuid import uuid4


class ShareService:
    def __init__(self, repo, frontend_url): self.repo, self.frontend_url = repo, frontend_url

    async def create(self, user_id, event_id):
        if not await self.repo.get_rsvp(user_id, event_id):
            raise PermissionError("RSVP before creating a share link")
        code = uuid4().hex[:8]
        await self.repo.create_share({"code": code, "event_id": event_id, "owner_user_id": user_id})
        return {"code": code, "url": f"{self.frontend_url}/s/{code}"}
