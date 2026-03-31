from playwright.async_api import async_playwright

ctx = {"pw": None, "browser": None, "page": None}

async def start_firefox():
    if ctx["browser"]:
        return
    pw = await async_playwright().start()
    browser = await pw.firefox.launch(headless=False)
    page = await browser.new_page()
    ctx.update({"pw": pw, "browser": browser, "page": page})

async def open_url(url: str):
    await start_firefox()
    await ctx["page"].goto(url)

async def click(selector: str):
    await ctx["page"].click(selector)

async def type_text(selector: str, text: str):
    await ctx["page"].fill(selector, text)
