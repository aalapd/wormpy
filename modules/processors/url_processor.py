"""
URL processing module for web scraping operations.

This module provides utility functions for handling and processing URLs
in the context of web scraping. It includes functions for URL validation,
normalization, and extraction from web content.

Functions:
    get_domain(url: str) -> str
    is_valid_url(url: str, base_url: str) -> bool
    normalize_url(url: str) -> str
    is_suspicious_url(url: str) -> bool
    is_image_content_type(url: str) -> bool
    is_pdf_url(url: str) -> bool
    extract_urls(content: str, base_url: str, content_type: str = 'text/html') -> set
"""

import requests
import logging
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
from ..utils import is_image_file_extension

def get_domain(url: str) -> str:
    """
    Extract the domain from a given URL.

    Args:
        url (str): The URL to extract the domain from.

    Returns:
        str: The extracted domain.
    """
    parsed_url = urlparse(url)
    return parsed_url.netloc

def is_valid_url(url: str, base_url: str) -> bool:
    """
    Check if a URL is valid and belongs to the same domain as the base URL.

    Args:
        url (str): The URL to check.
        base_url (str): The base URL to compare against.

    Returns:
        bool: True if the URL is valid and belongs to the same domain, False otherwise.
    """
    parsed_url = urlparse(url)
    parsed_base = urlparse(base_url)
    return (parsed_url.netloc == parsed_base.netloc and not is_image_file_extension(parsed_url.path))

def normalize_url(url: str) -> str:
    """
    Normalize a URL by removing trailing slashes and standardizing the scheme.

    Args:
        url (str): The URL to normalize.

    Returns:
        str: The normalized URL.
    """
    parsed = urlparse(url.lower())
    scheme = parsed.scheme or 'https'  # Default to https if no scheme is provided
    path = parsed.path.rstrip('/')  # Remove trailing slash from path
    return f"{scheme}://{parsed.netloc}{path}"

def url_matches_base(url: str, base_url: str) -> bool:
    """
    Check if a URL matches the base URL.

    Args:
        url (str): The URL to check.
        base_url (str): The base URL to compare against.

    Returns:
        bool: True if the URL matches the base URL, False otherwise.
    """
    parsed_url = urlparse(url)
    parsed_base = urlparse(base_url)
    return parsed_url.netloc == parsed_base.netloc and parsed_url.path.startswith(parsed_base.path)


def is_suspicious_url(url: str) -> bool:
    """
    Check if a URL is suspicious based on query parameters or file extension.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL is suspicious, False otherwise.
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    suspicious_params = ['itemId', 'imageId', 'galleryId']
    return any(param in query_params for param in suspicious_params) or is_image_file_extension(parsed_url.path)

def is_image_content_type(url: str) -> bool:
    """
    Check if a URL points to an image based on its content type.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL points to an image, False otherwise.
    """
    try:
        response = requests.head(url)
        content_type = response.headers.get('Content-Type', '')
        return content_type.startswith('image/')
    except requests.RequestException:
        logging.error(f"Error checking content type for {url}")
        return False

def is_pdf_url(url: str) -> bool:
    """
    Check if a URL points to a PDF file.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL likely points to a PDF, False otherwise.
    """
    try:
        if url.lower().endswith('.pdf'):
            return True
        response = requests.head(url, allow_redirects=True)
        return 'application/pdf' in response.headers.get('Content-Type', '').lower()
    except requests.RequestException:
        logging.warning(f"Error checking content type for {url}")
        return False

def extract_urls(content: str, base_url: str, content_type: str = 'text/html') -> set:
    """
    Extract URLs from the given content.

    Args:
        content (str): The content to extract URLs from.
        base_url (str): The base URL for resolving relative URLs.
        content_type (str, optional): The content type. Defaults to 'text/html'.

    Returns:
        set: A set of extracted URLs.
    """
    try:
        if content_type.lower().startswith('text/html'):
            soup = BeautifulSoup(content, 'html.parser')
            return {urljoin(base_url, a['href']) for a in soup.find_all('a', href=True)}
        elif content_type.lower() == 'application/pdf':
            logging.info(f"Skipping URL extraction for PDF content: {base_url}")
            return set()
        else:
            logging.warning(f"Unsupported content type for URL extraction: {content_type}")
            return set()
    except Exception as e:
        logging.error(f"Error extracting URLs from content: {e}")
        return set()