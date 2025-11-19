"""
WordPress API 서비스 모듈

WordPress REST API를 사용하여:
1. 이미지 업로드
2. 글 작성
3. Featured Image 설정
"""

import requests
import os
from typing import Dict, Optional
from dotenv import load_dotenv
import base64

# 환경 변수 로드
load_dotenv()


class WordPressService:
    """WordPress REST API 서비스 클래스"""

    def __init__(self, url: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None):
        """
        Args:
            url: WordPress 사이트 URL (없으면 환경 변수에서 로드)
            username: WordPress 사용자명 (없으면 환경 변수에서 로드)
            password: WordPress 앱 비밀번호 (없으면 환경 변수에서 로드)
        """
        self.url = url or os.getenv('WORDPRESS_URL')
        self.username = username or os.getenv('WORDPRESS_USERNAME')
        self.password = password or os.getenv('WORDPRESS_APP_PASSWORD')

        if not all([self.url, self.username, self.password]):
            raise ValueError("WordPress 설정이 완전하지 않습니다. .env 파일을 확인하세요.")

        # URL 정리 (마지막 슬래시 제거)
        self.url = self.url.rstrip('/')

        # API 엔드포인트
        self.api_url = f"{self.url}/wp-json/wp/v2"

        # 인증 정보
        credentials = f"{self.username}:{self.password}"
        token = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {token}',
        }

        print(f"[INFO] WordPress API 초기화 완료: {self.url}")

    def upload_image(self, image_path: str, title: str = None) -> Optional[int]:
        """
        WordPress에 이미지를 업로드합니다.

        Args:
            image_path: 업로드할 이미지 파일 경로
            title: 이미지 제목 (선택)

        Returns:
            업로드된 이미지의 미디어 ID (실패 시 None)
        """
        try:
            if not os.path.exists(image_path):
                print(f"[ERROR] 이미지 파일을 찾을 수 없습니다: {image_path}")
                return None

            # 이미지 파일 읽기 및 최적화
            from PIL import Image
            from io import BytesIO

            # 이미지 열기
            img = Image.open(image_path)

            # 크기 조정 (너무 크면 압축)
            max_size = (1920, 1080)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                print(f"[INFO] 이미지 크기 조정: {img.size}")

            # JPEG로 변환하여 메모리에 저장
            buffer = BytesIO()
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            img.save(buffer, format='JPEG', quality=85, optimize=True)
            img_data = buffer.getvalue()

            # 파일 크기 확인
            file_size_mb = len(img_data) / (1024 * 1024)
            print(f"[INFO] 이미지 파일 크기: {file_size_mb:.2f}MB")

            # 파일명 추출
            filename = os.path.basename(image_path)

            # 제목 설정
            if not title:
                title = os.path.splitext(filename)[0]

            headers = {
                **self.headers,
                'Content-Type': 'image/jpeg',
                'Content-Disposition': f'attachment; filename="{filename}"'
            }

            print(f"[INFO] 이미지 업로드 중: {filename}")

            response = requests.post(
                f"{self.api_url}/media",
                headers=headers,
                data=img_data,
                timeout=120  # 30초에서 120초로 증가
            )

            response.raise_for_status()
            media_data = response.json()
            media_id = media_data.get('id')

            print(f"[SUCCESS] 이미지 업로드 완료 (ID: {media_id})")
            return media_id

        except Exception as e:
            print(f"[ERROR] 이미지 업로드 실패: {str(e)}")
            return None

    def create_post(self, title: str, content: str, featured_image_id: Optional[int] = None,
                    status: str = 'publish', categories: list = None, tags: list = None) -> Optional[int]:
        """
        WordPress에 글을 작성합니다.

        Args:
            title: 글 제목
            content: 글 내용 (HTML)
            featured_image_id: Featured Image 미디어 ID (선택)
            status: 글 상태 ('draft', 'publish', 'private')
            categories: 카테고리 ID 리스트
            tags: 태그 ID 리스트

        Returns:
            작성된 글의 포스트 ID (실패 시 None)
        """
        try:
            post_data = {
                'title': title,
                'content': content,
                'status': status,
            }

            if featured_image_id:
                post_data['featured_media'] = featured_image_id

            if categories:
                post_data['categories'] = categories

            if tags:
                post_data['tags'] = tags

            print(f"[INFO] 글 작성 중: {title[:50]}...")

            response = requests.post(
                f"{self.api_url}/posts",
                headers=self.headers,
                json=post_data,
                timeout=30
            )

            response.raise_for_status()
            post_data = response.json()
            post_id = post_data.get('id')
            post_url = post_data.get('link')

            print(f"[SUCCESS] 글 작성 완료 (ID: {post_id})")
            print(f"[URL] {post_url}")

            return post_id

        except Exception as e:
            print(f"[ERROR] 글 작성 실패: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"[ERROR] 응답 내용: {e.response.text[:500]}")
            return None

    def get_or_create_tag(self, tag_name: str) -> Optional[int]:
        """
        태그를 가져오거나 생성합니다.

        Args:
            tag_name: 태그 이름

        Returns:
            태그 ID (실패 시 None)
        """
        try:
            # 기존 태그 검색
            response = requests.get(
                f"{self.api_url}/tags",
                headers=self.headers,
                params={'search': tag_name},
                timeout=10
            )
            response.raise_for_status()
            tags = response.json()

            # 정확히 일치하는 태그 찾기
            for tag in tags:
                if tag['name'].lower() == tag_name.lower():
                    print(f"[INFO] 기존 태그 사용: {tag_name} (ID: {tag['id']})")
                    return tag['id']

            # 태그가 없으면 생성
            response = requests.post(
                f"{self.api_url}/tags",
                headers=self.headers,
                json={'name': tag_name},
                timeout=10
            )
            response.raise_for_status()
            tag_data = response.json()
            tag_id = tag_data.get('id')
            print(f"[SUCCESS] 새 태그 생성: {tag_name} (ID: {tag_id})")
            return tag_id

        except Exception as e:
            print(f"[ERROR] 태그 생성/조회 실패: {str(e)}")
            return None

    def get_or_create_category(self, category_name: str) -> Optional[int]:
        """
        카테고리를 가져오거나 생성합니다.

        Args:
            category_name: 카테고리 이름

        Returns:
            카테고리 ID (실패 시 None)
        """
        try:
            # 기존 카테고리 검색
            response = requests.get(
                f"{self.api_url}/categories",
                headers=self.headers,
                params={'search': category_name},
                timeout=10
            )
            response.raise_for_status()
            categories = response.json()

            # 정확히 일치하는 카테고리 찾기
            for cat in categories:
                if cat['name'].lower() == category_name.lower():
                    print(f"[INFO] 기존 카테고리 사용: {category_name} (ID: {cat['id']})")
                    return cat['id']

            # 카테고리가 없으면 생성
            response = requests.post(
                f"{self.api_url}/categories",
                headers=self.headers,
                json={'name': category_name},
                timeout=10
            )
            response.raise_for_status()
            cat_data = response.json()
            cat_id = cat_data.get('id')
            print(f"[SUCCESS] 새 카테고리 생성: {category_name} (ID: {cat_id})")
            return cat_id

        except Exception as e:
            print(f"[ERROR] 카테고리 생성/조회 실패: {str(e)}")
            return None

    def publish_article(self, article: Dict, image_path: Optional[str] = None) -> Optional[int]:
        """
        기사를 이미지와 함께 WordPress에 게시합니다.

        Args:
            article: 기사 정보 (title, content 포함)
            image_path: 이미지 파일 경로 (선택)

        Returns:
            작성된 글의 포스트 ID (실패 시 None)
        """
        # 이미지 업로드
        featured_image_id = None
        if image_path and os.path.exists(image_path):
            featured_image_id = self.upload_image(image_path, article.get('title'))

        # 태그 처리 (BTC 또는 ALT)
        tag_ids = []
        classification = article.get('classification', 'BTC')
        tag_name = f"#{classification}"
        tag_id = self.get_or_create_tag(tag_name)
        if tag_id:
            tag_ids.append(tag_id)

        # 카테고리 처리 (소스별 동적 생성)
        category_ids = []
        # article에서 source 필드 읽기 (없으면 기본값 coindesk.com)
        source = article.get('source', 'coindesk.com')
        category_name = source  # 소스명을 그대로 카테고리로 사용
        category_id = self.get_or_create_category(category_name)
        if category_id:
            category_ids.append(category_id)

        # 글 작성
        title = article.get('seo_title') or article.get('title', '제목 없음')

        # HTML 컨텐츠 구성
        content_parts = []

        # 메타 설명
        if article.get('seo_meta_description'):
            content_parts.append(f"<p><strong>{article['seo_meta_description']}</strong></p>")

        # 본문
        if article.get('seo_body'):
            # 줄바꿈을 HTML 단락으로 변환
            body_paragraphs = article['seo_body'].split('\n\n')
            for para in body_paragraphs:
                if para.strip():
                    content_parts.append(f"<p>{para.strip()}</p>")

        # 키워드
        if article.get('seo_keywords'):
            content_parts.append(f"<p><em>키워드: {article['seo_keywords']}</em></p>")

        # 원문 링크
        if article.get('url'):
            content_parts.append(f'<p><a href="{article["url"]}" target="_blank">원문 보기</a></p>')

        content = '\n'.join(content_parts)

        # 글 게시
        post_id = self.create_post(
            title=title,
            content=content,
            featured_image_id=featured_image_id,
            status='publish',
            categories=category_ids if category_ids else None,
            tags=tag_ids if tag_ids else None
        )

        return post_id

    def test_connection(self) -> bool:
        """
        WordPress API 연결을 테스트합니다.

        Returns:
            연결 성공 여부
        """
        try:
            print("[INFO] WordPress API 연결 테스트 중...")
            response = requests.get(
                f"{self.api_url}/posts",
                headers=self.headers,
                params={'per_page': 1},
                timeout=10
            )
            response.raise_for_status()
            print("[SUCCESS] WordPress API 연결 성공!")
            return True
        except Exception as e:
            print(f"[ERROR] WordPress API 연결 실패: {str(e)}")
            return False


# 테스트 코드
if __name__ == "__main__":
    print("=" * 60)
    print("WordPress API 서비스 테스트")
    print("=" * 60)

    try:
        service = WordPressService()

        # 연결 테스트
        print("\n[TEST 1] 연결 테스트")
        if service.test_connection():
            print("[SUCCESS] 연결 성공")
        else:
            print("[ERROR] 연결 실패")
            exit(1)

        # 이미지 업로드 테스트
        print("\n[TEST 2] 이미지 업로드 테스트")
        test_image_path = "images/bitcoin_100k_test.jpg"

        if os.path.exists(test_image_path):
            media_id = service.upload_image(test_image_path, "Test Bitcoin Image")
            print(f"업로드된 미디어 ID: {media_id}")
        else:
            print(f"[WARNING] 테스트 이미지를 찾을 수 없습니다: {test_image_path}")
            media_id = None

        # 글 작성 테스트
        print("\n[TEST 3] 글 작성 테스트")
        test_article = {
            'title': '[테스트] Bitcoin Surges Past $100,000',
            'seo_title': '[테스트] 비트코인 10만 달러 돌파!',
            'seo_meta_description': '비트코인이 역사적인 10만 달러를 돌파했습니다.',
            'seo_body': '최근 비트코인이 사상 최초로 10만 달러를 돌파하며 암호화폐 시장에 큰 이정표를 세웠습니다.\n\n이번 상승은 기관 투자자들의 지속적인 관심과 함께 이루어졌습니다.',
            'seo_keywords': '비트코인, 암호화폐, 10만달러, 투자',
            'url': 'https://example.com/bitcoin-100k'
        }

        post_id = service.publish_article(test_article, test_image_path if media_id else None)

        if post_id:
            print(f"\n[SUCCESS] 테스트 글이 작성되었습니다 (Post ID: {post_id})")
        else:
            print("\n[ERROR] 글 작성 실패")

        print("\n" + "=" * 60)
        print("테스트 완료")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
