"""
数据库操作类
提供对所有表的CRUD操作
"""

import asyncpg
import logging
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal

from .connection import get_database_pool
from .models import *

logger = logging.getLogger(__name__)

class DatabaseOperations:
    """数据库操作类"""
    
    def __init__(self):
        self.pool = None
    
    async def get_pool(self) -> asyncpg.Pool:
        """获取数据库连接池"""
        if not self.pool:
            self.pool = await get_database_pool()
        return self.pool
    
    # 股票基础信息操作
    async def insert_stocks(self, stocks: List[StockInfo]) -> int:
        """批量插入股票基础信息"""
        pool = await self.get_pool()
        
        insert_sql = """
        INSERT INTO stocks (ts_code, symbol, name, area, industry, market, list_date, is_hs)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (ts_code) DO UPDATE SET
            name = EXCLUDED.name,
            area = EXCLUDED.area,
            industry = EXCLUDED.industry,
            market = EXCLUDED.market,
            is_hs = EXCLUDED.is_hs,
            updated_at = CURRENT_TIMESTAMP
        """
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                rows_affected = 0
                for stock in stocks:
                    await conn.execute(
                        insert_sql,
                        stock.ts_code, stock.symbol, stock.name, stock.area,
                        stock.industry, stock.market, stock.list_date, stock.is_hs
                    )
                    rows_affected += 1
                
                logger.info(f"插入/更新了 {rows_affected} 条股票基础信息")
                return rows_affected
    
    async def get_all_stocks(self) -> List[StockInfo]:
        """获取所有股票基础信息"""
        pool = await self.get_pool()
        
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM stocks ORDER BY ts_code")
            return [StockInfo(**dict(row)) for row in rows]
    
    async def get_stock_by_code(self, ts_code: str) -> Optional[StockInfo]:
        """根据代码获取股票信息"""
        pool = await self.get_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM stocks WHERE ts_code = $1", ts_code)
            return StockInfo(**dict(row)) if row else None
    
    # 日线数据操作
    async def insert_daily_data(self, daily_data: List[DailyData]) -> int:
        """批量插入日线数据"""
        pool = await self.get_pool()
        
        insert_sql = """
        INSERT INTO daily_data (ts_code, trade_date, open, high, low, close, pre_close, 
                               change, pct_chg, vol, amount)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        ON CONFLICT (ts_code, trade_date) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            pre_close = EXCLUDED.pre_close,
            change = EXCLUDED.change,
            pct_chg = EXCLUDED.pct_chg,
            vol = EXCLUDED.vol,
            amount = EXCLUDED.amount
        """
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                rows_affected = 0
                for data in daily_data:
                    await conn.execute(
                        insert_sql,
                        data.ts_code, data.trade_date, data.open, data.high, data.low,
                        data.close, data.pre_close, data.change, data.pct_chg, 
                        data.vol, data.amount
                    )
                    rows_affected += 1
                
                logger.info(f"插入/更新了 {rows_affected} 条日线数据")
                return rows_affected
    
    async def get_daily_data(self, ts_code: Optional[str] = None, 
                           start_date: Optional[date] = None,
                           end_date: Optional[date] = None,
                           limit: int = 1000) -> List[DailyData]:
        """获取日线数据"""
        pool = await self.get_pool()
        
        conditions = []
        params = []
        param_count = 0
        
        if ts_code:
            param_count += 1
            conditions.append(f"ts_code = ${param_count}")
            params.append(ts_code)
        
        if start_date:
            param_count += 1
            conditions.append(f"trade_date >= ${param_count}")
            params.append(start_date)
        
        if end_date:
            param_count += 1
            conditions.append(f"trade_date <= ${param_count}")
            params.append(end_date)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        sql = f"""
        SELECT * FROM daily_data 
        {where_clause}
        ORDER BY trade_date DESC, ts_code
        LIMIT {limit}
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [DailyData(**dict(row)) for row in rows]
    
    # 每日基本面数据操作
    async def insert_daily_basic(self, basic_data: List[DailyBasic]) -> int:
        """批量插入每日基本面数据"""
        pool = await self.get_pool()
        
        insert_sql = """
        INSERT INTO daily_basic (ts_code, trade_date, close, turnover_rate, volume_ratio,
                               pe, pb, ps, dv_ratio, dv_ttm, total_share, float_share,
                               free_share, total_mv, circ_mv)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
        ON CONFLICT (ts_code, trade_date) DO UPDATE SET
            close = EXCLUDED.close,
            turnover_rate = EXCLUDED.turnover_rate,
            volume_ratio = EXCLUDED.volume_ratio,
            pe = EXCLUDED.pe,
            pb = EXCLUDED.pb,
            ps = EXCLUDED.ps,
            dv_ratio = EXCLUDED.dv_ratio,
            dv_ttm = EXCLUDED.dv_ttm,
            total_share = EXCLUDED.total_share,
            float_share = EXCLUDED.float_share,
            free_share = EXCLUDED.free_share,
            total_mv = EXCLUDED.total_mv,
            circ_mv = EXCLUDED.circ_mv
        """
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                rows_affected = 0
                for data in basic_data:
                    await conn.execute(
                        insert_sql,
                        data.ts_code, data.trade_date, data.close, data.turnover_rate,
                        data.volume_ratio, data.pe, data.pb, data.ps, data.dv_ratio,
                        data.dv_ttm, data.total_share, data.float_share, data.free_share,
                        data.total_mv, data.circ_mv
                    )
                    rows_affected += 1
                
                logger.info(f"插入/更新了 {rows_affected} 条每日基本面数据")
                return rows_affected
    
    # 策略结果操作
    async def insert_strategy_results(self, results: List[StrategyResult]) -> int:
        """批量插入策略计算结果"""
        pool = await self.get_pool()
        
        insert_sql = """
        INSERT INTO strategy_results (ts_code, trade_date, total_score, volume_price_score,
                                    chip_score, dragon_tiger_score, theme_score, 
                                    money_flow_score, rank_position, is_candidate, reason)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        ON CONFLICT (ts_code, trade_date) DO UPDATE SET
            total_score = EXCLUDED.total_score,
            volume_price_score = EXCLUDED.volume_price_score,
            chip_score = EXCLUDED.chip_score,
            dragon_tiger_score = EXCLUDED.dragon_tiger_score,
            theme_score = EXCLUDED.theme_score,
            money_flow_score = EXCLUDED.money_flow_score,
            rank_position = EXCLUDED.rank_position,
            is_candidate = EXCLUDED.is_candidate,
            reason = EXCLUDED.reason
        """
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                rows_affected = 0
                for result in results:
                    await conn.execute(
                        insert_sql,
                        result.ts_code, result.trade_date, result.total_score,
                        result.volume_price_score, result.chip_score, 
                        result.dragon_tiger_score, result.theme_score,
                        result.money_flow_score, result.rank_position,
                        result.is_candidate, result.reason
                    )
                    rows_affected += 1
                
                logger.info(f"插入/更新了 {rows_affected} 条策略结果")
                return rows_affected
    
    async def get_strategy_results(self, trade_date: Optional[date] = None,
                                 is_candidate: Optional[bool] = None,
                                 limit: int = 100) -> List[StrategyResult]:
        """获取策略计算结果"""
        pool = await self.get_pool()
        
        conditions = []
        params = []
        param_count = 0
        
        if trade_date:
            param_count += 1
            conditions.append(f"trade_date = ${param_count}")
            params.append(trade_date)
        
        if is_candidate is not None:
            param_count += 1
            conditions.append(f"is_candidate = ${param_count}")
            params.append(is_candidate)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        sql = f"""
        SELECT * FROM strategy_results 
        {where_clause}
        ORDER BY total_score DESC, rank_position ASC
        LIMIT {limit}
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [StrategyResult(**dict(row)) for row in rows]
    
    # 获取候选股票（包含股票基本信息）
    async def get_candidate_stocks(self, trade_date: Optional[date] = None,
                                 limit: int = 50) -> List[CandidateStock]:
        """获取候选股票列表"""
        pool = await self.get_pool()
        
        date_condition = "WHERE sr.trade_date = $1" if trade_date else ""
        params = [trade_date] if trade_date else []
        
        sql = f"""
        SELECT 
            sr.ts_code,
            s.name,
            dd.close,
            dd.pct_chg,
            db.turnover_rate,
            db.volume_ratio,
            sr.total_score,
            sr.rank_position,
            sr.reason,
            db.circ_mv as market_cap,
            dd.amount
        FROM strategy_results sr
        JOIN stocks s ON sr.ts_code = s.ts_code
        LEFT JOIN daily_data dd ON sr.ts_code = dd.ts_code AND sr.trade_date = dd.trade_date
        LEFT JOIN daily_basic db ON sr.ts_code = db.ts_code AND sr.trade_date = db.trade_date
        {date_condition}
        WHERE sr.is_candidate = true
        ORDER BY sr.total_score DESC, sr.rank_position ASC
        LIMIT {limit}
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            
            candidates = []
            for row in rows:
                candidate = CandidateStock(
                    ts_code=row['ts_code'],
                    name=row['name'] or '',
                    close=row['close'] or Decimal('0'),
                    pct_chg=row['pct_chg'] or Decimal('0'),
                    turnover_rate=row['turnover_rate'] or Decimal('0'),
                    volume_ratio=row['volume_ratio'] or Decimal('0'),
                    total_score=row['total_score'] or Decimal('0'),
                    rank_position=row['rank_position'] or 0,
                    reason=row['reason'] or '',
                    market_cap=row['market_cap'],
                    amount=row['amount']
                )
                candidates.append(candidate)
            
            return candidates
    
    # 用户设置操作
    async def get_user_settings(self) -> Dict[str, str]:
        """获取所有用户设置"""
        pool = await self.get_pool()
        
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT setting_key, setting_value FROM user_settings")
            return {row['setting_key']: row['setting_value'] for row in rows}
    
    async def update_user_setting(self, key: str, value: str) -> bool:
        """更新用户设置"""
        pool = await self.get_pool()
        
        async with pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE user_settings 
                SET setting_value = $2, updated_at = CURRENT_TIMESTAMP 
                WHERE setting_key = $1
                """,
                key, value
            )
            return result.split()[-1] == '1'  # 检查是否更新了一行
    
    # 市场情绪统计
    async def get_market_sentiment(self, trade_date: Optional[date] = None) -> Dict[str, Any]:
        """获取市场情绪数据"""
        pool = await self.get_pool()
        
        date_condition = "WHERE trade_date = $1" if trade_date else ""
        params = [trade_date] if trade_date else []
        
        async with pool.acquire() as conn:
            # 涨停股数量
            limit_up_count = await conn.fetchval(
                f"SELECT COUNT(*) FROM limit_list {date_condition} AND limit = 'U'",
                *params
            )
            
            # 连板股数量统计
            if trade_date:
                limit_times_stats = await conn.fetch(
                    "SELECT limit_times, COUNT(*) as count FROM limit_list WHERE trade_date = $1 AND limit = 'U' GROUP BY limit_times ORDER BY limit_times",
                    trade_date
                )
            else:
                limit_times_stats = []
            
            # 炸板率统计
            if trade_date:
                zhaban_stats = await conn.fetchrow(
                    "SELECT AVG(open_times) as avg_open_times, COUNT(*) as total_limit FROM limit_list WHERE trade_date = $1 AND limit = 'U'",
                    trade_date
                )
            else:
                zhaban_stats = {'avg_open_times': 0, 'total_limit': 0}
            
            return {
                'limit_up_count': limit_up_count or 0,
                'limit_times_distribution': {str(row['limit_times']): row['count'] for row in limit_times_stats},
                'avg_open_times': float(zhaban_stats['avg_open_times'] or 0),
                'total_limit_stocks': zhaban_stats['total_limit'] or 0,
                'zhaban_rate': float(zhaban_stats['avg_open_times'] or 0) / max(zhaban_stats['total_limit'] or 1, 1)
            }
    
    # 获取最新交易日期
    async def get_latest_trade_date(self) -> Optional[date]:
        """获取最新交易日期"""
        pool = await self.get_pool()
        
        async with pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT MAX(trade_date) FROM daily_data"
            )
            return result
    
    # 涨跌停数据操作
    async def insert_limit_list(self, limit_data: List[LimitListData]) -> int:
        """批量插入涨跌停数据"""
        pool = await self.get_pool()
        
        insert_sql = """
        INSERT INTO limit_list (
            trade_date, ts_code, name, close, pct_chg, amount, 
            limit, fd_amount, first_time, last_time, open_times, 
            strth, limit_amount
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        ON CONFLICT (ts_code, trade_date) DO UPDATE SET
            name = EXCLUDED.name,
            close = EXCLUDED.close,
            pct_chg = EXCLUDED.pct_chg,
            amount = EXCLUDED.amount,
            limit = EXCLUDED.limit,
            fd_amount = EXCLUDED.fd_amount,
            first_time = EXCLUDED.first_time,
            last_time = EXCLUDED.last_time,
            open_times = EXCLUDED.open_times,
            strth = EXCLUDED.strth,
            limit_amount = EXCLUDED.limit_amount
        """
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                rows_affected = 0
                for data in limit_data:
                    await conn.execute(
                        insert_sql,
                        data.trade_date, data.ts_code, data.name, data.close,
                        data.pct_chg, data.amount, data.limit, data.fd_amount,
                        data.first_time, data.last_time, data.open_times,
                        data.strth, data.limit_amount
                    )
                    rows_affected += 1
                
                logger.info(f"插入/更新了 {rows_affected} 条涨跌停数据")
                return rows_affected
    
    # 资金流向数据操作
    async def insert_money_flow(self, money_flow_data: List[MoneyFlowData]) -> int:
        """批量插入资金流向数据"""
        pool = await self.get_pool()
        
        insert_sql = """
        INSERT INTO money_flow (
            trade_date, ts_code, name, close, pct_chg, vol, amount,
            buy_sm_vol, buy_sm_amount, sell_sm_vol, sell_sm_amount,
            buy_md_vol, buy_md_amount, sell_md_vol, sell_md_amount,
            buy_lg_vol, buy_lg_amount, sell_lg_vol, sell_lg_amount,
            buy_elg_vol, buy_elg_amount, sell_elg_vol, sell_elg_amount,
            net_mf_vol, net_mf_amount
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25)
        ON CONFLICT (ts_code, trade_date) DO UPDATE SET
            name = EXCLUDED.name,
            close = EXCLUDED.close,
            pct_chg = EXCLUDED.pct_chg,
            vol = EXCLUDED.vol,
            amount = EXCLUDED.amount,
            buy_sm_vol = EXCLUDED.buy_sm_vol,
            buy_sm_amount = EXCLUDED.buy_sm_amount,
            sell_sm_vol = EXCLUDED.sell_sm_vol,
            sell_sm_amount = EXCLUDED.sell_sm_amount,
            buy_md_vol = EXCLUDED.buy_md_vol,
            buy_md_amount = EXCLUDED.buy_md_amount,
            sell_md_vol = EXCLUDED.sell_md_vol,
            sell_md_amount = EXCLUDED.sell_md_amount,
            buy_lg_vol = EXCLUDED.buy_lg_vol,
            buy_lg_amount = EXCLUDED.buy_lg_amount,
            sell_lg_vol = EXCLUDED.sell_lg_vol,
            sell_lg_amount = EXCLUDED.sell_lg_amount,
            buy_elg_vol = EXCLUDED.buy_elg_vol,
            buy_elg_amount = EXCLUDED.buy_elg_amount,
            sell_elg_vol = EXCLUDED.sell_elg_vol,
            sell_elg_amount = EXCLUDED.sell_elg_amount,
            net_mf_vol = EXCLUDED.net_mf_vol,
            net_mf_amount = EXCLUDED.net_mf_amount
        """
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                rows_affected = 0
                for data in money_flow_data:
                    await conn.execute(
                        insert_sql,
                        data.trade_date, data.ts_code, data.name, data.close,
                        data.pct_chg, data.vol, data.amount,
                        data.buy_sm_vol, data.buy_sm_amount, data.sell_sm_vol, data.sell_sm_amount,
                        data.buy_md_vol, data.buy_md_amount, data.sell_md_vol, data.sell_md_amount,
                        data.buy_lg_vol, data.buy_lg_amount, data.sell_lg_vol, data.sell_lg_amount,
                        data.buy_elg_vol, data.buy_elg_amount, data.sell_elg_vol, data.sell_elg_amount,
                        data.net_mf_vol, data.net_mf_amount
                    )
                    rows_affected += 1
                
                logger.info(f"插入/更新了 {rows_affected} 条资金流向数据")
                return rows_affected
    
    # 龙虎榜数据操作
    async def insert_top_list(self, top_list_data: List[TopListData]) -> int:
        """批量插入龙虎榜数据"""
        pool = await self.get_pool()
        
        insert_sql = """
        INSERT INTO top_list (
            trade_date, ts_code, name, close, pct_chg, turnover_rate,
            reason, buy_amount, sell_amount, net_amount, amount_ratio,
            float_values, reason_type
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        ON CONFLICT (ts_code, trade_date) DO UPDATE SET
            name = EXCLUDED.name,
            close = EXCLUDED.close,
            pct_chg = EXCLUDED.pct_chg,
            turnover_rate = EXCLUDED.turnover_rate,
            reason = EXCLUDED.reason,
            buy_amount = EXCLUDED.buy_amount,
            sell_amount = EXCLUDED.sell_amount,
            net_amount = EXCLUDED.net_amount,
            amount_ratio = EXCLUDED.amount_ratio,
            float_values = EXCLUDED.float_values,
            reason_type = EXCLUDED.reason_type
        """
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                rows_affected = 0
                for data in top_list_data:
                    await conn.execute(
                        insert_sql,
                        data.trade_date, data.ts_code, data.name, data.close,
                        data.pct_chg, data.turnover_rate, data.reason,
                        data.buy_amount, data.sell_amount, data.net_amount,
                        data.amount_ratio, data.float_values, data.reason_type
                    )
                    rows_affected += 1
                
                logger.info(f"插入/更新了 {rows_affected} 条龙虎榜数据")
                return rows_affected
    
    # 龙虎榜机构数据操作
    async def insert_top_inst(self, top_inst_data: List[TopInstData]) -> int:
        """批量插入龙虎榜机构数据"""
        pool = await self.get_pool()
        
        insert_sql = """
        INSERT INTO top_inst (
            trade_date, ts_code, exalter, buy, buy_rate, sell, sell_rate,
            net_buy, side, reason
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        ON CONFLICT (ts_code, trade_date, exalter) DO UPDATE SET
            buy = EXCLUDED.buy,
            buy_rate = EXCLUDED.buy_rate,
            sell = EXCLUDED.sell,
            sell_rate = EXCLUDED.sell_rate,
            net_buy = EXCLUDED.net_buy,
            side = EXCLUDED.side,
            reason = EXCLUDED.reason
        """
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                rows_affected = 0
                for data in top_inst_data:
                    await conn.execute(
                        insert_sql,
                        data.trade_date, data.ts_code, data.exalter, data.buy,
                        data.buy_rate, data.sell, data.sell_rate, data.net_buy,
                        data.side, data.reason
                    )
                    rows_affected += 1
                
                logger.info(f"插入/更新了 {rows_affected} 条龙虎榜机构数据")
                return rows_affected
