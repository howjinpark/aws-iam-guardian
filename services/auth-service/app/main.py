"""
Auth Service 메인 애플리케이션
FastAPI 앱 설정 및 라우터 등록
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import sys
from datetime import datetime

from .config import settings
from .database import create_tables, check_database_connection
from .routers import auth, users
from .schemas import HealthCheck, ErrorResponse


# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 실행
    logger.info("Auth Service 시작 중...")
    
    try:
        # 데이터베이스 연결 확인
        if not check_database_connection():
            logger.error("데이터베이스 연결 실패")
            sys.exit(1)
        
        # 테이블 생성
        create_tables()
        
        logger.info("Auth Service 시작 완료")
        
    except Exception as e:
        logger.error(f"서비스 시작 중 오류: {e}")
        sys.exit(1)
    
    yield
    
    # 종료 시 실행
    logger.info("Auth Service 종료 중...")


# FastAPI 앱 생성
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    IAM 관리 시스템의 인증 서비스
    
    ## 주요 기능
    
    * **사용자 인증**: JWT 기반 로그인/로그아웃
    * **사용자 관리**: 사용자 생성, 조회, 수정, 비활성화
    * **세션 관리**: 토큰 기반 세션 관리 및 무효화
    * **감사 로그**: 모든 인증 관련 활동 기록
    
    ## 보안 기능
    
    * 비밀번호 강도 검증
    * JWT 토큰 기반 인증
    * 세션 무효화 지원
    * IP 주소 및 User-Agent 추적
    """,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 전역 예외 처리기
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """요청 검증 오류 처리"""
    logger.warning(f"요청 검증 오류: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="VALIDATION_ERROR",
            message="요청 데이터가 올바르지 않습니다",
            details={"errors": exc.errors()}
        ).dict()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 처리"""
    logger.error(f"예상치 못한 오류: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="INTERNAL_SERVER_ERROR",
            message="서버 내부 오류가 발생했습니다"
        ).dict()
    )


# 미들웨어: 요청 로깅
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """HTTP 요청 로깅 미들웨어"""
    start_time = datetime.utcnow()
    
    # 클라이언트 정보
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # 요청 로깅
    logger.info(f"요청 시작: {request.method} {request.url.path} - IP: {client_ip}")
    
    try:
        response = await call_next(request)
        
        # 응답 시간 계산
        process_time = (datetime.utcnow() - start_time).total_seconds()
        
        # 응답 로깅
        logger.info(
            f"요청 완료: {request.method} {request.url.path} - "
            f"상태: {response.status_code} - 처리시간: {process_time:.3f}s"
        )
        
        # 응답 헤더에 처리 시간 추가
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(
            f"요청 오류: {request.method} {request.url.path} - "
            f"오류: {str(e)} - 처리시간: {process_time:.3f}s"
        )
        raise


# 라우터 등록
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")


# 기본 엔드포인트
@app.get("/", summary="서비스 정보")
async def root():
    """서비스 기본 정보"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs_url": "/docs" if settings.debug else "disabled"
    }


@app.get("/health", response_model=HealthCheck, summary="헬스체크")
async def health_check():
    """
    서비스 상태 확인
    
    데이터베이스 연결 상태를 포함한 전반적인 서비스 상태를 반환합니다.
    """
    database_status = check_database_connection()
    
    return HealthCheck(
        status="healthy" if database_status else "unhealthy",
        version=settings.app_version,
        database=database_status
    )


@app.get("/metrics", summary="메트릭스")
async def metrics():
    """
    Prometheus 메트릭스
    
    모니터링을 위한 기본 메트릭스를 반환합니다.
    """
    return {
        "service_info": {
            "name": settings.app_name,
            "version": settings.app_version
        },
        "database_connected": check_database_connection(),
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Auth Service 시작: {settings.host}:{settings.port}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )