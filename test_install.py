import asyncio
import sys

async def check_systems():
    print(f"🐍 Python Version: {sys.version}")
    
    checks = [
        ("httpx", "import httpx"),
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

if __name__ == "__main__":
    asyncio.run(check_systems())
