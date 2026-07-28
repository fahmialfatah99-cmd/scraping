# Advanced Python Scraper

Proyek scraper Python tingkat lanjut yang tahan blokir (resilient), modular, dan terstruktur.

## 🚀 Fitur Unggulan

### Core Features
- **Async HTTP & Browser Automation** - Menggunakan httpx untuk HTTP/2 dan Playwright untuk browser automation
- **Anti-bot & Stealth Mechanisms** - User agent rotation, header spoofing, navigator injection, human behavior simulation
- **Structured Data Extraction** - Validasi data dengan Pydantic models
- **Robust Retry & Error Handling** - Exponential backoff retry logic dengan konfigurasi fleksibel
- **Rate Limiting** - Token bucket algorithm untuk mengontrol frekuensi request
- **Proxy Rotation** - Support multi-proxy dengan automatic failover
- **Concurrent Scraping** - Asyncio-based parallel execution dengan semaphore control

### URL Management
- **Priority Queue** - URL scheduling berdasarkan prioritas
- **Duplicate Detection** - Mencegah scraping URL yang sama berulang kali
- **Domain Politeness** - Rate limiting per domain
- **Depth Control** - Batasi kedalaman crawling

### Data Export
- **Multiple Formats** - JSON, CSV, SQLite, MongoDB
- **Compression** - Optional gzip compression untuk JSON
- **Batch Processing** - Efficient handling untuk large datasets
- **Auto Naming** - Timestamp-based file naming

## 📦 Instalasi

```bash
# Install dependencies
pip install -e .

# Install Playwright browsers
playwright install
```

## 🛠️ Penggunaan Dasar

### Simple Scraping

```python
import asyncio
from src.core import BaseScraper, ScraperConfig

async def main():
    config = ScraperConfig(
        base_url="https://example.com",
        max_retries=3,
        timeout=30,
        save_to_file=True,
    )
    
    async with BaseScraper(config) as scraper:
        results = await scraper.run(["https://example.com"])
        
        for item in results:
            print(f"URL: {item.url}")
            print(f"Title: {item.title}")
            print(f"Data: {item.data}")

asyncio.run(main())
```

### Advanced Configuration

```python
config = ScraperConfig(
    base_url="https://target-site.com",
    max_retries=5,              # Jumlah maksimal retry
    retry_delay=2.0,            # Delay awal antara retry
    timeout=60,                 # Timeout dalam detik
    rate_limit_delay=1.0,       # Delay antar request
    enable_proxy_rotation=True, # Aktifkan proxy rotation
    proxy_list=[               # Daftar proxy
        "http://proxy1:port",
        "http://proxy2:port",
    ],
    enable_stealth=True,        # Aktifkan stealth mode
    max_concurrent_requests=10, # Maksimal request paralel
    save_to_file=True,          # Simpan hasil ke file
    output_dir="output",        # Direktori output
    debug_mode=False,           # Mode debug
)
```

### Browser Automation (untuk JavaScript-heavy sites)

```python
async with BaseScraper(config) as scraper:
    # Gunakan browser untuk site yang membutuhkan JavaScript
    result = await scraper.scrape_url("https://dynamic-site.com", use_browser=True)
```

### Custom Parsing

Override method `parse_page` untuk custom extraction:

```python
class CustomScraper(BaseScraper):
    def parse_page(self, html: str, url: str) -> ScrapedItem:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        
        # Custom extraction logic
        product_name = soup.find("h1", class_="product-title").text
        price = soup.find("span", class_="price").text
        
        return ScrapedItem(
            url=url,
            title=product_name,
            data={"price": price, ...},
        )
```

### URL Manager

```python
from src.url_manager import URLManager

url_mgr = URLManager(
    max_urls=10000,
    max_depth=5,
    allowed_domains=["example.com"],
)

# Add URLs
await url_mgr.add_url("https://example.com/page1", priority=1)
await url_mgr.add_url("https://example.com/page2", depth=1)

# Get next URL
next_url = await url_mgr.get_next_url()

# Extract links from HTML
links = await url_mgr.extract_links(html, base_url)
```

### Data Exporter

```python
from src.exporter import DataExporter

exporter = DataExporter(output_dir="output")

# Export to specific format
await exporter.export_json(data, compress=True)
await exporter.export_csv(data, delimiter=',')
await exporter.export_sqlite(data, table_name="products")

# Export to all formats
results = await exporter.export_all(data, formats=['json', 'csv', 'sqlite'])
```

## 📁 Struktur Proyek

```
/workspace/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── core.py              # Main scraper logic
│   ├── url_manager.py       # URL management system
│   └── exporter.py          # Data export utilities
├── output/                   # Scraped data output
├── logs/                     # Log files
├── pyproject.toml           # Project configuration
└── README.md                # Documentation
```

## 🔒 Best Practices

1. **Respect robots.txt** - Selalu cek robots.txt target website
2. **Rate Limiting** - Jangan overload server target
3. **Error Handling** - Implementasikan retry logic yang robust
4. **Logging** - Gunakan logging untuk debugging dan monitoring
5. **Data Validation** - Validate semua data yang di-scrape

## 📊 Logging

Log disimpan otomatis di `logs/scraper_YYYY-MM-DD.log` dengan rotation harian.

## 🤝 Kontribusi

Silakan submit PR atau issue untuk improvement.

## 📄 License

MIT License
