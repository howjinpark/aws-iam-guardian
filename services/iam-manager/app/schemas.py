"""
IAM Manager Service Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class AWSAccountBase(BaseModel):
    """AWS 계정 기본 스키마"""
    account_key: str = Field(..., description="계정 키 (dev, staging, prod)")
    account_id: str = Field(..., min_length=12, max_length=12, description="AWS 계정 ID")
    account_name: str = Field(..., description="계정 이름")
    regions: List[str] = Field(..., description="사용할 리전 목록")
    role_arn: Optional[str] = Field(None, description="Cross-account 역할 ARN")


class AWSAccountCreate(AWSAccountBase):
    """AWS 계정 생성 스키마"""
    pass


class AWSAccountResponse(AWSAccountBase):
    """AWS 계정 응답 스키마"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class IAMUserBase(BaseModel):
    """IAM 사용자 기본 스키마"""
    user_name: str = Field(..., description="IAM 사용자명")
    path: str = Field(default="/", description="IAM 경로")


class IAMUserResponse(IAMUserBase):
    """IAM 사용자 응답 스키마"""
    id: int
    user_id: str
    arn: str
    create_date: Optional[datetime] = None
    password_last_used: Optional[datetime] = None
    is_active: bool
    risk_score: int
    attached_policies: Optional[List[str]] = None
    groups: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class IAMRoleResponse(BaseModel):
    """IAM 역할 응답 스키마"""
    id: int
    role_name: str
    role_id: str
    arn: str
    path: str
    description: Optional[str] = None
    max_session_duration: int
    risk_score: int
    attached_policies: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class IAMPolicyResponse(BaseModel):
    """IAM 정책 응답 스키마"""
    id: int
    policy_name: str
    arn: str
    policy_type: str
    description: Optional[str] = None
    risk_score: int
    attachment_count: int
    
    class Config:
        from_attributes = True


class SyncRequest(BaseModel):
    """동기화 요청 스키마"""
    account_key: str = Field(..., description="동기화할 계정 키")
    sync_type: str = Field(default="FULL", description="동기화 타입")
    regions: Optional[List[str]] = Field(None, description="동기화할 리전 (없으면 전체)")


class SyncResponse(BaseModel):
    """동기화 응답 스키마"""
    sync_id: int
    status: str
    message: str
    started_at: datetime
    resources_synced: Optional[Dict[str, int]] = None


class HealthCheck(BaseModel):
    """헬스체크 응답 스키마"""
    status: str = Field(default="healthy", description="서비스 상태")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="확인 시간")
    version: str = Field(..., description="서비스 버전")
    database: bool = Field(..., description="데이터베이스 연결 상태")
    aws_connectivity: Dict[str, bool] = Field(..., description="AWS 계정별 연결 상태")


class ErrorResponse(BaseModel):
    """에러 응답 스키마"""
    error: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")
    details: Optional[Dict[str, Any]] = Field(None, description="상세 정보")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="발생 시간")