"""
데이터베이스 CRUD 작업
사용자 및 세션 관리 로직
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from . import models, schemas, security

logger = logging.getLogger(__name__)


class UserCRUD:
    """사용자 CRUD 작업 클래스"""
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
        """ID로 사용자 조회"""
        try:
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if user:
                logger.debug(f"사용자 조회 성공: ID={user_id}")
            return user
        except Exception as e:
            logger.error(f"사용자 조회 실패 (ID={user_id}): {e}")
            return None
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
        """사용자명으로 사용자 조회"""
        try:
            user = db.query(models.User).filter(models.User.username == username).first()
            if user:
                logger.debug(f"사용자 조회 성공: username={username}")
            return user
        except Exception as e:
            logger.error(f"사용자 조회 실패 (username={username}): {e}")
            return None
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
        """이메일로 사용자 조회"""
        try:
            user = db.query(models.User).filter(models.User.email == email).first()
            if user:
                logger.debug(f"사용자 조회 성공: email={email}")
            return user
        except Exception as e:
            logger.error(f"사용자 조회 실패 (email={email}): {e}")
            return None
    
    @staticmethod
    def get_user_by_username_or_email(db: Session, identifier: str) -> Optional[models.User]:
        """사용자명 또는 이메일로 사용자 조회"""
        try:
            user = db.query(models.User).filter(
                or_(
                    models.User.username == identifier,
                    models.User.email == identifier
                )
            ).first()
            if user:
                logger.debug(f"사용자 조회 성공: identifier={identifier}")
            return user
        except Exception as e:
            logger.error(f"사용자 조회 실패 (identifier={identifier}): {e}")
            return None
    
    @staticmethod
    def create_user(db: Session, user: schemas.UserCreate) -> models.User:
        """새 사용자 생성"""
        try:
            # 비밀번호 해싱
            hashed_password = security.hash_password(user.password)
            
            # 사용자 객체 생성
            db_user = models.User(
                username=user.username,
                email=user.email,
                hashed_password=hashed_password
            )
            
            # 데이터베이스에 저장
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            logger.info(f"새 사용자 생성 완료: ID={db_user.id}, username={db_user.username}")
            return db_user
            
        except Exception as e:
            logger.error(f"사용자 생성 실패: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate) -> Optional[models.User]:
        """사용자 정보 수정"""
        try:
            db_user = db.query(models.User).filter(models.User.id == user_id).first()
            if not db_user:
                return None
            
            # 수정할 필드만 업데이트
            update_data = user_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_user, field, value)
            
            db.commit()
            db.refresh(db_user)
            
            logger.info(f"사용자 정보 수정 완료: ID={user_id}")
            return db_user
            
        except Exception as e:
            logger.error(f"사용자 정보 수정 실패 (ID={user_id}): {e}")
            db.rollback()
            raise
    
    @staticmethod
    def update_last_login(db: Session, user_id: int) -> None:
        """마지막 로그인 시간 업데이트"""
        try:
            db.query(models.User).filter(models.User.id == user_id).update({
                "last_login": datetime.utcnow()
            })
            db.commit()
            logger.debug(f"마지막 로그인 시간 업데이트: user_id={user_id}")
        except Exception as e:
            logger.error(f"마지막 로그인 시간 업데이트 실패 (user_id={user_id}): {e}")
            db.rollback()
    
    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
        """사용자 목록 조회"""
        try:
            users = db.query(models.User).offset(skip).limit(limit).all()
            logger.debug(f"사용자 목록 조회: {len(users)}명")
            return users
        except Exception as e:
            logger.error(f"사용자 목록 조회 실패: {e}")
            return []


class SessionCRUD:
    """세션 CRUD 작업 클래스"""
    
    @staticmethod
    def create_session(db: Session, user_id: int, token_jti: str, 
                      ip_address: str = None, user_agent: str = None) -> models.UserSession:
        """새 세션 생성"""
        try:
            expires_at = datetime.utcnow() + timedelta(minutes=security.settings.access_token_expire_minutes)
            
            db_session = models.UserSession(
                user_id=user_id,
                token_jti=token_jti,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=expires_at
            )
            
            db.add(db_session)
            db.commit()
            db.refresh(db_session)
            
            logger.info(f"새 세션 생성: user_id={user_id}, jti={token_jti}")
            return db_session
            
        except Exception as e:
            logger.error(f"세션 생성 실패: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_active_session(db: Session, token_jti: str) -> Optional[models.UserSession]:
        """활성 세션 조회"""
        try:
            session = db.query(models.UserSession).filter(
                and_(
                    models.UserSession.token_jti == token_jti,
                    models.UserSession.is_active == True,
                    models.UserSession.expires_at > datetime.utcnow()
                )
            ).first()
            return session
        except Exception as e:
            logger.error(f"세션 조회 실패 (jti={token_jti}): {e}")
            return None
    
    @staticmethod
    def revoke_session(db: Session, token_jti: str) -> bool:
        """세션 무효화"""
        try:
            result = db.query(models.UserSession).filter(
                models.UserSession.token_jti == token_jti
            ).update({
                "is_active": False,
                "revoked_at": datetime.utcnow()
            })
            
            db.commit()
            
            if result > 0:
                logger.info(f"세션 무효화 완료: jti={token_jti}")
                return True
            else:
                logger.warning(f"무효화할 세션을 찾을 수 없음: jti={token_jti}")
                return False
                
        except Exception as e:
            logger.error(f"세션 무효화 실패 (jti={token_jti}): {e}")
            db.rollback()
            return False


class AuditCRUD:
    """감사 로그 CRUD 작업 클래스"""
    
    @staticmethod
    def create_audit_log(db: Session, user_id: Optional[int], action: str, 
                        result: str, resource: str = None, details: str = None,
                        ip_address: str = None, user_agent: str = None) -> models.AuditLog:
        """감사 로그 생성"""
        try:
            audit_log = models.AuditLog(
                user_id=user_id,
                action=action,
                resource=resource,
                result=result,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            
            logger.debug(f"감사 로그 생성: action={action}, result={result}")
            return audit_log
            
        except Exception as e:
            logger.error(f"감사 로그 생성 실패: {e}")
            db.rollback()
            raise