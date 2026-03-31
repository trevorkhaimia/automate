import os
import asyncio
import subprocess
from fastapi import FastAPI, WebSocket
from dotenv import load_dotenv
from pydantic import BaseModel
from .browser import start_firefox, open_url, click, type_text
from .llm import chat

load_dotenv()

app = FastAPI()

NULLCLAW_CMD = os.getenv("NULLCLAW_CMD", "python main.py").split()
NULLCLAW_CWD = os.getenv("NULLCLAW_CWD", "../nullclaw")

process = None
clients = []

class Message(BaseModel):
    text: str

class Url(BaseModel):
    url: str

class Click(BaseModel):
    selector: str

class Type(BaseModel):
    selector: str
    text: str

@app.post("/api/chat")
async def chat_api(m: Message):
    response = chat([
        {"role": "user", "content": m.text}
    ])
    return {"response": response}

@app.post("/api/browser/firefox/start")
async def fx_start():
    await start_firefox()
    return {"ok": True}

@app.post("/api/browser/firefox/open")
async def fx_open(u: Url):
    await open_url(u.url)
    return {"ok": True}