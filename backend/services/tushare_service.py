"""
Tushare数据服务
负责从Tushare API获取真实股票数据
"""

import tushare as ts
import pandas as pd
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
from config import settings

logger = logging.getLogger(__name__)

class TushareService:
    """Tushare数据服务类"""
    
    def __init__(self):
        """初始化Tushare API"""
        try:
            ts.set_token(settings.tushare_token)
            self.pro = ts.pro_api()
            logger.info("Tushare API初始化成功")
        except Exception as e:
            logger.error(f"Tushare API初始化失败: {e}")
            raise
    
    async def get_stock_basic(self) -> pd.DataFrame:
        """获取股票基本信息"""
        try:
            # 获取A股股票基本信息
            df = self.pro.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry,market,list_date'
            )
            logger.info(f"获取股票基本信息成功，共{len(df)}只股票")
            return df
        except Exception as e:
            logger.error(f"获取股票基本信息失败: {e}")
            raise
    
    async def get_daily_data(self, trade_date: str = None) -> pd.DataFrame:
        """获取日线行情数据"""
        try:
            if not trade_date:
                trade_date = datetime.now().strftime('%Y%m%d')
            
            # 转换日期格式
            if '-' in trade_date:
                trade_date = trade_date.replace('-', '')
            
            df = self.pro.daily(
                trade_date=trade_date,
                fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount'
            )
            logger.info(f"获取{trade_date}日线数据成功，共{len(df)}条记录")
            return df
        except Exception as e:
            logger.error(f"获取日线数据失败: {e}")
            raise
    
    async def get_daily_basic(self, trade_date: str = None) -> pd.DataFrame:
        """获取每日基本面数据"""
        try:
            if not trade_date:
                trade_date = datetime.now().strftime('%Y%m%d')
            
            if '-' in trade_date:
                trade_date = trade_date.replace('-', '')
            
            df = self.pro.daily_basic(
                trade_date=trade_date,
                fields='ts_code,trade_date,turnover_rate,volume_ratio,pe,pb,ps,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv'
            )
            logger.info(f"获取{trade_date}基本面数据成功，共{len(df)}条记录")
            return df
        except Exception as e:
            logger.error(f"获取基本面数据失败: {e}")
            raise
    
    async def get_limit_list(self, trade_date: str = None) -> pd.DataFrame:
        """获取涨跌停股票数据"""
        try:
            if not trade_date:
                trade_date = datetime.now().strftime('%Y%m%d')
            
            if '-' in trade_date:
                trade_date = trade_date.replace('-', '')
            
            # 获取涨停股票
            df_up = self.pro.limit_list_d(
                trade_date=trade_date,
                limit_type='U',
                fields='ts_code,trade_date,name,close,pct_chg,amount,limit_amount,times'
            )
            
            # 获取跌停股票
            df_down = self.pro.limit_list_d(
                trade_date=trade_date,
                limit_type='D',
                fields='ts_code,trade_date,name,close,pct_chg,amount,limit_amount,times'
            )
            
            # 合并数据
            df_up['limit_type'] = 'U'
            df_down['limit_type'] = 'D'
            df = pd.concat([df_up, df_down], ignore_index=True)
            
            logger.info(f"获取{trade_date}涨跌停数据成功，涨停{len(df_up)}只，跌停{len(df_down)}只")
            return df
        except Exception as e:
            logger.error(f"获取涨跌停数据失败: {e}")
            raise
    
    async def get_money_flow(self, trade_date: str = None) -> pd.DataFrame:
        """获取资金流向数据"""
        try:
            if not trade_date:
                trade_date = datetime.now().strftime('%Y%m%d')
            
            if '-' in trade_date:
                trade_date = trade_date.replace('-', '')
            
            df = self.pro.moneyflow(
                trade_date=trade_date,
                fields='ts_code,trade_date,buy_sm_amount,buy_md_amount,buy_lg_amount,buy_elg_amount,sell_sm_amount,sell_md_amount,sell_lg_amount,sell_elg_amount,net_mf_amount'
            )
            logger.info(f"获取{trade_date}资金流向数据成功，共{len(df)}条记录")
            return df
        except Exception as e:
            logger.error(f"获取资金流向数据失败: {e}")
            raise
    
    async def get_top_list(self, trade_date: str = None) -> pd.DataFrame:
        """获取龙虎榜数据"""
        try:
            if not trade_date:
                trade_date = datetime.now().strftime('%Y%m%d')
            
            if '-' in trade_date:
                trade_date = trade_date.replace('-', '')
            
            df = self.pro.top_list(
                trade_date=trade_date,
                fields='ts_code,trade_date,name,close,pct_chg,turnover_rate,amount,l_sell,l_buy,l_amount,net_amount,net_rate,amount_rate,float_values,reason'
            )
            logger.info(f"获取{trade_date}龙虎榜数据成功，共{len(df)}条记录")
            return df
        except Exception as e:
            logger.error(f"获取龙虎榜数据失败: {e}")
            raise
    
    async def get_top_inst(self, trade_date: str = None) -> pd.DataFrame:
        """获取龙虎榜机构成交明细"""
        try:
            if not trade_date:
                trade_date = datetime.now().strftime('%Y%m%d')
            
            if '-' in trade_date:
                trade_date = trade_date.replace('-', '')
            
            df = self.pro.top_inst(
                trade_date=trade_date,
                fields='ts_code,trade_date,exalter,buy,buy_rate,sell,sell_rate,net_buy'
            )
            logger.info(f"获取{trade_date}龙虎榜机构数据成功，共{len(df)}条记录")
            return df
        except Exception as e:
            logger.error(f"获取龙虎榜机构数据失败: {e}")
            raise
    
    async def get_trade_cal(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取交易日历"""
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            
            df = self.pro.trade_cal(
                exchange='SSE',
                start_date=start_date,
                end_date=end_date,
                fields='exchange,cal_date,is_open'
            )
            
            # 只返回交易日
            trade_dates = df[df['is_open'] == 1]['cal_date'].tolist()
            logger.info(f"获取交易日历成功，{start_date}到{end_date}共{len(trade_dates)}个交易日")
            return trade_dates
        except Exception as e:
            logger.error(f"获取交易日历失败: {e}")
            raise
    
    async def get_concept_detail(self, ts_code: str) -> List[str]:
        """获取股票概念分类"""
        try:
            df = self.pro.concept_detail(
                ts_code=ts_code,
                fields='ts_code,concept_name'
            )
            concepts = df['concept_name'].tolist() if not df.empty else []
            logger.debug(f"获取{ts_code}概念分类成功: {concepts}")
            return concepts
        except Exception as e:
            logger.warning(f"获取{ts_code}概念分类失败: {e}")
            return []
    
    async def validate_api_connection(self) -> bool:
        """验证Tushare API连接"""
        try:
            # 测试获取少量数据
            df = self.pro.stock_basic(
                exchange='SSE',
                list_status='L',
                fields='ts_code,name',
                limit=5
            )
            if not df.empty:
                logger.info("Tushare API连接验证成功")
                return True
            else:
                logger.error("Tushare API连接验证失败：无法获取数据")
                return False
        except Exception as e:
            logger.error(f"Tushare API连接验证失败: {e}")
            return False
    
    def format_date(self, date_str: str) -> str:
        """格式化日期字符串"""
        if '-' in date_str:
            return date_str.replace('-', '')
        return date_str
    
    def parse_date(self, date_str: str) -> str:
        """解析日期字符串"""
        if len(date_str) == 8 and date_str.isdigit():
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        return date_str
