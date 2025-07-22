"""
数据库连接管理
"""

import asyncpg
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

# 全局连接池
pool: Optional[asyncpg.Pool] = None

async def get_database_pool() -> asyncpg.Pool:
    """获取数据库连接池"""
    global pool
    if pool is None:
        pool = await create_database_pool()
    return pool

async def create_database_pool() -> asyncpg.Pool:
    """创建数据库连接池"""
    try:
        pool = await asyncpg.create_pool(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
            database=settings.postgres_db,
            min_size=5,
            max_size=20,
            command_timeout=30
        )
        logger.info(f"数据库连接池创建成功: {settings.postgres_host}:{settings.postgres_port}")
        return pool
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise

async def init_db():
    """初始化数据库，创建所有表"""
    pool = await get_database_pool()
    
    # 创建表的SQL语句
    create_tables_sql = """
    -- 股票基础信息表
    CREATE TABLE IF NOT EXISTS stocks (
        ts_code VARCHAR(10) PRIMARY KEY,
        symbol VARCHAR(10) NOT NULL,
        name VARCHAR(50) NOT NULL,
        area VARCHAR(20),
        industry VARCHAR(50),
        market VARCHAR(10),
        list_date DATE,
        is_hs VARCHAR(1),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- 日线数据表
    CREATE TABLE IF NOT EXISTS daily_data (
        id SERIAL PRIMARY KEY,
        ts_code VARCHAR(10) NOT NULL,
        trade_date DATE NOT NULL,
        open DECIMAL(10,3),
        high DECIMAL(10,3),
        low DECIMAL(10,3),
        close DECIMAL(10,3),
        pre_close DECIMAL(10,3),
        change DECIMAL(10,3),
        pct_chg DECIMAL(8,4),
        vol BIGINT,
        amount DECIMAL(15,3),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(ts_code, trade_date),
        FOREIGN KEY (ts_code) REFERENCES stocks(ts_code)
    );
    
    -- 每日基本面数据表
    CREATE TABLE IF NOT EXISTS daily_basic (
        id SERIAL PRIMARY KEY,
        ts_code VARCHAR(10) NOT NULL,
        trade_date DATE NOT NULL,
        close DECIMAL(10,3),
        turnover_rate DECIMAL(8,4),
        volume_ratio DECIMAL(8,4),
        pe DECIMAL(10,4),
        pb DECIMAL(8,4),
        ps DECIMAL(8,4),
        dv_ratio DECIMAL(8,4),
        dv_ttm DECIMAL(8,4),
        total_share DECIMAL(15,2),
        float_share DECIMAL(15,2),
        free_share DECIMAL(15,2),
        total_mv DECIMAL(15,2),
        circ_mv DECIMAL(15,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(ts_code, trade_date),
        FOREIGN KEY (ts_code) REFERENCES stocks(ts_code)
    );
    
    -- 涨跌停统计表
    CREATE TABLE IF NOT EXISTS limit_list (
        id SERIAL PRIMARY KEY,
        ts_code VARCHAR(10) NOT NULL,
        trade_date DATE NOT NULL,
        limit VARCHAR(1) NOT NULL,  -- U=涨停, D=跌停
        fd_amount DECIMAL(15,2),
        first_time TIME,
        last_time TIME,
        open_times INTEGER,
        strth DECIMAL(8,4),
        limit_times INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(ts_code, trade_date),
        FOREIGN KEY (ts_code) REFERENCES stocks(ts_code)
    );
    
    -- 资金流向表
    CREATE TABLE IF NOT EXISTS money_flow (
        id SERIAL PRIMARY KEY,
        ts_code VARCHAR(10) NOT NULL,
        trade_date DATE NOT NULL,
        buy_sm_vol BIGINT,
        buy_sm_amount DECIMAL(15,2),
        sell_sm_vol BIGINT,
        sell_sm_amount DECIMAL(15,2),
        buy_md_vol BIGINT,
        buy_md_amount DECIMAL(15,2),
        sell_md_vol BIGINT,
        sell_md_amount DECIMAL(15,2),
        buy_lg_vol BIGINT,
        buy_lg_amount DECIMAL(15,2),
        sell_lg_vol BIGINT,
        sell_lg_amount DECIMAL(15,2),
        buy_elg_vol BIGINT,
        buy_elg_amount DECIMAL(15,2),
        sell_elg_vol BIGINT,
        sell_elg_amount DECIMAL(15,2),
        net_mf_vol BIGINT,
        net_mf_amount DECIMAL(15,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(ts_code, trade_date),
        FOREIGN KEY (ts_code) REFERENCES stocks(ts_code)
    );
    
    -- 龙虎榜数据表
    CREATE TABLE IF NOT EXISTS top_list (
        id SERIAL PRIMARY KEY,
        trade_date DATE NOT NULL,
        ts_code VARCHAR(10) NOT NULL,
        name VARCHAR(50),
        close DECIMAL(10,3),
        pct_chg DECIMAL(8,4),
        turnover_rate DECIMAL(8,4),
        amount DECIMAL(15,2),
        l_sell DECIMAL(15,2),
        l_buy DECIMAL(15,2),
        l_amount DECIMAL(15,2),
        net_amount DECIMAL(15,2),
        net_rate DECIMAL(8,4),
        amount_rate DECIMAL(8,4),
        float_values DECIMAL(15,2),
        reason VARCHAR(200),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(ts_code, trade_date),
        FOREIGN KEY (ts_code) REFERENCES stocks(ts_code)
    );
    
    -- 龙虎榜机构数据表
    CREATE TABLE IF NOT EXISTS top_inst (
        id SERIAL PRIMARY KEY,
        trade_date DATE NOT NULL,
        ts_code VARCHAR(10) NOT NULL,
        exalter VARCHAR(100),
        buy DECIMAL(15,2),
        buy_rate DECIMAL(8,4),
        sell DECIMAL(15,2),
        sell_rate DECIMAL(8,4),
        net_buy DECIMAL(15,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (ts_code) REFERENCES stocks(ts_code)
    );
    
    -- 策略计算结果表
    CREATE TABLE IF NOT EXISTS strategy_results (
        id SERIAL PRIMARY KEY,
        ts_code VARCHAR(10) NOT NULL,
        trade_date DATE NOT NULL,
        total_score DECIMAL(8,4),
        volume_price_score DECIMAL(8,4),
        chip_score DECIMAL(8,4),
        dragon_tiger_score DECIMAL(8,4),
        theme_score DECIMAL(8,4),
        money_flow_score DECIMAL(8,4),
        rank_position INTEGER,
        is_candidate BOOLEAN DEFAULT FALSE,
        reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(ts_code, trade_date),
        FOREIGN KEY (ts_code) REFERENCES stocks(ts_code)
    );
    
    -- 回测结果表
    CREATE TABLE IF NOT EXISTS backtest_results (
        id SERIAL PRIMARY KEY,
        strategy_name VARCHAR(100) NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        total_return DECIMAL(8,4),
        annual_return DECIMAL(8,4),
        max_drawdown DECIMAL(8,4),
        sharpe_ratio DECIMAL(8,4),
        win_rate DECIMAL(8,4),
        total_trades INTEGER,
        avg_holding_days DECIMAL(6,2),
        parameters JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- 用户设置表
    CREATE TABLE IF NOT EXISTS user_settings (
        id SERIAL PRIMARY KEY,
        setting_key VARCHAR(50) UNIQUE NOT NULL,
        setting_value TEXT,
        description TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- 创建索引
    CREATE INDEX IF NOT EXISTS idx_daily_data_trade_date ON daily_data(trade_date);
    CREATE INDEX IF NOT EXISTS idx_daily_data_ts_code ON daily_data(ts_code);
    CREATE INDEX IF NOT EXISTS idx_daily_basic_trade_date ON daily_basic(trade_date);
    CREATE INDEX IF NOT EXISTS idx_limit_list_trade_date ON limit_list(trade_date);
    CREATE INDEX IF NOT EXISTS idx_money_flow_trade_date ON money_flow(trade_date);
    CREATE INDEX IF NOT EXISTS idx_top_list_trade_date ON top_list(trade_date);
    CREATE INDEX IF NOT EXISTS idx_strategy_results_trade_date ON strategy_results(trade_date);
    CREATE INDEX IF NOT EXISTS idx_strategy_results_score ON strategy_results(total_score DESC);
    """
    
    async with pool.acquire() as conn:
        try:
            await conn.execute(create_tables_sql)
            logger.info("数据库表创建完成")
            
            # 初始化默认设置
            await _init_default_settings(conn)
            
        except Exception as e:
            logger.error(f"数据库表创建失败: {e}")
            raise

async def _init_default_settings(conn):
    """初始化默认设置"""
    default_settings = [
        ('max_market_cap', str(settings.max_market_cap), '最大流通市值(亿元)'),
        ('min_turnover_rate', str(settings.min_turnover_rate), '最小换手率(%)'),
        ('min_volume_ratio', str(settings.min_volume_ratio), '最小量比'),
        ('min_daily_gain', str(settings.min_daily_gain), '最小日涨幅(%)'),
        ('max_stock_price', str(settings.max_stock_price), '最大股价(元)'),
        ('chip_concentration_threshold', str(settings.chip_concentration_threshold), '筹码集中度阈值'),
        ('profit_ratio_threshold', str(settings.profit_ratio_threshold), '获利盘比例阈值')
    ]
    
    for key, value, desc in default_settings:
        await conn.execute(
            """
            INSERT INTO user_settings (setting_key, setting_value, description)
            VALUES ($1, $2, $3)
            ON CONFLICT (setting_key) DO NOTHING
            """,
            key, value, desc
        )
    
    logger.info("默认设置初始化完成")

async def close_db():
    """关闭数据库连接池"""
    global pool
    if pool:
        await pool.close()
        pool = None
        logger.info("数据库连接池已关闭")
