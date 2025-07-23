// 市场情绪组件

import React from 'react';
import { Card, Row, Col, Statistic, Progress, Tag, Space, Typography } from 'antd';
import {
  RiseOutlined,
  FallOutlined,
  TrophyOutlined,
  ThunderboltOutlined,
  FireOutlined
} from '@ant-design/icons';
import type { MarketSentiment } from '../../types';
import { formatPercent } from '../../utils';

const { Text, Title } = Typography;

interface MarketSentimentProps {
  data: MarketSentiment;
  loading?: boolean;
}

const MarketSentimentComponent: React.FC<MarketSentimentProps> = ({ data, loading = false }) => {
  // 计算情绪指数 (0-100)
  const emotionIndex = Math.min(100, (data.limit_up_count / 50) * 100);
  
  // 获取情绪等级和颜色
  const getEmotionLevel = (index: number) => {
    if (index >= 80) return { level: '极度狂热', color: '#ff4d4f', icon: <FireOutlined /> };
    if (index >= 60) return { level: '热度较高', color: '#fa8c16', icon: <ThunderboltOutlined /> };
    if (index >= 40) return { level: '情绪正常', color: '#52c41a', icon: <RiseOutlined /> };
    if (index >= 20) return { level: '情绪低迷', color: '#1890ff', icon: <FallOutlined /> };
    return { level: '极度冰点', color: '#8c8c8c', icon: <FallOutlined /> };
  };

  const emotion = getEmotionLevel(emotionIndex);

  // 连板分布数据
  const limitTimesData = Object.entries(data.limit_times_distribution || {})
    .map(([times, count]) => ({ times: parseInt(times), count }))
    .sort((a, b) => a.times - b.times);

  return (
    <Card title="市场情绪监控" loading={loading}>
      <Row gutter={[16, 16]}>
        {/* 情绪指数 */}
        <Col xs={24} sm={12} md={6}>
          <Card size="small" bordered={false}>
            <Statistic
              title="情绪指数"
              value={emotionIndex.toFixed(1)}
              precision={1}
              valueStyle={{ color: emotion.color }}
              prefix={emotion.icon}
              suffix={emotion.level}
            />
            <Progress
              percent={emotionIndex}
              strokeColor={emotion.color}
              size="small"
              showInfo={false}
              style={{ marginTop: 8 }}
            />
          </Card>
        </Col>

        {/* 涨停家数 */}
        <Col xs={24} sm={12} md={6}>
          <Card size="small" bordered={false}>
            <Statistic
              title="涨停家数"
              value={data.limit_up_count}
              valueStyle={{
                color: data.limit_up_count > 30 ? '#ff4d4f' : 
                       data.limit_up_count > 15 ? '#fa8c16' : '#52c41a'
              }}
              prefix={<RiseOutlined />}
              suffix="只"
            />
          </Card>
        </Col>

        {/* 连板家数 */}
        <Col xs={24} sm={12} md={6}>
          <Card size="small" bordered={false}>
            <Statistic
              title="连板家数"
              value={data.total_limit_stocks}
              valueStyle={{
                color: data.total_limit_stocks > 10 ? '#ff4d4f' : 
                       data.total_limit_stocks > 5 ? '#fa8c16' : '#52c41a'
              }}
              prefix={<TrophyOutlined />}
              suffix="只"
            />
          </Card>
        </Col>

        {/* 炸板率 */}
        <Col xs={24} sm={12} md={6}>
          <Card size="small" bordered={false}>
            <Statistic
              title="炸板率"
              value={data.zhaban_rate * 100}
              precision={1}
              valueStyle={{
                color: data.zhaban_rate > 0.5 ? '#52c41a' : 
                       data.zhaban_rate > 0.3 ? '#fa8c16' : '#ff4d4f'
              }}
              prefix={<ThunderboltOutlined />}
              suffix="%"
            />
          </Card>
        </Col>
      </Row>

      {/* 连板分布 */}
      <Row style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card size="small" title="连板分布情况" bordered={false}>
            <Space wrap>
              {limitTimesData.map(({ times, count }) => (
                <Tag
                  key={times}
                  color={times >= 5 ? 'red' : times >= 3 ? 'orange' : times >= 2 ? 'gold' : 'blue'}
                  style={{ marginBottom: 4 }}
                >
                  {times}连板: {count}只
                </Tag>
              ))}
            </Space>
            {limitTimesData.length === 0 && (
              <Text type="secondary">暂无连板数据</Text>
            )}
          </Card>
        </Col>
      </Row>

      {/* 平均打开次数 */}
      <Row style={{ marginTop: 8 }}>
        <Col span={24}>
          <Card size="small" bordered={false}>
            <Space>
              <Text type="secondary">平均打开次数:</Text>
              <Text strong style={{
                color: data.avg_open_times > 2 ? '#ff4d4f' : 
                       data.avg_open_times > 1 ? '#fa8c16' : '#52c41a'
              }}>
                {data.avg_open_times.toFixed(2)} 次
              </Text>
              <Text type="secondary">
                ({data.avg_open_times > 2 ? '分歧较大' : 
                  data.avg_open_times > 1 ? '分歧适中' : '高度一致'})
              </Text>
            </Space>
          </Card>
        </Col>
      </Row>
    </Card>
  );
};

export default MarketSentimentComponent;