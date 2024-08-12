from content_extractor import process_page
from file_handler import write_to_file
from utils import is_valid_url
import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests

def process_urls(base_url, output_file, max_depth):
    processed_urls = set()
    urls_to_process = [(base_url, 0)]  # (url, depth)

    while urls_to_process:
        current_url, depth = urls_to_process.pop(0)
        
        if current_url in processed_urls or depth > max_depth:
            continue

        logging.info(f"Processing URL (depth {depth}): {current_url}")
        try:
            content = process_page(current_url)
            write_to_file(output_file, f"\n\n--- Content from {current_url} ---\n\n")
            write_to_file(output_file, content)
            processed_urls.add(current_url)
            logging.info(f"Successfully processed {current_url}")

            if depth < max_depth:
                new_urls = extract_links(current_url, base_url)
                urls_to_process.extend((url, depth + 1) for url in new_urls if url not in processed_urls)
        except Exception as e:
            error_message = f"\n\nError processing {current_url}: {str(e)}\n\n"
            write_to_file(output_file, error_message)
            logging.error(f"Error processing {current_url}: {e}")

    return processed_urls

def extract_links(url, base_url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links = {urljoin(url, a['href']) for a in soup.find_all('a', href=True) 
                 if is_valid_url(urljoin(url, a['href']), base_url)}
        return links
    except requests.RequestException:
        logging.error(f"Error fetching HTML from {url}")
        return set()

