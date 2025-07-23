#!/usr/bin/env python3
"""
简化版筹码集中度计算测试
测试改进的简化计算算法
"""

def calculate_improved_chip_concentration(row) -> tuple[float, float]:
    """改进的筹码集中度计算"""
    turnover_rate = row.get('turnover_rate', 5.0)
    volume_ratio = row.get('volume_ratio', 1.0)
    pct_chg = row.get('pct_chg', 0.0)
    
    # 改进的集中度计算
    base_concentration = 0.5
    
    # 换手率因子：适度换手率最佳
    optimal_turnover = 8.0
    turnover_factor = 1.0 - abs(turnover_rate - optimal_turnover) / 20.0
    turnover_factor = max(0.3, min(1.2, turnover_factor))
    
    # 量比因子：适度放量表示有资金介入
    volume_factor = min(1.3, max(0.7, 0.8 + volume_ratio / 10))
    
    # 涨幅因子：适度上涨配合集中度
    price_factor = 1.0
    if 2 <= pct_chg <= 8:
        price_factor = 1.1
    elif pct_chg > 9:
        price_factor = 1.2
    elif pct_chg < -3:
        price_factor = 0.9
    
    # 综合计算集中度
    concentration = base_concentration * turnover_factor * volume_factor * price_factor
    concentration = max(0.2, min(0.95, concentration))
    
    # 获利盘估算
    profit_ratio = 0.5
    if pct_chg > 0:
        profit_ratio += min(0.3, pct_chg / 30)
    else:
        profit_ratio += max(-0.3, pct_chg / 20)
    
    profit_ratio = max(0.1, min(0.9, profit_ratio))
    
    return concentration, profit_ratio

def old_simple_calculation(row) -> float:
    """旧版简化计算（对比用）"""
    turnover_rate = row.get('turnover_rate', 5.0)
    return min(0.9, max(0.3, turnover_rate / 100 * 0.8))

def test_calculation_comparison():
    """对比新旧算法"""
    print("筹码集中度计算优化对比测试")
    print("=" * 80)
    
    test_cases = [
        {
            'name': '理想龙头股',
            'data': {'turnover_rate': 8.0, 'volume_ratio': 2.5, 'pct_chg': 6.5},
            'expected': '高集中度，高获利盘'
        },
        {
            'name': '涨停板股票',
            'data': {'turnover_rate': 12.0, 'volume_ratio': 3.5, 'pct_chg': 9.95},
            'expected': '很高集中度，很高获利盘'
        },
        {
            'name': '价值蓝筹股',
            'data': {'turnover_rate': 3.0, 'volume_ratio': 1.2, 'pct_chg': 2.1},
            'expected': '中等集中度，中等获利盘'
        },
        {
            'name': '垃圾股票',
            'data': {'turnover_rate': 25.0, 'volume_ratio': 6.0, 'pct_chg': -4.2},
            'expected': '低集中度，低获利盘'
        },
        {
            'name': '横盘整理',
            'data': {'turnover_rate': 4.5, 'volume_ratio': 0.9, 'pct_chg': 0.3},
            'expected': '中等集中度，中等获利盘'
        },
        {
            'name': '庄股操盘',
            'data': {'turnover_rate': 1.8, 'volume_ratio': 0.6, 'pct_chg': 8.5},
            'expected': '较高集中度，高获利盘'
        }
    ]
    
    print(f"{'股票类型':<12} {'换手率':<8} {'量比':<6} {'涨幅':<6} {'旧算法':<8} {'新集中度':<10} {'获利盘':<8} {'改进'}")
    print("-" * 80)
    
    for case in test_cases:
        data = case['data']
        old_result = old_simple_calculation(data)
        new_concentration, profit_ratio = calculate_improved_chip_concentration(data)
        
        improvement = "+" if new_concentration > old_result else "-" if new_concentration < old_result else "="
        
        print(f"{case['name']:<12} "
              f"{data['turnover_rate']:>6.1f}% "
              f"{data['volume_ratio']:>5.1f} "
              f"{data['pct_chg']:>5.1f}% "
              f"{old_result:>7.3f} "
              f"{new_concentration:>9.3f} "
              f"{profit_ratio:>7.3f} "
              f"{improvement:>4}")

def test_strategy_filtering():
    """测试策略筛选效果"""
    print("\n" + "=" * 80)
    print("策略筛选效果测试")
    print("=" * 80)
    
    # 模拟20只股票
    stocks = [
        {'name': '强势龙头A', 'turnover_rate': 8.2, 'volume_ratio': 2.8, 'pct_chg': 7.1},
        {'name': '强势龙头B', 'turnover_rate': 9.1, 'volume_ratio': 3.2, 'pct_chg': 8.5},
        {'name': '题材炒作A', 'turnover_rate': 18.5, 'volume_ratio': 5.2, 'pct_chg': 9.8},
        {'name': '题材炒作B', 'turnover_rate': 22.0, 'volume_ratio': 7.1, 'pct_chg': 6.3},
        {'name': '价值蓝筹A', 'turnover_rate': 2.8, 'volume_ratio': 1.1, 'pct_chg': 2.1},
        {'name': '价值蓝筹B', 'turnover_rate': 3.5, 'volume_ratio': 1.4, 'pct_chg': 3.2},
        {'name': '庄股控盘A', 'turnover_rate': 1.2, 'volume_ratio': 0.8, 'pct_chg': 4.5},
        {'name': '庄股控盘B', 'turnover_rate': 1.8, 'volume_ratio': 0.6, 'pct_chg': 7.8},
        {'name': '垃圾股票A', 'turnover_rate': 28.0, 'volume_ratio': 8.5, 'pct_chg': -3.2},
        {'name': '垃圾股票B', 'turnover_rate': 35.2, 'volume_ratio': 12.0, 'pct_chg': -5.8},
        {'name': '横盘股票A', 'turnover_rate': 4.2, 'volume_ratio': 0.9, 'pct_chg': 0.5},
        {'name': '横盘股票B', 'turnover_rate': 5.1, 'volume_ratio': 1.1, 'pct_chg': -0.2},
        {'name': '反弹股票A', 'turnover_rate': 12.5, 'volume_ratio': 4.2, 'pct_chg': 5.8},
        {'name': '反弹股票B', 'turnover_rate': 15.8, 'volume_ratio': 3.8, 'pct_chg': 4.2},
        {'name': '新股次新A', 'turnover_rate': 45.0, 'volume_ratio': 15.0, 'pct_chg': 2.1},
        {'name': '新股次新B', 'turnover_rate': 38.5, 'volume_ratio': 12.5, 'pct_chg': -1.5},
        {'name': '重组概念A', 'turnover_rate': 7.8, 'volume_ratio': 2.9, 'pct_chg': 9.2},
        {'name': '重组概念B', 'turnover_rate': 6.5, 'volume_ratio': 2.1, 'pct_chg': 6.8},
        {'name': '补涨股票A', 'turnover_rate': 11.2, 'volume_ratio': 3.0, 'pct_chg': 8.8},
        {'name': '补涨股票B', 'turnover_rate': 9.8, 'volume_ratio': 2.6, 'pct_chg': 7.5}
    ]
    
    # 计算所有股票的筹码指标
    results = []
    for stock in stocks:
        concentration, profit_ratio = calculate_improved_chip_concentration(stock)
        old_concentration = old_simple_calculation(stock)
        
        results.append({
            'name': stock['name'],
            'turnover_rate': stock['turnover_rate'],
            'volume_ratio': stock['volume_ratio'],
            'pct_chg': stock['pct_chg'],
            'old_concentration': old_concentration,
            'new_concentration': concentration,
            'profit_ratio': profit_ratio,
            'combined_score': concentration * 0.6 + profit_ratio * 0.4
        })
    
    # 排序
    results.sort(key=lambda x: x['combined_score'], reverse=True)
    
    print("\n所有股票筹码质量排名:")
    print(f"{'排名':<4} {'股票名称':<12} {'换手率':<8} {'集中度(新)':<10} {'获利盘':<8} {'综合分':<8}")
    print("-" * 60)
    
    for i, result in enumerate(results[:10], 1):  # 显示前10名
        print(f"{i:<4} {result['name']:<12} "
              f"{result['turnover_rate']:>6.1f}% "
              f"{result['new_concentration']:>9.3f} "
              f"{result['profit_ratio']:>7.3f} "
              f"{result['combined_score']:>7.3f}")
    
    # 应用策略筛选
    print(f"\n策略筛选结果:")
    print("条件: 筹码集中度 >= 0.65 AND 获利盘比例 >= 0.5")
    print("-" * 50)
    
    # 新算法筛选
    qualified_new = [r for r in results if r['new_concentration'] >= 0.65 and r['profit_ratio'] >= 0.5]
    print(f"\n使用新算法筛选结果 ({len(qualified_new)}只股票):")
    for result in qualified_new:
        print(f"✓ {result['name']} - 集中度:{result['new_concentration']:.3f}, 获利盘:{result['profit_ratio']:.3f}")
    
    # 旧算法筛选
    qualified_old = [r for r in results if r['old_concentration'] >= 0.65]
    print(f"\n使用旧算法筛选结果 ({len(qualified_old)}只股票):")
    for result in qualified_old:
        print(f"? {result['name']} - 集中度:{result['old_concentration']:.3f}")
    
    # 分析改进效果
    print(f"\n算法改进分析:")
    print(f"- 旧算法仅考虑换手率，筛选出 {len(qualified_old)} 只股票")
    print(f"- 新算法综合考虑换手率、量比、涨幅和获利盘，筛选出 {len(qualified_new)} 只股票")
    print(f"- 新算法增加了获利盘指标，提供更全面的筹码分析")

def test_parameter_sensitivity():
    """参数敏感性测试"""
    print("\n" + "=" * 80)
    print("参数敏感性分析")
    print("=" * 80)
    
    print("\n换手率对筹码集中度的影响 (量比=2.0, 涨幅=5.0%):")
    print("换手率(%) | 旧算法 | 新算法 | 获利盘 | 说明")
    print("-" * 55)
    
    for turnover in [1.0, 2.0, 4.0, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0]:
        data = {'turnover_rate': turnover, 'volume_ratio': 2.0, 'pct_chg': 5.0}
        old_result = old_simple_calculation(data)
        new_concentration, profit_ratio = calculate_improved_chip_concentration(data)
        
        if turnover <= 3:
            note = "庄股控盘"
        elif turnover <= 12:
            note = "正常范围"
        else:
            note = "过度活跃"
        
        print(f"{turnover:>8.1f} | {old_result:>6.3f} | {new_concentration:>6.3f} | {profit_ratio:>6.3f} | {note}")
    
    print(f"\n涨幅对获利盘的影响 (换手率=8.0%, 量比=2.0):")
    print("涨幅(%) | 集中度 | 获利盘 | 说明")
    print("-" * 40)
    
    for pct_chg in [-5.0, -2.0, 0.0, 2.0, 5.0, 8.0, 10.0]:
        data = {'turnover_rate': 8.0, 'volume_ratio': 2.0, 'pct_chg': pct_chg}
        concentration, profit_ratio = calculate_improved_chip_concentration(data)
        
        if pct_chg < 0:
            note = "下跌减分"
        elif pct_chg < 2:
            note = "平淡"
        elif pct_chg < 9:
            note = "适度上涨"
        else:
            note = "涨停加分"
        
        print(f"{pct_chg:>6.1f} | {concentration:>6.3f} | {profit_ratio:>6.3f} | {note}")

if __name__ == "__main__":
    try:
        test_calculation_comparison()
        test_strategy_filtering()
        test_parameter_sensitivity()
        
        print("\n" + "=" * 80)
        print("✓ 筹码集中度计算优化测试完成！")
        print("主要改进:")
        print("1. 考虑换手率的合理范围，过高过低都减分")
        print("2. 加入量比因子，反映资金介入程度") 
        print("3. 考虑涨幅影响，适度上涨加分")
        print("4. 增加获利盘比例指标，评估抛压大小")
        print("5. 双重筛选条件，提高选股精度")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()