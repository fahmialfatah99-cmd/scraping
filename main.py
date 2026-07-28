"""
Advanced Python Scraper - Main Entry Point
Usage examples and CLI interface for the scraper.
"""
import asyncio
import argparse
from pathlib import Path
from loguru import logger
from src.core import BaseScraper, ScraperConfig

async def run_scraper(args):
    """Run the scraper with provided arguments."""
    config = ScraperConfig(
        base_url=args.url,
        max_retries=args.retries,
        timeout=args.timeout,
        rate_limit_delay=args.delay,
        enable_proxy_rotation=args.proxy is not None,
        proxy_list=[args.proxy] if args.proxy else [],
        max_concurrent_requests=args.workers,
        save_to_file=True,
        output_dir=args.output or "output",
    )
    
    scraper = BaseScraper(config)
    
    # Scrape the URL(s)
    urls = [args.url]
    if args.file:
        with open(args.file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    
    results = await scraper.run(urls)
    
    # Export results
    if results:
        output_path = Path(args.output or "output")
        output_path.mkdir(parents=True, exist_ok=True)
        
        if args.format == "json":
            output_file = output_path / f"scraped_data.json"
            await scraper.save_results(results, str(output_file))
            logger.success(f"Data saved to {output_file}")
        elif args.format == "csv":
            output_file = output_path / f"scraped_data.csv"
            await scraper.export_to_csv(results, str(output_file))
            logger.success(f"Data saved to {output_file}")
        elif args.format == "db":
            output_file = output_path / f"scraped_data.db"
            await scraper.export_to_sqlite(results, str(output_file))
            logger.success(f"Data saved to {output_file}")
    
    logger.info(f"Scraping completed! {len(results)} items collected.")
    return results

def main():
    parser = argparse.ArgumentParser(
        description="Advanced Python Scraper - Lightweight web scraping with httpx & BeautifulSoup"
    )
    
    parser.add_argument(
        "--url", "-u",
        type=str,
        required=True,
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
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_scraper(args))
    except KeyboardInterrupt:
        logger.warning("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise

if __name__ == "__main__":
    main()
