"""
演示版主应用入口
简化的FastAPI应用，提供基础API演示
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime, date
import random
from typing import Dict, List, Any

# 设置基础日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="A股连续涨停板量化选股系统（演示版）",
    description="基于技术分析和资金流向的专业量化选股平台 - 演示版",
    version="1.0.0-demo",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模拟数据生成器
def generate_mock_stocks(count: int = 20) -> List[Dict[str, Any]]:
    """生成模拟股票数据"""
    stock_names = [
        "东方通信", "领益智造", "中科创达", "卓胜微", "沪硅产业",
        "金龙鱼", "宁德时代", "比亚迪", "隆基绿能", "通威股份",
        "药明康德", "迈瑞医疗", "恒瑞医药", "片仔癀", "云南白药",
        "贵州茅台", "五粮液", "泸州老窖", "山西汾酒", "今世缘"
    ]
    
    themes = ["5G通信", "新能源", "半导体", "医药生物", "白酒", "光伏", "汽车", "AI概念"]
    
    stocks = []
    for i in range(count):
        ts_code = f"0{str(i+1).zfill(5)}.SZ" if i % 2 == 0 else f"6{str(i+1).zfill(5)}.SH"
        stocks.append({
            "ts_code": ts_code,
            "name": stock_names[i % len(stock_names)],
            "close": round(random.uniform(10, 100), 2),
            "pct_chg": round(random.uniform(5, 10.01), 2),
            "turnover_rate": round(random.uniform(10, 35), 2),
            "volume_ratio": round(random.uniform(2, 8), 2),
            "total_score": round(random.uniform(60, 95), 1),
            "rank_position": i + 1,
            "reason": "技术突破+量价齐升+题材热度",
            "market_cap": round(random.uniform(20, 100), 2),
            "amount": random.randint(50000, 500000),
            "theme": themes[i % len(themes)],
            "chip_concentration": round(random.uniform(0.6, 0.9), 3),
            "dragon_tiger_net_amount": random.randint(-50000000, 100000000)
        })
    return stocks

def generate_market_sentiment() -> Dict[str, Any]:
    """生成市场情绪数据"""
    return {
        "limit_up_count": random.randint(20, 80),
        "limit_times_distribution": {
            "2": random.randint(5, 15),
            "3": random.randint(3, 10),
            "4": random.randint(1, 5),
            "5": random.randint(0, 3)
        },
        "avg_open_times": round(random.uniform(1.2, 3.5), 2),
        "total_limit_stocks": random.randint(10, 30),
        "zhaban_rate": round(random.uniform(0.2, 0.7), 3)
    }

# API路由
@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "message": "A股连续涨停板量化选股系统（演示版）",
        "status": "running",
        "version": "1.0.0-demo",
        "docs": "/docs",
        "note": "这是演示版本，使用模拟数据"
    }

@app.get("/api/dashboard")
async def get_dashboard():
    """获取仪表盘数据"""
    candidates = generate_mock_stocks(20)
    
    return {
        "code": 200,
        "message": "获取仪表盘数据成功",
        "data": {
            "market_sentiment": generate_market_sentiment(),
            "today_candidates": candidates,
            "strategy_stats": {
                "total_analyzed": random.randint(3000, 5000),
                "candidate_count": len(candidates),
                "avg_score": round(random.uniform(70, 85), 1)
            },
            "recent_performance": {
                "last_update": datetime.now().isoformat(),
                "data_status": "success"
            },
            "update_time": datetime.now().isoformat()
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/stocks/candidates")
async def get_candidate_stocks(limit: int = 50):
    """获取候选股票列表"""
    candidates = generate_mock_stocks(min(limit, 50))
    
    return {
        "code": 200,
        "message": "获取候选股票成功",
        "data": {
            "trade_date": date.today().isoformat(),
            "candidates": candidates,
            "total_count": len(candidates)
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/strategy/recompute")
async def recompute_strategy():
    """重新计算策略"""
    return {
        "code": 200,
        "message": "策略重新计算完成",
        "data": {
            "status": "completed",
            "updated_count": random.randint(15, 25),
            "execution_time": round(random.uniform(2, 8), 2)
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/settings")
async def get_settings():
    """获取设置"""
    return {
        "code": 200,
        "message": "获取设置成功",
        "data": {
            "settings": {
                "max_market_cap": "50",
                "min_turnover_rate": "10",
                "min_volume_ratio": "2",
                "min_daily_gain": "9",
                "max_stock_price": "30",
                "chip_concentration_threshold": "0.65",
                "profit_ratio_threshold": "0.5",
                "volume_price_weight": "30",
                "chip_weight": "25",
                "dragon_tiger_weight": "20",
                "theme_weight": "15",
                "money_flow_weight": "10"
            },
            "count": 12
        },
        "timestamp": datetime.now().isoformat()
    }

@app.put("/api/settings")
async def update_setting(setting_key: str, setting_value: str):
    """更新设置"""
    return {
        "code": 200,
        "message": "设置更新成功",
        "data": {
            "setting_key": setting_key,
            "setting_value": setting_value,
            "updated_at": datetime.now().isoformat()
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/backtest")
async def get_backtest_results():
    """获取回测结果"""
    results = []
    for i in range(5):
        results.append({
            "backtest_id": f"bt_{str(random.randint(100000, 999999))}",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "status": "completed",
            "total_return": round(random.uniform(0.1, 0.8), 4),
            "annual_return": round(random.uniform(0.15, 0.9), 4),
            "max_drawdown": round(random.uniform(0.05, 0.25), 4),
            "sharpe_ratio": round(random.uniform(0.8, 2.5), 2),
            "win_rate": round(random.uniform(0.4, 0.7), 3),
            "total_trades": random.randint(50, 200),
            "created_at": datetime.now().isoformat()
        })
    
    return {
        "code": 200,
        "message": "获取回测结果成功",
        "data": {
            "results": results,
            "total_count": len(results)
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/backtest/run")
async def run_backtest(start_date: str, end_date: str):
    """运行回测"""
    result = {
        "backtest_id": f"bt_{str(random.randint(100000, 999999))}",
        "start_date": start_date,
        "end_date": end_date,
        "status": "completed",
        "total_return": round(random.uniform(0.2, 0.6), 4),
        "annual_return": round(random.uniform(0.25, 0.7), 4),
        "max_drawdown": round(random.uniform(0.08, 0.2), 4),
        "sharpe_ratio": round(random.uniform(1.2, 2.8), 2),
        "win_rate": round(random.uniform(0.45, 0.65), 3),
        "total_trades": random.randint(80, 150),
        "created_at": datetime.now().isoformat()
    }
    
    return {
        "code": 200,
        "message": "回测运行成功",
        "data": result,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/export")
async def export_data():
    """导出数据"""
    return {
        "code": 200,
        "message": "数据导出功能暂未实现（演示版）",
        "data": {
            "export_url": "#",
            "note": "演示版本不支持真实数据导出"
        },
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "demo_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
