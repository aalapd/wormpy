"""
Module for tracking visited URLs and managing a common pool of URLs to be processed across all scrapers.
"""

import asyncio
from typing import Set, Optional
from collections import deque

from modules.utils.logger import get_logger
logging = get_logger(__name__)

class URLTracker:
    """
    A class to manage URL tracking and provide a common pool of URLs for scrapers.

    This class handles visited URL tracking, maintains a queue of URLs to be processed,
    and provides thread-safe operations for adding and retrieving URLs.

    Attributes:
        visited_urls (Set[str]): A set of URLs that have been visited.
        url_pool (deque): A queue of URLs to be processed.
        lock (asyncio.Lock): A lock for ensuring thread-safe operations.
    """

    def __init__(self):
        """Initialize the URLTracker."""
        self.visited_urls: Set[str] = set()
        self.url_pool: deque = deque()
        self.lock = asyncio.Lock()
        logging.debug("URL tracker initialized.")

    async def is_visited(self, url: str) -> bool:
        """
        Check if a URL has been visited.

        Args:
            url (str): The URL to check.

        Returns:
            bool: True if the URL has been visited, False otherwise.
        """
        return url in self.visited_urls

    async def mark_visited(self, url: str) -> None:
        """
        Mark a URL as visited.

        Args:
            url (str): The URL to mark as visited.
        """
        async with self.lock:
            self.visited_urls.add(url)
            logging.debug(f"Marked URL as visited: {url}")

    async def add_to_pool(self, url: str) -> None:
        """
        Add a URL to the processing pool if it hasn't been visited.

        Args:
            url (str): The URL to add to the pool.
        """
        if not await self.is_visited(url):
            async with self.lock:
                self.url_pool.append(url)
                logging.debug(f"Added URL to pool: {url}")

    async def get_next_url(self) -> Optional[str]:
        """
        Get the next URL from the pool to process.

        Returns:
            Optional[str]: The next URL to process, or None if the pool is empty.
        """
        async with self.lock:
            return self.url_pool.popleft() if self.url_pool else None

    async def add_bulk_to_pool(self, urls: Set[str]) -> None:
        """
        Add multiple URLs to the processing pool.

        Args:
            urls (Set[str]): A set of URLs to add to the pool.
        """
        async with self.lock:
            for url in urls:
                if url not in self.visited_urls:
                    self.url_pool.append(url)
            logging.info(f"Added {len(urls)} URLs to the pool.")

    async def get_pool_size(self) -> int:
        """
        Get the current size of the URL pool.

        Returns:
            int: The number of URLs in the pool.
        """
        return len(self.url_pool)

    async def get_visited_count(self) -> int:
        """
        Get the number of visited URLs.

        Returns:
            int: The number of visited URLs.
        """
        return len(self.visited_urls)

    async def is_pool_empty(self) -> bool:
        """
        Check if the URL pool is empty.

        Returns:
            bool: True if the pool is empty, False otherwise.
        """
        return len(self.url_pool) == 0

    async def return_url_to_pool(self, url: str) -> None:
        """
        Return a URL to the pool, typically used when processing fails.

        Args:
            url (str): The URL to return to the pool.
        """
        async with self.lock:
            self.url_pool.appendleft(url)
            logging.debug(f"Returned URL to pool: {url}")

    async def clear_pool(self) -> None:
        """Clear all URLs from the pool."""
        async with self.lock:
            self.url_pool.clear()
            logging.info("URL pool cleared.")

# Global instance of URLTracker
url_tracker = URLTracker()