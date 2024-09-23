import argparse
import logging
import os
from datetime import datetime
from modules.website_scraper import scrape_website
from modules.utils import is_valid_url, format_output
from modules.file_handler import save_output

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
    #parser.add_argument("--urls-only", action="store_true", help="Return only URLs instead of content")
    parser.add_argument("--log", default="INFO", help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    parser.add_argument("--output", help="Specify the output file name (without extension)")
    parser.add_argument("--format", choices=['csv', 'json'], default='csv', help="Specify the output format (csv or json)")
    args = parser.parse_args()

    setup_logging(args.log)

    base_url = args.url
    max_depth = args.depth
    #urls_only = args.urls_only
    output_format = args.format

    if not is_valid_url(base_url, base_url):
        logging.error("Invalid URL provided.")
        return

    if max_depth < 0:
        logging.error("Depth must be greater than or equal to zero.")
        return

    try:
        # Scrape website and get results as a dictionary
        results = scrape_website(base_url, max_depth)
        
        # Format the results
        formatted_output = format_output(results, output_format)
        
        # Determine output filename with current time
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = args.output if args.output else f"scrape_{base_url.split('//')[1].split('/')[0]}"
        filename = f"{output_file}_{timestamp}.{output_format}"
        
        # Save the formatted output
        save_output(formatted_output, filename, output_format)
        
        # Get the absolute path of the output file
        file_path = os.path.abspath(filename)
        logging.info(f"Scraping complete. Output saved to {file_path}")
    except Exception as e:
        logging.error(f"An error occurred during scraping: {str(e)}")

if __name__ == "__main__":
    main()