import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
import logging

def fetch_sitemap(url):
    try:
        logging.info(f"Attempting to fetch sitemap index from {url}")
        response = requests.get(urljoin(url, 'sitemap_index.xml'))
        response.raise_for_status()
        logging.info("Sitemap index fetched successfully")
        return response.text
    except requests.RequestException as e:
        logging.warning(f"Failed to fetch sitemap index: {e}")
        try:
            logging.info(f"Attempting to fetch sitemap from {url}")
            response = requests.get(urljoin(url, 'sitemap.xml'))
            response.raise_for_status()
            logging.info("Sitemap fetched successfully")
            return response.text
        except requests.RequestException as e:
            logging.error(f"Failed to fetch sitemap: {e}")
            logging.info("Falling back to HTML parsing.")
            return None

def parse_sitemap(xml_content, base_url):
    if xml_content is None:
        return parse_html_for_links(base_url)
    
    try:
        root = ET.fromstring(xml_content)
        urls = []
        for elem in root.iter():
            if 'loc' in elem.tag:
                url = elem.text.strip()
                if url.endswith('.xml'):
                    urls.extend(parse_sub_sitemap(url))
                else:
                    urls.append(url)
        logging.info("Sitemap parsed successfully")
        return urls
    except ET.ParseError as e:
        logging.error(f"Error parsing XML: {e}")
        logging.info("Falling back to HTML parsing.")
        return parse_html_for_links(base_url)

def parse_sub_sitemap(url):
    try:
        logging.info(f"Attempting to fetch and parse sub-sitemap from {url}")
        response = requests.get(url)
        response.raise_for_status()
        root = ET.fromstring(response.text)
        return [elem.text.strip() for elem in root.iter() if 'loc' in elem.tag]
    except (requests.RequestException, ET.ParseError) as e:
        logging.error(f"Error parsing sub-sitemap {url}: {e}")
        return []

def get_all_urls(base_url):
    sitemap = fetch_sitemap(base_url)
    return parse_sitemap(sitemap, base_url)

def parse_html_for_links(url):
    try:
        logging.info(f"Attempting to fetch HTML content from {url}")
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links = [urljoin(url, a['href']) for a in soup.find_all('a', href=True)]
        unique_links = list(set(links))  # Remove duplicates
        logging.info(f"Found {len(unique_links)} unique links in HTML content")
        return unique_links
    except requests.RequestException as e:
        logging.error(f"Error fetching HTML from {url}: {e}")
        return []
