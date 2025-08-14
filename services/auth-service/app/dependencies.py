"""
FastAPI 의존성 주입
인증, 데이터베이스 세션 등 공통 의존성 관리
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import logging

from .database import get_database_session
from .security import verify_token
from .schemas import TokenData
from .crud import UserCRUD, SessionCRUD, AuditCRUD
from . import models

logger = logging.getLogger(__name__)

# HTTP Bearer 토큰 스키마
security_scheme = HTTPBearer(auto_error=False)


def get_db() -> Session:
    """데이터베이스 세션 의존성"""
    return Depends(get_database_session)


def get_current_user_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> TokenData:
    """현재 사용자 토큰 검증"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 토큰이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return verify_token(credentials.credentials)


def get_current_user(
    db: Session = Depends(get_database_session),
    token_data: TokenData = Depends(get_current_user_token)
) -> models.User:
    """현재 인증된 사용자 조회"""
    user = UserCRUD.get_user_by_id(db, token_data.user_id)
    if not user:
        logger.warning(f"토큰은 유효하지만 사용자를 찾을 수 없음: user_id={token_data.user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다"
        )
    
    if not user.is_active:
        logger.warning(f"비활성화된 사용자 접근 시도: user_id={user.id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비활성화된 계정입니다"
        )
    
    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """현재 활성 사용자 (별칭)"""
    return current_user


def get_current_admin_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """현재 관리자 사용자"""
    if not current_user.is_admin:
        logger.warning(f"관리자 권한 필요한 작업 시도: user_id={current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    
    return current_user


def validate_session(
    db: Session = Depends(get_database_session),
    token_data: TokenData = Depends(get_current_user_token)
) -> models.UserSession:
    """세션 유효성 검증"""
    if not token_data.jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다"
        )
    
    session = SessionCRUD.get_active_session(db, token_data.jti)
    if not session:
        logger.warning(f"유효하지 않은 세션: jti={token_data.jti}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="세션이 만료되었거나 유효하지 않습니다"
        )
    
    return session


def get_client_info(request: Request) -> dict:
    """클라이언트 정보 추출"""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "forwarded_for": request.headers.get("x-forwarded-for"),
        "real_ip": request.headers.get("x-real-ip")
    }


def log_user_action(
    action: str,
    result: str = "success",
    resource: str = None,
    details: str = None
):
    """사용자 액션 로깅 데코레이터 팩토리"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 의존성에서 필요한 객체들 추출
            db = None
            current_user = None
            request = None
            
            for arg in args:
                if isinstance(arg, Session):
                    db = arg
                elif isinstance(arg, models.User):
                    current_user = arg
                elif isinstance(arg, Request):
                    request = arg
            
            # kwargs에서도 확인
            db = db or kwargs.get('db')
            current_user = current_user or kwargs.get('current_user')
            request = request or kwargs.get('request')
            
            try:
                # 원본 함수 실행
                result_data = await func(*args, **kwargs)
                
                # 성공 로그 기록
                if db:
                    client_info = get_client_info(request) if request else {}
                    AuditCRUD.create_audit_log(
                        db=db,
                        user_id=current_user.id if current_user else None,
                        action=action,
                        result="success",
                        resource=resource,
                        details=details,
                        ip_address=client_info.get("ip_address"),
                        user_agent=client_info.get("user_agent")
                    )
                
                return result_data
                
            except Exception as e:
                # 실패 로그 기록
                if db:
                    client_info = get_client_info(request) if request else {}
                    AuditCRUD.create_audit_log(
                        db=db,
                        user_id=current_user.id if current_user else None,
                        action=action,
                        result="failure",
                        resource=resource,
                        details=f"Error: {str(e)}",
                        ip_address=client_info.get("ip_address"),
                        user_agent=client_info.get("user_agent")
                    )
                
                raise
        
        return wrapper
    return decorator