# main.py

"""
Main entry point for the Wormpy web scraping tool.

This module handles command-line argument parsing, logging setup,
and orchestrates the web scraping process.
"""

import argparse
import logging
import asyncio
import time
from typing import Dict, Any, Tuple

from config import MAX_SIMULTANEOUS_SCRAPERS
from modules.website_scraper import WebsiteScraper, run_init_scraper
from modules.utils import format_output, set_filename
from modules.file_handler import save_output
from modules.processors.url_processor import (
    get_domain,
    is_valid_url,
    normalize_url,
    url_matches_base
)

def setup_logging(log_level: str) -> None:
    """
    Set up logging configuration.

    Args:
        log_level (str): Desired logging level.

    Raises:
        ValueError: If an invalid log level is provided.
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

async def run_scraping(
    base_url: str,
    max_depth: int,
    force_scrape_method: str,
    output_format: str
) -> Tuple[Dict[str, Any], int]:
    """
    Run the web scraping process.

    Args:
        base_url (str): The base URL to start scraping from.
        max_depth (int): The maximum depth to crawl.
        force_scrape_method (str): Method to force for scraping ('req' or 'sel').
        output_format (str): The desired output format ('csv' or 'json').

    Returns:
        Tuple[Dict[str, Any], int]: A tuple containing the formatted output
        and the total number of URLs scraped.
    """
    normalized_base_url = normalize_url(base_url)
    initial_scraper_config = {
        'base_url': normalized_base_url,
        'max_depth': 0,
        'force_scrape_method': force_scrape_method
    }

    logging.info("Starting initial scraper for URL discovery.")
    initial_results = await run_init_scraper(initial_scraper_config)
    logging.info("Initial scraper finished. Processing results.")

    all_discovered_urls = set()
    for result in initial_results.values():
        all_discovered_urls.update(
            url for url in result.get('discovered_urls', [])
            if url_matches_base(url, normalized_base_url)
        )

    logging.info(f"Total URLs discovered on target URL: {len(all_discovered_urls)}")

    if max_depth > 0 and all_discovered_urls:
        url_batches = [
            list(all_discovered_urls)[i::MAX_SIMULTANEOUS_SCRAPERS]
            for i in range(MAX_SIMULTANEOUS_SCRAPERS)
        ]

        scrapers = []
        for i, batch in enumerate(url_batches):
            scraper = WebsiteScraper(
                normalized_base_url,
                max_depth,
                scraper_id=i+1,
                force_scrape_method=force_scrape_method
            )
            scraper.urls_to_process = [(url, 1) for url in batch]
            scrapers.append(scraper)
            logging.info(f"Scraper {i+1} initialized with {len(batch)} URLs")

        results = await asyncio.gather(*(scraper.scrape() for scraper in scrapers))

        collated_results = {}
        for result in results:
            collated_results.update(result)

        formatted_output = format_output(collated_results, output_format)
        total_urls_scraped = len(collated_results) + 1
    else:
        formatted_output = format_output(initial_results, output_format)
        total_urls_scraped = 1

    return formatted_output, total_urls_scraped

def main() -> None:
    """
    Main function to run the web scraper.
    """
    start_time = time.time()

    parser = argparse.ArgumentParser(description="Website Scraper")
    parser.add_argument("url", help="Base URL of the website to scrape")
    parser.add_argument(
        "depth",
        type=int,
        help="Maximum crawling depth; 0 returns content from a single page"
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

    try:
        setup_logging(args.log)

        if not is_valid_url(args.url, args.url):
            raise ValueError("Invalid URL provided.")

        if args.depth < 0:
            raise ValueError("Depth must be greater than or equal to zero.")

        formatted_output, total_urls_scraped = asyncio.run(
            run_scraping(args.url, args.depth, args.force, args.format)
        )

        filename = set_filename(args.format)
        folder_name = args.savename or get_domain(normalize_url(args.url))
        full_filepath = save_output(formatted_output, folder_name, filename, args.format)

        logging.info(f"Scraping complete. Saved output to {full_filepath}.")
        logging.info(f"Total URLs scraped: {total_urls_scraped}")

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
    finally:
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(f"Time taken: {elapsed_time:.2f} seconds.")

if __name__ == "__main__":
    main()