// API服务层

import axios, { AxiosResponse } from 'axios';
import { message } from 'antd';
import type {
  ApiResponse,
  DashboardData,
  CandidateStock,
  StrategySettings,
  BacktestRequest,
  BacktestResult,
  ExportRequest
} from '../types';

// 创建axios实例 - 真实数据版本
const api = axios.create({
  baseURL: 'https://zbhwqysllfettelcwynh.supabase.co/functions/v1/stock-api-real',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpiaHdxeXNsbGZldHRlbGN3eW5oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMwOTM1NjAsImV4cCI6MjA2ODY2OTU2MH0.3axIXGwTGQl1OnQb327gZo0WpOyoc3G5Pz_EQvYAVuA'
  }
});

// 创建回测引擎API实例
const backtestApi = axios.create({
  baseURL: 'https://zbhwqysllfettelcwynh.supabase.co/functions/v1/backtest-engine',
  timeout: 300000, // 5分钟超时，回测可能需要较长时间
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpiaHdxeXNsbGZldHRlbGN3eW5oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMwOTM1NjAsImV4cCI6MjA2ODY2OTU2MH0.3axIXGwTGQl1OnQb327gZo0WpOyoc3G5Pz_EQvYAVuA'
  }
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token等
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const { data } = response;
    
    // 检查业务状态码
    if (data.code !== 200) {
      console.error('API业务错误:', data);
      message.error(data.message || '请求失败');
      return Promise.reject(new Error(data.message));
    }
    
    return response;
  },
  (error) => {
    console.error('API网络错误:', error);
    let errorMessage;
    
    if (error.code === 'ECONNABORTED') {
      errorMessage = '请求超时，请检查网络连接';
    } else if (error.response) {
      errorMessage = error.response?.data?.message || error.response?.data?.detail || `服务器错误 (${error.response.status})`;
    } else if (error.request) {
      errorMessage = '网络连接失败，请检查网络设置';
    } else {
      errorMessage = error.message || '未知错误';
    }
    
    message.error(errorMessage);
    return Promise.reject(error);
  }
);

// API方法定义
export const apiService = {
  // Dashboard相关
  async getDashboard(tradeDate?: string): Promise<DashboardData> {
    const params = tradeDate ? { trade_date: tradeDate } : {};
    const response = await api.get<ApiResponse<DashboardData>>('/dashboard', { params });
    return response.data.data;
  },

  async getMarketSentiment(tradeDate?: string) {
    const params = tradeDate ? { trade_date: tradeDate } : {};
    const response = await api.get('/dashboard/market-sentiment', { params });
    return response.data.data;
  },

  async getStrategyStats(tradeDate?: string) {
    const params = tradeDate ? { trade_date: tradeDate } : {};
    const response = await api.get('/dashboard/stats', { params });
    return response.data.data;
  },

  // 股票数据相关
  async getCandidateStocks(tradeDate?: string, limit: number = 50): Promise<{
    trade_date: string;
    candidates: CandidateStock[];
    total_count: number;
  }> {
    const params: any = { limit };
    if (tradeDate) params.trade_date = tradeDate;
    
    const response = await api.get<ApiResponse>('/stocks/candidates', { params });
    return response.data.data;
  },

  async getStockBasicInfo(tsCode: string) {
    const response = await api.get(`/stocks/basic/${tsCode}`);
    return response.data.data;
  },

  async getStockStrategyResult(tsCode: string, tradeDate?: string) {
    const params = tradeDate ? { trade_date: tradeDate } : {};
    const response = await api.get(`/stocks/strategy-result/${tsCode}`, { params });
    return response.data.data;
  },

  async searchStocks(keyword: string, limit: number = 20) {
    const params = { keyword, limit };
    const response = await api.get('/stocks/search', { params });
    return response.data.data;
  },

  // 策略相关
  async recomputeStrategy(data: { trade_date?: string; force_update?: boolean }) {
    const response = await api.post('/strategy/recompute', data);
    return response.data.data;
  },

  async updateStrategyConfig(configUpdates: Record<string, any>) {
    const response = await api.put('/strategy/config', { config_updates: configUpdates });
    return response.data.data;
  },

  async getStrategyStatus() {
    const response = await api.get('/strategy/status');
    return response.data.data;
  },

  // 设置相关
  async getSettings(): Promise<{ settings: Record<string, string>; count: number }> {
    const response = await api.get<ApiResponse>('/settings');
    return response.data.data;
  },

  async updateSetting(settingKey: string, settingValue: string) {
    const response = await api.put('/settings', {
      setting_key: settingKey,
      setting_value: settingValue
    });
    return response.data.data;
  },

  async updateSettingsBatch(settings: Record<string, any>) {
    const response = await api.put('/settings', {
      settings: settings
    });
    return response.data.data;
  },

  // 回测相关
  async getBacktestResults(limit: number = 20) {
    const params = { limit };
    const response = await api.get('/backtest', { params });
    return response.data.data;
  },

  async runBacktest(data: BacktestRequest): Promise<BacktestResult> {
    // 生成唯一的回测ID
    const backtestId = `backtest_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // 首先在数据库中创建回测记录
    try {
      const initResponse = await api.post('/backtest/init', {
        backtest_id: backtestId,
        start_date: data.startDate,
        end_date: data.endDate,
        initial_capital: data.initialCapital || 1000000,
        strategy_name: '趋势跟踪策略',
        strategy_params: data
      });
      
      // 启动回测引擎
      const engineResponse = await backtestApi.post('', {
        action: 'run_backtest',
        data: {
          backtestId,
          config: {
            startDate: data.startDate,
            endDate: data.endDate,
            initialCapital: data.initialCapital || 1000000,
            strategyParams: {
              maxMarketCap: data.maxMarketCap || 500,
              minTurnoverRate: data.minTurnoverRate || 2,
              minVolumeRatio: data.minVolumeRatio || 1.5,
              minDailyGain: data.minDailyGain || 3,
              maxStockPrice: data.maxStockPrice || 100,
              chipConcentrationThreshold: data.chipConcentrationThreshold || 0.6,
              profitRatioThreshold: data.profitRatioThreshold || 0.5,
              maxPositions: 10,
              stopLoss: 10,
              takeProfit: 20,
              holdingDays: [3, 20]
            }
          }
        }
      });
      
      return engineResponse.data;
      
    } catch (error) {
      console.error('回测失败:', error);
      throw error;
    }
  },

  // 新增：获取回测详细信息
  async getBacktestDetail(backtestId: string): Promise<{
    backtest: BacktestResult;
    trades: any[];
    dailyPerformance: any[];
  }> {
    const response = await backtestApi.post('', {
      action: 'get_backtest_detail',
      data: { backtestId }
    });
    return response.data;
  },

  // 导出相关
  async exportData(data: ExportRequest): Promise<Blob> {
    const response = await api.post('/export', data, {
      responseType: 'blob'
    });
    return response.data;
  },

  // 健康检查
  async healthCheck() {
    const response = await api.get('/');
    return response.data;
  }
};

export default apiService;
