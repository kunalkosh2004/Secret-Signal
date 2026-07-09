from datetime import datetime

from pydantic import BaseModel


class ChatMessageResponse(BaseModel):
    id: int
    user_id: int
    username: str
    content: str
    created_at: datetime


class SendMessageRequest(BaseModel):
    content: str
