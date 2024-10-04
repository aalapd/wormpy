# file_handler.py

import os
import csv
import json

from modules.utils.logger import get_logger
logging = get_logger(__name__)


def save_output(data, domain, filename, output_format):
    """
    Save the formatted output to a file.

    Args:
        data: Formatted data to be saved (list for CSV, dict for JSON)
        domain (str): The domain being scraped
        filename (str): Name of the output file
        output_format (str): Format of the output ('csv' or 'json')

    Returns:
        str: The full path of the output file

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
        
        logging.debug(f"Successfully saved output to {full_path}")
        return full_path
    except IOError as e:
        logging.error(f"Error writing to file {filename}: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error while saving output: {e}")
        raise

def read_file(file_path):
    """
    Read the contents of a file.

    Args:
        file_path (str): Path to the file to be read

    Returns:
        str: Contents of the file

    Raises:
        IOError: If there's an error reading the file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except IOError as e:
        logging.error(f"Error reading file {file_path}: {e}")
        raise

def write_file(file_path, content):
    """
    Write content to a file.

    Args:
        file_path (str): Path to the file to be written
        content (str): Content to write to the file

    Raises:
        IOError: If there's an error writing to the file
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except IOError as e:
        logging.error(f"Error writing to file {file_path}: {e}")
        raise

def append_to_file(file_path, content):
    """
    Append content to an existing file.

    Args:
        file_path (str): Path to the file to be appended
        content (str): Content to append to the file

    Raises:
        IOError: If there's an error appending to the file
    """
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content)
    except IOError as e:
        logging.error(f"Error appending to file {file_path}: {e}")
        raise

def delete_file(file_path):
    """
    Delete a file.

    Args:
        file_path (str): Path to the file to be deleted

    Raises:
        OSError: If there's an error deleting the file
    """
    try:
        os.remove(file_path)
    except OSError as e:
        logging.error(f"Error deleting file {file_path}: {e}")
        raise

def create_directory(dir_path):
    """
    Create a directory if it doesn't exist.

    Args:
        dir_path (str): Path to the directory to be created

    Raises:
        OSError: If there's an error creating the directory
    """
    try:
        os.makedirs(dir_path, exist_ok=True)
    except OSError as e:
        logging.error(f"Error creating directory {dir_path}: {e}")
        raise

def list_files(dir_path):
    """
    List all files in a directory.

    Args:
        dir_path (str): Path to the directory

    Returns:
        list: List of file names in the directory

    Raises:
        OSError: If there's an error reading the directory
    """
    try:
        return os.listdir(dir_path)
    except OSError as e:
        logging.error(f"Error listing files in directory {dir_path}: {e}")
        raise

def file_exists(file_path):
    """
    Check if a file exists.

    Args:
        file_path (str): Path to the file

    Returns:
        bool: True if the file exists, False otherwise
    """
    return os.path.exists(file_path)

def get_file_size(file_path):
    """
    Get the size of a file in bytes.

    Args:
        file_path (str): Path to the file

    Returns:
        int: Size of the file in bytes

    Raises:
        OSError: If there's an error getting the file size
    """
    try:
        return os.path.getsize(file_path)
    except OSError as e:
        logging.error(f"Error getting size of file {file_path}: {e}")
        raise