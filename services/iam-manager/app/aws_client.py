"""
AWS SDK 클라이언트 관리
멀티 계정/리전 지원 및 IAM 서비스 연동
"""
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from .config import settings, get_aws_account_config, initialize_aws_config

logger = logging.getLogger(__name__)


class AWSClientManager:
    """AWS 클라이언트 관리 클래스"""
    
    def __init__(self):
        self._clients: Dict[str, Dict[str, Any]] = {}
        self._sessions: Dict[str, boto3.Session] = {}
        # AWS 설정 초기화
        initialize_aws_config()
    
    def get_session(self, account_key: str) -> Optional[boto3.Session]:
        """특정 계정의 boto3 세션 반환"""
        if account_key in self._sessions:
            return self._sessions[account_key]
        
        account_config = get_aws_account_config(account_key)
        if not account_config:
            logger.error(f"계정 설정을 찾을 수 없음: {account_key}")
            return None
        
        try:
            # Role ARN이 있으면 AssumeRole 사용
            if account_config.get('role_arn'):
                session = self._create_assume_role_session(account_config)
            else:
                # 기본 자격증명 사용
                session = boto3.Session(
                    region_name=settings.aws_default_region
                )
            
            self._sessions[account_key] = session
            logger.info(f"AWS 세션 생성 완료: {account_key}")
            return session
            
        except Exception as e:
            logger.error(f"AWS 세션 생성 실패 ({account_key}): {e}")
            return None
    
    def _create_assume_role_session(self, account_config: Dict) -> boto3.Session:
        """AssumeRole을 사용한 세션 생성"""
        sts_client = boto3.client('sts')
        
        response = sts_client.assume_role(
            RoleArn=account_config['role_arn'],
            RoleSessionName=f"IAMManager-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        
        credentials = response['Credentials']
        
        return boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
            region_name=settings.aws_default_region
        )
    
    def get_iam_client(self, account_key: str, region: str = None) -> Optional[Any]:
        """IAM 클라이언트 반환"""
        client_key = f"{account_key}-iam-{region or settings.aws_default_region}"
        
        if client_key in self._clients:
            return self._clients[client_key]
        
        session = self.get_session(account_key)
        if not session:
            return None
        
        try:
            # IAM은 글로벌 서비스이므로 리전 무관
            client = session.client('iam')
            self._clients[client_key] = client
            logger.debug(f"IAM 클라이언트 생성: {account_key}")
            return client
            
        except Exception as e:
            logger.error(f"IAM 클라이언트 생성 실패 ({account_key}): {e}")
            return None
    
    def test_connection(self, account_key: str) -> bool:
        """AWS 연결 테스트"""
        try:
            iam_client = self.get_iam_client(account_key)
            if not iam_client:
                return False
            
            # 간단한 API 호출로 연결 테스트
            iam_client.get_account_summary()
            logger.info(f"AWS 연결 테스트 성공: {account_key}")
            return True
            
        except ClientError as e:
            logger.error(f"AWS 연결 테스트 실패 ({account_key}): {e}")
            return False
        except Exception as e:
            logger.error(f"AWS 연결 테스트 오류 ({account_key}): {e}")
            return False


class IAMService:
    """IAM 서비스 클래스"""
    
    def __init__(self, client_manager: AWSClientManager):
        self.client_manager = client_manager
    
    def list_users(self, account_key: str, path_prefix: str = "/") -> List[Dict]:
        """IAM 사용자 목록 조회"""
        try:
            iam_client = self.client_manager.get_iam_client(account_key)
            if not iam_client:
                return []
            
            paginator = iam_client.get_paginator('list_users')
            users = []
            
            for page in paginator.paginate(PathPrefix=path_prefix):
                for user in page['Users']:
                    # 추가 정보 수집
                    user_detail = self._get_user_details(iam_client, user['UserName'])
                    user.update(user_detail)
                    users.append(user)
            
            logger.info(f"IAM 사용자 조회 완료 ({account_key}): {len(users)}명")
            return users
            
        except ClientError as e:
            logger.error(f"IAM 사용자 조회 실패 ({account_key}): {e}")
            return []
    
    def _get_user_details(self, iam_client: Any, user_name: str) -> Dict:
        """사용자 상세 정보 조회"""
        details = {
            'attached_policies': [],
            'inline_policies': [],
            'groups': [],
            'access_keys': []
        }
        
        try:
            # 연결된 정책 조회
            try:
                attached_policies = iam_client.list_attached_user_policies(UserName=user_name)
                details['attached_policies'] = [p['PolicyArn'] for p in attached_policies['AttachedPolicies']]
            except Exception as e:
                logger.warning(f"연결된 정책 조회 실패 ({user_name}): {e}")
                details['attached_policies'] = []
            
            # 인라인 정책 조회
            try:
                inline_policies = iam_client.list_user_policies(UserName=user_name)
                details['inline_policies'] = inline_policies['PolicyNames']
            except Exception as e:
                logger.warning(f"인라인 정책 조회 실패 ({user_name}): {e}")
                details['inline_policies'] = []
            
            # 그룹 조회
            try:
                groups = iam_client.get_groups_for_user(UserName=user_name)
                details['groups'] = [g['GroupName'] for g in groups['Groups']]
            except Exception as e:
                logger.warning(f"그룹 조회 실패 ({user_name}): {e}")
                details['groups'] = []
            
            # 액세스 키 조회
            try:
                access_keys = iam_client.list_access_keys(UserName=user_name)
                details['access_keys'] = [
                    {
                        'AccessKeyId': ak['AccessKeyId'],
                        'Status': ak['Status'],
                        'CreateDate': ak['CreateDate'].isoformat() if hasattr(ak['CreateDate'], 'isoformat') else str(ak['CreateDate'])
                    }
                    for ak in access_keys['AccessKeyMetadata']
                ]
            except Exception as e:
                logger.warning(f"액세스 키 조회 실패 ({user_name}): {e}")
                details['access_keys'] = []
            
        except ClientError as e:
            logger.warning(f"사용자 상세 정보 조회 실패 ({user_name}): {e}")
        
        return details
    
    def list_roles(self, account_key: str, path_prefix: str = "/") -> List[Dict]:
        """IAM 역할 목록 조회"""
        try:
            iam_client = self.client_manager.get_iam_client(account_key)
            if not iam_client:
                return []
            
            paginator = iam_client.get_paginator('list_roles')
            roles = []
            
            for page in paginator.paginate(PathPrefix=path_prefix):
                for role in page['Roles']:
                    # 추가 정보 수집
                    role_detail = self._get_role_details(iam_client, role['RoleName'])
                    role.update(role_detail)
                    roles.append(role)
            
            logger.info(f"IAM 역할 조회 완료 ({account_key}): {len(roles)}개")
            return roles
            
        except ClientError as e:
            logger.error(f"IAM 역할 조회 실패 ({account_key}): {e}")
            return []
    
    def _get_role_details(self, iam_client: Any, role_name: str) -> Dict:
        """역할 상세 정보 조회"""
        details = {
            'attached_policies': [],
            'inline_policies': []
        }
        
        try:
            # 연결된 정책 조회
            attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
            details['attached_policies'] = [p['PolicyArn'] for p in attached_policies['AttachedPolicies']]
            
            # 인라인 정책 조회
            inline_policies = iam_client.list_role_policies(RoleName=role_name)
            details['inline_policies'] = inline_policies['PolicyNames']
            
        except ClientError as e:
            logger.warning(f"역할 상세 정보 조회 실패 ({role_name}): {e}")
        
        return details
    
    def list_policies(self, account_key: str, scope: str = "Local") -> List[Dict]:
        """IAM 정책 목록 조회"""
        try:
            iam_client = self.client_manager.get_iam_client(account_key)
            if not iam_client:
                return []
            
            paginator = iam_client.get_paginator('list_policies')
            policies = []
            
            for page in paginator.paginate(Scope=scope):  # Local = Customer Managed
                policies.extend(page['Policies'])
            
            logger.info(f"IAM 정책 조회 완료 ({account_key}): {len(policies)}개")
            return policies
            
        except ClientError as e:
            logger.error(f"IAM 정책 조회 실패 ({account_key}): {e}")
            return []
    
    def get_account_summary(self, account_key: str) -> Dict:
        """계정 요약 정보 조회"""
        try:
            iam_client = self.client_manager.get_iam_client(account_key)
            if not iam_client:
                return {}
            
            response = iam_client.get_account_summary()
            summary = response['SummaryMap']
            
            logger.info(f"계정 요약 조회 완료: {account_key}")
            return summary
            
        except ClientError as e:
            logger.error(f"계정 요약 조회 실패 ({account_key}): {e}")
            return {}


# 전역 인스턴스
aws_client_manager = AWSClientManager()
iam_service = IAMService(aws_client_manager)