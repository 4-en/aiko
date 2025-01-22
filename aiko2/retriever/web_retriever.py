from . import RetrievalResults, QueryResults, BaseRetriever
from aiko2.core import Conversation


import aiohttp
import asyncio
import re
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from readability import Document
import requests

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

# Regex patterns for "useless" pages (login, captchas, errors)
USELESS_PAGE_PATTERNS = [
    r"/login", r"/signin", r"/signup", r"/auth",
    r"/captcha", r"/error", r"/404", r"/terms", r"/privacy",
    r"/cart", r"/checkout", r"/subscribe"
]

def matches_useless_pattern(url):
    """Checks if a URL matches known useless page patterns (e.g., login, captcha)."""
    return any(re.search(pattern, url) for pattern in USELESS_PAGE_PATTERNS)

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
    try:
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
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
    return url, "Error", "Failed to retrieve page"

def scrape_website_sync(url):
    """Scrape a webpage and extract properly formatted text."""
    try:
        html = requests.get(url).text
        doc = Document(html)  # Extracts main readable content
        soup = BeautifulSoup(doc.summary(), "html.parser")  # Parse with BeautifulSoup
        
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
        formatted_text = "\n\n".join(paragraphs)  # Keep paragraph breaks

        # Remove spaces before punctuation (e.g., "word ." → "word.")
        clean_text = re.sub(r"\s+([.,!?;:()\[\]'])", r"\1", formatted_text)

        return url, doc.title(), clean_text
    except Exception as e:
        return url, "Error", f"Failed to parse content: {e}"

async def get_search_results(query, num_results=5, time_filter="all"):
    """Get search result URLs from DuckDuckGo asynchronously with optional date filtering."""
    results = []
    time_code = DATE_FILTERS.get(time_filter.lower(), None)  # Get time filter code

    with DDGS() as ddgs:
        for result in ddgs.text(query, max_results=num_results, timelimit=time_code):
            if not is_blacklisted(result["href"]) and not matches_useless_pattern(result["href"]):
                results.append(result["href"])
    
    return results

def get_search_results_sync(query, num_results=5, time_filter="all"):
    """Get search result URLs from DuckDuckGo synchronously with optional date filtering."""
    results = []
    time_code = DATE_FILTERS.get(time_filter.lower(), None)  # Get time filter code

    with DDGS() as ddgs:
        for result in ddgs.text(query, max_results=num_results, timelimit=time_code):
            if not is_blacklisted(result["href"]) and not matches_useless_pattern(result["href"]):
                results.append(result["href"])
    
    return results

class WebRetriever(BaseRetriever):
    """
    A retriever that retrieves information from the web using a query.
    
    """

    def query(self, queries):
        """
        Query the web for information using a list of queries.
        
        Parameters
        ----------
        queries : List[str]
            A list of queries to retrieve information.
        
        Returns
        -------
        list[QueryResults]
            The query results containing the URLs and titles of the search results.
        """
        
        # Initialize the query results
        query_results = [ QueryResults(query) for query in queries ]

        # Create an new event loop
        loop = asyncio.get_event_loop()

        if not loop.is_running():

            # Get the search results asynchronously
            async def get_search_results_async(query, num_results=5, time_filter="all"):
                return await get_search_results(query, num_results, time_filter)
            
            async def get_query_results(query_results:QueryResults, query):
                async with aiohttp.ClientSession() as session:
                    print(f"\nSearching for: {query}...\n")
                    try:
                        search_results = await get_search_results_async(query)
                        tasks = [scrape_website(session, url) for url in search_results]
                        scraped_data = await asyncio.gather(*tasks)
                        for idx, (url, title, content) in enumerate(scraped_data, 1):
                            if contains_text(content, min_words=10):
                                # TODO: requery if not enough results
                                query_results.add_result(content)
                    except Exception as e:
                        print(f"Failed to retrieve search results: {e}")
                        

            # Run the asynchronous tasks
            async def run_queries():
                for query_result, query in zip(query_results, queries):
                    await get_query_results(query_result, query)

            loop.run_until_complete(run_queries())

        else:
            for query_result, query in zip(query_results, queries):
                print(f"\nSearching for: {query}...\n")
                try:
                    search_results = get_search_results_sync(query)
                    tasks = [scrape_website_sync(url) for url in search_results]
                    scraped_data = [task for task in tasks]
                    for idx, (url, title, content) in enumerate(scraped_data, 1):
                        if contains_text(content, min_words=10):
                
                            query_result.add_result(content)
                except Exception as e:
                    print(f"Failed to retrieve search results: {e}")
                

        
        
        return query_results
    
    def retrieve(self, conversation, queries) -> RetrievalResults:
        """
        Retrieve information from the web using a query.
        
        Parameters
        ----------
        conversation : Conversation
            The conversation to retrieve information for.
        queries : List[str]
            A list of queries to retrieve information.
        
        Returns
        -------
        RetrievalResults
            The retrieval context containing the results of the retrieval operation.
        """
        
        # Initialize the results
        
        # Get the query results
        query_results = self.query(queries)
        
        # Add the query results to the retrieval results
        retrieval_results = RetrievalResults(query_results)
        retrieval_results.rank_results()
        
        return retrieval_results