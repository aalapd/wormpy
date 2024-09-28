import asyncio
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
import logging

class SeleniumDriver:
    def __init__(self):
        self.driver = None

    def setup_selenium(self):
        if self.driver is None:
            firefox_options = FirefoxOptions()
            #firefox_options.add_argument("--headless")  # Use headless mode if absolutely required; currently disabled because several websites block headless scraping.
            firefox_options.add_argument("--no-sandbox")
            firefox_options.add_argument("--disable-dev-shm-usage")

            service = FirefoxService(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=firefox_options)
            self.driver.minimize_window()
        return self.driver

    def quit_selenium(self):
        if self.driver is not None:
            self.driver.quit()
            self.driver = None

    async def fetch_with_selenium(self, url, timeout=30, scroll_pause=1, max_scrolls=10):
        """
        Fetch page content using Selenium for dynamic content.
        """
        driver = self.setup_selenium()
        try:
            await asyncio.get_event_loop().run_in_executor(None, driver.get, url)
            
            # Wait for the initial page load
            await asyncio.get_event_loop().run_in_executor(
                None, 
                WebDriverWait(driver, timeout).until,
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for the page to become interactive
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: WebDriverWait(driver, timeout).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
            )
            
            # Scroll to trigger lazy loading
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
                    break
                last_height = new_height
            
            # Wait for any remaining dynamic content
            await asyncio.sleep(2)
            
            # Check if there are any AJAX requests still pending
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
                None, driver.execute_script, "return document.contentType;"
            )
            return page_source, content_type
        except Exception as e:
            logging.error(f"Selenium error fetching {url}: {str(e)}")
            return None, None