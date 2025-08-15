@echo off
echo 🌟 IAM Manager 시스템 시작
echo ================================

echo 📋 서비스 실행 순서:
echo    1. Auth Service (포트: 8000)
echo    2. IAM Manager Service (포트: 8001)
echo.

echo 🚀 Auth Service 시작 중...
start "Auth Service" cmd /k "cd services\auth-service && python run-local.py"

timeout /t 5 /nobreak > nul

echo 🚀 IAM Manager Service 시작 중...
start "IAM Manager Service" cmd /k "cd services\iam-manager && python run-local.py"

timeout /t 3 /nobreak > nul

echo.
echo 🌐 서비스 접속 정보:
echo    - Auth Service API: http://localhost:8000/docs
echo    - IAM Manager API: http://localhost:8001/docs
echo    - 헬스체크: http://localhost:8000/health, http://localhost:8001/health
echo.
echo ✅ 모든 서비스가 시작되었습니다!
echo    각 서비스 창에서 Ctrl+C로 개별 종료 가능합니다.
echo.
pause