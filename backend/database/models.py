"""
数据模型定义
包含所有数据库表对应的Pydantic模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime, time
from decimal import Decimal

class StockInfo(BaseModel):
    """股票基础信息模型"""
    ts_code: str = Field(..., description="股票代码")
    symbol: str = Field(..., description="股票简称")
    name: str = Field(..., description="股票名称")
    area: Optional[str] = Field(None, description="地域")
    industry: Optional[str] = Field(None, description="行业")
    market: Optional[str] = Field(None, description="市场类型")
    list_date: Optional[date] = Field(None, description="上市日期")
    is_hs: Optional[str] = Field(None, description="是否沪深港通")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class DailyData(BaseModel):
    """日线数据模型"""
    ts_code: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="交易日期")
    open: Optional[Decimal] = Field(None, description="开盘价")
    high: Optional[Decimal] = Field(None, description="最高价")
    low: Optional[Decimal] = Field(None, description="最低价")
    close: Optional[Decimal] = Field(None, description="收盘价")
    pre_close: Optional[Decimal] = Field(None, description="昨收价")
    change: Optional[Decimal] = Field(None, description="涨跌额")
    pct_chg: Optional[Decimal] = Field(None, description="涨跌幅")
    vol: Optional[int] = Field(None, description="成交量")
    amount: Optional[Decimal] = Field(None, description="成交额")
    created_at: Optional[datetime] = Field(None, description="创建时间")

class DailyBasic(BaseModel):
    """每日基本面数据模型"""
    ts_code: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="交易日期")
    close: Optional[Decimal] = Field(None, description="收盘价")
    turnover_rate: Optional[Decimal] = Field(None, description="换手率")
    volume_ratio: Optional[Decimal] = Field(None, description="量比")
    pe: Optional[Decimal] = Field(None, description="市盈率")
    pb: Optional[Decimal] = Field(None, description="市净率")
    ps: Optional[Decimal] = Field(None, description="市销率")
    dv_ratio: Optional[Decimal] = Field(None, description="股息率")
    dv_ttm: Optional[Decimal] = Field(None, description="股息率TTM")
    total_share: Optional[Decimal] = Field(None, description="总股本")
    float_share: Optional[Decimal] = Field(None, description="流通股本")
    free_share: Optional[Decimal] = Field(None, description="自由流通股本")
    total_mv: Optional[Decimal] = Field(None, description="总市值")
    circ_mv: Optional[Decimal] = Field(None, description="流通市值")
    created_at: Optional[datetime] = Field(None, description="创建时间")

class LimitListData(BaseModel):
    """涨跌停统计模型"""
    ts_code: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="交易日期")
    limit: str = Field(..., description="涨跌停标识")
    fd_amount: Optional[Decimal] = Field(None, description="封单金额")
    first_time: Optional[time] = Field(None, description="首次封板时间")
    last_time: Optional[time] = Field(None, description="最后封板时间")
    open_times: Optional[int] = Field(None, description="炸板次数")
    strth: Optional[Decimal] = Field(None, description="封单强度")
    limit_times: Optional[int] = Field(None, description="连板数")
    created_at: Optional[datetime] = Field(None, description="创建时间")

class MoneyFlowData(BaseModel):
    """资金流向模型"""
    ts_code: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="交易日期")
    buy_sm_vol: Optional[int] = Field(None, description="小单买入量")
    buy_sm_amount: Optional[Decimal] = Field(None, description="小单买入额")
    sell_sm_vol: Optional[int] = Field(None, description="小单卖出量")
    sell_sm_amount: Optional[Decimal] = Field(None, description="小单卖出额")
    buy_md_vol: Optional[int] = Field(None, description="中单买入量")
    buy_md_amount: Optional[Decimal] = Field(None, description="中单买入额")
    sell_md_vol: Optional[int] = Field(None, description="中单卖出量")
    sell_md_amount: Optional[Decimal] = Field(None, description="中单卖出额")
    buy_lg_vol: Optional[int] = Field(None, description="大单买入量")
    buy_lg_amount: Optional[Decimal] = Field(None, description="大单买入额")
    sell_lg_vol: Optional[int] = Field(None, description="大单卖出量")
    sell_lg_amount: Optional[Decimal] = Field(None, description="大单卖出额")
    buy_elg_vol: Optional[int] = Field(None, description="特大单买入量")
    buy_elg_amount: Optional[Decimal] = Field(None, description="特大单买入额")
    sell_elg_vol: Optional[int] = Field(None, description="特大单卖出量")
    sell_elg_amount: Optional[Decimal] = Field(None, description="特大单卖出额")
    net_mf_vol: Optional[int] = Field(None, description="净流入量")
    net_mf_amount: Optional[Decimal] = Field(None, description="净流入额")
    created_at: Optional[datetime] = Field(None, description="创建时间")

class TopListData(BaseModel):
    """龙虎榜数据模型"""
    trade_date: date = Field(..., description="交易日期")
    ts_code: str = Field(..., description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")
    close: Optional[Decimal] = Field(None, description="收盘价")
    pct_chg: Optional[Decimal] = Field(None, description="涨跌幅")
    turnover_rate: Optional[Decimal] = Field(None, description="换手率")
    amount: Optional[Decimal] = Field(None, description="成交额")
    l_sell: Optional[Decimal] = Field(None, description="龙虎榜卖出额")
    l_buy: Optional[Decimal] = Field(None, description="龙虎榜买入额")
    l_amount: Optional[Decimal] = Field(None, description="龙虎榜成交额")
    net_amount: Optional[Decimal] = Field(None, description="净买入额")
    net_rate: Optional[Decimal] = Field(None, description="净买额占比")
    amount_rate: Optional[Decimal] = Field(None, description="成交额占比")
    float_values: Optional[Decimal] = Field(None, description="流通市值")
    reason: Optional[str] = Field(None, description="上榜原因")
    created_at: Optional[datetime] = Field(None, description="创建时间")

class TopInstData(BaseModel):
    """龙虎榜机构数据模型"""
    trade_date: date = Field(..., description="交易日期")
    ts_code: str = Field(..., description="股票代码")
    exalter: Optional[str] = Field(None, description="营业部名称")
    buy: Optional[Decimal] = Field(None, description="买入额")
    buy_rate: Optional[Decimal] = Field(None, description="买入占比")
    sell: Optional[Decimal] = Field(None, description="卖出额")
    sell_rate: Optional[Decimal] = Field(None, description="卖出占比")
    net_buy: Optional[Decimal] = Field(None, description="净买入额")
    created_at: Optional[datetime] = Field(None, description="创建时间")

class StrategyResult(BaseModel):
    """策略计算结果模型"""
    ts_code: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="交易日期")
    total_score: Decimal = Field(..., description="综合评分")
    volume_price_score: Decimal = Field(..., description="量价突破得分")
    chip_score: Decimal = Field(..., description="筹码集中度得分")
    dragon_tiger_score: Decimal = Field(..., description="龙虎榜得分")
    theme_score: Decimal = Field(..., description="题材热度得分")
    money_flow_score: Decimal = Field(..., description="资金流向得分")
    rank_position: Optional[int] = Field(None, description="排名")
    is_candidate: bool = Field(False, description="是否为候选股")
    reason: Optional[str] = Field(None, description="选中/排除原因")
    created_at: Optional[datetime] = Field(None, description="创建时间")

class BacktestResult(BaseModel):
    """回测结果模型"""
    strategy_name: str = Field(..., description="策略名称")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    total_return: Decimal = Field(..., description="总收益率")
    annual_return: Decimal = Field(..., description="年化收益率")
    max_drawdown: Decimal = Field(..., description="最大回撤")
    sharpe_ratio: Decimal = Field(..., description="夏普比率")
    win_rate: Decimal = Field(..., description="胜率")
    total_trades: int = Field(..., description="交易次数")
    avg_holding_days: Decimal = Field(..., description="平均持仓天数")
    parameters: dict = Field(..., description="策略参数")
    created_at: Optional[datetime] = Field(None, description="创建时间")

class UserSetting(BaseModel):
    """用户设置模型"""
    setting_key: str = Field(..., description="设置键")
    setting_value: str = Field(..., description="设置值")
    description: Optional[str] = Field(None, description="描述")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

# API响应模型
class ApiResponse(BaseModel):
    """统一API响应模型"""
    code: int = Field(..., description="响应码")
    message: str = Field(..., description="响应消息")
    data: Optional[dict] = Field(None, description="响应数据")
    timestamp: Optional[datetime] = Field(None, description="响应时间")

class CandidateStock(BaseModel):
    """候选股票模型"""
    ts_code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    close: Decimal = Field(..., description="收盘价")
    pct_chg: Decimal = Field(..., description="涨跌幅")
    turnover_rate: Decimal = Field(..., description="换手率")
    volume_ratio: Decimal = Field(..., description="量比")
    total_score: Decimal = Field(..., description="综合评分")
    rank_position: int = Field(..., description="排名")
    reason: str = Field(..., description="选中原因")
    market_cap: Optional[Decimal] = Field(None, description="流通市值")
    amount: Optional[Decimal] = Field(None, description="成交额")

class DashboardData(BaseModel):
    """仪表盘数据模型"""
    market_sentiment: dict = Field(..., description="市场情绪数据")
    today_candidates: List[CandidateStock] = Field(..., description="今日候选股")
    strategy_stats: dict = Field(..., description="策略统计")
    recent_performance: dict = Field(..., description="近期表现")
    update_time: datetime = Field(..., description="更新时间")
