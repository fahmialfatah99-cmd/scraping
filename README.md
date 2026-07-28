# 🚀 Advanced Python Scraper

Sistem web scraping production-grade yang canggih, cepat, dan tahan banting. Dibangun dengan arsitektur async modern untuk menangani skala besar dengan fitur anti-bot terintegrasi. Menggunakan `httpx` dan `BeautifulSoup` untuk scraping yang ringan tanpa dependensi browser.

## ✨ Fitur Unggulan

### 🛡️ Anti-Deteksi & Keamanan
- **User Agent Rotation**: Rotasi otomatis menggunakan database user-agent terbaru
- **Header Spoofing**: Simulasi header browser asli secara lengkap
- **Proxy Rotation**: Failover otomatis jika proxy gagal
- **Rate Limiting**: Token bucket algorithm untuk menghormati server target
- **Fingerprint Randomization**: Session fingerprint unik untuk setiap scraping session

### ⚡ Performa Tinggi
- **Async HTTP**: Menggunakan `httpx` dengan dukungan HTTP/2 untuk kecepatan maksimal
- **Lightweight**: Tidak memerlukan instalasi browser atau dependencies berat
- **Concurrent Scraping**: Eksekusi paralel dengan kontrol semaphore
- **Intelligent Retry**: Exponential backoff dengan jitter
- **Priority Queue**: URL scheduling berbasis prioritas

### 📊 Manajemen Data
- **Multi-format Export**: JSON, CSV, SQLite
- **Compression**: Opsional gzip untuk menghemat storage
- **Validation**: Pydantic models untuk memastikan integritas data
- **Batch Processing**: Efisien untuk dataset besar

### 🕷️ Cerdas & Adaptif
- **Link Extraction**: Otomatis menemukan dan mengantrikan link baru
- **Domain Politeness**: Rate limiting per domain untuk etika crawling
- **Depth Control**: Membatasi kedalaman crawling
- **Duplicate Detection**: Mencegah scraping URL yang sama dua kali

---

## 📋 Prasyarat Sistem

| Komponen | Versi Minimum | Rekomendasi |
|----------|---------------|-------------|
| Python | 3.9 | 3.10+ |
| RAM | 1 GB | 2 GB+ |
| Storage | 200 MB | 500 MB+ |
| OS | Linux/macOS/Windows | Linux (Ubuntu 20.04+) |

---

## 🛠️ Panduan Instalasi

### 🐧 Linux (Ubuntu/Debian/Kali)

```bash
# 1. Update sistem
sudo apt update && sudo apt upgrade -y

# 2. Install dependencies sistem
sudo apt install -y python3 python3-pip python3-venv git curl wget

# 3. Setup project
mkdir -p ~/advanced-scraper && cd ~/advanced-scraper
python3 -m venv venv
source venv/bin/activate

# 4. Install library Python
pip install --upgrade pip
pip install httpx beautifulsoup4 pydantic loguru aiosqlite fake-useragent
```

### 🍎 macOS (Intel & Apple Silicon)

```bash
# 1. Install via Homebrew (jika belum ada)
# /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install python git

# 2. Setup project
mkdir -p ~/advanced-scraper && cd ~/advanced-scraper
python3 -m venv venv
source venv/bin/activate

# 3. Install library
pip install --upgrade pip
pip install httpx beautifulsoup4 pydantic loguru aiosqlite fake-useragent
```

### 🪟 Windows (10/11)

**Langkah Manual:**
1. Download & Install Python dari [python.org](https://www.python.org/downloads/)
   - ⚠️ **PENTING**: Centang **"Add Python to PATH"** saat instalasi.
2. Buka PowerShell sebagai Administrator:
   ```powershell
   # Cek instalasi
   python --version
   
   # Buat folder & venv
   mkdir advanced-scraper
   cd advanced-scraper
   python -m venv venv
   
   # Aktifkan venv (jika error policy, jalankan perintah Set-ExecutionPolicy di bawah dulu)
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   .\venv\Scripts\Activate.ps1
   
   # Install libraries
   python -m pip install --upgrade pip
   pip install httpx beautifulsoup4 pydantic loguru aiosqlite fake-useragent
   ```

---

## 🚀 Cara Penggunaan

### Struktur Folder Rekomendasi
```text
advanced-scraper/
├── venv/                  # Virtual environment
├── src/                   # Source code
│   ├── core/              # Scraper engine
│   ├── exporters/         # Modul export data
│   ├── managers/          # URL & Proxy manager
│   └── utils/             # Helper functions
├── data/                  # Hasil scraping
│   ├── json/
│   ├── csv/
│   └── db/
├── logs/                  # Log file
├── config.py              # Konfigurasi global
├── main.py                # Entry point
└── requirements.txt       # Dependencies
```

### Contoh Dasar (CLI)

```bash
# Aktifkan environment
source venv/bin/activate  # Linux/Mac
# atau
.\venv\Scripts\Activate.ps1 # Windows

# Jalankan scraper sederhana
python main.py --url "https://example.com" --format json --depth 1

# Scraping dengan proxy dan concurrency tinggi
python main.py --url "https://target-site.com" \
    --proxy "http://user:pass@proxy-ip:port" \
    --workers 10 \
    --max-depth 3 \
    --output data/results

# Gunakan mode browser (untuk situs JS berat) - *Tidak tersedia, gunakan httpx+BeautifulSoup*
```

### Contoh Kode (Python API)

```python
import asyncio
from src.core.scraper import AdvancedScraper
from src.config import ScraperConfig

async def main():
    # Konfigurasi
    config = ScraperConfig(
        base_url="https://quotes.toscrape.com",
        max_depth=2,
        max_workers=5,
        use_proxy=False,
        delay_range=(1.0, 3.0),
        user_agent_rotation=True
    )

    # Inisialisasi
    scraper = AdvancedScraper(config)

    # Jalankan
    results = await scraper.run()
    
    print(f"✅ Selesai! {len(results)} data diambil.")
    
    # Export manual jika perlu
    await scraper.exporter.save_to_json(results, "hasil_scraping.json")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🧪 Verifikasi Instalasi

Buat file `test_install.py` untuk memastikan semua komponen berjalan:

```python
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
```

Jalankan: `python test_install.py`

---

## ⚙️ Konfigurasi Lanjutan

Edit `config.py` untuk menyesuaikan perilaku scraper:

```python
from pydantic import BaseModel
from typing import List, Optional

class ScraperConfig(BaseModel):
    # Target
    base_url: str
    allowed_domains: Optional[List[str]] = None
    
    # Performa
    max_workers: int = 5
    max_depth: int = 3
    timeout: int = 30
    
    # Anti-Bot
    user_agent_rotation: bool = True
    use_proxy: bool = False
    proxy_list: List[str] = []
    
    # Etika
    delay_range: tuple = (1.0, 3.0)  # (min, max) detik
    respect_robots_txt: bool = True
```

---

## 📄 Lisensi & Etika

Proyek ini dibuat untuk tujuan edukasi dan riset. 
- ✅ Selalu hormati `robots.txt` target.
- ✅ Jangan lakukan scraping yang membebani server target.
- ✅ Patuhi hukum dan regulasi setempat terkait data.
- ❌ Dilarang digunakan untuk aktivitas ilegal atau pencurian data sensitif.

---

## 🤝 Kontribusi

Kontribusi sangat diterima! Silakan buat Pull Request atau buka Issue untuk laporan bug/fitur baru.

1. Fork repository
2. Buat branch fitur (`git checkout -b fitur-keren`)
3. Commit perubahan (`git commit -m 'Menambah fitur keren'`)
4. Push ke branch (`git push origin fitur-keren`)
5. Buka Pull Request

---

## 📞 Dukungan

Jika mengalami masalah, pastikan:
1. Python versi sesuai (3.9+)
2. Semua dependencies terinstall (`pip install -r requirements.txt`)
3. Firewall/Antivirus tidak memblokir koneksi

Untuk pertanyaan lebih lanjut, silakan buka tab **Issues**.

---

*Dibuat dengan ❤️ menggunakan Python Async, httpx & BeautifulSoup*
