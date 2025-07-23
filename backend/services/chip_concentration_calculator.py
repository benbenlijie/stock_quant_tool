import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)

class ChipConcentrationCalculator:
    """
    Advanced chip concentration calculator based on cost distribution analysis.
    
    This implementation uses historical price and volume data to estimate chip distribution
    across different price levels, providing more accurate concentration metrics than
    simple turnover-rate-based calculations.
    """
    
    def __init__(self, lookback_days: int = 60, decay_factor: float = 0.95):
        """
        Initialize the chip concentration calculator.
        
        Args:
            lookback_days: Number of days to look back for historical data
            decay_factor: Decay factor for older transactions (0-1)
        """
        self.lookback_days = lookback_days
        self.decay_factor = decay_factor
        
    def calculate_chip_concentration(self, 
                                   current_price: float,
                                   historical_data: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate comprehensive chip concentration metrics.
        
        Args:
            current_price: Current stock price
            historical_data: DataFrame with columns ['date', 'close', 'volume', 'turnover_rate']
            
        Returns:
            Dict containing concentration metrics
        """
        try:
            if len(historical_data) < 5:
                return self._fallback_calculation(current_price, historical_data)
            
            # Calculate cost distribution
            cost_distribution = self._calculate_cost_distribution(historical_data)
            
            # Calculate concentration index
            concentration_index = self._calculate_concentration_index(cost_distribution)
            
            # Calculate profit ratio
            profit_ratio = self._calculate_profit_ratio(current_price, cost_distribution)
            
            # Calculate chip stability
            chip_stability = self._calculate_chip_stability(historical_data)
            
            # Calculate turnover concentration
            turnover_concentration = self._calculate_turnover_concentration(historical_data)
            
            # Combine multiple factors for final concentration score
            final_concentration = self._combine_concentration_factors(
                concentration_index, chip_stability, turnover_concentration
            )
            
            return {
                'chip_concentration': round(final_concentration, 4),
                'concentration_index': round(concentration_index, 4),
                'profit_ratio': round(profit_ratio, 4),
                'chip_stability': round(chip_stability, 4),
                'turnover_concentration': round(turnover_concentration, 4),
                'calculation_method': 'advanced'
            }
            
        except Exception as e:
            logger.warning(f"Advanced calculation failed: {e}, falling back to simple method")
            return self._fallback_calculation(current_price, historical_data)
    
    def _calculate_cost_distribution(self, historical_data: pd.DataFrame) -> Dict[float, float]:
        """
        Calculate chip cost distribution using volume-weighted price levels.
        
        This method estimates how many chips (shares) were acquired at different price levels
        based on historical trading data with time decay.
        """
        cost_distribution = {}
        
        # Sort data by date (oldest first)
        data = historical_data.sort_values('date').copy()
        
        # Calculate days ago for each record
        latest_date = data['date'].max()
        data['days_ago'] = (latest_date - data['date']).dt.days
        
        for _, row in data.iterrows():
            price = row['close']
            volume = row['volume']
            days_ago = row['days_ago']
            
            # Apply time decay - older transactions have less weight
            decay_weight = self.decay_factor ** (days_ago / 30)  # Monthly decay
            
            # Weight by volume and decay
            weighted_volume = volume * decay_weight
            
            # Group into price buckets (1% intervals)
            price_bucket = round(price * 100) / 100
            
            if price_bucket in cost_distribution:
                cost_distribution[price_bucket] += weighted_volume
            else:
                cost_distribution[price_bucket] = weighted_volume
        
        # Normalize to get distribution percentages
        total_volume = sum(cost_distribution.values())
        if total_volume > 0:
            for price in cost_distribution:
                cost_distribution[price] /= total_volume
        
        return cost_distribution
    
    def _calculate_concentration_index(self, cost_distribution: Dict[float, float]) -> float:
        """
        Calculate chip concentration index using Gini coefficient approach.
        
        Higher values indicate more concentrated chip distribution.
        """
        if not cost_distribution:
            return 0.5
        
        # Sort by volume percentage
        volumes = list(cost_distribution.values())
        volumes.sort()
        
        n = len(volumes)
        if n == 0:
            return 0.5
        
        # Calculate Gini coefficient
        cumsum = np.cumsum(volumes)
        gini = (n + 1 - 2 * sum((n + 1 - i) * y for i, y in enumerate(cumsum))) / (n * sum(volumes))
        
        # Convert Gini to concentration index (0-1, higher = more concentrated)
        concentration = max(0.0, min(1.0, gini))
        
        return concentration
    
    def _calculate_profit_ratio(self, current_price: float, 
                               cost_distribution: Dict[float, float]) -> float:
        """
        Calculate profit ratio - percentage of chips that are profitable at current price.
        """
        if not cost_distribution:
            return 0.5
        
        profitable_volume = 0
        total_volume = 0
        
        for price, volume in cost_distribution.items():
            total_volume += volume
            if price < current_price:  # Profitable chips
                profitable_volume += volume
        
        if total_volume == 0:
            return 0.5
        
        return profitable_volume / total_volume
    
    def _calculate_chip_stability(self, historical_data: pd.DataFrame) -> float:
        """
        Calculate chip stability based on turnover rate variance.
        
        Lower turnover variance indicates more stable chip structure.
        """
        if len(historical_data) < 3:
            return 0.5
        
        turnover_rates = historical_data['turnover_rate'].dropna()
        if len(turnover_rates) == 0:
            return 0.5
        
        # Calculate coefficient of variation
        mean_turnover = turnover_rates.mean()
        std_turnover = turnover_rates.std()
        
        if mean_turnover == 0:
            return 0.5
        
        cv = std_turnover / mean_turnover
        
        # Convert to stability score (lower CV = higher stability)
        stability = max(0.0, min(1.0, 1 / (1 + cv)))
        
        return stability
    
    def _calculate_turnover_concentration(self, historical_data: pd.DataFrame) -> float:
        """
        Calculate concentration based on recent turnover patterns.
        
        High recent turnover suggests chip redistribution and potential concentration.
        """
        if len(historical_data) < 5:
            return 0.5
        
        # Get recent vs historical turnover
        recent_data = historical_data.tail(5)
        historical_avg = historical_data['turnover_rate'].mean()
        recent_avg = recent_data['turnover_rate'].mean()
        
        if historical_avg == 0:
            return 0.5
        
        # Calculate turnover concentration factor
        turnover_ratio = recent_avg / historical_avg
        
        # Convert to concentration score
        # Higher recent turnover suggests redistribution/concentration
        concentration = min(1.0, max(0.1, turnover_ratio * 0.4))
        
        return concentration
    
    def _combine_concentration_factors(self, concentration_index: float, 
                                     chip_stability: float, 
                                     turnover_concentration: float) -> float:
        """
        Combine multiple concentration factors into final score.
        """
        # Weighted combination
        weights = {
            'concentration_index': 0.5,     # Primary factor from cost distribution
            'chip_stability': 0.3,          # Stability indicates locked chips
            'turnover_concentration': 0.2   # Recent activity patterns
        }
        
        final_score = (
            concentration_index * weights['concentration_index'] +
            chip_stability * weights['chip_stability'] +
            turnover_concentration * weights['turnover_concentration']
        )
        
        return max(0.0, min(1.0, final_score))
    
    def _fallback_calculation(self, current_price: float, 
                            historical_data: pd.DataFrame) -> Dict[str, float]:
        """
        Fallback to improved simple calculation when advanced method fails.
        """
        if len(historical_data) == 0:
            return {
                'chip_concentration': 0.65,
                'concentration_index': 0.65,
                'profit_ratio': 0.5,
                'chip_stability': 0.5,
                'turnover_concentration': 0.5,
                'calculation_method': 'fallback_default'
            }
        
        # Get latest data
        latest = historical_data.iloc[-1]
        turnover_rate = latest.get('turnover_rate', 5.0)
        
        # Improved simple calculation
        # Base concentration from turnover (high turnover can indicate redistribution)
        base_concentration = min(0.9, max(0.3, (turnover_rate / 15) * 0.6 + 0.4))
        
        # Adjust based on recent price stability
        if len(historical_data) >= 5:
            recent_prices = historical_data.tail(5)['close']
            price_cv = recent_prices.std() / recent_prices.mean() if recent_prices.mean() > 0 else 0
            stability_factor = max(0.8, min(1.2, 1 - price_cv))
            base_concentration *= stability_factor
        
        # Estimate profit ratio (simplified)
        profit_ratio = 0.5  # Default neutral
        if len(historical_data) >= 10:
            # Compare current price to historical average
            historical_avg = historical_data.tail(30)['close'].mean()
            if historical_avg > 0:
                profit_ratio = min(0.9, max(0.1, current_price / historical_avg - 0.5 + 0.5))
        
        return {
            'chip_concentration': round(base_concentration, 4),
            'concentration_index': round(base_concentration, 4),
            'profit_ratio': round(profit_ratio, 4),
            'chip_stability': 0.5,
            'turnover_concentration': round(min(0.8, turnover_rate / 20), 4),
            'calculation_method': 'fallback_improved'
        }

def calculate_chip_metrics_batch(stocks_data: List[Dict]) -> List[Dict]:
    """
    Calculate chip concentration metrics for multiple stocks in batch.
    
    Args:
        stocks_data: List of stock data dicts with historical data
        
    Returns:
        List of dicts with chip metrics added
    """
    calculator = ChipConcentrationCalculator()
    results = []
    
    for stock_data in stocks_data:
        try:
            current_price = stock_data.get('close', stock_data.get('price', 0))
            historical_data = stock_data.get('historical_data', pd.DataFrame())
            
            if isinstance(historical_data, list):
                historical_data = pd.DataFrame(historical_data)
            
            chip_metrics = calculator.calculate_chip_concentration(current_price, historical_data)
            
            # Merge with original data
            result = stock_data.copy()
            result.update(chip_metrics)
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error calculating chip metrics for stock {stock_data.get('symbol', 'unknown')}: {e}")
            # Fallback
            result = stock_data.copy()
            result.update({
                'chip_concentration': 0.65,
                'profit_ratio': 0.5,
                'calculation_method': 'error_fallback'
            })
            results.append(result)
    
    return results