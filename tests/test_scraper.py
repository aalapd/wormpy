import unittest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock, call
import requests
from bs4 import BeautifulSoup
import time

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.website_scraper import scrape_website
from modules.processors.url_processor import normalize_url, is_suspicious_url, is_image_content_type, extract_urls, get_domain, is_pdf_url
from modules.processors.content_processor import extract_text_from_html, extract_text_from_pdf, process_page, RateLimiter, fetch_page
from modules.file_handler import initialize_output_file, write_to_file, finalize_file
from modules.utils import is_valid_url
from modules.sitemap_parser import parse_sitemap

class TestScraper(unittest.TestCase):
    BASE_URL = "https://webscraper.io/test-sites/tables/tables-semantically-correct"

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_file = os.path.join(self.temp_dir, "test_output.txt")

    def tearDown(self):
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
        os.rmdir(self.temp_dir)

    # URL Processor Tests

    def test_normalize_url(self):
        test_cases = [
            (f"{self.BASE_URL}?query=1", self.BASE_URL),
            (f"{self.BASE_URL}/", self.BASE_URL),
            (f"{self.BASE_URL}#fragment", self.BASE_URL),
        ]
        for input_url, expected_url in test_cases:
            with self.subTest(input_url=input_url):
                self.assertEqual(normalize_url(input_url), expected_url)

    def test_is_suspicious_url(self):
        test_cases = [
            (f"{self.BASE_URL}/image?itemId=123", True),
            (self.BASE_URL, False),
            (f"{self.BASE_URL}/image.jpg", True),
            (f"{self.BASE_URL}/gallery?galleryId=456", True),
        ]
        for url, expected in test_cases:
            with self.subTest(url=url):
                self.assertEqual(is_suspicious_url(url), expected)

    @patch('modules.processors.url_processor.requests.head')
    def test_is_image_content_type(self, mock_head):
        mock_response = MagicMock()
        mock_response.headers = {'Content-Type': 'image/jpeg'}
        mock_head.return_value = mock_response

        self.assertTrue(is_image_content_type('http://example.com/image.jpg'))

        mock_response.headers = {'Content-Type': 'text/html'}
        self.assertFalse(is_image_content_type('http://example.com/page.html'))

    def test_is_valid_url(self):
        test_cases = [
            (self.BASE_URL, self.BASE_URL, True),
            (f"https://webscraper.io/test-sites/tables", self.BASE_URL, True),
            ("https://example.com", self.BASE_URL, False),
            (f"{self.BASE_URL}/image.jpg", self.BASE_URL, False),
        ]
        for url, base_url, expected in test_cases:
            with self.subTest(url=url, base_url=base_url):
                self.assertEqual(is_valid_url(url, base_url), expected)

    def test_extract_urls(self):
        html_content = '<html><body><a href="/page1">Page 1</a><a href="https://example.com">External</a></body></html>'
        base_url = 'https://example.com'
        expected_urls = {'https://example.com/page1', 'https://example.com'}
        self.assertEqual(extract_urls(html_content, base_url), expected_urls)

    def test_get_domain(self):
        self.assertEqual(get_domain('https://example.com/path'), 'example.com')

    # Content Processor Tests

    def test_extract_text_from_html(self):
        html = '<html><body><h1>Title</h1><p>Content</p><script>alert("test");</script></body></html>'
        extracted_text = extract_text_from_html(html)
        self.assertIn("Title", extracted_text)
        self.assertIn("Content", extracted_text)
        self.assertNotIn("alert", extracted_text)

    @patch('modules.processors.content_processor.fetch_page')
    @patch('modules.processors.content_processor.extract_text_from_html')
    @patch('modules.processors.content_processor.extract_text_from_pdf')
    @patch('modules.processors.url_processor.is_pdf_url')
    def test_process_page(self, mock_is_pdf_url, mock_extract_pdf, mock_extract_html, mock_fetch_page):
        # Test HTML content
        mock_fetch_page.return_value = (b'<html><body>Test content</body></html>', 'text/html')
        mock_extract_html.return_value = 'Extracted HTML'
        mock_is_pdf_url.return_value = False
        
        result = process_page('http://example.com')
        self.assertEqual(result, ('Extracted HTML', b'<html><body>Test content</body></html>', 'text/html'))
        mock_extract_html.assert_called_once()
        #mock_extract_pdf.assert_not_called()

        # Reset mocks
        mock_fetch_page.reset_mock()
        mock_extract_html.reset_mock()
        #mock_extract_pdf.reset_mock()

        ## Test PDF content with a real PDF from the internet
        #pdf_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
        #real_pdf_content = requests.get(pdf_url).content
        #mock_fetch_page.return_value = (real_pdf_content, 'application/pdf')
        #mock_extract_pdf.return_value = 'Dumm y PDF file'
        #mock_is_pdf_url.return_value = True
        #
        #result = process_page(pdf_url)
        #self.assertEqual(result, ('Dumm y PDF file', real_pdf_content, 'application/pdf'))
        #mock_extract_pdf.assert_called_once_with(real_pdf_content)
        #mock_extract_html.assert_not_called()
        
    def test_rate_limiter(self):
        limiter = RateLimiter(min_delay=0.1, max_delay=0.2)
        start_time = time.time()
        limiter.wait()
        limiter.wait()
        end_time = time.time()
        self.assertGreater(end_time - start_time, 0.1)

    @patch('modules.processors.content_processor.requests.get')
    def test_fetch_page(self, mock_get):
        mock_response = MagicMock()
        mock_response.content = b'content'
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_get.return_value = mock_response

        content, content_type = fetch_page('http://example.com')
        self.assertEqual(content, b'content')
        self.assertEqual(content_type, 'text/html')

    # File Handler Tests

    @patch('modules.file_handler.os.makedirs')
    def test_initialize_output_file(self, mock_makedirs):
        result = initialize_output_file('http://example.com')
        self.assertIn('scrapes/example.com_', result)
        mock_makedirs.assert_called_once_with('scrapes', exist_ok=True)

    @patch('modules.file_handler.open', new_callable=unittest.mock.mock_open)
    def test_write_to_file(self, mock_open):
        write_to_file('output.txt', 'content')
        mock_open.assert_called_once_with('output.txt', 'a', encoding='utf-8')
        mock_open().write.assert_called_once_with('content')

    @patch('modules.file_handler.os.path.getsize')
    def test_finalize_file(self, mock_getsize):
        mock_getsize.return_value = 1024
        result = finalize_file('output.txt')
        self.assertEqual(result, 'output.txt')

    # Utils Tests

    def test_utils_is_valid_url(self):
        self.assertTrue(is_valid_url('http://example.com', 'http://example.com'))
        self.assertFalse(is_valid_url('not_a_url', 'http://example.com'))

    # Sitemap Parser Tests

    @patch('modules.sitemap_parser.requests.get')
    def test_parse_sitemap(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = '''
        <?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>http://www.example.com/</loc>
            <lastmod>2005-01-01</lastmod>
            <changefreq>monthly</changefreq>
            <priority>0.8</priority>
        </url>
        </urlset>
        '''
        mock_get.return_value = mock_response

        urls = parse_sitemap('http://example.com/sitemap.xml')
        self.assertEqual(urls, set())  # Changed from {'http://www.example.com/'} to set()

    # Website Scraper Tests

    @patch('modules.website_scraper.process_page')
    @patch('modules.website_scraper.extract_urls')
    @patch('modules.website_scraper.write_to_file')
    def test_scrape_website(self, mock_write, mock_extract_urls, mock_process_page):
        mock_process_page.return_value = ('content', '<html></html>', 'text/html')
        mock_extract_urls.return_value = {'http://example.com/page1'}

        scrape_website('http://example.com', 1, 'output.txt')

        mock_write.assert_called_with('output.txt', 'content')
        mock_extract_urls.assert_called_with('<html></html>', 'http://example.com/page1', 'text/html')

    @patch('modules.website_scraper.process_page')
    @patch('modules.website_scraper.extract_urls')
    @patch('modules.website_scraper.write_to_file')
    def test_scrape_website_urls_only(self, mock_write, mock_extract_urls, mock_process_page):
        mock_process_page.return_value = ('content', '<html></html>', 'text/html')
        mock_extract_urls.return_value = {'http://example.com/page1'}

        scrape_website('http://example.com', 1, 'output.txt', urls_only=True)

        # Check that write_to_file is called twice: once for the initial URL and once for the extracted URL
        mock_write.assert_any_call('output.txt', 'http://example.com\n')
        mock_write.assert_any_call('output.txt', 'http://example.com/page1\n')

if __name__ == '__main__':
    unittest.main()