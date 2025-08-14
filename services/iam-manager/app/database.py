"""
IAM Manager Service 데이터베이스 연결 및 세션 관리
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# 데이터베이스 엔진 생성
engine = create_engine(
    settings.database_url,
    poolclass=StaticPool,
    pool_pre_ping=True,
    echo=settings.debug
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 베이스 모델 클래스
Base = declarative_base()

# 메타데이터
metadata = MetaData()


def get_database_session() -> Generator[Session, None, None]:
    """데이터베이스 세션 생성 및 관리"""
    session = SessionLocal()
    try:
        logger.debug("IAM Manager 데이터베이스 세션 생성")
        yield session
    except Exception as e:
        logger.error(f"데이터베이스 세션 오류: {e}")
        session.rollback()
        raise
    finally:
        logger.debug("IAM Manager 데이터베이스 세션 종료")
        session.close()


def create_tables():
    """데이터베이스 테이블 생성"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("IAM Manager 데이터베이스 테이블 생성 완료")
    except Exception as e:
        logger.error(f"테이블 생성 실패: {e}")
        raise


def check_database_connection() -> bool:
    """데이터베이스 연결 상태 확인"""
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("IAM Manager 데이터베이스 연결 성공")
        return True
    except Exception as e:
        logger.error(f"데이터베이스 연결 실패: {e}")
        return False