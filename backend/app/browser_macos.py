import os
from playwright.async_api import async_playwright

ctx = {"pw": None, "browser": None, "page": None}


def _mac_firefox_path():
    candidates = [
        "/Applications/Firefox.app/Contents/MacOS/firefox",
        "/Applications/Firefox Developer Edition.app/Contents/MacOS/firefox",
        os.path.expanduser("~/Applications/Firefox.app/Contents/MacOS/firefox"),
        os.path.expanduser("~/Applications/Firefox Developer Edition.app/Contents/MacOS/firefox"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


async def start_firefox():
    if ctx["browser"]:
        return

    pw = await async_playwright().start()
    executable_path = os.getenv("FIREFOX_EXECUTABLE_PATH") or _mac_firefox_path()

    launch_kwargs = {"headless": False}
    if executable_path:
        launch_kwargs["executable_path"] = executable_path

    browser = await pw.firefox.launch(**launch_kwargs)
    page = await browser.new_page()
    ctx.update({"pw": pw, "browser": browser, "page": page})


async def open_url(url: str):
    await start_firefox()
    await ctx["page"].goto(url)


async def click(selector: str):
    await ctx["page"].click(selector)


async def type_text(selector: str, text: str):
    await ctx["page"].fill(selector, text)
