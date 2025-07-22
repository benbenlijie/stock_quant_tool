"""
主应用入口
FastAPI应用的启动和配置
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import settings
from database import init_db
from routers import (
    dashboard, 
    stocks, 
    strategy, 
    backtest, 
    export, 
    settings as settings_router
)
from services.scheduler import StrategyScheduler
from utils.logger import setup_logger

# 设置日志
setup_logger()
logger = logging.getLogger(__name__)

# 调度器实例
scheduler = AsyncIOScheduler()
strategy_scheduler = StrategyScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("正在启动量化选股系统...")
    
    # 初始化数据库
    await init_db()
    logger.info("数据库初始化完成")
    
    # 启动定时任务调度器
    scheduler.start()
    
    # 添加每日17:00的数据更新任务
    scheduler.add_job(
        func=strategy_scheduler.daily_data_update,
        trigger=CronTrigger(hour=17, minute=0),
        id='daily_data_update',
        name='每日数据更新和策略计算',
        replace_existing=True
    )
    
    logger.info("定时任务调度器启动完成")
    logger.info(f"系统启动完成，监听地址: {settings.api_host}:{settings.api_port}")
    
    yield
    
    # 关闭时执行
    logger.info("正在关闭量化选股系统...")
    scheduler.shutdown()
    logger.info("系统关闭完成")

# 创建FastAPI应用
app = FastAPI(
    title="A股连续涨停板量化选股系统",
    description="基于技术分析和资金流向的专业量化选股平台",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(dashboard.router, prefix="/api", tags=["仪表盘"])
app.include_router(stocks.router, prefix="/api", tags=["股票数据"])
app.include_router(strategy.router, prefix="/api", tags=["策略计算"])
app.include_router(backtest.router, prefix="/api", tags=["历史回测"])
app.include_router(export.router, prefix="/api", tags=["数据导出"])
app.include_router(settings_router.router, prefix="/api", tags=["系统设置"])

@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "message": "A股连续涨停板量化选股系统",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": strategy_scheduler.get_current_timestamp()
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info"
    )
