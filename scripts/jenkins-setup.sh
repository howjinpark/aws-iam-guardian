#!/bin/bash

echo "🔧 Jenkins 설정 시작..."

# 1. Jenkins를 Docker로 실행
echo "🐳 Jenkins Docker 컨테이너 시작..."
docker run -d \
  --name jenkins \
  -p 8082:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(which docker):/usr/bin/docker \
  jenkins/jenkins:lts

echo "⏳ Jenkins 시작 대기 중..."
sleep 30

# 2. 초기 관리자 비밀번호 가져오기
echo "🔑 Jenkins 초기 관리자 비밀번호:"
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword

echo ""
echo "✅ Jenkins 설정 완료!"
echo ""
echo "다음 단계:"
echo "1. http://localhost:8082 접속"
echo "2. 위의 비밀번호로 로그인"
echo "3. 추천 플러그인 설치"
echo "4. 관리자 계정 생성"
echo "5. jenkins/Jenkinsfile을 사용하여 파이프라인 생성"
echo ""
echo "Jenkins 중지: docker stop jenkins"
echo "Jenkins 재시작: docker start jenkins"