from pydantic import BaseModel
import uuid
from datetime import datetime
from fastapi_users import schemas
from fastapi import Form

class UserRead(schemas.BaseUser[uuid.UUID]):
    username: str

class UserCreate(schemas.BaseUserCreate):
    username: str

class UserUpdate(schemas.BaseUserUpdate):
    username: str | None = None

class TweetPostRequest(BaseModel):
    title: str = Form('Title')
    content: str

class TweetResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    content: str
    created_at: datetime
    email: str

class TweetPatchRequest(BaseModel):
    title: str | None = None
    content: str | None = None

