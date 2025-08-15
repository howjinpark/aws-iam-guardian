import React, { useState } from 'react';
import { 
  Card, 
  Typography, 
  Table, 
  Tag, 
  Button, 
  Space, 
  Select, 
  Input, 
  Modal,
  Descriptions,
  Alert,
  Row,
  Col
} from 'antd';
import {
  UserOutlined,
  SearchOutlined,
  EyeOutlined,
  WarningOutlined,
  ReloadOutlined,
  CloudServerOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import iamService from '../services/iamService';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text } = Typography;
const { Option } = Select;

const IAMUsers = () => {
  const [selectedAccount, setSelectedAccount] = useState('main');
  const [searchText, setSearchText] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [userDetailVisible, setUserDetailVisible] = useState(false);
  const { isAdmin, userRole } = useAuth();
  
  // 분석 권한 확인 (관리자, 분석가, 감사자만 가능)
  const canAnalyze = isAdmin || userRole === 'analyst' || userRole === 'auditor';

  // 계정 목록 조회
  const { data: accounts } = useQuery('accounts', iamService.getAccounts);

  // IAM 사용자 목록 조회
  const { 
    data: iamUsers, 
    isLoading, 
    refetch,
    error 
  } = useQuery(
    ['iamUsers', selectedAccount],
    () => iamService.getIAMUsers(selectedAccount, { limit: 1000 }),
    { enabled: !!selectedAccount }
  );

  // 사용자 권한 분석
  const analyzeUser = async (userName) => {
    try {
      const analysis = await iamService.analyzeUserPermissions(selectedAccount, userName);
      setSelectedUser(analysis.data);
      setUserDetailVisible(true);
    } catch (error) {
      console.error('사용자 분석 실패:', error);
    }
  };

  const columns = [
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
      filteredValue: searchText ? [searchText] : null,
      onFilter: (value, record) => 
        record.user_name.toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: '이메일',
      dataIndex: 'email',
      key: 'email',
      render: (email) => email || '-',
    },
    {
      title: '연결된 정책',
      dataIndex: 'attached_policies',
      key: 'attached_policies',
      render: (policies) => (
        <div>
          {policies?.slice(0, 2).map((policy, index) => (
            <Tag key={index} color="blue" style={{ marginBottom: 4 }}>
              {policy.split('/').pop()}
            </Tag>
          ))}
          {policies?.length > 2 && (
            <Text type="secondary">+{policies.length - 2}개 더</Text>
          )}
        </div>
      ),
    },
    {
      title: '그룹',
      dataIndex: 'groups',
      key: 'groups',
      render: (groups) => (
        <div>
          {groups?.slice(0, 2).map((group, index) => (
            <Tag key={index} color="green">
              {group}
            </Tag>
          ))}
          {groups?.length > 2 && (
            <Text type="secondary">+{groups.length - 2}개 더</Text>
          )}
        </div>
      ),
    },
    {
      title: '액세스 키',
      dataIndex: 'access_keys',
      key: 'access_keys',
      render: (keys) => (
        <Space>
          <Text>{keys?.length || 0}개</Text>
          {keys?.some(key => key.status === 'Active') && (
            <Tag color="green">활성</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '생성일',
      dataIndex: 'create_date',
      key: 'create_date',
      render: (date) => date ? new Date(date).toLocaleDateString('ko-KR') : '-',
    },
    {
      title: '작업',
      key: 'actions',
      render: (_, record) => (
        <Space>
          {canAnalyze ? (
            <Button 
              type="primary" 
              size="small" 
              icon={<EyeOutlined />}
              onClick={() => analyzeUser(record.user_name)}
            >
              분석
            </Button>
          ) : (
            <Button 
              size="small" 
              disabled
              icon={<EyeOutlined />}
              title="분석 권한이 없습니다 (분석가/관리자 권한 필요)"
            >
              분석
            </Button>
          )}
        </Space>
      ),
    },
  ];

  const filteredUsers = iamUsers?.data?.users?.filter(user =>
    user.user_name.toLowerCase().includes(searchText.toLowerCase())
  ) || [];

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Title level={2}>IAM 사용자</Title>
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
              onClick={() => refetch()}
              loading={isLoading}
            >
              새로고침
            </Button>
          </Space>
        </Col>
      </Row>

      {error && (
        <Alert
          message="데이터 로드 실패"
          description={error.message}
          type="error"
          style={{ marginBottom: 16 }}
        />
      )}

      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Input
            placeholder="사용자명 검색"
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
          />
          <Text type="secondary">
            총 {filteredUsers.length}명의 사용자
          </Text>
        </Space>

        <Table
          columns={columns}
          dataSource={filteredUsers}
          rowKey="user_name"
          loading={isLoading}
          pagination={{ 
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `총 ${total}개 항목`
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 사용자 상세 분석 모달 */}
      <Modal
        title={`사용자 분석: ${selectedUser?.user_info?.user_name}`}
        open={userDetailVisible}
        onCancel={() => setUserDetailVisible(false)}
        footer={null}
        width={800}
      >
        {selectedUser && (
          <div>
            {/* 위험도 평가 */}
            <Alert
              message={`위험도: ${selectedUser.risk_assessment?.risk_level}`}
              description={`점수: ${selectedUser.risk_assessment?.risk_score}/100`}
              type={selectedUser.risk_assessment?.risk_level === 'HIGH' ? 'error' : 
                    selectedUser.risk_assessment?.risk_level === 'MEDIUM' ? 'warning' : 'success'}
              style={{ marginBottom: 16 }}
            />

            {/* 기본 정보 */}
            <Descriptions title="기본 정보" bordered size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="사용자 ID">{selectedUser.user_info?.user_id}</Descriptions.Item>
              <Descriptions.Item label="ARN">{selectedUser.user_info?.arn}</Descriptions.Item>
              <Descriptions.Item label="생성일">{selectedUser.user_info?.create_date}</Descriptions.Item>
            </Descriptions>

            {/* 위험 요소 */}
            {selectedUser.risk_assessment?.risk_factors?.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <Title level={5}>위험 요소</Title>
                {selectedUser.risk_assessment.risk_factors.map((factor, index) => (
                  <Tag key={index} color="red" style={{ marginBottom: 4 }}>
                    <WarningOutlined /> {factor}
                  </Tag>
                ))}
              </div>
            )}

            {/* 추천사항 */}
            {selectedUser.recommendations?.length > 0 && (
              <div>
                <Title level={5}>추천사항</Title>
                <ul>
                  {selectedUser.recommendations.map((rec, index) => (
                    <li key={index}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default IAMUsers;