"""
데이터베이스 모델 정의
사용자 인증 관련 테이블 구조
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    """사용자 모델"""
    __tablename__ = "users"
    
    # 기본 필드
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    
    # 상태 필드
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class UserSession(Base):
    """사용자 세션 모델 (토큰 관리)"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    token_jti = Column(String(255), unique=True, index=True, nullable=False)  # JWT ID
    
    # 세션 정보
    ip_address = Column(String(45), nullable=True)  # IPv6 지원
    user_agent = Column(Text, nullable=True)
    
    # 시간 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # 상태
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"


class AuditLog(Base):
    """감사 로그 모델"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # 익명 액션도 있을 수 있음
    
    # 액션 정보
    action = Column(String(100), nullable=False, index=True)  # login, logout, create_user 등
    resource = Column(String(100), nullable=True)  # 대상 리소스
    result = Column(String(20), nullable=False)  # success, failure, error
    
    # 세부 정보
    details = Column(Text, nullable=True)  # JSON 형태의 추가 정보
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # 시간 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', result='{self.result}')>"