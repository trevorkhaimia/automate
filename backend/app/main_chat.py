from fastapi import APIRouter
from pydantic import BaseModel
from .llm import chat

router = APIRouter()

class Message(BaseModel):
    text: str

@router.post("/api/chat")
async def chat_api(m: Message):
    response = chat([
        {"role": "user", "content": m.text}
    ])
    return {"response": response}
