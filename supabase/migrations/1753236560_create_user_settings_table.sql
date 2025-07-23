-- Migration: create_user_settings_table
-- Created at: 1753236560

-- 创建用户设置表
CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT NOT NULL,
    setting_type VARCHAR(50) DEFAULT 'string',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_user_settings_key ON user_settings(setting_key);

-- 插入默认策略参数
INSERT INTO user_settings (setting_key, setting_value, setting_type, description) VALUES
('max_market_cap', '100', 'number', '最大市值(亿元)'),
('min_turnover_rate', '3', 'number', '最低换手率(%)'),
('min_volume_ratio', '1.2', 'number', '最低量比'),
('min_daily_gain', '3', 'number', '最低日涨幅(%)'),
('max_stock_price', '200', 'number', '最高股价(元)'),
('chip_concentration_threshold', '0.3', 'number', '筹码集中度阈值'),
('profit_ratio_threshold', '0.5', 'number', '获利盘比例阈值'),
('volume_price_weight', '30', 'number', '量价权重(%)'),
('chip_weight', '25', 'number', '筹码权重(%)'),
('dragon_tiger_weight', '20', 'number', '龙虎榜权重(%)'),
('theme_weight', '15', 'number', '题材权重(%)'),
('money_flow_weight', '10', 'number', '资金流权重(%)')
ON CONFLICT (setting_key) DO NOTHING;;