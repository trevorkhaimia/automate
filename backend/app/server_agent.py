import re
from fastapi import FastAPI
from dotenv import load_dotenv
from pydantic import BaseModel
from .browser_selenium import start_firefox, open_url, click, type_text, ctx
from .llm import chat

load_dotenv()
app = FastAPI()

class Message(BaseModel):
    text: str

COOKIE_SELECTORS = [
    'button:has-text("Accept")',
    'button:has-text("I agree")',
    'button:has-text("Agree")',
    'button:has-text("Allow all")',
    'button:has-text("Accept all")',
    '#onetrust-accept-btn-handler',
    '[aria-label*="accept" i]',
    '[title*="accept" i]',
    'button[id*="accept" i]',
]


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


def _extract_search(text: str):
    m = re.search(r'\b(?:search|google)\s+(?:for\s+)?(.+)', text, re.I)
    if m:
        return m.group(1).strip()
    return None


def _driver():
    return ctx.get("driver")


async def _dismiss_cookies():
    driver = _driver()
    if not driver:
        return False

    for selector in COOKIE_SELECTORS:
        try:
            if ':has-text(' in selector:
                continue
            el = driver.find_element("css selector", selector)
            el.click()
            return True
        except Exception:
            pass

    xpath_candidates = [
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]",
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'allow all')]",
        "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
    ]

    for xp in xpath_candidates:
        try:
            el = driver.find_element("xpath", xp)
            el.click()
            return True
        except Exception:
            pass

    return False


async def _ensure_browser():
    await start_firefox()
    return True


@app.get("/")
async def root():
    return {"ok": True, "service": "automate-agent"}


@app.post("/api/chat")
async def chat_api(m: Message):
    text = m.text.strip()
    lower = text.lower()

    try:
        if any(k in lower for k in ["open the browser", "open browser", "start browser", "launch browser"]):
            await _ensure_browser()
            return {"response": "Opened Firefox.", "action": "browser_started"}

        url = _extract_url(text)
        if url:
            await _ensure_browser()
            await open_url(url)
            dismissed = await _dismiss_cookies()
            return {
                "response": f"Opened {url}" + (" and dismissed a cookie banner." if dismissed else "."),
                "action": "browser_opened",
                "url": url,
                "cookie_banner_dismissed": dismissed,
            }

        search_query = _extract_search(text)
        if search_query:
            await _ensure_browser()
            q = search_query.replace(' ', '+')
            url = f"https://www.google.com/search?q={q}"
            await open_url(url)
            dismissed = await _dismiss_cookies()
            return {
                "response": f"Searched Google for {search_query}." + (" Dismissed a cookie banner." if dismissed else ""),
                "action": "browser_search",
                "query": search_query,
                "cookie_banner_dismissed": dismissed,
            }

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
            return {"response": "Use: type <selector> :: <text>", "action": "help"}

        response = chat([
            {"role": "system", "content": "You are a browser-enabled assistant. If the user asks a normal question, answer normally. If they ask for a browser task, prefer concise, action-oriented language."},
            {"role": "user", "content": text},
        ])
        return {"response": response, "action": "chat"}

    except Exception as e:
        return {"response": "The browser action failed.", "action": "browser_error", "error": str(e)}
