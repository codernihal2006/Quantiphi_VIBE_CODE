from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


RsvpStatus = Literal["interested", "going"]


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=160)
    city: str = Field(default="New York", min_length=2, max_length=80)


class User(UserCreate):
    id: str
    created_at: datetime


class RsvpRequest(BaseModel):
    event_id: str
    status: RsvpStatus = "interested"
    reminder_enabled: bool = True
    minutes_before: int = Field(default=60, ge=5, le=10080)
    via_share_code: str | None = None


class ReminderUpdate(BaseModel):
    enabled: bool
    minutes_before: int = Field(default=60, ge=5, le=10080)


class Rsvp(BaseModel):
    event_id: str
    user_id: str
    status: RsvpStatus
    reminder_enabled: bool
    minutes_before: int
    created_at: datetime


class Event(BaseModel):
    id: str
    title: str
    venue: str
    city: str
    date: str
    time: str
    image_url: str
    category: str
    description: str
    friends_attending: int = 0
    user_status: RsvpStatus | None = None


class ShareResponse(BaseModel):
    code: str
    url: str
