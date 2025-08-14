# VMware 서버 구축 가이드

## 🖥️ 서버 사양 권장사항

- **OS**: Ubuntu 20.04/22.04 LTS
- **RAM**: 8GB 이상
- **CPU**: 4코어 이상
- **스토리지**: 50GB 이상
- **네트워크**: 고정 IP 권장

## 🚀 설치 순서

### 1. 서버 초기 설정
```bash
# 스크립트 실행 권한 부여
chmod +x *.sh

# 의존성 설치
./install-dependencies.sh

# 재부팅 (Docker 그룹 권한 적용)
sudo reboot
```

### 2. 데이터베이스 설정
```bash
# PostgreSQL 설정
./setup-database.sh
```

### 3. 소스코드 업로드
```bash
# 로컬에서 서버로 파일 복사
scp -r ./services user@server-ip:/opt/iam-manager/
```

### 4. 서비스 배포
```bash
# Auth Service 배포
./deploy-services.sh
```

## 🔍 서비스 확인

### Auth Service
- **API 문서**: http://서버IP:8000/docs
- **헬스체크**: http://서버IP:8000/health
- **상태 확인**: `sudo systemctl status auth-service`
- **로그 확인**: `sudo journalctl -u auth-service -f`

### 데이터베이스
```bash
# PostgreSQL 접속
sudo -u postgres psql

# 데이터베이스 목록 확인
\l

# 사용자 목록 확인
\du
```

### 쿠버네티스 (k3s)
```bash
# 클러스터 상태 확인
sudo kubectl get nodes

# 네임스페이스 확인
sudo kubectl get namespaces
```

## 🛠️ 트러블슈팅

### 서비스가 시작되지 않는 경우
```bash
# 로그 확인
sudo journalctl -u auth-service -n 50

# 수동 실행으로 오류 확인
cd /opt/iam-manager/services/auth-service
source ../../venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 데이터베이스 연결 오류
```bash
# PostgreSQL 상태 확인
sudo systemctl status postgresql

# 연결 테스트
psql -h localhost -U auth_user -d auth_db
```

### 방화벽 설정
```bash
# 포트 열기
sudo ufw allow 8000/tcp
sudo ufw allow 5432/tcp

# 방화벽 상태 확인
sudo ufw status
```

## 📋 다음 단계

1. **IAM Manager Service** 개발 및 배포
2. **Audit Service** 개발 및 배포
3. **Analyzer Service** 개발 및 배포
4. **쿠버네티스 배포** 설정
5. **CI/CD 파이프라인** 구축

## 🔐 보안 설정

### 필수 보안 조치
- PostgreSQL 비밀번호 변경
- JWT Secret Key 변경
- 방화벽 규칙 최소화
- SSH 키 기반 인증 설정
- 정기적인 시스템 업데이트