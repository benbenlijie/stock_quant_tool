#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare Pro API 连续涨停板量化选股策略演示代码
演示如何使用Tushare Pro API获取策略所需的关键数据

作者: MiniMax Agent
日期: 2025-07-22
"""

import tushare as ts
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

class TushareStrategyDemo:
    def __init__(self, token):
        """
        初始化Tushare API
        
        参数:
        token (str): Tushare Pro API Token
        """
        ts.set_token(token)
        self.pro = ts.pro_api()
        
    def get_stock_basic_info(self):
        """
        获取股票基础信息，用于初筛
        排除ST股票，筛选市值条件等
        """
        print("正在获取股票基础信息...")
        
        # 获取股票基础列表
        stock_basic = self.pro.stock_basic(
            exchange='',
            list_status='L',  # 仅获取上市股票
            fields='ts_code,symbol,name,area,industry,market,list_date'
        )
        
        # 过滤ST股票和特殊股票
        stock_basic = stock_basic[~stock_basic['name'].str.contains('ST|\\*ST|退', na=False)]
        
        print(f"获取到 {len(stock_basic)} 只非ST股票")
        return stock_basic
    
    def get_daily_basic_data(self, trade_date=None):
        """
        获取每日基本面数据
        包括市值、换手率、量比等关键指标
        
        参数:
        trade_date (str): 交易日期，格式YYYYMMDD
        """
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y%m%d')
            
        print(f"正在获取 {trade_date} 每日基本面数据...")
        
        try:
            daily_basic = self.pro.daily_basic(
                trade_date=trade_date,
                fields='ts_code,trade_date,close,turnover_rate,volume_ratio,pe,pb,total_mv,circ_mv'
            )
            
            print(f"获取到 {len(daily_basic)} 只股票的基本面数据")
            return daily_basic
        except Exception as e:
            print(f"获取每日基本面数据失败: {e}")
            return pd.DataFrame()
    
    def get_daily_price_data(self, trade_date=None):
        """
        获取日线行情数据
        包括OHLCV和涨跌幅数据
        
        参数:
        trade_date (str): 交易日期，格式YYYYMMDD
        """
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y%m%d')
            
        print(f"正在获取 {trade_date} 日线行情数据...")
        
        try:
            daily_data = self.pro.daily(
                trade_date=trade_date,
                fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount'
            )
            
            print(f"获取到 {len(daily_data)} 只股票的行情数据")
            return daily_data
        except Exception as e:
            print(f"获取日线行情数据失败: {e}")
            return pd.DataFrame()
    
    def get_limit_list_data(self, trade_date=None):
        """
        获取涨停股票列表
        包括涨停、跌停、炸板数据
        
        参数:
        trade_date (str): 交易日期，格式YYYYMMDD
        """
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y%m%d')
            
        print(f"正在获取 {trade_date} 涨停股票数据...")
        
        try:
            limit_data = self.pro.limit_list_d(
                trade_date=trade_date,
                fields='trade_date,ts_code,name,close,pct_chg,amount,turnover_ratio,fd_amount,first_time,last_time,open_times,limit_times,limit'
            )
            
            print(f"获取到 {len(limit_data)} 只涨跌停股票数据")
            return limit_data
        except Exception as e:
            print(f"获取涨停股票数据失败: {e}")
            return pd.DataFrame()
    
    def get_moneyflow_data(self, trade_date=None, ts_codes=None):
        """
        获取资金流向数据
        分析大单、特大单净流入情况
        
        参数:
        trade_date (str): 交易日期，格式YYYYMMDD
        ts_codes (list): 股票代码列表
        """
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y%m%d')
            
        print(f"正在获取 {trade_date} 资金流向数据...")
        
        try:
            if ts_codes:
                # 分批获取指定股票的资金流向
                all_moneyflow = []
                for i in range(0, len(ts_codes), 50):  # 每次获取50只股票
                    batch_codes = ts_codes[i:i+50]
                    for code in batch_codes:
                        try:
                            mf_data = self.pro.moneyflow(
                                ts_code=code,
                                trade_date=trade_date,
                                fields='ts_code,trade_date,buy_lg_amount,sell_lg_amount,buy_elg_amount,sell_elg_amount,net_mf_amount'
                            )
                            if not mf_data.empty:
                                all_moneyflow.append(mf_data)
                            time.sleep(0.1)  # 避免频率限制
                        except:
                            continue
                
                if all_moneyflow:
                    moneyflow_data = pd.concat(all_moneyflow, ignore_index=True)
                else:
                    moneyflow_data = pd.DataFrame()
            else:
                # 获取全市场资金流向数据（可能受积分限制）
                moneyflow_data = self.pro.moneyflow(
                    trade_date=trade_date,
                    fields='ts_code,trade_date,buy_lg_amount,sell_lg_amount,buy_elg_amount,sell_elg_amount,net_mf_amount'
                )
            
            print(f"获取到 {len(moneyflow_data)} 只股票的资金流向数据")
            return moneyflow_data
        except Exception as e:
            print(f"获取资金流向数据失败: {e}")
            return pd.DataFrame()
    
    def get_top_list_data(self, trade_date=None):
        """
        获取龙虎榜数据
        分析游资动向和净买入情况
        
        参数:
        trade_date (str): 交易日期，格式YYYYMMDD
        """
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y%m%d')
            
        print(f"正在获取 {trade_date} 龙虎榜数据...")
        
        try:
            top_list = self.pro.top_list(
                trade_date=trade_date,
                fields='trade_date,ts_code,name,close,pct_change,turnover_rate,amount,l_buy,l_sell,net_amount,net_rate,reason'
            )
            
            print(f"获取到 {len(top_list)} 只股票的龙虎榜数据")
            return top_list
        except Exception as e:
            print(f"获取龙虎榜数据失败: {e}")
            return pd.DataFrame()
    
    def calculate_market_cap_filter(self, daily_basic_data, max_circ_mv=5000000):
        """
        计算市值筛选条件
        筛选流通市值小于50亿的股票
        
        参数:
        daily_basic_data (DataFrame): 每日基本面数据
        max_circ_mv (float): 最大流通市值（万元），默认5000000万元=50亿元
        """
        print("正在进行市值筛选...")
        
        # 筛选流通市值小于50亿的股票
        filtered_data = daily_basic_data[
            (daily_basic_data['circ_mv'] <= max_circ_mv) & 
            (daily_basic_data['circ_mv'] > 0)
        ].copy()
        
        print(f"市值筛选后剩余 {len(filtered_data)} 只股票")
        return filtered_data
    
    def analyze_volume_price_signals(self, daily_data, daily_basic_data):
        """
        分析量价突破信号
        筛选放量涨停或接近涨停的股票
        
        参数:
        daily_data (DataFrame): 日线行情数据
        daily_basic_data (DataFrame): 每日基本面数据
        """
        print("正在分析量价突破信号...")
        
        # 合并数据
        merged_data = daily_data.merge(daily_basic_data, on=['ts_code', 'trade_date'], how='inner')
        
        # 筛选条件
        volume_price_signals = merged_data[
            (merged_data['pct_chg'] >= 9.0) &  # 涨幅大于9%
            (merged_data['turnover_rate'] >= 10.0) &  # 换手率大于10%
            (merged_data['volume_ratio'] >= 2.0) &  # 量比大于2
            (merged_data['amount'] > 10000)  # 成交额大于1亿元
        ].copy()
        
        print(f"量价突破信号筛选后剩余 {len(volume_price_signals)} 只股票")
        return volume_price_signals
    
    def analyze_capital_flow_signals(self, moneyflow_data, top_list_data):
        """
        分析资金流向信号
        筛选主力资金净流入的股票
        
        参数:
        moneyflow_data (DataFrame): 资金流向数据
        top_list_data (DataFrame): 龙虎榜数据
        """
        print("正在分析资金流向信号...")
        
        # 计算大单净流入
        if not moneyflow_data.empty:
            moneyflow_data['large_net_inflow'] = (
                moneyflow_data['buy_lg_amount'] - moneyflow_data['sell_lg_amount'] +
                moneyflow_data['buy_elg_amount'] - moneyflow_data['sell_elg_amount']
            )
            
            # 筛选大单净流入为正的股票
            positive_flow = moneyflow_data[
                (moneyflow_data['large_net_inflow'] > 0) &
                (moneyflow_data['net_mf_amount'] > 1000)  # 净流入超过1000万
            ]['ts_code'].tolist()
        else:
            positive_flow = []
        
        # 分析龙虎榜净买入
        if not top_list_data.empty:
            positive_top_list = top_list_data[
                (top_list_data['net_amount'] > 0) &  # 龙虎榜净买入为正
                (top_list_data['net_rate'] > 5)  # 净买额占比大于5%
            ]['ts_code'].tolist()
        else:
            positive_top_list = []
        
        # 合并资金流向信号
        capital_signals = list(set(positive_flow + positive_top_list))
        
        print(f"资金流向信号筛选出 {len(capital_signals)} 只股票")
        return capital_signals
    
    def comprehensive_screening(self, trade_date=None):
        """
        综合筛选策略
        整合所有筛选条件，找出符合连板潜力的股票
        
        参数:
        trade_date (str): 交易日期，格式YYYYMMDD
        """
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y%m%d')
            
        print(f"\n开始综合筛选策略 - 交易日期: {trade_date}")
        print("="*50)
        
        # 1. 获取基础数据
        stock_basic = self.get_stock_basic_info()
        daily_basic = self.get_daily_basic_data(trade_date)
        daily_data = self.get_daily_price_data(trade_date)
        limit_data = self.get_limit_list_data(trade_date)
        top_list = self.get_top_list_data(trade_date)
        
        if daily_basic.empty or daily_data.empty:
            print("基础数据获取失败，无法进行筛选")
            return pd.DataFrame()
        
        # 2. 市值筛选
        market_cap_filtered = self.calculate_market_cap_filter(daily_basic)
        
        # 3. 量价信号筛选
        volume_price_filtered = self.analyze_volume_price_signals(daily_data, market_cap_filtered)
        
        # 4. 获取候选股票的资金流向数据
        if not volume_price_filtered.empty:
            candidate_codes = volume_price_filtered['ts_code'].tolist()
            moneyflow_data = self.get_moneyflow_data(trade_date, candidate_codes)
        else:
            moneyflow_data = pd.DataFrame()
        
        # 5. 资金流向信号筛选
        capital_signals = self.analyze_capital_flow_signals(moneyflow_data, top_list)
        
        # 6. 综合筛选结果
        if not volume_price_filtered.empty:
            # 筛选同时满足量价信号和资金流向信号的股票
            final_candidates = volume_price_filtered[
                volume_price_filtered['ts_code'].isin(capital_signals)
            ].copy()
            
            # 添加涨停板信息
            if not limit_data.empty:
                final_candidates = final_candidates.merge(
                    limit_data[['ts_code', 'fd_amount', 'first_time', 'last_time', 'open_times', 'limit_times']],
                    on='ts_code',
                    how='left'
                )
            
            # 按关键指标排序
            if not final_candidates.empty:
                final_candidates = final_candidates.sort_values([
                    'pct_chg',  # 涨幅
                    'turnover_rate',  # 换手率
                    'volume_ratio'  # 量比
                ], ascending=False)
                
                # 选择关键字段
                result_fields = [
                    'ts_code', 'trade_date', 'close', 'pct_chg', 'turnover_rate', 
                    'volume_ratio', 'amount', 'circ_mv', 'fd_amount', 'limit_times'
                ]
                
                available_fields = [field for field in result_fields if field in final_candidates.columns]
                final_result = final_candidates[available_fields]
            else:
                final_result = pd.DataFrame()
        else:
            final_result = pd.DataFrame()
        
        print(f"\n最终筛选结果: {len(final_result)} 只股票")
        print("="*50)
        
        return final_result
    
    def display_results(self, results):
        """
        显示筛选结果
        
        参数:
        results (DataFrame): 筛选结果
        """
        if results.empty:
            print("未找到符合条件的股票")
            return
        
        print("符合连板潜力的候选股票:")
        print("-" * 80)
        
        for idx, row in results.head(10).iterrows():
            print(f"股票代码: {row['ts_code']}")
            print(f"收盘价: {row['close']:.2f}元")
            print(f"涨跌幅: {row['pct_chg']:.2f}%")
            print(f"换手率: {row['turnover_rate']:.2f}%")
            print(f"量比: {row['volume_ratio']:.2f}")
            print(f"成交额: {row['amount']/10000:.2f}亿元")
            print(f"流通市值: {row['circ_mv']/10000:.2f}亿元")
            
            if 'limit_times' in row and pd.notna(row['limit_times']):
                print(f"连板数: {row['limit_times']}")
            if 'fd_amount' in row and pd.notna(row['fd_amount']):
                print(f"封单金额: {row['fd_amount']/10000:.2f}万元")
            
            print("-" * 80)


def main():
    """
    主函数 - 演示策略筛选流程
    """
    # 注意：需要在此处填入您的Tushare Pro Token
    TOKEN = "YOUR_TUSHARE_TOKEN_HERE"
    
    if TOKEN == "YOUR_TUSHARE_TOKEN_HERE":
        print("请先在代码中设置您的Tushare Pro Token")
        print("Token获取方法：")
        print("1. 访问 https://tushare.pro/register")
        print("2. 注册账号并获取Token")
        print("3. 将Token填入上方TOKEN变量")
        return
    
    # 初始化策略
    strategy = TushareStrategyDemo(TOKEN)
    
    # 执行综合筛选
    results = strategy.comprehensive_screening()
    
    # 显示结果
    strategy.display_results(results)
    
    # 保存结果到文件
    if not results.empty:
        output_file = f"data/limit_up_candidates_{datetime.now().strftime('%Y%m%d')}.csv"
        results.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n结果已保存到: {output_file}")


if __name__ == "__main__":
    main()
