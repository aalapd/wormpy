# Wormpy

## Overview

Wormpy is a Python-based web scraping tool designed to extract content from websites efficiently and respectfully. It can parse sitemaps, crawl websites up to a specified depth, and handle various content types including HTML and PDF.

Please, for god's sake, make sure you use a VPN when using this!

Read the [tutorial](https://medium.com/@aalapdavjekar/7-lessons-i-learned-while-writing-code-with-ai-b59414181da6) on how I built the first version of this tool.

## Features

- Parallel scraping with asyncio
- Sitemap parsing (sitemap.xml, sitemap_index.xml, etc.)
- Fallback to HTML parsing if sitemaps are unavailable
- Recursive URL processing up to a specified depth
- PDF content extraction
- Rate limiting to respect server resources
- Flexible logging
- Content saved to timestamped files
- Command-line interface for easy use
- Image URL detection and skipping
- Suspicious URL detection
- Output in CSV or JSON format
- Discovered URLs listed for each scraped page

## Requirements

- Python 3.x
- Required libraries:
  - beautifulsoup4==4.12.3
  - certifi==2024.7.4
  - charset-normalizer==3.3.2
  - idna==3.7
  - parameterized==0.9.0
  - PyPDF2==3.0.1
  - PyYAML==6.0.2
  - requests==2.32.3
  - responses==0.25.3
  - soupsieve==2.5
  - urllib3==2.2.2

Install the required libraries using pip:

```
pip install -r requirements.txt
```

## Usage

1. Clone the repository or download the source code.
2. Navigate to the directory containing the source code.
3. Run the program with the following command:

```
python main.py [--log LOG_LEVEL] [--savename SAVE_DIRECTORY] [--format {csv,json}] [--force {req,sel}]
```

Arguments:
 - `url`: Base URL of the website to scrape (required)
 - `depth`: Maximum crawling depth (required, must be a non-negative integer)
 - `--log`: Set the logging level (optional, default is INFO)
 - `--savename`: Specify the directory name to save output (optional)
 - `--format`: Specify the output format, either 'csv' or 'json' (optional, default is 'json')
 - `--force`: Force scraping with either 'req' for requests or 'sel' for selenium (optional)

Example:
```
python main.py https://www.example.com 1 --log DEBUG --savename example_scrape --format csv --force sel
```

## Key Components

- `main.py`: Entry point of the application
- `website_scraper.py`: Core scraping logic
- `sitemap_parser.py`: Handles sitemap parsing
- `content_processor.py`: Processes and extracts text from HTML and PDF content
- `url_processor.py`: Processes URLs and extracts links
- `pdf_processor.py`: Handles PDF-specific processing (for future functionality)
- `file_handler.py`: Manages file operations
- `utils.py`: Utility functions
- `config.py`: Configuration settings

## Error Handling and Logging

Wormpy implements robust error handling and logging throughout the codebase. Errors are caught, logged, and in many cases, the script attempts to continue execution where possible.

## Rate Limiting

To be respectful of server resources, Wormpy implements a rate limiter that adds a random delay between requests.

## PDF Handling

Wormpy can detect and extract text from PDF files, both from local files and URLs.

## URL Processing

- The tool now offers an option to return only URLs instead of content.
- It detects and skips image URLs to avoid unnecessary processing.
- Suspicious URLs are identified and handled appropriately.

## Contributing

Contributions are welcome! If you have suggestions for improvements or encounter any issues, please open an issue or submit a pull request.

## License

This project is licensed under the GNU GENERAL PUBLIC LICENSE. See the LICENSE file for more details.

## Disclaimer

Web scraping may be subject to legal and ethical considerations. Always ensure you have permission to scrape a website and that you're complying with the website's robots.txt file and terms of service.