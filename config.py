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

# Maximum URLs to visit (for discovery mode)
MAX_URLS_TO_SCRAPE = 100

# URL Pool configurations
MAX_POOL_SIZE = 500  # Maximum number of URLs in the pool
URL_RETRY_LIMIT = 3  # Number of times to retry a failed URL

# Request timeout in seconds
REQUEST_TIMEOUT = 10

# Maximum number of retries for fetching content
MAX_RETRIES = 2

# Initial delay for retry (in seconds)
INITIAL_RETRY_DELAY = 1

# Rate limiting delay range (in seconds)
RATE_LIMIT_MIN = 1
RATE_LIMIT_MAX = 5

# Max number of scrapers to use
MAX_SIMULTANEOUS_SCRAPERS = 6

# Proxy-related settings
PROXY_TEST_URL = "http://httpbin.org/ip"
MAX_PROXIES = 100 # Number of proxies to keep in rotation
PROXY_TIMEOUT = 20
PROXY_REFRESH_THRESHOLD = 10  # Refresh proxy list when available proxies fall below this number
COUNTRY = "us"
SSL = "no"
ANONYMITY = "elite"
