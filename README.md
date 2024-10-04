🪱
# Wormpy

## Overview

Wormpy is a Python-based web scraping tool designed to crawl across websites and extract their contents efficiently and respectfully. It now features a discovery mode for comprehensive website crawling, as well as a single-page scraping option. Wormpy can parse sitemaps, handle various content types including HTML and PDF, and respects server resources.

Read the [tutorial](https://medium.com/@aalapdavjekar/7-lessons-i-learned-while-writing-code-with-ai-b59414181da6) on how I built the first version of this tool.

**For god's sake, make sure you use a VPN when using this!** (Get 3 months free with NordVPN by using [this link](https://refer-nordvpn.com/kwTbjBYxbud).)

## New Features

- Discovery mode for comprehensive website crawling
- Single-page scraping option
- Dynamic scraper allocation based on URL pool size
- Improved URL pool management
- Configurable maximum number of URLs to scrape

## Existing Features

- Parallel scraping with asyncio
- PDF content extraction
- Sitemap parsing (sitemap.xml, sitemap_index.xml, etc.)
- Rate limiting to respect server resources
- Flexible logging
- Content saved to timestamped files
- Command-line interface for easy use
- Image URL detection and skipping
- Output in CSV or JSON format
- Discovered URLs listed for each scraped page

## Requirements

- Python 3.x
- Required libraries (see requirements.txt)

Install the required libraries using pip:

```
pip install -r requirements.txt
```

## Usage

1. Clone the repository or download the source code.
2. Navigate to the directory containing the source code.
3. Run the program with the following command:

```
python main.py <url> [--discovery] [--log LOG_LEVEL] [--savename SAVE_DIRECTORY] [--format {csv,json}] [--force {req,sel}]
```

Arguments:
 - `url`: Base URL of the website to scrape (required)
 - `--discovery`: Enable discovery mode to scrape the entire website (optional)
 - `--format`: Specify the output format, either 'csv' or 'json' (optional, default is 'json')
 - `--force`: Force scraping with either 'req' for requests or 'sel' for selenium (optional)
 - `--log`: Set the logging level (optional, default is INFO)
 - `--savename`: Specify the directory name to save output (optional)

Examples:
```
# Scrape a single page
python main.py https://www.example.com --savename example_scrape --format csv

# Scrape the entire website (discovery mode)
python main.py https://www.example.com --discovery --log INFO --format json --force sel
```

## Key Components

- `main.py`: Entry point of the application
- `scraper.py`: Core scraping logic and scraper management
- `content_processor.py`: Processes and extracts text from HTML and PDF content
- `url_processor.py`: Processes URLs and extracts links
- `url_tracker.py`: Manages the URL pool and tracks visited URLs
- `utils.py`: Utility functions
- `config.py`: Configuration settings

## Error Handling and Logging

Wormpy implements robust error handling and logging throughout the codebase. Errors are caught, logged, and in many cases, the script attempts to continue execution where possible.

## Rate Limiting

To be respectful of server resources, Wormpy implements a rate limiter that adds a random delay between requests.

## PDF Handling

Wormpy can detect and extract text from PDF files, both from local files and URLs.

## URL Processing

- The tool offers both single-page and full website scraping options.
- It detects and skips image URLs to avoid unnecessary processing.
- Suspicious URLs are identified and handled appropriately.

## Contributing

Contributions are welcome! If you have suggestions for improvements or encounter any issues, please open an issue or submit a pull request.

## License

This project is licensed under the GNU GENERAL PUBLIC LICENSE. See the LICENSE file for more details.

## Disclaimer

Web scraping may be subject to legal and ethical considerations. Always ensure you have permission to scrape a website and that you're complying with the website's robots.txt file and terms of service.