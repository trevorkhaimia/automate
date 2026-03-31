import os
import re
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

class ClickIn(BaseModel):
    selector: str

class TypeIn(BaseModel):
    selector: str
    text: str

async def broadcast(data):
    dead = []
    for ws in clients:
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in clients:
            clients.remove(ws)

async def read_output(proc):
    while True:
        line = await asyncio.to_thread(proc.stdout.readline)
        if not line:
            break
        await broadcast({"type": "log", "text": line.strip()})

def _extract_url(text: str):
    m = re.search(r'(https?://\S+)', text)
    if m:
        return m.group(1)
    m = re.search(r'\bopen\s+([A-Za-z0-9.-]+\.[A-Za-z]{2,})(/\S*)?', text, re.I)
    if m:
        domain = m.group(1)
        path = m.group(2) or ""
        return f"https://{domain}{path}"
    return None

@app.get("/")
async def root():
    return {"ok": True, "service": "automate-backend"}

@app.websocket("/ws/events")
async def ws(ws: WebSocket):
    await ws.accept()
    clients.append(ws)
    try:
        while True:
            await ws.receive_text()
    except Exception:
        pass
    finally:
        if ws in clients:
            clients.remove(ws)

@app.post("/api/chat")
async def chat_api(m: Message):
    text = m.text.strip()
    lower = text.lower()

    if any(k in lower for k in ["open the browser", "open browser", "start browser", "launch browser"]):
        await start_firefox()
        return {"response": "Opened Firefox.", "action": "browser_started"}

    url = _extract_url(text)
    if url:
        await start_firefox()
        await open_url(url)
        return {"response": f"Opened {url}", "action": "browser_opened", "url": url}

    if lower.startswith("click "):
        selector = text[6:].strip()
        await click(selector)
        return {"response": f"Clicked {selector}", "action": "browser_click", "selector": selector}

    if lower.startswith("type "):
        parts = text[5:].split("::", 1)
        if len(parts) == 2:
            selector = parts[0].strip()
            value = parts[1].strip()
            await type_text(selector, value)
            return {"response": f"Typed into {selector}", "action": "browser_type", "selector": selector}
        return {"response": "Use: type <selector> :: <text>"}

    response = chat([
        {"role": "system", "content": "You can answer normally. Browser actions are handled by the app when the user asks to open browser, open a URL, click a selector, or type into a selector."},
        {"role": "user", "content": text},
    ])
    return {"response": response, "action": "chat"}

@app.post("/api/nullclaw/start")
async def start():
    global process
    if process and process.poll() is None:
        return {"ok": True, "message": "already running"}
    process = subprocess.Popen(
        NULLCLAW_CMD,
        cwd=NULLCLAW_CWD,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
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
    return {"ok": False, "error": "nullclaw is not running"}

@app.post("/api/browser/firefox/start")
async def fx_start():
    await start_firefox()
    return {"ok": True}

@app.post("/api/browser/firefox/open")
async def fx_open(u: Url):
    await start_firefox()
    await open_url(u.url)
    return {"ok": True}

@app.post("/api/browser/firefox/click")
async def fx_click(c: ClickIn):
    await click(c.selector)
    return {"ok": True}

@app.post("/api/browser/firefox/type")
async def fx_type(t: TypeIn):
    await type_text(t.selector, t.text)
    return {"ok": True}
