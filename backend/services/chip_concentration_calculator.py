"""
增强筹码集中度计算器 - 基于换手率递推法的筹码分布建模
实现科学的筹码分布计算和获利盘比例分析
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, List
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ChipConcentrationCalculator:
    """
    筹码集中度和获利盘比例计算器
    采用基于换手率的日线递推法构建筹码分布模型
    """
    
    def __init__(self, lookback_days: int = 60, price_step: float = 0.01):
        """
        初始化计算器
        
        Args:
            lookback_days: 历史数据回看天数，用于筹码分布计算
            price_step: 价格分桶步长（元），默认0.01元
        """
        self.lookback_days = lookback_days
        self.price_step = price_step
    
    def calculate_chip_concentration(self, current_price: float, 
                                   historical_data: pd.DataFrame) -> Dict[str, float]:
        """
        计算筹码集中度和获利盘比例
        
        Args:
            current_price: 当前股价
            historical_data: 历史数据，包含 close, high, low, volume, turnover_rate 等字段
           
        Returns:
            Dict包含: chip_concentration, profit_ratio, chip_stability 等指标
        """
        try:
            # 检查数据有效性
            if historical_data.empty or len(historical_data) < 3:
                logger.warning("历史数据不足，使用简化计算")
                return self._fallback_calculation(current_price, historical_data)
            
            # 使用换手率递推法计算筹码分布
            prices, chip_distribution = self._calculate_chip_distribution_recursive(historical_data)
            
            if not chip_distribution or len(chip_distribution) == 0:
                return self._fallback_calculation(current_price, historical_data)
            
            # 计算筹码集中度（基尼系数）
            concentration = self._calculate_gini_concentration(chip_distribution)
            
            # 计算获利盘比例
            profit_ratio = self._calculate_profit_ratio_from_distribution(
                current_price, prices, chip_distribution
            )
            
            # 计算筹码稳定性
            stability = self._calculate_chip_stability(historical_data)
            
            # 计算集中度峰值信息
            peak_info = self._analyze_distribution_peaks(prices, chip_distribution, current_price)
            
            return {
                'chip_concentration': round(concentration, 4),
                'profit_ratio': round(profit_ratio, 4),
                'chip_stability': round(stability, 4),
                'calculation_method': 'turnover_rate_recursive',
                'cost_levels': len([v for v in chip_distribution if v > 0]),
                'data_days': len(historical_data),
                'main_cost_area': peak_info['main_cost_price'],
                'cost_concentration_degree': peak_info['concentration_degree']
            }
            
        except Exception as e:
            logger.warning(f"筹码集中度计算失败，使用后备方案: {e}")
            return self._fallback_calculation(current_price, historical_data)
    
    def _calculate_chip_distribution_recursive(self, historical_data: pd.DataFrame) -> Tuple[List[float], List[float]]:
        """
        基于换手率的日线递推法计算筹码分布
        
        核心算法：
        1. 旧筹码衰减：D'[i] = D[i] * (1 - turnover_rate)
        2. 新筹码注入：将当日成交量按价格区间分布
        3. 递推更新：D_new = D_old_decayed + D_new_trades
        
        Returns:
            Tuple[价格刻度列表, 筹码分布列表]
        """
        # 1. 初始化价格分桶
        global_low = historical_data['low'].min()
        global_high = historical_data['high'].max()
        
        # 扩展价格范围以防边界问题
        price_range = global_high - global_low
        global_low = global_low - price_range * 0.1
        global_high = global_high + price_range * 0.1
        
        prices = self._init_price_bins(global_low, global_high)
        
        # 2. 初始化筹码分布（第一天所有筹码按价格区间分布）
        chip_distribution = [0.0] * len(prices)
        
        # 获取第一个交易日数据
        first_day = historical_data.iloc[0]
        float_shares = self._estimate_float_shares(first_day)
        
        # 初始分布：假设所有流通筹码在第一天的价格区间内
        chip_distribution = self._distribute_volume_triangle(
            chip_distribution, prices, 
            first_day['low'], first_day['high'], 
            self._compute_vwap(first_day),
            float_shares
        )
        
        # 3. 递推计算每日筹码分布
        for idx in range(1, len(historical_data)):
            day_data = historical_data.iloc[idx]
            
            # 计算换手率
            turnover_rate = day_data.get('turnover_rate', 0)
            if pd.isna(turnover_rate) or turnover_rate <= 0:
                # 如果没有换手率数据，用成交量估算
                volume = day_data.get('volume', 0)
                turnover_rate = min(1.0, volume / float_shares) if float_shares > 0 else 0.05
            
            # 限制换手率在合理范围
            turnover_rate = max(0.001, min(1.0, turnover_rate))
            
            # 步骤1：旧筹码衰减
            retention_rate = 1.0 - turnover_rate
            chip_distribution = [vol * retention_rate for vol in chip_distribution]
            
            # 步骤2：新筹码注入
            new_volume = day_data.get('volume', 0)
            if new_volume > 0:
                vwap = self._compute_vwap(day_data)
                chip_distribution = self._distribute_volume_triangle(
                    chip_distribution, prices,
                    day_data['low'], day_data['high'],
                    vwap, new_volume
                )
            
            # 步骤3：归一化（防止累积误差）
            total_volume = sum(chip_distribution)
            if total_volume > 0:
                scale_factor = float_shares / total_volume
                chip_distribution = [vol * scale_factor for vol in chip_distribution]
        
        return prices, chip_distribution
    
    def _init_price_bins(self, min_price: float, max_price: float) -> List[float]:
        """初始化价格分桶"""
        prices = []
        price = min_price
        while price <= max_price:
            prices.append(round(price, 2))
            price += self.price_step
        return prices
    
    def _distribute_volume_triangle(self, distribution: List[float], prices: List[float],
                                  low: float, high: float, vwap: float, volume: float) -> List[float]:
        """
        使用三角分布将成交量分配到价格区间
        以VWAP为中心，向两边递减
        """
        if high <= low or volume <= 0:
            return distribution
        
        # 找到价格区间内的桶索引
        valid_indices = []
        for i, price in enumerate(prices):
            if low <= price <= high:
                valid_indices.append(i)
        
        if not valid_indices:
            return distribution
        
        # 计算三角分布权重
        weights = []
        price_range = high - low
        if price_range < 1e-6:  # 价格区间太小，均匀分布
            weights = [1.0] * len(valid_indices)
        else:
            for idx in valid_indices:
                price = prices[idx]
                # 三角分布：距离VWAP越近权重越大
                distance = abs(price - vwap) / price_range
                weight = max(0.1, 1.0 - distance)  # 最小权重0.1
                weights.append(weight)
        
        # 归一化权重并分配成交量
        total_weight = sum(weights)
        if total_weight > 0:
            for i, (idx, weight) in enumerate(zip(valid_indices, weights)):
                allocation = volume * (weight / total_weight)
                distribution[idx] += allocation
        
        return distribution
    
    def _distribute_volume_uniform(self, distribution: List[float], prices: List[float],
                                 low: float, high: float, volume: float) -> List[float]:
        """均匀分布成交量到价格区间"""
        if high <= low or volume <= 0:
            return distribution
        
        valid_indices = [i for i, price in enumerate(prices) if low <= price <= high]
        if not valid_indices:
            return distribution
        
        allocation_per_bin = volume / len(valid_indices)
        for idx in valid_indices:
            distribution[idx] += allocation_per_bin
        
        return distribution
    
    def _compute_vwap(self, day_data) -> float:
        """
        计算成交量加权平均价格
        如果没有精确数据，使用 (High + Low + Close) / 3 近似
        """
        # 尝试获取精确的VWAP
        if 'vwap' in day_data:
            return day_data['vwap']
        
        # 使用典型价格近似
        high = day_data.get('high', 0)
        low = day_data.get('low', 0)
        close = day_data.get('close', 0)
        
        if high > 0 and low > 0 and close > 0:
            return (high + low + close) / 3
        
        return close if close > 0 else 0
    
    def _estimate_float_shares(self, day_data) -> float:
        """
        估算流通股本
        如果有明确数据最好，否则通过成交量和换手率反推
        """
        # 如果有直接的流通股数据
        if 'float_shares' in day_data:
            return day_data['float_shares']
        
        # 通过成交量和换手率估算
        volume = day_data.get('volume', 0)
        turnover_rate = day_data.get('turnover_rate', 0)
        
        if volume > 0 and turnover_rate > 0:
            estimated_float = volume / (turnover_rate / 100)
            return estimated_float
        
        # 默认估算值（需要根据实际情况调整）
        return 100000000  # 1亿股作为默认值
    
    def _calculate_gini_concentration(self, chip_distribution: List[float]) -> float:
        """
        使用基尼系数计算筹码集中度
        基尼系数越高，筹码越集中
        """
        volumes = [v for v in chip_distribution if v > 0]
        if len(volumes) < 2:
            return 0.5
        
        n = len(volumes)
        total_volume = sum(volumes)
        
        if total_volume <= 0:
            return 0.5
        
        # 计算基尼系数
        gini_sum = 0
        for i in range(n):
            for j in range(n):
                gini_sum += abs(volumes[i] - volumes[j])
        
        gini = gini_sum / (2 * n * total_volume)
        
        # 转换为集中度指标（0-1，越高越集中）
        concentration = min(1.0, gini * 2)
        
        return max(0.1, min(0.95, concentration))
    
    def _calculate_profit_ratio_from_distribution(self, current_price: float, 
                                                prices: List[float], 
                                                chip_distribution: List[float]) -> float:
        """
        从筹码分布精确计算获利盘比例
        获利盘比例 = 成本价低于当前价的筹码量 / 总筹码量
        """
        total_volume = sum(chip_distribution)
        if total_volume <= 0:
            return 0.5
        
        profitable_volume = 0
        for price, volume in zip(prices, chip_distribution):
            if price <= current_price:
                profitable_volume += volume
        
        profit_ratio = profitable_volume / total_volume
        
        # 边界处理
        return max(0.05, min(0.95, profit_ratio))
    
    def _analyze_distribution_peaks(self, prices: List[float], 
                                  chip_distribution: List[float], 
                                  current_price: float) -> Dict:
        """
        分析筹码分布的峰值特征
        """
        if not chip_distribution:
            return {'main_cost_price': current_price, 'concentration_degree': 0.5}
        
        # 找到最大筹码集中的价格区间
        max_volume = max(chip_distribution)
        max_idx = chip_distribution.index(max_volume)
        main_cost_price = prices[max_idx] if max_idx < len(prices) else current_price
        
        # 计算集中度：主要成本区域的筹码占比
        total_volume = sum(chip_distribution)
        if total_volume > 0:
            # 计算主要成本区域（最大值附近的筹码）
            peak_range = max(10, len(prices) // 20)  # 动态确定峰值范围
            start_idx = max(0, max_idx - peak_range // 2)
            end_idx = min(len(chip_distribution), max_idx + peak_range // 2)
            
            peak_volume = sum(chip_distribution[start_idx:end_idx])
            concentration_degree = peak_volume / total_volume
        else:
            concentration_degree = 0.5
        
        return {
            'main_cost_price': main_cost_price,
            'concentration_degree': min(1.0, concentration_degree)
        }
    
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
        
        # 使用变异系数的倒数作为稳定性指标
        mean_turnover = turnover_rates.mean()
        std_turnover = turnover_rates.std()
        
        if mean_turnover <= 0 or std_turnover <= 0:
            return 0.5
        
        cv = std_turnover / mean_turnover  # 变异系数
        stability = 1.0 / (1.0 + cv)  # 变异系数越小，稳定性越高
        
        return max(0.1, min(0.9, stability))
    
    def _fallback_calculation(self, current_price: float, 
                            historical_data: pd.DataFrame) -> Dict[str, float]:
        """
        后备计算方案：简化的筹码集中度和获利盘比例估算
        """
        if historical_data.empty:
            return {
                'chip_concentration': 0.5,
                'profit_ratio': 0.5,
                'chip_stability': 0.5,
                'calculation_method': 'fallback_simple',
                'cost_levels': 0,
                'data_days': 0
            }
        
        # 简化计算
        recent_data = historical_data.tail(10)
        
        # 基于价格波动计算集中度
        price_volatility = recent_data['close'].std() / recent_data['close'].mean()
        concentration = max(0.2, min(0.8, 0.6 - price_volatility))
        
        # 基于涨跌幅估算获利盘比例
        latest_close = recent_data['close'].iloc[-1]
        avg_cost = recent_data['close'].mean()
        
        if avg_cost > 0:
            profit_ratio = 0.5 + (current_price - avg_cost) / avg_cost * 0.3
        else:
            profit_ratio = 0.5
        
        profit_ratio = max(0.1, min(0.9, profit_ratio))
        
        return {
            'chip_concentration': round(concentration, 4),
            'profit_ratio': round(profit_ratio, 4),
            'chip_stability': 0.5,
            'calculation_method': 'fallback_simple',
            'cost_levels': len(recent_data),
            'data_days': len(historical_data)
        }