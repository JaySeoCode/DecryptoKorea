"""
Gemini API 서비스 모듈

Google Gemini API를 사용하여:
1. 기사 내용을 SEO 최적화된 형식으로 요약
2. 기사 관련 이미지 생성 (이미지 URL 또는 프롬프트)
"""

import google.generativeai as genai
import os
import requests
from typing import Dict, Optional
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image

# 환경 변수 로드
load_dotenv()


class GeminiService:
    """Gemini API 서비스 클래스"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Gemini API 키 (없으면 환경 변수에서 로드)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')

        if not self.api_key:
            raise ValueError("Gemini API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")

        # Gemini 설정
        genai.configure(api_key=self.api_key)

        # Gemini 2.5 Flash - 텍스트 생성용
        self.text_model = genai.GenerativeModel('gemini-2.5-flash')

        # Gemini 2.5 Flash Image - 이미지 생성용
        self.image_model = genai.GenerativeModel('gemini-2.5-flash-image')

        print("[INFO] Gemini 2.5 API 초기화 완료")

    def classify_article(self, article: Dict) -> str:
        """
        기사가 BTC 관련인지 ALT 코인 관련인지 분류합니다.

        Args:
            article: 기사 정보

        Returns:
            'BTC' 또는 'ALT'
        """
        try:
            title = article.get('title', '')
            content = article.get('content', '')[:500]

            prompt = f"""
다음 암호화폐 뉴스 기사가 비트코인(BTC)에 관한 것인지, 알트코인(ALT)에 관한 것인지 분류해주세요.

제목: {title}
내용: {content}

판단 기준:
- BTC: 비트코인이 주요 주제인 경우
- ALT: 이더리움, 리플, 솔라나 등 비트코인 이외의 알트코인이 주요 주제인 경우

오직 'BTC' 또는 'ALT' 중 하나만 응답하세요.
"""

            response = self.text_model.generate_content(prompt)
            classification = response.text.strip().upper()

            if 'BTC' in classification:
                return 'BTC'
            elif 'ALT' in classification:
                return 'ALT'
            else:
                # 기본값: 제목에 bitcoin이 있으면 BTC, 아니면 ALT
                if 'bitcoin' in title.lower() or 'btc' in title.lower():
                    return 'BTC'
                else:
                    return 'ALT'

        except Exception as e:
            print(f"[ERROR] 기사 분류 실패: {str(e)}")
            # 기본값 반환
            return 'BTC'

    def summarize_for_seo(self, article: Dict) -> Dict:
        """
        기사를 SEO 최적화된 형식으로 요약합니다.

        Args:
            article: 기사 정보 (title, content 포함)

        Returns:
            SEO 최적화된 요약 정보
        """
        try:
            title = article.get('title', '')
            content = article.get('content', '')
            original_summary = article.get('summary', '')

            # 프롬프트 작성
            prompt = f"""
다음은 암호화폐 관련 뉴스 기사입니다. 이 기사를 SEO에 최적화된 형식으로 요약해주세요.

원문 제목: {title}

원문 내용:
{content[:2000]}

요구사항:
1. 매력적이고 SEO 친화적인 한글 제목 (50자 이내)
2. 메타 설명 (150자 이내, 핵심 키워드 포함)
3. 본문 요약 (300-500자, 문단 구분)
4. 주요 키워드 5개 (쉼표로 구분)
5. H2 헤딩 2-3개 제안

응답 형식:
제목: [여기에 제목]
메타설명: [여기에 메타 설명]
본문:
[여기에 요약된 본문]

키워드: [키워드1, 키워드2, 키워드3, 키워드4, 키워드5]
헤딩:
- [H2 헤딩 1]
- [H2 헤딩 2]
- [H2 헤딩 3]
"""

            try:
                print(f"[INFO] Gemini로 SEO 요약 생성 중: {title[:50]}...")
            except UnicodeEncodeError:
                print(f"[INFO] Gemini로 SEO 요약 생성 중: [Contains special characters]")
            response = self.text_model.generate_content(prompt)

            # 응답 파싱
            seo_content = self._parse_seo_response(response.text)
            seo_content['original_title'] = title
            seo_content['original_content'] = content

            print(f"[SUCCESS] SEO 요약 생성 완료")
            return seo_content

        except Exception as e:
            print(f"[ERROR] SEO 요약 생성 실패: {str(e)}")
            # 실패 시 원본 반환
            return {
                'title': title,
                'meta_description': original_summary[:150] if original_summary else title,
                'body': content[:500],
                'keywords': 'cryptocurrency, bitcoin, blockchain, crypto news',
                'headings': [],
                'original_title': title,
                'original_content': content
            }

    def _parse_seo_response(self, response_text: str) -> Dict:
        """Gemini 응답을 파싱하여 구조화된 데이터로 변환"""
        lines = response_text.strip().split('\n')

        result = {
            'title': '',
            'meta_description': '',
            'body': '',
            'keywords': '',
            'headings': []
        }

        current_section = None
        body_lines = []

        for line in lines:
            line = line.strip()

            if line.startswith('제목:'):
                result['title'] = line.replace('제목:', '').strip()
            elif line.startswith('메타설명:') or line.startswith('메타 설명:'):
                result['meta_description'] = line.replace('메타설명:', '').replace('메타 설명:', '').strip()
            elif line.startswith('키워드:'):
                result['keywords'] = line.replace('키워드:', '').strip()
            elif line.startswith('본문:'):
                current_section = 'body'
            elif line.startswith('헤딩:'):
                current_section = 'headings'
            elif line.startswith('-') and current_section == 'headings':
                result['headings'].append(line.replace('-', '').strip())
            elif current_section == 'body' and line and not line.startswith('키워드:') and not line.startswith('헤딩:'):
                body_lines.append(line)

        result['body'] = '\n\n'.join(body_lines)

        return result

    def generate_image_prompt(self, article: Dict) -> str:
        """
        기사 내용을 바탕으로 이미지 생성 프롬프트를 만듭니다.

        Args:
            article: 기사 정보

        Returns:
            이미지 생성 프롬프트 (영문)
        """
        try:
            title = article.get('title', '')
            content = article.get('content', '')[:500]

            prompt = f"""
다음 암호화폐 뉴스 기사에 어울리는 이미지를 생성하기 위한 프롬프트를 영어로 작성해주세요.

기사 제목: {title}
기사 내용: {content}

요구사항:
- 암호화폐, 비트코인, 블록체인 관련 시각적 요소 포함
- 전문적이고 현대적인 느낌
- 뉴스 기사에 적합한 이미지
- 50단어 이내의 영문 프롬프트

프롬프트만 작성하세요:
"""

            print(f"[INFO] 이미지 프롬프트 생성 중...")
            response = self.text_model.generate_content(prompt)
            image_prompt = response.text.strip()

            print(f"[SUCCESS] 이미지 프롬프트 생성 완료")
            return image_prompt

        except Exception as e:
            print(f"[ERROR] 이미지 프롬프트 생성 실패: {str(e)}")
            return "Professional cryptocurrency news article image, bitcoin, blockchain, modern digital finance"

    def generate_image(self, article: Dict, save_path: str = "images/article_image.jpg") -> Optional[str]:
        """
        Gemini 2.5를 사용하여 기사 관련 이미지를 생성합니다.

        Args:
            article: 기사 정보
            save_path: 저장 경로

        Returns:
            저장된 이미지 경로 또는 None
        """
        try:
            # 이미지 생성 프롬프트 작성
            title = article.get('title', '')
            content = article.get('content', '')[:300]

            prompt = f"""Create a professional news article image for this cryptocurrency news:

Title: {title}

Content: {content}

Create a modern, professional image suitable for a cryptocurrency news article. Include visual elements related to Bitcoin, blockchain, or digital finance. The image should be eye-catching and appropriate for a news website."""

            print(f"[INFO] Gemini로 이미지 생성 중...")
            response = self.image_model.generate_content(prompt)

            # 이미지 데이터 추출 및 저장
            if hasattr(response, 'parts') and len(response.parts) > 0:
                for part in response.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # 디렉토리 생성
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)

                        # 이미지 데이터 저장
                        image_data = part.inline_data.data
                        with open(save_path, 'wb') as f:
                            f.write(image_data)

                        print(f"[SUCCESS] 이미지 생성 및 저장 완료: {save_path}")
                        return save_path

            print("[WARNING] 생성된 이미지 데이터를 찾을 수 없습니다")
            return None

        except Exception as e:
            print(f"[ERROR] 이미지 생성 실패: {str(e)}")
            # 실패 시 스톡 이미지 다운로드 시도
            return self.get_stock_image(article.get('title', 'cryptocurrency'), save_path)

    def get_stock_image(self, keywords: str, save_path: str = "images/article_image.jpg") -> Optional[str]:
        """
        Unsplash API를 사용하여 무료 스톡 이미지를 가져옵니다.

        Args:
            keywords: 검색 키워드
            save_path: 저장 경로

        Returns:
            저장된 이미지 경로 또는 None
        """
        try:
            # Unsplash API (무료, API 키 불필요)
            # 키워드 정리
            search_term = keywords.split(',')[0].strip() if ',' in keywords else keywords
            search_term = search_term.replace('cryptocurrency', 'bitcoin').replace('crypto', 'blockchain')

            url = f"https://source.unsplash.com/1200x630/?{search_term},technology"

            print(f"[INFO] 이미지 다운로드 중: {search_term}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # 디렉토리 생성
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # 이미지 저장
            img = Image.open(BytesIO(response.content))
            img.save(save_path, 'JPEG', quality=85)

            print(f"[SUCCESS] 이미지 저장 완료: {save_path}")
            return save_path

        except Exception as e:
            print(f"[ERROR] 이미지 다운로드 실패: {str(e)}")
            return None

    def process_article_complete(self, article: Dict) -> Dict:
        """
        기사를 완전히 처리합니다 (분류 + SEO 요약 + 이미지)

        Args:
            article: 원본 기사 정보

        Returns:
            처리된 기사 정보 (분류, SEO 요약, 이미지 경로 포함)
        """
        # 기사 분류 (BTC vs ALT)
        classification = self.classify_article(article)
        print(f"[INFO] 기사 분류: {classification}")

        # SEO 요약 생성
        seo_content = self.summarize_for_seo(article)

        # Gemini로 이미지 생성
        image_path = self.generate_image(article)

        # 결과 통합
        result = {
            **article,
            'classification': classification,  # BTC 또는 ALT
            'seo_title': seo_content['title'],
            'seo_meta_description': seo_content['meta_description'],
            'seo_body': seo_content['body'],
            'seo_keywords': seo_content['keywords'],
            'seo_headings': seo_content['headings'],
            'image_path': image_path,
            'image_prompt': self.generate_image_prompt(article)
        }

        return result


# 테스트 코드
if __name__ == "__main__":
    print("=" * 60)
    print("Gemini API 서비스 테스트")
    print("=" * 60)

    try:
        service = GeminiService()

        # 테스트 기사
        test_article = {
            'title': 'Bitcoin Falls Below $94,000 for First Time Since May',
            'content': '''Bitcoin fell below $94,000 for the first time since May amid extreme fear sentiment in the cryptocurrency market. Analysts highlighted retail distress, rare social-dominance surges and warnings of a possible deeper pullback as several major tokens remained under pressure. The decline comes as investors reassess their positions in digital assets following recent market volatility.''',
            'summary': 'Bitcoin drops below $94,000 as market sentiment turns fearful',
            'author': 'Crypto News Team',
            'published_date': '2025-11-17'
        }

        # SEO 요약 테스트
        print("\n[TEST 1] SEO 요약 생성")
        seo_result = service.summarize_for_seo(test_article)
        print(f"\nSEO 제목: {seo_result['title']}")
        print(f"메타 설명: {seo_result['meta_description']}")
        print(f"키워드: {seo_result['keywords']}")
        print(f"본문 (처음 200자): {seo_result['body'][:200]}...")

        # 이미지 생성 테스트 (Gemini 2.5)
        print("\n[TEST 2] Gemini 2.5로 이미지 생성")
        image_path = service.generate_image(test_article, "images/test_gemini_image.jpg")
        if image_path:
            print(f"이미지 저장 경로: {image_path}")

        # 전체 처리 테스트
        print("\n[TEST 3] 전체 기사 처리 (SEO + 이미지)")
        processed = service.process_article_complete(test_article)
        print(f"SEO 제목: {processed.get('seo_title', 'N/A')}")
        print(f"이미지 경로: {processed.get('image_path', 'N/A')}")

        print("\n" + "=" * 60)
        print("테스트 완료")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] 테스트 실패: {str(e)}")
