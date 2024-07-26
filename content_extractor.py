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
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        logging.info("Successfully extracted text from HTML content")
        return text
    except Exception as e:
        logging.error(f"Error extracting text from HTML content: {e}")
        raise

def process_page(url):
    html = fetch_page(url)
    return extract_text(html)
