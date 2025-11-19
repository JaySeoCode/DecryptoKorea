"""
CoinDesk 크롤링 모듈

CoinDesk.com에서 최신 암호화폐 뉴스를 크롤링하는 모듈입니다.
"""

from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import time
from .base_crawler import BaseCrawler


class CoinDeskCrawler(BaseCrawler):
    """CoinDesk 웹사이트 크롤러"""

    BASE_URL = "https://www.coindesk.com"

    def __init__(self):
        super().__init__()
        print("[INFO] CoinDesk 크롤러 초기화 완료")

    @property
    def source_name(self) -> str:
        """소스 이름 반환"""
        return "coindesk.com"

    @property
    def source_url(self) -> str:
        """크롤링할 메인 URL 반환"""
        return self.BASE_URL

    def get_latest_articles(self, limit: int = 10) -> List[Dict]:
        """
        CoinDesk 메인 페이지에서 최신 기사 목록을 가져옵니다.

        Args:
            limit: 가져올 기사 수 (기본값: 10)

        Returns:
            기사 정보 리스트 (제목, URL, 날짜 등)
        """
        try:
            print(f"[INFO] CoinDesk에서 최신 기사 {limit}개 크롤링 중...")
            response = self.session.get(self.BASE_URL, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')
            articles = []

            # CoinDesk의 기사 링크 찾기
            # 기사는 /markets/, /policy/, /business/, /tech/ 등의 카테고리로 시작
            article_links = soup.find_all('a', href=True)

            seen_urls = set()
            for link in article_links:
                href = link.get('href', '')

                # 기사 URL 패턴 확인
                if self._is_article_url(href) and href not in seen_urls:
                    full_url = self._get_full_url(href)

                    # 제목 추출
                    title = link.get_text(strip=True)
                    if not title or len(title) < 10:  # 너무 짧은 제목은 제외
                        continue

                    article_info = {
                        'url': full_url,
                        'title': title,
                        'relative_url': href,
                        'crawled_at': datetime.now().isoformat()
                    }

                    articles.append(article_info)
                    seen_urls.add(href)

                    if len(articles) >= limit:
                        break

            print(f"[SUCCESS] {len(articles)}개 기사 목록 수집 완료")
            return articles[:limit]

        except Exception as e:
            print(f"[ERROR] 기사 목록 크롤링 실패: {str(e)}")
            return []

    def get_article_content(self, url: str) -> Optional[Dict]:
        """
        개별 기사의 전체 내용을 가져옵니다.

        Args:
            url: 기사 URL

        Returns:
            기사 상세 정보 (제목, 본문, 저자, 날짜 등)
        """
        try:
            print(f"[INFO] 기사 내용 크롤링 중: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # 제목 추출
            title = self._extract_title(soup)

            # 본문 추출
            content = self._extract_content(soup)

            # 저자 추출
            author = self._extract_author(soup)

            # 날짜 추출
            published_date = self._extract_date(soup)

            # 요약 추출 (있는 경우)
            summary = self._extract_summary(soup)

            article_data = {
                'url': url,
                'title': title,
                'content': content,
                'author': author,
                'published_date': published_date,
                'summary': summary,
                'crawled_at': datetime.now().isoformat()
            }

            print(f"[SUCCESS] 기사 내용 크롤링 완료: {title[:50]}...")
            return article_data

        except Exception as e:
            print(f"[ERROR] 기사 내용 크롤링 실패 ({url}): {str(e)}")
            return None

    def _is_article_url(self, url: str) -> bool:
        """URL이 기사인지 확인"""
        article_patterns = ['/markets/', '/policy/', '/business/', '/tech/', '/consensus-magazine/']
        # 날짜 패턴 포함 (예: /2025/11/16/)
        return any(pattern in url for pattern in article_patterns) and '/20' in url

    def _get_full_url(self, url: str) -> str:
        """상대 URL을 절대 URL로 변환"""
        if url.startswith('http'):
            return url
        return self.BASE_URL + url

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """제목 추출"""
        # h1 태그에서 제목 찾기
        title_tag = soup.find('h1')
        if title_tag:
            return title_tag.get_text(strip=True)

        # meta 태그에서 찾기
        meta_title = soup.find('meta', property='og:title')
        if meta_title:
            return meta_title.get('content', '').strip()

        return "제목 없음"

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """본문 추출"""
        # CoinDesk는 article 태그 내에 본문이 있음
        article = soup.find('article')
        if not article:
            article = soup.find('div', class_='article-body')

        if article:
            # 본문 단락들 찾기
            paragraphs = article.find_all('p')
            content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            return content

        return "본문 없음"

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """저자 추출"""
        # CoinDesk 저자 패턴
        author_tag = soup.find('a', {'rel': 'author'})
        if author_tag:
            return author_tag.get_text(strip=True)

        # meta 태그에서 찾기
        meta_author = soup.find('meta', {'name': 'author'})
        if meta_author:
            return meta_author.get('content', '').strip()

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

        return ""

    def crawl_multiple_articles(self, urls: List[str], delay: float = 1.0) -> List[Dict]:
        """
        여러 기사를 크롤링합니다.

        Args:
            urls: 기사 URL 리스트
            delay: 각 요청 사이 대기 시간 (초)

        Returns:
            기사 데이터 리스트
        """
        articles = []
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] 기사 크롤링 중...")
            article = self.get_article_content(url)
            if article:
                articles.append(article)

            # 서버 부하 방지를 위한 대기
            if i < len(urls):
                time.sleep(delay)

        return articles


# 테스트 코드
if __name__ == "__main__":
    crawler = CoinDeskCrawler()

    # 최신 기사 목록 가져오기
    print("=" * 60)
    print("CoinDesk 크롤러 테스트")
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
