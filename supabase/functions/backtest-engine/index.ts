// Supabase Edge Function for Backtest Engine
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// 基于换手率递推法的筹码分布计算（用于模拟数据生成）
function generateRealisticChipMetrics(pctChg: number, turnoverRate: number, volumeRatio: number): [number, number] {
  // 基于市场规律生成更真实的筹码集中度和获利盘比例
  
  // 筹码集中度计算 - 换手率因子分析
  let baseConcentration = 0.5;
  
  // 换手率因子：适度换手率最佳（符合筹码集中的特征）
  const optimalTurnover = 8.0;
  let turnoverFactor = 1.0 - Math.abs(turnoverRate - optimalTurnover) / 20.0;
  turnoverFactor = Math.max(0.3, Math.min(1.2, turnoverFactor));
  
  // 量比因子：适度放量表示有资金介入
  const volumeFactor = Math.min(1.3, Math.max(0.7, 0.8 + volumeRatio / 10));
  
  // 涨幅因子：适度上涨配合集中度
  let priceFactor = 1.0;
  if (pctChg >= 2 && pctChg <= 8) {
    priceFactor = 1.1;  // 温和上涨有利于筹码集中
  } else if (pctChg > 9) {
    priceFactor = 1.2;  // 大涨可能伴随筹码集中
  } else if (pctChg < -3) {
    priceFactor = 0.9;  // 下跌通常筹码分散
  }
  
  // 综合计算集中度（基于基尼系数的简化版本）
  let concentration = baseConcentration * turnoverFactor * volumeFactor * priceFactor;
  concentration = Math.max(0.2, Math.min(0.95, concentration));
  
  // 获利盘比例计算 - 基于换手率递推法的核心思想
  let profitRatio = 0.5; // 基础获利盘比例
  
  // 涨跌幅影响（采用分段处理，符合真实市场规律）
  if (pctChg > 0) {
    // 上涨时获利盘增加，但需要考虑涨幅大小
    if (pctChg <= 3) {
      profitRatio += pctChg / 20; // 温和上涨：获利盘线性增加
    } else if (pctChg <= 7) {
      profitRatio += 0.15 + (pctChg - 3) / 40; // 适度上涨：增幅放缓
    } else {
      profitRatio += 0.25 + Math.min(0.15, (pctChg - 7) / 60); // 大涨：增幅递减（高位套现）
    }
  } else {
    // 下跌时获利盘减少（成本上移效应）
    profitRatio += Math.max(-0.3, pctChg / 15);
  }
  
  // 换手率影响 - 高换手可能意味着获利盘在减少
  // 这符合换手率递推法中"旧筹码衰减"的核心思想
  if (turnoverRate > 10) {
    const decayFactor = Math.min(0.1, (turnoverRate - 10) / 100);
    profitRatio -= decayFactor; // 高换手率导致获利盘流失
  }
  
  // 量比影响 - 放量上涨增加获利盘可信度
  if (volumeRatio > 1.5 && pctChg > 2) {
    const volumeBonus = Math.min(0.05, (volumeRatio - 1.5) / 20);
    profitRatio += volumeBonus; // 放量上涨确认获利盘增加
  }
  
  // 边界处理（符合实际市场情况）
  profitRatio = Math.max(0.1, Math.min(0.9, profitRatio));
  
  return [concentration, profitRatio];
}

interface BacktestConfig {
  startDate: string;
  endDate: string;
  initialCapital: number;
  strategyParams: {
    maxMarketCap: number;
    minTurnoverRate: number;
    minVolumeRatio: number;
    minDailyGain: number;
    maxStockPrice: number;
    chipConcentrationThreshold: number;
    profitRatioThreshold: number;
    maxPositions: number;
    stopLoss: number;
    takeProfit: number;
    holdingDays: [number, number];
  };
}

interface StockData {
  stock_code: string;
  stock_name: string;
  price: number;
  pct_chg: number;
  turnover_rate: number;
  volume_ratio: number;
  market_cap: number;
  chip_concentration: number;
  profit_ratio: number;
  trade_date: string;
}

interface Position {
  stock_code: string;
  stock_name: string;
  entry_date: string;
  entry_price: number;
  quantity: number;
  entry_amount: number;
  entry_reason: string;
  holding_days: number;
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
  trade_reason: string;
  signal_strength: number;
  profit_loss?: number;
  cumulative_return: number;
  portfolio_value: number;
}

class BacktestEngine {
  private supabase: any;
  private backtestId: string;
  private config: BacktestConfig;
  private portfolio: {
    cash: number;
    positions: Position[];
    totalValue: number;
  };
  private trades: TradeRecord[] = [];
  private dailyPerformance: any[] = [];
  private signals: any[] = [];

  constructor(supabase: any, backtestId: string, config: BacktestConfig) {
    this.supabase = supabase;
    this.backtestId = backtestId;
    this.config = config;
    this.portfolio = {
      cash: config.initialCapital,
      positions: [],
      totalValue: config.initialCapital
    };
  }

  // 主回测流程
  async runBacktest(): Promise<any> {
    try {
      console.log(`开始回测: ${this.backtestId}`);
      
      // 获取历史数据
      const historicalData = await this.getHistoricalData();
      
      // 按日期分组数据
      const dataByDate = this.groupDataByDate(historicalData);
      const sortedDates = Object.keys(dataByDate).sort();
      
      // 逐日进行回测
      for (const date of sortedDates) {
        await this.processDay(date, dataByDate[date]);
      }
      
      // 计算最终指标
      const finalMetrics = this.calculateFinalMetrics();
      
      // 保存回测结果
      await this.saveBacktestResults(finalMetrics);
      
      return {
        success: true,
        backtestId: this.backtestId,
        metrics: finalMetrics,
        trades: this.trades.length,
        finalValue: this.portfolio.totalValue
      };
      
    } catch (error) {
      console.error('回测执行错误:', error);
      throw error;
    }
  }

  // 获取历史数据
  private async getHistoricalData(): Promise<StockData[]> {
    // 这里应该从实际数据源获取历史数据
    // 为了演示，我们生成模拟数据
    return this.generateMockHistoricalData();
  }

  // 生成模拟历史数据
  private generateMockHistoricalData(): StockData[] {
    const data: StockData[] = [];
    const stocks = [
      '000001.SZ', '000002.SZ', '300015.SZ', '002594.SZ', '600519.SH',
      '000858.SZ', '002415.SZ', '300059.SZ', '600036.SH', '000725.SZ'
    ];
    const stockNames = [
      '平安银行', '万科A', '爱尔眼科', '比亚迪', '贵州茅台',
      '五粮液', '汤臣倍健', '东方财富', '招商银行', '京东方A'
    ];

    const startDate = new Date(this.config.startDate);
    const endDate = new Date(this.config.endDate);
    
    // 为每天每只股票生成数据
    for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
      // 跳过周末
      if (d.getDay() === 0 || d.getDay() === 6) continue;
      
      const dateStr = d.toISOString().split('T')[0];
      
      stocks.forEach((stock, index) => {
        const basePrice = 10 + Math.random() * 100;
        const pctChg = (Math.random() - 0.5) * 20; // -10% to +10%
        
        const [chipConcentration, profitRatio] = generateRealisticChipMetrics(pctChg, 1 + Math.random() * 15, 0.5 + Math.random() * 3);

        data.push({
          stock_code: stock,
          stock_name: stockNames[index],
          price: basePrice * (1 + pctChg / 100),
          pct_chg: pctChg,
          turnover_rate: 1 + Math.random() * 15,
          volume_ratio: 0.5 + Math.random() * 3,
          market_cap: 50 + Math.random() * 500, // 亿元
          chip_concentration: chipConcentration,
          profit_ratio: profitRatio,
          trade_date: dateStr
        });
      });
    }
    
    return data;
  }

  // 按日期分组数据
  private groupDataByDate(data: StockData[]): Record<string, StockData[]> {
    return data.reduce((acc, item) => {
      if (!acc[item.trade_date]) {
        acc[item.trade_date] = [];
      }
      acc[item.trade_date].push(item);
      return acc;
    }, {} as Record<string, StockData[]>);
  }

  // 处理单日数据
  private async processDay(date: string, dayData: StockData[]): Promise<void> {
    // 1. 检查现有持仓是否需要卖出
    await this.checkExitSignals(date, dayData);
    
    // 2. 筛选买入候选股票
    const candidates = this.screenStocks(dayData);
    
    // 3. 执行买入信号
    await this.executeBuySignals(date, candidates);
    
    // 4. 更新投资组合价值
    this.updatePortfolioValue(date, dayData);
    
    // 5. 记录每日绩效
    this.recordDailyPerformance(date);
  }

  // 检查卖出信号
  private async checkExitSignals(date: string, dayData: StockData[]): Promise<void> {
    const dataMap = new Map(dayData.map(d => [d.stock_code, d]));
    
    for (let i = this.portfolio.positions.length - 1; i >= 0; i--) {
      const position = this.portfolio.positions[i];
      const currentData = dataMap.get(position.stock_code);
      
      if (!currentData) continue;
      
      const currentPrice = currentData.price;
      const returnRate = (currentPrice - position.entry_price) / position.entry_price;
      const holdingDays = this.calculateHoldingDays(position.entry_date, date);
      
      let shouldSell = false;
      let sellReason = '';
      
      // 止损检查
      if (returnRate <= -this.config.strategyParams.stopLoss / 100) {
        shouldSell = true;
        sellReason = '达到止损线';
      }
      // 止盈检查
      else if (returnRate >= this.config.strategyParams.takeProfit / 100) {
        shouldSell = true;
        sellReason = '达到止盈目标';
      }
      // 持仓天数检查
      else if (holdingDays >= this.config.strategyParams.holdingDays[1]) {
        shouldSell = true;
        sellReason = '达到最大持仓天数';
      }
      // 技术面恶化
      else if (currentData.pct_chg < -5 && currentData.volume_ratio < 0.5) {
        shouldSell = true;
        sellReason = '技术面恶化';
      }
      
      if (shouldSell) {
        await this.executeSellOrder(position, currentPrice, date, sellReason);
        this.portfolio.positions.splice(i, 1);
      }
    }
  }

  // 筛选股票
  private screenStocks(dayData: StockData[]): StockData[] {
    const { strategyParams } = this.config;
    
    return dayData.filter(stock => {
      // 基本条件筛选
      if (stock.price > strategyParams.maxStockPrice) return false;
      if (stock.market_cap > strategyParams.maxMarketCap) return false;
      if (stock.turnover_rate < strategyParams.minTurnoverRate) return false;
      if (stock.volume_ratio < strategyParams.minVolumeRatio) return false;
      if (stock.pct_chg < strategyParams.minDailyGain) return false;
      if (stock.chip_concentration < strategyParams.chipConcentrationThreshold) return false;
      if (stock.profit_ratio < strategyParams.profitRatioThreshold) return false;
      
      // 避免重复买入
      if (this.portfolio.positions.some(p => p.stock_code === stock.stock_code)) return false;
      
      return true;
    }).sort((a, b) => {
      // 按综合得分排序
      const scoreA = this.calculateStockScore(a);
      const scoreB = this.calculateStockScore(b);
      return scoreB - scoreA;
    });
  }

  // 计算股票得分
  private calculateStockScore(stock: StockData): number {
    let score = 0;
    
    // 涨幅得分
    score += Math.min(stock.pct_chg * 2, 20);
    
    // 成交量得分
    if (stock.volume_ratio > 2) score += 15;
    else if (stock.volume_ratio > 1.5) score += 10;
    
    // 换手率得分
    if (stock.turnover_rate > 5 && stock.turnover_rate < 15) score += 10;
    
    // 筹码集中度得分
    score += stock.chip_concentration * 20;
    
    // 获利盘比例得分
    if (stock.profit_ratio > 0.6) score += 15;
    else if (stock.profit_ratio > 0.5) score += 10;
    
    return score;
  }

  // 执行买入信号
  private async executeBuySignals(date: string, candidates: StockData[]): Promise<void> {
    const maxNewPositions = this.config.strategyParams.maxPositions - this.portfolio.positions.length;
    const selectedStocks = candidates.slice(0, maxNewPositions);
    
    for (const stock of selectedStocks) {
      // 计算买入数量（等权重分配）
      const availableCash = this.portfolio.cash;
      const positionValue = availableCash / (maxNewPositions + this.portfolio.positions.length);
      const quantity = Math.floor(positionValue / stock.price / 100) * 100; // 按手买入
      
      if (quantity >= 100) { // 至少一手
        await this.executeBuyOrder(stock, quantity, date);
      }
    }
  }

  // 执行买入订单
  private async executeBuyOrder(stock: StockData, quantity: number, date: string): Promise<void> {
    const amount = stock.price * quantity;
    const commission = amount * 0.0003; // 0.03% 手续费
    const totalCost = amount + commission;
    
    if (this.portfolio.cash >= totalCost) {
      // 更新现金
      this.portfolio.cash -= totalCost;
      
      // 添加持仓
      const position: Position = {
        stock_code: stock.stock_code,
        stock_name: stock.stock_name,
        entry_date: date,
        entry_price: stock.price,
        quantity: quantity,
        entry_amount: totalCost,
        entry_reason: this.generateBuyReason(stock),
        holding_days: 0
      };
      this.portfolio.positions.push(position);
      
      // 记录交易
      const trade: TradeRecord = {
        trade_id: `T${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
        stock_code: stock.stock_code,
        stock_name: stock.stock_name,
        action: 'buy',
        price: stock.price,
        quantity: quantity,
        amount: amount,
        trade_date: date,
        trade_reason: position.entry_reason,
        signal_strength: this.calculateStockScore(stock) / 100,
        cumulative_return: this.calculateCumulativeReturn(),
        portfolio_value: this.portfolio.totalValue
      };
      
      this.trades.push(trade);
      
      console.log(`买入: ${stock.stock_name} ${quantity}股 @${stock.price}`);
    }
  }

  // 执行卖出订单
  private async executeSellOrder(position: Position, currentPrice: number, date: string, reason: string): Promise<void> {
    const amount = currentPrice * position.quantity;
    const commission = amount * 0.0003;
    const netAmount = amount - commission;
    const profitLoss = netAmount - position.entry_amount;
    
    // 更新现金
    this.portfolio.cash += netAmount;
    
    // 记录交易
    const trade: TradeRecord = {
      trade_id: `T${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
      stock_code: position.stock_code,
      stock_name: position.stock_name,
      action: 'sell',
      price: currentPrice,
      quantity: position.quantity,
      amount: amount,
      trade_date: date,
      trade_reason: reason,
      signal_strength: 0.5,
      profit_loss: profitLoss,
      cumulative_return: this.calculateCumulativeReturn(),
      portfolio_value: this.portfolio.totalValue
    };
    
    this.trades.push(trade);
    
    console.log(`卖出: ${position.stock_name} ${position.quantity}股 @${currentPrice} 盈亏:${profitLoss.toFixed(2)}`);
  }

  // 生成买入原因
  private generateBuyReason(stock: StockData): string {
    const reasons = [];
    
    if (stock.pct_chg > 5) reasons.push('强势上涨');
    if (stock.volume_ratio > 2) reasons.push('放量突破');
    if (stock.chip_concentration > 0.7) reasons.push('筹码集中');
    if (stock.profit_ratio > 0.6) reasons.push('获利盘丰厚');
    if (stock.turnover_rate > 8) reasons.push('活跃换手');
    
    return reasons.join('+') || '符合选股条件';
  }

  // 更新投资组合价值
  private updatePortfolioValue(date: string, dayData: StockData[]): void {
    const dataMap = new Map(dayData.map(d => [d.stock_code, d]));
    
    let positionsValue = 0;
    for (const position of this.portfolio.positions) {
      const currentData = dataMap.get(position.stock_code);
      if (currentData) {
        positionsValue += currentData.price * position.quantity;
      }
    }
    
    this.portfolio.totalValue = this.portfolio.cash + positionsValue;
  }

  // 记录每日绩效
  private recordDailyPerformance(date: string): void {
    const dailyReturn = this.portfolio.totalValue / this.config.initialCapital - 1;
    const cumulativeReturn = this.calculateCumulativeReturn();
    
    this.dailyPerformance.push({
      backtest_id: this.backtestId,
      trade_date: date,
      portfolio_value: this.portfolio.totalValue,
      daily_return: dailyReturn,
      cumulative_return: cumulativeReturn,
      benchmark_return: 0, // 简化，实际应计算基准收益
      drawdown: this.calculateDrawdown(),
      positions_count: this.portfolio.positions.length,
      cash_balance: this.portfolio.cash,
      market_exposure: 1 - (this.portfolio.cash / this.portfolio.totalValue)
    });
  }

  // 计算累计收益率
  private calculateCumulativeReturn(): number {
    return (this.portfolio.totalValue - this.config.initialCapital) / this.config.initialCapital;
  }

  // 计算回撤
  private calculateDrawdown(): number {
    if (this.dailyPerformance.length === 0) return 0;
    
    const currentValue = this.portfolio.totalValue;
    const maxValue = Math.max(...this.dailyPerformance.map(p => p.portfolio_value), currentValue);
    
    return (maxValue - currentValue) / maxValue;
  }

  // 计算持仓天数
  private calculateHoldingDays(entryDate: string, currentDate: string): number {
    const entry = new Date(entryDate);
    const current = new Date(currentDate);
    return Math.floor((current.getTime() - entry.getTime()) / (1000 * 60 * 60 * 24));
  }

  // 计算最终指标
  private calculateFinalMetrics(): any {
    const totalReturn = this.calculateCumulativeReturn();
    const days = this.dailyPerformance.length;
    const annualReturn = Math.pow(1 + totalReturn, 365 / days) - 1;
    
    const profitableTrades = this.trades.filter(t => t.action === 'sell' && (t.profit_loss || 0) > 0);
    const losingTrades = this.trades.filter(t => t.action === 'sell' && (t.profit_loss || 0) < 0);
    const totalSellTrades = this.trades.filter(t => t.action === 'sell').length;
    
    const winRate = totalSellTrades > 0 ? profitableTrades.length / totalSellTrades : 0;
    const maxDrawdown = Math.max(...this.dailyPerformance.map(p => p.drawdown || 0), 0);
    
    // 计算夏普比率（简化版本）
    const returns = this.dailyPerformance.map(p => p.daily_return || 0);
    const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
    const returnStd = Math.sqrt(returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length);
    const sharpeRatio = returnStd > 0 ? (avgReturn / returnStd) * Math.sqrt(252) : 0;
    
    return {
      final_capital: this.portfolio.totalValue,
      total_return: totalReturn,
      annual_return: annualReturn,
      max_drawdown: maxDrawdown,
      sharpe_ratio: sharpeRatio,
      win_rate: winRate,
      total_trades: totalSellTrades,
      profitable_trades: profitableTrades.length,
      losing_trades: losingTrades.length,
      avg_trade_return: totalSellTrades > 0 ? this.trades
        .filter(t => t.action === 'sell')
        .reduce((sum, t) => sum + (t.profit_loss || 0), 0) / totalSellTrades : 0,
      max_single_trade_loss: Math.min(...this.trades.map(t => t.profit_loss || 0), 0),
      max_single_trade_profit: Math.max(...this.trades.map(t => t.profit_loss || 0), 0)
    };
  }

  // 保存回测结果到数据库
  private async saveBacktestResults(metrics: any): Promise<void> {
    try {
      // 保存主要回测结果
      const { error: resultError } = await this.supabase
        .from('backtest_results')
        .update({
          ...metrics,
          status: 'completed',
          strategy_params: this.config.strategyParams,
          performance_metrics: {
            total_days: this.dailyPerformance.length,
            trading_days: this.trades.length,
            avg_daily_return: this.dailyPerformance.reduce((sum, p) => sum + (p.daily_return || 0), 0) / this.dailyPerformance.length
          }
        })
        .eq('backtest_id', this.backtestId);
      
      if (resultError) throw resultError;
      
      // 保存交易记录
      if (this.trades.length > 0) {
        const { error: tradesError } = await this.supabase
          .from('backtest_trades')
          .insert(this.trades.map(trade => ({
            backtest_id: this.backtestId,
            ...trade
          })));
        
        if (tradesError) throw tradesError;
      }
      
      // 保存每日绩效
      if (this.dailyPerformance.length > 0) {
        const { error: performanceError } = await this.supabase
          .from('backtest_daily_performance')
          .insert(this.dailyPerformance);
        
        if (performanceError) throw performanceError;
      }
      
      console.log(`回测结果已保存: ${this.backtestId}`);
      
    } catch (error) {
      console.error('保存回测结果失败:', error);
      throw error;
    }
  }
}

// Edge Function 主入口
Deno.serve(async (req) => {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
  }

  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      {
        global: {
          headers: { Authorization: req.headers.get('Authorization')! },
        },
      }
    )

    const { action, data } = await req.json()

    switch (action) {
      case 'run_backtest': {
        const { backtestId, config } = data;
        
        // 创建回测引擎实例
        const engine = new BacktestEngine(supabaseClient, backtestId, config);
        
        // 运行回测
        const result = await engine.runBacktest();
        
        return new Response(
          JSON.stringify(result),
          { 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 200 
          }
        )
      }
      
      case 'get_backtest_detail': {
        const { backtestId } = data;
        
        // 获取回测基本信息
        const { data: backtestResult, error: backtestError } = await supabaseClient
          .from('backtest_results')
          .select('*')
          .eq('backtest_id', backtestId)
          .single();
        
        if (backtestError) throw backtestError;
        
        // 获取交易记录
        const { data: trades, error: tradesError } = await supabaseClient
          .from('backtest_trades')
          .select('*')
          .eq('backtest_id', backtestId)
          .order('trade_date', { ascending: true });
        
        if (tradesError) throw tradesError;
        
        // 获取每日绩效
        const { data: dailyPerformance, error: performanceError } = await supabaseClient
          .from('backtest_daily_performance')
          .select('*')
          .eq('backtest_id', backtestId)
          .order('trade_date', { ascending: true });
        
        if (performanceError) throw performanceError;
        
        return new Response(
          JSON.stringify({
            success: true,
            backtest: backtestResult,
            trades: trades || [],
            dailyPerformance: dailyPerformance || []
          }),
          { 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 200 
          }
        )
      }
      
      default:
        return new Response(
          JSON.stringify({ error: '不支持的操作' }),
          { 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 400 
          }
        )
    }

  } catch (error) {
    console.error('处理请求时发生错误:', error)
    return new Response(
      JSON.stringify({ 
        error: '服务器内部错误',
        details: error.message 
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500 
      }
    )
  }
})