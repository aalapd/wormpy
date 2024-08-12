import argparse
import logging
from website_scraper import scrape_website
from utils import is_valid_url
from file_handler import initialize_output_file, finalize_file

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
    parser.add_argument("depth", type=int, help="Maximum crawling depth")
    parser.add_argument("--log", default="INFO", help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    parser.add_argument("--output", help="Specify the output file name")
    args = parser.parse_args()

    setup_logging(args.log)

    base_url = args.url
    max_depth = args.depth

    if not is_valid_url(base_url, base_url):
        logging.error("Invalid URL provided.")
        return

    if max_depth < 1:
        logging.error("Depth must be a positive integer.")
        return

    try:
        output_file = args.output if args.output else initialize_output_file(base_url)
        scrape_website(base_url, max_depth, output_file)
        finalize_file(output_file)
        logging.info(f"Scraping complete. Output saved to {output_file}")
    except Exception as e:
        logging.error(f"An error occurred during scraping: {str(e)}")

if __name__ == "__main__":
    main()