"""
데이터 저장 및 관리 모듈 (Supabase 버전)

처리된 기사 목록을 Supabase PostgreSQL에 저장하여 중복 포스팅을 방지합니다.
클라우드 배포 환경(Railway/Render)에서 안정적으로 동작합니다.
"""

import os
from typing import List, Dict, Set
from datetime import datetime
from supabase import create_client, Client


class ArticleStorage:
    """Supabase 기반 기사 저장소 관리 클래스"""

    def __init__(self):
        """
        Supabase 클라이언트 초기화
        환경 변수 필요:
            - SUPABASE_URL: Supabase 프로젝트 URL
            - SUPABASE_KEY: Supabase API 키 (anon/public key)
        """
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')

        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY environment variables are required. "
                "Please check your .env file or deployment environment variables."
            )

        try:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            print("[INFO] Supabase 연결 성공")
        except Exception as e:
            print(f"[ERROR] Supabase 연결 실패: {str(e)}")
            raise

    def load_processed_articles(self) -> List[Dict]:
        """
        처리된 기사 목록을 로드합니다.

        Returns:
            처리된 기사 리스트
        """
        try:
            response = self.supabase.table('processed_articles')\
                .select('*')\
                .order('processed_at', desc=True)\
                .execute()

            return response.data if response.data else []
        except Exception as e:
            print(f"[ERROR] 기사 목록 로드 실패: {str(e)}")
            return []

    def save_processed_article(self, article: Dict):
        """
        처리된 기사를 저장합니다.

        Args:
            article: 기사 정보 딕셔너리
        """
        try:
            # 중복 확인
            if self.is_article_processed(article['url']):
                print(f"[INFO] 이미 처리된 기사: {article['url']}")
                return

            # 새 기사 저장
            processed_entry = {
                'url': article['url'],
                'title': article.get('title', ''),
                'source': article.get('source', 'unknown'),
                'published_date': article.get('published_date', ''),
                'processed_at': datetime.now().isoformat(),
            }

            self.supabase.table('processed_articles').insert(processed_entry).execute()

            try:
                print(f"[SUCCESS] 기사 저장됨: {article.get('title', 'Unknown')[:50]}")
            except UnicodeEncodeError:
                print(f"[SUCCESS] 기사 저장됨: [Contains special characters]")

        except Exception as e:
            print(f"[ERROR] 기사 저장 실패: {str(e)}")

    def is_article_processed(self, url: str) -> bool:
        """
        기사가 이미 처리되었는지 확인합니다.

        Args:
            url: 기사 URL

        Returns:
            처리 여부 (True/False)
        """
        try:
            response = self.supabase.table('processed_articles')\
                .select('url')\
                .eq('url', url)\
                .execute()

            return len(response.data) > 0 if response.data else False
        except Exception as e:
            print(f"[ERROR] 기사 확인 실패: {str(e)}")
            return False

    def get_processed_urls(self) -> Set[str]:
        """
        처리된 기사 URL 세트를 반환합니다.

        Returns:
            URL 세트
        """
        try:
            response = self.supabase.table('processed_articles')\
                .select('url')\
                .execute()

            if response.data:
                return {article['url'] for article in response.data}
            return set()
        except Exception as e:
            print(f"[ERROR] URL 목록 조회 실패: {str(e)}")
            return set()

    def filter_new_articles(self, article_list: List[Dict]) -> List[Dict]:
        """
        새로운 기사만 필터링합니다.

        Args:
            article_list: 기사 리스트

        Returns:
            처리되지 않은 새 기사 리스트
        """
        processed_urls = self.get_processed_urls()
        new_articles = [
            article for article in article_list
            if article['url'] not in processed_urls
        ]

        print(f"[INFO] 전체 {len(article_list)}개 중 새 기사 {len(new_articles)}개 발견")
        return new_articles

    def get_stats(self) -> Dict:
        """
        저장소 통계를 반환합니다.

        Returns:
            통계 정보 딕셔너리
        """
        try:
            # 전체 기사 수
            response = self.supabase.table('processed_articles')\
                .select('*', count='exact')\
                .execute()

            articles = response.data if response.data else []
            total_count = len(articles)

            if total_count == 0:
                return {
                    'total_articles': 0,
                    'oldest_article': None,
                    'newest_article': None,
                    'by_source': {}
                }

            # 소스별 통계
            by_source = {}
            for article in articles:
                source = article.get('source', 'unknown')
                if source not in by_source:
                    by_source[source] = 0
                by_source[source] += 1

            # 날짜순 정렬
            sorted_articles = sorted(
                articles,
                key=lambda x: x.get('processed_at', ''),
                reverse=True
            )

            return {
                'total_articles': total_count,
                'oldest_article': sorted_articles[-1] if sorted_articles else None,
                'newest_article': sorted_articles[0] if sorted_articles else None,
                'by_source': by_source
            }
        except Exception as e:
            print(f"[ERROR] 통계 조회 실패: {str(e)}")
            return {
                'total_articles': 0,
                'oldest_article': None,
                'newest_article': None,
                'by_source': {}
            }

    def clear_all(self):
        """모든 저장된 기사를 삭제합니다 (주의!)"""
        try:
            # Supabase에서 모든 레코드 삭제
            # 주의: 이 작업은 되돌릴 수 없습니다!
            self.supabase.table('processed_articles').delete().neq('id', 0).execute()
            print("[WARNING] 모든 기사 기록이 삭제되었습니다")
        except Exception as e:
            print(f"[ERROR] 삭제 실패: {str(e)}")


# 테스트 코드
if __name__ == "__main__":
    # 환경 변수 로드
    from dotenv import load_dotenv
    load_dotenv()

    storage = ArticleStorage()

    print("=" * 60)
    print("Supabase 저장소 테스트")
    print("=" * 60)

    # 테스트 기사 데이터
    test_article = {
        'url': 'https://www.coindesk.com/test-article-supabase-1',
        'title': 'Supabase 테스트 기사 제목',
        'source': 'coindesk',
        'published_date': '2025-01-18'
    }

    # 기사 저장
    print("\n1. 기사 저장 테스트")
    storage.save_processed_article(test_article)

    # 중복 확인
    print("\n2. 중복 확인 테스트")
    if storage.is_article_processed(test_article['url']):
        print("[SUCCESS] 기사가 저장소에 있습니다")
    else:
        print("[ERROR] 기사를 찾을 수 없습니다")

    # 같은 기사 다시 저장 시도
    print("\n3. 중복 저장 시도")
    storage.save_processed_article(test_article)

    # 새 기사 필터링 테스트
    print("\n4. 새 기사 필터링 테스트")
    article_list = [
        test_article,  # 이미 처리됨
        {'url': 'https://www.coindesk.com/test-article-new-1', 'title': '새 기사 1', 'source': 'coindesk'},
        {'url': 'https://www.coindesk.com/test-article-new-2', 'title': '새 기사 2', 'source': 'coindesk'},
    ]

    new_articles = storage.filter_new_articles(article_list)
    print(f"새 기사: {[a['title'] for a in new_articles]}")

    # 통계 확인
    print("\n5. 저장소 통계")
    stats = storage.get_stats()
    print(f"총 기사 수: {stats['total_articles']}")
    print(f"소스별 통계: {stats['by_source']}")
    if stats['newest_article']:
        print(f"최근 기사: {stats['newest_article']['title']}")

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)
