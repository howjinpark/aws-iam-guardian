"""
사용자 관리 API 라우터
사용자 생성, 조회, 수정 등
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import logging

from ..database import get_database_session
from ..schemas import UserCreate, UserUpdate, UserResponse, ErrorResponse
from ..crud import UserCRUD, AuditCRUD
from ..dependencies import get_current_user, get_current_admin_user, get_client_info
from .. import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["사용자 관리"])


@router.post("/init-admin", response_model=UserResponse, summary="초기 관리자 생성")
async def create_initial_admin(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_database_session)
):
    """
    초기 관리자 계정을 생성합니다.
    
    시스템에 사용자가 없을 때만 실행 가능합니다.
    """
    client_info = get_client_info(request)
    
    try:
        # 기존 사용자가 있는지 확인
        existing_users = UserCRUD.get_users(db, skip=0, limit=1)
        if existing_users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용자가 존재합니다. 초기 관리자는 생성할 수 없습니다."
            )
        
        # 중복 사용자명 확인
        existing_user = UserCRUD.get_user_by_username(db, user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 존재하는 사용자명입니다"
            )
        
        # 관리자 사용자 생성
        new_user = UserCRUD.create_user(db, user_data)
        
        # 관리자 권한 부여
        new_user.is_admin = True
        db.commit()
        db.refresh(new_user)
        
        # 성공 로그 기록
        AuditCRUD.create_audit_log(
            db=db,
            user_id=None,
            action="create_initial_admin",
            result="success",
            resource=f"user:{new_user.id}",
            details=f"Created initial admin: {new_user.username}",
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent")
        )
        
        logger.info(f"초기 관리자 생성 완료: ID={new_user.id}, username={new_user.username}")
        
        return UserResponse.from_orm(new_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"초기 관리자 생성 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="초기 관리자 생성 중 오류가 발생했습니다"
        )


@router.post("/", response_model=UserResponse, summary="새 사용자 생성")
async def create_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_database_session),
    current_user: models.User = Depends(get_current_admin_user)  # 관리자만 생성 가능
):
    """
    새 사용자를 생성합니다.
    
    - **username**: 사용자명 (3-50자, 영문/숫자/언더스코어만)
    - **email**: 이메일 주소
    - **password**: 비밀번호 (8자 이상, 대소문자/숫자/특수문자 포함)
    
    관리자 권한이 필요합니다.
    """
    client_info = get_client_info(request)
    
    try:
        # 중복 사용자명 확인
        existing_user = UserCRUD.get_user_by_username(db, user_data.username)
        if existing_user:
            logger.warning(f"중복 사용자명 생성 시도: {user_data.username}")
            AuditCRUD.create_audit_log(
                db=db,
                user_id=current_user.id,
                action="create_user",
                result="failure",
                details=f"Duplicate username: {user_data.username}",
                ip_address=client_info.get("ip_address"),
                user_agent=client_info.get("user_agent")
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 존재하는 사용자명입니다"
            )
        
        # 중복 이메일 확인
        existing_email = UserCRUD.get_user_by_email(db, user_data.email)
        if existing_email:
            logger.warning(f"중복 이메일 생성 시도: {user_data.email}")
            AuditCRUD.create_audit_log(
                db=db,
                user_id=current_user.id,
                action="create_user",
                result="failure",
                details=f"Duplicate email: {user_data.email}",
                ip_address=client_info.get("ip_address"),
                user_agent=client_info.get("user_agent")
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 존재하는 이메일입니다"
            )
        
        # 사용자 생성
        new_user = UserCRUD.create_user(db, user_data)
        
        # 성공 로그 기록
        AuditCRUD.create_audit_log(
            db=db,
            user_id=current_user.id,
            action="create_user",
            result="success",
            resource=f"user:{new_user.id}",
            details=f"Created user: {new_user.username}",
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent")
        )
        
        logger.info(f"새 사용자 생성 완료: ID={new_user.id}, username={new_user.username}, created_by={current_user.id}")
        
        return UserResponse.from_orm(new_user)
        
    except HTTPException:
        raise
    except IntegrityError as e:
        logger.error(f"사용자 생성 중 무결성 오류: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="중복된 사용자 정보입니다"
        )
    except Exception as e:
        logger.error(f"사용자 생성 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 생성 중 오류가 발생했습니다"
        )


@router.get("/", response_model=List[UserResponse], summary="사용자 목록 조회")
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_database_session),
    current_user: models.User = Depends(get_current_admin_user)  # 관리자만 조회 가능
):
    """
    사용자 목록을 조회합니다.
    
    - **skip**: 건너뛸 사용자 수 (페이징용)
    - **limit**: 조회할 최대 사용자 수 (최대 100)
    
    관리자 권한이 필요합니다.
    """
    try:
        if limit > 100:
            limit = 100
        
        users = UserCRUD.get_users(db, skip=skip, limit=limit)
        
        logger.debug(f"사용자 목록 조회: {len(users)}명, requested_by={current_user.id}")
        
        return [UserResponse.from_orm(user) for user in users]
        
    except Exception as e:
        logger.error(f"사용자 목록 조회 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 목록 조회 중 오류가 발생했습니다"
        )


@router.get("/{user_id}", response_model=UserResponse, summary="특정 사용자 조회")
async def get_user(
    user_id: int,
    db: Session = Depends(get_database_session),
    current_user: models.User = Depends(get_current_user)
):
    """
    특정 사용자의 정보를 조회합니다.
    
    - 본인 정보는 누구나 조회 가능
    - 다른 사용자 정보는 관리자만 조회 가능
    """
    try:
        # 본인 정보가 아니고 관리자가 아닌 경우 권한 확인
        if user_id != current_user.id and not current_user.is_admin:
            logger.warning(f"권한 없는 사용자 정보 조회 시도: user_id={user_id}, requested_by={current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="다른 사용자의 정보를 조회할 권한이 없습니다"
            )
        
        user = UserCRUD.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        
        logger.debug(f"사용자 정보 조회: user_id={user_id}, requested_by={current_user.id}")
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 조회 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 조회 중 오류가 발생했습니다"
        )


@router.put("/{user_id}", response_model=UserResponse, summary="사용자 정보 수정")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    request: Request,
    db: Session = Depends(get_database_session),
    current_user: models.User = Depends(get_current_user)
):
    """
    사용자 정보를 수정합니다.
    
    - 본인 정보는 누구나 수정 가능 (is_active 제외)
    - 다른 사용자 정보는 관리자만 수정 가능
    """
    client_info = get_client_info(request)
    
    try:
        # 대상 사용자 조회
        target_user = UserCRUD.get_user_by_id(db, user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        
        # 권한 확인
        is_self_update = user_id == current_user.id
        is_admin = current_user.is_admin
        
        if not is_self_update and not is_admin:
            logger.warning(f"권한 없는 사용자 정보 수정 시도: user_id={user_id}, requested_by={current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="다른 사용자의 정보를 수정할 권한이 없습니다"
            )
        
        # 본인이 수정하는 경우 is_active 필드 제거 (관리자만 수정 가능)
        if is_self_update and not is_admin:
            update_data = user_update.dict(exclude_unset=True)
            if 'is_active' in update_data:
                del update_data['is_active']
                user_update = UserUpdate(**update_data)
        
        # 이메일 중복 확인
        if user_update.email:
            existing_email = UserCRUD.get_user_by_email(db, user_update.email)
            if existing_email and existing_email.id != user_id:
                logger.warning(f"중복 이메일 수정 시도: {user_update.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 존재하는 이메일입니다"
                )
        
        # 사용자 정보 수정
        updated_user = UserCRUD.update_user(db, user_id, user_update)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        
        # 성공 로그 기록
        AuditCRUD.create_audit_log(
            db=db,
            user_id=current_user.id,
            action="update_user",
            result="success",
            resource=f"user:{user_id}",
            details=f"Updated user: {updated_user.username}",
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent")
        )
        
        logger.info(f"사용자 정보 수정 완료: user_id={user_id}, updated_by={current_user.id}")
        
        return UserResponse.from_orm(updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 정보 수정 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 정보 수정 중 오류가 발생했습니다"
        )


@router.delete("/{user_id}", summary="사용자 비활성화")
async def deactivate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_database_session),
    current_user: models.User = Depends(get_current_admin_user)  # 관리자만 비활성화 가능
):
    """
    사용자를 비활성화합니다.
    
    실제로 삭제하지 않고 is_active를 False로 설정합니다.
    관리자 권한이 필요합니다.
    """
    client_info = get_client_info(request)
    
    try:
        # 자기 자신은 비활성화할 수 없음
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="자기 자신을 비활성화할 수 없습니다"
            )
        
        # 대상 사용자 조회
        target_user = UserCRUD.get_user_by_id(db, user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        
        # 이미 비활성화된 경우
        if not target_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 비활성화된 사용자입니다"
            )
        
        # 사용자 비활성화
        deactivate_data = UserUpdate(is_active=False)
        updated_user = UserCRUD.update_user(db, user_id, deactivate_data)
        
        # 성공 로그 기록
        AuditCRUD.create_audit_log(
            db=db,
            user_id=current_user.id,
            action="deactivate_user",
            result="success",
            resource=f"user:{user_id}",
            details=f"Deactivated user: {target_user.username}",
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent")
        )
        
        logger.info(f"사용자 비활성화 완료: user_id={user_id}, deactivated_by={current_user.id}")
        
        return {"message": f"사용자 '{target_user.username}'가 비활성화되었습니다"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 비활성화 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 비활성화 중 오류가 발생했습니다"
        )