"""
IAM Manager Service 기본 테스트
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os

# 테스트용 환경변수 설정
os.environ.update({
    "DATABASE_URL": "sqlite:///./test.db",
    "AWS_ACCESS_KEY_ID": "testing",
    "AWS_SECRET_ACCESS_KEY": "testing",
    "AWS_DEFAULT_REGION": "us-east-1",
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
        with patch('app.aws_client.aws_client_manager.test_connection', return_value=True):
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "version" in data
            assert "database" in data


def test_metrics_endpoint():
    """메트릭스 엔드포인트 테스트"""
    with patch('app.database.check_database_connection', return_value=True):
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "service_info" in data
        assert "database_connected" in data
        assert "timestamp" in data


@pytest.mark.asyncio
async def test_aws_mock_integration():
    """AWS Mock 통합 테스트"""
    from moto import mock_iam
    import boto3
    
    with mock_iam():
        # Mock IAM 클라이언트 생성
        iam_client = boto3.client(
            'iam',
            aws_access_key_id='testing',
            aws_secret_access_key='testing',
            region_name='us-east-1'
        )
        
        # 테스트용 사용자 생성
        response = iam_client.create_user(UserName='test-user')
        assert response['User']['UserName'] == 'test-user'
        
        # 사용자 목록 조회
        users = iam_client.list_users()
        assert len(users['Users']) == 1
        assert users['Users'][0]['UserName'] == 'test-user'


def test_accounts_endpoint():
    """계정 목록 엔드포인트 테스트"""
    response = client.get("/api/v1/accounts/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio 
async def test_database_connection_failure():
    """데이터베이스 연결 실패 시 헬스체크 테스트"""
    with patch('app.database.check_database_connection', return_value=False):
        with patch('app.aws_client.aws_client_manager.test_connection', return_value=False):
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database"] is False