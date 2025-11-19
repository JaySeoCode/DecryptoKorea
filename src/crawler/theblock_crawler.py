"""
The Block crawler module

Crawls cryptocurrency news from TheBlock.co using RSS feed
"""

from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import feedparser
from .base_crawler import BaseCrawler


class TheBlockCrawler(BaseCrawler):
    """The Block website crawler"""

    BASE_URL = "https://www.theblock.co"
    RSS_FEED_URL = f"{BASE_URL}/rss.xml"

    def __init__(self):
        super().__init__()
        print("[INFO] The Block crawler initialized (using RSS feed)")

    @property
    def source_name(self) -> str:
        """Return source name"""
        return "theblock.co"

    @property
    def source_url(self) -> str:
        """Return main crawling URL"""
        return self.RSS_FEED_URL

    def get_latest_articles(self, limit: int = 10) -> List[Dict]:
        """
        Get latest articles from The Block RSS feed.

        Args:
            limit: Number of articles to fetch (default: 10)

        Returns:
            List of article information (title, URL, date, etc.)
        """
        try:
            print(f"[INFO] Fetching latest {limit} articles from The Block RSS feed...")

            # Parse RSS feed
            feed = feedparser.parse(self.RSS_FEED_URL)

            if not feed.entries:
                print("[ERROR] No articles found in RSS feed")
                return []

            articles = []
            for entry in feed.entries[:limit]:
                # Title
                title = entry.get('title', 'No title')

                # URL
                url = entry.get('link', '')

                # Summary
                summary = entry.get('summary', '')
                # Remove HTML tags
                if summary:
                    summary_soup = BeautifulSoup(summary, 'html.parser')
                    summary = summary_soup.get_text(strip=True)[:200]

                # Published date
                published_date = entry.get('published', '')

                # Categories (if available)
                categories = [tag.get('term', '') for tag in entry.get('tags', [])]

                article_info = {
                    'url': url,
                    'title': title,
                    'summary': summary,
                    'published_date': published_date,
                    'categories': categories,
                    'crawled_at': datetime.now().isoformat()
                }

                articles.append(article_info)

            print(f"[SUCCESS] Collected {len(articles)} article listings")
            return articles

        except Exception as e:
            print(f"[ERROR] RSS feed crawling failed: {str(e)}")
            return []

    def get_article_content(self, url: str) -> Optional[Dict]:
        """
        Get full article content.
        The Block may have Cloudflare protection, so we use RSS feed data.

        Args:
            url: Article URL

        Returns:
            Article details (title, content, author, date, etc.)
        """
        try:
            print(f"[INFO] Fetching article data from RSS feed: {url}")

            # Re-parse RSS feed to get full info for this URL
            feed = feedparser.parse(self.RSS_FEED_URL)

            for entry in feed.entries:
                if entry.get('link') == url:
                    # Title
                    title = entry.get('title', 'No title')

                    # Content (use RSS content or summary)
                    content = ''
                    if hasattr(entry, 'content') and entry.content:
                        content = entry.content[0].get('value', '')
                    elif hasattr(entry, 'summary'):
                        content = entry.get('summary', '')

                    # Remove HTML tags
                    if content:
                        soup = BeautifulSoup(content, 'html.parser')
                        content = soup.get_text(strip=True)

                    # Author
                    author = entry.get('author', 'Unknown author')

                    # Date
                    published_date = entry.get('published', datetime.now().isoformat())

                    # Summary
                    summary_text = entry.get('summary', '')
                    if summary_text:
                        summary_soup = BeautifulSoup(summary_text, 'html.parser')
                        summary_text = summary_soup.get_text(strip=True)[:200]

                    article_data = {
                        'url': url,
                        'title': title,
                        'content': content,
                        'author': author,
                        'published_date': published_date,
                        'summary': summary_text,
                        'crawled_at': datetime.now().isoformat()
                    }

                    print(f"[SUCCESS] Article data retrieved: {title[:50]}...")
                    print(f"[INFO] Content length: {len(content)} characters (from RSS)")
                    return article_data

            print(f"[WARNING] URL not found in RSS feed: {url}")
            return None

        except Exception as e:
            print(f"[ERROR] Article data retrieval failed ({url}): {str(e)}")
            return None


# Test code
if __name__ == "__main__":
    crawler = TheBlockCrawler()

    print("=" * 60)
    print("The Block Crawler Test")
    print("=" * 60)

    # Get latest articles
    articles = crawler.get_latest_articles(limit=5)

    print(f"\n[RESULT] Found {len(articles)} articles:")
    for i, article in enumerate(articles, 1):
        print(f"\n{i}. {article['title'][:80]}...")
        print(f"   URL: {article['url']}")

    # Get first article details
    if articles:
        print("\n" + "=" * 60)
        print("First Article Details")
        print("=" * 60)

        first_article = crawler.get_article_content(articles[0]['url'])
        if first_article:
            print(f"\nTitle: {first_article['title']}")
            print(f"Author: {first_article['author']}")
            print(f"Date: {first_article['published_date']}")
            print(f"Summary: {first_article['summary'][:200]}...")
            print(f"\nContent length: {len(first_article['content'])} characters")
            print(f"Content (first 500 chars):\n{first_article['content'][:500]}...")
