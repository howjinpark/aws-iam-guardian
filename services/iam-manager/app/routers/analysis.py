"""
IAM 권한 분석 API 라우터
권한 분석, 위험도 평가, 최소 권한 추천 등
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
import logging
import json

from ..aws_client import iam_service
from ..config import list_aws_accounts

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["IAM 권한 분석"])


@router.get("/{account_key}/user/{user_name}/permissions", summary="사용자 권한 분석")
async def analyze_user_permissions(
    account_key: str,
    user_name: str
):
    """
    특정 IAM 사용자의 권한을 상세 분석합니다.
    
    - 직접 연결된 정책
    - 그룹을 통한 권한
    - 인라인 정책
    - 위험도 평가
    """
    try:
        # 계정 존재 여부 확인
        aws_accounts = list_aws_accounts()
        if account_key not in aws_accounts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"계정을 찾을 수 없습니다: {account_key}"
            )
        
        # IAM 클라이언트 가져오기
        iam_client = iam_service.client_manager.get_iam_client(account_key)
        if not iam_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AWS IAM 서비스에 연결할 수 없습니다"
            )
        
        logger.info(f"사용자 권한 분석 시작: {account_key}/{user_name}")
        
        # 사용자 기본 정보
        try:
            user_info = iam_client.get_user(UserName=user_name)['User']
        except iam_client.exceptions.NoSuchEntityException:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"사용자를 찾을 수 없습니다: {user_name}"
            )
        
        # 직접 연결된 정책
        try:
            attached_policies = iam_client.list_attached_user_policies(UserName=user_name)
        except Exception as e:
            logger.warning(f"연결된 정책 조회 실패 ({user_name}): {e}")
            attached_policies = {'AttachedPolicies': []}
        
        # 인라인 정책
        try:
            inline_policies = iam_client.list_user_policies(UserName=user_name)
        except Exception as e:
            logger.warning(f"인라인 정책 조회 실패 ({user_name}): {e}")
            inline_policies = {'PolicyNames': []}
        
        # 그룹 정보
        try:
            groups = iam_client.get_groups_for_user(UserName=user_name)
        except Exception as e:
            logger.warning(f"그룹 조회 실패 ({user_name}): {e}")
            groups = {'Groups': []}
        
        # 액세스 키 정보
        try:
            access_keys = iam_client.list_access_keys(UserName=user_name)
        except Exception as e:
            logger.warning(f"액세스 키 조회 실패 ({user_name}): {e}")
            access_keys = {'AccessKeyMetadata': []}
        
        # 위험도 분석
        risk_factors = []
        risk_score = 0
        
        # 관리자 권한 확인
        for policy in attached_policies['AttachedPolicies']:
            if 'Administrator' in policy['PolicyName'] or policy['PolicyArn'].endswith('AdministratorAccess'):
                risk_factors.append("관리자 권한 보유")
                risk_score += 50
        
        # 오래된 액세스 키 확인
        for key in access_keys['AccessKeyMetadata']:
            from datetime import datetime, timezone
            key_age = (datetime.now(timezone.utc) - key['CreateDate']).days
            if key_age > 90:
                risk_factors.append(f"오래된 액세스 키 ({key_age}일)")
                risk_score += 20
        
        # 인라인 정책 사용
        if inline_policies['PolicyNames']:
            risk_factors.append("인라인 정책 사용")
            risk_score += 10
        
        # 결과 구성
        analysis_result = {
            "user_info": {
                "user_name": user_info['UserName'],
                "user_id": user_info['UserId'],
                "arn": user_info['Arn'],
                "create_date": user_info['CreateDate'].isoformat(),
                "password_last_used": user_info.get('PasswordLastUsed', '').isoformat() if user_info.get('PasswordLastUsed') else None
            },
            "permissions": {
                "attached_policies": [
                    {
                        "policy_name": p['PolicyName'],
                        "policy_arn": p['PolicyArn']
                    }
                    for p in attached_policies['AttachedPolicies']
                ],
                "inline_policies": inline_policies['PolicyNames'],
                "groups": [
                    {
                        "group_name": g['GroupName'],
                        "group_id": g['GroupId'],
                        "arn": g['Arn']
                    }
                    for g in groups['Groups']
                ]
            },
            "access_keys": [
                {
                    "access_key_id": ak['AccessKeyId'],
                    "status": ak['Status'],
                    "create_date": ak['CreateDate'].isoformat(),
                    "age_days": (datetime.now(timezone.utc) - ak['CreateDate']).days
                }
                for ak in access_keys['AccessKeyMetadata']
            ],
            "risk_assessment": {
                "risk_score": min(risk_score, 100),  # 최대 100점
                "risk_level": "HIGH" if risk_score >= 70 else "MEDIUM" if risk_score >= 30 else "LOW",
                "risk_factors": risk_factors
            },
            "recommendations": []
        }
        
        # 추천사항 생성
        if risk_score >= 50:
            analysis_result["recommendations"].append("관리자 권한을 최소 권한으로 제한하세요")
        
        if any(key['age_days'] > 90 for key in analysis_result['access_keys']):
            analysis_result["recommendations"].append("90일 이상 된 액세스 키를 교체하세요")
        
        if inline_policies['PolicyNames']:
            analysis_result["recommendations"].append("인라인 정책을 관리형 정책으로 변경하세요")
        
        if not analysis_result["recommendations"]:
            analysis_result["recommendations"].append("현재 권한 설정이 양호합니다")
        
        logger.info(f"사용자 권한 분석 완료: {user_name}, 위험도: {analysis_result['risk_assessment']['risk_level']}")
        
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 권한 분석 실패 ({account_key}/{user_name}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 권한 분석 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{account_key}/high-risk-users", summary="고위험 사용자 탐지")
async def find_high_risk_users(
    account_key: str,
    min_risk_score: int = Query(50, description="최소 위험도 점수")
):
    """
    고위험 사용자들을 탐지합니다.
    
    - 관리자 권한을 가진 사용자
    - 오래된 액세스 키를 가진 사용자
    - 과도한 권한을 가진 사용자
    """
    try:
        # 계정 존재 여부 확인
        aws_accounts = list_aws_accounts()
        if account_key not in aws_accounts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"계정을 찾을 수 없습니다: {account_key}"
            )
        
        logger.info(f"고위험 사용자 탐지 시작: account={account_key}")
        
        # 모든 사용자 조회
        users = iam_service.list_users(account_key)
        high_risk_users = []
        
        for user in users:
            user_name = user['UserName']
            risk_score = 0
            risk_factors = []
            
            # 관리자 권한 확인
            attached_policies = user.get('attached_policies', [])
            for policy_arn in attached_policies:
                if 'AdministratorAccess' in policy_arn:
                    risk_factors.append("관리자 권한")
                    risk_score += 50
            
            # 액세스 키 확인
            access_keys = user.get('access_keys', [])
            for key in access_keys:
                if 'CreateDate' in key:
                    from datetime import datetime
                    create_date = datetime.fromisoformat(key['CreateDate'].replace('Z', '+00:00'))
                    age_days = (datetime.now(create_date.tzinfo) - create_date).days
                    if age_days > 90:
                        risk_factors.append(f"오래된 액세스 키 ({age_days}일)")
                        risk_score += 20
            
            # 인라인 정책 확인
            if user.get('inline_policies'):
                risk_factors.append("인라인 정책 사용")
                risk_score += 10
            
            # 최소 위험도 이상인 사용자만 포함
            if risk_score >= min_risk_score:
                high_risk_users.append({
                    "user_name": user_name,
                    "user_id": user.get('UserId'),
                    "arn": user.get('Arn'),
                    "risk_score": risk_score,
                    "risk_level": "HIGH" if risk_score >= 70 else "MEDIUM",
                    "risk_factors": risk_factors,
                    "create_date": user.get('CreateDate')
                })
        
        # 위험도 순으로 정렬
        high_risk_users.sort(key=lambda x: x['risk_score'], reverse=True)
        
        logger.info(f"고위험 사용자 탐지 완료: {len(high_risk_users)}명")
        
        return {
            "account_key": account_key,
            "min_risk_score": min_risk_score,
            "total_high_risk_users": len(high_risk_users),
            "users": high_risk_users
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"고위험 사용자 탐지 실패 ({account_key}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"고위험 사용자 탐지 중 오류가 발생했습니다: {str(e)}"
        )