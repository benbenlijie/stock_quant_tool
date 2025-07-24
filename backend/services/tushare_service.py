"""
Tushare数据服务
负责从Tushare API获取真实股票数据，集成频率控制和缓存机制
"""

import pandas as pd
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any

from .rate_limited_tushare_client import RateLimitedTushareClient

logger = logging.getLogger(__name__)

class TushareService:
    """Tushare数据服务类，带频率控制和缓存"""
    
    def __init__(self, cache_ttl: int = 3600):
        """
        初始化Tushare API服务
        
        Args:
            cache_ttl: 缓存过期时间（秒），默认1小时
        """
        try:
            self.client = RateLimitedTushareClient(cache_ttl=cache_ttl)
            logger.info("Tushare Service 初始化成功")
        except Exception as e:
            logger.error(f"Tushare Service 初始化失败: {e}")
            raise
    
    async def get_stock_basic(self) -> pd.DataFrame:
        """获取股票基本信息"""
        try:
            df = await self.client.get_stock_basic()
            logger.info(f"获取股票基本信息成功，共{len(df)}只股票")
            return df
        except Exception as e:
            logger.error(f"获取股票基本信息失败: {e}")
            # 返回空DataFrame而不是抛异常，提高系统健壮性
            return pd.DataFrame()
    
    async def get_daily_data(self, trade_date: str = None) -> pd.DataFrame:
        """获取日线行情数据"""
        try:
            if not trade_date:
                trade_date = datetime.now().strftime('%Y%m%d')
            
            # 转换日期格式
            if '-' in trade_date:
                trade_date = trade_date.replace('-', '')
            
            df = await self.client.get_daily_data(trade_date=trade_date)
            
            if not df.empty:
                # 数据预处理
                df = self._preprocess_daily_data(df)
                logger.info(f"获取日线数据成功: {trade_date}, 共{len(df)}只股票")
            else:
                logger.warning(f"日线数据为空: {trade_date}")
            
            return df
            
        except Exception as e:
            logger.error(f"获取日线数据失败 {trade_date}: {e}")
            return pd.DataFrame()
    
    async def get_daily_basic(self, trade_date: str = None) -> pd.DataFrame:
        """获取每日基本面数据"""
        try:
            if not trade_date:
                trade_date = datetime.now().strftime('%Y%m%d')
            
            if '-' in trade_date:
                trade_date = trade_date.replace('-', '')
            
            df = await self.client.get_daily_basic(trade_date=trade_date)
            
            if not df.empty:
                # 数据预处理
                df = self._preprocess_basic_data(df)
                logger.info(f"获取基本面数据成功: {trade_date}, 共{len(df)}只股票")
            else:
                logger.warning(f"基本面数据为空: {trade_date}")
            
            return df
            
        except Exception as e:
            logger.error(f"获取基本面数据失败 {trade_date}: {e}")
            return pd.DataFrame()
    
    async def get_limit_list(self, trade_date: str) -> pd.DataFrame:
        """获取涨跌停股票列表"""
        try:
            if '-' in trade_date:
                trade_date = trade_date.replace('-', '')
            
            df = await self.client.get_limit_list(trade_date=trade_date)
            
            if not df.empty:
                logger.info(f"获取涨跌停数据成功: {trade_date}, 共{len(df)}只股票")
            else:
                logger.info(f"涨跌停数据为空: {trade_date}")
            
            return df
            
        except Exception as e:
            logger.error(f"获取涨跌停数据失败 {trade_date}: {e}")
            return pd.DataFrame()
    
    async def get_money_flow(self, trade_date: str = None, ts_codes: List[str] = None) -> pd.DataFrame:
        """获取资金流向数据"""
        try:
            if not trade_date:
                trade_date = datetime.now().strftime('%Y%m%d')
            
            if '-' in trade_date:
                trade_date = trade_date.replace('-', '')
            
            # 如果指定了股票代码，分批获取
            if ts_codes:
                all_data = []
                # 分批处理，避免单次请求过多
                batch_size = 100
                for i in range(0, len(ts_codes), batch_size):
                    batch_codes = ts_codes[i:i + batch_size]
                    for ts_code in batch_codes:
                        try:
                            df = await self.client.get_money_flow(trade_date=trade_date, ts_code=ts_code)
                            if not df.empty:
                                all_data.append(df)
                        except Exception as e:
                            logger.warning(f"获取资金流向数据失败 {ts_code}: {e}")
                            continue
                
                if all_data:
                    df = pd.concat(all_data, ignore_index=True)
                else:
                    df = pd.DataFrame()
            else:
                # 获取全市场数据
                df = await self.client.get_money_flow(trade_date=trade_date)
            
            if not df.empty:
                logger.info(f"获取资金流向数据成功: {trade_date}, 共{len(df)}只股票")
            else:
                logger.info(f"资金流向数据为空: {trade_date}")
            
            return df
            
        except Exception as e:
            logger.error(f"获取资金流向数据失败 {trade_date}: {e}")
            return pd.DataFrame()
    
    async def get_top_list(self, trade_date: str) -> pd.DataFrame:
        """获取龙虎榜数据"""
        try:
            if '-' in trade_date:
                trade_date = trade_date.replace('-', '')
            
            df = await self.client.get_top_list(trade_date=trade_date)
            
            if not df.empty:
                logger.info(f"获取龙虎榜数据成功: {trade_date}, 共{len(df)}条记录")
            else:
                logger.info(f"龙虎榜数据为空: {trade_date}")
            
            return df
            
        except Exception as e:
            logger.error(f"获取龙虎榜数据失败 {trade_date}: {e}")
            return pd.DataFrame()
    
    async def get_concept_detail(self, ts_code: str) -> List[str]:
        """获取个股概念详情（简化版）"""
        try:
            # 这里可以根据需要实现概念获取逻辑
            # 暂时返回空列表，避免过多API调用
            return []
        except Exception as e:
            logger.error(f"获取概念详情失败 {ts_code}: {e}")
            return []
    
    def _preprocess_daily_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """预处理日线数据"""
        if df.empty:
            return df
        
        try:
            # 确保数值列为正确类型
            numeric_columns = ['open', 'high', 'low', 'close', 'pre_close', 'change', 'pct_chg', 'vol', 'amount']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 过滤异常数据
            df = df[df['close'] > 0]  # 价格必须大于0
            df = df[df['vol'] >= 0]   # 成交量不能为负
            
            # 重置索引
            df = df.reset_index(drop=True)
            
        except Exception as e:
            logger.warning(f"日线数据预处理失败: {e}")
        
        return df
    
    def _preprocess_basic_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """预处理基本面数据"""
        if df.empty:
            return df
        
        try:
            # 确保数值列为正确类型
            numeric_columns = ['turnover_rate', 'turnover_rate_f', 'volume_ratio', 'pe', 'pb', 'ps', 
                             'dv_ratio', 'dv_ttm', 'total_share', 'float_share', 'free_share', 'total_mv', 'circ_mv']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 处理异常值
            if 'turnover_rate' in df.columns:
                df.loc[df['turnover_rate'] < 0, 'turnover_rate'] = 0
                df.loc[df['turnover_rate'] > 100, 'turnover_rate'] = 100
            
            if 'volume_ratio' in df.columns:
                df.loc[df['volume_ratio'] < 0, 'volume_ratio'] = 0
            
            # 重置索引
            df = df.reset_index(drop=True)
            
        except Exception as e:
            logger.warning(f"基本面数据预处理失败: {e}")
        
        return df
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            return await self.client.health_check()
        except Exception as e:
            logger.error(f"Tushare Service 健康检查失败: {e}")
            return False
    
    def get_api_stats(self) -> Dict[str, Any]:
        """获取API调用统计"""
        try:
            return self.client.get_stats()
        except Exception as e:
            logger.error(f"获取API统计失败: {e}")
            return {}
    
    def clear_cache(self, older_than_hours: int = 24):
        """清理过期缓存"""
        try:
            self.client.clear_cache(older_than_hours)
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
    
    async def validate_connection(self) -> bool:
        """验证Tushare API连接"""
        try:
            result = await self.health_check()
            if result:
                logger.info("Tushare API连接验证成功")
                return True
            else:
                logger.error("Tushare API连接验证失败：无法获取数据")
                return False
        except Exception as e:
            logger.error(f"Tushare API连接验证失败: {e}")
            return False
