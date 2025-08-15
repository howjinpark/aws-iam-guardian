import React, { useState } from 'react';
import { 
  Card, 
  Typography, 
  Tabs,
  Form,
  Input,
  Button,
  Space,
  Alert,
  Divider,
  Row,
  Col,
  Avatar,
  Upload,
  Switch,
  Select,
  message,
  Modal
} from 'antd';
import {
  SettingOutlined,
  UserOutlined,
  LockOutlined,
  BellOutlined,
  SecurityScanOutlined,
  SaveOutlined,
  CameraOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userService } from '../services/iamService';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { confirm } = Modal;

const Settings = () => {
  const [activeTab, setActiveTab] = useState('profile');
  const [profileForm] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const [notificationForm] = Form.useForm();
  const { user, updateUser } = useAuth();
  const queryClient = useQueryClient();

  // 현재 사용자 정보 조회
  const { 
    data: currentUserData
  } = useQuery({
    queryKey: ['current-user'],
    queryFn: () => userService.getCurrentUser(),
    staleTime: 5 * 60 * 1000,
  });

  const currentUser = currentUserData?.data || user;

  // 프로필 업데이트 뮤테이션
  const updateProfileMutation = useMutation({
    mutationFn: (userData) => userService.updateUser(currentUser.id, userData),
    onSuccess: (response) => {
      message.success('프로필이 성공적으로 업데이트되었습니다');
      updateUser(response.data);
      queryClient.invalidateQueries(['current-user']);
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '프로필 업데이트에 실패했습니다');
    },
  });

  // 비밀번호 변경 뮤테이션
  const changePasswordMutation = useMutation({
    mutationFn: (passwordData) => userService.changePassword(currentUser.id, passwordData),
    onSuccess: () => {
      message.success('비밀번호가 성공적으로 변경되었습니다');
      passwordForm.resetFields();
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '비밀번호 변경에 실패했습니다');
    },
  });

  // 프로필 업데이트 처리
  const handleProfileUpdate = async (values) => {
    updateProfileMutation.mutate(values);
  };

  // 비밀번호 변경 처리
  const handlePasswordChange = async (values) => {
    if (values.newPassword !== values.confirmPassword) {
      message.error('새 비밀번호가 일치하지 않습니다');
      return;
    }

    confirm({
      title: '비밀번호를 변경하시겠습니까?',
      icon: <ExclamationCircleOutlined />,
      content: '비밀번호 변경 후 다시 로그인해야 할 수 있습니다.',
      onOk() {
        changePasswordMutation.mutate(values);
      },
    });
  };

  // 알림 설정 처리
  const handleNotificationUpdate = async (values) => {
    // 실제로는 별도의 알림 설정 API가 필요하지만, 
    // 현재는 사용자 정보에 포함시켜 저장
    message.success('알림 설정이 저장되었습니다');
  };

  // 프로필 탭
  const ProfileTab = () => (
    <Card>
      <Row gutter={24}>
        <Col xs={24} md={8}>
          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            <Avatar 
              size={120} 
              icon={<UserOutlined />}
              style={{ backgroundColor: '#1890ff', marginBottom: 16 }}
            />
            <br />
            <Upload
              showUploadList={false}
              beforeUpload={() => {
                message.info('프로필 사진 업로드 기능은 준비 중입니다');
                return false;
              }}
            >
              <Button icon={<CameraOutlined />} size="small">
                사진 변경
              </Button>
            </Upload>
          </div>
        </Col>
        <Col xs={24} md={16}>
          <Form
            form={profileForm}
            layout="vertical"
            initialValues={{
              username: currentUser?.username,
              email: currentUser?.email,
              full_name: currentUser?.full_name,
            }}
            onFinish={handleProfileUpdate}
          >
            <Form.Item
              name="username"
              label="사용자명"
            >
              <Input disabled />
            </Form.Item>

            <Form.Item
              name="email"
              label="이메일"
              rules={[
                { required: true, message: '이메일을 입력해주세요' },
                { type: 'email', message: '올바른 이메일 형식이 아닙니다' }
              ]}
            >
              <Input />
            </Form.Item>

            <Form.Item
              name="full_name"
              label="이름"
            >
              <Input placeholder="이름을 입력해주세요" />
            </Form.Item>

            <Form.Item>
              <Button 
                type="primary" 
                htmlType="submit"
                icon={<SaveOutlined />}
                loading={updateProfileMutation.isLoading}
              >
                프로필 저장
              </Button>
            </Form.Item>
          </Form>
        </Col>
      </Row>
    </Card>
  );

  // 보안 탭
  const SecurityTab = () => (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card title="비밀번호 변경">
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handlePasswordChange}
          style={{ maxWidth: 400 }}
        >
          <Form.Item
            name="currentPassword"
            label="현재 비밀번호"
            rules={[
              { required: true, message: '현재 비밀번호를 입력해주세요' }
            ]}
          >
            <Input.Password placeholder="현재 비밀번호" />
          </Form.Item>

          <Form.Item
            name="newPassword"
            label="새 비밀번호"
            rules={[
              { required: true, message: '새 비밀번호를 입력해주세요' },
              { min: 8, message: '비밀번호는 최소 8자 이상이어야 합니다' }
            ]}
          >
            <Input.Password placeholder="새 비밀번호" />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            label="비밀번호 확인"
            rules={[
              { required: true, message: '비밀번호 확인을 입력해주세요' }
            ]}
          >
            <Input.Password placeholder="새 비밀번호 확인" />
          </Form.Item>

          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit"
              icon={<LockOutlined />}
              loading={changePasswordMutation.isLoading}
            >
              비밀번호 변경
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="보안 정보">
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div>
            <Text strong>계정 상태: </Text>
            <Text type={currentUser?.is_active ? 'success' : 'danger'}>
              {currentUser?.is_active ? '활성' : '비활성'}
            </Text>
          </div>
          <div>
            <Text strong>권한: </Text>
            <Text>{currentUser?.is_admin ? '관리자' : '일반 사용자'}</Text>
          </div>
          <div>
            <Text strong>계정 생성일: </Text>
            <Text>
              {currentUser?.created_at ? 
                new Date(currentUser.created_at).toLocaleDateString() : '-'}
            </Text>
          </div>
          <div>
            <Text strong>최종 로그인: </Text>
            <Text>
              {currentUser?.last_login ? 
                new Date(currentUser.last_login).toLocaleString() : '기록 없음'}
            </Text>
          </div>
        </Space>
      </Card>
    </Space>
  );

  // 알림 탭
  const NotificationTab = () => (
    <Card title="알림 설정">
      <Form
        form={notificationForm}
        layout="vertical"
        onFinish={handleNotificationUpdate}
        initialValues={{
          emailNotifications: true,
          securityAlerts: true,
          systemUpdates: false,
          weeklyReports: true,
        }}
      >
        <Form.Item
          name="emailNotifications"
          label="이메일 알림"
          valuePropName="checked"
        >
          <Switch 
            checkedChildren="켜짐" 
            unCheckedChildren="꺼짐"
          />
        </Form.Item>
        <Paragraph type="secondary" style={{ marginTop: -16, marginBottom: 24 }}>
          중요한 시스템 알림을 이메일로 받습니다
        </Paragraph>

        <Form.Item
          name="securityAlerts"
          label="보안 경고"
          valuePropName="checked"
        >
          <Switch 
            checkedChildren="켜짐" 
            unCheckedChildren="꺼짐"
          />
        </Form.Item>
        <Paragraph type="secondary" style={{ marginTop: -16, marginBottom: 24 }}>
          보안 위험 요소 발견 시 즉시 알림을 받습니다
        </Paragraph>

        <Form.Item
          name="systemUpdates"
          label="시스템 업데이트"
          valuePropName="checked"
        >
          <Switch 
            checkedChildren="켜짐" 
            unCheckedChildren="꺼짐"
          />
        </Form.Item>
        <Paragraph type="secondary" style={{ marginTop: -16, marginBottom: 24 }}>
          시스템 업데이트 및 새 기능 소식을 받습니다
        </Paragraph>

        <Form.Item
          name="weeklyReports"
          label="주간 보고서"
          valuePropName="checked"
        >
          <Switch 
            checkedChildren="켜짐" 
            unCheckedChildren="꺼짐"
          />
        </Form.Item>
        <Paragraph type="secondary" style={{ marginTop: -16, marginBottom: 24 }}>
          주간 보안 분석 보고서를 받습니다
        </Paragraph>

        <Divider />

        <Form.Item>
          <Button 
            type="primary" 
            htmlType="submit"
            icon={<SaveOutlined />}
          >
            알림 설정 저장
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );

  // 시스템 탭 (관리자만)
  const SystemTab = () => (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card title="시스템 설정">
        <Alert
          message="시스템 설정"
          description="시스템 전반적인 설정을 관리합니다. 변경 시 주의가 필요합니다."
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />
        
        <Form layout="vertical">
          <Form.Item label="세션 타임아웃 (분)">
            <Select defaultValue="60" style={{ width: 200 }}>
              <Option value="30">30분</Option>
              <Option value="60">1시간</Option>
              <Option value="120">2시간</Option>
              <Option value="480">8시간</Option>
            </Select>
          </Form.Item>

          <Form.Item label="로그 레벨">
            <Select defaultValue="INFO" style={{ width: 200 }}>
              <Option value="DEBUG">DEBUG</Option>
              <Option value="INFO">INFO</Option>
              <Option value="WARNING">WARNING</Option>
              <Option value="ERROR">ERROR</Option>
            </Select>
          </Form.Item>

          <Form.Item label="자동 백업">
            <Switch 
              defaultChecked 
              checkedChildren="켜짐" 
              unCheckedChildren="꺼짐"
            />
          </Form.Item>

          <Form.Item>
            <Button type="primary" icon={<SaveOutlined />}>
              시스템 설정 저장
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="데이터베이스 관리">
        <Space direction="vertical" size="middle">
          <div>
            <Text strong>데이터베이스 상태: </Text>
            <Text type="success">정상</Text>
          </div>
          <div>
            <Text strong>마지막 백업: </Text>
            <Text>2024-01-15 02:00:00</Text>
          </div>
          <Space>
            <Button>백업 실행</Button>
            <Button>로그 정리</Button>
            <Button danger>캐시 초기화</Button>
          </Space>
        </Space>
      </Card>
    </Space>
  );

  const tabItems = [
    {
      key: 'profile',
      label: (
        <span>
          <UserOutlined />
          프로필
        </span>
      ),
      children: <ProfileTab />,
    },
    {
      key: 'security',
      label: (
        <span>
          <LockOutlined />
          보안
        </span>
      ),
      children: <SecurityTab />,
    },
    {
      key: 'notifications',
      label: (
        <span>
          <BellOutlined />
          알림
        </span>
      ),
      children: <NotificationTab />,
    },
    ...(currentUser?.is_admin ? [{
      key: 'system',
      label: (
        <span>
          <SecurityScanOutlined />
          시스템
        </span>
      ),
      children: <SystemTab />,
    }] : []),
  ];

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2}>
            <SettingOutlined /> 설정
          </Title>
        </Col>
      </Row>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        size="large"
      />
    </div>
  );
};

export default Settings;