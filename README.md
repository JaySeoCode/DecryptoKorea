# CoinDesk Auto Poster

CoinDesk.com의 최신 암호화폐 뉴스를 자동으로 크롤링하여 WordPress 사이트에 포스팅하는 봇입니다.

## 주요 기능

- 🕒 **30분 간격 자동 실행**: 새로운 기사를 자동으로 체크
- 📰 **CoinDesk 크롤링**: 최신 암호화폐 뉴스 자동 수집
- 🎨 **AI 이미지 생성**: Gemini API를 사용하여 기사 관련 이미지 자동 생성
- ✍️ **SEO 최적화**: 기사를 SEO 친화적인 형식으로 자동 요약
- 📝 **WordPress 자동 포스팅**: 이미지와 함께 자동으로 글 작성

## 프로젝트 구조

```
coindesk-auto-poster/
├── src/
│   ├── crawler/
│   │   └── coindesk_crawler.py     # CoinDesk 크롤링 모듈
│   ├── services/
│   │   ├── gemini_service.py       # Gemini API 서비스
│   │   └── wordpress_service.py    # WordPress API 서비스
│   ├── utils/
│   │   ├── storage.py              # 데이터 저장 유틸리티
│   │   └── logger.py               # 로깅 유틸리티
│   └── main.py                     # 메인 실행 파일
├── data/
│   └── processed_articles.json     # 처리된 기사 ID 목록
├── logs/
│   └── app.log                     # 애플리케이션 로그
├── images/                         # 생성된 이미지 임시 저장
├── .env                            # 환경 변수 (git에 포함되지 않음)
├── .env.example                    # 환경 변수 예시
├── requirements.txt                # Python 패키지 의존성
└── README.md                       # 프로젝트 문서
```

## 설치 방법

### 1. 저장소 클론
```bash
git clone https://github.com/JaySeoCode/Crypto_news_generator.git
cd Crypto_news_generator
```

### 2. 가상환경 생성 및 활성화
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
```bash
# .env.example을 .env로 복사
cp .env.example .env

# .env 파일을 편집하여 실제 API 키 입력
# - GEMINI_API_KEY: Google Gemini API 키
# - WORDPRESS_URL: WordPress 사이트 URL
# - WORDPRESS_USERNAME: WordPress 사용자명
# - WORDPRESS_APP_PASSWORD: WordPress 앱 비밀번호
```

## 사용 방법

### 기본 실행
```bash
python src/main.py
```

### 백그라운드 실행 (Windows)
```bash
start /B python src/main.py > output.log 2>&1
```

### 백그라운드 실행 (Linux/macOS)
```bash
nohup python src/main.py > output.log 2>&1 &
```

## API 키 발급 방법

### Gemini API 키
1. [Google AI Studio](https://makersuite.google.com/app/apikey) 접속
2. "Create API Key" 클릭
3. 발급된 키를 `.env` 파일의 `GEMINI_API_KEY`에 입력

### WordPress 앱 비밀번호
1. WordPress 관리자 페이지 로그인
2. 사용자 → 프로필 페이지 이동
3. "애플리케이션 비밀번호" 섹션에서 새 비밀번호 생성
4. 생성된 비밀번호를 `.env` 파일의 `WORDPRESS_APP_PASSWORD`에 입력

## 작동 원리

1. **크롤링**: 30분마다 CoinDesk.com에서 최신 뉴스 목록 확인
2. **중복 체크**: 이미 처리한 기사는 건너뛰기
3. **이미지 생성**: Gemini API로 기사 내용 기반 이미지 생성
4. **SEO 요약**: 기사를 SEO 최적화된 형식으로 요약
5. **포스팅**: WordPress에 이미지와 함께 자동 포스팅
6. **기록**: 처리된 기사 ID를 저장하여 중복 방지

## 주의사항

- 로컬에서 실행 시 컴퓨터를 계속 켜두어야 합니다
- API 키는 절대 GitHub에 업로드하지 마세요 (.gitignore에 포함됨)
- WordPress 사이트의 REST API가 활성화되어 있어야 합니다

## 라이선스

MIT License

## 기여

이슈 및 풀 리퀘스트는 언제나 환영합니다!
