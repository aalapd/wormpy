import requests
import time
import io
import logging
import random
import PyPDF2
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from .url_processor import is_pdf_url
from config import HEADERS, REQUEST_TIMEOUT, MAX_RETRIES, INITIAL_RETRY_DELAY, RATE_LIMIT_MIN, RATE_LIMIT_MAX

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

def fetch_page(url, max_retries=MAX_RETRIES, initial_delay=INITIAL_RETRY_DELAY):
    for attempt in range(max_retries):
        try:
            logging.info(f"Fetching content from URL: {url}")
            rate_limiter.wait()
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            logging.info(f"Successfully fetched content from URL: {url}")
            return response.content, response.headers.get('Content-Type', '')
        except requests.RequestException as e:
            logging.warning(f"Error fetching content from URL {url} (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)
                logging.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error(f"Failed to fetch content from URL {url} after {max_retries} attempts")
                raise

def extract_text_from_html(html):
    """
    Extract text content from HTML, removing unwanted elements and formatting.

    This function parses HTML content, removes unwanted elements (such as scripts, 
    styles, navigation, headers, footers, asides, and hidden elements), and 
    extracts the remaining text content.

    Args:
        html (str): The HTML content to process.

    Returns:
        str: The extracted and cleaned text content.

    Raises:
        Exception: If there's an error during the extraction process.

    Logs:
        - INFO: When text is successfully extracted.
        - ERROR: When an error occurs during extraction.
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script, style, and other unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Remove hidden elements
        for hidden in soup.find_all(style=lambda value: value and "display:none" in value):
            hidden.decompose()

        # Remove elements with "hidden" in their class names
        for hidden_class in soup.find_all(class_=lambda x: x and 'hidden' in x):
            hidden_class.decompose()
        
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

def extract_text_from_pdf(file_path_or_url):
    """
    Extract text content from a PDF file.
    
    :param file_path_or_url: Local file path or URL of the PDF file
    :return: Extracted text content as a string
    """
    pdf_file = None
    try:
        # Determine if the input is a URL or local file path
        parsed = urlparse(file_path_or_url)
        if parsed.scheme in ('http', 'https'):
            response = requests.get(file_path_or_url)
            response.raise_for_status()
            pdf_file = io.BytesIO(response.content)
        else:
            pdf_file = open(file_path_or_url, 'rb')

        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract text from all pages
        text_content = "\n".join(page.extract_text() for page in pdf_reader.pages)
        
        logging.info(f"Successfully extracted text from PDF: {file_path_or_url}")
        return text_content.strip()

    except requests.RequestException as e:
        logging.error(f"Error fetching PDF from URL {file_path_or_url}: {str(e)}")
        return f"Error fetching PDF: {str(e)}"
    except PyPDF2.errors.PdfReadError as e:
        logging.error(f"Error reading PDF {file_path_or_url}: {str(e)}")
        return f"Error reading PDF: {str(e)}"
    except Exception as e:
        logging.error(f"Unexpected error processing PDF {file_path_or_url}: {str(e)}")
        return f"Unexpected error: {str(e)}"
    finally:
        if pdf_file and not isinstance(pdf_file, io.BytesIO):
            pdf_file.close()

def process_page(url):
    content, content_type = fetch_page(url)
    if content_type.lower().startswith('text/html'):
        extracted_text = extract_text_from_html(content.decode('utf-8'))
    elif content_type.lower() == 'application/pdf' or is_pdf_url(url):
        extracted_text = extract_text_from_pdf(url)
    else:
        extracted_text = f"Unsupported content type: {content_type}"
    
    return extracted_text, content, content_type