import asyncio
import sys

async def check_systems():
    print(f"🐍 Python Version: {sys.version}")
    
    checks = [
        ("httpx", "import httpx"),
        ("playwright", "from playwright.async_api import async_playwright"),
        ("pydantic", "from pydantic import BaseModel"),
        ("beautifulsoup4", "from bs4 import BeautifulSoup"),
        ("aiosqlite", "import aiosqlite"),
    ]

    for name, cmd in checks:
        try:
            exec(cmd)
            print(f"✅ {name} OK")
        except Exception as e:
            print(f"❌ {name} GAGAL: {e}")

    # Tes Browser
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            await browser.close()
        print("✅ Browser Engine OK")
    except Exception as e:
        print(f"❌ Browser GAGAL: {e}")

if __name__ == "__main__":
    asyncio.run(check_systems())
