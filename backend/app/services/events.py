from app.models.schemas import Event


class EventService:
    def __init__(self, ticketmaster, repo):
        self.ticketmaster, self.repo = ticketmaster, repo

    async def list_events(self, city, user_id, from_date=None, to_date=None):
        raw = await self.ticketmaster.search(city, from_date, to_date)
        output = []
        for item in raw:
            self.repo.events[item["id"]] = item
            rsvp = await self.repo.get_rsvp(user_id, item["id"])
            output.append(Event(**item, friends_attending=await self.repo.friends_count(item["id"]), user_status=rsvp["status"] if rsvp else None))
        return output

    async def calendar(self, city, user_id, month):
        events = await self.list_events(city, user_id)
        return {event.date: sum(1 for item in events if item.date == event.date) for event in events if event.date.startswith(month)}
