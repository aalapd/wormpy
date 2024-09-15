import logging
from .processors.url_processor import normalize_url, is_suspicious_url, extract_urls
from .processors.content_processor import process_page
from .file_handler import write_to_file
from .utils import is_image_content_type, is_valid_url

def scrape_website(base_url, max_depth, output_file, urls_only=False):
    all_discovered_urls = set()
    processed_urls = set()
    error_urls = set()  # New set to track URLs that resulted in errors
    urls_to_process = [(base_url, 0)]  # (url, depth)

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
            text_content, raw_content, content_type = process_page(current_url)

            if not urls_only:
                write_to_file(output_file, f"\n\n--- Content from {current_url} ---\n\n")
                write_to_file(output_file, text_content)

            processed_urls.add(normalized_url)
            all_discovered_urls.add(normalized_url)
            logging.info(f"Successfully processed {current_url}")

            new_urls = set(normalize_url(url) for url in extract_urls(raw_content, current_url, content_type) if is_valid_url(url, base_url))
            new_urls = new_urls - processed_urls - error_urls  # Remove already processed or errored URLs
            all_discovered_urls.update(new_urls)

            if depth < max_depth:
                urls_to_process.extend((url, depth + 1) for url in new_urls)

        except Exception as e:
            error_message = f"\n\nError processing {current_url}: {str(e)}\n\n"
            write_to_file(output_file, error_message)
            logging.error(f"Error processing {current_url}: {e}")
            error_urls.add(normalized_url)  # Add the URL to the error set

    if urls_only:
        for url in all_discovered_urls:
            write_to_file(output_file, f"{url}\n")

    return processed_urls

if __name__ == "__main__":
    # This code will only run if the script is executed directly (not imported)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    # Add any test code or function calls here