"""
IAM Manager Service 설정 관리
AWS 계정 정보 및 서비스 설정
"""
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings


class AWSAccountConfig(BaseSettings):
    """AWS 계정 설정"""
    account_id: str
    account_name: str
    regions: List[str]
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    role_arn: Optional[str] = None  # Cross-account role
    
    class Config:
        env_prefix = "AWS_"


class Settings(BaseSettings):
    """IAM Manager Service 설정"""
    
    # 기본 설정
    app_name: str = "IAM Manager Service"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8001
    
    # 데이터베이스 설정
    database_url: str = "postgresql://iam_user:iam_pass123@localhost:5432/iam_db"
    
    # Auth Service 연동
    auth_service_url: str = "http://localhost:8000"
    
    # AWS 기본 설정 (환경변수에서 읽기)
    aws_default_region: str = "ap-northeast-2"
    
    # AWS 계정 ID (환경변수에서 자동 감지)
    aws_account_id: Optional[str] = None
    
    # 멀티 계정 설정 (환경변수 기반)
    aws_accounts: Dict[str, Dict] = {}
    
    # 로깅 설정
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 전역 설정 인스턴스
settings = Settings()


def get_settings() -> Settings:
    """설정 객체 반환 (의존성 주입용)"""
    return settings


def get_aws_account_config(account_key: str) -> Optional[Dict]:
    """특정 AWS 계정 설정 반환"""
    return settings.aws_accounts.get(account_key)


def list_aws_accounts() -> Dict[str, Dict]:
    """모든 AWS 계정 목록 반환"""
    # 환경변수 기반으로 동적 생성
    if not settings.aws_accounts:
        # 기본 계정 설정 (환경변수 자격증명 사용)
        settings.aws_accounts = {
            "main": {
                "account_id": "auto-detect",  # boto3가 자동으로 감지
                "account_name": "Main Account",
                "regions": [settings.aws_default_region],
                # role_arn 없음 = 환경변수 자격증명 직접 사용
            }
        }
    return settings.aws_accounts


def initialize_aws_config():
    """AWS 설정 초기화 (실제 계정 ID 감지)"""
    try:
        import boto3
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        actual_account_id = identity['Account']
        
        # 실제 계정 ID로 업데이트
        if "main" in settings.aws_accounts:
            settings.aws_accounts["main"]["account_id"] = actual_account_id
        
        settings.aws_account_id = actual_account_id
        return actual_account_id
    except Exception as e:
        print(f"AWS 계정 ID 감지 실패: {e}")
        return None