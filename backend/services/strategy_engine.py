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
            candidates = await self._calculate_chip_concentration(candidates, trade_date)
            
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
    
    async def _calculate_chip_concentration(self, data: pd.DataFrame, trade_date: str) -> pd.DataFrame:
        """计算筹码集中度"""
        try:
            # 简化的筹码集中度计算
            # 实际应用中需要更复杂的历史成交分布计算
            
            chip_scores = []
            for _, row in data.iterrows():
                # 基于换手率和量比的简化筹码集中度
                # 高换手 + 高量比 = 筹码重新分布，集中度相对较高
                concentration = min(0.9, 
                    (row['turnover_rate'] / 100 * 0.6 + 
                     row['volume_ratio'] / 10 * 0.4)
                )
                
                # 确保在合理范围内
                concentration = max(0.3, concentration)
                chip_scores.append(concentration)
            
            data['chip_concentration'] = chip_scores
            
            # 筛选筹码集中度高的股票
            data = data[data['chip_concentration'] >= settings.chip_concentration_threshold]
            
            logger.info(f"筹码集中度计算完成，剩余{len(data)}只股票")
            return data
            
        except Exception as e:
            logger.error(f"筹码集中度计算失败: {e}")
            raise
    
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
