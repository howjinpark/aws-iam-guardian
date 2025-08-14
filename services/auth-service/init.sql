-- Auth Service 초기 데이터베이스 설정
-- 기본 관리자 계정 생성 및 인덱스 최적화

-- 확장 기능 활성화
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 초기 관리자 계정 생성 (테이블이 생성된 후 실행됨)
-- 비밀번호: Admin123!
-- 실제 운영에서는 반드시 변경 필요

-- 이 스크립트는 애플리케이션 시작 후 수동으로 실행하거나
-- 마이그레이션 도구를 통해 실행해야 합니다.

/*
INSERT INTO users (username, email, hashed_password, is_active, is_admin, created_at)
VALUES (
    'admin',
    'admin@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3L3jzjvQSG',  -- Admin123!
    true,
    true,
    NOW()
) ON CONFLICT (username) DO NOTHING;
*/

-- 성능 최적화를 위한 추가 인덱스
-- (애플리케이션에서 테이블 생성 후 실행)

/*
-- 사용자 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- 세션 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active);

-- 감사 로그 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_result ON audit_logs(result);
*/