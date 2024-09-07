import requests
import logging
from urllib.parse import urlparse

def is_valid_url(url, base_url):
    parsed_url = urlparse(url)
    parsed_base = urlparse(base_url)
    return (parsed_url.netloc == parsed_base.netloc and
            not is_image_file_extension(parsed_url.path))

def is_image_file_extension(path):
    image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'mp3', 'mp4', 'wav', 'avi', 'mov']
    return path.split('.')[-1].lower() in image_extensions

def is_image_content_type(url):
    try:
        response = requests.head(url)
        content_type = response.headers.get('Content-Type', '')
        return content_type.startswith('image/')
    except requests.RequestException:
        logging.error(f"Error checking content type for {url}")
        return False