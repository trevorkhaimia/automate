import os
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

ctx = {"driver": None}


def _driver_path():
    candidates = [
        os.getenv("GECKODRIVER_PATH"),
        "/opt/homebrew/bin/geckodriver",
        "/usr/local/bin/geckodriver",
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def _firefox_binary():
    candidates = [
        os.getenv("FIREFOX_EXECUTABLE_PATH"),
        "/Applications/Firefox.app/Contents/MacOS/firefox",
        "/Applications/Firefox Developer Edition.app/Contents/MacOS/firefox",
        os.path.expanduser("~/Applications/Firefox.app/Contents/MacOS/firefox"),
        os.path.expanduser("~/Applications/Firefox Developer Edition.app/Contents/MacOS/firefox"),
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


async def start_firefox():
    if ctx["driver"]:
        return

    options = Options()
    options.binary_location = _firefox_binary()
    options.set_preference("remote.active-protocols", 1)

    service_path = _driver_path()
    service = Service(executable_path=service_path) if service_path else Service()
    driver = webdriver.Firefox(service=service, options=options)
    ctx["driver"] = driver


async def open_url(url: str):
    await start_firefox()
    ctx["driver"].get(url)


async def click(selector: str):
    await start_firefox()
    ctx["driver"].find_element(By.CSS_SELECTOR, selector).click()


async def type_text(selector: str, text: str):
    await start_firefox()
    el = ctx["driver"].find_element(By.CSS_SELECTOR, selector)
    el.clear()
    el.send_keys(text)
