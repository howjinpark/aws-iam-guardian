"""
애플리케이션 설정 관리
환경변수와 기본값을 명확하게 정의
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # 기본 설정
    app_name: str = "IAM Auth Service"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8000
    
    # 데이터베이스 설정
    database_url: str = "postgresql://auth_user:auth_pass@localhost:5432/auth_db"
    
    # JWT 설정
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # 로깅 설정
    log_level: str = "INFO"
    
    class Config:
        env_file = [".env.local", ".env"]  # .env.local을 우선으로 읽기
        case_sensitive = False


# 전역 설정 인스턴스
settings = Settings()


def get_settings() -> Settings:
    """설정 객체 반환 (의존성 주입용)"""
    return settings