# Crawler Factory
# Central registry for all news site crawlers

from typing import Dict, List, Optional
from .base_crawler import BaseCrawler
from .coindesk_crawler import CoinDeskCrawler
from .cryptopolitan_crawler import CryptopolitanCrawler
from .theblock_crawler import TheBlockCrawler


class CrawlerFactory:
    """
    Crawler factory class for managing multiple news site crawlers
    """

    # Registry of available crawlers
    _crawlers: Dict[str, type] = {
        'coindesk': CoinDeskCrawler,
        'cryptopolitan': CryptopolitanCrawler,
        'theblock': TheBlockCrawler,
        # Add more crawlers here as needed
        # 'binance': BinanceCrawler,
    }

    @classmethod
    def get_crawler(cls, source: str) -> Optional[BaseCrawler]:
        """
        Get a crawler instance by source name

        Args:
            source: Source name (e.g., 'coindesk', 'cryptopolitan')

        Returns:
            Crawler instance or None if not found
        """
        crawler_class = cls._crawlers.get(source.lower())
        if crawler_class:
            return crawler_class()
        else:
            print(f"[ERROR] Unknown crawler source: {source}")
            print(f"[INFO] Available sources: {', '.join(cls._crawlers.keys())}")
            return None

    @classmethod
    def get_all_crawlers(cls) -> List[BaseCrawler]:
        """
        Get instances of all available crawlers

        Returns:
            List of all crawler instances
        """
        return [crawler() for crawler in cls._crawlers.values()]

    @classmethod
    def get_available_sources(cls) -> List[str]:
        """
        Get list of all available source names

        Returns:
            List of source names
        """
        return list(cls._crawlers.keys())

    @classmethod
    def register_crawler(cls, name: str, crawler_class: type):
        """
        Register a new crawler dynamically

        Args:
            name: Source name
            crawler_class: Crawler class (must inherit from BaseCrawler)
        """
        if not issubclass(crawler_class, BaseCrawler):
            raise ValueError(f"{crawler_class} must inherit from BaseCrawler")

        cls._crawlers[name.lower()] = crawler_class
        print(f"[INFO] Registered crawler: {name}")


# Test code
if __name__ == "__main__":
    print("=" * 60)
    print("Crawler Factory Test")
    print("=" * 60)

    # List available sources
    print("\nAvailable sources:")
    for source in CrawlerFactory.get_available_sources():
        print(f"  - {source}")

    # Test individual crawler
    print("\n" + "=" * 60)
    print("Testing CoinDesk Crawler")
    print("=" * 60)
    coindesk = CrawlerFactory.get_crawler('coindesk')
    if coindesk:
        print(f"Crawler: {coindesk}")
        print(f"Source: {coindesk.source_name}")
        print(f"URL: {coindesk.source_url}")

    print("\n" + "=" * 60)
    print("Testing Cryptopolitan Crawler")
    print("=" * 60)
    crypto_crawler = CrawlerFactory.get_crawler('cryptopolitan')
    if crypto_crawler:
        print(f"Crawler: {crypto_crawler}")
        print(f"Source: {crypto_crawler.source_name}")
        print(f"URL: {crypto_crawler.source_url}")

    # Test all crawlers
    print("\n" + "=" * 60)
    print("Getting All Crawlers")
    print("=" * 60)
    all_crawlers = CrawlerFactory.get_all_crawlers()
    for crawler in all_crawlers:
        print(f"  - {crawler.source_name}: {crawler.source_url}")

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
