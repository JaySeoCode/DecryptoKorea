"""
Cryptopolitan 크롤링 모듈

Cryptopolitan.com의 News -> Crypto 섹션에서 암호화폐 뉴스를 크롤링합니다.
"""

from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import time
import feedparser
from .base_crawler import BaseCrawler


class CryptopolitanCrawler(BaseCrawler):
    """Cryptopolitan 웹사이트 크롤러"""

    BASE_URL = "https://www.cryptopolitan.com"
    RSS_FEED_URL = f"{BASE_URL}/feed/"

    def __init__(self):
        super().__init__()
        print("[INFO] Cryptopolitan 크롤러 초기화 완료 (RSS 피드 사용)")

    @property
    def source_name(self) -> str:
        """소스 이름 반환"""
        return "cryptopolitan.com"

    @property
    def source_url(self) -> str:
        """크롤링할 메인 URL 반환"""
        return self.RSS_FEED_URL

    def get_latest_articles(self, limit: int = 10) -> List[Dict]:
        """
        Cryptopolitan RSS 피드에서 최신 기사 목록을 가져옵니다.

        Args:
            limit: 가져올 기사 수 (기본값: 10)

        Returns:
            기사 정보 리스트 (제목, URL, 날짜 등)
        """
        try:
            print(f"[INFO] Cryptopolitan RSS 피드에서 최신 기사 {limit}개 크롤링 중...")

            # RSS 피드 파싱
            feed = feedparser.parse(self.RSS_FEED_URL)

            if not feed.entries:
                print("[ERROR] RSS 피드에서 기사를 찾을 수 없습니다")
                return []

            articles = []
            for entry in feed.entries[:limit]:
                # 제목
                title = entry.get('title', '제목 없음')

                # URL
                url = entry.get('link', '')

                # 요약
                summary = entry.get('summary', '')
                # HTML 태그 제거
                if summary:
                    summary_soup = BeautifulSoup(summary, 'html.parser')
                    summary = summary_soup.get_text(strip=True)[:200]

                # 발행 날짜
                published_date = entry.get('published', '')

                # 카테고리 (있는 경우)
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

            print(f"[SUCCESS] {len(articles)}개 기사 목록 수집 완료")
            return articles

        except Exception as e:
            print(f"[ERROR] RSS 피드 크롤링 실패: {str(e)}")
            return []

    def get_article_content(self, url: str) -> Optional[Dict]:
        """
        개별 기사의 전체 내용을 가져옵니다.
        Cryptopolitan은 403 차단이 있으므로 RSS 피드에서 이미 가져온 데이터를 재사용합니다.

        Args:
            url: 기사 URL

        Returns:
            기사 상세 정보 (제목, 본문, 저자, 날짜 등)
        """
        try:
            print(f"[INFO] RSS 피드에서 기사 데이터 조회 중: {url}")

            # RSS 피드 다시 파싱하여 해당 URL의 전체 정보 가져오기
            feed = feedparser.parse(self.RSS_FEED_URL)

            for entry in feed.entries:
                if entry.get('link') == url:
                    # 제목
                    title = entry.get('title', '제목 없음')

                    # 본문 (RSS의 content 또는 summary 사용)
                    content = ''
                    if hasattr(entry, 'content') and entry.content:
                        content = entry.content[0].get('value', '')
                    elif hasattr(entry, 'summary'):
                        content = entry.get('summary', '')

                    # HTML 태그 제거
                    if content:
                        soup = BeautifulSoup(content, 'html.parser')
                        content = soup.get_text(strip=True)

                    # 저자
                    author = entry.get('author', '저자 미상')

                    # 날짜
                    published_date = entry.get('published', datetime.now().isoformat())

                    # 요약
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

                    print(f"[SUCCESS] 기사 데이터 조회 완료: {title[:50]}...")
                    print(f"[INFO] Content length: {len(content)} characters (from RSS)")
                    return article_data

            print(f"[WARNING] URL not found in RSS feed: {url}")
            return None

        except Exception as e:
            print(f"[ERROR] 기사 데이터 조회 실패 ({url}): {str(e)}")
            return None

    def _get_full_url(self, url: str) -> str:
        """상대 URL을 절대 URL로 변환"""
        if url.startswith('http'):
            return url
        if url.startswith('/'):
            return self.BASE_URL + url
        return self.BASE_URL + '/' + url

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """제목 추출"""
        # h1 태그에서 제목 찾기
        title_tag = soup.find('h1')
        if title_tag:
            return title_tag.get_text(strip=True)

        # article header 내 h1
        article_header = soup.find('header', class_=lambda x: x and 'entry-header' in x.lower())
        if article_header:
            title_tag = article_header.find('h1')
            if title_tag:
                return title_tag.get_text(strip=True)

        # meta 태그에서 찾기
        meta_title = soup.find('meta', property='og:title')
        if meta_title:
            return meta_title.get('content', '').strip()

        return "제목 없음"

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """본문 추출"""
        # article 태그 찾기
        article = soup.find('article')

        if not article:
            # entry-content, article-content 등의 클래스 찾기
            article = soup.find('div', class_=lambda x: x and ('entry-content' in x.lower() or 'article-content' in x.lower()))

        if article:
            # 본문 단락들 찾기
            paragraphs = article.find_all('p')

            # 광고, 공유 버튼 등 제외
            content_paragraphs = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                # 너무 짧거나 링크만 있는 단락 제외
                if len(text) > 30 and not text.startswith('Read more:'):
                    content_paragraphs.append(text)

            content = '\n\n'.join(content_paragraphs)
            return content if content else "본문 없음"

        return "본문 없음"

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """저자 추출"""
        # author 클래스 찾기
        author_tag = soup.find('a', class_=lambda x: x and 'author' in x.lower())
        if author_tag:
            return author_tag.get_text(strip=True)

        # rel="author" 찾기
        author_rel = soup.find('a', {'rel': 'author'})
        if author_rel:
            return author_rel.get_text(strip=True)

        # meta 태그에서 찾기
        meta_author = soup.find('meta', {'name': 'author'})
        if meta_author:
            return meta_author.get('content', '').strip()

        # byline 찾기
        byline = soup.find('span', class_=lambda x: x and 'byline' in x.lower())
        if byline:
            return byline.get_text(strip=True)

        return "저자 미상"

    def _extract_date(self, soup: BeautifulSoup) -> str:
        """발행 날짜 추출"""
        # time 태그 찾기
        time_tag = soup.find('time')
        if time_tag:
            datetime_attr = time_tag.get('datetime')
            if datetime_attr:
                return datetime_attr

        # meta 태그에서 찾기
        meta_date = soup.find('meta', property='article:published_time')
        if meta_date:
            return meta_date.get('content', '').strip()

        meta_date_name = soup.find('meta', {'name': 'publish-date'})
        if meta_date_name:
            return meta_date_name.get('content', '').strip()

        return datetime.now().isoformat()

    def _extract_summary(self, soup: BeautifulSoup) -> str:
        """요약 추출"""
        # meta description
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '').strip()

        meta_og_desc = soup.find('meta', property='og:description')
        if meta_og_desc:
            return meta_og_desc.get('content', '').strip()

        # 첫 번째 단락을 요약으로 사용
        article = soup.find('article') or soup.find('div', class_='entry-content')
        if article:
            first_p = article.find('p')
            if first_p:
                return first_p.get_text(strip=True)[:200]

        return ""


# 테스트 코드
if __name__ == "__main__":
    crawler = CryptopolitanCrawler()

    # 최신 기사 목록 가져오기
    print("=" * 60)
    print("Cryptopolitan 크롤러 테스트")
    print("=" * 60)

    articles = crawler.get_latest_articles(limit=5)

    print(f"\n[RESULT] 발견된 기사 {len(articles)}개:")
    for i, article in enumerate(articles, 1):
        print(f"\n{i}. {article['title']}")
        print(f"   URL: {article['url']}")

    # 첫 번째 기사 상세 내용 가져오기
    if articles:
        print("\n" + "=" * 60)
        print("첫 번째 기사 상세 내용 크롤링")
        print("=" * 60)

        first_article = crawler.get_article_content(articles[0]['url'])
        if first_article:
            print(f"\n제목: {first_article['title']}")
            print(f"저자: {first_article['author']}")
            print(f"날짜: {first_article['published_date']}")
            print(f"요약: {first_article['summary'][:200]}...")
            print(f"\n본문 (처음 500자):\n{first_article['content'][:500]}...")
