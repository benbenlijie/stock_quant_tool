// 参数设置页面

import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Slider,
  InputNumber,
  Button,
  Space,
  Typography,
  Row,
  Col,
  Divider,
  message,
  Alert,
  Progress,
  Tag,
  Tooltip
} from 'antd';
import {
  SaveOutlined,
  ReloadOutlined,
  SettingOutlined,
  QuestionCircleOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';
import apiService from '../../services/api';
import { handleError, debounce } from '../../utils';

const { Title, Text, Paragraph } = Typography;

interface SettingsForm {
  // 基础筛选参数
  max_market_cap: number;
  min_turnover_rate: number;
  min_volume_ratio: number;
  min_daily_gain: number;
  max_stock_price: number;
  chip_concentration_threshold: number;
  profit_ratio_threshold: number;
  
  // 策略权重
  volume_price_weight: number;
  chip_weight: number;
  dragon_tiger_weight: number;
  theme_weight: number;
  money_flow_weight: number;
  
  // 风控参数
  stop_loss_ratio: number;
  max_drawdown: number;
  max_position_size: number;
}

const Settings: React.FC = () => {
  const [form] = Form.useForm<SettingsForm>();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [recomputing, setRecomputing] = useState(false);
  const [initialValues, setInitialValues] = useState<SettingsForm | null>(null);
  const [weightSum, setWeightSum] = useState(100);

  useEffect(() => {
    loadSettings();
  }, []);

  // 加载设置
  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await apiService.getSettings();
      
      // 转换设置为表单格式
      const formValues: SettingsForm = {
        max_market_cap: parseFloat(data.settings.max_market_cap || '50'),
        min_turnover_rate: parseFloat(data.settings.min_turnover_rate || '10'),
        min_volume_ratio: parseFloat(data.settings.min_volume_ratio || '2'),
        min_daily_gain: parseFloat(data.settings.min_daily_gain || '9'),
        max_stock_price: parseFloat(data.settings.max_stock_price || '30'),
        chip_concentration_threshold: parseFloat(data.settings.chip_concentration_threshold || '0.65'),
        profit_ratio_threshold: parseFloat(data.settings.profit_ratio_threshold || '0.5'),
        
        volume_price_weight: parseFloat(data.settings.volume_price_weight || '30'),
        chip_weight: parseFloat(data.settings.chip_weight || '25'),
        dragon_tiger_weight: parseFloat(data.settings.dragon_tiger_weight || '20'),
        theme_weight: parseFloat(data.settings.theme_weight || '15'),
        money_flow_weight: parseFloat(data.settings.money_flow_weight || '10'),
        
        stop_loss_ratio: parseFloat(data.settings.stop_loss_ratio || '0.1'),
        max_drawdown: parseFloat(data.settings.max_drawdown || '0.2'),
        max_position_size: parseFloat(data.settings.max_position_size || '0.5'),
      };
      
      form.setFieldsValue(formValues);
      setInitialValues(formValues);
      calculateWeightSum(formValues);
      
    } catch (error) {
      handleError(error, '加载设置失败');
    } finally {
      setLoading(false);
    }
  };

  // 计算权重总和
  const calculateWeightSum = (values: Partial<SettingsForm>) => {
    const sum = (
      Number(values.volume_price_weight || 0) +
      Number(values.chip_weight || 0) +
      Number(values.dragon_tiger_weight || 0) +
      Number(values.theme_weight || 0) +
      Number(values.money_flow_weight || 0)
    );
    setWeightSum(isNaN(sum) ? 0 : sum);
  };

  // 权重变化处理（防抖）
  const debouncedWeightChange = debounce((changedValues: Partial<SettingsForm>) => {
    calculateWeightSum(form.getFieldsValue());
  }, 300);

  // 表单值变化
  const handleFormChange = (changedValues: Partial<SettingsForm>) => {
    // 检查是否有权重字段变化
    const weightFields = ['volume_price_weight', 'chip_weight', 'dragon_tiger_weight', 'theme_weight', 'money_flow_weight'];
    if (Object.keys(changedValues).some(key => weightFields.includes(key))) {
      debouncedWeightChange(changedValues);
    }
  };

  // 权重归一化
  const normalizeWeights = () => {
    const values = form.getFieldsValue();
    const currentSum = (
      Number(values.volume_price_weight || 0) +
      Number(values.chip_weight || 0) +
      Number(values.dragon_tiger_weight || 0) +
      Number(values.theme_weight || 0) +
      Number(values.money_flow_weight || 0)
    );
    
    if (currentSum !== 100 && currentSum > 0 && !isNaN(currentSum)) {
      const factor = 100 / currentSum;
      const newWeights = {
        volume_price_weight: Math.round(Number(values.volume_price_weight || 0) * factor),
        chip_weight: Math.round(Number(values.chip_weight || 0) * factor),
        dragon_tiger_weight: Math.round(Number(values.dragon_tiger_weight || 0) * factor),
        theme_weight: Math.round(Number(values.theme_weight || 0) * factor),
        money_flow_weight: Math.round(Number(values.money_flow_weight || 0) * factor),
      };
      
      form.setFieldsValue(newWeights);
      setWeightSum(100);
      message.success('权重已归一化为100%');
    } else if (isNaN(currentSum) || currentSum <= 0) {
      message.error('无效的权重数值，请检查输入');
    }
  };

  // 保存设置
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      
      // 转换为API格式（安全的toString转换）
      const settingsToUpdate = {
        max_market_cap: (values.max_market_cap ?? 50).toString(),
        min_turnover_rate: (values.min_turnover_rate ?? 10).toString(),
        min_volume_ratio: (values.min_volume_ratio ?? 2).toString(),
        min_daily_gain: (values.min_daily_gain ?? 9).toString(),
        max_stock_price: (values.max_stock_price ?? 30).toString(),
        chip_concentration_threshold: (values.chip_concentration_threshold ?? 0.65).toString(),
        profit_ratio_threshold: (values.profit_ratio_threshold ?? 0.5).toString(),
        
        volume_price_weight: (values.volume_price_weight ?? 30).toString(),
        chip_weight: (values.chip_weight ?? 25).toString(),
        dragon_tiger_weight: (values.dragon_tiger_weight ?? 20).toString(),
        theme_weight: (values.theme_weight ?? 15).toString(),
        money_flow_weight: (values.money_flow_weight ?? 10).toString(),
        
        stop_loss_ratio: (values.stop_loss_ratio ?? 0.1).toString(),
        max_drawdown: (values.max_drawdown ?? 0.2).toString(),
        max_position_size: (values.max_position_size ?? 0.5).toString(),
      };
      
      // 批量更新设置
      await apiService.updateStrategyConfig(settingsToUpdate);
      message.success('设置保存成功');
      
      // 更新初始值
      setInitialValues(values);
      
    } catch (error) {
      handleError(error, '保存设置失败');
    } finally {
      setSaving(false);
    }
  };

  // 重置设置
  const handleReset = () => {
    if (initialValues) {
      form.setFieldsValue(initialValues);
      calculateWeightSum(initialValues);
      message.success('设置已重置');
    }
  };

  // 实时重算
  const handleRecompute = async () => {
    try {
      setRecomputing(true);
      await apiService.recomputeStrategy({ force_update: true });
      message.success('策略重新计算完成');
    } catch (error) {
      handleError(error, '重新计算失败');
    } finally {
      setRecomputing(false);
    }
  };

  return (
    <div className="settings">
      <Title level={2}>参数设置</Title>
      
      <Form
        form={form}
        layout="vertical"
        onValuesChange={handleFormChange}
        disabled={loading}
      >
        {/* 基础筛选参数 */}
        <Card title="基础筛选参数" style={{ marginBottom: 16 }}>
          <Row gutter={[24, 16]}>
            <Col xs={24} md={12}>
              <Form.Item
                name="max_market_cap"
                label={
                  <Space>
                    <span>最大流通市值</span>
                    <Tooltip title="筛选流通市值小于该值的股票（单位：亿元）">
                      <QuestionCircleOutlined />
                    </Tooltip>
                  </Space>
                }
                rules={[{ required: true, type: 'number', min: 1, max: 1000 }]}
              >
                <Slider
                  min={10}
                  max={200}
                  step={5}
                  marks={{
                    10: '10亿',
                    50: '50亿',
                    100: '100亿',
                    200: '200亿',
                  }}
                  tooltip={{ formatter: (value) => `${value}亿元` }}
                />
              </Form.Item>
            </Col>
            
            <Col xs={24} md={12}>
              <Form.Item
                name="min_turnover_rate"
                label={
                  <Space>
                    <span>最小换手率</span>
                    <Tooltip title="筛选换手率大于该值的股票（单位：%）">
                      <QuestionCircleOutlined />
                    </Tooltip>
                  </Space>
                }
                rules={[{ required: true, type: 'number', min: 0, max: 50 }]}
              >
                <Slider
                  min={1}
                  max={30}
                  step={1}
                  marks={{
                    1: '1%',
                    10: '10%',
                    20: '20%',
                    30: '30%',
                  }}
                  tooltip={{ formatter: (value) => `${value}%` }}
                />
              </Form.Item>
            </Col>
            
            <Col xs={24} md={12}>
              <Form.Item
                name="min_volume_ratio"
                label={
                  <Space>
                    <span>最小量比</span>
                    <Tooltip title="筛选量比大于该值的股票">
                      <QuestionCircleOutlined />
                    </Tooltip>
                  </Space>
                }
                rules={[{ required: true, type: 'number', min: 0.1, max: 10 }]}
              >
                <Slider
                  min={0.5}
                  max={5}
                  step={0.1}
                  marks={{
                    0.5: '0.5',
                    2: '2',
                    3.5: '3.5',
                    5: '5',
                  }}
                  tooltip={{ formatter: (value) => `${value}倍` }}
                />
              </Form.Item>
            </Col>
            
            <Col xs={24} md={12}>
              <Form.Item
                name="min_daily_gain"
                label={
                  <Space>
                    <span>最小日涨幅</span>
                    <Tooltip title="筛选当日涨幅大于该值的股票（单位：%）">
                      <QuestionCircleOutlined />
                    </Tooltip>
                  </Space>
                }
                rules={[{ required: true, type: 'number', min: 0, max: 20 }]}
              >
                <Slider
                  min={5}
                  max={15}
                  step={0.5}
                  marks={{
                    5: '5%',
                    9: '9%',
                    10: '10%',
                    15: '15%',
                  }}
                  tooltip={{ formatter: (value) => `${value}%` }}
                />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* 高级阈值配置 */}
        <Card title="高级阈值配置" style={{ marginBottom: 16 }}>
          <Row gutter={[24, 16]}>
            <Col xs={24} md={12}>
              <Form.Item
                name="chip_concentration_threshold"
                label={
                  <Space>
                    <span>筹码集中度阈值</span>
                    <Tooltip title="筛选筹码集中度大于该值的股票（0-1）">
                      <QuestionCircleOutlined />
                    </Tooltip>
                  </Space>
                }
                rules={[{ required: true, type: 'number', min: 0, max: 1 }]}
              >
                <Slider
                  min={0.3}
                  max={0.9}
                  step={0.05}
                  marks={{
                    0.3: '30%',
                    0.5: '50%',
                    0.65: '65%',
                    0.8: '80%',
                    0.9: '90%',
                  }}
                  tooltip={{ formatter: (value) => `${(value * 100).toFixed(0)}%` }}
                />
              </Form.Item>
            </Col>
            
            <Col xs={24} md={12}>
              <Form.Item
                name="profit_ratio_threshold"
                label={
                  <Space>
                    <span>获利盘比例阈值</span>
                    <Tooltip title="筛选获利盘比例大于该值的股票（0-1）">
                      <QuestionCircleOutlined />
                    </Tooltip>
                  </Space>
                }
                rules={[{ required: true, type: 'number', min: 0, max: 1 }]}
              >
                <Slider
                  min={0.2}
                  max={0.8}
                  step={0.05}
                  marks={{
                    0.2: '20%',
                    0.4: '40%',
                    0.5: '50%',
                    0.6: '60%',
                    0.8: '80%',
                  }}
                  tooltip={{ formatter: (value) => `${(value * 100).toFixed(0)}%` }}
                />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* 策略权重配置 */}
        <Card 
          title={
            <Space>
              <span>策略权重配置</span>
              <Tag color={weightSum === 100 ? 'green' : 'orange'}>
                当前总和: {weightSum}%
              </Tag>
              {weightSum !== 100 && (
                <Button size="small" onClick={normalizeWeights}>
                  归一化
                </Button>
              )}
            </Space>
          }
          style={{ marginBottom: 16 }}
        >
          {weightSum !== 100 && (
            <Alert
              message="权重总和应为100%"
              description="当前权重总和不等于100%，建议点击归一化按钮自动调整"
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}
          
          <Row gutter={[24, 16]}>
            <Col xs={24} md={12}>
              <Form.Item
                name="volume_price_weight"
                label="量价突破权重"
                rules={[{ required: true, type: 'number', min: 0, max: 100 }]}
              >
                <Slider
                  min={0}
                  max={50}
                  marks={{ 0: '0%', 30: '30%', 50: '50%' }}
                  tooltip={{ formatter: (value) => `${value}%` }}
                />
              </Form.Item>
            </Col>
            
            <Col xs={24} md={12}>
              <Form.Item
                name="chip_weight"
                label="筹码集中度权重"
                rules={[{ required: true, type: 'number', min: 0, max: 100 }]}
              >
                <Slider
                  min={0}
                  max={50}
                  marks={{ 0: '0%', 25: '25%', 50: '50%' }}
                  tooltip={{ formatter: (value) => `${value}%` }}
                />
              </Form.Item>
            </Col>
          </Row>
          
          <Progress
            percent={weightSum}
            status={weightSum === 100 ? 'success' : 'exception'}
            format={() => `${weightSum}%`}
          />
        </Card>
      </Form>

      {/* 操作按钮 */}
      <Card>
        <Space size="middle">
          <Button
            type="primary"
            size="large"
            icon={<SaveOutlined />}
            onClick={handleSave}
            loading={saving}
          >
            保存设置
          </Button>
          
          <Button
            size="large"
            icon={<ReloadOutlined />}
            onClick={handleReset}
            disabled={loading}
          >
            重置设置
          </Button>
          
          <Button
            size="large"
            icon={<ThunderboltOutlined />}
            onClick={handleRecompute}
            loading={recomputing}
            type="dashed"
          >
            实时重算
          </Button>
        </Space>
      </Card>
    </div>
  );
};

export default Settings;