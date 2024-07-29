import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
import logging

import requests
from urllib.parse import urljoin
import logging

def fetch_sitemap(url, max_redirects=5):
    sitemap_locations = [
        'sitemap.xml',
        'sitemap_index.xml',
        'sitemap/',
        'sitemap1.xml',
        'post-sitemap.xml',
        'page-sitemap.xml',
        'sitemapindex.xml',
        'sitemap-index.xml',
        'wp-sitemap.xml'
    ]
    
    with requests.Session() as session:
        session.max_redirects = max_redirects
        
        for location in sitemap_locations:
            try:
                full_url = urljoin(url, location)
                logging.info(f"Attempting to fetch sitemap from {full_url}")
                response = session.get(full_url, allow_redirects=True)
                response.raise_for_status()
                logging.info(f"Sitemap fetched successfully from {response.url}")
                return response.text
            except requests.RequestException as e:
                logging.warning(f"Failed to fetch sitemap from {full_url}: {e}")
        
        # If we've exhausted all options, try to fetch the root URL
        try:
            logging.info(f"Attempting to fetch root URL {url}")
            response = session.get(url, allow_redirects=True)
            response.raise_for_status()
            if 'text/xml' in response.headers.get('Content-Type', ''):
                logging.info(f"Sitemap found at root URL {response.url}")
                return response.text
        except requests.RequestException as e:
            logging.warning(f"Failed to fetch root URL {url}: {e}")

    logging.error("Failed to fetch any sitemap. Falling back to HTML parsing.")
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
