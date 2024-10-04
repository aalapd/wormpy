# content_processor.py

import requests
import io
import asyncio
import PyPDF2
import json
from typing import Tuple, List, Optional, Dict, Any
from bs4 import BeautifulSoup
from .url_processor import is_pdf_url, extract_urls
from ..utils.utils import get_pdf_data
#from ..utils.url_tracker import url_tracker
from config import HEADERS, REQUEST_TIMEOUT, MAX_RETRIES, INITIAL_RETRY_DELAY

from modules.utils.logger import get_logger
logging = get_logger(__name__)

async def process_page(
    scraper_id: int,
    url: str,
    force_scrape_method: Optional[str] = None,
    selenium_driver: Any = None
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[Dict[str, Any]], List[str]]:
    """
    Process a page by fetching its content and extracting relevant information.

    Args:
        scraper_id (int): The ID of the scraper processing this page.
        url (str): The URL of the page to process.
        force_scrape_method (str, optional): Force a specific scraping method ('req' or 'sel').
        selenium_driver (SeleniumDriver, optional): Instance of SeleniumDriver for Selenium operations.

    Returns:
        tuple: A tuple containing content, content type, extracted text, metadata, and discovered URLs.
    """
    try:
        content, content_type, fetched_urls = await fetch_page(scraper_id, url, force_scrape_method, selenium_driver=selenium_driver)

        # Convert content to string if it's bytes
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='replace')

        # Extract metadata
        metadata = extract_metadata(content, content_type, url)

        # Extract text
        if content_type.lower().startswith('text/html'):
            extracted_text = extract_text_from_html(content)
        elif content_type.lower() == 'application/pdf' or is_pdf_url(url):
            extracted_text = extract_text_from_pdf(url)
        else:
            extracted_text = f"Scraper {scraper_id}: Unsupported content type: {content_type}"

        # Extract URLs
        discovered_urls = fetched_urls if fetched_urls else extract_urls(content, url, content_type)

        return content, content_type, extracted_text, metadata, discovered_urls
    except Exception as e:
        logging.error("Scraper %d: Error processing %s: %s", scraper_id, url, str(e))
        return None, None, None, None, []

async def fetch_page(
    scraper_id: int,
    url: str,
    force_scrape_method: Optional[str] = None,
    max_retries: int = MAX_RETRIES,
    initial_delay: float = INITIAL_RETRY_DELAY,
    selenium_driver: Any = None
) -> Tuple[Optional[bytes], str, List[str]]:
    """
    Fetch page content, trying static first and then dynamic if needed.

    Args:
        scraper_id (int): The ID of the scraper fetching the page.
        url (str): The URL to fetch.
        force_scrape_method (str, optional): Force the use of 'req' for requests or 'sel' for selenium.
        max_retries (int): Maximum number of retry attempts.
        initial_delay (float): Initial delay between retries.
        selenium_driver (SeleniumDriver, optional): Instance of SeleniumDriver for Selenium operations.

    Returns:
        tuple: A tuple containing the page content, content type, and discovered URLs.

    Raises:
        Exception: If unable to fetch the page after max_retries.
    """
    for attempt in range(max_retries):
        try:
            logging.info("Scraper %d: Attempting to fetch content from URL: %s", scraper_id, url)

            if force_scrape_method == 'sel':
                logging.info("Scraper %d: Forcing Selenium for %s", scraper_id, url)
                if selenium_driver is None:
                    raise Exception("Selenium driver not provided")
                content, content_type, discovered_urls = await selenium_driver.fetch_with_selenium(url)
                if content is None:
                    raise Exception("Scraper %d: Selenium fetch failed!", scraper_id)
            else:
                # Try with requests first
                response = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: requests.get(
                        url,
                        headers=HEADERS,
                        timeout=REQUEST_TIMEOUT,
                    )
                )
                response.raise_for_status()
                content = response.content
                content_type = response.headers.get('Content-Type', '')
                discovered_urls = []

                # Check if the content is likely to be dynamic
                if force_scrape_method != 'req' and is_dynamic_content(content):
                    logging.debug("Scraper %d: Content seems dynamic, switching to Selenium for %s", scraper_id, url)
                    if selenium_driver is None:
                        raise Exception("Could not get Selenium driver for dynamic content")
                    content, content_type, discovered_urls = await selenium_driver.fetch_with_selenium(url)
                    if content is None:
                        raise Exception("Scraper %d: Selenium fetch failed!", scraper_id)

                logging.info("Scraper %d: Successfully fetched content from URL: %s", scraper_id, url)
            return content, content_type, discovered_urls
        except (requests.RequestException, Exception) as e:
            logging.warning("Scraper %d: Error fetching content from URL %s (attempt %d/%d): %s", 
                           scraper_id, url, attempt + 1, max_retries, str(e))
            if attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)
                logging.info("Scraper %d: Retrying in %d seconds...", scraper_id, delay)
                await asyncio.sleep(delay)
            else:
                logging.error("Scraper %d: Failed to fetch content from URL %s after %d attempts!", 
                             scraper_id, url, max_retries)
                raise

def extract_metadata(content: str, content_type: str, url: str) -> Dict[str, Any]:
    """
    Extract metadata from the content based on its type.

    Args:
        content (str): The raw content of the page.
        content_type (str): The content type of the page.
        url (str): The URL of the page.

    Returns:
        dict: A dictionary containing the extracted metadata.
    """
    metadata: Dict[str, Any] = {
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
                logging.warning("Failed to parse schema.org data for %s", url)

    elif content_type.lower() == 'application/pdf':
        try:
            pdf_file = get_pdf_data(url)
            reader = PyPDF2.PdfReader(pdf_file)
            if reader.metadata:
                metadata.update(reader.metadata)
        except Exception as e:
            logging.error("Error extracting PDF metadata from %s: %s", url, str(e))

    return metadata

def extract_text_from_html(html: str) -> str:
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

        return text
    except Exception as e:
        logging.error("Error extracting text from HTML content: %s", str(e))
        raise

def extract_text_from_pdf(file_path_or_url: str) -> str:
    """
    Extract text content from a PDF file.

    Args:
        file_path_or_url (str): Local file path or URL of the PDF file

    Returns:
        str: Extracted text content as a string
    """
    pdf_file = None
    try:
        pdf_file = get_pdf_data(file_path_or_url)
        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        # Extract text from all pages
        text_content = "\n".join(page.extract_text() for page in pdf_reader.pages)

        return text_content.strip()

    except requests.RequestException as e:
        logging.error("Error fetching PDF from URL %s: %s", file_path_or_url, str(e))
        return f"Error fetching PDF: {str(e)}"
    except PyPDF2.errors.PdfReadError as e:
        logging.error("Error reading PDF %s: %s", file_path_or_url, str(e))
        return f"Error reading PDF: {str(e)}"
    except Exception as e:
        logging.error("Unexpected error processing PDF %s: %s", file_path_or_url, str(e))
        return f"Unexpected error: {str(e)}"
    finally:
        if pdf_file and not isinstance(pdf_file, io.BytesIO):
            pdf_file.close()

def is_dynamic_content(content: bytes) -> bool:
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
        logging.warning("Error in is_dynamic_content: %s", str(e))
        return True  # Assume dynamic if there's an error