import argparse
import logging
import asyncio
import time
from config import MAX_SIMULTANEOUS_SCRAPERS
from modules.website_scraper import WebsiteScraper, run_scrapers, run_init_scraper
from modules.utils import format_output, set_filename
from modules.file_handler import save_output
from modules.processors.url_processor import get_domain, is_valid_url

def setup_logging(log_level):
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    logging.basicConfig(level=numeric_level,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()])

def main():
    start_time = time.time()  # Record the start time

    parser = argparse.ArgumentParser(description="Website Scraper")
    parser.add_argument("url", help="Base URL of the website to scrape")
    parser.add_argument("depth", type=int, help="Maximum crawling depth; 0 returns content from a single page")
    parser.add_argument("--log", default="INFO", help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    parser.add_argument("--savename", help="Specify the directory name to save output")
    parser.add_argument("--format", choices=['csv', 'json'], default='json', help="Specify the output format (csv or json)")
    parser.add_argument("--force", choices=['req', 'sel'], help="Force scraping with either requests or selenium")
    args = parser.parse_args()

    setup_logging(args.log)

    base_url = args.url
    max_depth = args.depth
    save_name = args.savename
    output_format = args.format
    force_scrape_method = args.force

    if not is_valid_url(base_url, base_url):
        logging.error("Invalid URL provided.")
        return

    if max_depth < 0:
        logging.error("Depth must be greater than or equal to zero.")
        return

    if force_scrape_method and force_scrape_method != 'req' and force_scrape_method != 'sel':
        logging.error("Invalid flag used for --force. Please use either 'req' for requests or 'sel' for selenium.")
        return

    async def run_scraping():
        try:
            # Prepare a single scraper configuration for initial URL discovery
            initial_scraper_config = {'base_url': base_url, 'max_depth': 0, 'force_scrape_method': force_scrape_method}

            logging.info("Starting initial scraper for URL discovery")
            # Run the initial scraper to discover URLs
            initial_results = await run_init_scraper(initial_scraper_config)
            logging.info("Initial scraper finished execution. Processing discovered URLs.")

            # Collect all discovered URLs from the initial scrape
            all_discovered_urls = set()
            for result in initial_results.values():
                all_discovered_urls.update(result['discovered_urls'])

            logging.info(f"Total URLs discovered: {len(all_discovered_urls)}")
            if max_depth > 0 and len(all_discovered_urls) > 0:

                # Divide discovered URLs among multiple scrapers
                url_batches = [list(all_discovered_urls)[i::MAX_SIMULTANEOUS_SCRAPERS] for i in range(MAX_SIMULTANEOUS_SCRAPERS)]

                # Prepare multiple scraper configurations for discovered URLs
                scrapers = []
                for i in range(min(len(all_discovered_urls), MAX_SIMULTANEOUS_SCRAPERS)):
                    scraper = WebsiteScraper(base_url, max_depth, scraper_id=i+1, force_scrape_method=force_scrape_method)
                    scraper.urls_to_process = [(url, 1) for url in url_batches[i]]  # Start at depth 1 for new URLs
                    scrapers.append(scraper)
                    logging.info(f"Scraper {i+1} initialized with {len(url_batches[i])} URLs")

                # Run scrapers on discovered URLs and get results
                results = await asyncio.gather(*(scraper.scrape() for scraper in scrapers))

                # Collate and sort results
                collated_results = {}
                for result in results:
                    collated_results.update(result)

                # Format the collated results
                formatted_output = format_output(collated_results, output_format)
            
            else: 
                formatted_output = format_output(initial_results, output_format)

            # Determine output filename with current time
            filename = set_filename(output_format)

            # Save the formatted output
            if save_name:
                folder_name = save_name
            else:
                domain = get_domain(base_url)
                folder_name = domain
            full_filepath = save_output(formatted_output, folder_name, filename, output_format)

            logging.info(f"Scraping complete. Saved output to {full_filepath}.")
        except Exception as e:
            logging.error(f"An error occurred during scraping: {str(e)}")

    asyncio.run(run_scraping())

    end_time = time.time()  # Record the end time
    elapsed_time = end_time - start_time  # Calculate the elapsed time
    logging.info(f"Time taken: {elapsed_time:.2f} seconds.")  # Log the elapsed time

if __name__ == "__main__":
    main()