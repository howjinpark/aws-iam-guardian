"""
Pydantic 스키마 정의
API 요청/응답 데이터 검증 및 직렬화
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re


class UserBase(BaseModel):
    """사용자 기본 스키마"""
    username: str = Field(..., min_length=3, max_length=50, description="사용자명")
    email: str = Field(None, description="이메일 주소 (선택사항)")
    
    @validator('username')
    def validate_username(cls, v):
        """사용자명 검증: 영문, 숫자, 언더스코어만 허용"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('사용자명은 영문, 숫자, 언더스코어만 사용 가능합니다')
        return v


class UserCreate(UserBase):
    """사용자 생성 스키마"""
    password: str = Field(..., min_length=8, max_length=100, description="비밀번호")
    
    @validator('password')
    def validate_password(cls, v):
        """비밀번호 강도 검증"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('비밀번호에 대문자가 포함되어야 합니다')
        if not re.search(r'[a-z]', v):
            raise ValueError('비밀번호에 소문자가 포함되어야 합니다')
        if not re.search(r'\d', v):
            raise ValueError('비밀번호에 숫자가 포함되어야 합니다')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('비밀번호에 특수문자가 포함되어야 합니다')
        return v


class UserUpdate(BaseModel):
    """사용자 정보 수정 스키마"""
    email: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """사용자 응답 스키마"""
    id: int
    username: str
    email: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """로그인 요청 스키마"""
    username: str = Field(..., description="사용자명 또는 이메일")
    password: str = Field(..., description="비밀번호")


class LoginResponse(BaseModel):
    """로그인 응답 스키마"""
    access_token: str = Field(..., description="JWT 액세스 토큰")
    token_type: str = Field(default="bearer", description="토큰 타입")
    expires_in: int = Field(..., description="토큰 만료 시간(초)")
    user: UserResponse = Field(..., description="사용자 정보")


class TokenData(BaseModel):
    """토큰 데이터 스키마"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    jti: Optional[str] = None  # JWT ID


class HealthCheck(BaseModel):
    """헬스체크 응답 스키마"""
    status: str = Field(default="healthy", description="서비스 상태")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="확인 시간")
    version: str = Field(..., description="서비스 버전")
    database: bool = Field(..., description="데이터베이스 연결 상태")


class ErrorResponse(BaseModel):
    """에러 응답 스키마"""
    error: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")
    details: Optional[dict] = Field(None, description="상세 정보")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="발생 시간")