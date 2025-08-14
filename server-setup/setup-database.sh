#!/bin/bash
# PostgreSQL 데이터베이스 설정 스크립트

set -e

echo "🗄️ PostgreSQL 데이터베이스 설정 시작..."

# PostgreSQL 서비스 시작 및 활성화
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 데이터베이스 및 사용자 생성
echo "👤 데이터베이스 사용자 및 DB 생성..."
sudo -u postgres psql << EOF
-- Auth Service용 데이터베이스
CREATE DATABASE auth_db;
CREATE USER auth_user WITH ENCRYPTED PASSWORD 'auth_pass_change_in_production';
GRANT ALL PRIVILEGES ON DATABASE auth_db TO auth_user;

-- IAM Manager Service용 데이터베이스
CREATE DATABASE iam_db;
CREATE USER iam_user WITH ENCRYPTED PASSWORD 'iam_pass_change_in_production';
GRANT ALL PRIVILEGES ON DATABASE iam_db TO iam_user;

-- Audit Service용 데이터베이스
CREATE DATABASE audit_db;
CREATE USER audit_user WITH ENCRYPTED PASSWORD 'audit_pass_change_in_production';
GRANT ALL PRIVILEGES ON DATABASE audit_db TO audit_user;

-- 연결 확인
\l
\du
EOF

# PostgreSQL 설정 파일 수정 (외부 접속 허용)
echo "🔧 PostgreSQL 설정 수정..."
PG_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" | grep -oP '\d+\.\d+' | head -1)
PG_CONFIG_DIR="/etc/postgresql/$PG_VERSION/main"

# postgresql.conf 수정
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" $PG_CONFIG_DIR/postgresql.conf

# pg_hba.conf 수정 (로컬 네트워크 접속 허용)
echo "host    all             all             10.0.0.0/8             md5" | sudo tee -a $PG_CONFIG_DIR/pg_hba.conf
echo "host    all             all             172.16.0.0/12          md5" | sudo tee -a $PG_CONFIG_DIR/pg_hba.conf
echo "host    all             all             192.168.0.0/16         md5" | sudo tee -a $PG_CONFIG_DIR/pg_hba.conf

# PostgreSQL 재시작
sudo systemctl restart postgresql

# 방화벽 설정 (PostgreSQL 포트 5432 열기)
sudo ufw allow 5432/tcp

echo "✅ PostgreSQL 설정 완료!"
echo ""
echo "데이터베이스 정보:"
echo "- Auth DB: postgresql://auth_user:auth_pass_change_in_production@localhost:5432/auth_db"
echo "- IAM DB: postgresql://iam_user:iam_pass_change_in_production@localhost:5432/iam_db"
echo "- Audit DB: postgresql://audit_user:audit_pass_change_in_production@localhost:5432/audit_db"
echo ""
echo "⚠️  프로덕션에서는 반드시 비밀번호를 변경하세요!"