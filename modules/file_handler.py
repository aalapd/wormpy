import os
import csv
import json
import logging

def save_output(data, domain, filename, output_format):
    """
    Save the formatted output to a file.

    Args:
        data: Formatted data to be saved (list for CSV, dict for JSON)
        filename (str): Name of the output file
        output_format (str): Format of the output ('csv' or 'json')

    Raises:
        ValueError: If an invalid output format is specified
        IOError: If there's an error writing to the file
    """
    try:

        # Create a directory for the domain inside 'scrapes'
        domain_dir = os.path.join('scrapes', domain)
        os.makedirs(domain_dir, exist_ok=True)
        # Full path for the output file
        full_path = os.path.join(domain_dir, filename)
                                                                                                                                                
        if output_format == 'csv':
            with open(full_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(data)
        elif output_format == 'json':
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Invalid output format: {output_format}")
                                                                                                                                                
        logging.info(f"Successfully saved output to {full_path}.")
        return full_path
    except IOError as e:
        logging.error(f"Error writing to file {filename}: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error while saving output: {e}")
        raise