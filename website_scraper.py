import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from content_extractor import extract_text_from_html
from file_handler import write_to_file
from utils import is_valid_url, is_image_file_extension, get_domain

def is_suspicious_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    suspicious_params = ['itemId', 'imageId', 'galleryId']
    return any(param in query_params for param in suspicious_params) or is_image_file_extension(parsed_url.path)

def is_image_content_type(url):
    try:
        response = requests.head(url)
        content_type = response.headers.get('Content-Type', '')
        return content_type.startswith('image/')
    except requests.RequestException:
        logging.error(f"Error checking content type for {url}")
        return False

def is_image_heavy_page(html_content, text_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    view_fullsize_count = text_content.lower().count("view fullsize")
    
    # Calculate text-to-HTML ratio
    text_length = len(text_content)
    html_length = len(html_content)
    text_to_html_ratio = text_length / html_length if html_length > 0 else 0
    
    return view_fullsize_count >= 5 or text_to_html_ratio < 0.1

def normalize_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

def scrape_website(base_url, max_depth, output_file, urls_only=False):
    all_discovered_urls = set()
    processed_urls = set()
    urls_to_process = [(base_url, 0)]  # (url, depth)

    while urls_to_process:
        current_url, depth = urls_to_process.pop(0)
        normalized_url = normalize_url(current_url)
        
        if normalized_url in processed_urls:
            continue

        logging.info(f"Processing URL (depth {depth}): {current_url}")

        if is_suspicious_url(current_url):
            if is_image_content_type(current_url):
                logging.info(f"Skipping image URL: {current_url}")
                continue

        try:
            response = requests.get(current_url)
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')

            if not urls_only:
                text_content = extract_text_from_html(html_content)
                write_to_file(output_file, f"\n\n--- Content from {current_url} ---\n\n")
                write_to_file(output_file, text_content)

            processed_urls.add(current_url)
            all_discovered_urls.add(current_url)
            logging.info(f"Successfully processed {current_url}")

            new_urls = {urljoin(current_url, a['href']) for a in soup.find_all('a', href=True) 
                        if is_valid_url(urljoin(current_url, a['href']), base_url)}
            all_discovered_urls.update(new_urls)

            if depth < max_depth:
                urls_to_process.extend((url, depth + 1) for url in new_urls if url not in processed_urls)

        except Exception as e:
            error_message = f"\n\nError processing {current_url}: {str(e)}\n\n"
            write_to_file(output_file, error_message)
            logging.error(f"Error processing {current_url}: {e}")

    if urls_only:
        for url in all_discovered_urls:
            write_to_file(output_file, f"{url}\n")

    return processed_urls

if __name__ == "__main__":
    # This code will only run if the script is executed directly (not imported)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    # Add any test code or function calls here