import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
from .utils import is_valid_url
import logging

def get_all_urls(base_url):
    sitemap_urls = parse_sitemap(base_url)
    return sitemap_urls

def parse_sitemap(base_url):
    sitemap = fetch_sitemap(base_url)
    if sitemap:
        return parse_sitemap_xml(sitemap, base_url)
    else:
        return set()

def fetch_sitemap(base_url):
    sitemap_locations = [
        'sitemap.xml', 'sitemap_index.xml', 'sitemap/', 'sitemap1.xml',
        'post-sitemap.xml', 'page-sitemap.xml', 'sitemapindex.xml',
        'sitemap-index.xml', 'wp-sitemap.xml'
    ]
    
    for location in sitemap_locations:
        full_url = urljoin(base_url, location)
        try:
            response = requests.get(full_url)
            response.raise_for_status()
            if 'xml' in response.headers.get('Content-Type', ''):
                logging.info(f"Sitemap fetched from {full_url}")
                return response.text
        except requests.RequestException:
            continue
    
    logging.warning("No sitemap found.")
    return None

def parse_sitemap_xml(xml_content, base_url):
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
        logging.error("Error parsing XML.")
        return set()

def parse_sub_sitemap(url, base_url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        root = ET.fromstring(response.text)
        return {elem.text.strip() for elem in root.iter() 
                if 'loc' in elem.tag and is_valid_url(elem.text.strip(), base_url)}
    except (requests.RequestException, ET.ParseError):
        logging.error(f"Error parsing sub-sitemap {url}")
        return set()