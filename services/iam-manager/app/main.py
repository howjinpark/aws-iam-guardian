"""
IAM Manager Service 메인 애플리케이션
"""
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .aws_client import aws_client_manager
from .config import settings
from .database import check_database_connection, create_tables
from .schemas import ErrorResponse, HealthCheck


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
    logger.info("IAM Manager Service 시작 중...")
    
    try:
        # 데이터베이스 연결 확인
        if not check_database_connection():
            logger.error("데이터베이스 연결 실패")
            sys.exit(1)
        
        # 테이블 생성
        create_tables()
        
        logger.info("IAM Manager Service 시작 완료")
        
    except Exception as e:
        logger.error(f"서비스 시작 중 오류: {e}")
        sys.exit(1)
    
    yield
    
    # 종료 시 실행
    logger.info("IAM Manager Service 종료 중...")


# FastAPI 앱 생성
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    IAM 관리 시스템의 IAM Manager 서비스
    
    ## 주요 기능
    
    * **멀티 계정 관리**: 여러 AWS 계정을 한 번에 관리
    * **IAM 리소스 관리**: 사용자, 역할, 정책 CRUD
    * **권한 분석**: 과도한 권한 탐지 및 최소 권한 추천
    * **정책 시뮬레이션**: AWS Policy Simulator 연동
    * **실시간 동기화**: AWS와 데이터베이스 동기화
    
    ## AWS 연동
    
    * Cross-account Role 기반 접근
    * 멀티 리전 지원
    * 실시간 IAM 데이터 수집
    """,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
from .routers import analysis, iam

app.include_router(iam.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")


# 기본 엔드포인트
@app.get("/", summary="서비스 정보")
async def root():
    """서비스 기본 정보"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs_url": "/docs" if settings.debug else "disabled",
        "container_registry": "ghcr.io"
    }


@app.get("/health", response_model=HealthCheck, summary="헬스체크")
async def health_check():
    """
    서비스 상태 확인
    
    데이터베이스 연결 상태와 AWS 계정별 연결 상태를 확인합니다.
    """
    database_status = check_database_connection()
    
    # AWS 계정별 연결 상태 확인
    from .config import list_aws_accounts
    aws_accounts = list_aws_accounts()  # 동적으로 계정 목록 생성
    
    aws_connectivity = {}
    for account_key in aws_accounts.keys():
        aws_connectivity[account_key] = aws_client_manager.test_connection(account_key)
    
    # 전체 상태 결정
    overall_status = "healthy" if database_status and any(aws_connectivity.values()) else "unhealthy"
    
    return HealthCheck(
        status=overall_status,
        version=settings.app_version,
        database=database_status,
        aws_connectivity=aws_connectivity
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
        "aws_accounts": len(settings.aws_accounts),
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"IAM Manager Service 시작: {settings.host}:{settings.port}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )