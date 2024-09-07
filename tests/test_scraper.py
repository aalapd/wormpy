import unittest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.website_scraper import scrape_website
from modules.processors.url_processor import normalize_url, is_suspicious_url, is_valid_url
from modules.processors.content_processor import extract_text_from_html, process_page

class TestScraper(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_file = os.path.join(self.temp_dir, "test_output.txt")

    def tearDown(self):
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
        os.rmdir(self.temp_dir)

    def test_normalize_url(self):
        self.assertEqual(normalize_url("http://example.com/page?query=1"), "http://example.com/page")
        self.assertEqual(normalize_url("https://example.com/page/"), "https://example.com/page")

    def test_is_suspicious_url(self):
        self.assertTrue(is_suspicious_url("http://example.com/image?itemId=123"))
        self.assertFalse(is_suspicious_url("http://example.com/page"))

    def test_is_valid_url(self):
        self.assertTrue(is_valid_url("http://example.com/page", "http://example.com"))
        self.assertFalse(is_valid_url("http://another-domain.com", "http://example.com"))

    def test_extract_text_from_html(self):
        html = "<html><body><h1>Title</h1><p>Content</p></body></html>"
        self.assertEqual(extract_text_from_html(html).strip(), "Title\nContent")

    @patch('modules.processors.content_processor.process_page')
    @patch('modules.processors.url_processor.extract_urls')
    def test_scrape_website_urls_only_html(self, mock_extract_urls, mock_process_page):
        mock_process_page.return_value = ("Sample content", "<html><body><a href='http://example.com/page1'>Link</a></body></html>")
        mock_extract_urls.return_value = ["http://example.com/page1"]

        base_url = "http://example.com"
        max_depth = 1
        scrape_website(base_url, max_depth, self.output_file, urls_only=True)
        
        with open(self.output_file, 'r') as f:
            content = f.read()
        
        self.assertIn("http://example.com/page1", content)
        self.assertNotIn("Sample content", content)

    @patch('modules.processors.content_processor.process_page')
    @patch('modules.processors.url_processor.extract_urls')
    def test_scrape_website_urls_only_pdf(self, mock_extract_urls, mock_process_page):
        mock_process_page.return_value = ("PDF content", b"%PDF-1.4 ... PDF content ...")
        mock_extract_urls.return_value = []

        base_url = "http://example.com/document.pdf"
        max_depth = 0
        scrape_website(base_url, max_depth, self.output_file, urls_only=True)
        
        with open(self.output_file, 'r') as f:
            content = f.read()
        
        self.assertIn("http://example.com/document.pdf", content)
        self.assertNotIn("PDF content", content)

    @patch('modules.processors.content_processor.process_page')
    @patch('modules.processors.url_processor.extract_urls')
    def test_scrape_website_with_content(self, mock_extract_urls, mock_process_page):
        mock_process_page.return_value = ("Sample content", "<html><body><a href='http://example.com/page1'>Link</a></body></html>")
        mock_extract_urls.return_value = ["http://example.com/page1"]

        base_url = "http://example.com"
        max_depth = 1
        scrape_website(base_url, max_depth, self.output_file, urls_only=False)
        
        with open(self.output_file, 'r') as f:
            content = f.read()
        
        self.assertIn("Sample content", content)

if __name__ == '__main__':
    unittest.main()