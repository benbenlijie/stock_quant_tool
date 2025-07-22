"""
应用配置模块
管理环境变量、数据库连接、API密钥等配置信息
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """应用设置类"""
    
    # Tushare API
    tushare_token: str = Field(..., env="TUSHARE_TOKEN")
    
    # 数据库配置
    postgres_host: str = Field("localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(5432, env="POSTGRES_PORT")
    postgres_db: str = Field("stock_analysis", env="POSTGRES_DB")
    postgres_user: str = Field("postgres", env="POSTGRES_USER")
    postgres_password: str = Field("postgres123", env="POSTGRES_PASSWORD")
    
    # Redis配置
    redis_host: str = Field("localhost", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    redis_db: int = Field(0, env="REDIS_DB")
    
    # API服务配置
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    debug: bool = Field(True, env="DEBUG")
    
    # 时区配置
    timezone: str = Field("Asia/Shanghai", env="TIMEZONE")
    
    # 策略参数默认值
    max_market_cap: float = Field(50, env="MAX_MARKET_CAP")  # 亿元
    min_turnover_rate: float = Field(10, env="MIN_TURNOVER_RATE")  # %
    min_volume_ratio: float = Field(2, env="MIN_VOLUME_RATIO")
    min_daily_gain: float = Field(9, env="MIN_DAILY_GAIN")  # %
    max_stock_price: float = Field(30, env="MAX_STOCK_PRICE")  # 元
    chip_concentration_threshold: float = Field(0.65, env="CHIP_CONCENTRATION_THRESHOLD")
    profit_ratio_threshold: float = Field(0.5, env="PROFIT_RATIO_THRESHOLD")
    
    # 风控参数
    stop_loss_ratio: float = Field(0.1, env="STOP_LOSS_RATIO")  # 10%
    max_drawdown: float = Field(0.2, env="MAX_DRAWDOWN")  # 20%
    max_position_size: float = Field(0.5, env="MAX_POSITION_SIZE")  # 50%
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def database_url(self) -> str:
        """获取数据库连接URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def redis_url(self) -> str:
        """获取Redis连接URL"""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

# 全局设置实例
settings = Settings()

# 数据库表名常量
class TableNames:
    """数据库表名常量"""
    STOCKS = "stocks"
    DAILY_DATA = "daily_data"
    DAILY_BASIC = "daily_basic"
    LIMIT_LIST = "limit_list"
    MONEY_FLOW = "money_flow"
    TOP_LIST = "top_list"
    TOP_INST = "top_inst"
    STRATEGY_RESULTS = "strategy_results"
    BACKTEST_RESULTS = "backtest_results"
    USER_SETTINGS = "user_settings"

# API响应常量
class ResponseCode:
    """API响应码常量"""
    SUCCESS = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_ERROR = 500

# 策略评分权重
class StrategyWeights:
    """策略评分权重配置"""
    VOLUME_PRICE = 0.30  # 量价突破 30%
    CHIP_CONCENTRATION = 0.25  # 筹码集中度 25%
    DRAGON_TIGER = 0.20  # 龙虎榜 20%
    THEME_HEAT = 0.15  # 题材热度 15%
    MONEY_FLOW = 0.10  # 资金流向 10%
