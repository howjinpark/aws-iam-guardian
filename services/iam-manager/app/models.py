"""
IAM Manager Service 데이터베이스 모델
AWS 계정, IAM 리소스, 정책 분석 결과 등을 저장
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class AWSAccount(Base):
    """AWS 계정 정보 모델"""
    __tablename__ = "aws_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_key = Column(String(50), unique=True, index=True, nullable=False)  # dev, staging, prod
    account_id = Column(String(12), unique=True, index=True, nullable=False)   # AWS Account ID
    account_name = Column(String(100), nullable=False)
    
    # 설정 정보
    regions = Column(JSON, nullable=False)  # ["us-east-1", "ap-northeast-2"]
    role_arn = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sync = Column(DateTime(timezone=True), nullable=True)
    
    # 관계
    iam_users = relationship("IAMUser", back_populates="aws_account")
    iam_roles = relationship("IAMRole", back_populates="aws_account")
    iam_policies = relationship("IAMPolicy", back_populates="aws_account")
    
    def __repr__(self):
        return f"<AWSAccount(key='{self.account_key}', id='{self.account_id}', name='{self.account_name}')>"


class IAMUser(Base):
    """IAM 사용자 모델"""
    __tablename__ = "iam_users"
    
    id = Column(Integer, primary_key=True, index=True)
    aws_account_id = Column(Integer, ForeignKey("aws_accounts.id"), nullable=False)
    
    # AWS IAM 정보
    user_name = Column(String(64), nullable=False, index=True)
    user_id = Column(String(21), nullable=False, index=True)  # AWS User ID (AIDACKCEVSQ6C2EXAMPLE)
    arn = Column(String(255), nullable=False)
    path = Column(String(512), default="/")
    
    # 상태 정보
    create_date = Column(DateTime(timezone=True), nullable=True)
    password_last_used = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # 권한 분석 결과
    attached_policies = Column(JSON, nullable=True)  # 연결된 정책 목록
    inline_policies = Column(JSON, nullable=True)    # 인라인 정책 목록
    groups = Column(JSON, nullable=True)             # 소속 그룹 목록
    access_keys = Column(JSON, nullable=True)        # 액세스 키 정보
    
    # 위험도 분석
    risk_score = Column(Integer, default=0)          # 0-100 위험도 점수
    risk_factors = Column(JSON, nullable=True)       # 위험 요소 목록
    
    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sync = Column(DateTime(timezone=True), nullable=True)
    
    # 관계
    aws_account = relationship("AWSAccount", back_populates="iam_users")
    
    def __repr__(self):
        return f"<IAMUser(name='{self.user_name}', account='{self.aws_account_id}')>"


class IAMRole(Base):
    """IAM 역할 모델"""
    __tablename__ = "iam_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    aws_account_id = Column(Integer, ForeignKey("aws_accounts.id"), nullable=False)
    
    # AWS IAM 정보
    role_name = Column(String(64), nullable=False, index=True)
    role_id = Column(String(21), nullable=False, index=True)
    arn = Column(String(255), nullable=False)
    path = Column(String(512), default="/")
    
    # 역할 설정
    assume_role_policy = Column(JSON, nullable=True)  # Trust Policy
    description = Column(Text, nullable=True)
    max_session_duration = Column(Integer, default=3600)
    
    # 권한 분석
    attached_policies = Column(JSON, nullable=True)
    inline_policies = Column(JSON, nullable=True)
    risk_score = Column(Integer, default=0)
    risk_factors = Column(JSON, nullable=True)
    
    # 메타데이터
    create_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sync = Column(DateTime(timezone=True), nullable=True)
    
    # 관계
    aws_account = relationship("AWSAccount", back_populates="iam_roles")
    
    def __repr__(self):
        return f"<IAMRole(name='{self.role_name}', account='{self.aws_account_id}')>"


class IAMPolicy(Base):
    """IAM 정책 모델"""
    __tablename__ = "iam_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    aws_account_id = Column(Integer, ForeignKey("aws_accounts.id"), nullable=False)
    
    # AWS IAM 정보
    policy_name = Column(String(128), nullable=False, index=True)
    policy_id = Column(String(21), nullable=True, index=True)  # AWS Managed Policy ID
    arn = Column(String(255), nullable=False)
    path = Column(String(512), default="/")
    
    # 정책 내용
    policy_document = Column(JSON, nullable=False)    # 정책 JSON
    policy_type = Column(String(20), nullable=False)  # AWS_MANAGED, CUSTOMER_MANAGED, INLINE
    description = Column(Text, nullable=True)
    
    # 분석 결과
    permissions = Column(JSON, nullable=True)         # 권한 목록 분석
    resources = Column(JSON, nullable=True)           # 대상 리소스 분석
    risk_score = Column(Integer, default=0)
    risk_factors = Column(JSON, nullable=True)
    
    # 사용 현황
    attachment_count = Column(Integer, default=0)     # 연결된 사용자/역할 수
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # 메타데이터
    create_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sync = Column(DateTime(timezone=True), nullable=True)
    
    # 관계
    aws_account = relationship("AWSAccount", back_populates="iam_policies")
    
    def __repr__(self):
        return f"<IAMPolicy(name='{self.policy_name}', type='{self.policy_type}')>"


class PolicyAnalysis(Base):
    """정책 분석 결과 모델"""
    __tablename__ = "policy_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    aws_account_id = Column(Integer, ForeignKey("aws_accounts.id"), nullable=False)
    
    # 분석 대상
    resource_type = Column(String(20), nullable=False)  # USER, ROLE, POLICY
    resource_name = Column(String(128), nullable=False)
    resource_arn = Column(String(255), nullable=False)
    
    # 분석 결과
    analysis_type = Column(String(50), nullable=False)  # RISK_ASSESSMENT, LEAST_PRIVILEGE, UNUSED_PERMISSIONS
    analysis_result = Column(JSON, nullable=False)      # 분석 결과 JSON
    
    # 추천사항
    recommendations = Column(JSON, nullable=True)       # 개선 추천사항
    severity = Column(String(20), default="LOW")        # LOW, MEDIUM, HIGH, CRITICAL
    
    # 메타데이터
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<PolicyAnalysis(resource='{self.resource_name}', type='{self.analysis_type}')>"


class SyncHistory(Base):
    """AWS 동기화 이력 모델"""
    __tablename__ = "sync_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    aws_account_id = Column(Integer, ForeignKey("aws_accounts.id"), nullable=False)
    
    # 동기화 정보
    sync_type = Column(String(50), nullable=False)      # FULL, INCREMENTAL, USERS_ONLY, ROLES_ONLY, POLICIES_ONLY
    region = Column(String(20), nullable=False)
    
    # 결과
    status = Column(String(20), nullable=False)         # SUCCESS, FAILED, PARTIAL
    resources_synced = Column(JSON, nullable=True)      # 동기화된 리소스 통계
    errors = Column(JSON, nullable=True)                # 오류 목록
    
    # 성능 정보
    duration_seconds = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SyncHistory(account='{self.aws_account_id}', type='{self.sync_type}', status='{self.status}')>"