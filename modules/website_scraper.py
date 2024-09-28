# File: modules/website_scraper.py

import logging
import asyncio
from .processors.url_processor import normalize_url, is_suspicious_url, extract_urls, is_valid_url, get_domain
from .processors.content_processor import process_page
from .processors.selenium_processor import SeleniumDriver
from .utils import is_image_content_type, AsyncRateLimiter

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
        self.scraper_id = scraper_id
        self.force_scrape_method = force_scrape_method
        self.selenium_driver = SeleniumDriver() if force_scrape_method == 'sel' else None
        self.rate_limiter = AsyncRateLimiter()
        self.all_discovered_urls = set()
        self.processed_urls = set()
        self.error_urls = set()
        self.urls_to_process = [(base_url, 0)]  # (url, depth)
        self.results = {}

    async def scrape(self):
        """
        Asynchronously scrape the website.

        This method manages the scraping process, including URL discovery,
        content processing, and error handling.

        Returns:
            dict: A dictionary containing the scraping results.
        """
        logging.info(f"Initializing new scraper (ID: {self.scraper_id})")
        try:
            while self.urls_to_process:
                current_url, depth = self.urls_to_process.pop(0)
                normalized_url = normalize_url(current_url)
                
                if normalized_url in self.processed_urls or normalized_url in self.error_urls:
                    continue

                logging.info(f"Scraper {self.scraper_id}: Processing URL (depth {depth}): {current_url}")

                if is_suspicious_url(current_url):
                    if is_image_content_type(current_url):
                        logging.info(f"Scraper {self.scraper_id}: Skipping image URL: {current_url}")
                        continue

                try:
                    domain = get_domain(current_url)
                    await self.rate_limiter.wait(domain)
                    text_content, raw_content, content_type, metadata, discovered_urls = await process_page(
                        self.scraper_id,
                        current_url, 
                        self.force_scrape_method, 
                        selenium_driver=self.selenium_driver,
                    )
                
                    new_urls = set(normalize_url(url) for url in discovered_urls if is_valid_url(url, self.base_url))
                    new_urls = {url for url in new_urls if url.startswith(self.base_url)}  # Filter URLs to start with base_url
                    new_urls = new_urls - self.processed_urls - self.error_urls  # Remove already processed or errored URLs
                    sorted_new_urls = sorted(list(new_urls))  # Sort the new URLs

                    self.results[normalized_url] = {
                        'metadata': metadata,
                        'content': text_content,
                        'discovered_urls': list(sorted_new_urls),
                    }
                    
                    self.processed_urls.add(normalized_url)
                    self.all_discovered_urls.add(normalized_url)
                    self.all_discovered_urls.update(sorted_new_urls)
                    logging.info(f"Scraper {self.scraper_id}: Successfully processed {current_url}")

                    if depth < self.max_depth:
                        self.urls_to_process.extend((url, depth + 1) for url in new_urls)

                except Exception as e:
                    error_message = f"Scraper {self.scraper_id}: Error processing {current_url}: {str(e)}"
                    logging.error(error_message)
                    self.results[normalized_url] = {
                        'content': error_message,
                    }
                    self.error_urls.add(normalized_url)
        finally:
            if self.selenium_driver:
                self.selenium_driver.quit_selenium()

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
    logging.info("Initial scraper finished. Processing discovered URLs.")

    # Collect all discovered URLs from the initial scrape
    all_discovered_urls = set()
    for result in initial_results.values():
        all_discovered_urls.update(result.get('discovered_urls', []))

    logging.info(f"Total URLs discovered: {len(all_discovered_urls)}")

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
        logging.info(f"Scraper {i+1} initialized with {len(url_batches[i])} URLs")

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

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    # Example usage
    # asyncio.run(run_scrapers([{'base_url': 'https://example.com', 'max_depth': 2}]))
