"""
真实的A股量化选股系统后端服务
集成Tushare API和完整策略逻辑
"""

import uvicorn
import logging
import tushare as ts
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from config import settings
from contextlib import asynccontextmanager

# 导入自定义模块
from models.response_models import (
    BaseResponse, CandidateStock, MarketSentiment, 
    BacktestConfig, BacktestResult, AnalysisReport
)
from services.strategy_engine import StrategyEngine
from services.database_operations import DatabaseOperations
from services.tushare_service import TushareService
from services.scheduler import ScheduledRunner

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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 全局变量
db_ops = None
strategy_engine = None
scheduler = None
tushare_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global db_ops, strategy_engine, scheduler, tushare_service
    
    # 启动时初始化
    try:
        logger.info("正在初始化应用...")
        
        # 初始化数据库
        db_ops = DatabaseOperations()
        await db_ops.init_database()
        
        # 初始化策略引擎
        strategy_engine = StrategyEngine(db_ops)
        
        # 初始化调度器
        scheduler = ScheduledRunner()
        
        # 初始化Tushare服务
        tushare_service = TushareService(cache_ttl=1800)  # 30分钟缓存
        
        # 验证Tushare连接
        is_connected = await tushare_service.validate_connection()
        if not is_connected:
            logger.warning("Tushare API连接失败，部分功能可能不可用")
        
        logger.info("应用初始化完成")
        
    except Exception as e:
        logger.error(f"应用初始化失败: {e}")
        raise
    
    yield
    
    # 关闭时清理
    try:
        logger.info("正在关闭应用...")
        if tushare_service:
            tushare_service.clear_cache(older_than_hours=1)  # 清理1小时前的缓存
        logger.info("应用关闭完成")
    except Exception as e:
        logger.error(f"应用关闭时出错: {e}")

# 创建FastAPI应用
app = FastAPI(
    title="A股量化选股系统",
    description="基于Tushare数据的专业量化选股系统",
    version="2.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "A股量化选股系统 API",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "基于Tushare Pro API的真实数据",
            "智能频率控制和缓存机制",
            "换手率递推法筹码分布计算",
            "多维度选股策略",
            "完整回测系统"
        ]
    }

@app.get("/api/stocks", response_model=BaseResponse)
async def get_candidate_stocks(
    date: Optional[str] = Query(None, description="查询日期 (YYYY-MM-DD)"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    min_score: float = Query(70.0, ge=0, le=100, description="最低评分")
):
    """获取候选股票列表"""
    try:
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
            
        logger.info(f"获取候选股票: date={date}, limit={limit}, min_score={min_score}")
        
        # 运行策略
        candidates = await strategy_engine.run_daily_strategy(date)
        
        # 过滤和排序
        filtered_candidates = [
            stock for stock in candidates 
            if stock.total_score >= min_score
        ]
        
        # 按评分排序并限制数量
        filtered_candidates.sort(key=lambda x: x.total_score, reverse=True)
        result_candidates = filtered_candidates[:limit]
        
        # 获取Tushare API统计
        api_stats = tushare_service.get_api_stats() if tushare_service else {}
        
        return BaseResponse(
            success=True,
            data=result_candidates,
            message=f"成功获取{len(result_candidates)}只候选股票",
            metadata={
                "query_date": date,
                "total_found": len(filtered_candidates),
                "returned_count": len(result_candidates),
                "min_score_applied": min_score,
                "data_source": "Tushare Pro API",
                "api_stats": api_stats
            }
        )
        
    except Exception as e:
        logger.error(f"获取候选股票失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取候选股票失败: {str(e)}")

@app.get("/api/market-sentiment", response_model=BaseResponse)
async def get_market_sentiment(
    date: Optional[str] = Query(None, description="查询日期 (YYYY-MM-DD)")
):
    """获取市场情绪指标"""
    try:
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
            
        logger.info(f"获取市场情绪: date={date}")
        
        sentiment = await strategy_engine.analyze_market_sentiment(date)
        
        return BaseResponse(
            success=True,
            data=sentiment,
            message="成功获取市场情绪指标",
            metadata={
                "query_date": date,
                "data_source": "Tushare Pro API"
            }
        )
        
    except Exception as e:
        logger.error(f"获取市场情绪失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取市场情绪失败: {str(e)}")

@app.post("/api/backtest", response_model=BaseResponse)
async def run_backtest(config: BacktestConfig):
    """运行回测"""
    try:
        logger.info(f"开始回测: {config.start_date} 到 {config.end_date}")
        
        result = await strategy_engine.run_backtest(config)
        
        return BaseResponse(
            success=True,
            data=result,
            message="回测完成",
            metadata={
                "backtest_period": f"{config.start_date} 到 {config.end_date}",
                "strategy_params": config.strategy_params
            }
        )
        
    except Exception as e:
        logger.error(f"回测失败: {e}")
        raise HTTPException(status_code=500, detail=f"回测失败: {str(e)}")

@app.get("/api/analysis/{ts_code}", response_model=BaseResponse)
async def get_stock_analysis(
    ts_code: str,
    days: int = Query(30, ge=1, le=365, description="分析天数")
):
    """获取个股详细分析"""
    try:
        logger.info(f"分析个股: {ts_code}, 天数: {days}")
        
        analysis = await strategy_engine.analyze_single_stock(ts_code, days)
        
        return BaseResponse(
            success=True,
            data=analysis,
            message=f"成功分析股票 {ts_code}",
            metadata={
                "ts_code": ts_code,
                "analysis_days": days,
                "data_source": "Tushare Pro API"
            }
        )
        
    except Exception as e:
        logger.error(f"个股分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"个股分析失败: {str(e)}")

# 新增：Tushare API 监控端点
@app.get("/api/tushare/status", response_model=BaseResponse)
async def get_tushare_status():
    """获取Tushare API状态和统计信息"""
    try:
        if not tushare_service:
            raise HTTPException(status_code=503, detail="Tushare服务未初始化")
        
        # 健康检查
        is_healthy = await tushare_service.health_check()
        
        # 获取统计信息
        stats = tushare_service.get_api_stats()
        
        return BaseResponse(
            success=True,
            data={
                "is_healthy": is_healthy,
                "api_stats": stats,
                "service_status": "active" if is_healthy else "degraded"
            },
            message="Tushare API状态获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取Tushare状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取Tushare状态失败: {str(e)}")

@app.post("/api/tushare/clear-cache", response_model=BaseResponse)
async def clear_tushare_cache(
    older_than_hours: int = Query(24, ge=1, le=168, description="清理多少小时前的缓存")
):
    """清理Tushare API缓存"""
    try:
        if not tushare_service:
            raise HTTPException(status_code=503, detail="Tushare服务未初始化")
        
        tushare_service.clear_cache(older_than_hours)
        
        return BaseResponse(
            success=True,
            data={"cleared_hours": older_than_hours},
            message=f"成功清理{older_than_hours}小时前的缓存"
        )
        
    except Exception as e:
        logger.error(f"清理缓存失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理缓存失败: {str(e)}")

@app.post("/api/data/refresh", response_model=BaseResponse)
async def refresh_data(background_tasks: BackgroundTasks):
    """刷新数据（后台任务）"""
    try:
        def refresh_task():
            """后台刷新任务"""
            try:
                if tushare_service:
                    tushare_service.clear_cache(older_than_hours=1)
                logger.info("数据刷新任务完成")
            except Exception as e:
                logger.error(f"后台数据刷新失败: {e}")
        
        background_tasks.add_task(refresh_task)
        
        return BaseResponse(
            success=True,
            data={"task": "started"},
            message="数据刷新任务已启动"
        )
        
    except Exception as e:
        logger.error(f"启动刷新任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动刷新任务失败: {str(e)}")

@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    try:
        checks = {
            "database": True,  # 可以添加数据库连接检查
            "tushare_api": False,
            "strategy_engine": strategy_engine is not None,
            "scheduler": scheduler is not None
        }
        
        if tushare_service:
            checks["tushare_api"] = await tushare_service.health_check()
        
        all_healthy = all(checks.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.now().isoformat(),
            "checks": checks
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_real:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
