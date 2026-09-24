from datetime import date, timedelta
import httpx


DEMO_EVENTS = [
    {"id": "demo-jazz", "title": "Blue Note After Dark", "venue": "The Blue Room", "city": "New York", "date": str(date.today() + timedelta(days=2)), "time": "20:00", "category": "Music", "image_url": "https://images.unsplash.com/photo-1511192336575-5a79af67a629?auto=format&fit=crop&w=900&q=80", "description": "A late-night jazz set with a house trio and special guests."},
    {"id": "demo-design", "title": "Design Systems Social", "venue": "Pier 17 Studio", "city": "New York", "date": str(date.today() + timedelta(days=5)), "time": "18:30", "category": "Community", "image_url": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?auto=format&fit=crop&w=900&q=80", "description": "Meet designers and engineers shaping the next generation of products."},
    {"id": "demo-terrace", "title": "Rooftop Cinema Club", "venue": "Skyline Terrace", "city": "New York", "date": str(date.today() + timedelta(days=9)), "time": "21:00", "category": "Film", "image_url": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=900&q=80", "description": "A cult classic under the stars, with city views and local snacks."},
    {"id": "demo-run", "title": "Hudson Sunrise Run", "venue": "Riverside Park", "city": "New York", "date": str(date.today() + timedelta(days=12)), "time": "07:00", "category": "Wellness", "image_url": "https://images.unsplash.com/photo-1552674605-db6ffd4facb5?auto=format&fit=crop&w=900&q=80", "description": "A friendly five-kilometre run followed by coffee by the river."},
]


class TicketmasterService:
    def __init__(self, api_key=None):
        self.api_key = api_key

    async def search(self, city: str, from_date: str | None = None, to_date: str | None = None):
        if not self.api_key:
            return [e for e in DEMO_EVENTS if e["city"].lower() == city.lower() or city.lower() == "all"]
        params = {"apikey": self.api_key, "city": city, "size": 20, "sort": "date,asc"}
        if from_date: params["startDateTime"] = f"{from_date}T00:00:00Z"
        if to_date: params["endDateTime"] = f"{to_date}T23:59:59Z"
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get("https://app.ticketmaster.com/discovery/v2/events.json", params=params)
            response.raise_for_status()
            raw = response.json().get("_embedded", {}).get("events", [])
        return [self._normalize(e, city) for e in raw]

    def _normalize(self, event, city):
        start = event.get("dates", {}).get("start", {})
        venues = event.get("_embedded", {}).get("venues", [])
        return {"id": event["id"], "title": event.get("name", "Untitled event"), "venue": venues[0].get("name", "TBA") if venues else "TBA", "city": city, "date": start.get("localDate", ""), "time": start.get("localTime", "TBA"), "category": event.get("classifications", [{}])[0].get("segment", {}).get("name", "Event"), "image_url": (event.get("images") or [{}])[0].get("url", ""), "description": event.get("info") or "Discover something new in your city."}
