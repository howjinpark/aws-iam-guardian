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
  Input
} from 'antd';
import {
  FileTextOutlined,
  ReloadOutlined,
  SearchOutlined,
  InfoCircleOutlined,
  CloudServerOutlined,
  SafetyOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import iamService from '../services/iamService';

const { Title, Text } = Typography;
const { Option } = Select;
const { Search } = Input;

const IAMPolicies = () => {
  const [selectedAccount, setSelectedAccount] = useState('main');
  const [selectedScope, setSelectedScope] = useState('Local');
  const [searchText, setSearchText] = useState('');
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [policyModalVisible, setPolicyModalVisible] = useState(false);

  // 계정 목록 조회
  const { data: accountsData } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => iamService.getAccounts(),
    staleTime: 5 * 60 * 1000,
  });

  // IAM 정책 목록 조회
  const { 
    data: policiesData, 
    isLoading: policiesLoading, 
    error: policiesError,
    refetch: refetchPolicies 
  } = useQuery({
    queryKey: ['iam-policies', selectedAccount, selectedScope],
    queryFn: () => iamService.getIAMPolicies(selectedAccount, { 
      scope: selectedScope,
      limit: 1000 
    }),
    enabled: !!selectedAccount,
    staleTime: 2 * 60 * 1000,
  });

  const policies = policiesData?.data?.policies || [];
  const totalCount = policiesData?.data?.total_count || 0;

  // 검색 필터링
  const filteredPolicies = policies.filter(policy => 
    policy.policy_name.toLowerCase().includes(searchText.toLowerCase()) ||
    (policy.description && policy.description.toLowerCase().includes(searchText.toLowerCase()))
  );

  // 정책 상세 정보 모달
  const showPolicyDetails = (policy) => {
    setSelectedPolicy(policy);
    setPolicyModalVisible(true);
  };

  // 정책 유형별 색상
  const getPolicyTypeColor = (arn) => {
    if (arn.includes('aws:iam::aws:policy/')) {
      return 'blue'; // AWS 관리형
    }
    return 'green'; // 고객 관리형
  };

  // 정책 유형 텍스트
  const getPolicyTypeText = (arn) => {
    if (arn.includes('aws:iam::aws:policy/')) {
      return 'AWS 관리형';
    }
    return '고객 관리형';
  };

  // 테이블 컬럼 정의
  const columns = [
    {
      title: '정책 이름',
      dataIndex: 'policy_name',
      key: 'policy_name',
      width: 250,
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <Button 
            type="link" 
            onClick={() => showPolicyDetails(record)}
            style={{ padding: 0, height: 'auto' }}
          >
            <FileTextOutlined /> {text}
          </Button>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.path}
          </Text>
        </Space>
      ),
    },
    {
      title: '유형',
      dataIndex: 'arn',
      key: 'type',
      width: 120,
      render: (arn) => (
        <Tag color={getPolicyTypeColor(arn)}>
          {getPolicyTypeText(arn)}
        </Tag>
      ),
    },
    {
      title: '설명',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text) => text || <Text type="secondary">설명 없음</Text>,
    },
    {
      title: '연결 수',
      dataIndex: 'attachment_count',
      key: 'attachment_count',
      width: 100,
      align: 'center',
      render: (count) => (
        <Tag color={count > 0 ? 'orange' : 'default'}>
          {count}
        </Tag>
      ),
    },
    {
      title: '연결 가능',
      dataIndex: 'is_attachable',
      key: 'is_attachable',
      width: 100,
      align: 'center',
      render: (attachable) => (
        <Tag color={attachable ? 'green' : 'red'}>
          {attachable ? '가능' : '불가능'}
        </Tag>
      ),
    },
    {
      title: '생성일',
      dataIndex: 'create_date',
      key: 'create_date',
      width: 120,
      render: (date) => date ? new Date(date).toLocaleDateString() : '-',
    },
    {
      title: '작업',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Button 
          type="primary" 
          size="small"
          icon={<InfoCircleOutlined />}
          onClick={() => showPolicyDetails(record)}
        >
          상세
        </Button>
      ),
    },
  ];

  // 통계 데이터
  const stats = {
    total: totalCount,
    customer: policies.filter(p => !p.arn.includes('aws:iam::aws:policy/')).length,
    aws: policies.filter(p => p.arn.includes('aws:iam::aws:policy/')).length,
    attached: policies.filter(p => p.attachment_count > 0).length,
  };

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2}>
            <FileTextOutlined /> IAM 정책
          </Title>
        </Col>
        <Col>
          <Space>
            <Select
              value={selectedAccount}
              onChange={setSelectedAccount}
              style={{ width: 150 }}
              placeholder="계정 선택"
            >
              {accountsData?.data?.accounts?.map(account => (
                <Option key={account.account_key} value={account.account_key}>
                  {account.account_name || account.account_key}
                </Option>
              ))}
            </Select>
            <Select
              value={selectedScope}
              onChange={setSelectedScope}
              style={{ width: 150 }}
            >
              <Option value="Local">고객 관리형</Option>
              <Option value="AWS">AWS 관리형</Option>
              <Option value="All">전체</Option>
            </Select>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => refetchPolicies()}
              loading={policiesLoading}
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
              title="전체 정책"
              value={stats.total}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="고객 관리형"
              value={stats.customer}
              prefix={<CloudServerOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="AWS 관리형"
              value={stats.aws}
              prefix={<SafetyOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="연결된 정책"
              value={stats.attached}
              prefix={<InfoCircleOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 검색 */}
      <Card style={{ marginBottom: 16 }}>
        <Search
          placeholder="정책 이름 또는 설명으로 검색"
          allowClear
          enterButton={<SearchOutlined />}
          size="large"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ maxWidth: 400 }}
        />
      </Card>

      {/* 에러 표시 */}
      {policiesError && (
        <Alert
          message="정책 목록 조회 실패"
          description={policiesError.response?.data?.detail || policiesError.message}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 정책 목록 테이블 */}
      <Card>
        <Table
          columns={columns}
          dataSource={filteredPolicies}
          rowKey="policy_id"
          loading={policiesLoading}
          pagination={{
            total: filteredPolicies.length,
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} / 총 ${total}개`,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 정책 상세 정보 모달 */}
      <Modal
        title={
          <Space>
            <FileTextOutlined />
            정책 상세 정보
          </Space>
        }
        open={policyModalVisible}
        onCancel={() => setPolicyModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setPolicyModalVisible(false)}>
            닫기
          </Button>
        ]}
        width={800}
      >
        {selectedPolicy && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="정책 이름" span={2}>
              <Text strong>{selectedPolicy.policy_name}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="정책 ID">
              <Text code>{selectedPolicy.policy_id}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="ARN">
              <Text code style={{ fontSize: '12px' }}>
                {selectedPolicy.arn}
              </Text>
            </Descriptions.Item>
            <Descriptions.Item label="경로">
              {selectedPolicy.path}
            </Descriptions.Item>
            <Descriptions.Item label="유형">
              <Tag color={getPolicyTypeColor(selectedPolicy.arn)}>
                {getPolicyTypeText(selectedPolicy.arn)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="연결 수">
              <Tag color={selectedPolicy.attachment_count > 0 ? 'orange' : 'default'}>
                {selectedPolicy.attachment_count}개
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="연결 가능">
              <Tag color={selectedPolicy.is_attachable ? 'green' : 'red'}>
                {selectedPolicy.is_attachable ? '가능' : '불가능'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="기본 버전">
              {selectedPolicy.default_version_id || 'v1'}
            </Descriptions.Item>
            <Descriptions.Item label="생성일">
              {selectedPolicy.create_date ? 
                new Date(selectedPolicy.create_date).toLocaleString() : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="수정일">
              {selectedPolicy.update_date ? 
                new Date(selectedPolicy.update_date).toLocaleString() : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="설명" span={2}>
              {selectedPolicy.description || '설명이 없습니다.'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default IAMPolicies;