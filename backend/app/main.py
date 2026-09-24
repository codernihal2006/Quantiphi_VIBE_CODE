from fastapi import FastAPI, Header, HTTPException, Query, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from uuid import uuid4
from app.core.config import get_settings
from app.models.schemas import UserCreate, RsvpRequest, ReminderUpdate
from app.repositories.memory import MemoryRepository
from app.db.mongo import MongoRepository
from app.services.ticketmaster import TicketmasterService
from app.services.events import EventService
from app.services.rsvp import RsvpService
from app.services.share import ShareService
from app.ws.manager import ConnectionManager

settings = get_settings()
repo = MongoRepository(settings.mongo_uri, settings.mongo_db) if settings.mongo_uri else MemoryRepository()
ticketmaster = TicketmasterService(settings.ticketmaster_api_key)
events = EventService(ticketmaster, repo)
rsvps = RsvpService(repo)
shares = ShareService(repo, settings.frontend_url)
ws_manager = ConnectionManager()
app = FastAPI(title="Evently API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_url, "http://localhost:5173"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True)


async def current_user(x_user_id: str | None):
    if not x_user_id or not await repo.find_user(x_user_id): raise HTTPException(401, "Create a profile first")
    return x_user_id


@app.get("/api/health")
async def health():
    if settings.mongo_uri:
        try:
            await repo.ping()
            mongo = "connected"
        except Exception:
            mongo = "unavailable"
    else:
        mongo = "memory"
    return {"ok": mongo != "unavailable", "mongo": mongo, "demoMode": not bool(settings.ticketmaster_api_key)}


@app.on_event("startup")
async def startup():
    if settings.mongo_uri:
        await repo.ensure_indexes()


@app.post("/api/users")
async def create_user(payload: UserCreate): return await repo.create_user(payload.model_dump())


@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    user = await repo.find_user(user_id)
    if not user: raise HTTPException(404, "User not found")
    return user


@app.get("/api/events")
async def list_events(city: str = Query(settings.default_city), from_date: str | None = Query(None, alias="from"), to_date: str | None = Query(None, alias="to"), x_user_id: str | None = Header(None)):
    return await events.list_events(city, await current_user(x_user_id), from_date, to_date)


@app.get("/api/events/calendar")
async def calendar(month: str, city: str = settings.default_city, x_user_id: str | None = Header(None)):
    return await events.calendar(city, await current_user(x_user_id), month)


@app.post("/api/rsvp")
async def save_rsvp(payload: RsvpRequest, x_user_id: str | None = Header(None)):
    try: return await rsvps.save(await current_user(x_user_id), payload.model_dump())
    except ValueError as exc: raise HTTPException(400, str(exc))


@app.delete("/api/rsvp/{event_id}")
async def delete_rsvp(event_id: str, x_user_id: str | None = Header(None)):
    await current_user(x_user_id); return {"deleted": bool(await repo.delete_rsvp(x_user_id, event_id))}


@app.patch("/api/rsvp/{event_id}/reminder")
async def update_reminder(event_id: str, payload: ReminderUpdate, x_user_id: str | None = Header(None)):
    user_id = await current_user(x_user_id); record = await repo.get_rsvp(user_id, event_id)
    if not record: raise HTTPException(404, "RSVP not found")
    record.update({"reminder_enabled": payload.enabled, "minutes_before": payload.minutes_before}); return record


@app.get("/api/rsvp/dashboard")
async def dashboard(x_user_id: str | None = Header(None)): return await rsvps.dashboard(await current_user(x_user_id))


@app.post("/api/share")
async def create_share(event_id: str, x_user_id: str | None = Header(None)):
    try: return await shares.create(await current_user(x_user_id), event_id)
    except PermissionError as exc: raise HTTPException(403, str(exc))


@app.get("/s/{code}")
async def follow_share(code: str, request: Request, response: Response):
    share = await repo.get_share(code)
    if not share: raise HTTPException(404, "Share link not found")
    visitor_id = request.cookies.get("visitor_id") or uuid4().hex
    updated = await repo.record_visit(code, visitor_id)
    await ws_manager.broadcast(updated["event_id"], await repo.friends_count(updated["event_id"]))
    redirect = RedirectResponse(f"{settings.frontend_url}/?event={updated['event_id']}&ref={code}", status_code=302)
    if not request.cookies.get("visitor_id"): redirect.set_cookie("visitor_id", visitor_id, max_age=60*60*24*365, httponly=True, samesite="lax")
    return redirect


@app.websocket("/ws/events/{event_id}")
async def event_socket(websocket: WebSocket, event_id: str):
    await ws_manager.connect(websocket, event_id)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect: ws_manager.disconnect(websocket, event_id)
