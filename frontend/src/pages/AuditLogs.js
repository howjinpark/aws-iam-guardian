import React, { useState } from 'react';
import { 
  Card, 
  Typography, 
  Table, 
  Tag, 
  Button, 
  Space, 
  Select, 
  Alert,
  Row,
  Col,
  Statistic,
  Modal,
  Descriptions,
  Tabs
} from 'antd';
import {
  AuditOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  UserOutlined,
  BarChartOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { auditService, userService } from '../services/iamService';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text } = Typography;
const { Option } = Select;

const AuditLogs = () => {
  const [activeTab, setActiveTab] = useState('logs');
  const [selectedLog, setSelectedLog] = useState(null);
  const [logModalVisible, setLogModalVisible] = useState(false);
  const [filters, setFilters] = useState({
    user_id: null,
    action: null,
    result: null,
  });
  const { isAdmin, userRole } = useAuth();
  
  // 전체 로그 조회 권한 (관리자, 감사자만)
  const canViewAllLogs = isAdmin || userRole === 'auditor';

  // 감사 로그 목록 조회 (관리자, 감사자용)
  const { 
    data: auditLogsData, 
    isLoading: logsLoading, 
    error: logsError,
    refetch: refetchLogs 
  } = useQuery({
    queryKey: ['audit-logs', filters],
    queryFn: () => auditService.getAuditLogs({ 
      ...filters,
      limit: 1000 
    }),
    enabled: canViewAllLogs,
    staleTime: 30 * 1000,
  });

  // 내 활동 로그 조회
  const { 
    data: myLogsData, 
    isLoading: myLogsLoading, 
    error: myLogsError,
    refetch: refetchMyLogs 
  } = useQuery({
    queryKey: ['my-audit-logs'],
    queryFn: () => auditService.getMyAuditLogs({ limit: 500 }),
    staleTime: 30 * 1000,
  });

  // 감사 로그 통계 (관리자, 감사자용)
  const { 
    data: statsData, 
    isLoading: statsLoading 
  } = useQuery({
    queryKey: ['audit-stats'],
    queryFn: () => auditService.getAuditStats(),
    enabled: canViewAllLogs,
    staleTime: 60 * 1000,
  });

  // 내 활동 통계
  const { 
    data: myStatsData, 
    isLoading: myStatsLoading 
  } = useQuery({
    queryKey: ['my-audit-stats'],
    queryFn: () => auditService.getMyAuditStats(),
    staleTime: 60 * 1000,
  });

  // 사용자 목록 조회 (필터용)
  const { data: usersData } = useQuery({
    queryKey: ['users-for-filter'],
    queryFn: () => userService.getUsers({ limit: 1000 }),
    enabled: canViewAllLogs,
    staleTime: 5 * 60 * 1000,
  });

  // 사용 가능한 액션 목록
  const { data: actionsData } = useQuery({
    queryKey: ['audit-actions'],
    queryFn: () => auditService.getAvailableActions(),
    enabled: canViewAllLogs,
    staleTime: 10 * 60 * 1000,
  });

  const auditLogs = auditLogsData?.data || [];
  const myLogs = myLogsData?.data || [];
  const stats = statsData?.data || {};
  const myStats = myStatsData?.data || {};
  const users = usersData?.data || [];
  const actions = actionsData?.data?.actions || [];

  // 로그 상세 정보 모달
  const showLogDetails = (log) => {
    setSelectedLog(log);
    setLogModalVisible(true);
  };

  // 결과 상태 색상
  const getResultColor = (result) => {
    switch (result) {
      case 'success': return 'green';
      case 'failure': return 'orange';
      case 'error': return 'red';
      default: return 'default';
    }
  };

  // 결과 상태 텍스트
  const getResultText = (result) => {
    switch (result) {
      case 'success': return '성공';
      case 'failure': return '실패';
      case 'error': return '오류';
      default: return result;
    }
  };

  // 액션 한글 변환
  const getActionText = (action) => {
    const actionMap = {
      'login': '로그인',
      'logout': '로그아웃',
      'create_user': '사용자 생성',
      'update_user': '사용자 수정',
      'deactivate_user': '사용자 비활성화',
      'create_initial_admin': '초기 관리자 생성',
      'change_password': '비밀번호 변경',
      'view_users': '사용자 조회',
      'view_audit_logs': '감사 로그 조회',
      'iam_users_query': 'IAM 사용자 조회',
      'iam_roles_query': 'IAM 역할 조회',
      'iam_policies_query': 'IAM 정책 조회',
      'security_analysis': '보안 분석',
      'system_settings_change': '시스템 설정 변경'
    };
    return actionMap[action] || action;
  };

  // 사용자명 조회
  const getUserName = (userId) => {
    if (!userId) return '시스템';
    const user = users.find(u => u.id === userId);
    return user ? user.username : `사용자 ${userId}`;
  };

  // 테이블 컬럼 정의 (관리자용)
  const adminColumns = [
    {
      title: '시간',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date) => new Date(date).toLocaleString(),
      sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
    },
    {
      title: '사용자',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 120,
      render: (userId) => (
        <Space>
          <UserOutlined />
          {getUserName(userId)}
        </Space>
      ),
    },
    {
      title: '액션',
      dataIndex: 'action',
      key: 'action',
      width: 150,
      render: (action) => (
        <Tag color="blue">{getActionText(action)}</Tag>
      ),
    },
    {
      title: '리소스',
      dataIndex: 'resource',
      key: 'resource',
      width: 120,
      render: (resource) => resource || <Text type="secondary">-</Text>,
    },
    {
      title: '결과',
      dataIndex: 'result',
      key: 'result',
      width: 80,
      align: 'center',
      render: (result) => (
        <Tag color={getResultColor(result)}>
          {getResultText(result)}
        </Tag>
      ),
    },
    {
      title: 'IP 주소',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 120,
      render: (ip) => ip || <Text type="secondary">-</Text>,
    },
    {
      title: '작업',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Button 
          type="primary" 
          size="small"
          icon={<EyeOutlined />}
          onClick={() => showLogDetails(record)}
        >
          상세
        </Button>
      ),
    },
  ];

  // 테이블 컬럼 정의 (개인용)
  const userColumns = [
    {
      title: '시간',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date) => new Date(date).toLocaleString(),
      sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
    },
    {
      title: '액션',
      dataIndex: 'action',
      key: 'action',
      width: 150,
      render: (action) => (
        <Tag color="blue">{getActionText(action)}</Tag>
      ),
    },
    {
      title: '리소스',
      dataIndex: 'resource',
      key: 'resource',
      width: 120,
      render: (resource) => resource || <Text type="secondary">-</Text>,
    },
    {
      title: '결과',
      dataIndex: 'result',
      key: 'result',
      width: 80,
      align: 'center',
      render: (result) => (
        <Tag color={getResultColor(result)}>
          {getResultText(result)}
        </Tag>
      ),
    },
    {
      title: 'IP 주소',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 120,
      render: (ip) => ip || <Text type="secondary">-</Text>,
    },
    {
      title: '작업',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Button 
          type="primary" 
          size="small"
          icon={<EyeOutlined />}
          onClick={() => showLogDetails(record)}
        >
          상세
        </Button>
      ),
    },
  ];

  // 관리자 로그 탭
  const AdminLogsTab = () => (
    <div>
      {/* 필터 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col xs={24} sm={8}>
            <Select
              placeholder="사용자 선택"
              allowClear
              style={{ width: '100%' }}
              value={filters.user_id}
              onChange={(value) => setFilters({ ...filters, user_id: value })}
            >
              {users.map(user => (
                <Option key={user.id} value={user.id}>
                  {user.username}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={8}>
            <Select
              placeholder="액션 선택"
              allowClear
              style={{ width: '100%' }}
              value={filters.action}
              onChange={(value) => setFilters({ ...filters, action: value })}
            >
              {actions.map(action => (
                <Option key={action} value={action}>
                  {getActionText(action)}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={8}>
            <Select
              placeholder="결과 선택"
              allowClear
              style={{ width: '100%' }}
              value={filters.result}
              onChange={(value) => setFilters({ ...filters, result: value })}
            >
              <Option value="success">성공</Option>
              <Option value="failure">실패</Option>
              <Option value="error">오류</Option>
            </Select>
          </Col>
        </Row>
      </Card>

      {/* 에러 표시 */}
      {logsError && (
        <Alert
          message="감사 로그 조회 실패"
          description={logsError.response?.data?.detail || logsError.message}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 로그 테이블 */}
      <Card>
        <Table
          columns={adminColumns}
          dataSource={auditLogs}
          rowKey="id"
          loading={logsLoading}
          pagination={{
            total: auditLogs.length,
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} / 총 ${total}개`,
          }}
          scroll={{ x: 1000 }}
        />
      </Card>
    </div>
  );

  // 개인 로그 탭
  const MyLogsTab = () => (
    <div>
      {/* 에러 표시 */}
      {myLogsError && (
        <Alert
          message="활동 로그 조회 실패"
          description={myLogsError.response?.data?.detail || myLogsError.message}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 로그 테이블 */}
      <Card>
        <Table
          columns={userColumns}
          dataSource={myLogs}
          rowKey="id"
          loading={myLogsLoading}
          pagination={{
            total: myLogs.length,
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} / 총 ${total}개`,
          }}
          scroll={{ x: 800 }}
        />
      </Card>
    </div>
  );

  // 통계 탭
  const StatsTab = () => {
    const currentStats = canViewAllLogs ? stats : myStats;
    const loading = canViewAllLogs ? statsLoading : myStatsLoading;

    return (
      <div>
        {/* 통계 카드 */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={6}>
            <Card loading={loading}>
              <Statistic
                title="전체 활동"
                value={currentStats.total_count || 0}
                prefix={<AuditOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card loading={loading}>
              <Statistic
                title="성공"
                value={currentStats.success_count || 0}
                prefix={<AuditOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card loading={loading}>
              <Statistic
                title="실패"
                value={currentStats.failure_count || 0}
                prefix={<AuditOutlined />}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card loading={loading}>
              <Statistic
                title="오류"
                value={currentStats.error_count || 0}
                prefix={<AuditOutlined />}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 액션별 통계 */}
        <Card title="액션별 활동 통계" loading={loading}>
          <Table
            dataSource={currentStats.action_stats || []}
            columns={[
              {
                title: '액션',
                dataIndex: 'action',
                key: 'action',
                render: (action) => (
                  <Tag color="blue">{getActionText(action)}</Tag>
                ),
              },
              {
                title: '횟수',
                dataIndex: 'count',
                key: 'count',
                align: 'right',
                render: (count) => (
                  <Text strong>{count.toLocaleString()}</Text>
                ),
              },
            ]}
            pagination={false}
            size="small"
          />
        </Card>
      </div>
    );
  };

  const tabItems = [
    ...(canViewAllLogs ? [{
      key: 'logs',
      label: (
        <span>
          <AuditOutlined />
          전체 로그
        </span>
      ),
      children: <AdminLogsTab />,
    }] : []),
    {
      key: 'my-logs',
      label: (
        <span>
          <UserOutlined />
          내 활동
        </span>
      ),
      children: <MyLogsTab />,
    },
    {
      key: 'stats',
      label: (
        <span>
          <BarChartOutlined />
          통계
        </span>
      ),
      children: <StatsTab />,
    },
  ];

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2}>
            <AuditOutlined /> 감사 로그
          </Title>
        </Col>
        <Col>
          <Space>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => {
                if (canViewAllLogs) refetchLogs();
                refetchMyLogs();
              }}
              loading={logsLoading || myLogsLoading}
            >
              새로고침
            </Button>
          </Space>
        </Col>
      </Row>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        size="large"
      />

      {/* 로그 상세 정보 모달 */}
      <Modal
        title={
          <Space>
            <InfoCircleOutlined />
            로그 상세 정보
          </Space>
        }
        open={logModalVisible}
        onCancel={() => setLogModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setLogModalVisible(false)}>
            닫기
          </Button>
        ]}
        width={700}
      >
        {selectedLog && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="ID">
              <Text code>{selectedLog.id}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="사용자">
              {getUserName(selectedLog.user_id)}
            </Descriptions.Item>
            <Descriptions.Item label="액션">
              <Tag color="blue">{getActionText(selectedLog.action)}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="결과">
              <Tag color={getResultColor(selectedLog.result)}>
                {getResultText(selectedLog.result)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="리소스">
              {selectedLog.resource || '없음'}
            </Descriptions.Item>
            <Descriptions.Item label="IP 주소">
              {selectedLog.ip_address || '없음'}
            </Descriptions.Item>
            <Descriptions.Item label="시간" span={2}>
              {new Date(selectedLog.created_at).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="User Agent" span={2}>
              <Text style={{ fontSize: '12px', wordBreak: 'break-all' }}>
                {selectedLog.user_agent || '없음'}
              </Text>
            </Descriptions.Item>
            <Descriptions.Item label="상세 정보" span={2}>
              <Text style={{ fontSize: '12px', wordBreak: 'break-all' }}>
                {selectedLog.details || '없음'}
              </Text>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default AuditLogs;