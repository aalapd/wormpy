# File: modules/scraper.py

import asyncio
from selenium.common.exceptions import WebDriverException
from .processors.url_processor import normalize_url, is_suspicious_url, get_domain
from .processors.content_processor import process_page
from .processors.selenium_processor import SeleniumDriver
from .utils.utils import is_image_content_type, AsyncRateLimiter
from .utils.url_tracker import url_tracker

from modules.utils.logger import get_logger
logger = get_logger(__name__)

class WebsiteScraper:
    """
    A class to scrape websites asynchronously.

    This class manages the scraping process for a given website, including
    URL discovery, content processing, and rate limiting.

    Attributes:
        base_url (str): The base URL of the website to scrape.
        max_depth (int): The maximum depth to crawl.
        scraper_id (int): Unique identifier for this scraper instance.
        force_scrape_method (str): Method to force for scraping ('req' or 'sel').
        selenium_driver (SeleniumDriver): Instance of SeleniumDriver for Selenium operations.
        rate_limiter (AsyncRateLimiter): Instance of the rate limiter.
        all_discovered_urls (set): Set of all discovered URLs.
        processed_urls (set): Set of processed URLs.
        error_urls (set): Set of URLs that resulted in errors.
        urls_to_process (list): List of URLs to process, with their depths.
        results (dict): Dictionary to store scraping results.
    """

    def __init__(self, base_url, max_depth, force_scrape_method=None, scraper_id=0):
        self.base_url = base_url
        self.max_depth = max_depth
        self.force_scrape_method = force_scrape_method
        self.scraper_id = scraper_id
        self.selenium_driver = None
        self.rate_limiter = AsyncRateLimiter()
        self.all_discovered_urls = set()
        self.processed_urls = set()
        self.error_urls = set()
        self.urls_to_process = [(base_url, 0)]  # (url, depth)
        self.results = {}
    
    def get_selenium_driver(self):
        if self.selenium_driver is None:
            self.selenium_driver = SeleniumDriver()
        return self.selenium_driver

    async def scrape(self):
        """
        Asynchronously scrape the website.

        This method manages the scraping process, including URL discovery,
        content processing, and error handling.

        Returns:
            dict: A dictionary containing the scraping results.
        """
        logger.info("Initializing new scraper (ID: %d)", self.scraper_id)
        try:
            while self.urls_to_process:
                current_url, depth = self.urls_to_process.pop(0)
                normalized_url = normalize_url(current_url)
                
                if not normalized_url.startswith(self.base_url):
                    logger.info("Skipping URL not starting with base URL: %s", normalized_url)
                    continue

                if normalized_url in self.processed_urls or normalized_url in self.error_urls:
                    continue

                if await url_tracker.is_visited(normalized_url):
                    logger.info("Skipping already visited URL: %s", normalized_url)
                    continue

                if is_suspicious_url(current_url):
                    if is_image_content_type(current_url):
                        logger.info("Scraper %d: Skipping image URL: %s", self.scraper_id, current_url)
                        continue

                try:
                    logger.info("Scraper %d: Attempting to process URL (depth %d): %s", self.scraper_id, depth, current_url)
                    domain = get_domain(current_url)
                    await self.rate_limiter.wait(domain)
                    content, content_type, extracted_text, metadata, discovered_urls = await process_page(
                        self.scraper_id,
                        current_url, 
                        self.force_scrape_method, 
                        selenium_driver=self.get_selenium_driver(),
                    )
                    
                    # Normalize all discovered URLs
                    all_discovered_urls = set(normalize_url(url) for url in discovered_urls)
                    
                    # Filter URLs for processing (only those starting with base_url)
                    urls_for_processing = {url for url in all_discovered_urls if url.startswith(self.base_url)}
                    
                    # Remove already processed or errored URLs from processing list
                    urls_for_processing = urls_for_processing - self.processed_urls - self.error_urls
                    
                    # Sort the URLs for consistent output
                    sorted_all_discovered = sorted(list(all_discovered_urls))
                    sorted_urls_for_processing = sorted(list(urls_for_processing))

                    self.results[normalized_url] = {
                        'metadata': metadata,
                        'content': extracted_text,
                        'discovered_urls': sorted_all_discovered,  # All discovered URLs
                    }
                    
                    self.processed_urls.add(normalized_url)
                    self.all_discovered_urls.update(all_discovered_urls)
                    logger.info("Scraper %d: Successfully processed %s", self.scraper_id, current_url)

                    await url_tracker.mark_visited(normalized_url)
                    logger.info("Marked URL as visited: %s", normalized_url)

                    if depth < self.max_depth:
                        self.urls_to_process.extend((url, depth + 1) for url in sorted_urls_for_processing)
                        logger.info("Scraper %d: Found %d URLs to process...", self.scraper_id, len(self.urls_to_process))

                except WebDriverException as e: # To catch Selenium exceptions and handle them appropriately
                    error_message = f"Scraper {self.scraper_id}: Selenium error processing {current_url}: {str(e)}"
                    logger.error(error_message)
                    self.selenium_driver.quit_selenium()  # Close the current driver
                    self.selenium_driver = None  # Reset the driver
                    # Optionally, to retry this URL later
                    # self.urls_to_process.append((current_url, depth))

                except Exception as e:
                    error_message = f"Scraper {self.scraper_id}: Error processing {current_url}: {str(e)}"
                    logger.error(error_message)
                    self.results[normalized_url] = {
                        'content': error_message,
                    }
                    self.error_urls.add(normalized_url)
        finally:
            if self.selenium_driver:
                self.selenium_driver.quit_selenium()
                logger.info("Scraper %d: Scraper terminated.", self.scraper_id)

        return self.results

async def run_scrapers(scraper_configs):
    """
    Run multiple scrapers concurrently.

    Args:
        scraper_configs (list): List of dictionaries containing configuration for each scraper.

    Returns:
        dict: Collated results from all scrapers.
    """
    # Start with a single scraper to discover initial URLs
    initial_scraper = WebsiteScraper(**scraper_configs[0], scraper_id=0)
    initial_results = await initial_scraper.scrape()
    logger.info("Initial scraper finished. Processing discovered URLs.")

    # Collect all discovered URLs from the initial scrape
    all_discovered_urls = set()
    for result in initial_results.values():
        all_discovered_urls.update(result.get('discovered_urls', []))

    logger.info("Total URLs discovered: %d", len(all_discovered_urls))

    # Divide discovered URLs among multiple scrapers
    url_batches = [list(all_discovered_urls)[i::len(scraper_configs)] for i in range(len(scraper_configs))]

    # Create new scrapers for each batch of URLs
    tasks = []
    for i, config in enumerate(scraper_configs):
        scraper = WebsiteScraper(config['base_url'], config['max_depth'], 
                                 force_scrape_method=config.get('force_scrape_method'), 
                                 scraper_id=i+1)
        scraper.urls_to_process = [(url, 1) for url in url_batches[i]]  # Start at depth 1 for new URLs
        tasks.append(scraper.scrape())
        logger.info("Scraper %d initialized with %d URLs", i+1, len(url_batches[i]))

    # Run all scrapers concurrently
    results = await asyncio.gather(*tasks)

    # Collate and sort results
    collated_results = {}
    for result in results:
        collated_results.update(result)

    return collated_results

async def run_init_scraper(scraper_config):
    """
    Run the initial scraper to discover URLs.

    Args:
        scraper_config (dict): Configuration for the initial scraper.

    Returns:
        dict: Results from the initial scraper.
    """
    scraper = WebsiteScraper(**scraper_config, scraper_id=0)
    results = await scraper.scrape()
    return results