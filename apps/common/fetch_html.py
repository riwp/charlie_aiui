# apps/common/fetch_html.py
import logging
from typing import Optional
from newspaper import Article
from bs4 import BeautifulSoup

def fetch_html(url: str) -> str:
    """
    Scrapes a URL using newspaper, cleans the content via BeautifulSoup, 
    and returns a sanitized block of text.
    """
    try:
        logging.info(f"🌐 Scraping URL: {url}")
        
        # Configure standard user agent header to prevent bot blocks
        article = Article(url, browser_user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
        article.download()
        article.parse()

        if not article.text:
            return ""

        return sanitize_html(article.text)
    except Exception as e:
        logging.error(f"⚠️ Error fetching or parsing article: {e}")
        return ""

def sanitize_html(html_content: str) -> str:
    """
    Cleans raw text blocks, stripping scripts, styles, and hidden markup structures.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Target system cleanup arrays
    blacklist = [
        "script", "style", "meta", "iframe", "img",
        "link", "noscript", "fluent-design-system-provider",
        "entry-point"
    ]
    for tag in soup.find_all(blacklist):
        tag.decompose()

    # Locate and destroy inline CSS hidden layout components
    for tag in soup.find_all(style=True):
        if "display: none" in tag['style']:
            tag.decompose()

    return soup.get_text(separator=" ").strip()