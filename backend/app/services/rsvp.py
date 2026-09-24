class RsvpService:
    def __init__(self, repo): self.repo = repo

    async def save(self, user_id, data):
        if data["event_id"] not in self.repo.events:
            raise ValueError("Event is not available in the current feed")
        return await self.repo.upsert_rsvp(user_id, data)

    async def dashboard(self, user_id):
        return await self.repo.user_rsvps(user_id)
