"""
보안 관련 유틸리티
JWT 토큰 생성/검증, 비밀번호 해싱 등
"""
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import uuid
import logging

from .config import settings
from .schemas import TokenData

logger = logging.getLogger(__name__)

# 비밀번호 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """비밀번호 해싱"""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"비밀번호 해싱 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="비밀번호 처리 중 오류가 발생했습니다"
        )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"비밀번호 검증 실패: {e}")
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """JWT 액세스 토큰 생성"""
    try:
        to_encode = data.copy()
        
        # 만료 시간 설정
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        # JWT 클레임 추가
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4()),  # JWT ID (토큰 무효화용)
            "type": "access"  # 토큰 타입
        })
        
        # 토큰 생성
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.secret_key, 
            algorithm=settings.algorithm
        )
        
        logger.info(f"JWT 액세스 토큰 생성 완료: user_id={data.get('sub')}")
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"JWT 토큰 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="토큰 생성 중 오류가 발생했습니다"
        )


def create_refresh_token(data: dict) -> str:
    """JWT 리프레시 토큰 생성"""
    try:
        to_encode = data.copy()
        
        # 리프레시 토큰은 더 긴 만료 시간 (7일)
        expire = datetime.utcnow() + timedelta(days=7)
        
        # JWT 클레임 추가
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4()),  # JWT ID
            "type": "refresh"  # 토큰 타입
        })
        
        # 토큰 생성
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.secret_key, 
            algorithm=settings.algorithm
        )
        
        logger.info(f"JWT 리프레시 토큰 생성 완료: user_id={data.get('sub')}")
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"JWT 리프레시 토큰 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="리프레시 토큰 생성 중 오류가 발생했습니다"
        )


def verify_token(token: str) -> TokenData:
    """JWT 토큰 검증 및 데이터 추출"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 토큰 디코딩
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        
        # 사용자 ID 추출
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("토큰에 사용자 ID가 없음")
            raise credentials_exception
        
        # 토큰 데이터 생성
        token_data = TokenData(
            user_id=int(user_id),
            username=payload.get("username"),
            jti=payload.get("jti")
        )
        
        logger.debug(f"토큰 검증 성공: user_id={user_id}")
        return token_data
        
    except JWTError as e:
        logger.warning(f"JWT 토큰 검증 실패: {e}")
        raise credentials_exception
    except ValueError as e:
        logger.warning(f"토큰 데이터 변환 실패: {e}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"토큰 검증 중 예상치 못한 오류: {e}")
        raise credentials_exception


def get_token_expire_time() -> int:
    """토큰 만료 시간(초) 반환"""
    return settings.access_token_expire_minutes * 60


def is_token_expired(token: str) -> bool:
    """토큰 만료 여부 확인"""
    try:
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm],
            options={"verify_exp": False}  # 만료 시간만 확인
        )
        
        exp = payload.get("exp")
        if exp is None:
            return True
        
        return datetime.utcnow() > datetime.fromtimestamp(exp)
        
    except Exception:
        return True