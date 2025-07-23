-- 回测主表
CREATE TABLE IF NOT EXISTS backtest_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    backtest_id VARCHAR(50) UNIQUE NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    strategy_name VARCHAR(100) NOT NULL DEFAULT '趋势跟踪策略',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(15,2) DEFAULT 1000000.00,
    final_capital DECIMAL(15,2),
    total_return DECIMAL(10,6),
    annual_return DECIMAL(10,6),
    max_drawdown DECIMAL(10,6),
    sharpe_ratio DECIMAL(10,4),
    win_rate DECIMAL(10,6),
    total_trades INTEGER DEFAULT 0,
    profitable_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    avg_trade_return DECIMAL(10,6),
    max_single_trade_loss DECIMAL(10,6),
    max_single_trade_profit DECIMAL(10,6),
    status VARCHAR(20) DEFAULT 'running',
    data_source VARCHAR(20) DEFAULT 'real_backtest',
    strategy_params JSONB,
    performance_metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 回测交易记录表
CREATE TABLE IF NOT EXISTS backtest_trades (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    backtest_id VARCHAR(50) REFERENCES backtest_results(backtest_id) ON DELETE CASCADE,
    trade_id VARCHAR(50) NOT NULL,
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(50) NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('buy', 'sell')),
    price DECIMAL(10,4) NOT NULL,
    quantity INTEGER NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    commission DECIMAL(10,2) DEFAULT 0,
    trade_date TIMESTAMP WITH TIME ZONE NOT NULL,
    trade_reason TEXT,
    signal_strength DECIMAL(5,4),
    market_condition VARCHAR(50),
    position_size_ratio DECIMAL(10,6),
    profit_loss DECIMAL(15,2),
    cumulative_return DECIMAL(10,6),
    portfolio_value DECIMAL(15,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 回测每日绩效表
CREATE TABLE IF NOT EXISTS backtest_daily_performance (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    backtest_id VARCHAR(50) REFERENCES backtest_results(backtest_id) ON DELETE CASCADE,
    trade_date DATE NOT NULL,
    portfolio_value DECIMAL(15,2) NOT NULL,
    daily_return DECIMAL(10,6),
    cumulative_return DECIMAL(10,6),
    benchmark_return DECIMAL(10,6),
    drawdown DECIMAL(10,6),
    positions_count INTEGER DEFAULT 0,
    cash_balance DECIMAL(15,2),
    market_exposure DECIMAL(10,6),
    sector_allocation JSONB,
    risk_metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(backtest_id, trade_date)
);

-- 回测持仓表
CREATE TABLE IF NOT EXISTS backtest_positions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    backtest_id VARCHAR(50) REFERENCES backtest_results(backtest_id) ON DELETE CASCADE,
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(50) NOT NULL,
    entry_date DATE NOT NULL,
    exit_date DATE,
    entry_price DECIMAL(10,4) NOT NULL,
    exit_price DECIMAL(10,4),
    quantity INTEGER NOT NULL,
    entry_amount DECIMAL(15,2) NOT NULL,
    exit_amount DECIMAL(15,2),
    holding_days INTEGER,
    profit_loss DECIMAL(15,2),
    profit_loss_ratio DECIMAL(10,6),
    max_profit DECIMAL(15,2),
    max_loss DECIMAL(15,2),
    entry_reason TEXT,
    exit_reason TEXT,
    position_status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 回测策略信号表
CREATE TABLE IF NOT EXISTS backtest_signals (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    backtest_id VARCHAR(50) REFERENCES backtest_results(backtest_id) ON DELETE CASCADE,
    signal_date DATE NOT NULL,
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(50) NOT NULL,
    signal_type VARCHAR(20) NOT NULL, -- buy, sell, hold
    signal_strength DECIMAL(5,4),
    signal_reason TEXT,
    technical_indicators JSONB,
    fundamental_metrics JSONB,
    market_sentiment JSONB,
    executed BOOLEAN DEFAULT FALSE,
    execution_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_backtest_results_user_id ON backtest_results(user_id);
CREATE INDEX IF NOT EXISTS idx_backtest_results_created_at ON backtest_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_backtest_trades_backtest_id ON backtest_trades(backtest_id);
CREATE INDEX IF NOT EXISTS idx_backtest_trades_trade_date ON backtest_trades(trade_date);
CREATE INDEX IF NOT EXISTS idx_backtest_daily_performance_backtest_id ON backtest_daily_performance(backtest_id);
CREATE INDEX IF NOT EXISTS idx_backtest_daily_performance_date ON backtest_daily_performance(trade_date);
CREATE INDEX IF NOT EXISTS idx_backtest_positions_backtest_id ON backtest_positions(backtest_id);
CREATE INDEX IF NOT EXISTS idx_backtest_signals_backtest_id ON backtest_signals(backtest_id);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_backtest_results_updated_at BEFORE UPDATE ON backtest_results
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_backtest_positions_updated_at BEFORE UPDATE ON backtest_positions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 启用行级安全策略
ALTER TABLE backtest_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE backtest_trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE backtest_daily_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE backtest_positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE backtest_signals ENABLE ROW LEVEL SECURITY;

-- 创建策略
CREATE POLICY "Users can view their own backtest results" ON backtest_results
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own backtest results" ON backtest_results
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own backtest results" ON backtest_results
    FOR UPDATE USING (auth.uid() = user_id);

-- 为其他表创建类似的策略
CREATE POLICY "Users can access their backtest trades" ON backtest_trades
    FOR ALL USING (
        backtest_id IN (
            SELECT backtest_id FROM backtest_results WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can access their backtest performance" ON backtest_daily_performance
    FOR ALL USING (
        backtest_id IN (
            SELECT backtest_id FROM backtest_results WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can access their backtest positions" ON backtest_positions
    FOR ALL USING (
        backtest_id IN (
            SELECT backtest_id FROM backtest_results WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can access their backtest signals" ON backtest_signals
    FOR ALL USING (
        backtest_id IN (
            SELECT backtest_id FROM backtest_results WHERE user_id = auth.uid()
        )
    );