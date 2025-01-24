from . import RetrievalResults, QueryResult, BaseRetriever, Query
from aiko2.core import Conversation

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

    def query(self, queries: list[Query]) -> RetrievalResults:
        """
        Query the web for information using a list of queries.
        
        Parameters
        ----------
        queries : List[Query]
            A list of queries to retrieve information.
        
        Returns
        -------
        list[QueryResults]
            The query results containing the URLs and titles of the search results.
        """
        
        # Initialize the query results
        retrieval_results = RetrievalResults()

        for query in queries:
            print(f"\nSearching for: {query.query}...\n")
            try:
                # get results from search engine
                search_results = get_search_results_sync(query.query)
                # scrape the content from the search results
                tasks = [scrape_website_sync(url) for url in search_results]
                scraped_data = [task for task in tasks]
                
                for idx, (url, title, content) in enumerate(scraped_data, 1):
                    if contains_text(content, min_words=10):                
                        query_result = QueryResult(content, query, source=url, retriever=self)
                        retrieval_results.add_result(query_result)
            except Exception as e:
                print(f"Failed to retrieve search results: {e}")
                import traceback
                traceback.print_exc()

        return retrieval_results
    
    def retrieve(self, conversation: Conversation, queries: list[Query]) -> RetrievalResults:
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
        retrieval_results = self.query(queries)
        
        # Add the query results to the retrieval results
        # retrieval_results = RetrievalResults(query_results)
        retrieval_results.rank_results()
        
        return retrieval_results