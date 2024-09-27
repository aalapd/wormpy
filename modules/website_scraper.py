import logging
import asyncio
from .processors.url_processor import normalize_url, is_suspicious_url, extract_urls, is_valid_url
from .processors.content_processor import process_page
from .utils import is_image_content_type

class WebsiteScraper:
    def __init__(self, base_url, max_depth, force_scrape_method=None):
        self.base_url = base_url
        self.max_depth = max_depth
        self.force_scrape_method = force_scrape_method
        self.all_discovered_urls = set()
        self.processed_urls = set()
        self.error_urls = set()
        self.urls_to_process = [(base_url, 0)]  # (url, depth)
        self.results = {}

    async def scrape(self):
        while self.urls_to_process:
            current_url, depth = self.urls_to_process.pop(0)
            normalized_url = normalize_url(current_url)
            
            if normalized_url in self.processed_urls or normalized_url in self.error_urls:
                continue

            logging.info(f"Processing URL (depth {depth}): {current_url}")

            if is_suspicious_url(current_url):
                if is_image_content_type(current_url):
                    logging.info(f"Skipping image URL: {current_url}")
                    continue

            try:
                text_content, raw_content, content_type, metadata = await process_page(current_url, self.force_scrape_method)
                
                new_urls = set(normalize_url(url) for url in extract_urls(raw_content, current_url, content_type) if is_valid_url(url, self.base_url))
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
                logging.info(f"Successfully processed {current_url}")

                if depth < self.max_depth:
                    self.urls_to_process.extend((url, depth + 1) for url in new_urls)

            except Exception as e:
                error_message = f"Error processing {current_url}: {str(e)}"
                logging.error(error_message)
                self.results[normalized_url] = {
                    'content': error_message,
                }
                self.error_urls.add(normalized_url)

        return self.results

async def run_scrapers(scraper_configs):
    # Start with a single scraper to discover initial URLs
    initial_scraper = WebsiteScraper(**scraper_configs[0])
    initial_results = await initial_scraper.scrape()

    # Collect all discovered URLs from the initial scrape
    all_discovered_urls = set()
    for result in initial_results.values():
        all_discovered_urls.update(result['discovered_urls'])

    # Divide discovered URLs among multiple scrapers
    url_batches = [list(all_discovered_urls)[i::len(scraper_configs)] for i in range(len(scraper_configs))]

    # Create new scrapers for each batch of URLs
    tasks = []
    for i, config in enumerate(scraper_configs):
        scraper = WebsiteScraper(config['base_url'], config['max_depth'], config['force_scrape_method'])
        scraper.urls_to_process = [(url, 1) for url in url_batches[i]]  # Start at depth 1 for new URLs
        tasks.append(scraper.scrape())

    # Run all scrapers concurrently
    results = await asyncio.gather(*tasks)

    # Collate and sort results
    collated_results = {}
    for result in results:
        collated_results.update(result)

    return collated_results

async def run_scrapers(scraper_configs):
    tasks = []
    for config in scraper_configs:
        scraper = WebsiteScraper(**config)
        tasks.append(scraper.scrape())
    results = await asyncio.gather(*tasks)
    return results

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    # Example usage
    # asyncio.run(run_scrapers([{'base_url': 'https://example.com', 'max_depth': 2}]))
