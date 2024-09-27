import logging
from .processors.url_processor import normalize_url, is_suspicious_url, extract_urls, is_valid_url
from .processors.content_processor import process_page
from .utils import is_image_content_type

def scrape_website(base_url, max_depth, force_scrape_method):
    all_discovered_urls = set()
    processed_urls = set()
    error_urls = set()
    urls_to_process = [(base_url, 0)]  # (url, depth)
    results = {}

    while urls_to_process:
        current_url, depth = urls_to_process.pop(0)
        normalized_url = normalize_url(current_url)
        
        if normalized_url in processed_urls or normalized_url in error_urls:
            continue

        logging.info(f"Processing URL (depth {depth}): {current_url}")

        if is_suspicious_url(current_url):
            if is_image_content_type(current_url):
                logging.info(f"Skipping image URL: {current_url}")
                continue

        try:
            text_content, raw_content, content_type, metadata = process_page(current_url, force_scrape_method)
            
            new_urls = set(normalize_url(url) for url in extract_urls(raw_content, current_url, content_type) if is_valid_url(url, base_url))
            new_urls = {url for url in new_urls if url.startswith(base_url)}  # Filter URLs to start with base_url
            new_urls = new_urls - processed_urls - error_urls  # Remove already processed or errored URLs
            sorted_new_urls = sorted(list(new_urls))  # Sort the new URLs

            results[normalized_url] = {
                'metadata': metadata,
                'content': text_content,
                'discovered_urls': list(sorted_new_urls),
            }
            
            processed_urls.add(normalized_url)
            all_discovered_urls.add(normalized_url)
            all_discovered_urls.update(sorted_new_urls)
            logging.info(f"Successfully processed {current_url}")

            if depth < max_depth:
                urls_to_process.extend((url, depth + 1) for url in new_urls)

        except Exception as e:
            error_message = f"Error processing {current_url}: {str(e)}"
            logging.error(error_message)
            results[normalized_url] = {
                'content': error_message,
            }
            error_urls.add(normalized_url)

    return results

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    # Add any test code or function calls here