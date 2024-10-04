# File: modules/scraper.py

import asyncio
from typing import Dict, Any, Optional
from selenium.common.exceptions import WebDriverException
from .processors.url_processor import normalize_url, is_suspicious_url, get_domain
from .processors.content_processor import process_page
from .processors.selenium_processor import SeleniumDriver
from .utils.utils import is_image_content_type, AsyncRateLimiter
from .utils.url_tracker import url_tracker
from config import MAX_SIMULTANEOUS_SCRAPERS, MAX_URLS_TO_SCRAPE

from modules.utils.logger import get_logger
logging = get_logger(__name__)

class WebsiteScraper:
    """
    A class to scrape websites asynchronously using a shared URL pool.

    This class manages the scraping process for a given website, including
    URL discovery, content processing, and rate limiting.

    Attributes:
        base_url (str): The base URL of the website to scrape.
        scraper_id (int): Unique identifier for this scraper instance.
        discovery_mode (bool): Whether to scrape the entire site or just the base URL.
        force_scrape_method (Optional[str]): Method to force for scraping ('req' or 'sel').
        selenium_driver (Optional[SeleniumDriver]): Instance of SeleniumDriver for Selenium operations.
        rate_limiter (AsyncRateLimiter): Instance of the rate limiter.
    """

    def __init__(self, base_url: str, scraper_id: int, discovery_mode: bool, force_scrape_method: Optional[str] = None):
        self.base_url = base_url
        self.scraper_id = scraper_id
        self.discovery_mode = discovery_mode
        self.force_scrape_method = force_scrape_method
        self.selenium_driver: Optional[SeleniumDriver] = None
        self.rate_limiter = AsyncRateLimiter()

    def get_selenium_driver(self) -> SeleniumDriver:
        """
        Get or create a Selenium driver instance.

        Returns:
            SeleniumDriver: An instance of the Selenium driver.
        """
        if self.selenium_driver is None:
            self.selenium_driver = SeleniumDriver()
        return self.selenium_driver

    async def scrape(self) -> Dict[str, Any]:
        """
        Asynchronously scrape the website using the shared URL pool.

        This method manages the scraping process, including URL discovery,
        content processing, and error handling.

        Returns:
            Dict[str, Any]: A dictionary containing the scraping results.
        """
        logging.debug(f"Initializing scraper (ID: {self.scraper_id})")
        results: Dict[str, Any] = {}

        try:
            while True:
                url = await url_tracker.get_next_url()
                if url is None or (self.discovery_mode and len(results) >= MAX_URLS_TO_SCRAPE):
                    logging.debug(f"Scraper {self.scraper_id}: No more URLs to process or reached MAX_URLS_TO_SCRAPE.")
                    break

                normalized_url = normalize_url(url)
                
                if not normalized_url.startswith(self.base_url):
                    logging.debug(f"Scraper {self.scraper_id}: Skipping URL not starting with base URL: {normalized_url}")
                    continue

                if await url_tracker.is_visited(normalized_url):
                    logging.debug(f"Scraper {self.scraper_id}: Skipping already visited URL: {normalized_url}")
                    continue

                if is_suspicious_url(normalized_url):
                    if is_image_content_type(normalized_url):
                        logging.debug(f"Scraper {self.scraper_id}: Skipping image URL: {normalized_url}")
                        continue

                try:
                    logging.info(f"Scraper {self.scraper_id}: Attempting to process URL: {normalized_url}")
                    domain = get_domain(normalized_url)
                    await self.rate_limiter.wait(domain)
                    content, content_type, extracted_text, metadata, discovered_urls = await process_page(
                        self.scraper_id,
                        normalized_url, 
                        self.force_scrape_method, 
                        selenium_driver=self.get_selenium_driver(),
                    )
                    
                    if self.discovery_mode:
                        # Normalize all discovered URLs
                        all_discovered_urls = set(normalize_url(url) for url in discovered_urls)
                        
                        # Filter URLs for processing (only those starting with base_url)
                        urls_for_processing = {url for url in all_discovered_urls if url.startswith(self.base_url)}
                        
                        # Add new URLs to the shared pool
                        await url_tracker.add_bulk_to_pool(urls_for_processing)
                    
                    results[normalized_url] = {
                        'metadata': metadata,
                        'content': extracted_text,
                        'discovered_urls': sorted(list(discovered_urls)) if self.discovery_mode else [],
                    }
                    
                    await url_tracker.mark_visited(normalized_url)
                    logging.info(f"Scraper {self.scraper_id}: Successfully processed {normalized_url}")

                    if not self.discovery_mode:
                        break  # Stop after processing the first URL in non-discovery mode

                except WebDriverException as e:
                    error_message = f"Scraper {self.scraper_id}: Selenium error processing {normalized_url}: {str(e)}"
                    logging.error(error_message)
                    if self.selenium_driver:
                        self.selenium_driver.quit_selenium()
                    self.selenium_driver = None
                    await url_tracker.return_url_to_pool(normalized_url)

                except Exception as e:
                    error_message = f"Scraper {self.scraper_id}: Error processing {normalized_url}: {str(e)}"
                    logging.error(error_message)
                    results[normalized_url] = {'content': error_message}
                    await url_tracker.mark_visited(normalized_url)

        finally:
            if self.selenium_driver:
                self.selenium_driver.quit_selenium()
            logging.info(f"Scraper {self.scraper_id}: Scraper terminated.")

        return results

async def run_scrapers(base_url: str, discovery_mode: bool, force_scrape_method: Optional[str] = None) -> Dict[str, Any]:
    """
    Run scrapers concurrently using a shared URL pool.

    Args:
        discovery_mode (bool): Whether to scrape the entire site or just the base URL.
        force_scrape_method (Optional[str]): Method to force for scraping ('req' or 'sel').

    Returns:
        Dict[str, Any]: Collated results from all scrapers.
    """
    base_url = base_url
    if base_url is None:
        logging.error("No base URL found!")
        return {}

    if not discovery_mode:
        # Run a single scraper for the base URL
        scraper = WebsiteScraper(base_url, 1, discovery_mode, force_scrape_method)
        results = await scraper.scrape()
    else:
        # Create scrapers based on the number of URLs in the pool
        pool_size = await url_tracker.get_pool_size()
        num_scrapers = min(MAX_SIMULTANEOUS_SCRAPERS, max(1, pool_size))
        logging.info(f"Starting {MAX_SIMULTANEOUS_SCRAPERS} scrapers...")

        scrapers = [WebsiteScraper(base_url, i+1, discovery_mode, force_scrape_method) for i in range(num_scrapers)]
        results = await asyncio.gather(*(scraper.scrape() for scraper in scrapers))

    # Collate results
    collated_results = {}
    for result in results if isinstance(results, list) else [results]:
        collated_results.update(result)

    return collated_results