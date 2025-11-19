# Multi-Source Crypto News Auto Poster
# Main orchestrator for crawling, processing, and publishing cryptocurrency news

import sys
sys.path.append('src')

import json
import time
from datetime import datetime
from typing import Dict, List
from apscheduler.schedulers.blocking import BlockingScheduler
from crawler.crawler_factory import CrawlerFactory
from services.gemini_service import GeminiService
from services.wordpress_service import WordPressService
from utils.storage import ArticleStorage


def load_config(config_file: str = "config.json") -> Dict:
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"[INFO] Configuration loaded from {config_file}")
        return config
    except Exception as e:
        print(f"[ERROR] Failed to load config: {str(e)}")
        return {}


def process_source(source_name: str, config: Dict, gemini: GeminiService,
                   wordpress: WordPressService, storage: ArticleStorage) -> Dict:
    """
    Process a single news source

    Returns:
        Statistics dictionary
    """
    print(f"\n{'='*60}")
    print(f"Processing Source: {source_name.upper()}")
    print(f"{'='*60}")

    stats = {
        'source': source_name,
        'crawled': 0,
        'new_articles': 0,
        'published': 0,
        'failed': 0
    }

    try:
        # Get source configuration
        source_config = config['sources'].get(source_name, {})
        limit = source_config.get('limit', 5)

        # Get crawler
        crawler = CrawlerFactory.get_crawler(source_name)
        if not crawler:
            print(f"[ERROR] Could not create crawler for {source_name}")
            return stats

        # Step 1: Crawl latest articles
        print(f"\n[STEP 1] Crawling latest {limit} articles from {crawler.source_name}")
        articles = crawler.get_latest_articles(limit=limit)
        stats['crawled'] = len(articles)

        if not articles:
            print("[WARNING] No articles found")
            return stats

        # Step 2: Filter new articles
        print(f"\n[STEP 2] Filtering new articles")
        new_articles = storage.filter_new_articles(articles)
        stats['new_articles'] = len(new_articles)

        if not new_articles:
            print("[INFO] No new articles to process")
            return stats

        # Step 3: Process each new article
        for idx, article in enumerate(new_articles, 1):
            print(f"\n{'-'*60}")
            print(f"[Article {idx}/{len(new_articles)}] Processing")
            print(f"{'-'*60}")
            # Handle Unicode safely for Windows console
            try:
                print(f"Title: {article.get('title', 'N/A')[:80]}...")
            except UnicodeEncodeError:
                print(f"Title: [Contains special characters]")

            try:
                # Get full article content
                print(f"[STEP 3-{idx}] Fetching full content")
                article_detail = crawler.get_article_content(article['url'])

                if not article_detail:
                    print(f"[ERROR] Failed to fetch article content")
                    stats['failed'] += 1
                    continue

                # Add source field
                article_detail['source'] = crawler.source_name

                print(f"Content length: {len(article_detail.get('content', ''))} characters")

                # Process with Gemini
                print(f"[STEP 4-{idx}] Processing with Gemini 2.5")
                processed = gemini.process_article_complete(article_detail)

                print(f"Classification: {processed.get('classification', 'N/A')}")
                try:
                    print(f"SEO Title: {processed.get('seo_title', 'N/A')[:60]}...")
                except UnicodeEncodeError:
                    print(f"SEO Title: [Contains special characters]")
                print(f"Image: {processed.get('image_path', 'N/A')}")

                # Publish to WordPress
                print(f"[STEP 5-{idx}] Publishing to WordPress")
                print(f"  Tag: #{processed.get('classification', 'BTC')}")
                print(f"  Category: {processed.get('source', 'unknown')}")

                post_id = wordpress.publish_article(
                    processed,
                    processed.get('image_path')
                )

                if post_id:
                    print(f"[SUCCESS] Published! Post ID: {post_id}")

                    # Save to storage
                    print(f"[STEP 6-{idx}] Saving to storage")
                    storage.save_processed_article(processed)

                    stats['published'] += 1
                else:
                    print(f"[ERROR] Failed to publish article")
                    stats['failed'] += 1

                # Small delay between articles
                time.sleep(2)

            except Exception as e:
                print(f"[ERROR] Failed to process article: {str(e)}")
                stats['failed'] += 1
                continue

    except Exception as e:
        print(f"[ERROR] Failed to process source {source_name}: {str(e)}")

    return stats


def print_summary(all_stats: List[Dict], storage: ArticleStorage):
    """Print summary statistics"""
    print(f"\n{'='*60}")
    print("EXECUTION SUMMARY")
    print(f"{'='*60}")

    total_crawled = sum(s['crawled'] for s in all_stats)
    total_new = sum(s['new_articles'] for s in all_stats)
    total_published = sum(s['published'] for s in all_stats)
    total_failed = sum(s['failed'] for s in all_stats)

    print(f"\nOverall:")
    print(f"  Articles Crawled: {total_crawled}")
    print(f"  New Articles: {total_new}")
    print(f"  Successfully Published: {total_published}")
    print(f"  Failed: {total_failed}")

    print(f"\nBy Source:")
    for stats in all_stats:
        print(f"  {stats['source']}:")
        print(f"    Crawled: {stats['crawled']}")
        print(f"    New: {stats['new_articles']}")
        print(f"    Published: {stats['published']}")
        print(f"    Failed: {stats['failed']}")

    # Storage stats
    storage_stats = storage.get_stats()
    print(f"\nStorage Statistics:")
    print(f"  Total Articles in DB: {storage_stats['total_articles']}")
    if storage_stats.get('by_source'):
        print(f"  By Source:")
        for source, count in storage_stats['by_source'].items():
            print(f"    {source}: {count}")


def run_pipeline():
    """Execute the crawling and publishing pipeline once"""
    print(f"\n{'='*60}")
    print(f"Pipeline Execution - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    # Load configuration
    config = load_config()
    if not config:
        print("[ERROR] Configuration is empty or invalid")
        return

    # Initialize services
    print("\n[INIT] Initializing services...")
    gemini = GeminiService()
    wordpress = WordPressService()
    storage = ArticleStorage()

    # Get enabled sources
    enabled_sources = [
        source_name
        for source_name, source_config in config['sources'].items()
        if source_config.get('enabled', False)
    ]

    if not enabled_sources:
        print("[ERROR] No sources are enabled in config.json")
        return

    print(f"\n[INFO] Enabled sources: {', '.join(enabled_sources)}")

    # Process each source sequentially
    all_stats = []
    for source_name in enabled_sources:
        stats = process_source(source_name, config, gemini, wordpress, storage)
        all_stats.append(stats)

    # Print summary
    print_summary(all_stats, storage)

    print(f"\n{'='*60}")
    print(f"Pipeline Execution Complete - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")


def main():
    """Main entry point"""
    print("="*60)
    print("Multi-Source Crypto News Auto Poster")
    print("="*60)

    # Load configuration
    config = load_config()
    if not config:
        print("[ERROR] Configuration is empty or invalid")
        return

    # Check if scheduler is enabled
    scheduler_config = config.get('scheduler', {})
    scheduler_enabled = scheduler_config.get('enabled', False)
    interval_minutes = scheduler_config.get('interval_minutes', 30)

    if scheduler_enabled:
        print(f"\n[INFO] Scheduler mode enabled")
        print(f"[INFO] Interval: {interval_minutes} minutes")
        print(f"[INFO] Press Ctrl+C to stop the scheduler")

        # Create scheduler
        scheduler = BlockingScheduler()

        # Schedule the pipeline to run at specified intervals
        scheduler.add_job(
            run_pipeline,
            'interval',
            minutes=interval_minutes,
            next_run_time=datetime.now()  # Run immediately on start
        )

        try:
            print(f"\n[INFO] Starting scheduler...")
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print(f"\n[INFO] Scheduler stopped by user")
            scheduler.shutdown()
    else:
        print(f"\n[INFO] Single execution mode")
        run_pipeline()


if __name__ == "__main__":
    main()
