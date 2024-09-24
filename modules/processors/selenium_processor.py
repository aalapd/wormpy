from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
import logging
import time

def setup_selenium():
    firefox_options = FirefoxOptions()
    firefox_options.add_argument("--headless")  # Use headless mode
    firefox_options.add_argument("--no-sandbox")  # Required for some environments
    firefox_options.add_argument("--disable-dev-shm-usage")
    
    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=firefox_options)
    return driver

def fetch_with_selenium(url, timeout=30):
    """
    Fetch page content using Selenium for dynamic content.

    Args:
        url (str): The URL to fetch.
        timeout (int): Maximum time to wait for page load.

    Returns:
        tuple: (page_source, content_type)
    """
    driver = setup_selenium()
    try:
        driver.minimize_window()
        driver.get(url)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        return driver.page_source, driver.execute_script("return document.contentType;")
    except Exception as e:
        logging.error(f"Selenium error fetching {url}: {str(e)}")
        return None, None
    finally:
        driver.quit()

def scroll_and_extract(url, max_scroll=10, scroll_pause=2):
    """
    Scroll through a page with infinite loading and extract content.

    Args:
        url (str): The URL to scrape.
        max_scroll (int): Maximum number of scroll attempts.
        scroll_pause (int): Time to pause between scrolls.

    Returns:
        tuple: (page_source, content_type)
    """
    driver = setup_selenium()
    try:
        driver.get(url)
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(max_scroll):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        return driver.page_source, driver.execute_script("return document.contentType;")
    except Exception as e:
        logging.error(f"Error scrolling and extracting from {url}: {str(e)}")
        return None, None
    finally:
        driver.quit()
