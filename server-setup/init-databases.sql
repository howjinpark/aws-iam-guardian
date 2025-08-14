-- 모든 서비스용 데이터베이스 및 사용자 생성

-- Auth Service용
CREATE DATABASE auth_db;
CREATE USER auth_user WITH ENCRYPTED PASSWORD 'auth_pass123';
GRANT ALL PRIVILEGES ON DATABASE auth_db TO auth_user;

-- IAM Manager Service용
CREATE DATABASE iam_db;
CREATE USER iam_user WITH ENCRYPTED PASSWORD 'iam_pass123';
GRANT ALL PRIVILEGES ON DATABASE iam_db TO iam_user;

-- Audit Service용
CREATE DATABASE audit_db;
CREATE USER audit_user WITH ENCRYPTED PASSWORD 'audit_pass123';
GRANT ALL PRIVILEGES ON DATABASE audit_db TO audit_user;

-- Analyzer Service용
CREATE DATABASE analyzer_db;
CREATE USER analyzer_user WITH ENCRYPTED PASSWORD 'analyzer_pass123';
GRANT ALL PRIVILEGES ON DATABASE analyzer_db TO analyzer_user;

-- 생성된 데이터베이스 확인
\l
\du