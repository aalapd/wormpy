import requests
import logging
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
from ..utils import is_image_file_extension

# urlparse output:
# ParseResult(scheme='https', netloc='www.example.com:8080', path='/path/to/resource', params='', query='query=example', fragment='fragment')

def get_domain(url):
    # Parse the domain from the URL and format it
    parsed_url = urlparse(url)
    domain = parsed_url.netloc #.replace('.', 'dot')
    return domain 

def is_valid_url(url, base_url):
    parsed_url = urlparse(url)
    parsed_base = urlparse(base_url)
    return (parsed_url.netloc == parsed_base.netloc and not is_image_file_extension(parsed_url.path))

def normalize_url(url):
    parsed = urlparse(url)
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
    return normalized

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
    
def is_pdf_url(url):
    """
    Check if the given URL points to a PDF file.
    
    :param url: URL to check
    :return: Boolean indicating if the URL is likely a PDF
    """
    try:
        if url.lower().endswith('.pdf'):
            return True
        response = requests.head(url, allow_redirects=True)
        return 'application/pdf' in response.headers.get('Content-Type', '').lower()
    except requests.RequestException:
        logging.warning(f"Error checking content type for {url}")
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