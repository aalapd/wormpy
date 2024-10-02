# selenium_processor.py

import os
import sys
import asyncio
import requests
import zipfile
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from config import MAX_RETRIES

from modules.utils.logger import get_logger
logger = get_logger(__name__)

GECKODRIVER_BASE_URL = "https://github.com/mozilla/geckodriver/releases/download/v0.35.0/"
GECKODRIVER_REPO_URL = "https://github.com/mozilla/geckodriver/releases"

class SeleniumDriver:
    """A class to manage Selenium WebDriver for Firefox."""

    def __init__(self):
        """Initialize SeleniumDriver with driver set to None."""
        self.driver = None
        self.driver_path = self._get_driver_path()

    def _get_driver_path(self) -> str:
        """
        Get the path for the geckodriver executable.

        Returns:
            str: Path to the geckodriver executable.
        """
        base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, 'drivers', 'geckodriver')

    def _download_driver(self) -> bool:
        """
        Download the geckodriver if it doesn't exist.

        Returns:
            bool: True if download was successful, False otherwise.
        """
        if sys.platform.startswith('win'):
            driver_url = f"{GECKODRIVER_BASE_URL}geckodriver-v0.35.0-win64.zip"
            driver_name = "geckodriver.exe"
        elif sys.platform.startswith('linux'):
            driver_url = f"{GECKODRIVER_BASE_URL}geckodriver-v0.35.0-linux64.tar.gz"
            driver_name = "geckodriver"
        elif sys.platform.startswith('darwin'):
            driver_url = f"{GECKODRIVER_BASE_URL}geckodriver-v0.35.0-macos.tar.gz"
            driver_name = "geckodriver"
        else:
            logger.error("Unsupported operating system")
            return False

        try:
            response = requests.get(driver_url)
            response.raise_for_status()

            driver_dir = os.path.dirname(self.driver_path)
            os.makedirs(driver_dir, exist_ok=True)

            if driver_url.endswith('.zip'):
                with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
                    zip_ref.extract(driver_name, path=driver_dir)
            else:
                import tarfile
                with tarfile.open(fileobj=BytesIO(response.content), mode="r:gz") as tar:
                    tar.extract(driver_name, path=driver_dir)

            # Rename the extracted file if necessary
            extracted_path = os.path.join(driver_dir, driver_name)
            if extracted_path != self.driver_path:
                os.rename(extracted_path, self.driver_path)

            # Set executable permissions
            if not sys.platform.startswith('win'):
                os.chmod(self.driver_path, 0o755)

            logger.info(f"Successfully downloaded geckodriver to {self.driver_path}")
            return True
        except Exception as e:
            logger.error(f"Error downloading geckodriver: {str(e)}")
            logger.error(f"Please download geckodriver manually from {GECKODRIVER_REPO_URL} "
                         f"and save it to {self.driver_path}")
            return False

    def setup_selenium(self) -> webdriver.Firefox:
        """
        Set up and return a Selenium WebDriver for Firefox.

        Returns:
            webdriver.Firefox: Configured Firefox WebDriver.
        """
        if self.driver is None:
            if not os.path.exists(self.driver_path):
                if not self._download_driver():
                    raise Exception("Failed to set up geckodriver")

            firefox_options = FirefoxOptions()
            firefox_options.add_argument("--no-sandbox")
            firefox_options.add_argument("--disable-dev-shm-usage")

            service = FirefoxService(executable_path=self.driver_path)
            self.driver = webdriver.Firefox(service=service, options=firefox_options)
            self.driver.minimize_window()
        return self.driver

    def quit_selenium(self) -> None:
        """Quit the Selenium WebDriver if it exists."""
        if self.driver is not None:
            self.driver.quit()
            self.driver = None

    async def fetch_with_selenium(self, url: str, timeout: int = 30, scroll_pause: int = 1, max_scrolls: int = 10) -> tuple:
        """
        Fetch page content using Selenium for dynamic content.

        Args:
            url (str): The URL to fetch.
            timeout (int): Maximum time to wait for page load.
            scroll_pause (int): Time to pause between scrolls.
            max_scrolls (int): Maximum number of scroll attempts.

        Returns:
            tuple: (page_source, content_type, discovered_urls)
        """
        driver = self.setup_selenium()
        for attempt in range(MAX_RETRIES):
            try:
                await asyncio.get_event_loop().run_in_executor(None, driver.get, url)
                
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    WebDriverWait(driver, timeout).until,
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: WebDriverWait(driver, timeout).until(
                        lambda d: d.execute_script('return document.readyState') == 'complete'
                    )
                )

                last_height = await asyncio.get_event_loop().run_in_executor(
                    None, driver.execute_script, "return document.body.scrollHeight"
                )
                for _ in range(max_scrolls):
                    await asyncio.get_event_loop().run_in_executor(
                        None, driver.execute_script, "window.scrollTo(0, document.body.scrollHeight);"
                    )
                    await asyncio.sleep(scroll_pause)
                    new_height = await asyncio.get_event_loop().run_in_executor(
                        None, driver.execute_script, "return document.body.scrollHeight"
                    )
                    if new_height == last_height:
                        try:
                            load_more_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Load More')]")
                            await asyncio.get_event_loop().run_in_executor(None, load_more_button.click)
                            await asyncio.sleep(scroll_pause)
                            continue
                        except Exception as e:
                            logger.debug(f"No 'Load More' button found or error clicking it: {str(e)}")
                            break
                    last_height = new_height

                await asyncio.sleep(5)

                is_jquery_active = await asyncio.get_event_loop().run_in_executor(
                    None, driver.execute_script, "return window.jQuery && jQuery.active > 0"
                )
                if is_jquery_active:
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: WebDriverWait(driver, timeout).until(
                            lambda d: d.execute_script("return window.jQuery && jQuery.active == 0")
                        )
                    )

                page_source = await asyncio.get_event_loop().run_in_executor(None, lambda: driver.page_source)
                content_type = await asyncio.get_event_loop().run_in_executor(
                    None, driver.execute_script, "return document.contentType || 'text/html';"
                )
                
                if isinstance(page_source, bytes):
                    page_source = page_source.decode('utf-8', errors='ignore')
                elif page_source is None:
                    logger.error(f"Failed to retrieve page source for {url}")
                    return None, None, []

                discovered_urls = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: list(set(filter(None, [element.get_attribute('href') for element in driver.find_elements(By.TAG_NAME, 'a')])))
                )

                return page_source, content_type, discovered_urls
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Attempt {attempt + 1} failed. Retrying...")
                    self.quit_selenium()  # Close the current driver
                    self.driver = None    # Reset the driver
                    await asyncio.sleep(3)  # Wait before retrying
                else:
                    logger.error(f"All attempts failed for {url}: {str(e)}")
                    return None, None, []