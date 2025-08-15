# Frontend Dockerfile
# 멀티스테이지 빌드로 최적화

# Build stage
FROM node:18-alpine as builder

WORKDIR /app

# 의존성 파일 복사 및 설치
COPY package*.json ./
RUN npm ci --only=production

# 소스 코드 복사 및 빌드
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# 빌드된 파일 복사
COPY --from=builder /app/build /usr/share/nginx/html

# Nginx 설정 복사
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 포트 노출
EXPOSE 80

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]