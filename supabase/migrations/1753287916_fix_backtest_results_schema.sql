-- Migration to fix backtest_results table schema
-- Created at: 1753287916

-- First, let's check if the table exists and drop it if needed
DROP TABLE IF EXISTS backtest_results CASCADE;

-- Recreate the backtest_results table with the correct schema
CREATE TABLE backtest_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backtest_id VARCHAR(100) UNIQUE NOT NULL,
    start_date DATE,  -- Allow null values temporarily
    strategy_name VARCHAR(100) NOT NULL DEFAULT '未知策略',
    end_date DATE,
    initial_capital DECIMAL(15,2) DEFAULT 1000000.00,
    total_return DECIMAL(8,4),
    annual_return DECIMAL(8,4),
    max_drawdown DECIMAL(8,4),
    sharpe_ratio DECIMAL(8,4),
    win_rate DECIMAL(8,4),
    total_trades INTEGER DEFAULT 0,
    avg_holding_days DECIMAL(6,2) DEFAULT 0,
    parameters JSONB,
    status VARCHAR(20) DEFAULT 'running',
    data_source VARCHAR(50) DEFAULT 'real_backtest',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create an index for better performance
CREATE INDEX idx_backtest_results_backtest_id ON backtest_results(backtest_id);
CREATE INDEX idx_backtest_results_status ON backtest_results(status);
CREATE INDEX idx_backtest_results_created_at ON backtest_results(created_at);

-- Add a trigger to update the updated_at field automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_backtest_results_updated_at 
    BEFORE UPDATE ON backtest_results 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();