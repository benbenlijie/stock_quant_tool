import React, { useState, useEffect } from 'react';
import {
  Modal,
  Tabs,
  Table,
  Descriptions,
  Card,
  Tag,
  Space,
  Typography,
  Row,
  Col,
  Statistic,
  Timeline,
  Spin,
  Alert
} from 'antd';
import {
  RiseOutlined,
  FallOutlined,
  ClockCircleOutlined,
  DollarOutlined,
  LineChartOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { BacktestResult } from '../../types';
import { formatPercent, formatCurrency, formatDateTime, getChangeColor } from '../../utils';
import apiService from '../../services/api';

const { Title, Text } = Typography;

interface BacktestDetailModalProps {
  visible: boolean;
  backtest: BacktestResult | null;
  onClose: () => void;
}

interface TradeRecord {
  trade_id: string;
  stock_code: string;
  stock_name: string;
  action: 'buy' | 'sell';
  price: number;
  quantity: number;
  amount: number;
  trade_date: string;
  reason: string;
  profit_loss?: number;
}

interface StrategyParam {
  name: string;
  value: any;
  description: string;
}

const BacktestDetailModal: React.FC<BacktestDetailModalProps> = ({
  visible,
  backtest,
  onClose
}) => {
  const [loading, setLoading] = useState(false);
  const [detailData, setDetailData] = useState<{
    trades: any[];
    dailyPerformance: any[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 加载详细数据
  useEffect(() => {
    if (visible && backtest && backtest.backtest_id) {
      loadDetailData();
    }
  }, [visible, backtest]);

  const loadDetailData = async () => {
    if (!backtest?.backtest_id) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiService.getBacktestDetail(backtest.backtest_id);
      setDetailData({
        trades: response.trades || [],
        dailyPerformance: response.dailyPerformance || []
      });
    } catch (err) {
      console.error('加载回测详情失败:', err);
      setError('加载回测详情失败，请稍后重试');
      // 如果API失败，使用模拟数据
      setDetailData({
        trades: generateMockTrades(),
        dailyPerformance: []
      });
    } finally {
      setLoading(false);
    }
  };

  if (!backtest) return null;

  // 生成模拟交易数据（作为fallback）
  const generateMockTrades = (): TradeRecord[] => {
    const mockTrades: TradeRecord[] = [];
    const stocks = [
      { code: '000001.SZ', name: '平安银行' },
      { code: '300015.SZ', name: '爱尔眼科' },
      { code: '002594.SZ', name: '比亚迪' },
      { code: '000858.SZ', name: '五粮液' },
      { code: '002415.SZ', name: '汤臣倍健' }
    ];

    stocks.forEach((stock, index) => {
      const buyPrice = 10 + Math.random() * 50;
      const sellPrice = buyPrice * (0.9 + Math.random() * 0.2);
      const quantity = Math.floor(Math.random() * 10 + 1) * 100;

      // 买入记录
      mockTrades.push({
        trade_id: `T${Date.now()}_${index}_buy`,
        stock_code: stock.code,
        stock_name: stock.name,
        action: 'buy',
        price: buyPrice,
        quantity: quantity,
        amount: buyPrice * quantity,
        trade_date: new Date(Date.now() - (stocks.length - index) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        reason: '符合选股条件',
        profit_loss: 0
      });

      // 卖出记录
      mockTrades.push({
        trade_id: `T${Date.now()}_${index}_sell`,
        stock_code: stock.code,
        stock_name: stock.name,
        action: 'sell',
        price: sellPrice,
        quantity: quantity,
        amount: sellPrice * quantity,
        trade_date: new Date(Date.now() - (stocks.length - index - 1) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        reason: sellPrice > buyPrice ? '达到止盈目标' : '达到止损线',
        profit_loss: (sellPrice - buyPrice) * quantity
      });
    });

    return mockTrades.sort((a, b) => new Date(a.trade_date).getTime() - new Date(b.trade_date).getTime());
  };

  // 模拟策略参数数据
  const strategyParams: StrategyParam[] = [
    {
      name: '最大市值',
      value: '100亿',
      description: '选股时的最大市值限制'
    },
    {
      name: '最小换手率',
      value: '3%',
      description: '选股时的最小换手率要求'
    },
    {
      name: '最小成交量比',
      value: '1.5',
      description: '相对平均成交量的倍数'
    },
    {
      name: '涨停板筛选',
      value: '启用',
      description: '优先选择有涨停板历史的股票'
    },
    {
      name: '持仓数量',
      value: '10只',
      description: '最大同时持仓股票数量'
    },
    {
      name: '止损比例',
      value: '8%',
      description: '单只股票的最大损失比例'
    },
    {
      name: '止盈比例',
      value: '20%',
      description: '单只股票的目标收益比例'
    },
    {
      name: '持仓天数',
      value: '1-5天',
      description: '单只股票的持仓时间范围'
    }
  ];

  // 模拟交易记录数据
  const mockTradeRecords: TradeRecord[] = [
    {
      trade_id: 'T001',
      stock_code: '000001.SZ',
      stock_name: '平安银行',
      action: 'buy',
      price: 12.45,
      quantity: 1000,
      amount: 12450,
      trade_date: '2024-01-15 09:30:00',
      reason: '涨停板概念+资金流入'
    },
    {
      trade_id: 'T002',
      stock_code: '000001.SZ',
      stock_name: '平安银行',
      action: 'sell',
      price: 13.28,
      quantity: 1000,
      amount: 13280,
      trade_date: '2024-01-17 14:45:00',
      reason: '达到止盈目标',
      profit_loss: 830
    },
    {
      trade_id: 'T003',
      stock_code: '300015.SZ',
      stock_name: '爱尔眼科',
      action: 'buy',
      price: 45.67,
      quantity: 300,
      amount: 13701,
      trade_date: '2024-01-18 10:15:00',
      reason: '医药概念+技术突破'
    },
    {
      trade_id: 'T004',
      stock_code: '300015.SZ',
      stock_name: '爱尔眼科',
      action: 'sell',
      price: 42.10,
      quantity: 300,
      amount: 12630,
      trade_date: '2024-01-22 11:30:00',
      reason: '达到止损线',
      profit_loss: -1071
    }
  ];

  // 计算交易统计数据
  const trades = detailData?.trades || mockTradeRecords;
  const sellTrades = trades.filter((trade: any) => trade.action === 'sell' && trade.profit_loss !== undefined);
  const totalProfit = sellTrades.filter((trade: any) => (trade.profit_loss || 0) > 0).reduce((sum: number, trade: any) => sum + (trade.profit_loss || 0), 0);
  const totalLoss = sellTrades.filter((trade: any) => (trade.profit_loss || 0) < 0).reduce((sum: number, trade: any) => sum + (trade.profit_loss || 0), 0);
  const profitTrades = sellTrades.filter((trade: any) => (trade.profit_loss || 0) > 0);
  const lossTrades = sellTrades.filter((trade: any) => (trade.profit_loss || 0) < 0);

  // 交易记录表格列配置
  const tradeColumns: ColumnsType<TradeRecord> = [
    {
      title: '交易时间',
      dataIndex: 'trade_date',
      key: 'trade_date',
      width: 150,
      render: (date: string) => (
        <Text style={{ fontSize: '12px' }}>
          {formatDateTime(date)}
        </Text>
      )
    },
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 100,
      render: (code: string) => (
        <Text code>{code}</Text>
      )
    },
    {
      title: '股票名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      width: 100
    },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
      width: 80,
      render: (action: string) => (
        <Tag color={action === 'buy' ? 'red' : 'green'}>
          {action === 'buy' ? '买入' : '卖出'}
        </Tag>
      )
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      width: 80,
      render: (price: number) => (
        <Text>{price.toFixed(2)}</Text>
      )
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 100,
      render: (amount: number) => (
        <Text>{formatCurrency(amount)}</Text>
      )
    },
    {
      title: '盈亏',
      dataIndex: 'profit_loss',
      key: 'profit_loss',
      width: 100,
      render: (profitLoss: number | undefined) => {
        if (profitLoss === undefined) return '-';
        return (
          <Text style={{ color: getChangeColor(profitLoss) }}>
            {profitLoss > 0 ? '+' : ''}{formatCurrency(profitLoss)}
          </Text>
        );
      }
    },
    {
      title: '交易原因',
      dataIndex: 'reason',
      key: 'reason',
      ellipsis: true
    }
  ];

  // 获取最终的交易记录数据（保持向后兼容）
  const finalTradeRecords = detailData?.trades || generateMockTrades();

  const tabItems = [
    {
      key: 'overview',
      label: '回测概览',
      children: (
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {/* 基本信息 */}
          <Descriptions title="基本信息" bordered size="small">
            <Descriptions.Item label="回测ID">{backtest.backtest_id}</Descriptions.Item>
            <Descriptions.Item label="开始日期">{backtest.start_date}</Descriptions.Item>
            <Descriptions.Item label="结束日期">{backtest.end_date}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={backtest.status === 'completed' ? 'green' : 'blue'}>
                {backtest.status === 'completed' ? '已完成' : backtest.status}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {formatDateTime(backtest.created_at)}
            </Descriptions.Item>
            <Descriptions.Item label="数据来源">
              <Tag color={backtest.data_source === 'real_backtest' ? 'green' : 'orange'}>
                {backtest.data_source === 'real_backtest' ? '真实回测' : '演示数据'}
              </Tag>
            </Descriptions.Item>
          </Descriptions>

          {/* 核心指标 */}
          <Card title="核心指标">
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Statistic
                  title="总收益率"
                  value={backtest.total_return * 100}
                  precision={2}
                  valueStyle={{ color: backtest.total_return > 0 ? '#3f8600' : '#cf1322' }}
                  prefix={backtest.total_return > 0 ? <RiseOutlined /> : <FallOutlined />}
                  suffix="%"
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="年化收益率"
                  value={backtest.annual_return * 100}
                  precision={2}
                  valueStyle={{ color: backtest.annual_return > 0 ? '#3f8600' : '#cf1322' }}
                  suffix="%"
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="最大回撤"
                  value={backtest.max_drawdown * 100}
                  precision={2}
                  valueStyle={{ color: '#fa8c16' }}
                  suffix="%"
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="夏普比率"
                  value={backtest.sharpe_ratio}
                  precision={2}
                  valueStyle={{ 
                    color: backtest.sharpe_ratio > 1 ? '#3f8600' : 
                           backtest.sharpe_ratio > 0.5 ? '#faad14' : '#cf1322'
                  }}
                />
              </Col>
            </Row>
          </Card>

          {/* 交易统计 */}
          <Card title="交易统计">
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Statistic
                  title="总交易次数"
                  value={backtest.total_trades}
                  suffix="笔"
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="胜率"
                  value={backtest.win_rate * 100}
                  precision={2}
                  valueStyle={{ color: backtest.win_rate > 0.6 ? '#52c41a' : '#fa8c16' }}
                  suffix="%"
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="盈亏比"
                  value={totalLoss !== 0 ? Math.abs(totalProfit / totalLoss) : 0}
                  precision={2}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
            </Row>
          </Card>
        </Space>
      )
    },
    {
      key: 'params',
      label: '策略参数',
      children: (
        <Card title="策略配置">
          <Descriptions bordered size="small">
            {strategyParams.map((param, index) => (
              <Descriptions.Item 
                key={index}
                label={param.name}
                labelStyle={{ width: '120px' }}
              >
                <Space direction="vertical" size={0}>
                  <Text strong>{param.value}</Text>
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    {param.description}
                  </Text>
                </Space>
              </Descriptions.Item>
            ))}
          </Descriptions>
        </Card>
      )
    },
    {
      key: 'trades',
      label: '交易记录',
      children: (
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {/* 交易汇总 */}
          <Row gutter={16}>
            <Col span={8}>
              <Card size="small">
                <Statistic
                  title="盈利交易"
                  value={profitTrades.length}
                  suffix="笔"
                  valueStyle={{ color: '#52c41a' }}
                  prefix={<RiseOutlined />}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card size="small">
                <Statistic
                  title="亏损交易"
                  value={lossTrades.length}
                  suffix="笔"
                  valueStyle={{ color: '#f5222d' }}
                  prefix={<FallOutlined />}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card size="small">
                <Statistic
                  title="净盈亏"
                  value={totalProfit + totalLoss}
                  precision={2}
                  valueStyle={{ color: (totalProfit + totalLoss) > 0 ? '#52c41a' : '#f5222d' }}
                  prefix={<DollarOutlined />}
                  suffix="元"
                />
              </Card>
            </Col>
          </Row>

          {/* 交易记录表格 */}
          {loading ? (
            <Spin tip="加载交易记录中...">
              <div style={{ minHeight: 200 }} />
            </Spin>
          ) : error ? (
            <Alert 
              message="加载失败" 
              description={error} 
              type="warning" 
              showIcon 
              style={{ marginBottom: 16 }}
            />
          ) : null}
          
          <Table
            columns={tradeColumns}
            dataSource={detailData?.trades || generateMockTrades()}
            rowKey="trade_id"
            size="small"
            scroll={{ x: 800 }}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            }}
            loading={loading}
          />
        </Space>
      )
    },
    {
      key: 'timeline',
      label: '操作时间线',
      children: (
        <Card title="交易时间线">
          <Timeline
            mode="left"
            items={finalTradeRecords.map((trade, index) => ({
              label: formatDateTime(trade.trade_date),
              children: (
                <Space direction="vertical" size={0}>
                  <Space>
                    <Tag color={trade.action === 'buy' ? 'red' : 'green'}>
                      {trade.action === 'buy' ? '买入' : '卖出'}
                    </Tag>
                    <Text strong>{trade.stock_name}</Text>
                    <Text code>{trade.stock_code}</Text>
                  </Space>
                  <Text>
                    {trade.action === 'buy' ? '买入' : '卖出'} {trade.quantity}股 @ ¥{trade.price}
                  </Text>
                  <Text type="secondary">{trade.reason}</Text>
                  {trade.profit_loss !== undefined && (
                    <Text style={{ color: getChangeColor(trade.profit_loss) }}>
                      盈亏: {trade.profit_loss > 0 ? '+' : ''}{formatCurrency(trade.profit_loss)}
                    </Text>
                  )}
                </Space>
              ),
              color: trade.action === 'buy' ? 'red' : 'green',
              dot: trade.action === 'buy' ? <RiseOutlined /> : <FallOutlined />
            }))}
          />
        </Card>
      )
    }
  ];

  return (
    <Modal
      title={
        <Space>
          <LineChartOutlined />
          <span>回测详情</span>
          <Tag color="blue">{backtest.backtest_id.substring(0, 8)}...</Tag>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={1200}
      style={{ top: 20 }}
    >
      <Tabs items={tabItems} defaultActiveKey="overview" />
    </Modal>
  );
};

export default BacktestDetailModal;