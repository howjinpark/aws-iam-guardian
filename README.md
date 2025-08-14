# IAM Manager - 마이크로서비스 CI/CD 프로젝트

## 🎯 프로젝트 개요

AWS IAM 관리를 위한 마이크로서비스 아키텍처 기반 시스템입니다.
현대적인 CI/CD 파이프라인과 GitOps를 활용한 자동화된 배포를 구현했습니다.

> 🚀 **GitHub Container Registry (GHCR) 연동 완료** - 자동화된 컨테이너 이미지 빌드 및 배포

## 🏗️ 아키텍처

```
┌─────────────────┐    ┌─────────────────┐
│   Auth Service  │    │ IAM Manager     │
│   (포트 8000)    │    │   (포트 8001)    │
│                 │    │                 │
│ • JWT 인증      │    │ • AWS IAM 연동  │
│ • 사용자 관리    │    │ • 권한 분석     │
│ • 감사 로그     │    │ • 위험도 평가   │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌─────────────────┐
         │   PostgreSQL    │
         │   (가상서버)     │
         └─────────────────┘
```

## 🚀 주요 기능

### Auth Service
- JWT 기반 인증/인가
- 사용자 및 권한 관리
- 세션 관리 및 감사 로그
- 초기 관리자 생성 기능

### IAM Manager Service
- 실제 AWS IAM 데이터 조회
- 멀티 계정/리전 관리
- 권한 분석 및 위험도 평가
- 고위험 사용자 자동 탐지

## 🔄 CI/CD 파이프라인

### GitHub Actions
- **코드 품질 검사**: Black, flake8, isort
- **보안 스캔**: Bandit, Safety, Trivy, git-secrets
- **자동화된 테스트**: 단위 테스트 + 통합 테스트
- **Docker 이미지 빌드**: 멀티스테이지 최적화
- **GitOps 배포**: ArgoCD 연동

### 파이프라인 구조
```
코드 푸시 → GitHub Actions → Docker 빌드 → GitOps 업데이트 → ArgoCD 배포
```

## 🛠️ 기술 스택

### Backend
- **Python 3.11** + FastAPI
- **PostgreSQL** (데이터베이스)
- **SQLAlchemy** (ORM)
- **JWT** (인증)
- **boto3** (AWS SDK)

### DevOps
- **Docker** (컨테이너화)
- **GitHub Actions** (CI/CD)
- **ArgoCD** (GitOps)
- **Kubernetes** (오케스트레이션)

### 보안
- **다중 보안 스캔** (Trivy, Bandit, Safety)
- **자격증명 스캔** (git-secrets)
- **코드 품질 검증** (flake8, Black)

## 🚀 로컬 실행 방법

### 1. Auth Service
```bash
cd services/auth-service
pip install -r requirements.txt
python run-local.py
```
- API 문서: http://localhost:8000/docs

### 2. IAM Manager Service
```bash
cd services/iam-manager
pip install -r requirements.txt
python run-local.py
```
- API 문서: http://localhost:8001/docs

## 🔧 환경 설정

### 필수 환경변수
```bash
# Auth Service
DATABASE_URL=postgresql://user:pass@host:5432/auth_db
SECRET_KEY=your-secret-key

# IAM Manager Service
DATABASE_URL=postgresql://user:pass@host:5432/iam_db
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=ap-northeast-2
```

## 📊 API 엔드포인트

### Auth Service (포트 8000)
- `POST /api/v1/users/init-admin` - 초기 관리자 생성
- `POST /api/v1/auth/login` - 로그인
- `GET /api/v1/auth/me` - 현재 사용자 정보
- `POST /api/v1/users/` - 사용자 생성 (관리자만)

### IAM Manager Service (포트 8001)
- `GET /api/v1/accounts/main/users` - IAM 사용자 목록
- `GET /api/v1/accounts/main/roles` - IAM 역할 목록
- `GET /api/v1/analyze/main/high-risk-users` - 고위험 사용자 탐지
- `GET /api/v1/analyze/main/user/{user_name}/permissions` - 사용자 권한 분석

## 🎯 포트폴리오 포인트

### 1. 마이크로서비스 아키텍처
- 서비스별 독립적인 개발/배포
- API Gateway 패턴
- 서비스 간 통신

### 2. 현대적인 CI/CD
- GitOps 기반 배포
- 다중 보안 스캔
- 자동화된 품질 검증

### 3. 실제 AWS 연동
- 실무에서 사용 가능한 수준
- 보안 중심 설계
- 권한 분석 및 추천

### 4. 인프라 자동화
- Docker 컨테이너화
- Kubernetes 배포
- 모니터링 및 로깅

## 🔐 보안 고려사항

- 환경변수로 민감 정보 관리
- JWT 기반 인증
- 다중 보안 스캔 파이프라인
- 최소 권한 원칙 적용
- 감사 로그 기록

## 📈 향후 계획

- [ ] 프론트엔드 대시보드 개발
- [ ] CloudTrail 연동 (Audit Service)
- [ ] 정책 변경 승인 워크플로우
- [ ] 실시간 알림 시스템
- [ ] 성능 모니터링 강화

## 🤝 기여 방법

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 라이선스

MIT License