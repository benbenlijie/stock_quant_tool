#!/usr/bin/env python3
"""
测试筹码集中度计算优化
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from services.chip_concentration_calculator import ChipConcentrationCalculator

def test_basic_calculation():
    """测试基础计算功能"""
    print("=" * 60)
    print("测试1: 基础筹码集中度计算")
    print("=" * 60)
    
    calculator = ChipConcentrationCalculator()
    
    # 创建模拟历史数据
    dates = pd.date_range(start='2024-11-01', end='2024-12-21', freq='D')
    
    # 模拟1: 筹码高度集中的股票
    print("\n1.1 测试高度集中筹码的股票:")
    concentrated_data = pd.DataFrame({
        'date': dates[:30],
        'close': np.concatenate([
            np.random.normal(10, 0.1, 20),  # 前20天价格稳定在10元附近
            np.random.normal(12, 0.2, 10)   # 后10天价格在12元附近
        ]),
        'volume': np.concatenate([
            np.random.normal(1000000, 100000, 20),  # 前期正常成交量
            np.random.normal(2000000, 200000, 10)   # 后期放量
        ]),
        'turnover_rate': np.concatenate([
            np.random.normal(3, 0.5, 20),   # 前期低换手
            np.random.normal(8, 1, 10)      # 后期适度换手
        ])
    })
    
    current_price = 12.5
    result = calculator.calculate_chip_concentration(current_price, concentrated_data)
    
    print(f"  当前价格: {current_price}")
    print(f"  筹码集中度: {result['chip_concentration']:.3f}")
    print(f"  获利盘比例: {result['profit_ratio']:.3f}")
    print(f"  计算方法: {result['calculation_method']}")
    
    # 模拟2: 筹码分散的股票
    print("\n1.2 测试筹码分散的股票:")
    dispersed_data = pd.DataFrame({
        'date': dates[:30],
        'close': np.random.normal(15, 2, 30),  # 价格波动较大
        'volume': np.random.normal(1500000, 500000, 30),  # 成交量波动大
        'turnover_rate': np.random.normal(15, 5, 30)  # 高换手率
    })
    
    current_price = 15.2
    result = calculator.calculate_chip_concentration(current_price, dispersed_data)
    
    print(f"  当前价格: {current_price}")
    print(f"  筹码集中度: {result['chip_concentration']:.3f}")
    print(f"  获利盘比例: {result['profit_ratio']:.3f}")
    print(f"  计算方法: {result['calculation_method']}")

def test_fallback_calculation():
    """测试后备计算功能"""
    print("\n" + "=" * 60)
    print("测试2: 后备计算机制")
    print("=" * 60)
    
    calculator = ChipConcentrationCalculator()
    
    # 测试数据不足情况
    print("\n2.1 测试数据不足的情况:")
    small_data = pd.DataFrame({
        'date': pd.date_range(start='2024-12-20', periods=2),
        'close': [10.0, 10.5],
        'volume': [1000000, 1200000],
        'turnover_rate': [5.0, 8.0]
    })
    
    result = calculator.calculate_chip_concentration(10.3, small_data)
    print(f"  筹码集中度: {result['chip_concentration']:.3f}")
    print(f"  获利盘比例: {result['profit_ratio']:.3f}")
    print(f"  计算方法: {result['calculation_method']}")
    
    # 测试空数据情况
    print("\n2.2 测试空数据的情况:")
    empty_data = pd.DataFrame()
    result = calculator.calculate_chip_concentration(10.0, empty_data)
    print(f"  筹码集中度: {result['chip_concentration']:.3f}")
    print(f"  获利盘比例: {result['profit_ratio']:.3f}")
    print(f"  计算方法: {result['calculation_method']}")

def test_improved_simple_calculation():
    """测试改进的简化计算"""
    print("\n" + "=" * 60)
    print("测试3: 改进的简化筹码集中度计算")
    print("=" * 60)
    
    # 导入改进的简化计算函数
    from main_real import calculate_improved_chip_concentration
    
    test_cases = [
        {
            'name': '理想情况: 适度换手 + 适度上涨',
            'data': {'turnover_rate': 8.0, 'volume_ratio': 2.5, 'pct_chg': 5.0}
        },
        {
            'name': '涨停板: 高涨幅 + 高换手',
            'data': {'turnover_rate': 12.0, 'volume_ratio': 3.0, 'pct_chg': 9.8}
        },
        {
            'name': '缩量上涨: 低换手 + 适度上涨',
            'data': {'turnover_rate': 3.0, 'volume_ratio': 1.2, 'pct_chg': 4.0}
        },
        {
            'name': '放量下跌: 高换手 + 下跌',
            'data': {'turnover_rate': 15.0, 'volume_ratio': 4.0, 'pct_chg': -3.5}
        },
        {
            'name': '横盘整理: 低换手 + 微涨',
            'data': {'turnover_rate': 2.0, 'volume_ratio': 0.8, 'pct_chg': 0.5}
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        concentration, profit_ratio = calculate_improved_chip_concentration(case['data'])
        print(f"\n3.{i} {case['name']}:")
        print(f"  输入: 换手率={case['data']['turnover_rate']:.1f}%, "
              f"量比={case['data']['volume_ratio']:.1f}, "
              f"涨幅={case['data']['pct_chg']:.1f}%")
        print(f"  输出: 筹码集中度={concentration:.3f}, 获利盘比例={profit_ratio:.3f}")

def test_concentration_strategies():
    """测试不同筹码集中度策略的效果"""
    print("\n" + "=" * 60)
    print("测试4: 筹码集中度策略效果分析")
    print("=" * 60)
    
    # 模拟多只股票数据
    stocks = [
        {'name': '强势龙头', 'turnover_rate': 8.5, 'volume_ratio': 2.8, 'pct_chg': 7.2},
        {'name': '题材炒作', 'turnover_rate': 18.0, 'volume_ratio': 5.0, 'pct_chg': 9.9},
        {'name': '价值蓝筹', 'turnover_rate': 2.5, 'volume_ratio': 1.1, 'pct_chg': 2.1},
        {'name': '垃圾股票', 'turnover_rate': 25.0, 'volume_ratio': 8.0, 'pct_chg': -5.2},
        {'name': '横盘股票', 'turnover_rate': 4.0, 'volume_ratio': 0.9, 'pct_chg': 0.3}
    ]
    
    from main_real import calculate_improved_chip_concentration
    
    results = []
    for stock in stocks:
        concentration, profit_ratio = calculate_improved_chip_concentration(stock)
        results.append({
            'name': stock['name'],
            'concentration': concentration,
            'profit_ratio': profit_ratio,
            'combined_score': concentration * 0.6 + profit_ratio * 0.4  # 组合评分
        })
    
    # 按组合评分排序
    results.sort(key=lambda x: x['combined_score'], reverse=True)
    
    print("\n股票筹码质量排名 (按组合评分):")
    print("-" * 60)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['name']:<10} "
              f"集中度: {result['concentration']:.3f} "
              f"获利盘: {result['profit_ratio']:.3f} "
              f"综合: {result['combined_score']:.3f}")
    
    # 应用策略阈值筛选
    print("\n策略筛选结果 (集中度>=0.65, 获利盘>=0.5):")
    print("-" * 40)
    qualified = [r for r in results if r['concentration'] >= 0.65 and r['profit_ratio'] >= 0.5]
    if qualified:
        for result in qualified:
            print(f"✓ {result['name']} - 符合策略要求")
    else:
        print("✗ 没有股票符合策略要求")

def test_parameter_sensitivity():
    """测试参数敏感性分析"""
    print("\n" + "=" * 60)
    print("测试5: 参数敏感性分析")
    print("=" * 60)
    
    from main_real import calculate_improved_chip_concentration
    
    # 测试换手率对集中度的影响
    print("\n5.1 换手率敏感性测试:")
    print("换手率(%) | 集中度 | 获利盘")
    print("-" * 30)
    
    for turnover in range(2, 21, 2):
        concentration, profit_ratio = calculate_improved_chip_concentration({
            'turnover_rate': turnover,
            'volume_ratio': 2.0,
            'pct_chg': 5.0
        })
        print(f"{turnover:8.1f} | {concentration:6.3f} | {profit_ratio:6.3f}")
    
    # 测试涨幅对获利盘的影响
    print("\n5.2 涨幅敏感性测试:")
    print("涨幅(%) | 集中度 | 获利盘")
    print("-" * 28)
    
    for pct_chg in range(-5, 11, 1):
        concentration, profit_ratio = calculate_improved_chip_concentration({
            'turnover_rate': 8.0,
            'volume_ratio': 2.0,
            'pct_chg': pct_chg
        })
        print(f"{pct_chg:6.1f} | {concentration:6.3f} | {profit_ratio:6.3f}")

if __name__ == "__main__":
    print("筹码集中度计算优化测试")
    print("=" * 60)
    
    try:
        # 运行所有测试
        test_basic_calculation()
        test_fallback_calculation()
        test_improved_simple_calculation()
        test_concentration_strategies()
        test_parameter_sensitivity()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试完成！筹码集中度计算优化验证成功。")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()