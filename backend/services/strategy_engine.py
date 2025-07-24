"""
量化选股策略引擎
实现完整的连续涨停板选股策略逻辑
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from database.operations import DatabaseOperations
from services.tushare_service import TushareService
from config import settings, StrategyWeights

logger = logging.getLogger(__name__)

@dataclass
class CandidateStock:
    """候选股票数据结构"""
    ts_code: str
    name: str
    close: float
    pct_chg: float
    turnover_rate: float
    volume_ratio: float
    total_score: float
    rank_position: int
    reason: str
    market_cap: float = 0.0
    amount: float = 0.0
    theme: str = ""
    chip_concentration: float = 0.0
    dragon_tiger_net_amount: float = 0.0
    
    # 策略子分数
    volume_price_score: float = 0.0
    chip_score: float = 0.0
    dragon_tiger_score: float = 0.0
    theme_score: float = 0.0
    money_flow_score: float = 0.0

@dataclass
class MarketSentiment:
    """市场情绪数据结构"""
    limit_up_count: int
    limit_times_distribution: Dict[str, int]
    avg_open_times: float
    total_limit_stocks: int
    zhaban_rate: float
    emotion_index: float

class StrategyEngine:
    """策略引擎"""
    
    def __init__(self, db_ops: DatabaseOperations):
        self.db_ops = db_ops
        self.tushare = TushareService()
        
    async def run_daily_strategy(self, trade_date: str = None) -> List[CandidateStock]:
        """运行每日选股策略"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"开始运行{trade_date}的选股策略")
        
        try:
            # 1. 获取基础数据
            daily_data = await self.tushare.get_daily_data(trade_date)
            daily_basic = await self.tushare.get_daily_basic(trade_date)
            limit_list = await self.tushare.get_limit_list(trade_date)
            money_flow = await self.tushare.get_money_flow(trade_date)
            top_list = await self.tushare.get_top_list(trade_date)
            
            if daily_data.empty:
                logger.warning(f"{trade_date}无交易数据")
                return []
            
            # 2. 数据预处理和合并
            merged_data = self._merge_data(daily_data, daily_basic, money_flow, top_list)
            
            # 3. 候选股初筛
            candidates = self._initial_screening(merged_data)
            
            if candidates.empty:
                logger.warning(f"{trade_date}初筛后无候选股票")
                return []
            
            # 4. 量价关系过滤
            candidates = self._volume_price_filter(candidates)
            
            # 5. 技术形态筛选
            candidates = self._technical_filter(candidates)
            
            # 6. 计算筹码集中度
            candidates = await self._calculate_chip_concentration_with_enhanced_data(candidates)
            
            # 7. 分析龙虎榜资金
            candidates = self._analyze_dragon_tiger(candidates, top_list)
            
            # 8. 主题题材评分
            candidates = await self._theme_scoring(candidates)
            
            # 9. 综合评分和排名
            result = self._comprehensive_scoring(candidates)
            
            logger.info(f"{trade_date}策略运行完成，筛选出{len(result)}只候选股票")
            return result
            
        except Exception as e:
            logger.error(f"策略运行失败: {e}")
            raise
    
    def _merge_data(self, daily_data: pd.DataFrame, daily_basic: pd.DataFrame, 
                   money_flow: pd.DataFrame, top_list: pd.DataFrame) -> pd.DataFrame:
        """合并各类数据"""
        try:
            # 以日线数据为基础
            merged = daily_data.copy()
            
            # 合并基本面数据
            if not daily_basic.empty:
                merged = merged.merge(
                    daily_basic[['ts_code', 'turnover_rate', 'volume_ratio', 'circ_mv']],
                    on='ts_code',
                    how='left'
                )
            
            # 合并资金流向数据
            if not money_flow.empty:
                # 计算主力净流入
                money_flow['net_inflow'] = (
                    money_flow['buy_lg_amount'] + money_flow['buy_elg_amount'] -
                    money_flow['sell_lg_amount'] - money_flow['sell_elg_amount']
                )
                merged = merged.merge(
                    money_flow[['ts_code', 'net_inflow']],
                    on='ts_code',
                    how='left'
                )
            
            # 合并龙虎榜数据
            if not top_list.empty:
                merged = merged.merge(
                    top_list[['ts_code', 'net_amount', 'net_rate']],
                    on='ts_code',
                    how='left'
                )
            
            # 填充空值
            merged = merged.fillna(0)
            
            logger.info(f"数据合并完成，共{len(merged)}条记录")
            return merged
            
        except Exception as e:
            logger.error(f"数据合并失败: {e}")
            raise
    
    def _initial_screening(self, data: pd.DataFrame) -> pd.DataFrame:
        """候选股初筛"""
        try:
            # 1. 流通市值筛选（小于50亿）
            data = data[data['circ_mv'] <= settings.max_market_cap * 10000]  # 万元转换
            
            # 2. 股价筛选（小于30元）
            data = data[data['close'] <= settings.max_stock_price]
            
            # 3. 排除ST股票（股票代码规则筛选）
            data = data[~data['ts_code'].str.contains('ST|\*ST', na=False)]
            
            # 4. 涨幅筛选（大于等于9%）
            data = data[data['pct_chg'] >= settings.min_daily_gain]
            
            # 5. 排除停牌股票（成交额为0）
            data = data[data['amount'] > 0]
            
            logger.info(f"初筛完成，剩余{len(data)}只股票")
            return data
            
        except Exception as e:
            logger.error(f"初筛失败: {e}")
            raise
    
    def _volume_price_filter(self, data: pd.DataFrame) -> pd.DataFrame:
        """量价关系过滤"""
        try:
            # 1. 量比筛选（大于2倍）
            data = data[data['volume_ratio'] >= settings.min_volume_ratio]
            
            # 2. 换手率筛选（大于等于10%）
            data = data[data['turnover_rate'] >= settings.min_turnover_rate]
            
            # 3. 成交量异常放大（量比排序取前50%）
            volume_threshold = data['volume_ratio'].quantile(0.5)
            data = data[data['volume_ratio'] >= volume_threshold]
            
            logger.info(f"量价过滤完成，剩余{len(data)}只股票")
            return data
            
        except Exception as e:
            logger.error(f"量价过滤失败: {e}")
            raise
    
    def _technical_filter(self, data: pd.DataFrame) -> pd.DataFrame:
        """技术形态筛选"""
        try:
            # 1. 涨停板或接近涨停（涨幅9%以上已在初筛中处理）
            
            # 2. 放量突破（这里简化为量比和换手率的组合）
            data['technical_score'] = (
                data['volume_ratio'] * 0.4 +
                data['turnover_rate'] * 0.3 +
                data['pct_chg'] * 0.3
            )
            
            # 3. 技术评分排序，取前70%
            tech_threshold = data['technical_score'].quantile(0.3)
            data = data[data['technical_score'] >= tech_threshold]
            
            logger.info(f"技术筛选完成，剩余{len(data)}只股票")
            return data
            
        except Exception as e:
            logger.error(f"技术筛选失败: {e}")
            raise
    
    async def _calculate_chip_concentration_with_enhanced_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """使用增强数据计算筹码集中度和获利盘比例"""
        try:
            from services.chip_concentration_calculator import ChipConcentrationCalculator
            
            calculator = ChipConcentrationCalculator(lookback_days=60)
            chip_scores = []
            profit_ratios = []
            
            logger.info("开始计算增强筹码集中度...")
            
            for idx, row in data.iterrows():
                ts_code = row['ts_code']
                current_price = row.get('close', 0)
                
                try:
                    # 获取历史数据用于筹码计算
                    trade_date = row.get('trade_date', datetime.now().strftime('%Y%m%d'))
                    historical_data = await self._get_historical_data_for_chip_calc(ts_code, trade_date)
                    
                    if len(historical_data) >= 10:
                        # 使用增强计算方法
                        chip_metrics = calculator.calculate_enhanced_metrics(current_price, historical_data)
                        concentration = chip_metrics['chip_concentration']
                        profit_ratio = chip_metrics['profit_ratio']
                        
                        logger.debug(f"增强算法计算 {ts_code}: 集中度={concentration:.3f}, 获利盘={profit_ratio:.3f}")
                    else:
                        # 使用改进的简化算法作为后备
                        concentration, profit_ratio = self._calculate_improved_simple_concentration_with_tushare(row, historical_data)
                        logger.debug(f"简化算法计算 {ts_code}: 集中度={concentration:.3f}, 获利盘={profit_ratio:.3f}")
                    
                except Exception as e:
                    logger.warning(f"获取{ts_code}历史数据失败，使用基础算法: {e}")
                    # 使用改进的简化算法作为后备
                    concentration, profit_ratio = self._calculate_improved_simple_concentration_with_tushare(row)
                
                chip_scores.append(concentration)
                profit_ratios.append(profit_ratio)
            
            # 添加计算结果到数据框
            data['chip_concentration'] = chip_scores
            data['profit_ratio'] = profit_ratios
            
            # 双重筛选：筹码集中度 AND 获利盘比例
            concentration_filter = data['chip_concentration'] >= settings.chip_concentration_threshold
            profit_ratio_threshold = getattr(settings, 'profit_ratio_threshold', 0.5)
            profit_filter = data['profit_ratio'] >= profit_ratio_threshold
            
            # 组合筛选条件
            combined_filter = concentration_filter & profit_filter
            filtered_data = data[combined_filter]
            
            logger.info(f"增强筹码集中度计算完成：")
            logger.info(f"  - 集中度 >= {settings.chip_concentration_threshold}: {concentration_filter.sum()}只")
            logger.info(f"  - 获利盘 >= {profit_ratio_threshold}: {profit_filter.sum()}只")
            logger.info(f"  - 双重条件筛选后剩余: {len(filtered_data)}只股票")
            
            return filtered_data
            
        except Exception as e:
            logger.error(f"增强筹码集中度计算失败: {e}")
            # 回退到原始方法
            return await self._calculate_chip_concentration(data)

    def _calculate_improved_simple_concentration_with_tushare(self, row: pd.Series, 
                                                           historical_data: pd.DataFrame = None) -> tuple[float, float]:
        """基于Tushare数据的改进简化筹码集中度计算"""
        
        # 基础数据
        turnover_rate = row.get('turnover_rate', 5.0)
        volume_ratio = row.get('volume_ratio', 1.0)
        pct_chg = row.get('pct_chg', 0.0)
        current_price = row.get('close', 0)
        
        # 额外的Tushare指标
        pe_ttm = row.get('pe_ttm', 20)  # 市盈率
        pb = row.get('pb', 2)  # 市净率
        circ_mv = row.get('circ_mv', 0)  # 流通市值（万元）
        
        # === 筹码集中度计算 ===
        
        # 1. 基础集中度：适度换手率表示筹码流动但不过度分散
        base_concentration = 0.5
        
        # 2. 换手率因子：过高过低都不好，8%左右最优
        optimal_turnover = 8.0
        turnover_factor = 1.0 - abs(turnover_rate - optimal_turnover) / 20.0
        turnover_factor = max(0.3, min(1.2, turnover_factor))
        
        # 3. 量比因子：适度放量表示有资金介入
        volume_factor = min(1.3, max(0.7, 0.8 + volume_ratio / 10))
        
        # 4. 价格因子：适度上涨配合集中度
        price_factor = 1.0
        if 2 <= pct_chg <= 8:  # 适度上涨
            price_factor = 1.1
        elif pct_chg > 9:  # 涨停附近
            price_factor = 1.2
        elif pct_chg < -3:  # 下跌过多
            price_factor = 0.9
        
        # 5. 市值因子：小盘股更容易集中
        if circ_mv > 0:
            if circ_mv <= 300000:  # 30亿以下
                size_factor = 1.1
            elif circ_mv <= 500000:  # 50亿以下
                size_factor = 1.05
            else:
                size_factor = 1.0
        else:
            size_factor = 1.0
        
        # 6. 估值因子：合理估值更容易吸引资金集中
        valuation_factor = 1.0
        if pe_ttm > 0:
            if 10 <= pe_ttm <= 30:  # 合理估值区间
                valuation_factor = 1.05
            elif pe_ttm > 100:  # 估值过高
                valuation_factor = 0.95
        
        # 综合计算集中度
        concentration = base_concentration * turnover_factor * volume_factor * price_factor * size_factor * valuation_factor
        concentration = max(0.2, min(0.95, concentration))
        
        # === 获利盘比例计算 ===
        
        if historical_data is not None and len(historical_data) >= 5:
            # 使用历史数据计算更准确的获利盘比例
            profit_ratio = self._calculate_profit_ratio_from_history(current_price, historical_data)
        else:
            # 基于当前数据估算获利盘比例
            profit_ratio = self._estimate_profit_ratio_from_current_data(row)
        
        return concentration, profit_ratio
    
    def _calculate_profit_ratio_from_history(self, current_price: float, 
                                           historical_data: pd.DataFrame) -> float:
        """基于历史数据计算获利盘比例"""
        try:
            if len(historical_data) < 5:
                return 0.5
            
            # 计算不同时间段的平均成本
            periods = [5, 10, 20, 30]  # 不同周期
            weights = [0.4, 0.3, 0.2, 0.1]  # 对应权重，近期权重更高
            
            total_profit_volume = 0
            total_volume = 0
            
            for period, weight in zip(periods, weights):
                if len(historical_data) >= period:
                    period_data = historical_data.tail(period)
                    
                    # 计算该周期的加权平均成本
                    period_volumes = period_data['volume'].fillna(0)
                    period_prices = period_data['close'].fillna(0)
                    
                    if period_volumes.sum() > 0:
                        weighted_cost = (period_prices * period_volumes).sum() / period_volumes.sum()
                        period_volume = period_volumes.sum() * weight
                        
                        total_volume += period_volume
                        
                        # 如果平均成本低于当前价格，算作获利盘
                        if weighted_cost < current_price:
                            total_profit_volume += period_volume
            
            if total_volume > 0:
                profit_ratio = total_profit_volume / total_volume
                # 调整边界
                profit_ratio = max(0.05, min(0.95, profit_ratio))
            else:
                profit_ratio = 0.5
            
            return profit_ratio
            
        except Exception as e:
            logger.warning(f"历史获利盘计算失败: {e}")
            return 0.5
    
    def _estimate_profit_ratio_from_current_data(self, row: pd.Series) -> float:
        """基于当前数据估算获利盘比例"""
        
        pct_chg = row.get('pct_chg', 0.0)
        turnover_rate = row.get('turnover_rate', 5.0)
        volume_ratio = row.get('volume_ratio', 1.0)
        
        # 基础获利盘比例
        base_profit_ratio = 0.5
        
        # 1. 涨跌幅影响：涨幅越大，获利盘越多
        if pct_chg > 0:
            price_effect = min(0.3, pct_chg / 30)  # 每1%涨幅增加约0.033获利盘比例
        else:
            price_effect = max(-0.3, pct_chg / 20)  # 跌幅对获利盘的负面影响更大
        
        # 2. 换手率影响：适度换手表示有获利了结和新资金进入
        if 5 <= turnover_rate <= 15:
            turnover_effect = 0.05  # 适度换手，获利盘比例略高
        elif turnover_rate > 20:
            turnover_effect = -0.05  # 过度换手，可能是获利盘大量出逃
        else:
            turnover_effect = 0
        
        # 3. 量比影响：放量上涨通常表示更多获利盘
        if volume_ratio > 1.5 and pct_chg > 0:
            volume_effect = min(0.1, (volume_ratio - 1) / 10)
        else:
            volume_effect = 0
        
        # 综合计算
        profit_ratio = base_profit_ratio + price_effect + turnover_effect + volume_effect
        
        # 边界处理
        profit_ratio = max(0.1, min(0.9, profit_ratio))
        
        return profit_ratio

    async def _get_historical_data_for_chip_calc(self, ts_code: str, trade_date: str) -> pd.DataFrame:
        """获取用于筹码计算的历史数据"""
        try:
            if not hasattr(self, 'tushare_client') or not self.tushare_client:
                return pd.DataFrame()
            
            # 计算开始日期（60天前）
            end_date = datetime.strptime(trade_date, '%Y%m%d')
            start_date = end_date - timedelta(days=80)  # 多取一些数据，排除非交易日
            
            start_date_str = start_date.strftime('%Y%m%d')
            end_date_str = end_date.strftime('%Y%m%d')
            
            # 获取日线数据
            daily_df = self.tushare_client.pro.daily(
                ts_code=ts_code,
                start_date=start_date_str,
                end_date=end_date_str,
                fields='ts_code,trade_date,open,high,low,close,vol,amount'
            )
            
            # 获取基本面数据
            basic_df = self.tushare_client.pro.daily_basic(
                ts_code=ts_code,
                start_date=start_date_str,
                end_date=end_date_str,
                fields='ts_code,trade_date,turnover_rate,volume_ratio'
            )
            
            if len(daily_df) == 0:
                return pd.DataFrame()
            
            # 合并数据
            merged_df = pd.merge(daily_df, basic_df, on=['ts_code', 'trade_date'], how='left')
            
            # 重命名列以匹配计算器期望的格式
            merged_df = merged_df.rename(columns={
                'vol': 'volume',
                'trade_date': 'date'
            })
            
            # 转换日期格式
            merged_df['date'] = pd.to_datetime(merged_df['date'])
            merged_df = merged_df.sort_values('date')
            
            # 填充缺失值
            merged_df['turnover_rate'] = merged_df['turnover_rate'].fillna(5.0)
            merged_df['volume_ratio'] = merged_df['volume_ratio'].fillna(1.0)
            
            logger.debug(f"获取{ts_code}历史数据成功，共{len(merged_df)}条记录")
            
            return merged_df
            
        except Exception as e:
            logger.warning(f"获取{ts_code}历史数据失败: {e}")
            return pd.DataFrame()
    
    def _analyze_dragon_tiger(self, data: pd.DataFrame, top_list: pd.DataFrame) -> pd.DataFrame:
        """分析龙虎榜资金"""
        try:
            # 为所有股票初始化龙虎榜分数
            data['dragon_tiger_score'] = 0.0
            data['dragon_tiger_net_amount'] = 0.0
            
            if not top_list.empty:
                # 合并龙虎榜数据
                for _, row in top_list.iterrows():
                    ts_code = row['ts_code']
                    if ts_code in data['ts_code'].values:
                        mask = data['ts_code'] == ts_code
                        
                        # 净买额评分
                        net_amount = row.get('net_amount', 0)
                        net_rate = row.get('net_rate', 0)
                        
                        # 龙虎榜评分逻辑
                        if net_amount > 0 and net_rate > 0.1:  # 净买入且占比>10%
                            score = min(100, net_rate * 500)  # 转换为0-100分
                        elif net_amount < 0 and abs(net_rate) > 0.05:  # 砸盘席位>5%
                            score = -min(50, abs(net_rate) * 1000)
                        else:
                            score = 0
                        
                        data.loc[mask, 'dragon_tiger_score'] = score
                        data.loc[mask, 'dragon_tiger_net_amount'] = net_amount
            
            logger.info(f"龙虎榜分析完成，{len(top_list)}只股票上榜")
            return data
            
        except Exception as e:
            logger.error(f"龙虎榜分析失败: {e}")
            raise
    
    async def _theme_scoring(self, data: pd.DataFrame) -> pd.DataFrame:
        """主题题材评分"""
        try:
            # 简化的题材评分
            # 实际应用中需要实时题材热度分析
            
            theme_scores = []
            themes = []
            
            # 定义热门题材关键词
            hot_themes = {
                'AI人工智能': 90,
                '新能源': 85,
                '半导体': 80,
                '5G通信': 75,
                '医药生物': 70,
                '新材料': 65,
                '光伏': 80,
                '储能': 75,
                '汽车': 60
            }
            
            for _, row in data.iterrows():
                ts_code = row['ts_code']
                
                # 获取股票概念（简化处理）
                try:
                    concepts = await self.tushare.get_concept_detail(ts_code)
                    
                    # 计算题材热度分数
                    max_score = 0
                    main_theme = "其他"
                    
                    for concept in concepts:
                        for theme, score in hot_themes.items():
                            if theme in concept:
                                if score > max_score:
                                    max_score = score
                                    main_theme = theme
                                break
                    
                    if max_score == 0:
                        max_score = 30  # 默认分数
                    
                    theme_scores.append(max_score)
                    themes.append(main_theme)
                    
                except Exception as e:
                    logger.warning(f"获取{ts_code}概念失败: {e}")
                    theme_scores.append(30)
                    themes.append("其他")
            
            data['theme_score'] = theme_scores
            data['theme'] = themes
            
            logger.info(f"题材评分完成")
            return data
            
        except Exception as e:
            logger.error(f"题材评分失败: {e}")
            raise
    
    def _comprehensive_scoring(self, data: pd.DataFrame) -> List[CandidateStock]:
        """综合评分和排名"""
        try:
            results = []
            
            for i, row in data.iterrows():
                # 计算各维度分数（0-100分制）
                
                # 1. 量价分数 (30%)
                volume_price_score = (
                    min(100, row['volume_ratio'] * 20) * 0.4 +
                    min(100, row['turnover_rate'] * 3) * 0.3 +
                    min(100, row['pct_chg'] * 8) * 0.3
                )
                
                # 2. 筹码分数 (25%)
                chip_score = row['chip_concentration'] * 100
                
                # 3. 龙虎榜分数 (20%)
                dragon_tiger_score = max(0, min(100, row.get('dragon_tiger_score', 0)))
                
                # 4. 题材分数 (15%)
                theme_score = row.get('theme_score', 30)
                
                # 5. 资金流分数 (10%)
                net_inflow = row.get('net_inflow', 0)
                money_flow_score = min(100, max(0, (net_inflow / 10000000 + 1) * 50))  # 千万为单位
                
                # 综合评分
                total_score = (
                    volume_price_score * StrategyWeights.VOLUME_PRICE +
                    chip_score * StrategyWeights.CHIP_CONCENTRATION +
                    dragon_tiger_score * StrategyWeights.DRAGON_TIGER +
                    theme_score * StrategyWeights.THEME_HEAT +
                    money_flow_score * StrategyWeights.MONEY_FLOW
                )
                
                # 创建候选股票对象
                candidate = CandidateStock(
                    ts_code=row['ts_code'],
                    name=row.get('name', ''),
                    close=float(row['close']),
                    pct_chg=float(row['pct_chg']),
                    turnover_rate=float(row.get('turnover_rate', 0)),
                    volume_ratio=float(row.get('volume_ratio', 0)),
                    total_score=float(total_score),
                    rank_position=0,  # 后续排序后设置
                    reason="技术突破+量价齐升+题材热度",
                    market_cap=float(row.get('circ_mv', 0)) / 10000,  # 转换为亿元
                    amount=float(row.get('amount', 0)),
                    theme=row.get('theme', '其他'),
                    chip_concentration=float(row.get('chip_concentration', 0)),
                    dragon_tiger_net_amount=float(row.get('dragon_tiger_net_amount', 0)),
                    volume_price_score=float(volume_price_score),
                    chip_score=float(chip_score),
                    dragon_tiger_score=float(dragon_tiger_score),
                    theme_score=float(theme_score),
                    money_flow_score=float(money_flow_score)
                )
                
                results.append(candidate)
            
            # 按评分排序
            results.sort(key=lambda x: x.total_score, reverse=True)
            
            # 设置排名
            for i, candidate in enumerate(results):
                candidate.rank_position = i + 1
            
            # 取前50只
            results = results[:50]
            
            logger.info(f"综合评分完成，最终筛选出{len(results)}只候选股票")
            return results
            
        except Exception as e:
            logger.error(f"综合评分失败: {e}")
            raise
    
    async def get_market_sentiment(self, trade_date: str = None) -> MarketSentiment:
        """获取市场情绪指标"""
        try:
            if not trade_date:
                trade_date = datetime.now().strftime('%Y-%m-%d')
            
            # 获取涨跌停数据
            limit_list = await self.tushare.get_limit_list(trade_date)
            
            if limit_list.empty:
                return MarketSentiment(
                    limit_up_count=0,
                    limit_times_distribution={},
                    avg_open_times=0.0,
                    total_limit_stocks=0,
                    zhaban_rate=0.0,
                    emotion_index=0.0
                )
            
            # 分析涨停股票
            limit_up = limit_list[limit_list['limit_type'] == 'U']
            
            # 涨停家数
            limit_up_count = len(limit_up)
            
            # 连板分布
            times_dist = limit_up['times'].value_counts().to_dict()
            times_dist = {str(k): v for k, v in times_dist.items()}
            
            # 总连板股数
            total_limit_stocks = len(limit_up[limit_up['times'] >= 2])
            
            # 平均打开次数（简化计算）
            avg_open_times = max(1.0, limit_up['times'].mean()) if not limit_up.empty else 1.0
            
            # 炸板率（简化为连续板占比的逆向指标）
            zhaban_rate = 1 - (total_limit_stocks / max(1, limit_up_count))
            
            # 情绪指数
            emotion_index = min(100, (limit_up_count / 50) * 100)
            
            sentiment = MarketSentiment(
                limit_up_count=limit_up_count,
                limit_times_distribution=times_dist,
                avg_open_times=float(avg_open_times),
                total_limit_stocks=total_limit_stocks,
                zhaban_rate=float(zhaban_rate),
                emotion_index=float(emotion_index)
            )
            
            logger.info(f"市场情绪分析完成：涨停{limit_up_count}只，连板{total_limit_stocks}只")
            return sentiment
            
        except Exception as e:
            logger.error(f"市场情绪分析失败: {e}")
            # 返回默认值
            return MarketSentiment(
                limit_up_count=0,
                limit_times_distribution={},
                avg_open_times=0.0,
                total_limit_stocks=0,
                zhaban_rate=0.0,
                emotion_index=0.0
            )
