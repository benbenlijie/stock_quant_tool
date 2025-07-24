"""
增强筹码集中度计算器
基于历史价格和成交量数据计算筹码分布和获利盘比例
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ChipConcentrationCalculator:
    """筹码集中度和获利盘比例计算器"""
    
    def __init__(self, lookback_days: int = 60):
        """
        初始化计算器
        
        Args:
            lookback_days: 历史数据回看天数，用于筹码分布计算
        """
        self.lookback_days = lookback_days
    
    def calculate_chip_concentration(self, current_price: float, 
                                   historical_data: pd.DataFrame) -> Dict[str, float]:
        """
        计算筹码集中度和获利盘比例
        
        Args:
            current_price: 当前股价
            historical_data: 历史数据，包含 close, volume, turnover_rate 等字段
            
        Returns:
            Dict: 包含 chip_concentration, profit_ratio, calculation_method 等
        """
        try:
            if len(historical_data) < 10:
                return self._fallback_calculation(current_price, historical_data)
            
            # 计算筹码分布
            cost_distribution = self._calculate_cost_distribution(historical_data)
            
            if not cost_distribution:
                return self._fallback_calculation(current_price, historical_data)
            
            # 计算筹码集中度
            concentration = self._calculate_concentration_from_distribution(cost_distribution)
            
            # 计算获利盘比例
            profit_ratio = self._calculate_profit_ratio(current_price, cost_distribution)
            
            # 计算筹码稳定性
            stability = self._calculate_chip_stability(historical_data)
            
            # 综合调整
            final_concentration = min(0.95, concentration * (0.8 + 0.2 * stability))
            
            return {
                'chip_concentration': round(final_concentration, 4),
                'profit_ratio': round(profit_ratio, 4),
                'chip_stability': round(stability, 4),
                'calculation_method': 'enhanced_distribution_based',
                'cost_levels': len(cost_distribution),
                'data_days': len(historical_data)
            }
            
        except Exception as e:
            logger.warning(f"筹码集中度计算失败，使用后备方案: {e}")
            return self._fallback_calculation(current_price, historical_data)
    
    def _calculate_cost_distribution(self, historical_data: pd.DataFrame) -> Dict[float, float]:
        """
        基于历史交易数据计算筹码成本分布
        
        使用加权移动平均和成交量衰减模型来估算筹码分布
        """
        cost_distribution = {}
        total_days = len(historical_data)
        
        for i, row in historical_data.iterrows():
            # 计算该交易日的权重（越近期权重越高）
            days_ago = total_days - i - 1
            time_weight = np.exp(-days_ago / 20)  # 20天衰减系数
            
            # 获取价格和成交量
            close_price = row.get('close', 0)
            volume = row.get('volume', 0)
            turnover_rate = row.get('turnover_rate', 0)
            
            if close_price <= 0 or volume <= 0:
                continue
            
            # 计算换手调整系数（换手率越高，筹码变动越大）
            turnover_weight = min(2.0, 1 + turnover_rate / 100)
            
            # 综合权重
            final_weight = time_weight * turnover_weight * volume
            
            # 将筹码分布到价格附近的区间
            # 考虑当日高低价格区间内的筹码分布
            high_price = row.get('high', close_price)
            low_price = row.get('low', close_price)
            
            # 在高低价区间内分布筹码
            price_levels = np.linspace(low_price, high_price, 5)
            for price_level in price_levels:
                price_key = round(price_level, 2)
                if price_key not in cost_distribution:
                    cost_distribution[price_key] = 0
                cost_distribution[price_key] += final_weight / len(price_levels)
        
        return cost_distribution
    
    def _calculate_concentration_from_distribution(self, 
                                                 cost_distribution: Dict[float, float]) -> float:
        """
        从筹码分布计算集中度
        
        使用基尼系数方法计算筹码集中度
        """
        if not cost_distribution:
            return 0.5
        
        # 按价格排序
        prices = sorted(cost_distribution.keys())
        volumes = [cost_distribution[price] for price in prices]
        
        if sum(volumes) == 0:
            return 0.5
        
        # 计算基尼系数
        n = len(volumes)
        total_volume = sum(volumes)
        
        # 计算累积分布
        cumulative_volumes = []
        cumsum = 0
        for vol in volumes:
            cumsum += vol
            cumulative_volumes.append(cumsum / total_volume)
        
        # 基尼系数计算
        gini = 0
        for i in range(n):
            for j in range(n):
                gini += abs(volumes[i] - volumes[j])
        
        gini = gini / (2 * n * total_volume)
        
        # 转换为集中度指标（0-1，越高越集中）
        concentration = min(1.0, gini * 2)
        
        return concentration
    
    def _calculate_profit_ratio(self, current_price: float, 
                               cost_distribution: Dict[float, float]) -> float:
        """
        计算获利盘比例 - 当前价格下的获利筹码比例
        
        Args:
            current_price: 当前股价
            cost_distribution: 筹码成本分布
            
        Returns:
            float: 获利盘比例 (0-1)
        """
        if not cost_distribution:
            return 0.5
        
        profitable_volume = 0
        total_volume = 0
        
        for price, volume in cost_distribution.items():
            total_volume += volume
            if price < current_price:  # 成本价低于当前价格的为获利盘
                profitable_volume += volume
        
        if total_volume == 0:
            return 0.5
        
        profit_ratio = profitable_volume / total_volume
        
        # 边界处理
        return max(0.05, min(0.95, profit_ratio))
    
    def _calculate_chip_stability(self, historical_data: pd.DataFrame) -> float:
        """
        计算筹码稳定性
        
        基于换手率的变异系数来评估筹码稳定性
        """
        if len(historical_data) < 3:
            return 0.5
        
        turnover_rates = historical_data['turnover_rate'].dropna()
        if len(turnover_rates) == 0:
            return 0.5
        
        # 计算变异系数
        mean_turnover = turnover_rates.mean()
        std_turnover = turnover_rates.std()
        
        if mean_turnover == 0:
            return 0.5
        
        cv = std_turnover / mean_turnover
        
        # 转换为稳定性分数（变异系数越低，稳定性越高）
        stability = max(0.0, min(1.0, 1 / (1 + cv)))
        
        return stability
    
    def _calculate_turnover_concentration(self, historical_data: pd.DataFrame) -> float:
        """
        基于换手率模式计算集中度
        
        连续低换手率通常表示筹码集中
        """
        if len(historical_data) < 5:
            return 0.5
        
        turnover_rates = historical_data['turnover_rate'].tail(10)  # 最近10天
        
        # 低换手率天数比例
        low_turnover_days = (turnover_rates < 5).sum()
        low_turnover_ratio = low_turnover_days / len(turnover_rates)
        
        # 换手率标准差（越小表示越稳定）
        turnover_std = turnover_rates.std()
        stability_score = max(0, 1 - turnover_std / 10)
        
        # 综合计算
        concentration = (low_turnover_ratio * 0.6 + stability_score * 0.4)
        
        return max(0.2, min(0.9, concentration))
    
    def _fallback_calculation(self, current_price: float, 
                            historical_data: pd.DataFrame) -> Dict[str, float]:
        """
        后备计算方法
        
        当历史数据不足时使用的简化计算方法
        """
        if len(historical_data) == 0:
            return {
                'chip_concentration': 0.5,
                'profit_ratio': 0.5,
                'calculation_method': 'default_fallback',
                'data_days': 0
            }
        
        # 使用简化的技术指标计算
        recent_data = historical_data.tail(5)
        
        # 基于最近换手率计算集中度
        avg_turnover = recent_data['turnover_rate'].mean() if 'turnover_rate' in recent_data.columns else 5.0
        concentration = max(0.3, min(0.8, 1 - avg_turnover / 20))
        
        # 基于价格趋势估算获利盘比例
        if len(recent_data) >= 2:
            price_change_ratio = (current_price / recent_data['close'].iloc[0] - 1) if recent_data['close'].iloc[0] > 0 else 0
            # 根据涨跌幅估算获利盘
            if price_change_ratio > 0:
                profit_ratio = min(0.9, 0.5 + price_change_ratio * 2)
            else:
                profit_ratio = max(0.1, 0.5 + price_change_ratio)
        else:
            profit_ratio = 0.5  # Default neutral
        
        return {
            'chip_concentration': round(concentration, 4),
            'profit_ratio': round(profit_ratio, 4),
            'calculation_method': 'simplified_technical',
            'data_days': len(historical_data)
        }
    
    def calculate_enhanced_metrics(self, current_price: float, 
                                 historical_data: pd.DataFrame) -> Dict[str, float]:
        """
        计算增强的筹码指标
        
        包括更多维度的筹码分析指标
        """
        basic_result = self.calculate_chip_concentration(current_price, historical_data)
        
        if len(historical_data) < 5:
            return basic_result
        
        try:
            # 计算额外指标
            
            # 1. 筹码密集度 - 筹码在某个价格区间的集中程度
            chip_density = self._calculate_chip_density(current_price, historical_data)
            
            # 2. 筹码变动率 - 筹码结构的变化速度
            chip_change_rate = self._calculate_chip_change_rate(historical_data)
            
            # 3. 成本支撑强度 - 当前价格的成本支撑力度
            cost_support = self._calculate_cost_support(current_price, historical_data)
            
            # 4. 活跃度指标 - 基于成交量和换手率
            activity_index = self._calculate_activity_index(historical_data)
            
            # 更新结果
            basic_result.update({
                'chip_density': round(chip_density, 4),
                'chip_change_rate': round(chip_change_rate, 4),
                'cost_support': round(cost_support, 4),
                'activity_index': round(activity_index, 4),
                'enhanced_calculation': True
            })
            
        except Exception as e:
            logger.warning(f"增强指标计算失败: {e}")
            basic_result['enhanced_calculation'] = False
        
        return basic_result
    
    def _calculate_chip_density(self, current_price: float, 
                               historical_data: pd.DataFrame) -> float:
        """计算筹码密集度"""
        if len(historical_data) < 5:
            return 0.5
        
        # 计算价格区间内的成交量密度
        price_range = historical_data['high'].max() - historical_data['low'].min()
        if price_range == 0:
            return 0.5
        
        # 计算当前价格附近的成交集中度
        price_tolerance = price_range * 0.05  # 5%的价格容忍度
        
        nearby_volumes = []
        for _, row in historical_data.iterrows():
            if abs(row['close'] - current_price) <= price_tolerance:
                nearby_volumes.append(row.get('volume', 0))
        
        if not nearby_volumes:
            return 0.3
        
        total_volume = historical_data['volume'].sum()
        nearby_volume_sum = sum(nearby_volumes)
        
        density = nearby_volume_sum / total_volume if total_volume > 0 else 0
        return max(0.1, min(0.9, density * 5))  # 放大系数
    
    def _calculate_chip_change_rate(self, historical_data: pd.DataFrame) -> float:
        """计算筹码变动率"""
        if len(historical_data) < 10:
            return 0.5
        
        # 基于换手率的滚动标准差计算变动率
        turnover_rates = historical_data['turnover_rate'].tail(10)
        change_rate = turnover_rates.std() / turnover_rates.mean() if turnover_rates.mean() > 0 else 1
        
        # 标准化到0-1范围
        normalized_rate = max(0.1, min(0.9, 1 / (1 + change_rate)))
        return normalized_rate
    
    def _calculate_cost_support(self, current_price: float, 
                               historical_data: pd.DataFrame) -> float:
        """计算成本支撑强度"""
        if len(historical_data) < 5:
            return 0.5
        
        # 统计当前价格下方的成交量（支撑力度）
        support_volume = 0
        total_volume = 0
        
        for _, row in historical_data.iterrows():
            volume = row.get('volume', 0)
            close_price = row.get('close', 0)
            
            total_volume += volume
            
            # 当前价格下方10%范围内的成交量作为支撑
            if close_price <= current_price and close_price >= current_price * 0.9:
                support_volume += volume
        
        support_ratio = support_volume / total_volume if total_volume > 0 else 0
        return max(0.1, min(0.9, support_ratio * 2))
    
    def _calculate_activity_index(self, historical_data: pd.DataFrame) -> float:
        """计算活跃度指标"""
        if len(historical_data) < 5:
            return 0.5
        
        # 基于换手率和成交量变化计算活跃度
        recent_data = historical_data.tail(5)
        
        avg_turnover = recent_data['turnover_rate'].mean()
        volume_cv = recent_data['volume'].std() / recent_data['volume'].mean() if recent_data['volume'].mean() > 0 else 1
        
        # 适度的活跃度较好（既不过于冷清，也不过于狂热）
        optimal_turnover = 8.0
        turnover_score = 1 - abs(avg_turnover - optimal_turnover) / optimal_turnover
        
        # 成交量稳定性
        volume_stability = 1 / (1 + volume_cv)
        
        activity = (turnover_score * 0.6 + volume_stability * 0.4)
        return max(0.1, min(0.9, activity))