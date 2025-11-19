# DecryptoKorea 클라우드 배포 가이드

이 가이드는 DecryptoKorea 자동 뉴스 게시 봇을 Railway 또는 Render에 배포하는 방법을 설명합니다.

## 📋 목차

1. [사전 준비](#사전-준비)
2. [Supabase 설정](#supabase-설정)
3. [Railway 배포](#railway-배포-추천)
4. [Render 배포](#render-배포-완전-무료)
5. [배포 후 확인](#배포-후-확인)
6. [문제 해결](#문제-해결)

---

## 🛠️ 사전 준비

### 1. 필수 계정

다음 계정들이 필요합니다:

- ✅ **GitHub 계정** (코드 리포지토리)
- ✅ **Supabase 계정** (무료) - https://supabase.com
- ✅ **Railway 계정** (추천) - https://railway.app
  - 또는 **Render 계정** (완전 무료) - https://render.com
- ✅ **Google Cloud 계정** (Gemini API)
- ✅ **WordPress 사이트** (게시 대상)

### 2. 환경 변수 준비

다음 값들을 미리 준비하세요:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
WORDPRESS_URL=https://yoursite.com
WORDPRESS_USERNAME=admin
WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key-here
```

---

## 🗄️ Supabase 설정

### 1단계: Supabase 프로젝트 생성

1. https://supabase.com 접속
2. "New Project" 클릭
3. 프로젝트 정보 입력:
   - **Name**: `decryptokorea`
   - **Database Password**: 안전한 비밀번호 설정
   - **Region**: `Northeast Asia (Seoul)` 선택 (한국에서 가장 빠름)
4. "Create new project" 클릭
5. 프로젝트 생성 완료까지 1-2분 대기

### 2단계: 데이터베이스 테이블 생성

1. 프로젝트 대시보드에서 **SQL Editor** 클릭
2. "New query" 클릭
3. `database/supabase_schema.sql` 파일의 내용을 복사해서 붙여넣기
4. **Run** 버튼 클릭
5. 성공 메시지 확인:
   ```
   ✅ Supabase 스키마 생성 완료!
   테이블: processed_articles
   인덱스: 3개 (url, source, processed_at)
   RLS 정책: 4개 (SELECT, INSERT, UPDATE, DELETE)
   ```

### 3단계: API 키 복사

1. 프로젝트 대시보드에서 **Settings** → **API** 클릭
2. 다음 정보를 복사:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** 키 → `SUPABASE_KEY`

> ⚠️ **주의**: `service_role` 키가 아닌 `anon` 키를 사용하세요!

---

## 🚂 Railway 배포 (추천)

Railway는 간단한 설정과 안정적인 성능으로 **가장 추천**하는 배포 방법입니다.

### 비용
- 💰 월 $5 무료 크레딧 제공
- 예상 사용량: 월 $2-3 정도 (충분함)

### 1단계: GitHub에 코드 푸시

```bash
# 로컬에서 실행
cd C:\A_Hobby\DecryptoKorea
git init
git add .
git commit -m "Initial commit: DecryptoKorea news bot"

# GitHub에 새 리포지토리 생성 후
git remote add origin https://github.com/your-username/DecryptoKorea.git
git branch -M main
git push -u origin main
```

### 2단계: Railway 프로젝트 생성

1. https://railway.app 접속
2. GitHub 계정으로 로그인
3. "New Project" 클릭
4. "Deploy from GitHub repo" 선택
5. `DecryptoKorea` 리포지토리 선택
6. 자동으로 배포 시작

### 3단계: 환경 변수 설정

1. 프로젝트 대시보드에서 **Variables** 탭 클릭
2. 다음 환경 변수들을 추가:

```bash
GEMINI_API_KEY=your_actual_key_here
WORDPRESS_URL=https://yoursite.com
WORDPRESS_USERNAME=admin
WORDPRESS_APP_PASSWORD=your_app_password
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

3. "Deploy" 클릭하여 재배포

### 4단계: 배포 확인

1. **Deployments** 탭에서 로그 확인
2. 다음과 같은 로그가 보이면 성공:
```
[INFO] Supabase 연결 성공
[INFO] Scheduler mode enabled
[INFO] Interval: 30 minutes
[INFO] Starting scheduler...
```

---

## 🎨 Render 배포 (완전 무료)

Render는 **완전 무료**로 운영할 수 있지만 Railway보다 약간 느립니다.

### 비용
- ✅ **완전 무료** (750시간/월, 한 달 24/7 실행 가능)

### 1단계: GitHub에 코드 푸시

Railway와 동일 (위 참조)

### 2단계: Render 서비스 생성

1. https://render.com 접속
2. GitHub 계정으로 로그인
3. "New +" → "Background Worker" 선택
4. GitHub 리포지토리 연결:
   - `DecryptoKorea` 선택
5. 서비스 정보 입력:
   - **Name**: `decryptokorea-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Plan**: `Free`

### 3단계: 환경 변수 설정

1. "Environment" 탭 클릭
2. "Add Environment Variable" 클릭하여 다음 변수들을 추가:

```bash
GEMINI_API_KEY=your_actual_key_here
WORDPRESS_URL=https://yoursite.com
WORDPRESS_USERNAME=admin
WORDPRESS_APP_PASSWORD=your_app_password
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

3. "Save Changes" 클릭

### 4단계: 배포 시작

1. "Manual Deploy" → "Deploy latest commit" 클릭
2. 로그에서 배포 진행 상황 확인
3. 성공 시 자동으로 시작

---

## ✅ 배포 후 확인

### 1. 로그 확인

**Railway:**
```
프로젝트 대시보드 → Deployments → View Logs
```

**Render:**
```
서비스 대시보드 → Logs 탭
```

### 2. 예상되는 로그 출력

```
============================================================
Multi-Source Crypto News Auto Poster
============================================================

[INFO] Configuration loaded from config.json
[INFO] Supabase 연결 성공

[INFO] Scheduler mode enabled
[INFO] Interval: 30 minutes
[INFO] Press Ctrl+C to stop the scheduler

[INFO] Starting scheduler...

============================================================
Pipeline Execution - 2025-01-18 10:30:00
============================================================

[INIT] Initializing services...

[INFO] Enabled sources: coindesk, cryptopolitan, theblock

============================================================
Processing Source: COINDESK
============================================================
...
```

### 3. Supabase 데이터 확인

1. Supabase 프로젝트 → **Table Editor** 클릭
2. `processed_articles` 테이블 선택
3. 처리된 기사 목록 확인

### 4. WordPress 게시 확인

1. WordPress 관리자 페이지 접속
2. **게시물** → **모든 게시물** 확인
3. 새 기사가 자동으로 게시되었는지 확인

---

## 🔧 문제 해결

### 문제 1: "SUPABASE_URL environment variable required" 오류

**원인**: 환경 변수가 설정되지 않음

**해결**:
1. Railway/Render 대시보드 → Variables/Environment 확인
2. `SUPABASE_URL`과 `SUPABASE_KEY` 추가
3. 재배포

### 문제 2: "Failed to connect to Supabase" 오류

**원인**: Supabase 키가 잘못됨

**해결**:
1. Supabase 대시보드 → Settings → API
2. `anon` 키를 다시 복사 (service_role 아님!)
3. 환경 변수 업데이트

### 문제 3: 중복 기사가 게시됨

**원인**: Supabase 테이블이 제대로 생성되지 않음

**해결**:
1. Supabase → SQL Editor
2. `database/supabase_schema.sql` 다시 실행
3. Table Editor에서 `processed_articles` 테이블 확인

### 문제 4: Railway/Render에서 프로세스가 계속 재시작됨

**원인**: 코드 오류 또는 환경 변수 누락

**해결**:
1. 로그 확인하여 에러 메시지 찾기
2. 모든 환경 변수가 올바르게 설정되었는지 확인
3. 로컬에서 먼저 테스트:
```bash
# .env 파일 설정 후
python main.py
```

### 문제 5: "처리된 기사 없음" (No new articles)

**원인**: 정상 동작 (이미 모든 기사 처리 완료)

**확인**:
1. Supabase Table Editor에서 기사 목록 확인
2. 30분 후 새 기사가 나오면 자동 처리됨

---

## 📊 비용 비교

| 플랫폼 | 무료 제공 | 예상 비용 | 안정성 | 추천도 |
|--------|----------|----------|--------|--------|
| **Railway** | $5/월 크레딧 | $2-3/월 | ⭐⭐⭐⭐⭐ | 🥇 1위 |
| **Render** | 750시간/월 | $0 | ⭐⭐⭐⭐ | 🥈 2위 |

---

## 🎯 다음 단계

배포가 완료되었다면:

1. ✅ 30분마다 자동으로 새 기사 크롤링
2. ✅ Gemini AI로 자동 번역 및 SEO 최적화
3. ✅ WordPress에 자동 게시
4. ✅ Supabase에 기록하여 중복 방지

**모니터링**:
- Railway/Render 로그를 주기적으로 확인
- WordPress에 새 게시물이 올라오는지 확인
- Supabase에 데이터가 쌓이는지 확인

**문제 발생 시**:
- GitHub Issues에 문의
- 로그 스크린샷 첨부
- 환경 변수 설정 재확인

---

## 📞 지원

문제가 발생하면:

1. 이 문서의 **문제 해결** 섹션 확인
2. Railway/Render 로그 확인
3. GitHub Issues에 질문

**Happy Deploying! 🚀**
