# Wormpy

## Overview

Wormpy is a Python-based tool designed to scrape websites for content. It can extract URLs from sitemaps or fallback to HTML parsing if a sitemap is not available. The scraped content is saved to a timestamped text file within a `scrapes` directory.

## Features

- Fetches and parses sitemaps (`sitemap_index.xml` or `sitemap.xml`).
- Falls back to HTML parsing if sitemaps are not available.
- Extracts and processes URLs recursively up to a specified depth.
- Saves the scraped content to a timestamped text file in the `scrapes` directory.

## Requirements

- Python 3.x
- `requests` library
- `beautifulsoup4` library

You can install the required libraries using pip:

`pip install requests beautifulsoup4`

## Usage

- Clone the repository or download the source code.
- Navigate to the directory containing the source code.
- Run the program with the following command:

`python main.py <base_url> <depth>`

- <base_url>: The base URL of the website you want to scrape.
- <depth>: The maximum crawling depth (must be a positive integer).

### Example

`python main.py https://www.example.com 50`

## Contributing

Contributions are welcome! If you have suggestions for improvements or encounter any issues, please open an issue or submit a pull request.

## License

This project is licensed under the GNU GENERAL PUBLIC LICENSE. See the LICENSE file for more details.