"""
Tushare API客户端
负责与T ushare API的所有交互，包括数据获取、错误处理和重试机制
"""

import tushare as ts
import pandas as pd
import logging
import asyncio
import time
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
from decimal import Decimal
import functools

from config import settings
from database.models import (
    StockInfo, DailyData, DailyBasic, LimitListData,
    MoneyFlowData, TopListData, TopInstData
)

logger = logging.getLogger(__name__)

def api_retry(max_retries: int = 3, delay: float = 1.0):
    """
API调用重试装饰器
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"API调用失败，已重试{max_retries}次: {func.__name__} - {e}")
                        raise e
                    
                    wait_time = delay * (2 ** attempt)
                    logger.warning(f"API调用失败，{wait_time}秒后重试: {func.__name__} - {e}")
                    await asyncio.sleep(wait_time)
            return None
        return wrapper
    return decorator

class TushareClient:
    """
Tushare API客户端类
    """
    
    def __init__(self):
        """初始化Tushare客户端"""
        self.token = settings.tushare_token
        self.pro = None
        self._init_client()
        
        # API调用频率控制
        self.last_call_time = 0
        self.min_interval = 0.3  # 最小调用间隔(秒)
    
    def _init_client(self):
        """初始化Tushare Pro客户端"""
        try:
            ts.set_token(self.token)
            self.pro = ts.pro_api()
            logger.info("Tushare Pro API初始化成功")
        except Exception as e:
            logger.error(f"Tushare Pro API初始化失败: {e}")
            raise
    
    async def _wait_for_rate_limit(self):
        """等待API调用频率限制"""
        current_time = time.time()
        elapsed = current_time - self.last_call_time
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            await asyncio.sleep(wait_time)
        self.last_call_time = time.time()
    
    @api_retry(max_retries=3, delay=1.0)
    async def get_stock_basic(self) -> List[StockInfo]:
        """获取股票基础信息"""
        await self._wait_for_rate_limit()
        
        def _fetch_stock_basic():
            # 主板 + 中小板 + 创业板
            df = self.pro.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry,market,list_date,is_hs'
            )
            return df
        
        try:
            # 在线程池中执行同步操作
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, _fetch_stock_basic)
            
            stocks = []
            for _, row in df.iterrows():
                stock = StockInfo(
                    ts_code=row['ts_code'],
                    symbol=row['symbol'],
                    name=row['name'],
                    area=row['area'],
                    industry=row['industry'],
                    market=row['market'],
                    list_date=pd.to_datetime(row['list_date']).date() if pd.notna(row['list_date']) else None,
                    is_hs=row['is_hs']
                )
                stocks.append(stock)
            
            logger.info(f"获取到 {len(stocks)} 只股票基础信息")
            return stocks
            
        except Exception as e:
            logger.error(f"获取股票基础信息失败: {e}")
            raise
    
    @api_retry(max_retries=3, delay=1.0)
    async def get_daily_data(self, trade_date: Optional[str] = None, 
                           ts_codes: Optional[List[str]] = None) -> List[DailyData]:
        """获取日线数据"""
        await self._wait_for_rate_limit()
        
        def _fetch_daily_data():
            if ts_codes:
                # 指定股票代码
                all_data = []
                # 分批获取，每次50只
                for i in range(0, len(ts_codes), 50):
                    batch_codes = ts_codes[i:i+50]
                    df = self.pro.daily(
                        ts_code=','.join(batch_codes),
                        trade_date=trade_date,
                        fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount'
                    )
                    all_data.append(df)
                    time.sleep(0.3)  # 避免频率限制
                
                if all_data:
                    df = pd.concat(all_data, ignore_index=True)
                else:
                    df = pd.DataFrame()
            else:
                # 获取所有股票的指定日期数据
                df = self.pro.daily(
                    trade_date=trade_date,
                    fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount'
                )
            return df
        
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, _fetch_daily_data)
            
            daily_data = []
            for _, row in df.iterrows():
                data = DailyData(
                    ts_code=row['ts_code'],
                    trade_date=pd.to_datetime(row['trade_date']).date(),
                    open=Decimal(str(row['open'])) if pd.notna(row['open']) else None,
                    high=Decimal(str(row['high'])) if pd.notna(row['high']) else None,
                    low=Decimal(str(row['low'])) if pd.notna(row['low']) else None,
                    close=Decimal(str(row['close'])) if pd.notna(row['close']) else None,
                    pre_close=Decimal(str(row['pre_close'])) if pd.notna(row['pre_close']) else None,
                    change=Decimal(str(row['change'])) if pd.notna(row['change']) else None,
                    pct_chg=Decimal(str(row['pct_chg'])) if pd.notna(row['pct_chg']) else None,
                    vol=int(row['vol']) if pd.notna(row['vol']) else None,
                    amount=Decimal(str(row['amount'])) if pd.notna(row['amount']) else None
                )
                daily_data.append(data)
            
            logger.info(f"获取到 {len(daily_data)} 条日线数据")
            return daily_data
            
        except Exception as e:
            logger.error(f"获取日线数据失败: {e}")
            raise
    
    @api_retry(max_retries=3, delay=1.0)
    async def get_daily_basic(self, trade_date: Optional[str] = None,
                            ts_codes: Optional[List[str]] = None) -> List[DailyBasic]:
        """获取每日基本面数据"""
        await self._wait_for_rate_limit()
        
        def _fetch_daily_basic():
            if ts_codes:
                all_data = []
                for i in range(0, len(ts_codes), 50):
                    batch_codes = ts_codes[i:i+50]
                    df = self.pro.daily_basic(
                        ts_code=','.join(batch_codes),
                        trade_date=trade_date,
                        fields='ts_code,trade_date,close,turnover_rate,volume_ratio,pe,pb,ps,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv'
                    )
                    all_data.append(df)
                    time.sleep(0.3)
                
                if all_data:
                    df = pd.concat(all_data, ignore_index=True)
                else:
                    df = pd.DataFrame()
            else:
                df = self.pro.daily_basic(
                    trade_date=trade_date,
                    fields='ts_code,trade_date,close,turnover_rate,volume_ratio,pe,pb,ps,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv'
                )
            return df
        
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, _fetch_daily_basic)
            
            basic_data = []
            for _, row in df.iterrows():
                data = DailyBasic(
                    ts_code=row['ts_code'],
                    trade_date=pd.to_datetime(row['trade_date']).date(),
                    close=Decimal(str(row['close'])) if pd.notna(row['close']) else None,
                    turnover_rate=Decimal(str(row['turnover_rate'])) if pd.notna(row['turnover_rate']) else None,
                    volume_ratio=Decimal(str(row['volume_ratio'])) if pd.notna(row['volume_ratio']) else None,
                    pe=Decimal(str(row['pe'])) if pd.notna(row['pe']) else None,
                    pb=Decimal(str(row['pb'])) if pd.notna(row['pb']) else None,
                    ps=Decimal(str(row['ps'])) if pd.notna(row['ps']) else None,
                    dv_ratio=Decimal(str(row['dv_ratio'])) if pd.notna(row['dv_ratio']) else None,
                    dv_ttm=Decimal(str(row['dv_ttm'])) if pd.notna(row['dv_ttm']) else None,
                    total_share=Decimal(str(row['total_share'])) if pd.notna(row['total_share']) else None,
                    float_share=Decimal(str(row['float_share'])) if pd.notna(row['float_share']) else None,
                    free_share=Decimal(str(row['free_share'])) if pd.notna(row['free_share']) else None,
                    total_mv=Decimal(str(row['total_mv'])) if pd.notna(row['total_mv']) else None,
                    circ_mv=Decimal(str(row['circ_mv'])) if pd.notna(row['circ_mv']) else None
                )
                basic_data.append(data)
            
            logger.info(f"获取到 {len(basic_data)} 条每日基本面数据")
            return basic_data
            
        except Exception as e:
            logger.error(f"获取每日基本面数据失败: {e}")
            raise
    
    @api_retry(max_retries=3, delay=1.0)
    async def get_limit_list(self, trade_date: str) -> List[LimitListData]:
        """获取涨跌停统计数据"""
        await self._wait_for_rate_limit()
        
        def _fetch_limit_list():
            df = self.pro.limit_list_d(
                trade_date=trade_date,
                fields='ts_code,trade_date,limit,fd_amount,first_time,last_time,open_times,strth,limit_times'
            )
            return df
        
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, _fetch_limit_list)
            
            limit_data = []
            for _, row in df.iterrows():
                data = LimitListData(
                    ts_code=row['ts_code'],
                    trade_date=pd.to_datetime(row['trade_date']).date(),
                    limit=row['limit'],
                    fd_amount=Decimal(str(row['fd_amount'])) if pd.notna(row['fd_amount']) else None,
                    first_time=pd.to_datetime(row['first_time']).time() if pd.notna(row['first_time']) else None,
                    last_time=pd.to_datetime(row['last_time']).time() if pd.notna(row['last_time']) else None,
                    open_times=int(row['open_times']) if pd.notna(row['open_times']) else None,
                    strth=Decimal(str(row['strth'])) if pd.notna(row['strth']) else None,
                    limit_times=int(row['limit_times']) if pd.notna(row['limit_times']) else None
                )
                limit_data.append(data)
            
            logger.info(f"获取到 {len(limit_data)} 条涨跌停数据")
            return limit_data
            
        except Exception as e:
            logger.error(f"获取涨跌停数据失败: {e}")
            raise
    
    @api_retry(max_retries=3, delay=1.0)
    async def get_money_flow(self, trade_date: str, ts_codes: List[str]) -> List[MoneyFlowData]:
        """获取资金流向数据"""
        await self._wait_for_rate_limit()
        
        def _fetch_money_flow():
            all_data = []
            # 分批获取，每次30只（资金流向数据量较大）
            for i in range(0, len(ts_codes), 30):
                batch_codes = ts_codes[i:i+30]
                try:
                    df = self.pro.moneyflow(
                        ts_code=','.join(batch_codes),
                        trade_date=trade_date,
                        fields='ts_code,trade_date,buy_sm_vol,buy_sm_amount,sell_sm_vol,sell_sm_amount,buy_md_vol,buy_md_amount,sell_md_vol,sell_md_amount,buy_lg_vol,buy_lg_amount,sell_lg_vol,sell_lg_amount,buy_elg_vol,buy_elg_amount,sell_elg_vol,sell_elg_amount,net_mf_vol,net_mf_amount'
                    )
                    if not df.empty:
                        all_data.append(df)
                except Exception as e:
                    logger.warning(f"获取资金流向数据失败 (batch {i}-{i+30}): {e}")
                
                time.sleep(0.5)  # 资金流向数据调用频率限制更严格
            
            if all_data:
                df = pd.concat(all_data, ignore_index=True)
            else:
                df = pd.DataFrame()
            return df
        
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, _fetch_money_flow)
            
            money_flow_data = []
            for _, row in df.iterrows():
                data = MoneyFlowData(
                    ts_code=row['ts_code'],
                    trade_date=pd.to_datetime(row['trade_date']).date(),
                    buy_sm_vol=int(row['buy_sm_vol']) if pd.notna(row['buy_sm_vol']) else None,
                    buy_sm_amount=Decimal(str(row['buy_sm_amount'])) if pd.notna(row['buy_sm_amount']) else None,
                    sell_sm_vol=int(row['sell_sm_vol']) if pd.notna(row['sell_sm_vol']) else None,
                    sell_sm_amount=Decimal(str(row['sell_sm_amount'])) if pd.notna(row['sell_sm_amount']) else None,
                    buy_md_vol=int(row['buy_md_vol']) if pd.notna(row['buy_md_vol']) else None,
                    buy_md_amount=Decimal(str(row['buy_md_amount'])) if pd.notna(row['buy_md_amount']) else None,
                    sell_md_vol=int(row['sell_md_vol']) if pd.notna(row['sell_md_vol']) else None,
                    sell_md_amount=Decimal(str(row['sell_md_amount'])) if pd.notna(row['sell_md_amount']) else None,
                    buy_lg_vol=int(row['buy_lg_vol']) if pd.notna(row['buy_lg_vol']) else None,
                    buy_lg_amount=Decimal(str(row['buy_lg_amount'])) if pd.notna(row['buy_lg_amount']) else None,
                    sell_lg_vol=int(row['sell_lg_vol']) if pd.notna(row['sell_lg_vol']) else None,
                    sell_lg_amount=Decimal(str(row['sell_lg_amount'])) if pd.notna(row['sell_lg_amount']) else None,
                    buy_elg_vol=int(row['buy_elg_vol']) if pd.notna(row['buy_elg_vol']) else None,
                    buy_elg_amount=Decimal(str(row['buy_elg_amount'])) if pd.notna(row['buy_elg_amount']) else None,
                    sell_elg_vol=int(row['sell_elg_vol']) if pd.notna(row['sell_elg_vol']) else None,
                    sell_elg_amount=Decimal(str(row['sell_elg_amount'])) if pd.notna(row['sell_elg_amount']) else None,
                    net_mf_vol=int(row['net_mf_vol']) if pd.notna(row['net_mf_vol']) else None,
                    net_mf_amount=Decimal(str(row['net_mf_amount'])) if pd.notna(row['net_mf_amount']) else None
                )
                money_flow_data.append(data)
            
            logger.info(f"获取到 {len(money_flow_data)} 条资金流向数据")
            return money_flow_data
            
        except Exception as e:
            logger.error(f"获取资金流向数据失败: {e}")
            raise
    
    @api_retry(max_retries=3, delay=1.0)
    async def get_top_list(self, trade_date: str) -> List[TopListData]:
        """获取龙虎榜数据"""
        await self._wait_for_rate_limit()
        
        def _fetch_top_list():
            df = self.pro.top_list(
                trade_date=trade_date,
                fields='trade_date,ts_code,name,close,pct_chg,turnover_rate,amount,l_sell,l_buy,l_amount,net_amount,net_rate,amount_rate,float_values,reason'
            )
            return df
        
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, _fetch_top_list)
            
            top_list_data = []
            for _, row in df.iterrows():
                data = TopListData(
                    trade_date=pd.to_datetime(row['trade_date']).date(),
                    ts_code=row['ts_code'],
                    name=row['name'],
                    close=Decimal(str(row['close'])) if pd.notna(row['close']) else None,
                    pct_chg=Decimal(str(row['pct_chg'])) if pd.notna(row['pct_chg']) else None,
                    turnover_rate=Decimal(str(row['turnover_rate'])) if pd.notna(row['turnover_rate']) else None,
                    amount=Decimal(str(row['amount'])) if pd.notna(row['amount']) else None,
                    l_sell=Decimal(str(row['l_sell'])) if pd.notna(row['l_sell']) else None,
                    l_buy=Decimal(str(row['l_buy'])) if pd.notna(row['l_buy']) else None,
                    l_amount=Decimal(str(row['l_amount'])) if pd.notna(row['l_amount']) else None,
                    net_amount=Decimal(str(row['net_amount'])) if pd.notna(row['net_amount']) else None,
                    net_rate=Decimal(str(row['net_rate'])) if pd.notna(row['net_rate']) else None,
                    amount_rate=Decimal(str(row['amount_rate'])) if pd.notna(row['amount_rate']) else None,
                    float_values=Decimal(str(row['float_values'])) if pd.notna(row['float_values']) else None,
                    reason=row['reason']
                )
                top_list_data.append(data)
            
            logger.info(f"获取到 {len(top_list_data)} 条龙虎榜数据")
            return top_list_data
            
        except Exception as e:
            logger.error(f"获取龙虎榜数据失败: {e}")
            raise
    
    @api_retry(max_retries=3, delay=1.0)
    async def get_top_inst(self, trade_date: str) -> List[TopInstData]:
        """获取龙虎榜机构数据"""
        await self._wait_for_rate_limit()
        
        def _fetch_top_inst():
            df = self.pro.top_inst(
                trade_date=trade_date,
                fields='trade_date,ts_code,exalter,buy,buy_rate,sell,sell_rate,net_buy'
            )
            return df
        
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, _fetch_top_inst)
            
            top_inst_data = []
            for _, row in df.iterrows():
                data = TopInstData(
                    trade_date=pd.to_datetime(row['trade_date']).date(),
                    ts_code=row['ts_code'],
                    exalter=row['exalter'],
                    buy=Decimal(str(row['buy'])) if pd.notna(row['buy']) else None,
                    buy_rate=Decimal(str(row['buy_rate'])) if pd.notna(row['buy_rate']) else None,
                    sell=Decimal(str(row['sell'])) if pd.notna(row['sell']) else None,
                    sell_rate=Decimal(str(row['sell_rate'])) if pd.notna(row['sell_rate']) else None,
                    net_buy=Decimal(str(row['net_buy'])) if pd.notna(row['net_buy']) else None
                )
                top_inst_data.append(data)
            
            logger.info(f"获取到 {len(top_inst_data)} 条龙虎榜机构数据")
            return top_inst_data
            
        except Exception as e:
            logger.error(f"获取龙虎榜机构数据失败: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """测试API连接"""
        try:
            # 简单测试：获取交易日历
            await self._wait_for_rate_limit()
            
            def _test_api():
                df = self.pro.trade_cal(start_date='20240101', end_date='20240102')
                return len(df) > 0
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _test_api)
            
            if result:
                logger.info("Tushare API连接测试成功")
            return result
            
        except Exception as e:
            logger.error(f"Tushare API连接测试失败: {e}")
            return False
    
    def get_trade_date_str(self, target_date: Optional[date] = None) -> str:
        """获取交易日期字符串格式"""
        if target_date is None:
            target_date = datetime.now().date()
        return target_date.strftime('%Y%m%d')
