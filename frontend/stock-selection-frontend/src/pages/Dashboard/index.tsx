// 仪表盘页面

import React, { useState, useEffect } from 'react';
import {
  Row,
  Col,
  Card,
  Button,
  Space,
  DatePicker,
  Statistic,
  Alert,
  Spin,
  message,
  Typography,
  Divider,
  Tag
} from 'antd';
import {
  ReloadOutlined,
  DownloadOutlined,
  CalendarOutlined,
  TrophyOutlined,
  LineChartOutlined
} from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';
import MarketSentiment from '../../components/MarketSentiment';
import StockTable from '../../components/StockTable';
import apiService from '../../services/api';
import { downloadFile, handleError } from '../../utils';
import type { DashboardData } from '../../types';

const { Title, Text } = Typography;

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [data, setData] = useState<DashboardData | null>(null);
  const [selectedDate, setSelectedDate] = useState<Dayjs>(dayjs());

  // 初始化加载数据
  useEffect(() => {
    loadDashboardData();
  }, []);

  // 加载仪表盘数据
  const loadDashboardData = async (tradeDate?: string) => {
    try {
      setLoading(true);
      const result = await apiService.getDashboard(tradeDate);
      setData(result);
    } catch (error) {
      handleError(error, '加载仪表盘数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 刷新数据
  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      const result = await apiService.getDashboard(selectedDate.format('YYYY-MM-DD'));
      setData(result);
      
      // 根据数据源显示不同的成功信息
      if (result.recent_performance?.data_source === 'tushare') {
        message.success('数据刷新成功（真实数据）');
      } else {
        message.warning('数据刷新成功（演示数据）');
      }
    } catch (error) {
      handleError(error, '刷新数据失败');
    } finally {
      setRefreshing(false);
    }
  };

  // 日期变更
  const handleDateChange = (date: Dayjs | null) => {
    if (date) {
      setSelectedDate(date);
      loadDashboardData(date.format('YYYY-MM-DD'));
    }
  };

  // 导出数据
  const handleExport = async () => {
    try {
      const blob = await apiService.exportData({
        export_type: 'candidates',
        trade_date: selectedDate.format('YYYY-MM-DD'),
        format: 'excel'
      });
      downloadFile(blob, `候选股票_${selectedDate.format('YYYY-MM-DD')}.xlsx`);
      message.success('导出成功');
    } catch (error) {
      handleError(error, '导出失败');
    }
  };

  // 触发策略重新计算
  const handleRecompute = async () => {
    try {
      setRefreshing(true);
      const result = await apiService.recomputeStrategy({
        trade_date: selectedDate.format('YYYY-MM-DD'),
        force_update: true
      });
      
      // 根据数据源显示不同的成功信息
      if (result.data_source === 'tushare') {
        message.success('重新计算完成（真实数据）');
      } else {
        message.warning('重新计算完成（演示数据）');
      }
      
      await loadDashboardData(selectedDate.format('YYYY-MM-DD'));
    } catch (error) {
      handleError(error, '重新计算失败');
    } finally {
      setRefreshing(false);
    }
  };

  if (loading && !data) {
    return (
      <div style={{ textAlign: 'center', marginTop: 100 }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>正在加载仪表盘数据...</Text>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      {/* 页面标题和操作栏 */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Space align="center">
            <Title level={2} style={{ margin: 0 }}>量化选股仪表盘</Title>
            <Tag color="blue">{selectedDate.format('YYYY-MM-DD')}</Tag>
          </Space>
        </Col>
        <Col>
          <Space>
            <DatePicker
              value={selectedDate}
              onChange={handleDateChange}
              allowClear={false}
              format="YYYY-MM-DD"
              placeholder="选择交易日期"
              suffixIcon={<CalendarOutlined />}
              disabled={refreshing}
            />
            <Button
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              loading={refreshing}
            >
              刷新数据
            </Button>
            <Button
              icon={<LineChartOutlined />}
              onClick={handleRecompute}
              loading={refreshing}
              type="primary"
            >
              重新计算
            </Button>
            <Button
              icon={<DownloadOutlined />}
              onClick={handleExport}
              disabled={!data?.today_candidates?.length}
            >
              导出结果
            </Button>
          </Space>
        </Col>
      </Row>

      {data ? (
        <>
          {/* 数据状态提示 */}
          {data.recent_performance?.data_source === 'mock' && (
            <Alert
              message="数据状态提示"
              description={
                <div>
                  <div>📊 当前使用演示数据，可能原因：API调用限制或网络问题</div>
                  <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                    最后更新: {data.update_time} | 数据源: {data.recent_performance?.data_source}
                  </div>
                </div>
              }
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}
          {data.recent_performance?.data_source === 'tushare' && (
            <Alert
              message="实时数据状态"
              description={
                <div>
                  <div>✅ 当前使用Tushare真实数据</div>
                  <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                    最后更新: {data.update_time} | 数据源: {data.recent_performance?.data_source}
                  </div>
                </div>
              }
              type="success"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          {/* 市场情绪组件 */}
          <MarketSentiment
            data={data.market_sentiment}
            loading={refreshing}
          />

          {/* 策略统计 */}
          <Row gutter={[16, 16]} style={{ margin: '16px 0' }}>
            <Col xs={24} sm={8}>
              <Card size="small">
                <Statistic
                  title="分析股票总数"
                  value={data.strategy_stats.total_analyzed}
                  prefix={<LineChartOutlined />}
                  suffix="只"
                />
              </Card>
            </Col>
            <Col xs={24} sm={8}>
              <Card size="small">
                <Statistic
                  title="候选股票数量"
                  value={data.strategy_stats.candidate_count}
                  prefix={<TrophyOutlined />}
                  suffix="只"
                  valueStyle={{ color: '#3f8600' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={8}>
              <Card size="small">
                <Statistic
                  title="平均评分"
                  value={data.strategy_stats.avg_score}
                  precision={1}
                  suffix="分"
                  valueStyle={{ color: '#cf1322' }}
                />
              </Card>
            </Col>
          </Row>

          <Divider />

          {/* 候选股票表格 */}
          <Card title="今日候选股票" size="small">
            {data.today_candidates && data.today_candidates.length > 0 ? (
              <StockTable
                data={data.today_candidates}
                loading={refreshing}
                pagination={true}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Text type="secondary">暂无候选股票数据</Text>
              </div>
            )}
          </Card>
        </>
      ) : (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Text type="secondary">暂无数据</Text>
        </div>
      )}
    </div>
  );
};

export default Dashboard;