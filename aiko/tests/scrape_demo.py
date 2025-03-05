import aiohttp
import asyncio
import re
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from readability import Document

# DuckDuckGo date filters
DATE_FILTERS = {
    "day": "d",
    "week": "w",
    "month": "m",
    "year": "y",
    "all": None  # No date filtering
}

# List of domains that typically contain no useful text when scraping
BLACKLISTED_DOMAINS = {
    # Video Platforms
    "youtube.com", "youtu.be", "vimeo.com", "dailymotion.com", "twitch.tv", "tiktok.com",
    
    # Social Media
    # "facebook.com", "twitter.com", "x.com", "instagram.com", "linkedin.com",
    # "snapchat.com", "reddit.com", "pinterest.com", "tumblr.com", "mastodon.social",

    # Streaming Services
    "netflix.com", "hulu.com", "disneyplus.com", "hbomax.com", "spotify.com",
    "applemusic.com", "soundcloud.com",

    # Search Engines (search pages, not results themselves)
    "google.com", "bing.com", "yahoo.com", "duckduckgo.com", "baidu.com", "ask.com",

    # News Aggregators (often just link lists, not content)
    "news.google.com", "flipboard.com", "feedly.com", "apple.news",

    # E-Commerce & Listings
    "amazon.com", "ebay.com", "walmart.com", "aliexpress.com", "etsy.com", "craigslist.org",

    # Stock & Financial Data (often requires authentication)
    "bloomberg.com", "nasdaq.com", "yahoo.finance.com", "marketwatch.com", "forbes.com",

    # Map & Location Services
    "maps.google.com", "mapquest.com", "bingmaps.com", "waze.com", "openstreetmap.org",

    # File Hosting & Cloud Storage
    "drive.google.com", "dropbox.com", "onedrive.live.com", "icloud.com", "mediafire.com",
    "megaupload.com", "box.com", "zippyshare.com",

    # Online Tools & Docs (Login required, not real content)
    "docs.google.com", "sheets.google.com", "notion.so", "trello.com", "evernote.com",
    "medium.com", "substack.com", "wordpress.com", "blogger.com", "ghost.io",

    # Job & Resume Sites (Often requires login)
    "linkedin.com", "indeed.com", "glassdoor.com", "monster.com", "ziprecruiter.com",

    # FAQ & Q&A Sites (Low-quality or user-generated content)
    # "quora.com", "stackexchange.com", "stackoverflow.com", "answers.com",

    # Image Galleries (No text)
    "flickr.com", "imgur.com", "500px.com", "unsplash.com", "pexels.com",

    # AI Chatbots & Content Generators
    "chat.openai.com", "bard.google.com", "perplexity.ai", "character.ai"
}

# Function to check if a URL is blacklisted
def is_blacklisted(url):
    """
    Checks if a given URL belongs to a blacklisted domain.
    
    :param url: The URL to check.
    :return: True if the URL is blacklisted, False otherwise.
    """
    return any(domain in url for domain in BLACKLISTED_DOMAINS)

def contains_text(s, min_words=2):
    """
    Checks if a string contains at least `min_words` real words (letters).

    :param s: Input string
    :param min_words: Minimum number of words required (default: 2)
    :return: True if the string contains enough words, False otherwise
    """
    words = re.findall(r'\b[a-zA-Z]{2,}\b', s)  # Find words with at least 2 letters
    return len(words) >= min_words

async def fetch(session, url):
    """Asynchronously fetch the content of a URL."""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with session.get(url, headers=headers, timeout=10) as response:
            if response.status == 200:
                return await response.text()
            else:
                return None
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None

async def scrape_website(session, url):
    """Asynchronously scrape a webpage and extract properly formatted text."""
    html = await fetch(session, url)
    if html:
        try:
            doc = Document(html)  # Extracts main readable content
            soup = BeautifulSoup(doc.summary(), "html.parser")  # Parse with BeautifulSoup
            
            paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
            formatted_text = "\n\n".join(paragraphs)  # Keep paragraph breaks

            # Remove spaces before punctuation (e.g., "word ." → "word.")
            clean_text = re.sub(r"\s+([.,!?;:()\[\]'])", r"\1", formatted_text)

            return url, doc.title(), clean_text
        except Exception as e:
            return url, "Error", f"Failed to parse content: {e}"
    return url, "Error", "Failed to retrieve page"

async def get_search_results(query, num_results=5, time_filter="all"):
    """Get search result URLs from DuckDuckGo asynchronously with optional date filtering."""
    results = []
    time_code = DATE_FILTERS.get(time_filter.lower(), None)  # Get time filter code

    with DDGS() as ddgs:
        for result in ddgs.text(query, max_results=num_results, timelimit=time_code):
            results.append(result["href"])
    
    return results

async def main():
    query = input("Enter your search query: ")
    num_results = int(input("Enter the number of results to retrieve: "))
    
    print("Time filters: day, week, month, year, all (no filter)")
    time_filter = input("Enter time filter (or 'all' for no filter): ").strip().lower()

    print(f"\nSearching for: {query} (Time filter: {time_filter})...\n")
    search_results = await get_search_results(query, num_results, time_filter)

    async with aiohttp.ClientSession() as session:
        tasks = [scrape_website(session, url) for url in search_results]
        scraped_data = await asyncio.gather(*tasks)

    for idx, (url, title, content) in enumerate(scraped_data, 1):
        print(f"\nResult {idx}: {title}\nURL: {url}\nContains text: {contains_text(content[:500])}\nContent:\n{content[:500]}...\n{'-'*80}")

if __name__ == "__main__":
    asyncio.run(main())
