import argparse
import logging
import re
from urllib.parse import urlparse
from sitemap_parser import get_all_urls
from url_processor import process_urls
from file_handler import initialize_output_file, finalize_file

def setup_logging():
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()])

def validate_url(url):
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])

def main():
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Website Scraper")
    parser.add_argument("url", help="Base URL of the website to scrape")
    parser.add_argument("depth", type=int, help="Maximum crawling depth")
    args = parser.parse_args()

    base_url = args.url
    max_depth = args.depth

    if not validate_url(base_url):
        logging.error("Invalid URL provided.")
        return

    if max_depth < 1:
        logging.error("Depth must be a positive integer.")
        return

    try:
        output_file = initialize_output_file(base_url)
    except Exception as e:
        logging.error(f"Failed to initialize output file: {str(e)}")
        return

    try:
        urls = get_all_urls(base_url)
        if not urls:
            logging.warning("No URLs found to scrape.")
            return
        process_urls(urls, output_file, max_depth)
        finalize_file(output_file)
        logging.info(f"Scraping complete. Output saved to {output_file}")
    except Exception as e:
        logging.error(f"An error occurred during scraping: {str(e)}")
    finally:
        try:
            finalize_file(output_file)
        except Exception as e:
            logging.error(f"Failed to finalize output file: {str(e)}")

if __name__ == "__main__":
    main()
