from content_extractor import process_page
from file_handler import write_to_file
import logging

def process_urls(urls, output_file, max_depth):
    for index, url in enumerate(urls[:max_depth]):
        logging.info(f"Processing URL {index + 1}/{min(len(urls), max_depth)}: {url}")
        try:
            content = process_page(url)
            write_to_file(output_file, f"\n\n--- Content from {url} ---\n\n")
            write_to_file(output_file, content)
            logging.info(f"Successfully processed {url}")
        except Exception as e:
            error_message = f"\n\nError processing {url}: {str(e)}\n\n"
            write_to_file(output_file, error_message)
            logging.error(f"Error processing {url}: {e}")
