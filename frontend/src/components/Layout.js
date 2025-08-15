import React, { useState } from 'react';
import { Layout as AntLayout, Menu, Avatar, Dropdown, Typography, Space, Button } from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  TeamOutlined,
  SafetyOutlined,
  SettingOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  CloudServerOutlined,
  AuditOutlined,
  KeyOutlined
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const { Header, Sider, Content } = AntLayout;
const { Title, Text } = Typography;

const Layout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  const handleUserMenuClick = ({ key }) => {
    if (key === 'logout') {
      logout();
      navigate('/login');
    } else if (key === 'profile') {
      navigate('/settings');
    }
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '프로필 설정',
      onClick: () => handleUserMenuClick({ key: 'profile' })
    },
    {
      type: 'divider'
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '로그아웃',
      onClick: () => handleUserMenuClick({ key: 'logout' })
    }
  ];

  // 사용자 역할 확인
  const userRole = user?.role || 'viewer';
  const isAnalyst = userRole === 'analyst';
  const isAuditor = userRole === 'auditor';

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '대시보드',
    },
    {
      key: 'iam',
      icon: <CloudServerOutlined />,
      label: 'IAM 관리',
      children: [
        {
          key: '/iam/users',
          icon: <UserOutlined />,
          label: 'IAM 사용자',
        },
        {
          key: '/iam/roles',
          icon: <KeyOutlined />,
          label: 'IAM 역할',
        },
        {
          key: '/iam/policies',
          icon: <SafetyOutlined />,
          label: 'IAM 정책',
        },
      ],
    },
    // 보안 분석 - 분석가, 관리자, 감사자만 접근
    ...(isAdmin || isAnalyst || isAuditor ? [{
      key: '/analysis',
      icon: <AuditOutlined />,
      label: '보안 분석',
    }] : []),
    // 감사 로그 - 관리자, 감사자만 전체 접근 (일반 사용자는 개인 로그만)
    // 감사 로그 - 관리자, 분석가, 감사자만 접근
    ...(isAdmin || isAnalyst || isAuditor ? [{
      key: '/audit',
      icon: <AuditOutlined />,
      label: '감사 로그',
    }] : []),
    // 사용자 관리 - 관리자만
    ...(isAdmin ? [
      {
        key: '/users',
        icon: <TeamOutlined />,
        label: '사용자 관리',
      },
    ] : []),
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '설정',
    },
  ];

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        theme="dark"
        width={250}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          borderBottom: '1px solid #303030'
        }}>
          {collapsed ? (
            <CloudServerOutlined style={{ fontSize: 24, color: '#1890ff' }} />
          ) : (
            <Space>
              <CloudServerOutlined style={{ fontSize: 24, color: '#1890ff' }} />
              <Title level={4} style={{ color: 'white', margin: 0 }}>
                IAM Manager
              </Title>
            </Space>
          )}
        </div>
        
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0 }}
        />
      </Sider>

      <AntLayout style={{ marginLeft: collapsed ? 80 : 250, transition: 'margin-left 0.2s' }}>
        <Header style={{ 
          background: '#fff', 
          padding: '0 24px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          boxShadow: '0 1px 4px rgba(0,21,41,.08)'
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: 16, width: 64, height: 64 }}
          />

          <Space>
            <Text type="secondary">안녕하세요,</Text>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Space style={{ cursor: 'pointer' }}>
                <Avatar 
                  size="small" 
                  icon={<UserOutlined />} 
                  style={{ backgroundColor: '#1890ff' }}
                />
                <Text strong>{user?.username}</Text>
                {isAdmin && (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    (관리자)
                  </Text>
                )}
              </Space>
            </Dropdown>
          </Space>
        </Header>

        <Content style={{ 
          margin: '24px', 
          padding: '24px',
          background: '#f0f2f5',
          minHeight: 'calc(100vh - 112px)',
          overflow: 'auto'
        }}>
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  );
};

export default Layout;