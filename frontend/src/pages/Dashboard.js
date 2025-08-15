import React, { useState } from 'react';
import { 
  Row, 
  Col, 
  Card, 
  Statistic, 
  Table, 
  Tag, 
  Alert, 
  Spin, 
  Typography,
  Select,
  Space,
  Button
} from 'antd';
import {
  UserOutlined,
  TeamOutlined,
  SafetyOutlined,
  WarningOutlined,
  ReloadOutlined,
  CloudServerOutlined
} from '@ant-design/icons';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { useQuery } from '@tanstack/react-query';
import iamService from '../services/iamService';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text } = Typography;
const { Option } = Select;

const Dashboard = () => {
  const [selectedAccount, setSelectedAccount] = useState('main');
  const { isAdmin, userRole } = useAuth();
  
  // 보안 분석 권한 확인 (관리자, 분석가, 감사자만 가능)
  const canViewSecurity = isAdmin || userRole === 'analyst' || userRole === 'auditor';

  // 계정 목록 조회
  const { data: accounts } = useQuery('accounts', iamService.getAccounts);

  // 계정 요약 정보 조회
  const { 
    data: accountSummary, 
    isLoading: summaryLoading, 
    refetch: refetchSummary 
  } = useQuery(
    ['accountSummary', selectedAccount],
    () => iamService.getAccountSummary(selectedAccount),
    { enabled: !!selectedAccount }
  );

  // 고위험 사용자 조회 (권한이 있는 사용자만)
  const { 
    data: highRiskUsers, 
    isLoading: riskLoading 
  } = useQuery(
    ['highRiskUsers', selectedAccount],
    () => iamService.getHighRiskUsers(selectedAccount, 30),
    { enabled: !!selectedAccount && canViewSecurity }
  );

  // IAM 사용자 조회 (통계용)
  const { data: iamUsers } = useQuery(
    ['iamUsers', selectedAccount],
    () => iamService.getIAMUsers(selectedAccount, { limit: 1000 }),
    { enabled: !!selectedAccount }
  );

  // 차트 데이터 준비
  const riskDistributionData = React.useMemo(() => {
    if (!highRiskUsers?.data?.users) return [];
    
    const riskCounts = { HIGH: 0, MEDIUM: 0, LOW: 0 };
    highRiskUsers.data.users.forEach(user => {
      riskCounts[user.risk_level] = (riskCounts[user.risk_level] || 0) + 1;
    });

    return [
      { name: '고위험', value: riskCounts.HIGH, color: '#ff4d4f' },
      { name: '중위험', value: riskCounts.MEDIUM, color: '#faad14' },
      { name: '저위험', value: riskCounts.LOW, color: '#52c41a' },
    ];
  }, [highRiskUsers]);

  const policyDistributionData = React.useMemo(() => {
    if (!iamUsers?.data?.users) return [];
    
    const policyStats = {};
    iamUsers.data.users.forEach(user => {
      const policyCount = (user.attached_policies?.length || 0) + (user.inline_policies?.length || 0);
      const range = policyCount === 0 ? '0개' : 
                   policyCount <= 5 ? '1-5개' : 
                   policyCount <= 10 ? '6-10개' : '10개 이상';
      policyStats[range] = (policyStats[range] || 0) + 1;
    });

    return Object.entries(policyStats).map(([range, count]) => ({
      name: range,
      value: count
    }));
  }, [iamUsers]);

  const riskTableColumns = [
    {
      title: '사용자명',
      dataIndex: 'user_name',
      key: 'user_name',
      render: (text) => (
        <Space>
          <UserOutlined />
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: '위험도',
      dataIndex: 'risk_level',
      key: 'risk_level',
      render: (level, record) => (
        <Tag 
          color={level === 'HIGH' ? 'red' : level === 'MEDIUM' ? 'orange' : 'green'}
          className={`risk-${level.toLowerCase()}`}
        >
          {level === 'HIGH' ? '고위험' : level === 'MEDIUM' ? '중위험' : '저위험'} ({record.risk_score}점)
        </Tag>
      ),
    },
    {
      title: '위험 요소',
      dataIndex: 'risk_factors',
      key: 'risk_factors',
      render: (factors) => (
        <div>
          {factors?.slice(0, 2).map((factor, index) => (
            <Tag key={index} style={{ marginBottom: 4 }}>
              {factor}
            </Tag>
          ))}
          {factors?.length > 2 && (
            <Text type="secondary">+{factors.length - 2}개 더</Text>
          )}
        </div>
      ),
    },
    {
      title: '생성일',
      dataIndex: 'create_date',
      key: 'create_date',
      render: (date) => date ? new Date(date).toLocaleDateString('ko-KR') : '-',
    },
  ];

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Title level={2}>대시보드</Title>
        </Col>
        <Col span={12} style={{ textAlign: 'right' }}>
          <Space>
            <Select
              value={selectedAccount}
              onChange={setSelectedAccount}
              style={{ width: 200 }}
              placeholder="AWS 계정 선택"
            >
              {accounts?.data?.accounts?.map(account => (
                <Option key={account.account_key} value={account.account_key}>
                  <Space>
                    <CloudServerOutlined />
                    {account.account_name}
                  </Space>
                </Option>
              ))}
            </Select>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => refetchSummary()}
              loading={summaryLoading}
            >
              새로고침
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 통계 카드 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="총 IAM 사용자"
              value={accountSummary?.data?.summary?.Users || 0}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="IAM 역할"
              value={accountSummary?.data?.summary?.Roles || 0}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="관리형 정책"
              value={accountSummary?.data?.summary?.Policies || 0}
              prefix={<SafetyOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        {canViewSecurity && (
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="고위험 사용자"
                value={highRiskUsers?.data?.total_high_risk_users || 0}
                prefix={<WarningOutlined />}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
        )}
      </Row>

      {/* 알림 */}
      {canViewSecurity && highRiskUsers?.data?.total_high_risk_users > 0 && (
        <Alert
          message="보안 주의"
          description={`${highRiskUsers.data.total_high_risk_users}명의 고위험 사용자가 발견되었습니다. 권한을 검토해주세요.`}
          type="warning"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      {/* 차트 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="위험도 분포" className="dashboard-card">
            {riskLoading ? (
              <div className="loading-container">
                <Spin size="large" />
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={riskDistributionData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {riskDistributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="정책 보유 현황" className="dashboard-card">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={policyDistributionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#1890ff" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* 고위험 사용자 테이블 */}
      {canViewSecurity && (
        <Card title="고위험 사용자 목록" className="dashboard-card">
          <Table
            columns={riskTableColumns}
            dataSource={highRiskUsers?.data?.users || []}
            rowKey="user_name"
            loading={riskLoading}
            pagination={{ pageSize: 10 }}
            scroll={{ x: 800 }}
          />
        </Card>
      )}
    </div>
  );
};

export default Dashboard;