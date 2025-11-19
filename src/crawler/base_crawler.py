"""
크롤러 베이스 클래스

모든 뉴스 사이트 크롤러가 상속받아야 하는 추상 클래스
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup


class BaseCrawler(ABC):
    """뉴스 크롤러 추상 베이스 클래스"""

    def __init__(self):
        """공통 초기화"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    @property
    @abstractmethod
    def source_name(self) -> str:
        """
        소스 이름 (예: "coindesk.com", "cryptopolitan.com")

        Returns:
            소스 도메인 이름
        """
        pass

    @property
    @abstractmethod
    def source_url(self) -> str:
        """
        크롤링할 메인 URL

        Returns:
            뉴스 목록 페이지 URL
        """
        pass

    @abstractmethod
    def get_latest_articles(self, limit: int = 10) -> List[Dict]:
        """
        최신 기사 목록을 가져옵니다.

        Args:
            limit: 가져올 기사 개수

        Returns:
            기사 목록 (각 기사는 최소한 'url', 'title' 포함)
        """
        pass

    @abstractmethod
    def get_article_content(self, url: str) -> Optional[Dict]:
        """
        개별 기사의 상세 내용을 가져옵니다.

        Args:
            url: 기사 URL

        Returns:
            기사 상세 정보 (title, content, author, published_date, summary 등)
            실패 시 None
        """
        pass

    def _fetch_page(self, url: str, timeout: int = 10) -> Optional[BeautifulSoup]:
        """
        웹페이지를 가져와서 BeautifulSoup 객체로 반환 (공통 메서드)

        Args:
            url: 페이지 URL
            timeout: 타임아웃 (초)

        Returns:
            BeautifulSoup 객체 또는 None
        """
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"[ERROR] 페이지 가져오기 실패 ({url}): {str(e)}")
            return None

    def __repr__(self):
        return f"<{self.__class__.__name__} source={self.source_name}>"
