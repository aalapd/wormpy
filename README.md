# Wormpy

## Overview

Wormpy is a Python-based web scraping tool designed to extract content from websites efficiently and respectfully. It can parse sitemaps, crawl websites up to a specified depth, and handle various content types including HTML and PDF.

Read the (tutorial)[https://medium.com/@aalapdavjekar/7-lessons-i-learned-while-writing-code-with-ai-b59414181da6] on how I built this.

## Features

- Sitemap parsing (`sitemap.xml`, `sitemap_index.xml`, etc.)
- Fallback to HTML parsing if sitemaps are unavailable
- Recursive URL processing up to a specified depth
- PDF content extraction
- Rate limiting to respect server resources
- Flexible logging
- Content saved to timestamped files in a `scrapes` directory
- Command-line interface for easy use

## Requirements

- Python 3.x
- Required libraries:
  - requests
  - beautifulsoup4
  - PyPDF2

Install the required libraries using pip:

```
pip install requests beautifulsoup4 PyPDF2
```

## Usage

1. Clone the repository or download the source code.
2. Navigate to the directory containing the source code.
3. Run the program with the following command:

```
python main.py <url> <depth> [--log LOG_LEVEL] [--output OUTPUT_FILE]
```

Arguments:
- `url`: Base URL of the website to scrape (required)
- `depth`: Maximum crawling depth (required, must be a positive integer)
- `--log`: Set the logging level (optional, default is INFO)
- `--output`: Specify the output file name (optional)

Example:
```
python main.py https://www.example.com 3 --log DEBUG --output example_scrape.txt
```

## Key Components

- `main.py`: Entry point of the application
- `website_scraper.py`: Core scraping logic
- `sitemap_parser.py`: Handles sitemap parsing
- `content_extractor.py`: Extracts text from HTML and PDF content
- `url_processor.py`: Processes URLs and extracts links
- `file_handler.py`: Manages file operations
- `utils.py`: Utility functions
- `config.py`: Configuration settings

## Error Handling and Logging

Wormpy implements robust error handling and logging throughout the codebase. Errors are caught, logged, and in many cases, the script attempts to continue execution where possible.

## Rate Limiting

To be respectful of server resources, Wormpy implements a rate limiter that adds a random delay between requests.

## PDF Handling

Wormpy can detect and extract text from PDF files, both from local files and URLs.

## Contributing

Contributions are welcome! If you have suggestions for improvements or encounter any issues, please open an issue or submit a pull request.

## License

This project is licensed under the GNU GENERAL PUBLIC LICENSE. See the LICENSE file for more details.

## Disclaimer

Web scraping may be subject to legal and ethical considerations. Always ensure you have permission to scrape a website and that you're complying with the website's robots.txt file and terms of service.