"""
仪表盘API路由
提供仪表盘数据接口
"""

from fastapi import APIRouter, HTTPException, Depends
import logging
from datetime import datetime, date
from typing import Optional

from database.operations import DatabaseOperations
from database.models import DashboardData, ApiResponse
from services.strategy_engine import StrategyEngine
from config import ResponseCode

logger = logging.getLogger(__name__)
router = APIRouter()

# 依赖注入
async def get_db():
    return DatabaseOperations()

async def get_strategy_engine():
    return StrategyEngine()

@router.get("/dashboard", 
           response_model=ApiResponse,
           summary="获取仪表盘数据",
           description="获取市场情绪、今日选股结果、策略统计等仪表盘数据")
async def get_dashboard(
    trade_date: Optional[str] = None,
    db: DatabaseOperations = Depends(get_db),
    strategy_engine: StrategyEngine = Depends(get_strategy_engine)
):
    """获取仪表盘数据"""
    try:
        # 解析日期参数
        if trade_date:
            try:
                target_date = datetime.strptime(trade_date, '%Y-%m-%d').date()
            except ValueError:
                raise HTTPException(
                    status_code=ResponseCode.BAD_REQUEST,
                    detail="日期格式错误，请使用YYYY-MM-DD格式"
                )
        else:
            # 使用最新交易日
            target_date = await db.get_latest_trade_date()
            if not target_date:
                target_date = datetime.now().date()
        
        logger.info(f"获取仪表盘数据，日期: {target_date}")
        
        # 获取市场情绪数据
        market_sentiment = await strategy_engine.get_market_sentiment(target_date)
        
        # 获取今日候选股
        today_candidates = await db.get_candidate_stocks(target_date, limit=20)
        
        # 获取策略统计
        strategy_results = await db.get_strategy_results(target_date, limit=1000)
        strategy_stats = {
            'total_analyzed': len(strategy_results),
            'candidate_count': len([r for r in strategy_results if r.is_candidate]),
            'avg_score': float(sum(r.total_score for r in strategy_results) / max(len(strategy_results), 1))
        }
        
        # 获取近期表现数据(简化版)
        recent_performance = {
            'last_update': target_date.strftime('%Y-%m-%d'),
            'data_status': 'completed' if strategy_results else 'pending'
        }
        
        # 构建仪表盘数据
        dashboard_data = {
            'market_sentiment': market_sentiment,
            'today_candidates': [candidate.__dict__ for candidate in today_candidates],
            'strategy_stats': strategy_stats,
            'recent_performance': recent_performance,
            'update_time': datetime.now()
        }
        
        return ApiResponse(
            code=ResponseCode.SUCCESS,
            message="仪表盘数据获取成功",
            data=dashboard_data,
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取仪表盘数据失败: {e}")
        raise HTTPException(
            status_code=ResponseCode.INTERNAL_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )
