"""
IAM 리소스 관리 API 라우터
실제 AWS IAM 데이터 조회 및 분석
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
import logging

from ..aws_client import iam_service
from ..schemas import IAMUserResponse, IAMRoleResponse, IAMPolicyResponse
from ..config import list_aws_accounts

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/accounts", tags=["IAM 리소스 관리"])


@router.get("/{account_key}/users", summary="IAM 사용자 목록 조회")
async def get_iam_users(
    account_key: str,
    path_prefix: str = Query("/", description="경로 필터 (예: /developers/)"),
    limit: int = Query(100, le=1000, description="최대 조회 수")
):
    """
    지정된 AWS 계정의 IAM 사용자 목록을 조회합니다.
    
    - **account_key**: AWS 계정 키 (main, dev, staging, prod 등)
    - **path_prefix**: IAM 경로 필터 (기본값: /)
    - **limit**: 최대 조회 개수
    
    실제 AWS IAM API를 호출하여 최신 데이터를 반환합니다.
    """
    try:
        # 계정 존재 여부 확인
        aws_accounts = list_aws_accounts()
        if account_key not in aws_accounts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"계정을 찾을 수 없습니다: {account_key}"
            )
        
        # AWS IAM 사용자 목록 조회
        logger.info(f"IAM 사용자 조회 시작: account={account_key}, path={path_prefix}")
        users = iam_service.list_users(account_key, path_prefix)
        
        # 결과 제한
        if len(users) > limit:
            users = users[:limit]
        
        # 응답 데이터 변환
        result = []
        for user in users:
            user_data = {
                "user_name": user.get("UserName"),
                "user_id": user.get("UserId"),
                "arn": user.get("Arn"),
                "path": user.get("Path", "/"),
                "create_date": user.get("CreateDate"),
                "password_last_used": user.get("PasswordLastUsed"),
                "attached_policies": user.get("attached_policies", []),
                "inline_policies": user.get("inline_policies", []),
                "groups": user.get("groups", []),
                "access_keys": user.get("access_keys", [])
            }
            result.append(user_data)
        
        logger.info(f"IAM 사용자 조회 완료: {len(result)}명")
        
        return {
            "account_key": account_key,
            "total_count": len(result),
            "users": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"IAM 사용자 조회 실패 ({account_key}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"IAM 사용자 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{account_key}/roles", summary="IAM 역할 목록 조회")
async def get_iam_roles(
    account_key: str,
    path_prefix: str = Query("/", description="경로 필터"),
    limit: int = Query(100, le=1000, description="최대 조회 수")
):
    """
    지정된 AWS 계정의 IAM 역할 목록을 조회합니다.
    """
    try:
        # 계정 존재 여부 확인
        aws_accounts = list_aws_accounts()
        if account_key not in aws_accounts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"계정을 찾을 수 없습니다: {account_key}"
            )
        
        # AWS IAM 역할 목록 조회
        logger.info(f"IAM 역할 조회 시작: account={account_key}, path={path_prefix}")
        roles = iam_service.list_roles(account_key, path_prefix)
        
        # 결과 제한
        if len(roles) > limit:
            roles = roles[:limit]
        
        # 응답 데이터 변환
        result = []
        for role in roles:
            role_data = {
                "role_name": role.get("RoleName"),
                "role_id": role.get("RoleId"),
                "arn": role.get("Arn"),
                "path": role.get("Path", "/"),
                "description": role.get("Description"),
                "create_date": role.get("CreateDate"),
                "assume_role_policy": role.get("AssumeRolePolicyDocument"),
                "max_session_duration": role.get("MaxSessionDuration", 3600),
                "attached_policies": role.get("attached_policies", []),
                "inline_policies": role.get("inline_policies", [])
            }
            result.append(role_data)
        
        logger.info(f"IAM 역할 조회 완료: {len(result)}개")
        
        return {
            "account_key": account_key,
            "total_count": len(result),
            "roles": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"IAM 역할 조회 실패 ({account_key}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"IAM 역할 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{account_key}/policies", summary="IAM 정책 목록 조회")
async def get_iam_policies(
    account_key: str,
    scope: str = Query("Local", description="정책 범위 (Local=고객관리, AWS=AWS관리, All=전체)"),
    limit: int = Query(100, le=1000, description="최대 조회 수")
):
    """
    지정된 AWS 계정의 IAM 정책 목록을 조회합니다.
    
    - **scope**: 
      - Local: 고객 관리형 정책만
      - AWS: AWS 관리형 정책만  
      - All: 모든 정책
    """
    try:
        # 계정 존재 여부 확인
        aws_accounts = list_aws_accounts()
        if account_key not in aws_accounts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"계정을 찾을 수 없습니다: {account_key}"
            )
        
        # AWS IAM 정책 목록 조회
        logger.info(f"IAM 정책 조회 시작: account={account_key}, scope={scope}")
        policies = iam_service.list_policies(account_key, scope)
        
        # 결과 제한
        if len(policies) > limit:
            policies = policies[:limit]
        
        # 응답 데이터 변환
        result = []
        for policy in policies:
            policy_data = {
                "policy_name": policy.get("PolicyName"),
                "policy_id": policy.get("PolicyId"),
                "arn": policy.get("Arn"),
                "path": policy.get("Path", "/"),
                "description": policy.get("Description"),
                "create_date": policy.get("CreateDate"),
                "update_date": policy.get("UpdateDate"),
                "attachment_count": policy.get("AttachmentCount", 0),
                "is_attachable": policy.get("IsAttachable", True),
                "default_version_id": policy.get("DefaultVersionId")
            }
            result.append(policy_data)
        
        logger.info(f"IAM 정책 조회 완료: {len(result)}개")
        
        return {
            "account_key": account_key,
            "scope": scope,
            "total_count": len(result),
            "policies": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"IAM 정책 조회 실패 ({account_key}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"IAM 정책 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{account_key}/summary", summary="계정 요약 정보 조회")
async def get_account_summary(account_key: str):
    """
    지정된 AWS 계정의 IAM 요약 정보를 조회합니다.
    
    사용자 수, 역할 수, 정책 수 등의 통계 정보를 제공합니다.
    """
    try:
        # 계정 존재 여부 확인
        aws_accounts = list_aws_accounts()
        if account_key not in aws_accounts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"계정을 찾을 수 없습니다: {account_key}"
            )
        
        # AWS 계정 요약 정보 조회
        logger.info(f"계정 요약 조회 시작: account={account_key}")
        summary = iam_service.get_account_summary(account_key)
        
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AWS 서비스에 연결할 수 없습니다"
            )
        
        logger.info(f"계정 요약 조회 완료: account={account_key}")
        
        return {
            "account_key": account_key,
            "account_info": aws_accounts[account_key],
            "summary": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"계정 요약 조회 실패 ({account_key}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"계정 요약 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/", summary="사용 가능한 AWS 계정 목록")
async def list_accounts():
    """
    현재 설정된 AWS 계정 목록을 반환합니다.
    """
    try:
        aws_accounts = list_aws_accounts()
        
        result = []
        for key, config in aws_accounts.items():
            account_info = {
                "account_key": key,
                "account_id": config.get("account_id"),
                "account_name": config.get("account_name"),
                "regions": config.get("regions", [])
            }
            result.append(account_info)
        
        return {
            "total_count": len(result),
            "accounts": result
        }
        
    except Exception as e:
        logger.error(f"계정 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"계정 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )