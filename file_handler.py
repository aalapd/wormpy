import os
from datetime import datetime
import logging

def initialize_output_file(base_url):
    try:
        # Create 'scrapes' directory if it does not exist
        os.makedirs('scrapes', exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain = base_url.split("//")[-1].split("/")[0]
        filename = f"scrapes/scrape_{domain}_{timestamp}.txt"
        logging.info(f"Output file initialized: {filename}")
        return filename
    except Exception as e:
        logging.error(f"Error initializing output file: {e}")
        raise

def write_to_file(filename, content):
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"Successfully wrote to file: {filename}")
    except Exception as e:
        logging.error(f"Error writing to file {filename}: {e}")
        raise

def finalize_file(filename):
    try:
        # Placeholder for any final processing
        logging.info(f"Finalizing file: {filename}")
    except Exception as e:
        logging.error(f"Error finalizing file {filename}: {e}")
        raise
