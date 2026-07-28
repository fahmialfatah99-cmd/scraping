"""
Advanced Python Scraper - Main Entry Point
Features: CLI with interactive menu for easy web scraping using httpx & BeautifulSoup
"""
import asyncio
import argparse
from pathlib import Path
from loguru import logger
from src.core import BaseScraper, ScraperConfig
from src.url_manager import URLManager


async def run_scraper(url: str, output_dir: str = "output", format: str = "json", 
                      retries: int = 3, timeout: int = 30, delay: float = 0.5,
                      workers: int = 5, proxy: str = None):
    """Run the scraper with provided arguments."""
    config = ScraperConfig(
        base_url=url,
        max_retries=retries,
        timeout=timeout,
        rate_limit_delay=delay,
        enable_proxy_rotation=proxy is not None,
        proxy_list=[proxy] if proxy else [],
        max_concurrent_requests=workers,
        save_to_file=True,
        output_dir=output_dir,
    )
    
    scraper = BaseScraper(config)
    
    # Scrape the URL
    results = await scraper.run([url])
    
    # Export results
    if results:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            output_file = output_path / f"scraped_data.json"
            await scraper.save_results(results, str(output_file))
            logger.success(f"Data saved to {output_file}")
        elif format == "csv":
            output_file = output_path / f"scraped_data.csv"
            await scraper.export_to_csv(results, str(output_file))
            logger.success(f"Data saved to {output_file}")
        elif format == "db":
            output_file = output_path / f"scraped_data.db"
            await scraper.export_to_sqlite(results, str(output_file))
            logger.success(f"Data saved to {output_file}")
    
    logger.info(f"Scraping completed! {len(results)} items collected.")
    return results


def show_menu():
    """Display interactive menu."""
    print("\n" + "=" * 60)
    print("🚀 ADVANCED PYTHON SCRAPER - Menu Interaktif")
    print("=" * 60)
    print("1. 🕷️  Scraping URL Tunggal")
    print("2. 📋  Scraping Multiple URLs dari File")
    print("3. 📊  Lihat Riwayat Scraping (Output Files)")
    print("4. 🗑️  Hapus Semua Output Files")
    print("5. ℹ️   Info & Bantuan")
    print("0. 🚪  Keluar")
    print("=" * 60)


async def handle_single_scrape():
    """Handle single URL scraping from menu."""
    print("\n--- Scraping URL Tunggal ---")
    url = input("Masukkan URL yang akan di-scrape: ").strip()
    
    if not url:
        logger.error("URL tidak boleh kosong!")
        return
    
    print("\nPilihan format output:")
    print("1. JSON (default)")
    print("2. CSV")
    print("3. SQLite Database")
    
    format_choice = input("Pilih format [1-3] (Enter untuk JSON): ").strip()
    format_map = {"1": "json", "2": "csv", "3": "db"}
    output_format = format_map.get(format_choice, "json")
    
    output_dir = input("Nama folder output (Enter untuk 'output'): ").strip() or "output"
    
    try:
        retries = int(input("Jumlah maksimal retry (Enter untuk 3): ").strip() or "3")
        timeout = int(input("Timeout dalam detik (Enter untuk 30): ").strip() or "30")
        delay = float(input("Delay antar request dalam detik (Enter untuk 0.5): ").strip() or "0.5")
        workers = int(input("Jumlah worker concurrent (Enter untuk 5): ").strip() or "5")
    except ValueError:
        logger.error("Input tidak valid, menggunakan nilai default")
        retries, timeout, delay, workers = 3, 30, 0.5, 5
    
    proxy = input("Proxy URL (kosongkan jika tidak pakai): ").strip() or None
    
    logger.info(f"Memulai scraping: {url}")
    await run_scraper(
        url=url,
        output_dir=output_dir,
        format=output_format,
        retries=retries,
        timeout=timeout,
        delay=delay,
        workers=workers,
        proxy=proxy
    )


async def handle_file_scrape():
    """Handle multiple URL scraping from file."""
    print("\n--- Scraping Multiple URLs dari File ---")
    file_path = input("Masukkan path file berisi URLs (satu URL per baris): ").strip()
    
    if not file_path:
        logger.error("Path file tidak boleh kosong!")
        return
    
    if not Path(file_path).exists():
        logger.error(f"File tidak ditemukan: {file_path}")
        return
    
    output_dir = input("Nama folder output (Enter untuk 'output'): ").strip() or "output"
    output_format = input("Format output [json/csv/db] (Enter untuk json): ").strip() or "json"
    
    try:
        workers = int(input("Jumlah worker concurrent (Enter untuk 5): ").strip() or "5")
    except ValueError:
        workers = 5
    
    # Read URLs from file
    with open(file_path, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    if not urls:
        logger.error("Tidak ada URL dalam file!")
        return
    
    logger.info(f"Ditemukan {len(urls)} URLs untuk di-scrape")
    
    config = ScraperConfig(
        base_url=urls[0] if urls else "",
        max_retries=3,
        timeout=30,
        rate_limit_delay=0.5,
        max_concurrent_requests=workers,
        save_to_file=True,
        output_dir=output_dir,
    )
    
    scraper = BaseScraper(config)
    results = await scraper.run(urls)
    
    if results:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if output_format == "json":
            output_file = output_path / f"scraped_data.json"
            await scraper.save_results(results, str(output_file))
        elif output_format == "csv":
            output_file = output_path / f"scraped_data.csv"
            await scraper.export_to_csv(results, str(output_file))
        elif output_format == "db":
            output_file = output_path / f"scraped_data.db"
            await scraper.export_to_sqlite(results, str(output_file))
        
        logger.success(f"Data saved to {output_file}")
    
    logger.info(f"Scraping selesai! {len(results)} items berhasil dikumpulkan.")


def show_history():
    """Show scraping history (output files)."""
    print("\n--- Riwayat Scraping ---")
    output_dir = Path("output")
    
    if not output_dir.exists():
        print("Belum ada file output.")
        return
    
    files = list(output_dir.glob("*"))
    if not files:
        print("Folder output kosong.")
        return
    
    print(f"\nDitemukan {len(files)} file di folder 'output':\n")
    for i, file in enumerate(files, 1):
        size = file.stat().st_size
        size_str = f"{size/1024:.2f} KB" if size > 1024 else f"{size} bytes"
        print(f"  {i}. {file.name} ({size_str})")
    
    print()


def clear_output():
    """Clear all output files."""
    print("\n--- Hapus Output Files ---")
    confirm = input("Apakah Anda yakin ingin menghapus semua file output? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("Batal menghapus.")
        return
    
    output_dir = Path("output")
    if not output_dir.exists():
        print("Folder output tidak ditemukan.")
        return
    
    count = 0
    for file in output_dir.glob("*"):
        if file.is_file():
            file.unlink()
            count += 1
    
    print(f"Berhasil menghapus {count} file.")


def show_info():
    """Show help and information."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║         ADVANCED PYTHON SCRAPER - Informasi              ║
╠═══════════════════════════════════════════════════════════╣
║  Alat web scraping modern menggunakan:                   ║
║  • httpx - HTTP client async yang cepat                  ║
║  • BeautifulSoup - Parser HTML yang ringan               ║
║                                                           ║
║  Fitur Utama:                                            ║
║  ✓ Anti-deteksi dengan rotasi User-Agent                 ║
║  ✓ Rate limiting otomatis                                ║
║  ✓ Retry dengan exponential backoff                      ║
║  ✓ Support proxy rotation                                ║
║  ✓ Multi-format export (JSON, CSV, SQLite)               ║
║  ✓ Concurrent scraping                                   ║
║                                                           ║
║  Cara Menggunakan:                                        ║
║  1. Pilih menu untuk scraping URL tunggal atau file      ║
║  2. Ikuti petunjuk untuk memasukkan parameter            ║
║  3. Hasil scraping disimpan di folder 'output'           ║
║                                                           ║
║  Mode CLI Langsung (tanpa menu):                         ║
║  python main.py -u https://example.com -f json           ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
""")


async def interactive_menu():
    """Main interactive menu loop."""
    while True:
        show_menu()
        choice = input("Pilih menu [0-5]: ").strip()
        
        if choice == "1":
            await handle_single_scrape()
        elif choice == "2":
            await handle_file_scrape()
        elif choice == "3":
            show_history()
        elif choice == "4":
            clear_output()
        elif choice == "5":
            show_info()
        elif choice == "0":
            print("\nTerima kasih telah menggunakan Advanced Python Scraper!")
            print("See you next time! 👋\n")
            break
        else:
            print("\n⚠️  Pilihan tidak valid. Silakan pilih 0-5.")
        
        # Wait for user to continue
        if choice != "0":
            input("\nTekan Enter untuk melanjutkan...")


def main():
    parser = argparse.ArgumentParser(
        description="Advanced Python Scraper - Lightweight web scraping with httpx & BeautifulSoup"
    )
    
    parser.add_argument(
        "--url", "-u",
        type=str,
        help="URL to scrape (e.g., https://example.com)"
    )
    parser.add_argument(
        "--format", "-f",
        type=str,
        choices=["json", "csv", "db"],
        default="json",
        help="Output format (default: json)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="output",
        help="Output directory (default: output)"
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=5,
        help="Number of concurrent workers (default: 5)"
    )
    parser.add_argument(
        "--retries", "-r",
        type=int,
        default=3,
        help="Max retries per URL (default: 3)"
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)"
    )
    parser.add_argument(
        "--delay", "-d",
        type=float,
        default=0.5,
        help="Rate limit delay between requests (default: 0.5s)"
    )
    parser.add_argument(
        "--proxy", "-p",
        type=str,
        default=None,
        help="Proxy URL (e.g., http://user:pass@ip:port)"
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="File containing list of URLs to scrape (one per line)"
    )
    parser.add_argument(
        "--menu", "-m",
        action="store_true",
        help="Run interactive menu mode"
    )
    
    args = parser.parse_args()
    
    # If --menu flag is set or no URL provided, run interactive menu
    if args.menu or not args.url:
        try:
            asyncio.run(interactive_menu())
        except KeyboardInterrupt:
            logger.warning("\nProgram interrupted by user")
    else:
        # Run in CLI mode with provided arguments
        try:
            asyncio.run(run_scraper(
                url=args.url,
                output_dir=args.output,
                format=args.format,
                retries=args.retries,
                timeout=args.timeout,
                delay=args.delay,
                workers=args.workers,
                proxy=args.proxy
            ))
        except KeyboardInterrupt:
            logger.warning("Scraping interrupted by user")
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raise


if __name__ == "__main__":
    main()
