import api from './api';

const IAM_BASE_URL = process.env.REACT_APP_IAM_API_URL || 'http://localhost:8001';

// IAM Manager API 클라이언트
const iamApi = api.create({
  baseURL: IAM_BASE_URL,
});

export const iamService = {
  // 계정 관리
  getAccounts: () => iamApi.get('/api/v1/accounts/'),
  
  getAccountSummary: (accountKey) => 
    iamApi.get(`/api/v1/accounts/${accountKey}/summary`),

  // IAM 사용자 관리
  getIAMUsers: (accountKey, params = {}) => 
    iamApi.get(`/api/v1/accounts/${accountKey}/users`, { params }),
  
  // IAM 역할 관리
  getIAMRoles: (accountKey, params = {}) => 
    iamApi.get(`/api/v1/accounts/${accountKey}/roles`, { params }),
  
  // IAM 정책 관리
  getIAMPolicies: (accountKey, params = {}) => 
    iamApi.get(`/api/v1/accounts/${accountKey}/policies`, { params }),

  // 권한 분석
  analyzeUserPermissions: (accountKey, userName) => 
    iamApi.get(`/api/v1/analyze/${accountKey}/user/${userName}/permissions`),
  
  getHighRiskUsers: (accountKey, minRiskScore = 50) => 
    iamApi.get(`/api/v1/analyze/${accountKey}/high-risk-users`, {
      params: { min_risk_score: minRiskScore }
    }),
};

// 시스템 사용자 관리 서비스
export const userService = {
  // 사용자 목록 조회
  getUsers: (params = {}) => 
    api.get('/api/v1/users/', { params }),
  
  // 특정 사용자 조회
  getUser: (userId) => 
    api.get(`/api/v1/users/${userId}`),
  
  // 사용자 생성
  createUser: (userData) => 
    api.post('/api/v1/users/', userData),
  
  // 사용자 정보 수정
  updateUser: (userId, userData) => 
    api.put(`/api/v1/users/${userId}`, userData),
  
  // 사용자 비활성화
  deactivateUser: (userId) => 
    api.delete(`/api/v1/users/${userId}`),
  
  // 초기 관리자 생성
  createInitialAdmin: (userData) => 
    api.post('/api/v1/users/init-admin', userData),
  
  // 현재 사용자 정보 조회
  getCurrentUser: () => 
    api.get('/api/v1/auth/me'),
  
  // 비밀번호 변경 (사용자 수정 API 활용)
  changePassword: (userId, passwordData) => 
    api.put(`/api/v1/users/${userId}`, { password: passwordData.newPassword }),
};

// 감사 로그 서비스
export const auditService = {
  // 감사 로그 목록 조회 (관리자)
  getAuditLogs: (params = {}) => 
    api.get('/api/v1/audit/logs', { params }),
  
  // 내 활동 로그 조회
  getMyAuditLogs: (params = {}) => 
    api.get('/api/v1/audit/logs/my', { params }),
  
  // 감사 로그 통계 (관리자)
  getAuditStats: (params = {}) => 
    api.get('/api/v1/audit/stats', { params }),
  
  // 내 활동 통계
  getMyAuditStats: () => 
    api.get('/api/v1/audit/stats/my'),
  
  // 사용 가능한 액션 목록
  getAvailableActions: () => 
    api.get('/api/v1/audit/actions'),
};

export default iamService;