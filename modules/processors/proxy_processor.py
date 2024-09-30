# proxy_processor.py

import aiohttp
import asyncio
import logging
from typing import List, Dict, Optional
import random
import time
from config import PROXY_TEST_URL, MAX_PROXIES, PROXY_TIMEOUT, PROXY_REFRESH_THRESHOLD, HEADERS, COUNTRY, SSL, ANONYMITY


PROXY_API_URL = f"https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country={COUNTRY}&ssl={SSL}&anonymity={ANONYMITY}"

class ProxyProcessor:
    """
    A class to manage fetching, testing, and rotating proxies for web scraping.
    """

    def __init__(self):
        """Initialize the ProxyProcessor."""
        self.proxies: List[Dict[str, any]] = []
        self.current_index: int = 0
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.proxy_api_url: str = PROXY_API_URL
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> None:
        """Initialize the aiohttp session and refresh proxies."""
        self.session = aiohttp.ClientSession(headers=HEADERS)
        await self.refresh_proxies()

    async def fetch_proxies(self) -> List[str]:
        """
        Fetch new proxy IPs from the API.

        Returns:
            List[str]: A list of proxy addresses.
        """
        try:
            async with self.session.get(self.proxy_api_url) as response:
                response.raise_for_status()
                data = await response.json()
                return [f"{proxy['ip']}:{proxy['port']}" for proxy in data]
        except aiohttp.ClientError as e:
            self.logger.error(f"Error fetching proxies: {str(e)}")
            return []

    async def test_proxy(self, proxy: str) -> Dict[str, any]:
        """
        Test a single proxy.

        Args:
            proxy (str): The proxy address to test.

        Returns:
            Dict[str, any]: A dictionary with proxy details and test results.
        """
        start_time = time.time()
        try:
            async with self.session.get(PROXY_TEST_URL, proxy=f"http://{proxy}", timeout=PROXY_TIMEOUT) as response:
                if response.status == 200:
                    content = await response.json()
                    end_time = time.time()
                    return {
                        "proxy": proxy,
                        "status": "working",
                        "response_time": end_time - start_time,
                        "ip": content.get("origin")
                    }
        except Exception as e:
            self.logger.debug(f"Proxy {proxy} failed: {str(e)}")
        return {"proxy": proxy, "status": "not_working"}

    async def test_proxies(self, proxies: List[str]) -> List[Dict[str, any]]:
        """
        Test multiple proxies in parallel.

        Args:
            proxies (List[str]): A list of proxy addresses to test.

        Returns:
            List[Dict[str, any]]: A list of dictionaries with proxy details and test results.
        """
        tasks = [self.test_proxy(proxy) for proxy in proxies]
        return await asyncio.gather(*tasks)

    async def refresh_proxies(self) -> None:
        """Fetch new proxies, test them, and update the proxy list."""
        new_proxies = await self.fetch_proxies()
        test_results = await self.test_proxies(new_proxies)
        working_proxies = [proxy for proxy in test_results if proxy["status"] == "working"]
        working_proxies.sort(key=lambda x: x["response_time"])

        self.proxies = working_proxies[:MAX_PROXIES]
        self.current_index = 0
        self.logger.info(f"Refreshed proxy list. Working proxies: {len(self.proxies)}")

    def get_proxy(self) -> Optional[str]:
        """
        Get the next working proxy from the rotation.

        Returns:
            Optional[str]: A proxy address or None if no proxies are available.
        """
        if not self.proxies:
            self.logger.warning("No working proxies available.")
            return None

        proxy = self.proxies[self.current_index]["proxy"]
        self.current_index = (self.current_index + 1) % len(self.proxies)

        if self.current_index == 0 and len(self.proxies) < PROXY_REFRESH_THRESHOLD:
            asyncio.create_task(self.refresh_proxies())

        return proxy

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()

    def __del__(self):
        """Ensure the aiohttp session is closed on object deletion."""
        if self.session and not self.session.closed:
            asyncio.get_event_loop().run_until_complete(self.close())

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()