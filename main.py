import argparse
import logging
import asyncio
from modules.website_scraper import run_scrapers
from modules.utils import format_output, set_filename
from modules.file_handler import save_output
from modules.processors.url_processor import get_domain, is_valid_url
from modules.processors.selenium_processor import quit_selenium

def setup_logging(log_level):
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    logging.basicConfig(level=numeric_level, 
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()])

def main():
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

    try:
        # Prepare scraper configuration
        scraper_config = {
            'base_url': base_url,
            'max_depth': max_depth,
            'force_scrape_method': force_scrape_method
        }
        
        # Run scrapers and get results
        results = asyncio.run(run_scrapers([scraper_config]))
        results = results[0]  # Since we are running only one scraper, get the first result
        
        # Format the results
        formatted_output = format_output(results, output_format)
        
        # Determine output filename with current time
        filename = set_filename(output_format)
        
        # Save the formatted output
        if save_name: folder_name = save_name 
        else: 
            domain = get_domain(base_url)
            folder_name = domain 
        full_filepath = save_output(formatted_output, folder_name, filename, output_format)
        
        logging.info(f"Scraping complete. Data saved to {full_filepath}")
    except Exception as e:
        logging.error(f"An error occurred during scraping: {str(e)}")
    finally:
        quit_selenium()  # Ensure the Selenium driver is quit after the task is done

if __name__ == "__main__":
    main()
