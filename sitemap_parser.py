import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import logging

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
    
    logging.warning("No sitemap found. Falling back to HTML parsing.")
    return None

def parse_sitemap(xml_content, base_url):
    if xml_content is None:
        return parse_html_for_links(base_url)
    
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
        return list(urls)
    except ET.ParseError:
        logging.error("Error parsing XML. Falling back to HTML parsing.")
        return parse_html_for_links(base_url)

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

def get_all_urls(base_url):
    sitemap = fetch_sitemap(base_url)
    return parse_sitemap(sitemap, base_url)

def parse_html_for_links(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links = {urljoin(url, a['href']) for a in soup.find_all('a', href=True) 
                 if is_valid_url(urljoin(url, a['href']), url)}
        logging.info(f"Found {len(links)} unique links in HTML content")
        return list(links)
    except requests.RequestException:
        logging.error(f"Error fetching HTML from {url}")
        return []

def is_valid_url(url, base_url):
    parsed_url = urlparse(url)
    parsed_base = urlparse(base_url)
    return (parsed_url.netloc == parsed_base.netloc and
            parsed_url.path.split('.')[-1].lower() not in 
            ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'mp3', 'mp4', 'wav', 'avi', 'mov'])