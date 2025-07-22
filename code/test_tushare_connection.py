#!/usr/bin/env python3
"""
Tushare API连接测试脚本
验证用户Token是否有效，以及策略所需的核心API是否可正常调用
"""

import tushare as ts
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

# 设置Tushare Token
TUSHARE_TOKEN = "2876ea85cb005fb5fa17c809a98174f2d5aae8b1f830110a5ead6211"
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()

def test_basic_connection():
    """测试基础连接"""
    print("=== 测试Tushare API基础连接 ===")
    try:
        # 获取交易日历
        trade_cal = pro.trade_cal(exchange='SSE', start_date='20250720', end_date='20250722')
        print(f"✅ 基础连接成功，获取到 {len(trade_cal)} 条交易日历数据")
        print(f"最新交易日: {trade_cal.iloc[-1]['cal_date']}")
        return True
    except Exception as e:
        print(f"❌ 基础连接失败: {e}")
        return False

def test_stock_basic():
    """测试股票基础信息接口"""
    print("\n=== 测试股票基础信息接口 ===")
    try:
        # 获取股票基础信息
        stocks = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,market,list_date')
        print(f"✅ 股票基础信息接口正常，获取到 {len(stocks)} 只股票")
        
        # 筛选一些样本股票用于后续测试
        sample_stocks = stocks.head(10)['ts_code'].tolist()
        print(f"样本股票代码: {sample_stocks[:5]}...")
        return sample_stocks
    except Exception as e:
        print(f"❌ 股票基础信息接口失败: {e}")
        return []

def test_daily_data(stock_codes):
    """测试日线行情数据"""
    print("\n=== 测试日线行情数据接口 ===")
    try:
        # 获取最近一个交易日的数据
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')
        
        daily_data = pro.daily(ts_code=stock_codes[0], start_date=start_date, end_date=end_date)
        print(f"✅ 日线数据接口正常，{stock_codes[0]} 获取到 {len(daily_data)} 条记录")
        
        if len(daily_data) > 0:
            latest = daily_data.iloc[0]
            print(f"最新数据: {latest['trade_date']} 收盘价: {latest['close']}")
        return True
    except Exception as e:
        print(f"❌ 日线数据接口失败: {e}")
        return False

def test_daily_basic(stock_codes):
    """测试每日基本面数据（流通市值等）"""
    print("\n=== 测试每日基本面数据接口 ===")
    try:
        trade_date = '20250719'  # 使用固定日期避免非交易日问题
        
        daily_basic = pro.daily_basic(ts_code=stock_codes[0], trade_date=trade_date, 
                                     fields='ts_code,trade_date,close,turnover_rate,volume_ratio,pe,pb,ps,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv')
        print(f"✅ 每日基本面数据接口正常，获取到 {len(daily_basic)} 条记录")
        
        if len(daily_basic) > 0:
            data = daily_basic.iloc[0]
            print(f"流通市值: {data['circ_mv']}万元, 换手率: {data['turnover_rate']}%")
        return True
    except Exception as e:
        print(f"❌ 每日基本面数据接口失败: {e}")
        return False

def test_limit_list():
    """测试涨跌停统计数据"""
    print("\n=== 测试涨跌停统计数据接口 ===")
    try:
        # 获取最近的涨停统计
        trade_date = '20250719'
        
        limit_data = pro.limit_list_d(trade_date=trade_date)
        print(f"✅ 涨跌停统计接口正常，{trade_date} 获取到 {len(limit_data)} 条记录")
        
        if len(limit_data) > 0:
            print(f"涨停家数: {limit_data['up_count'].iloc[0]}, 跌停家数: {limit_data['down_count'].iloc[0]}")
        return True
    except Exception as e:
        print(f"❌ 涨跌停统计接口失败: {e}")
        return False

def test_stk_limit():
    """测试涨跌停股票明细"""
    print("\n=== 测试涨跌停股票明细接口 ===")
    try:
        trade_date = '20250719'
        
        limit_stocks = pro.stk_limit(trade_date=trade_date, limit_type='U')
        print(f"✅ 涨停股票明细接口正常，{trade_date} 获取到 {len(limit_stocks)} 只涨停股")
        
        if len(limit_stocks) > 0:
            sample = limit_stocks.head(3)
            print(f"涨停股票样本: {sample[['ts_code', 'name', 'pct_chg']].to_string(index=False)}")
        return True
    except Exception as e:
        print(f"❌ 涨停股票明细接口失败: {e}")
        return False

def test_moneyflow():
    """测试资金流向数据"""
    print("\n=== 测试资金流向数据接口 ===")
    try:
        trade_date = '20250719'
        
        # 获取个股资金流向
        moneyflow = pro.moneyflow(trade_date=trade_date, limit=10)
        print(f"✅ 资金流向接口正常，{trade_date} 获取到 {len(moneyflow)} 条记录")
        
        if len(moneyflow) > 0:
            sample = moneyflow.head(3)
            print(f"资金流向样本: {sample[['ts_code', 'buy_lg_amount', 'sell_lg_amount']].to_string(index=False)}")
        return True
    except Exception as e:
        print(f"❌ 资金流向接口失败: {e}")
        return False

def test_top_list():
    """测试龙虎榜数据"""
    print("\n=== 测试龙虎榜数据接口 ===")
    try:
        trade_date = '20250719'
        
        top_list = pro.top_list(trade_date=trade_date)
        print(f"✅ 龙虎榜接口正常，{trade_date} 获取到 {len(top_list)} 条记录")
        
        if len(top_list) > 0:
            sample = top_list.head(3)
            print(f"龙虎榜样本: {sample[['ts_code', 'name', 'pct_chg']].to_string(index=False)}")
        return True
    except Exception as e:
        print(f"❌ 龙虎榜接口失败: {e}")
        return False

def test_top_inst():
    """测试龙虎榜机构交易明细"""
    print("\n=== 测试龙虎榜机构明细接口 ===")
    try:
        trade_date = '20250719'
        
        top_inst = pro.top_inst(trade_date=trade_date)
        print(f"✅ 龙虎榜机构明细接口正常，{trade_date} 获取到 {len(top_inst)} 条记录")
        
        if len(top_inst) > 0:
            sample = top_inst.head(3)
            print(f"机构明细样本: {sample[['ts_code', 'exalter', 'buy', 'sell']].to_string(index=False)}")
        return True
    except Exception as e:
        print(f"❌ 龙虎榜机构明细接口失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试Tushare API连接和核心接口...")
    print(f"Token: {TUSHARE_TOKEN[:20]}...")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试结果统计
    test_results = {}
    
    # 1. 测试基础连接
    test_results['基础连接'] = test_basic_connection()
    
    if not test_results['基础连接']:
        print("\n❌ 基础连接失败，请检查Token是否正确")
        return
    
    # 2. 测试股票基础信息
    stock_codes = test_stock_basic()
    test_results['股票基础信息'] = len(stock_codes) > 0
    
    if len(stock_codes) == 0:
        print("\n❌ 无法获取股票列表，后续测试可能受影响")
        stock_codes = ['000001.SZ']  # 使用默认股票代码
    
    # 3. 测试各个核心接口
    test_results['日线数据'] = test_daily_data(stock_codes)
    test_results['每日基本面'] = test_daily_basic(stock_codes)
    test_results['涨跌停统计'] = test_limit_list()
    test_results['涨停明细'] = test_stk_limit()
    test_results['资金流向'] = test_moneyflow()
    test_results['龙虎榜'] = test_top_list()
    test_results['龙虎榜机构'] = test_top_inst()
    
    # 输出测试结果总结
    print("\n" + "="*50)
    print("📊 测试结果总结:")
    print("="*50)
    
    success_count = 0
    total_count = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 成功" if result else "❌ 失败"
        print(f"{test_name:12} : {status}")
        if result:
            success_count += 1
    
    print("-"*50)
    print(f"总体通过率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("\n🎉 所有接口测试通过！可以开始构建量化选股系统。")
    elif success_count >= total_count * 0.7:
        print("\n⚠️  大部分接口正常，可以继续开发，但需注意失败的接口。")
    else:
        print("\n🚨 多个接口测试失败，请检查Token权限或网络连接。")
    
    # 保存测试结果
    result_file = '/workspace/extract/tushare_test_results.json'
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_time': datetime.now().isoformat(),
            'token_prefix': TUSHARE_TOKEN[:20],
            'results': test_results,
            'success_rate': success_count/total_count
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n测试结果已保存到: {result_file}")

if __name__ == "__main__":
    main()
