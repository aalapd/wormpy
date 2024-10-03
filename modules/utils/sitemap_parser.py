# sitemap_parser.py

import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
from typing import Set, Optional
from ..processors.url_processor import is_valid_url
from modules.utils.logger import get_logger

logger = get_logger(__name__)

def get_all_urls(base_url: str) -> Set[str]:
    """
    Get all URLs from the sitemap of the given base URL.

    Args:
        base_url (str): The base URL of the website.

    Returns:
        Set[str]: A set of all URLs found in the sitemap.
    """
    return sorted(set(parse_sitemap(base_url)))

def parse_sitemap(base_url: str) -> Set[str]:
    """
    Parse the sitemap of the given base URL.

    Args:
        base_url (str): The base URL of the website.

    Returns:
        Set[str]: A set of URLs found in the sitemap.
    """
    sitemap_content = fetch_sitemap(base_url)
    if sitemap_content:
        return parse_sitemap_xml(sitemap_content, base_url)
    return set()

def fetch_sitemap(base_url: str) -> Optional[str]:
    """
    Fetch the sitemap content from various possible locations.

    Args:
        base_url (str): The base URL of the website.

    Returns:
        Optional[str]: The content of the sitemap if found, None otherwise.
    """
    sitemap_locations = [
        'sitemap.xml', 'sitemap_index.xml', 'sitemap/', 'sitemap1.xml',
        'post-sitemap.xml', 'page-sitemap.xml', 'sitemapindex.xml',
        'sitemap-index.xml', 'wp-sitemap.xml'
    ]
    
    for location in sitemap_locations:
        full_url = urljoin(base_url, location)
        try:
            response = requests.get(full_url, timeout=10)
            response.raise_for_status()
            if 'xml' in response.headers.get('Content-Type', ''):
                logger.info(f"Sitemap fetched from {full_url}")
                return response.text
        except requests.RequestException as e:
            logger.debug(f"Failed to fetch sitemap from {full_url}: {str(e)}")
    
    logger.warning("No sitemap found.")
    return None

def parse_sitemap_xml(xml_content: str, base_url: str) -> Set[str]:
    """
    Parse the XML content of a sitemap.

    Args:
        xml_content (str): The XML content of the sitemap.
        base_url (str): The base URL of the website.

    Returns:
        Set[str]: A set of URLs found in the sitemap.
    """
    try:
        root = ET.fromstring(xml_content)
        urls = set()
        for elem in root.iter():
            if 'loc' in elem.tag:
                url = elem.text.strip()
                if url.endswith('.xml'):
                    urls.update(parse_sub_sitemap(url, base_url))
                elif is_valid_url(url, base_url):
                    urls.add(url)
        return urls
    except ET.ParseError:
        logger.error("Error parsing XML content.")
        return set()

def parse_sub_sitemap(url: str, base_url: str) -> Set[str]:
    """
    Parse a sub-sitemap referenced in the main sitemap.

    Args:
        url (str): The URL of the sub-sitemap.
        base_url (str): The base URL of the website.

    Returns:
        Set[str]: A set of URLs found in the sub-sitemap.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.text)
        return {elem.text.strip() for elem in root.iter() 
                if 'loc' in elem.tag and is_valid_url(elem.text.strip(), base_url)}
    except (requests.RequestException, ET.ParseError) as e:
        logger.error(f"Error parsing sub-sitemap {url}: {str(e)}")
        return set()