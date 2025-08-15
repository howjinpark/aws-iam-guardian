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
  Tabs,
  Spin
} from 'antd';
import {
  WarningOutlined,
  UserOutlined,
  SafetyOutlined,
  ReloadOutlined,
  CloudServerOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import iamService from '../services/iamService';
import { useAuth } from '../contexts/AuthContext';
import RoleGuard from '../components/RoleGuard';

const { Title, Text } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

const Analysis = () => {
  const [selectedAccount, setSelectedAccount] = useState('main');
  const [minRiskScore, setMinRiskScore] = useState(30);
  const { isAdmin, userRole } = useAuth();
  
  // 보안 분석 권한 확인
  const canViewSecurity = isAdmin || userRole === 'analyst' || userRole === 'auditor';

  // 계정 목록 조회 (항상 호출)
  const { data: accounts } = useQuery('accounts', iamService.getAccounts);

  // 고위험 사용자 조회 (권한 기반으로 활성화)
  const { 
    data: highRiskUsers, 
    isLoading: riskLoading,
    refetch: refetchRisk
  } = useQuery(
    ['highRiskUsers', selectedAccount, minRiskScore],
    () => iamService.getHighRiskUsers(selectedAccount, minRiskScore),
    { enabled: !!selectedAccount && canViewSecurity }
  );

  // IAM 사용자 전체 조회 (통계용, 권한 기반으로 활성화)
  const { data: allUsers } = useQuery(
    ['allIamUsers', selectedAccount],
    () => iamService.getIAMUsers(selectedAccount, { limit: 1000 }),
    { enabled: !!selectedAccount && canViewSecurity }
  );

  // 위험도 분포 차트 데이터 (항상 호출)
  const riskDistributionData = React.useMemo(() => {
    if (!canViewSecurity || !highRiskUsers?.data?.users) return [];
    
    const riskCounts = { HIGH: 0, MEDIUM: 0, LOW: 0 };
    highRiskUsers.data.users.forEach(user => {
      riskCounts[user.risk_level] = (riskCounts[user.risk_level] || 0) + 1;
    });

    return [
      { name: '고위험', value: riskCounts.HIGH, color: '#ff4d4f' },
      { name: '중위험', value: riskCounts.MEDIUM, color: '#faad14' },
      { name: '저위험', value: riskCounts.LOW, color: '#52c41a' },
    ].filter(item => item.value > 0);
  }, [highRiskUsers, canViewSecurity]);

  // 위험 요소 통계 (항상 호출)
  const riskFactorStats = React.useMemo(() => {
    if (!canViewSecurity || !highRiskUsers?.data?.users) return [];
    
    const factorCounts = {};
    highRiskUsers.data.users.forEach(user => {
      user.risk_factors?.forEach(factor => {
        factorCounts[factor] = (factorCounts[factor] || 0) + 1;
      });
    });

    return Object.entries(factorCounts)
      .map(([factor, count]) => ({ factor, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  }, [highRiskUsers, canViewSecurity]);

  // 권한이 없는 경우 접근 차단 (모든 Hook 호출 후)
  if (!canViewSecurity) {
    return (
      <RoleGuard 
        allowedRoles={['analyst', 'auditor']} 
        showMessage={true}
      />
    );
  }

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
        <Space>
          <Tag 
            color={level === 'HIGH' ? 'red' : level === 'MEDIUM' ? 'orange' : 'green'}
          >
            {level === 'HIGH' ? '고위험' : level === 'MEDIUM' ? '중위험' : '저위험'}
          </Tag>
          <Text type="secondary">({record.risk_score}점)</Text>
        </Space>
      ),
    },
    {
      title: '주요 위험 요소',
      dataIndex: 'risk_factors',
      key: 'risk_factors',
      render: (factors) => (
        <div>
          {factors?.slice(0, 3).map((factor, index) => (
            <Tag key={index} color="red" style={{ marginBottom: 4 }}>
              <WarningOutlined /> {factor}
            </Tag>
          ))}
          {factors?.length > 3 && (
            <Text type="secondary">+{factors.length - 3}개 더</Text>
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
          <Title level={2}>보안 분석</Title>
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
            <Select
              value={minRiskScore}
              onChange={setMinRiskScore}
              style={{ width: 150 }}
            >
              <Option value={10}>모든 위험도</Option>
              <Option value={30}>중위험 이상</Option>
              <Option value={50}>고위험만</Option>
              <Option value={70}>매우 고위험</Option>
            </Select>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => refetchRisk()}
              loading={riskLoading}
            >
              새로고침
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 통계 카드 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="총 IAM 사용자"
              value={allUsers?.data?.total_count || 0}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="고위험 사용자"
              value={highRiskUsers?.data?.total_high_risk_users || 0}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="보안 점수"
              value={Math.max(0, 100 - (highRiskUsers?.data?.total_high_risk_users || 0) * 10)}
              suffix="/ 100"
              prefix={<SafetyOutlined />}
              valueStyle={{ 
                color: (100 - (highRiskUsers?.data?.total_high_risk_users || 0) * 10) >= 80 ? '#52c41a' : 
                       (100 - (highRiskUsers?.data?.total_high_risk_users || 0) * 10) >= 60 ? '#faad14' : '#ff4d4f'
              }}
            />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="1">
        <TabPane tab="위험도 분석" key="1">
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="위험도 분포" className="dashboard-card">
                {riskLoading ? (
                  <div style={{ textAlign: 'center', padding: '50px' }}>
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
              <Card title="주요 위험 요소" className="dashboard-card">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={riskFactorStats}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="factor" 
                      angle={-45}
                      textAnchor="end"
                      height={100}
                    />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#ff4d4f" />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="고위험 사용자" key="2">
          <Card>
            {highRiskUsers?.data?.total_high_risk_users > 0 && (
              <Alert
                message="보안 주의"
                description={`${highRiskUsers.data.total_high_risk_users}명의 고위험 사용자가 발견되었습니다.`}
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}

            <Table
              columns={riskTableColumns}
              dataSource={highRiskUsers?.data?.users || []}
              rowKey="user_name"
              loading={riskLoading}
              pagination={{ 
                pageSize: 10,
                showTotal: (total) => `총 ${total}명의 고위험 사용자`
              }}
            />
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default Analysis;