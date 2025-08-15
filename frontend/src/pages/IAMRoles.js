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
  KeyOutlined,
  SearchOutlined,
  EyeOutlined,
  ReloadOutlined,
  CloudServerOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import iamService from '../services/iamService';

const { Title, Text } = Typography;
const { Option } = Select;

const IAMRoles = () => {
  const [selectedAccount, setSelectedAccount] = useState('main');
  const [searchText, setSearchText] = useState('');
  const [selectedRole, setSelectedRole] = useState(null);
  const [roleDetailVisible, setRoleDetailVisible] = useState(false);

  // 계정 목록 조회
  const { data: accounts } = useQuery('accounts', iamService.getAccounts);

  // IAM 역할 목록 조회
  const { 
    data: iamRoles, 
    isLoading, 
    refetch,
    error 
  } = useQuery(
    ['iamRoles', selectedAccount],
    () => iamService.getIAMRoles(selectedAccount, { limit: 1000 }),
    { enabled: !!selectedAccount }
  );

  const showRoleDetail = (role) => {
    setSelectedRole(role);
    setRoleDetailVisible(true);
  };

  const columns = [
    {
      title: '역할명',
      dataIndex: 'role_name',
      key: 'role_name',
      render: (text) => (
        <Space>
          <KeyOutlined />
          <Text strong>{text}</Text>
        </Space>
      ),
      filteredValue: searchText ? [searchText] : null,
      onFilter: (value, record) => 
        record.role_name.toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: '설명',
      dataIndex: 'description',
      key: 'description',
      render: (desc) => desc || '-',
      ellipsis: true,
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
      title: '최대 세션 시간',
      dataIndex: 'max_session_duration',
      key: 'max_session_duration',
      render: (duration) => `${Math.floor(duration / 3600)}시간`,
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
          <Button 
            type="primary" 
            size="small" 
            icon={<EyeOutlined />}
            onClick={() => showRoleDetail(record)}
          >
            상세보기
          </Button>
        </Space>
      ),
    },
  ];

  const filteredRoles = iamRoles?.data?.roles?.filter(role =>
    role.role_name.toLowerCase().includes(searchText.toLowerCase())
  ) || [];

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Title level={2}>IAM 역할</Title>
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
            placeholder="역할명 검색"
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
          />
          <Text type="secondary">
            총 {filteredRoles.length}개의 역할
          </Text>
        </Space>

        <Table
          columns={columns}
          dataSource={filteredRoles}
          rowKey="role_name"
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

      {/* 역할 상세 정보 모달 */}
      <Modal
        title={`역할 상세: ${selectedRole?.role_name}`}
        open={roleDetailVisible}
        onCancel={() => setRoleDetailVisible(false)}
        footer={null}
        width={800}
      >
        {selectedRole && (
          <div>
            <Descriptions title="기본 정보" bordered size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="역할 ID">{selectedRole.role_id}</Descriptions.Item>
              <Descriptions.Item label="ARN">{selectedRole.arn}</Descriptions.Item>
              <Descriptions.Item label="경로">{selectedRole.path}</Descriptions.Item>
              <Descriptions.Item label="설명" span={3}>{selectedRole.description || '설명 없음'}</Descriptions.Item>
              <Descriptions.Item label="최대 세션 시간">{Math.floor(selectedRole.max_session_duration / 3600)}시간</Descriptions.Item>
              <Descriptions.Item label="생성일">{selectedRole.create_date}</Descriptions.Item>
            </Descriptions>

            {/* 연결된 정책 */}
            {selectedRole.attached_policies?.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <Title level={5}>연결된 정책</Title>
                {selectedRole.attached_policies.map((policy, index) => (
                  <Tag key={index} color="blue" style={{ marginBottom: 4, marginRight: 8 }}>
                    {policy.split('/').pop()}
                  </Tag>
                ))}
              </div>
            )}

            {/* 인라인 정책 */}
            {selectedRole.inline_policies?.length > 0 && (
              <div>
                <Title level={5}>인라인 정책</Title>
                {selectedRole.inline_policies.map((policy, index) => (
                  <Tag key={index} color="orange" style={{ marginBottom: 4, marginRight: 8 }}>
                    {policy}
                  </Tag>
                ))}
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default IAMRoles;