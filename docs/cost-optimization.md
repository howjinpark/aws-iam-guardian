# 온프레미스 + AWS 하이브리드 아키텍처

## 🏠 온프레미스 구성

### 서버 환경
```
VMware 가상 서버 (Ubuntu/CentOS)
├── Kubernetes 클러스터 (k3s/kubeadm)
├── Auth Service (PostgreSQL)
├── IAM Manager (AWS SDK 연동)
├── Audit Service (CloudTrail API)
├── Analyzer Service
└── 모니터링 스택 (Prometheus/Grafana)
```

### AWS 연동 최소화
- **IAM API**: 읽기 전용 호출 (무료)
- **CloudTrail**: 관리 이벤트만 (90일 무료)
- **실제 권한 변경**: 시뮬레이션만 (실제 적용 X)

## 💡 비용 절약 팁

### 1. Mock 서비스 활용
```python
# 실제 AWS 대신 Mock 데이터 사용
if os.getenv('ENVIRONMENT') == 'demo':
    return mock_iam_users()
else:
    return boto3.client('iam').list_users()
```

### 2. 로컬 데이터베이스
```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: iam_manager
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### 3. 프리티어 모니터링
- AWS Billing Alerts 설정
- 월 $1 이상 사용 시 알림

## 📊 예상 비용 (최악의 경우)
- CloudTrail 데이터 이벤트: $0 (사용 안 함)
- S3 스토리지: $0 (프리티어 범위)
- EC2/RDS: $0 (로컬 환경 사용)

**총 예상 비용: $0/월**

## 🚀 실제 운영 시나리오
포트폴리오 완성 후 실제 AWS에 배포할 때만:
- EKS 클러스터: ~$70/월
- RDS: ~$15/월
- 기타: ~$10/월

하지만 개발/데모 단계에서는 완전 무료 가능!