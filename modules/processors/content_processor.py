import requests
import time
import io
import logging
import random
import PyPDF2
import json
from bs4 import BeautifulSoup
from .url_processor import is_pdf_url
from .selenium_processor import fetch_with_selenium
from ..utils import get_pdf_data
from config import HEADERS, REQUEST_TIMEOUT, MAX_RETRIES, INITIAL_RETRY_DELAY, RATE_LIMIT_MIN, RATE_LIMIT_MAX

class RateLimiter:
    def __init__(self, min_delay=RATE_LIMIT_MIN, max_delay=RATE_LIMIT_MAX):
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

def process_page(url, force_scrape_method=None):
    content, content_type = fetch_page(url,force_scrape_method=force_scrape_method)
    metadata = extract_metadata(content, content_type, url)
    
    if content_type.lower().startswith('text/html'):
        extracted_text = extract_text_from_html(content)
    elif content_type.lower() == 'application/pdf' or is_pdf_url(url):
        extracted_text = extract_text_from_pdf(url)
    else:
        extracted_text = f"Unsupported content type: {content_type}"
    
    return extracted_text, content, content_type, metadata

def fetch_page(url, force_scrape_method=None, max_retries=MAX_RETRIES, initial_delay=INITIAL_RETRY_DELAY):
    """
    Fetch page content, trying static first and then dynamic if needed.
                                                                                                                        
    Args:
        url (str): The URL to fetch.
        max_retries (int): Maximum number of retry attempts.
        initial_delay (float): Initial delay between retries.
        force_scrape_method (str): Force the use of 'req' for requests or 'sel' for selenium.
                                                                                                                        
    Returns:
        tuple: A tuple containing the page content and content type.
                                                                                                                        
    Raises:
        Exception: If unable to fetch the page after max_retries.
    """
    for attempt in range(max_retries):
        try:
            logging.info(f"Fetching content from URL: {url}")
            rate_limiter.wait()
                                                                                                                        
            if force_scrape_method == 'sel':
                logging.info(f"Forcing Selenium for {url}")
                content, content_type = fetch_with_selenium(url)
                if content is None:
                    raise Exception("Selenium fetch failed")
            else:
                # Try with requests first
                response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                content = response.content
                content_type = response.headers.get('Content-Type', '')
                                                                                                                        
                # Check if the content is likely to be dynamic
                if force_scrape_method != 'req' and is_dynamic_content(content):
                    logging.info(f"Content seems dynamic, switching to Selenium for {url}")
                    content, content_type = fetch_with_selenium(url)
                    if content is None:
                        raise Exception("Selenium fetch failed")
                                                                                                                        
            logging.info(f"Successfully fetched content from URL: {url}")
            return content, content_type
        except (requests.RequestException, Exception) as e:
            logging.warning(f"Error fetching content from URL {url} (attempt {attempt + 1}/{max_retries}): {str(e)}")    
            if attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)
                logging.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error(f"Failed to fetch content from URL {url} after {max_retries} attempts")
                raise

def extract_metadata(content, content_type, url):
    """
    Extract metadata from the content based on its type.
    
    Args:
        content (bytes or str): The raw content of the page.
        content_type (str): The content type of the page.
        url (str): The URL of the page.
    
    Returns:
        dict: A dictionary containing the extracted metadata.
    """
    metadata = {
        'url': url,
        'content_type': content_type,
    }
    
    if content_type.lower().startswith('text/html'):
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract title
        metadata['title'] = soup.title.string if soup.title else None
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            if 'name' in meta.attrs and 'content' in meta.attrs:
                metadata[meta['name'].lower()] = meta['content']
            elif 'property' in meta.attrs and 'content' in meta.attrs:
                metadata[meta['property'].lower()] = meta['content']
        
        # Extract Open Graph metadata
        for og in soup.find_all('meta', property=lambda x: x and x.startswith('og:')):
            metadata[og['property']] = og['content']
        
        # Extract schema.org metadata
        for schema in soup.find_all('script', type='application/ld+json'):
            try:
                schema_data = json.loads(schema.string)
                metadata['schema_org'] = schema_data
            except json.JSONDecodeError:
                logging.warning(f"Failed to parse schema.org data for {url}")
        
    elif content_type.lower() == 'application/pdf':
        try:
            pdf_file = get_pdf_data(url)
            reader = PyPDF2.PdfReader(pdf_file)
            if reader.metadata:
                metadata.update(reader.metadata)
        except Exception as e:
            logging.error(f"Error extracting PDF metadata from {url}: {str(e)}")
    
    # Add logic for other content types here in the future
    
    return metadata

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
    try:
        
        pdf_file = get_pdf_data(file_path_or_url)
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

def is_dynamic_content(content):
    """
    Check if the content is likely to be dynamic based on the amount of text.

    Args:
        content (bytes): The page content.

    Returns:
        bool: True if the content is likely dynamic, False otherwise.
    """
    if content is None:
        return True  # Assume dynamic if content is None
    try:
        text = extract_text_from_html(content.decode('utf-8'))
        return len(text) < 500  # Adjust this threshold as needed
    except Exception as e:
        logging.warning(f"Error in is_likely_dynamic: {e}")
        return True  # Assume dynamic if there's an error