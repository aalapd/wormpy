from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import logging

def setup_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def fetch_with_selenium(url):
    driver = setup_selenium()
    try:
        driver.get(url)
        content = driver.page_source
        content_type = driver.execute_script("return document.contentType;")
        return content, content_type
    except Exception as e:
        logging.error(f"Selenium error fetching {url}: {str(e)}")
        return None, None
    finally:
        driver.quit()