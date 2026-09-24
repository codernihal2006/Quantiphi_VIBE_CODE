from collections import defaultdict


class ConnectionManager:
    def __init__(self): self.connections = defaultdict(set)

    async def connect(self, websocket, event_id):
        await websocket.accept(); self.connections[event_id].add(websocket)

    def disconnect(self, websocket, event_id): self.connections[event_id].discard(websocket)

    async def broadcast(self, event_id, count):
        for websocket in list(self.connections[event_id]):
            try: await websocket.send_json({"eventId": event_id, "friendsAttending": count})
            except Exception: self.disconnect(websocket, event_id)
