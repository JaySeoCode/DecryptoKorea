-- DecryptoKorea Supabase Database Schema
-- 처리된 기사를 추적하여 중복 게시를 방지하는 테이블

-- 1. processed_articles 테이블 생성
CREATE TABLE IF NOT EXISTS processed_articles (
    id BIGSERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    source TEXT,
    published_date TEXT,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 인덱스 생성 (성능 최적화)
-- URL로 빠른 검색을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_processed_articles_url
    ON processed_articles(url);

-- 소스별 검색을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_processed_articles_source
    ON processed_articles(source);

-- 처리 시간별 정렬을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_processed_articles_processed_at
    ON processed_articles(processed_at DESC);

-- 3. 테이블 설명 (주석)
COMMENT ON TABLE processed_articles IS '처리된 암호화폐 뉴스 기사 목록 (중복 방지용)';
COMMENT ON COLUMN processed_articles.id IS '기본 키 (자동 증가)';
COMMENT ON COLUMN processed_articles.url IS '기사 원본 URL (중복 방지 키)';
COMMENT ON COLUMN processed_articles.title IS '기사 제목';
COMMENT ON COLUMN processed_articles.source IS '기사 출처 (coindesk, cryptopolitan, theblock 등)';
COMMENT ON COLUMN processed_articles.published_date IS '기사 원본 게시일';
COMMENT ON COLUMN processed_articles.processed_at IS 'AI 처리 및 WordPress 게시 완료 시간';
COMMENT ON COLUMN processed_articles.created_at IS '레코드 생성 시간';

-- 4. Row Level Security (RLS) 정책 설정
-- Supabase에서 보안을 위해 권장됨

-- RLS 활성화
ALTER TABLE processed_articles ENABLE ROW LEVEL SECURITY;

-- anon 키로 읽기 허용 (SELECT)
CREATE POLICY "Enable read access for anon key"
    ON processed_articles FOR SELECT
    TO anon
    USING (true);

-- anon 키로 쓰기 허용 (INSERT)
CREATE POLICY "Enable insert access for anon key"
    ON processed_articles FOR INSERT
    TO anon
    WITH CHECK (true);

-- anon 키로 업데이트 허용 (UPDATE)
CREATE POLICY "Enable update access for anon key"
    ON processed_articles FOR UPDATE
    TO anon
    USING (true);

-- anon 키로 삭제 허용 (DELETE)
CREATE POLICY "Enable delete access for anon key"
    ON processed_articles FOR DELETE
    TO anon
    USING (true);

-- 5. 통계 보기 (View) 생성 (선택 사항)
CREATE OR REPLACE VIEW processed_articles_stats AS
SELECT
    COUNT(*) as total_articles,
    COUNT(DISTINCT source) as total_sources,
    MAX(processed_at) as last_processed,
    MIN(processed_at) as first_processed,
    source,
    COUNT(*) as count_per_source
FROM processed_articles
GROUP BY source;

COMMENT ON VIEW processed_articles_stats IS '처리된 기사 통계 (소스별 집계)';

-- 완료 메시지 출력
DO $$
BEGIN
    RAISE NOTICE '✅ Supabase 스키마 생성 완료!';
    RAISE NOTICE '테이블: processed_articles';
    RAISE NOTICE '인덱스: 3개 (url, source, processed_at)';
    RAISE NOTICE 'RLS 정책: 4개 (SELECT, INSERT, UPDATE, DELETE)';
    RAISE NOTICE '통계 뷰: processed_articles_stats';
END $$;
