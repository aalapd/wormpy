# utils.py

import requests
import json
import io
import asyncio
import time
import random
from urllib.parse import urlparse
from collections import defaultdict
from config import RATE_LIMIT_MIN, RATE_LIMIT_MAX

from modules.utils.logger import get_logger
from modules.utils.url_tracker import url_tracker

logging = get_logger(__name__)

class AsyncRateLimiter:
    """
    Asynchronous rate limiter with per-domain limiting capabilities.

    This class provides an asynchronous way to limit the rate of requests
    to different domains.

    Attributes:
        min_delay (float): Minimum delay between requests in seconds.
        max_delay (float): Maximum delay between requests in seconds.
        last_request_times (defaultdict): Dictionary to store the last request time for each domain.
    """

    def __init__(self, min_delay=RATE_LIMIT_MIN, max_delay=RATE_LIMIT_MAX):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_times = defaultdict(float)

    async def wait(self, domain):
        """
        Asynchronously wait for the appropriate time before making a new request to a domain.

        Args:
            domain (str): The domain for which to wait.

        This method calculates the time elapsed since the last request to the given domain
        and waits for the remaining time if necessary.
        """
        current_time = time.time()
        elapsed = current_time - self.last_request_times[domain]
        delay = random.uniform(self.min_delay, self.max_delay)
        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)
        self.last_request_times[domain] = time.time()

async def get_scraping_stats():
    """Get current scraping statistics."""
    return {
        'urls_in_pool': await url_tracker.get_pool_size(),
        'urls_visited': await url_tracker.get_visited_count(),
        'is_pool_empty': await url_tracker.is_pool_empty(),
    }

def get_pdf_data(file_path_or_url):
    pdf_data = None     
    # Determine if the input is a URL or local file path
    parsed = urlparse(file_path_or_url)
    if parsed.scheme in ('http', 'https'):
        response = requests.get(file_path_or_url)
        response.raise_for_status()
        pdf_data = io.BytesIO(response.content)
    else:
        pdf_data = open(file_path_or_url, 'rb')
    return pdf_data

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

def format_output(results, output_format, include_urls=False, essential_metadata_only=True):
    """
    Format the scraped results according to the specified output format.

    Args:
        results (dict): Dictionary of scraped results with URLs as keys and 
                        dictionaries containing 'content', 'discovered_urls', and 'metadata' as values
        output_format (str): Desired output format ('csv' or 'json')
        include_urls (bool, optional): Whether to include discovered URLs in the output. Defaults to False.
        essential_metadata_only (bool, optional): Whether to include only essential metadata. Defaults to True.

    Returns:
        list or dict: Formatted data ready for output. For CSV, a list of lists where the first row
                      is the header. For JSON, the original dictionary structure is maintained.

    Raises:
        ValueError: If an invalid output format is specified
    """
    sorted_results = dict(sorted(results.items()))
    
    # Filter metadata if requested
    if essential_metadata_only:
        for url, data in sorted_results.items():
            if 'metadata' in data:
                # Keep only essential metadata fields
                essential_fields = ['url', 'title', 'content_type']
                data['metadata'] = {k: v for k, v in data['metadata'].items() if k in essential_fields}

    if output_format == 'csv':
        if include_urls:
            csv_data = [['URL', 'Content', 'Discovered URLs', 'Metadata']]
            for url, data in sorted_results.items():
                metadata_str = json.dumps(data.get('metadata', {}))
                csv_data.append([
                    url, 
                    data['content'], 
                    ', '.join(data.get('discovered_urls', [])),
                    metadata_str
                ])
        else:
            csv_data = [['URL', 'Content', 'Metadata']]
            for url, data in sorted_results.items():
                metadata_str = json.dumps(data.get('metadata', {}))
                csv_data.append([
                    url, 
                    data['content'],
                    metadata_str
                ])
        return csv_data
    elif output_format == 'json':
        if not include_urls:
            # Create a copy without the discovered_urls for each entry
            clean_results = {}
            for url, data in sorted_results.items():
                clean_results[url] = {
                    'metadata': data.get('metadata', {}),
                    'content': data['content']
                }
            return clean_results
        return sorted_results
    else:
        raise ValueError(f"Invalid output format: {output_format}")
    
def set_filename(output_format, now):
    filename = f"scrape_{now}.{output_format}"
    return filename