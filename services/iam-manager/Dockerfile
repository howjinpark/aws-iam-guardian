# IAM Manager Service Dockerfile
# 멀티스테이지 빌드로 최적화

FROM python:3.11-slim as builder

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 런타임 스테이지
FROM python:3.11-slim as runtime

# 시스템 패키지 설치 (런타임 필요)
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 보안을 위한 non-root 사용자 생성
RUN groupadd -r iamuser && useradd -r -g iamuser iamuser

# 작업 디렉토리 설정
WORKDIR /app

# 빌더 스테이지에서 설치된 패키지 복사
COPY --from=builder /root/.local /home/iamuser/.local

# 애플리케이션 코드 복사
COPY --chown=iamuser:iamuser app/ ./app/
COPY --chown=iamuser:iamuser .env* ./

# PATH에 사용자 로컬 bin 추가
ENV PATH=/home/iamuser/.local/bin:$PATH

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 포트 노출
EXPOSE 8001

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health')" || exit 1

# 사용자 전환
USER iamuser

# 애플리케이션 실행
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]