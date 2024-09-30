"""
Module for tracking visited URLs across all scrapers.
"""

import asyncio
import logging
from typing import Set

class URLTracker:
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.lock = asyncio.Lock()
        logging.info("URL tracker initialized.")

    async def is_visited(self, url: str) -> bool:
        """Check if a URL has been visited."""
        return url in self.visited_urls

    async def mark_visited(self, url: str) -> None:
        """Mark a URL as visited."""
        async with self.lock:
            self.visited_urls.add(url)

    async def get_unvisited(self, urls: Set[str]) -> Set[str]:
        """Get a set of unvisited URLs from a given set of URLs."""
        return urls - self.visited_urls

# Global instance of URLTracker
url_tracker = URLTracker()