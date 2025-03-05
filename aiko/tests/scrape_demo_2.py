import re
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse
from readability import Document

# Blacklisted domains (known useless pages)
BLACKLISTED_DOMAINS = {
    "youtube.com", "vimeo.com", "dailymotion.com", "twitch.tv", "tiktok.com",
    "netflix.com", "hulu.com", "disneyplus.com", "spotify.com",
    "google.com", "bing.com", "yahoo.com", "duckduckgo.com",
    "amazon.com", "ebay.com", "aliexpress.com", "etsy.com", "craigslist.org",
    "bloomberg.com", "nasdaq.com", "marketwatch.com", "maps.google.com",
    "drive.google.com", "dropbox.com", "onedrive.live.com",
    "docs.google.com", "notion.so", "trello.com",
    "chat.openai.com",
    "bard.google.com", "perplexity.ai", "character.ai"
}

# Regex patterns for "useless" pages (login, captchas, errors)
USELESS_PAGE_PATTERNS = [
    r"/login", r"/signin", r"/signup", r"/auth",
    r"/captcha", r"/error", r"/404", r"/terms", r"/privacy",
    r"/cart", r"/checkout", r"/subscribe"
]

async def fetch_html(url):
    """Fetches raw HTML content of a page asynchronously."""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    return None
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None

def extract_main_domain(url):
    """Extracts the base domain from a URL (ignores subdomains)."""
    parsed_url = urlparse(url)
    domain_parts = parsed_url.netloc.split('.')
    if len(domain_parts) > 2:
        return ".".join(domain_parts[-2:])  # Get "example.com" from "sub.example.com"
    return parsed_url.netloc

def is_blacklisted(url):
    """Checks if a URL belongs to a blacklisted domain."""
    domain = extract_main_domain(url)
    return domain in BLACKLISTED_DOMAINS

def matches_useless_pattern(url):
    """Checks if a URL matches known useless page patterns (e.g., login, captcha)."""
    return any(re.search(pattern, url) for pattern in USELESS_PAGE_PATTERNS)

def extract_text(html):
    """Extracts meaningful text from HTML using readability-lxml."""
    soup = BeautifulSoup(html, "html.parser")
    doc = Document(html)
    main_text = doc.summary()
    clean_text = BeautifulSoup(main_text, "html.parser").get_text(separator=" ", strip=True)
    return clean_text

def is_low_quality_text(text, min_words=5):
    """Checks if text is too short or lacks real content."""
    words = re.findall(r'\b[a-zA-Z]{2,}\b', text)
    return len(words) < min_words

async def filter_url(url):
    """Dynamically filters URLs based on domain, structure, and actual content."""
    if is_blacklisted(url):
        return False, "Blacklisted domain"

    if matches_useless_pattern(url):
        return False, "Matches useless URL pattern"

    html = await fetch_html(url)
    if not html:
        return False, "Failed to fetch page"

    text = extract_text(html)
    if is_low_quality_text(text):
        return False, "Low-quality or too little text"

    return True, "Valid page"

# Example Usage
async def main():
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://twitter.com/someuser/status/123456789",
        "https://exampleblog.com/articles/some-useful-text",
        "https://reddit.com/r/funny",
        "https://news.google.com/topstories",
        "https://randomsite.com/login"
    ]

    for url in test_urls:
        is_valid, reason = await filter_url(url)
        print(f"{url} -> {'Allowed' if is_valid else 'Blocked'} ({reason})")

# Run the async filter
asyncio.run(main())
