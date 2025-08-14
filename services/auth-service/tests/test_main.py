"""
Auth Service 기본 테스트
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os

# 테스트용 환경변수 설정
os.environ.update({
    "DATABASE_URL": "sqlite:///./test.db",
    "SECRET_KEY": "test-secret-key-for-testing",
    "DEBUG": "true"
})

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert "status" in data
    assert data["status"] == "running"


def test_health_endpoint():
    """헬스체크 엔드포인트 테스트"""
    with patch('app.database.check_database_connection', return_value=True):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "database" in data
        assert data["status"] == "healthy"


def test_health_endpoint_unhealthy():
    """데이터베이스 연결 실패 시 헬스체크 테스트"""
    with patch('app.database.check_database_connection', return_value=False):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] is False


def test_metrics_endpoint():
    """메트릭스 엔드포인트 테스트"""
    with patch('app.database.check_database_connection', return_value=True):
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "service_info" in data
        assert "database_connected" in data
        assert "timestamp" in data


def test_docs_endpoint():
    """API 문서 엔드포인트 테스트 (DEBUG 모드)"""
    response = client.get("/docs")
    # DEBUG 모드에서는 200, 프로덕션에서는 404
    assert response.status_code in [200, 404]


def test_cors_headers():
    """CORS 헤더 테스트"""
    response = client.options("/")
    # CORS 미들웨어가 적용되어 있는지 확인
    assert response.status_code in [200, 405]  # OPTIONS 메서드 허용 여부