import React, { useState } from 'react';
import { 
  Card, 
  Typography, 
  Table, 
  Tag, 
  Button, 
  Space, 
  Modal, 
  Form,
  Input,
  Switch,
  Alert,
  Row,
  Col,
  Statistic,
  Descriptions,
  Select,
  message,
  Popconfirm
} from 'antd';
import {
  UserOutlined,
  PlusOutlined,
  EditOutlined,
  ReloadOutlined,
  SearchOutlined,
  InfoCircleOutlined,
  TeamOutlined,
  UserAddOutlined,
  StopOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userService } from '../services/iamService';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;

const Users = () => {
  const [searchText, setSearchText] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [userModalVisible, setUserModalVisible] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();
  const queryClient = useQueryClient();

  // 사용자 목록 조회
  const { 
    data: usersData, 
    isLoading: usersLoading, 
    error: usersError,
    refetch: refetchUsers 
  } = useQuery({
    queryKey: ['users'],
    queryFn: () => userService.getUsers({ limit: 1000 }),
    staleTime: 2 * 60 * 1000,
  });

  const users = usersData?.data || [];

  // 검색 필터링
  const filteredUsers = users.filter(user => 
    user.username.toLowerCase().includes(searchText.toLowerCase()) ||
    user.email.toLowerCase().includes(searchText.toLowerCase()) ||
    (user.full_name && user.full_name.toLowerCase().includes(searchText.toLowerCase()))
  );

  // 사용자 생성 뮤테이션
  const createUserMutation = useMutation({
    mutationFn: userService.createUser,
    onSuccess: () => {
      message.success('사용자가 성공적으로 생성되었습니다');
      setCreateModalVisible(false);
      form.resetFields();
      queryClient.invalidateQueries(['users']);
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '사용자 생성에 실패했습니다');
    },
  });

  // 사용자 수정 뮤테이션
  const updateUserMutation = useMutation({
    mutationFn: ({ userId, userData }) => userService.updateUser(userId, userData),
    onSuccess: () => {
      message.success('사용자 정보가 성공적으로 수정되었습니다');
      setEditModalVisible(false);
      editForm.resetFields();
      queryClient.invalidateQueries(['users']);
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '사용자 정보 수정에 실패했습니다');
    },
  });

  // 사용자 비활성화 뮤테이션
  const deactivateUserMutation = useMutation({
    mutationFn: userService.deactivateUser,
    onSuccess: () => {
      message.success('사용자가 성공적으로 비활성화되었습니다');
      queryClient.invalidateQueries(['users']);
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '사용자 비활성화에 실패했습니다');
    },
  });

  // 사용자 상세 정보 모달
  const showUserDetails = (user) => {
    setSelectedUser(user);
    setUserModalVisible(true);
  };

  // 사용자 생성 모달
  const showCreateModal = () => {
    form.resetFields();
    setCreateModalVisible(true);
  };

  // 사용자 수정 모달
  const showEditModal = (user) => {
    setSelectedUser(user);
    editForm.setFieldsValue({
      email: user.email,
      full_name: user.full_name,
      is_active: user.is_active,
    });
    setEditModalVisible(true);
  };

  // 사용자 생성 처리
  const handleCreateUser = async (values) => {
    createUserMutation.mutate(values);
  };

  // 사용자 수정 처리
  const handleUpdateUser = async (values) => {
    updateUserMutation.mutate({
      userId: selectedUser.id,
      userData: values
    });
  };

  // 사용자 비활성화 처리
  const handleDeactivateUser = (userId) => {
    deactivateUserMutation.mutate(userId);
  };

  // 사용자 상태 색상
  const getUserStatusColor = (isActive) => {
    return isActive ? 'green' : 'red';
  };

  // 사용자 상태 텍스트
  const getUserStatusText = (isActive) => {
    return isActive ? '활성' : '비활성';
  };

  // 테이블 컬럼 정의
  const columns = [
    {
      title: '사용자명',
      dataIndex: 'username',
      key: 'username',
      width: 150,
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <Button 
            type="link" 
            onClick={() => showUserDetails(record)}
            style={{ padding: 0, height: 'auto' }}
          >
            <UserOutlined /> {text}
          </Button>
          {record.is_admin && (
            <Tag color="gold" size="small">관리자</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '이메일',
      dataIndex: 'email',
      key: 'email',
      ellipsis: true,
    },
    {
      title: '이름',
      dataIndex: 'full_name',
      key: 'full_name',
      render: (text) => text || <Text type="secondary">-</Text>,
    },
    {
      title: '상태',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      align: 'center',
      render: (isActive) => (
        <Tag color={getUserStatusColor(isActive)}>
          {getUserStatusText(isActive)}
        </Tag>
      ),
    },
    {
      title: '생성일',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date) => date ? new Date(date).toLocaleDateString() : '-',
    },
    {
      title: '최종 로그인',
      dataIndex: 'last_login',
      key: 'last_login',
      width: 120,
      render: (date) => date ? new Date(date).toLocaleDateString() : '없음',
    },
    {
      title: '작업',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space>
          <Button 
            type="primary" 
            size="small"
            icon={<InfoCircleOutlined />}
            onClick={() => showUserDetails(record)}
          >
            상세
          </Button>
          <Button 
            size="small"
            icon={<EditOutlined />}
            onClick={() => showEditModal(record)}
          >
            수정
          </Button>
          {record.is_active && (
            <Popconfirm
              title="사용자를 비활성화하시겠습니까?"
              description="비활성화된 사용자는 로그인할 수 없습니다."
              onConfirm={() => handleDeactivateUser(record.id)}
              okText="비활성화"
              cancelText="취소"
            >
              <Button 
                size="small"
                danger
                icon={<StopOutlined />}
                loading={deactivateUserMutation.isLoading}
              >
                비활성화
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  // 통계 데이터
  const stats = {
    total: users.length,
    active: users.filter(u => u.is_active).length,
    inactive: users.filter(u => !u.is_active).length,
    admins: users.filter(u => u.is_admin).length,
  };

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2}>
            <TeamOutlined /> 사용자 관리
          </Title>
        </Col>
        <Col>
          <Space>
            <Button 
              type="primary"
              icon={<PlusOutlined />}
              onClick={showCreateModal}
            >
              사용자 추가
            </Button>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => refetchUsers()}
              loading={usersLoading}
            >
              새로고침
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 통계 카드 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="전체 사용자"
              value={stats.total}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="활성 사용자"
              value={stats.active}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="비활성 사용자"
              value={stats.inactive}
              prefix={<StopOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="관리자"
              value={stats.admins}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 검색 */}
      <Card style={{ marginBottom: 16 }}>
        <Search
          placeholder="사용자명, 이메일, 이름으로 검색"
          allowClear
          enterButton={<SearchOutlined />}
          size="large"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ maxWidth: 400 }}
        />
      </Card>

      {/* 에러 표시 */}
      {usersError && (
        <Alert
          message="사용자 목록 조회 실패"
          description={usersError.response?.data?.detail || usersError.message}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 사용자 목록 테이블 */}
      <Card>
        <Table
          columns={columns}
          dataSource={filteredUsers}
          rowKey="id"
          loading={usersLoading}
          pagination={{
            total: filteredUsers.length,
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} / 총 ${total}개`,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 사용자 생성 모달 */}
      <Modal
        title={
          <Space>
            <UserAddOutlined />
            새 사용자 생성
          </Space>
        }
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateUser}
        >
          <Form.Item
            name="username"
            label="사용자명"
            rules={[
              { required: true, message: '사용자명을 입력해주세요' },
              { min: 3, max: 50, message: '사용자명은 3-50자여야 합니다' },
              { pattern: /^[a-zA-Z0-9_]+$/, message: '영문, 숫자, 언더스코어만 사용 가능합니다' }
            ]}
          >
            <Input placeholder="사용자명 입력" />
          </Form.Item>

          <Form.Item
            name="email"
            label="이메일"
            rules={[
              { required: true, message: '이메일을 입력해주세요' },
              { type: 'email', message: '올바른 이메일 형식이 아닙니다' }
            ]}
          >
            <Input placeholder="이메일 입력" />
          </Form.Item>

          <Form.Item
            name="password"
            label="비밀번호"
            rules={[
              { required: true, message: '비밀번호를 입력해주세요' },
              { min: 8, message: '비밀번호는 최소 8자 이상이어야 합니다' }
            ]}
          >
            <Input.Password placeholder="비밀번호 입력" />
          </Form.Item>

          <Form.Item
            name="full_name"
            label="이름"
          >
            <Input placeholder="이름 입력 (선택사항)" />
          </Form.Item>

          <Form.Item
            name="role"
            label="역할"
          >
            <Select placeholder="역할 선택 (선택사항)">
              <Option value="viewer">조회자</Option>
              <Option value="analyst">분석가</Option>
              <Option value="admin">관리자</Option>
            </Select>
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setCreateModalVisible(false)}>
                취소
              </Button>
              <Button 
                type="primary" 
                htmlType="submit"
                loading={createUserMutation.isLoading}
              >
                생성
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 사용자 수정 모달 */}
      <Modal
        title={
          <Space>
            <EditOutlined />
            사용자 정보 수정
          </Space>
        }
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleUpdateUser}
        >
          <Form.Item
            name="email"
            label="이메일"
            rules={[
              { required: true, message: '이메일을 입력해주세요' },
              { type: 'email', message: '올바른 이메일 형식이 아닙니다' }
            ]}
          >
            <Input placeholder="이메일 입력" />
          </Form.Item>

          <Form.Item
            name="full_name"
            label="이름"
          >
            <Input placeholder="이름 입력" />
          </Form.Item>

          <Form.Item
            name="is_active"
            label="활성 상태"
            valuePropName="checked"
          >
            <Switch 
              checkedChildren="활성" 
              unCheckedChildren="비활성" 
            />
          </Form.Item>

          <Form.Item
            name="role"
            label="역할"
          >
            <Select placeholder="역할 선택">
              <Option value="viewer">조회자</Option>
              <Option value="analyst">분석가</Option>
              <Option value="admin">관리자</Option>
            </Select>
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setEditModalVisible(false)}>
                취소
              </Button>
              <Button 
                type="primary" 
                htmlType="submit"
                loading={updateUserMutation.isLoading}
              >
                수정
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 사용자 상세 정보 모달 */}
      <Modal
        title={
          <Space>
            <UserOutlined />
            사용자 상세 정보
          </Space>
        }
        open={userModalVisible}
        onCancel={() => setUserModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setUserModalVisible(false)}>
            닫기
          </Button>
        ]}
        width={700}
      >
        {selectedUser && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="사용자명" span={2}>
              <Space>
                <Text strong>{selectedUser.username}</Text>
                {selectedUser.is_admin && (
                  <Tag color="gold">관리자</Tag>
                )}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="사용자 ID">
              <Text code>{selectedUser.id}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="상태">
              <Tag color={getUserStatusColor(selectedUser.is_active)}>
                {getUserStatusText(selectedUser.is_active)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="이메일" span={2}>
              {selectedUser.email}
            </Descriptions.Item>
            <Descriptions.Item label="이름">
              {selectedUser.full_name || '설정되지 않음'}
            </Descriptions.Item>
            <Descriptions.Item label="권한">
              {selectedUser.is_admin ? '관리자' : '일반 사용자'}
            </Descriptions.Item>
            <Descriptions.Item label="생성일">
              {selectedUser.created_at ? 
                new Date(selectedUser.created_at).toLocaleString() : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="수정일">
              {selectedUser.updated_at ? 
                new Date(selectedUser.updated_at).toLocaleString() : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="최종 로그인" span={2}>
              {selectedUser.last_login ? 
                new Date(selectedUser.last_login).toLocaleString() : '로그인 기록 없음'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default Users;