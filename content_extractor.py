import requests
from bs4 import BeautifulSoup
import time
import logging

def fetch_page(url):
    try:
        logging.info(f"Fetching page content from URL: {url}")
        response = requests.get(url)
        response.raise_for_status()
        time.sleep(1)  # Rate limiting
        logging.info(f"Successfully fetched content from URL: {url}")
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching page content from URL {url}: {e}")
        raise

def extract_text(html):
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
    html = fetch_page(url)
    return extract_text(html), html  # Return both extracted text and raw HTML