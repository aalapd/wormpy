import requests
import logging
from urllib.parse import urlparse

def is_valid_url(url, base_url):
    parsed_url = urlparse(url)
    parsed_base = urlparse(base_url)
    return (parsed_url.netloc == parsed_base.netloc and not is_image_file_extension(parsed_url.path))

def is_image_file_extension(path):
    image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'mp3', 'mp4', 'wav', 'avi', 'mov']
    return path.split('.')[-1].lower() in image_extensions

def is_image_content_type(url):
    try:
        response = requests.head(url)
        content_type = response.headers.get('Content-Type', '')
        return content_type.startswith('image/')
    except requests.RequestException:
        logging.error(f"Error checking content type for {url}")
        return False

def format_output(results, output_format):
    """
    Format the scraped results according to the specified output format.

    Args:
        results (dict): Dictionary of scraped results with URLs as keys and 
                        dictionaries containing 'content' and 'discovered_urls' as values
        output_format (str): Desired output format ('csv' or 'json')

    Returns:
        list or dict: Formatted data ready for output

    Raises:
        ValueError: If an invalid output format is specified
    """
    sorted_results = dict(sorted(results.items()))

    if output_format == 'csv':
        csv_data = [['URL', 'Content', 'Discovered URLs']]
        for url, data in sorted_results.items():
            csv_data.append([url, data['content'], ', '.join(data['discovered_urls'])])
        return csv_data
    elif output_format == 'json':
        return sorted_results
    else:
        raise ValueError(f"Invalid output format: {output_format}")
    
