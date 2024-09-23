# config.py

# User Agent string
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"

# Set of headers
HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}

# Request timeout in seconds
REQUEST_TIMEOUT = 10

# Maximum number of retries for fetching content
MAX_RETRIES = 3

# Initial delay for retry (in seconds)
INITIAL_RETRY_DELAY = 1

# Rate limiting delay range (in seconds)
RATE_LIMIT_MIN = 1
RATE_LIMIT_MAX = 5