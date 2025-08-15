import React from 'react';
import { Alert, Card } from 'antd';
import { useAuth } from '../contexts/AuthContext';

const RoleGuard = ({ 
  children, 
  allowedRoles = [], 
  fallback = null,
  showMessage = true 
}) => {
  const { isAdmin, userRole } = useAuth();

  // 관리자는 모든 권한 보유
  if (isAdmin) {
    return children;
  }

  // 허용된 역할 확인
  const hasPermission = allowedRoles.includes(userRole);

  if (!hasPermission) {
    if (fallback) {
      return fallback;
    }

    if (showMessage) {
      return (
        <Card>
          <Alert
            message="접근 권한 없음"
            description={`이 기능은 ${allowedRoles.join(', ')} 권한이 필요합니다. 현재 권한: ${userRole}`}
            type="warning"
            showIcon
          />
        </Card>
      );
    }

    return null;
  }

  return children;
};

export default RoleGuard;