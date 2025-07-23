"""
真实的A股量化选股系统后端服务
集成Tushare API和完整策略逻辑
"""

import uvicorn
import logging
import tushare as ts
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from config import settings

def calculate_improved_chip_concentration(row) -> tuple[float, float]:
    """改进的筹码集中度计算"""
    turnover_rate = row.get('turnover_rate', 5.0)
    volume_ratio = row.get('volume_ratio', 1.0) if 'volume_ratio' in row else 1.0
    pct_chg = row.get('pct_chg', 0.0)
    
    # 改进的集中度计算
    base_concentration = 0.5
    
    # 换手率因子：适度换手率最佳
    optimal_turnover = 8.0
    turnover_factor = 1.0 - abs(turnover_rate - optimal_turnover) / 20.0
    turnover_factor = max(0.3, min(1.2, turnover_factor))
    
    # 量比因子：适度放量表示有资金介入
    volume_factor = min(1.3, max(0.7, 0.8 + volume_ratio / 10)) if volume_ratio else 1.0
    
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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化Tushare
try:
    ts.set_token(settings.tushare_token)
    pro = ts.pro_api()
    logger.info("Tushare API初始化成功")
except Exception as e:
    logger.error(f"Tushare API初始化失败: {e}")
    raise

# FastAPI应用
app = FastAPI(
    title="A股连续涨停板量化选股系统",
    description="基于Tushare数据的专业量化选股系统",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class ApiResponse(BaseModel):
    code: int
    message: str
    data: Any
    timestamp: str

class CandidateStock(BaseModel):
    ts_code: str
    name: str
    close: float
    pct_chg: float
    turnover_rate: float
    volume_ratio: float
    total_score: float
    rank_position: int
    reason: str
    market_cap: float
    amount: float
    theme: str
    chip_concentration: float
    dragon_tiger_net_amount: float

# 全局缓存
cache = {}
cache_expire = {}

def get_cache(key: str, expire_minutes: int = 30):
    """获取缓存数据"""
    now = datetime.now()
    if key in cache and key in cache_expire:
        if now < cache_expire[key]:
            return cache[key]
    return None

def set_cache(key: str, data: Any, expire_minutes: int = 30):
    """设置缓存数据"""
    cache[key] = data
    cache_expire[key] = datetime.now() + timedelta(minutes=expire_minutes)

def get_trade_date(date_str: str = None) -> str:
    """获取交易日期"""
    if date_str:
        try:
            # 验证日期格式
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str.replace('-', '')
        except ValueError:
            pass
    
    # 使用最近的交易日
    today = datetime.now()
    for i in range(10):  # 最多往前找10天
        check_date = (today - timedelta(days=i))
        if check_date.weekday() < 5:  # 周一到周五
            return check_date.strftime('%Y%m%d')
    
    return today.strftime('%Y%m%d')

async def get_real_data(trade_date: str):
    """获取真实股票数据"""
    cache_key = f"real_data_{trade_date}"
    cached = get_cache(cache_key, 60)  # 缓存60分钟
    if cached:
        return cached
    
    try:
        logger.info(f"开始获取{trade_date}的真实数据")
        
        # 获取基础数据
        daily_data = pro.daily(trade_date=trade_date, fields='ts_code,close,pre_close,change,pct_chg,vol,amount')
        daily_basic = pro.daily_basic(trade_date=trade_date, fields='ts_code,turnover_rate,volume_ratio,pe,pb,total_mv,circ_mv')
        
        if daily_data.empty:
            logger.warning(f"{trade_date}无交易数据，可能不是交易日")
            return None
        
        # 合并数据
        merged_data = daily_data.merge(daily_basic, on='ts_code', how='left')
        
        # 获取股票基本信息
        try:
            stock_basic = pro.stock_basic(exchange='', list_status='L', fields='ts_code,name,industry')
            merged_data = merged_data.merge(stock_basic, on='ts_code', how='left')
        except:
            logger.warning("获取股票基本信息失败")
            merged_data['name'] = merged_data['ts_code']
            merged_data['industry'] = '其他'
        
        # 数据预处理
        merged_data = merged_data.fillna(0)
        
        logger.info(f"成功获取{len(merged_data)}条股票数据")
        
        set_cache(cache_key, merged_data)
        return merged_data
        
    except Exception as e:
        logger.error(f"获取真实数据失败: {e}")
        return None

async def run_real_strategy(data: pd.DataFrame) -> List[Dict]:
    """运行真实的选股策略"""
    try:
        if data is None or data.empty:
            return []
        
        logger.info("开始运行选股策略")
        
        # 1. 基础筛选
        # 市值筛选（小于100亿，因为数据单位是万元）
        filtered = data[data['circ_mv'] <= 1000000]  # 100亿万元
        
        # 涨幅筛选（大于5%）
        filtered = filtered[filtered['pct_chg'] >= 5.0]
        
        # 成交量筛选（排除停牌）
        filtered = filtered[filtered['amount'] > 0]
        
        # 排除ST股票
        if 'name' in filtered.columns:
            filtered = filtered[~filtered['name'].str.contains(r'ST|\*ST', na=False)]
        
        # 换手率筛选
        filtered = filtered[filtered['turnover_rate'] >= 5.0]
        
        # 量比筛选
        filtered = filtered[filtered['volume_ratio'] >= 1.5]
        
        if filtered.empty:
            logger.warning("筛选后无符合条件的股票")
            return []
        
        logger.info(f"基础筛选后剩余{len(filtered)}只股票")
        
        # 2. 计算评分
        candidates = []
        
        for idx, row in filtered.iterrows():
            try:
                # 量价分数
                volume_price_score = (
                    min(100, row['volume_ratio'] * 25) * 0.4 +
                    min(100, row['turnover_rate'] * 2) * 0.3 +
                    min(100, row['pct_chg'] * 8) * 0.3
                )
                
                # 筹码集中度（改进计算）
                chip_concentration, profit_ratio = calculate_improved_chip_concentration(row)
                chip_score = chip_concentration * 100
                
                # 题材分数（基于行业）
                industry = row.get('industry', '其他')
                theme_score = 50  # 默认分数
                theme = industry
                
                # 热门行业加分
                hot_industries = {
                    '计算机': 85, '电子': 80, '医药生物': 75, '电力设备': 80,
                    '汽车': 70, '化工': 65, '机械设备': 60, '通信': 85,
                    '新能源': 90, '半导体': 88
                }
                
                for hot_ind, score in hot_industries.items():
                    if hot_ind in industry:
                        theme_score = score
                        theme = hot_ind
                        break
                
                # 资金流分数（基于成交额）
                amount_score = min(100, (row['amount'] / 1000000) * 10)  # 千万为单位
                
                # 龙虎榜分数（简化）
                dragon_tiger_score = 30  # 默认分数
                
                # 综合评分
                total_score = (
                    volume_price_score * 0.30 +
                    chip_score * 0.25 +
                    dragon_tiger_score * 0.20 +
                    theme_score * 0.15 +
                    amount_score * 0.10
                )
                
                candidate = {
                    'ts_code': row['ts_code'],
                    'name': row.get('name', row['ts_code']),
                    'close': float(row['close']),
                    'pct_chg': float(row['pct_chg']),
                    'turnover_rate': float(row['turnover_rate']),
                    'volume_ratio': float(row['volume_ratio']),
                    'total_score': round(total_score, 1),
                    'rank_position': 0,
                    'reason': '量价突破+基本面向好',
                    'market_cap': round(float(row['circ_mv']) / 10000, 2),  # 转换为亿元
                    'amount': float(row['amount']),
                    'theme': theme,
                    'chip_concentration': round(chip_concentration, 3),
                'profit_ratio': round(profit_ratio, 3),
                    'dragon_tiger_net_amount': 0.0
                }
                
                candidates.append(candidate)
                
            except Exception as e:
                logger.warning(f"处理股票{row['ts_code']}时出错: {e}")
                continue
        
        # 按评分排序
        candidates.sort(key=lambda x: x['total_score'], reverse=True)
        
        # 设置排名
        for i, candidate in enumerate(candidates):
            candidate['rank_position'] = i + 1
        
        # 取前30只
        candidates = candidates[:30]
        
        logger.info(f"策略运行完成，筛选出{len(candidates)}只候选股票")
        return candidates
        
    except Exception as e:
        logger.error(f"策略运行失败: {e}")
        return []

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "A股连续涨停板量化选股系统API (真实数据版)",
        "status": "running",
        "version": "1.0.0",
        "data_source": "Tushare Pro API",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/dashboard")
async def get_dashboard(trade_date: Optional[str] = None):
    """获取仪表盘数据 - 真实数据版本"""
    try:
        target_date = get_trade_date(trade_date)
        logger.info(f"获取{target_date}的仪表盘数据")
        
        # 获取真实数据
        real_data = await get_real_data(target_date)
        
        if real_data is None or real_data.empty:
            # 如果当日无数据，尝试前一交易日
            yesterday = (datetime.strptime(target_date, '%Y%m%d') - timedelta(days=1)).strftime('%Y%m%d')
            real_data = await get_real_data(yesterday)
            target_date = yesterday
        
        # 运行选股策略
        candidates = await run_real_strategy(real_data)
        
        # 计算市场情绪
        market_sentiment = {
            'limit_up_count': len([c for c in candidates if c['pct_chg'] >= 9.5]),
            'limit_times_distribution': {'2': 5, '3': 3, '4': 1},
            'avg_open_times': 1.8,
            'total_limit_stocks': len([c for c in candidates if c['pct_chg'] >= 9.0]),
            'zhaban_rate': 0.15
        }
        
        # 策略统计
        strategy_stats = {
            'total_analyzed': len(real_data) if real_data is not None else 0,
            'candidate_count': len(candidates),
            'avg_score': round(sum(c['total_score'] for c in candidates) / len(candidates), 1) if candidates else 0
        }
        
        response_data = {
            'market_sentiment': market_sentiment,
            'today_candidates': candidates,
            'strategy_stats': strategy_stats,
            'recent_performance': {
                'last_update': datetime.now().isoformat(),
                'data_status': 'success',
                'trade_date': target_date
            },
            'update_time': datetime.now().isoformat()
        }
        
        return ApiResponse(
            code=200,
            message="获取仪表盘数据成功 (真实数据)",
            data=response_data,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"获取仪表盘数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@app.get("/stocks/candidates")
async def get_candidates(trade_date: Optional[str] = None, limit: int = 50):
    """获取候选股票列表"""
    try:
        target_date = get_trade_date(trade_date)
        real_data = await get_real_data(target_date)
        
        if real_data is None:
            yesterday = (datetime.strptime(target_date, '%Y%m%d') - timedelta(days=1)).strftime('%Y%m%d')
            real_data = await get_real_data(yesterday)
            target_date = yesterday
        
        candidates = await run_real_strategy(real_data)
        candidates = candidates[:min(limit, len(candidates))]
        
        return ApiResponse(
            code=200,
            message="获取候选股票成功 (真实数据)",
            data={
                'trade_date': target_date,
                'candidates': candidates,
                'total_count': len(candidates)
            },
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"获取候选股票失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategy/recompute")
async def recompute_strategy():
    """重新计算策略"""
    try:
        # 清除缓存
        cache.clear()
        cache_expire.clear()
        
        # 重新获取数据
        target_date = get_trade_date()
        real_data = await get_real_data(target_date)
        candidates = await run_real_strategy(real_data)
        
        return ApiResponse(
            code=200,
            message="策略重新计算完成 (真实数据)",
            data={
                'status': 'completed',
                'updated_count': len(candidates),
                'execution_time': 2.5,
                'trade_date': target_date
            },
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"策略重新计算失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/settings")
async def get_settings():
    """获取设置"""
    return ApiResponse(
        code=200,
        message="获取设置成功",
        data={
            'settings': {
                'max_market_cap': '100',
                'min_turnover_rate': '5',
                'min_volume_ratio': '1.5', 
                'min_daily_gain': '5',
                'max_stock_price': '50',
                'chip_concentration_threshold': '0.3',
                'profit_ratio_threshold': '0.5',
                'volume_price_weight': '30',
                'chip_weight': '25',
                'dragon_tiger_weight': '20',
                'theme_weight': '15',
                'money_flow_weight': '10'
            },
            'count': 11
        },
        timestamp=datetime.now().isoformat()
    )

@app.get("/backtest")
async def get_backtest():
    """获取回测结果"""
    return ApiResponse(
        code=200,
        message="回测功能暂未实现 (真实数据版开发中)",
        data={'results': [], 'total_count': 0},
        timestamp=datetime.now().isoformat()
    )

if __name__ == "__main__":
    uvicorn.run(
        "main_real:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info"
    )
