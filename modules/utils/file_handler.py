import os
import csv
import json
import logging
from datetime import datetime

from modules.utils.logger import get_logger, configure_logging

def setup_file_logging(domain_dir):
    """
    Set up logging to write to a file in the same directory as the output files.
    
    Args:
        domain_dir (str): The directory where output files are saved
    
    Returns:
        str: The path to the log file
    """
    log_filename = f"scrape_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_filepath = os.path.join(domain_dir, log_filename)
    
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    
    return log_filepath

def save_output(data, domain, filename, output_format):
    """
    Save the formatted output to a file and set up logging.

    Args:
        data: Formatted data to be saved (list for CSV, dict for JSON)
        domain (str): The domain being scraped
        filename (str): Name of the output file
        output_format (str): Format of the output ('csv' or 'json')

    Returns:
        tuple: (str, str) The full path of the output file and the log file

    Raises:
        ValueError: If an invalid output format is specified
        IOError: If there's an error writing to the file
    """
    try:
        # Create a directory for the domain inside 'scrapes'
        domain_dir = os.path.join('scrapes', domain)
        os.makedirs(domain_dir, exist_ok=True)
        
        # Set up logging to file
        log_filepath = setup_file_logging(domain_dir)
        
        # Full path for the output file
        full_path = os.path.join(domain_dir, filename)
        
        logging = get_logger(__name__)
        
        if output_format == 'csv':
            with open(full_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(data)
        elif output_format == 'json':
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Invalid output format: {output_format}")
        
        logging.info(f"Successfully saved output to {full_path}")
        return full_path, log_filepath
    except IOError as e:
        logging.error(f"Error writing to file {filename}: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error while saving output: {e}")
        raise
