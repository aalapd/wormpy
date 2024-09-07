from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
import requests
import logging
from ..utils import is_image_file_extension

def normalize_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

def is_suspicious_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    suspicious_params = ['itemId', 'imageId', 'galleryId']
    return any(param in query_params for param in suspicious_params) or is_image_file_extension(parsed_url.path)

def is_image_content_type(url):
    try:
        response = requests.head(url)
        content_type = response.headers.get('Content-Type', '')
        return content_type.startswith('image/')
    except requests.RequestException:
        logging.error(f"Error checking content type for {url}")
        return False

def extract_urls(content, base_url, content_type='text/html'):
    try:
        if content_type.lower().startswith('text/html'):
            soup = BeautifulSoup(content, 'html.parser')
            return {urljoin(base_url, a['href']) for a in soup.find_all('a', href=True)}
        elif content_type.lower() == 'application/pdf':
            # For PDF content, we don't extract URLs
            logging.info(f"Skipping URL extraction for PDF content: {base_url}")
            return set()
        else:
            logging.warning(f"Unsupported content type for URL extraction: {content_type}")
            return set()
    except Exception as e:
        logging.error(f"Error extracting URLs from content: {e}")
        return set()

def get_domain(url):
    return urlparse(url).netloc
