import requests
from bs4 import BeautifulSoup
import time
import logging
import random
from .pdf_processor import extract_text_from_pdf, is_pdf_url

class RateLimiter:
    def __init__(self, min_delay=1, max_delay=5):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0

    def wait(self):
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        delay = random.uniform(self.min_delay, self.max_delay)
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self.last_request_time = time.time()

rate_limiter = RateLimiter()

def fetch_page(url, max_retries=3, backoff_factor=2):
    for attempt in range(max_retries):
        try:
            logging.info(f"Fetching content from URL: {url}")
            rate_limiter.wait()
            response = requests.get(url)
            response.raise_for_status()
            logging.info(f"Successfully fetched content from URL: {url}")
            return response.content, response.headers.get('Content-Type', '')
        except requests.RequestException as e:
            logging.warning(f"Error fetching content from URL {url} (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                wait_time = backoff_factor ** attempt
                logging.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logging.error(f"Failed to fetch content from URL {url} after {max_retries} attempts")
                raise

def extract_text_from_html(html):
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script, style, and other unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Remove hidden elements
        for hidden in soup.find_all(style=lambda value: value and "display:none" in value):
            hidden.decompose()
        
        # Get text
        text = soup.get_text(separator='\n', strip=True)
        
        # Remove excessive newlines and whitespace
        lines = (line.strip() for line in text.splitlines())
        text = '\n'.join(line for line in lines if line)
        
        logging.info("Successfully extracted text from HTML content")
        return text
    except Exception as e:
        logging.error(f"Error extracting text from HTML content: {e}")
        raise

def process_page(url):
    content, content_type = fetch_page(url)
    
    if 'application/pdf' in content_type.lower() or is_pdf_url(url):
        extracted_text = extract_text_from_pdf(url)
        return extracted_text, content, content_type  # Return extracted text, raw content, and content type
    else:
        html = content.decode('utf-8', errors='ignore')
        extracted_text = extract_text_from_html(html)
        return extracted_text, html, content_type  # Return extracted text, raw HTML, and content type