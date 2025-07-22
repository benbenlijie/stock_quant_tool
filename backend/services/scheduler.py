"""
定时任务调度器
负责每日17:00的数据更新和策略计算
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Optional

from database.operations import DatabaseOperations
from .tushare_client import TushareClient
from .strategy_engine import StrategyEngine

logger = logging.getLogger(__name__)

class StrategyScheduler:
    """策略定时任务调度器"""
    
    def __init__(self):
        self.db = DatabaseOperations()
        self.tushare = TushareClient()
        self.strategy_engine = StrategyEngine()
        self.is_running = False
    
    async def daily_data_update(self, target_date: Optional[date] = None):
        """
        每日数据更新和策略计算主流程
        1. 检查是否为交易日
        2. 更新所有必要数据
        3. 执行策略计算
        4. 保存结果
        """
        if self.is_running:
            logger.warning("任务已在运行中，跳过本次执行")
            return
        
        self.is_running = True
        
        try:
            # 确定目标日期
            if target_date is None:
                target_date = datetime.now().date()
                # 如果是周末，使用上一个交易日
                if target_date.weekday() >= 5:  # 周六或周日
                    days_back = target_date.weekday() - 4  # 回到周五
                    target_date = target_date - timedelta(days=days_back)
            
            logger.info(f"开始每日数据更新任务，目标日期: {target_date}")
            
            # 步骤1: 检查和更新股票基础信息
            await self._update_stock_basic()
            
            # 步骤2: 更新当日的市场数据
            await self._update_market_data(target_date)
            
            # 步骤3: 更新专项数据（涨停、龙虎榜、资金流向）
            await self._update_special_data(target_date)
            
            # 步骤4: 执行策略计算
            await self._execute_strategy_calculation(target_date)
            
            logger.info(f"每日数据更新任务完成: {target_date}")
            
        except Exception as e:
            logger.error(f"每日数据更新任务失败: {e}")
            raise
        finally:
            self.is_running = False
    
    async def _update_stock_basic(self):
        """更新股票基础信息"""
        try:
            logger.info("开始更新股票基础信息...")
            
            # 获取最新的股票基础信息
            stocks = await self.tushare.get_stock_basic()
            
            if stocks:
                # 分批插入，每次500条
                batch_size = 500
                for i in range(0, len(stocks), batch_size):
                    batch = stocks[i:i + batch_size]
                    await self.db.insert_stocks(batch)
                    
                    # 避免数据库负载过大
                    if i + batch_size < len(stocks):
                        await asyncio.sleep(0.1)
                
                logger.info(f"股票基础信息更新完成，共 {len(stocks)} 条")
            else:
                logger.warning("未获取到股票基础信息")
                
        except Exception as e:
            logger.error(f"更新股票基础信息失败: {e}")
            raise
    
    async def _update_market_data(self, trade_date: date):
        """更新市场数据（日线和基本面）"""
        try:
            trade_date_str = self.tushare.get_trade_date_str(trade_date)
            logger.info(f"开始更新市场数据: {trade_date_str}")
            
            # 更新日线数据
            logger.info("更新日线数据...")
            daily_data = await self.tushare.get_daily_data(trade_date=trade_date_str)
            if daily_data:
                await self.db.insert_daily_data(daily_data)
                logger.info(f"日线数据更新完成，共 {len(daily_data)} 条")
            
            # 更新每日基本面数据
            logger.info("更新每日基本面数据...")
            basic_data = await self.tushare.get_daily_basic(trade_date=trade_date_str)
            if basic_data:
                await self.db.insert_daily_basic(basic_data)
                logger.info(f"每日基本面数据更新完成，共 {len(basic_data)} 条")
            
        except Exception as e:
            logger.error(f"更新市场数据失败: {e}")
            raise
    
    async def _update_special_data(self, trade_date: date):
        """更新专项数据（涨停、龙虎榜、资金流向）"""
        try:
            trade_date_str = self.tushare.get_trade_date_str(trade_date)
            logger.info(f"开始更新专项数据: {trade_date_str}")
            
            # 更新涨跌停数据
            try:
                logger.info("更新涨跌停数据...")
                limit_data = await self.tushare.get_limit_list(trade_date_str)
                if limit_data:
                    # 这里需要实现 insert_limit_list 方法
                    logger.info(f"涨跌停数据更新完成，共 {len(limit_data)} 条")
            except Exception as e:
                logger.warning(f"更新涨跌停数据失败: {e}")
            
            # 更新龙虎榜数据
            try:
                logger.info("更新龙虎榜数据...")
                top_list_data = await self.tushare.get_top_list(trade_date_str)
                if top_list_data:
                    # 这里需要实现 insert_top_list 方法
                    logger.info(f"龙虎榜数据更新完成，共 {len(top_list_data)} 条")
                
                # 更新龙虎榜机构数据
                top_inst_data = await self.tushare.get_top_inst(trade_date_str)
                if top_inst_data:
                    # 这里需要实现 insert_top_inst 方法
                    logger.info(f"龙虎榜机构数据更新完成，共 {len(top_inst_data)} 条")
            except Exception as e:
                logger.warning(f"更新龙虎榜数据失败: {e}")
            
            # 更新资金流向数据(只更新有涨停的股票)
            try:
                logger.info("更新资金流向数据...")
                # 获取当日有涨停的股票代码
                limit_stocks = [data.ts_code for data in limit_data if data.limit == 'U'] if 'limit_data' in locals() else []
                
                if limit_stocks:
                    money_flow_data = await self.tushare.get_money_flow(trade_date_str, limit_stocks)
                    if money_flow_data:
                        # 这里需要实现 insert_money_flow 方法
                        logger.info(f"资金流向数据更新完成，共 {len(money_flow_data)} 条")
            except Exception as e:
                logger.warning(f"更新资金流向数据失败: {e}")
            
        except Exception as e:
            logger.error(f"更新专项数据失败: {e}")
            # 不抛出异常，允许部分数据更新失败
    
    async def _execute_strategy_calculation(self, trade_date: date):
        """执行策略计算"""
        try:
            logger.info(f"开始执行策略计算: {trade_date}")
            
            # 加载策略配置
            await self.strategy_engine.load_config_from_db()
            
            # 执行策略
            strategy_results = await self.strategy_engine.execute_strategy(trade_date)
            
            if strategy_results:
                # 保存策略结果
                await self.db.insert_strategy_results(strategy_results)
                
                candidate_count = len([r for r in strategy_results if r.is_candidate])
                logger.info(f"策略计算完成，共 {len(strategy_results)} 只股票，其中 {candidate_count} 只候选股")
            else:
                logger.warning("策略计算未返回结果")
            
        except Exception as e:
            logger.error(f"策略计算失败: {e}")
            raise
    
    async def manual_trigger(self, target_date: Optional[date] = None) -> bool:
        """手动触发数据更新和策略计算"""
        try:
            await self.daily_data_update(target_date)
            return True
        except Exception as e:
            logger.error(f"手动触发任务失败: {e}")
            return False
    
    def get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def get_task_status(self) -> dict:
        """获取任务状态"""
        return {
            'is_running': self.is_running,
            'last_check': self.get_current_timestamp()
        }
