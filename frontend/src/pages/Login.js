import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Card, Typography, Space } from 'antd';
import { UserOutlined, LockOutlined, CloudServerOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';

const { Title, Text } = Typography;

const Login = () => {
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';

  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const success = await login(values.username, values.password);
      if (success) {
        navigate(from, { replace: true });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <Card className="login-form">
        <div className="login-logo">
          <CloudServerOutlined />
        </div>
        
        <Title level={2} className="login-title">
          IAM Manager
        </Title>
        
        <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginBottom: 30 }}>
          AWS IAM 관리 대시보드에 로그인하세요
        </Text>

        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '사용자명을 입력해주세요!' },
              { min: 3, message: '사용자명은 최소 3자 이상이어야 합니다.' }
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="사용자명"
              autoComplete="username"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: '비밀번호를 입력해주세요!' },
              { min: 6, message: '비밀번호는 최소 6자 이상이어야 합니다.' }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="비밀번호"
              autoComplete="current-password"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{ height: 45 }}
            >
              로그인
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center', marginTop: 20 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            초기 관리자가 없다면 회원가입 API를 사용하세요
          </Text>
        </div>
      </Card>
    </div>
  );
};

export default Login;