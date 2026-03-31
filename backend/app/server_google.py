import os
import re
from fastapi import FastAPI
from dotenv import load_dotenv
from pydantic import BaseModel
from .browser_selenium import start_firefox, open_url, click, type_text
from .llm import chat

load_dotenv()
app = FastAPI()

class Message(BaseModel):
    text: str


def _extract_url(text: str):
    m = re.search(r'(https?://\S+)', text)
    if m:
        return m.group(1)
    m = re.search(r'\b(?:open|go to|goto|visit|navigate to)\s+([A-Za-z0-9.-]+\.[A-Za-z]{2,})(/\S*)?', text, re.I)
    if m:
        domain = m.group(1)
        path = m.group(2) or ""
        return f"https://{domain}{path}"
    return None

@app.get("/")
async def root():
    return {"ok": True, "service": "automate-backend-google"}

@app.post("/api/chat")
async def chat_api(m: Message):
    text = m.text.strip()
    lower = text.lower()

    url = _extract_url(text)
    if url:
        try:
            await start_firefox()
            await open_url(url)
            return {"response": f"Opened {url}", "action": "browser_opened", "url": url}
        except Exception as e:
            return {"response": f"Could not open {url}", "action": "browser_error", "url": url, "error": str(e)}

    if any(k in lower for k in ["open the browser", "open browser", "start browser", "launch browser"]):
        try:
            await start_firefox()
            return {"response": "Opened Firefox.", "action": "browser_started"}
        except Exception as e:
            return {"response": "Firefox launch failed.", "action": "browser_error", "error": str(e)}

    if lower.startswith("click "):
        selector = text[6:].strip()
        try:
            await click(selector)
            return {"response": f"Clicked {selector}", "action": "browser_click", "selector": selector}
        except Exception as e:
            return {"response": f"Could not click {selector}", "action": "browser_error", "error": str(e)}

    if lower.startswith("type "):
        parts = text[5:].split("::", 1)
        if len(parts) == 2:
            selector = parts[0].strip()
            value = parts[1].strip()
            try:
                await type_text(selector, value)
                return {"response": f"Typed into {selector}", "action": "browser_type", "selector": selector}
            except Exception as e:
                return {"response": f"Could not type into {selector}", "action": "browser_error", "error": str(e)}
        return {"response": "Use: type <selector> :: <text>"}

    response = chat([
        {"role": "system", "content": "You can answer normally. Browser actions are handled by the app when the user asks to open browser, go to a URL, click a selector, or type into a selector."},
        {"role": "user", "content": text},
    ])
    return {"response": response, "action": "chat"}
