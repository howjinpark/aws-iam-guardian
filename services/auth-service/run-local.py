#!/usr/bin/env python3
"""
Auth Service 로컬 실행 스크립트
개발 환경에서 서비스를 쉽게 실행할 수 있도록 도와주는 스크립트
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """메인 실행 함수"""
    print("🚀 Auth Service 로컬 실행 시작...")
    
    # 현재 디렉토리를 서비스 루트로 설정
    service_root = Path(__file__).parent
    os.chdir(service_root)
    
    # 환경변수 설정
    env = os.environ.copy()
    env.update({
        'PYTHONPATH': str(service_root),
        'DEBUG': 'true',
        'HOST': '0.0.0.0',
        'PORT': '8000'
    })
    
    # .env.local 파일이 있으면 로드
    env_file = service_root / '.env.local'
    if env_file.exists():
        print(f"📄 환경 설정 파일 로드: {env_file}")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env[key.strip()] = value.strip()
    
    print("🔧 환경 설정:")
    print(f"   - HOST: {env.get('HOST', '0.0.0.0')}")
    print(f"   - PORT: {env.get('PORT', '8000')}")
    print(f"   - DEBUG: {env.get('DEBUG', 'false')}")
    print(f"   - DATABASE_URL: {env.get('DATABASE_URL', 'Not set')}")
    print(f"   - SECRET_KEY: {'설정됨' if env.get('SECRET_KEY') else 'Not set'}")
    
    # 의존성 확인
    try:
        import uvicorn
        import fastapi
        import sqlalchemy
        import jose
        print("✅ 필수 패키지 확인 완료")
    except ImportError as e:
        print(f"❌ 필수 패키지 누락: {e}")
        print("다음 명령어로 설치하세요:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    # 서비스 실행
    try:
        print("\n🌟 Auth Service 실행 중...")
        print("📍 접속 URL:")
        print(f"   - API 문서: http://{env.get('HOST', '0.0.0.0')}:{env.get('PORT', '8000')}/docs")
        print(f"   - 헬스체크: http://{env.get('HOST', '0.0.0.0')}:{env.get('PORT', '8000')}/health")
        print(f"   - 초기 관리자 생성: POST http://{env.get('HOST', '0.0.0.0')}:{env.get('PORT', '8000')}/api/v1/users/init-admin")
        print("\n⏹️  종료하려면 Ctrl+C를 누르세요\n")
        
        # uvicorn으로 서비스 실행
        cmd = [
            sys.executable, '-m', 'uvicorn',
            'app.main:app',
            '--host', env.get('HOST', '0.0.0.0'),
            '--port', env.get('PORT', '8000'),
            '--reload',
            '--log-level', 'info'
        ]
        
        subprocess.run(cmd, env=env, cwd=service_root)
        
    except KeyboardInterrupt:
        print("\n\n👋 Auth Service 종료됨")
    except Exception as e:
        print(f"\n❌ 서비스 실행 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()