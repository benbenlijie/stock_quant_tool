// 数据类型定义

export interface StockInfo {
  ts_code: string;
  name: string;
  close: number;
  pct_chg: number;
  turnover_rate: number;
  volume_ratio: number;
  total_score: number;
  rank_position: number;
  reason: string;
  market_cap?: number;
  amount?: number;
}

export interface CandidateStock extends StockInfo {
  theme?: string;
  chip_concentration?: number;
  profit_ratio?: number;
  dragon_tiger_net_amount?: number;
}

export interface MarketSentiment {
  limit_up_count: number;
  limit_times_distribution: Record<string, number>;
  avg_open_times: number;
  total_limit_stocks: number;
  zhaban_rate: number;
}

export interface StrategyStats {
  total_analyzed: number;
  candidate_count: number;
  avg_score: number;
}

export interface DashboardData {
  market_sentiment: MarketSentiment;
  today_candidates: CandidateStock[];
  strategy_stats: StrategyStats;
  recent_performance: {
    last_update: string;
    data_status: string;
    trade_date?: string;
    data_source?: string;
    error_info?: string | null;
  };
  update_time: string;
}

export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
  timestamp: string;
}

export interface StrategySettings {
  max_market_cap: number;
  min_turnover_rate: number;
  min_volume_ratio: number;
  min_daily_gain: number;
  max_stock_price: number;
      chip_concentration_threshold: number;
    profit_ratio_threshold: number;
}

export interface BacktestRequest {
  start_date: string;
  end_date: string;
  strategy_params?: Record<string, any>;
}

export interface BacktestResult {
  backtest_id: string;
  start_date: string;
  end_date: string;
  status: string;
  total_return: number;
  annual_return: number;
  max_drawdown: number;
  sharpe_ratio: number;
  win_rate: number;
  total_trades: number;
  created_at: string;
  data_source?: string;
  error_message?: string;
  initial_capital?: number;
  final_value?: number;
}

export interface ExportRequest {
  export_type: 'candidates' | 'strategy_results' | 'market_data';
  trade_date?: string;
  format: 'csv' | 'json' | 'excel';
  filters?: Record<string, any>;
}

export interface StrategyWeights {
  volume_price: number;
  chip: number;
  dragon_tiger: number;
  theme: number;
  money_flow: number;
}
