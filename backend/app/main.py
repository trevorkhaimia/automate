import os
import asyncio
import subprocess
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
from .browser import start_firefox, open_url, click, type_text

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

async def broadcast(data):
    for ws in clients:
        try:
            await ws.send_json(data)
        except:
            pass

async def read_output(proc):
    while True:
        line = await asyncio.to_thread(proc.stdout.readline)
        if not line:
            break
        await broadcast({"type": "log", "text": line.strip()})

@app.websocket("/ws/events")
async def ws(ws: WebSocket):
    await ws.accept()
    clients.append(ws)
    try:
        while True:
            await ws.receive_text()
    except:
        clients.remove(ws)

@app.post("/api/nullclaw/start")
async def start():
    global process
    if process and process.poll() is None:
        return {"ok": True}
    process = subprocess.Popen(NULLCLAW_CMD, cwd=NULLCLAW_CWD, stdout=subprocess.PIPE, stdin=subprocess.PIPE, text=True)
    asyncio.create_task(read_output(process))
    return {"ok": True}

@app.post("/api/nullclaw/stop")
async def stop():
    global process
    if process:
        process.terminate()
        process = None
    return {"ok": True}

@app.post("/api/nullclaw/message")
async def message(m: Message):
    if process and process.stdin:
        process.stdin.write(m.text + "\n")
        process.stdin.flush()
    return {"ok": True}

@app.post("/api/browser/firefox/start")
async def fx_start():
    await start_firefox()
    return {"ok": True}

@app.post("/api/browser/firefox/open")
async def fx_open(u: Url):
    await open_url(u.url)
    return {"ok": True}

@app.post("/api/browser/firefox/click")
async def fx_click(c: Click):
    await click(c.selector)
    return {"ok": True}

@app.post("/api/browser/firefox/type")
async def fx_type(t: Type):
    await type_text(t.selector, t.text)
    return {"ok": True}
