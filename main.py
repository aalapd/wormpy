# main.py

"""
Main entry point for the Wormpy web scraping tool.

This module handles command-line argument parsing, logging setup,
and orchestrates the web scraping process.
"""

import argparse
import asyncio
import time
from typing import Dict, Any, Tuple
from datetime import datetime
import os

from modules.utils.logger import configure_logging, get_logger
from modules.utils.sitemap_parser import get_all_urls
from modules.scraper import run_scrapers
from modules.utils.utils import format_output, set_filename, get_scraping_stats
from modules.utils.file_handler import save_output
from modules.utils.url_tracker import url_tracker
from modules.processors.url_processor import (
    get_domain,
    is_valid_url,
    normalize_url,
)

async def run_scraping(
    base_url: str,
    discovery_mode: bool,
    force_scrape_method: str,
    output_format: str,
) -> Tuple[Dict[str, Any], int]:
    """
    Run the web scraping process.

    Args:
        base_url (str): The base URL to start scraping from.
        discovery_mode (bool): Whether to scrape the entire site or just the base URL.
        force_scrape_method (str): Method to force for scraping ('req' or 'sel').
        output_format (str): The desired output format ('csv' or 'json').

    Returns:
        Tuple[Dict[str, Any], int]: A tuple containing the formatted output
        and the total number of URLs scraped.
    """
    logging = get_logger(__name__)
    normalized_base_url = normalize_url(base_url)
    
    # Initialize URL pool with base URL and sitemap URLs if in discovery mode
    await url_tracker.add_to_pool(normalized_base_url)
    sitemap_urls = []
    if discovery_mode:
        # Fetch sitemap
        sitemap_urls = get_all_urls(base_url)
        logging.info(f"Sitemap fetched. Total URLs in sitemap: {len(sitemap_urls)}")
        await url_tracker.add_bulk_to_pool(sitemap_urls)

    results = await run_scrapers(base_url, discovery_mode, force_scrape_method)

    formatted_output = format_output(results, output_format)
    total_urls_scraped = len(results)
    
    if output_format == 'json':
        formatted_output = {
            "sitemap_urls": list(sitemap_urls),
            "scraped_data": formatted_output
        }
    elif output_format == 'csv':
        sitemap_csv = [["Sitemap URL"]] + [[url] for url in sitemap_urls]
        formatted_output = sitemap_csv + [["Scraped Data"]] + formatted_output

    return formatted_output, total_urls_scraped

def main() -> None:
    """
    Main function to run the web scraper.
    """
    start_time = time.time()

    parser = argparse.ArgumentParser(description="Wormpy is a Python-based web scraping tool designed to extract content from websites efficiently and respectfully. It can parse sitemaps, crawl websites up to a specified depth, and handle various content types including HTML and PDF.")
    parser.add_argument("url", help="Base URL of the website to scrape")
    parser.add_argument(
        "--discovery",
        action="store_true",
        help="Enable discovery mode to scrape the entire website"
    )
    parser.add_argument(
        "--log",
        default="INFO",
        help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    parser.add_argument(
        "--savename",
        help="Specify the directory name to save output"
    )
    parser.add_argument(
        "--format",
        choices=['csv', 'json'],
        default='json',
        help="Specify the output format (csv or json)"
    )
    parser.add_argument(
        "--force",
        choices=['req', 'sel'],
        help="Force scraping with either requests or selenium"
    )
    args = parser.parse_args()
    
    base_url = normalize_url(args.url)

    # Create a dictionary with all configuration settings and flags
    config = {
        "url": base_url,
        "discovery_mode": args.discovery,
        "force_scrape_method": args.force,
        "log_level": args.log,
        "output_format": args.format,
        "save_directory": args.savename or get_domain(base_url),
    }

    # Set up logging
    now = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f"scrape_log_{now}.log"
    log_filepath = os.path.join('scrapes', config['save_directory'], log_filename)

    configure_logging(log_level=args.log, log_file=log_filepath, use_json=False)
    logging = get_logger(__name__)

    try:
        if not is_valid_url(base_url, base_url):
            raise ValueError("Invalid URL provided!")

        logging.info(f"Initial scraper config: {config}")

        logging.info("Starting web scraping process...")

        formatted_output, total_urls_scraped = asyncio.run(
            run_scraping(base_url, args.discovery, args.force, args.format)
        )

        filename = set_filename(args.format, now)
        folder_name = args.savename or get_domain(base_url)
        full_filepath = save_output(formatted_output, folder_name, filename, args.format)

        logging.info(f"Scraping complete. Saved output to {full_filepath}.")
        
        stats = asyncio.run(get_scraping_stats())
        logging.debug(f"Scraping statistics: {stats}")
        logging.info(f"Total URLs scraped: {total_urls_scraped}")

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
    finally:
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(f"Time taken: {elapsed_time:.2f} seconds.")

if __name__ == "__main__":
    main()