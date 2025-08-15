"""
인증 관련 API 라우터
로그인, 로그아웃, 토큰 검증 등
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from ..database import get_database_session
from ..schemas import LoginRequest, LoginResponse, UserResponse, ErrorResponse
from ..crud import UserCRUD, SessionCRUD, AuditCRUD
from ..security import verify_password, create_access_token, create_refresh_token, get_token_expire_time, verify_token
from ..dependencies import (
    get_current_user, get_current_user_token, validate_session, 
    get_client_info, security_scheme
)
from .. import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["인증"])


@router.post("/login", response_model=LoginResponse, summary="사용자 로그인")
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_database_session)
):
    """
    사용자 로그인
    
    - **username**: 사용자명 또는 이메일
    - **password**: 비밀번호
    
    성공 시 JWT 토큰과 사용자 정보를 반환합니다.
    """
    client_info = get_client_info(request)
    
    try:
        # 사용자 조회
        user = UserCRUD.get_user_by_username_or_email(db, login_data.username)
        if not user:
            logger.warning(f"존재하지 않는 사용자 로그인 시도: {login_data.username}")
            # 감사 로그 기록
            AuditCRUD.create_audit_log(
                db=db,
                user_id=None,
                action="login",
                result="failure",
                details=f"User not found: {login_data.username}",
                ip_address=client_info.get("ip_address"),
                user_agent=client_info.get("user_agent")
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자명 또는 비밀번호가 올바르지 않습니다"
            )
        
        # 계정 활성화 상태 확인
        if not user.is_active:
            logger.warning(f"비활성화된 계정 로그인 시도: user_id={user.id}")
            AuditCRUD.create_audit_log(
                db=db,
                user_id=user.id,
                action="login",
                result="failure",
                details="Account is inactive",
                ip_address=client_info.get("ip_address"),
                user_agent=client_info.get("user_agent")
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="비활성화된 계정입니다"
            )
        
        # 비밀번호 검증
        if not verify_password(login_data.password, user.hashed_password):
            logger.warning(f"잘못된 비밀번호 로그인 시도: user_id={user.id}")
            AuditCRUD.create_audit_log(
                db=db,
                user_id=user.id,
                action="login",
                result="failure",
                details="Invalid password",
                ip_address=client_info.get("ip_address"),
                user_agent=client_info.get("user_agent")
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자명 또는 비밀번호가 올바르지 않습니다"
            )
        
        # JWT 토큰 생성
        access_token_expires = timedelta(minutes=30)  # 30분
        token_data = {
            "sub": str(user.id),
            "username": user.username
        }
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        
        # 리프레시 토큰 생성
        refresh_token = create_refresh_token(data=token_data)
        
        # 토큰에서 JTI 추출
        token_payload = verify_token(access_token)
        
        # 세션 생성
        SessionCRUD.create_session(
            db=db,
            user_id=user.id,
            token_jti=token_payload.jti,
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent")
        )
        
        # 마지막 로그인 시간 업데이트
        UserCRUD.update_last_login(db, user.id)
        
        # 성공 로그 기록
        AuditCRUD.create_audit_log(
            db=db,
            user_id=user.id,
            action="login",
            result="success",
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent")
        )
        
        logger.info(f"사용자 로그인 성공: user_id={user.id}, username={user.username}")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=get_token_expire_time(),
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"로그인 처리 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 처리 중 오류가 발생했습니다"
        )


@router.post("/logout", summary="사용자 로그아웃")
async def logout(
    request: Request,
    db: Session = Depends(get_database_session),
    current_user: models.User = Depends(get_current_user),
    token_data = Depends(get_current_user_token),
    session: models.UserSession = Depends(validate_session)
):
    """
    사용자 로그아웃
    
    현재 세션을 무효화합니다.
    """
    client_info = get_client_info(request)
    
    try:
        # 세션 무효화
        success = SessionCRUD.revoke_session(db, token_data.jti)
        
        if success:
            # 성공 로그 기록
            AuditCRUD.create_audit_log(
                db=db,
                user_id=current_user.id,
                action="logout",
                result="success",
                ip_address=client_info.get("ip_address"),
                user_agent=client_info.get("user_agent")
            )
            
            logger.info(f"사용자 로그아웃 성공: user_id={current_user.id}")
            return {"message": "로그아웃되었습니다"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="로그아웃 처리 중 오류가 발생했습니다"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"로그아웃 처리 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그아웃 처리 중 오류가 발생했습니다"
        )


@router.get("/me", response_model=UserResponse, summary="현재 사용자 정보")
async def get_current_user_info(
    current_user: models.User = Depends(get_current_user)
):
    """
    현재 인증된 사용자의 정보를 반환합니다.
    """
    logger.debug(f"사용자 정보 조회: user_id={current_user.id}")
    return UserResponse.from_orm(current_user)


@router.post("/verify", summary="토큰 검증")
async def verify_token_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_database_session)
):
    """
    JWT 토큰의 유효성을 검증합니다.
    
    다른 서비스에서 토큰 검증용으로 사용할 수 있습니다.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 필요합니다"
        )
    
    try:
        # 토큰 검증
        token_data = verify_token(credentials.credentials)
        
        # 사용자 존재 여부 확인
        user = UserCRUD.get_user_by_id(db, token_data.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 사용자입니다"
            )
        
        # 세션 유효성 확인
        session = SessionCRUD.get_active_session(db, token_data.jti)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="세션이 만료되었습니다"
            )
        
        return {
            "valid": True,
            "user_id": user.id,
            "username": user.username,
            "is_admin": user.is_admin
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"토큰 검증 중 오류: {e}")
        return {
            "valid": False,
            "error": "토큰 검증 실패"
        }


@router.post("/refresh", summary="토큰 갱신")
async def refresh_token_endpoint(
    refresh_token: str,
    request: Request,
    db: Session = Depends(get_database_session)
):
    """
    리프레시 토큰을 사용하여 새로운 액세스 토큰을 발급합니다.
    
    - **refresh_token**: 리프레시 토큰
    """
    client_info = get_client_info(request)
    
    try:
        # 리프레시 토큰 검증
        token_payload = verify_token(refresh_token)
        
        # 토큰 타입 확인
        if token_payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 리프레시 토큰입니다"
            )
        
        # 사용자 조회
        user = UserCRUD.get_user_by_id(db, token_payload.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 사용자입니다"
            )
        
        # 새 액세스 토큰 생성
        access_token_expires = timedelta(minutes=30)
        new_token_data = {
            "sub": str(user.id),
            "username": user.username
        }
        new_access_token = create_access_token(
            data=new_token_data,
            expires_delta=access_token_expires
        )
        
        # 새 리프레시 토큰 생성
        new_refresh_token = create_refresh_token(data=new_token_data)
        
        # 새 토큰에서 JTI 추출
        new_token_payload = verify_token(new_access_token)
        
        # 새 세션 생성
        SessionCRUD.create_session(
            db=db,
            user_id=user.id,
            token_jti=new_token_payload.jti,
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent")
        )
        
        # 로그 기록
        AuditCRUD.create_audit_log(
            db=db,
            user_id=user.id,
            action="token_refresh",
            result="success",
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent")
        )
        
        logger.info(f"토큰 갱신 성공: user_id={user.id}")
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": get_token_expire_time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"토큰 갱신 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="토큰 갱신 중 오류가 발생했습니다"
        )