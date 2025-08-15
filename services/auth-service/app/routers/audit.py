"""
감사 로그 API 라우터
시스템 활동 추적 및 감사 기능
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..database import get_database_session
from ..schemas import AuditLogResponse, AuditLogStats, ErrorResponse
from ..crud import AuditCRUD, UserCRUD
from ..dependencies import get_current_user, get_current_admin_user
from .. import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["감사 로그"])


@router.get("/logs", response_model=List[AuditLogResponse], summary="감사 로그 목록 조회")
async def get_audit_logs(
    user_id: Optional[int] = Query(None, description="특정 사용자 필터"),
    action: Optional[str] = Query(None, description="액션 필터"),
    result: Optional[str] = Query(None, description="결과 필터 (success, failure, error)"),
    skip: int = Query(0, ge=0, description="건너뛸 로그 수"),
    limit: int = Query(100, ge=1, le=1000, description="조회할 최대 로그 수"),
    db: Session = Depends(get_database_session),
    current_user: models.User = Depends(get_current_admin_user)  # 관리자만 조회 가능
):
    """
    감사 로그 목록을 조회합니다.
    
    - **user_id**: 특정 사용자의 로그만 조회
    - **action**: 특정 액션 필터 (login, logout, create_user 등)
    - **result**: 결과 필터 (success, failure, error)
    - **skip**: 페이징을 위한 건너뛸 로그 수
    - **limit**: 조회할 최대 로그 수 (최대 1000)
    
    관리자 권한이 필요합니다.
    """
    try:
        audit_logs = AuditCRUD.get_audit_logs(
            db=db,
            user_id=user_id,
            action=action,
            result=result,
            skip=skip,
            limit=limit
        )
        
        logger.info(f"감사 로그 조회: {len(audit_logs)}개, requested_by={current_user.id}")
        
        return [AuditLogResponse.from_orm(log) for log in audit_logs]
        
    except Exception as e:
        logger.error(f"감사 로그 조회 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="감사 로그 조회 중 오류가 발생했습니다"
        )


@router.get("/logs/my", response_model=List[AuditLogResponse], summary="내 활동 로그 조회")
async def get_my_audit_logs(
    action: Optional[str] = Query(None, description="액션 필터"),
    result: Optional[str] = Query(None, description="결과 필터"),
    skip: int = Query(0, ge=0, description="건너뛸 로그 수"),
    limit: int = Query(50, ge=1, le=500, description="조회할 최대 로그 수"),
    db: Session = Depends(get_database_session),
    current_user: models.User = Depends(get_current_user)
):
    """
    현재 사용자의 활동 로그를 조회합니다.
    
    본인의 활동 기록만 조회할 수 있습니다.
    """
    try:
        audit_logs = AuditCRUD.get_audit_logs(
            db=db,
            user_id=current_user.id,
            action=action,
            result=result,
            skip=skip,
            limit=limit
        )
        
        logger.debug(f"개인 활동 로그 조회: {len(audit_logs)}개, user_id={current_user.id}")
        
        return [AuditLogResponse.from_orm(log) for log in audit_logs]
        
    except Exception as e:
        logger.error(f"개인 활동 로그 조회 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="활동 로그 조회 중 오류가 발생했습니다"
        )


@router.get("/stats", response_model=AuditLogStats, summary="감사 로그 통계")
async def get_audit_stats(
    user_id: Optional[int] = Query(None, description="특정 사용자 통계"),
    db: Session = Depends(get_database_session),
    current_user: models.User = Depends(get_current_admin_user)  # 관리자만 조회 가능
):
    """
    감사 로그 통계 정보를 조회합니다.
    
    - 전체 로그 수
    - 성공/실패/에러 통계
    - 액션별 통계
    
    관리자 권한이 필요합니다.
    """
    try:
        stats = AuditCRUD.get_audit_log_stats(db=db, user_id=user_id)
        
        logger.info(f"감사 로그 통계 조회: total={stats['total_count']}, requested_by={current_user.id}")
        
        return AuditLogStats(**stats)
        
    except Exception as e:
        logger.error(f"감사 로그 통계 조회 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="감사 로그 통계 조회 중 오류가 발생했습니다"
        )


@router.get("/stats/my", response_model=AuditLogStats, summary="내 활동 통계")
async def get_my_audit_stats(
    db: Session = Depends(get_database_session),
    current_user: models.User = Depends(get_current_user)
):
    """
    현재 사용자의 활동 통계를 조회합니다.
    
    본인의 활동 통계만 조회할 수 있습니다.
    """
    try:
        stats = AuditCRUD.get_audit_log_stats(db=db, user_id=current_user.id)
        
        logger.debug(f"개인 활동 통계 조회: total={stats['total_count']}, user_id={current_user.id}")
        
        return AuditLogStats(**stats)
        
    except Exception as e:
        logger.error(f"개인 활동 통계 조회 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="활동 통계 조회 중 오류가 발생했습니다"
        )


@router.get("/actions", summary="사용 가능한 액션 목록")
async def get_available_actions(
    current_user: models.User = Depends(get_current_admin_user)
):
    """
    시스템에서 사용 가능한 감사 로그 액션 목록을 반환합니다.
    
    관리자 권한이 필요합니다.
    """
    actions = [
        "login",
        "logout", 
        "create_user",
        "update_user",
        "deactivate_user",
        "create_initial_admin",
        "change_password",
        "view_users",
        "view_audit_logs",
        "iam_users_query",
        "iam_roles_query",
        "iam_policies_query",
        "security_analysis",
        "system_settings_change"
    ]
    
    return {
        "actions": actions,
        "total_count": len(actions)
    }