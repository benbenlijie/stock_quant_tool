// 股票表格组件

import React, { useState } from 'react';
import {
  Table,
  Tag,
  Space,
  Button,
  Tooltip,
  Typography,
  Row,
  Col,
  Card,
  Progress,
  List,
  Collapse
} from 'antd';
import {
  EyeOutlined,
  CopyOutlined,
  TrophyOutlined,
  RiseOutlined,
  FallOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { CandidateStock } from '../../types';
import {
  formatPercent,
  getChangeColor,
  getChangeText,
  getScoreLevel,
  copyToClipboard,
  formatLargeNumber
} from '../../utils';

const { Text, Title } = Typography;
const { Panel } = Collapse;

interface StockTableProps {
  data: CandidateStock[];
  loading?: boolean;
  pagination?: boolean;
}

interface ExpandedRowProps {
  record: CandidateStock;
}

// 展开行内容组件
const ExpandedRowContent: React.FC<ExpandedRowProps> = ({ record }) => {
  // 模拟K线数据和龙虎榜数据
  const mockDragonTigerData = [
    { rank: 1, seat: '机构专用', buy_amount: 12500000, sell_amount: 0, net_amount: 12500000 },
    { rank: 2, seat: '华泰证券上海淮海中路', buy_amount: 8600000, sell_amount: 500000, net_amount: 8100000 },
    { rank: 3, seat: '中信证券北京金融大街', buy_amount: 6200000, sell_amount: 1200000, net_amount: 5000000 },
    { rank: 4, seat: '国泰君安深圳益田路', buy_amount: 0, sell_amount: 7800000, net_amount: -7800000 },
    { rank: 5, seat: '招商证券深圳蛇口工业七路', buy_amount: 200000, sell_amount: 5600000, net_amount: -5400000 },
  ];

  return (
    <Row gutter={[16, 16]} style={{ padding: '16px 0' }}>
      <Col span={12}>
        <Card size="small" title="技术指标" bordered={false}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text type="secondary">筹码集中度: </Text>
              <Progress
                percent={(record.chip_concentration || 0.65) * 100}
                size="small"
                strokeColor={record.chip_concentration && record.chip_concentration > 0.65 ? '#52c41a' : '#faad14'}
                format={(percent) => `${percent?.toFixed(1)}%`}
              />
            </div>
            <div>
              <Text type="secondary">量比: </Text>
              <Tag color={record.volume_ratio > 3 ? 'red' : record.volume_ratio > 2 ? 'orange' : 'blue'}>
                {record.volume_ratio.toFixed(2)}
              </Tag>
            </div>
            <div>
              <Text type="secondary">换手率: </Text>
              <Text style={{ color: getChangeColor(record.turnover_rate) }}>
                {formatPercent(record.turnover_rate / 100)}
              </Text>
            </div>
            <div>
              <Text type="secondary">涨跌幅: </Text>
              <Text style={{ color: getChangeColor(record.pct_chg) }}>
                {getChangeText(record.pct_chg)}
              </Text>
            </div>
          </Space>
        </Card>
      </Col>
      <Col span={12}>
        <Card size="small" title="龙虎榜席位" bordered={false}>
          <List
            size="small"
            dataSource={mockDragonTigerData}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  title={<Text style={{ fontSize: '12px' }}>{item.seat}</Text>}
                  description={
                    <Space>
                      <Text style={{ 
                        fontSize: '11px',
                        color: item.net_amount > 0 ? '#f5222d' : '#52c41a'
                      }}>
                        净额: {formatLargeNumber(item.net_amount)}
                      </Text>
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        </Card>
      </Col>
    </Row>
  );
};

const StockTable: React.FC<StockTableProps> = ({ data, loading = false, pagination = true }) => {
  const [expandedRowKeys, setExpandedRowKeys] = useState<React.Key[]>([]);

  const columns: ColumnsType<CandidateStock> = [
    {
      title: '排名',
      dataIndex: 'rank_position',
      key: 'rank_position',
      width: 80,
      render: (rank: number) => (
        <Space>
          {rank <= 3 && <TrophyOutlined style={{ color: '#faad14' }} />}
          <Text strong>{rank}</Text>
        </Space>
      ),
    },
    {
      title: '股票信息',
      key: 'stock_info',
      width: 200,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Space>
            <Text strong>{record.name}</Text>
            <Button
              type="text"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => copyToClipboard(record.ts_code)}
            />
          </Space>
          <Text type="secondary" style={{ fontSize: '12px' }}>{record.ts_code}</Text>
        </Space>
      ),
    },
    {
      title: '所属题材',
      dataIndex: 'theme',
      key: 'theme',
      width: 120,
      render: (theme: string) => (
        <Tag color="blue">{theme || '暂无'}</Tag>
      ),
    },
    {
      title: '量比',
      dataIndex: 'volume_ratio',
      key: 'volume_ratio',
      width: 100,
      sorter: (a, b) => a.volume_ratio - b.volume_ratio,
      render: (ratio: number) => (
        <Tag color={ratio > 3 ? 'red' : ratio > 2 ? 'orange' : 'blue'}>
          {ratio.toFixed(2)}
        </Tag>
      ),
    },
    {
      title: '换手率',
      dataIndex: 'turnover_rate',
      key: 'turnover_rate',
      width: 100,
      sorter: (a, b) => a.turnover_rate - b.turnover_rate,
      render: (rate: number) => (
        <Text style={{ color: getChangeColor(rate) }}>
          {formatPercent(rate / 100)}
        </Text>
      ),
    },
    {
      title: '涨跌幅',
      dataIndex: 'pct_chg',
      key: 'pct_chg',
      width: 100,
      sorter: (a, b) => a.pct_chg - b.pct_chg,
      render: (pct: number) => (
        <Space>
          {pct > 0 ? <RiseOutlined style={{ color: '#f5222d' }} /> : <FallOutlined style={{ color: '#52c41a' }} />}
          <Text style={{ color: getChangeColor(pct) }}>
            {getChangeText(pct)}
          </Text>
        </Space>
      ),
    },
    {
      title: '筹码集中度',
      dataIndex: 'chip_concentration',
      key: 'chip_concentration',
      width: 120,
      sorter: (a, b) => (a.chip_concentration || 0) - (b.chip_concentration || 0),
      render: (concentration: number) => (
        <Progress
          percent={(concentration || 0.65) * 100}
          size="small"
          strokeColor={concentration && concentration > 0.65 ? '#52c41a' : '#faad14'}
          format={(percent) => `${percent?.toFixed(1)}%`}
        />
      ),
    },
    {
      title: '龙虎榜净买额',
      dataIndex: 'dragon_tiger_net_amount',
      key: 'dragon_tiger_net_amount',
      width: 120,
      sorter: (a, b) => (a.dragon_tiger_net_amount || 0) - (b.dragon_tiger_net_amount || 0),
      render: (amount: number) => (
        <Text style={{ color: getChangeColor(amount || 0) }}>
          {amount ? formatLargeNumber(amount) : '-'}
        </Text>
      ),
    },
    {
      title: '综合评分',
      dataIndex: 'total_score',
      key: 'total_score',
      width: 120,
      sorter: (a, b) => a.total_score - b.total_score,
      render: (score: number) => {
        const { level, color, description } = getScoreLevel(score);
        return (
          <Tooltip title={description}>
            <Space>
              <Tag color={color}>{level}</Tag>
              <Text strong style={{ color }}>{score.toFixed(1)}</Text>
            </Space>
          </Tooltip>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_, record) => (
        <Tooltip title="查看详情">
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => {
              const key = record.ts_code;
              if (expandedRowKeys.includes(key)) {
                setExpandedRowKeys(expandedRowKeys.filter(k => k !== key));
              } else {
                setExpandedRowKeys([...expandedRowKeys, key]);
              }
            }}
          />
        </Tooltip>
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={data}
      loading={loading}
      rowKey="ts_code"
      size="small"
      scroll={{ x: 1200 }}
      pagination={pagination ? {
        pageSize: 20,
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
      } : false}
      expandable={{
        expandedRowKeys,
        onExpandedRowsChange: (keys) => setExpandedRowKeys([...keys]),
        expandedRowRender: (record) => <ExpandedRowContent record={record} />,
        rowExpandable: () => true,
      }}
      className="stock-table"
    />
  );
};

export default StockTable;