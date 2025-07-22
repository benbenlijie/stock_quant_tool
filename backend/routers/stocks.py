"""
股票数据API路由
提供股票基础信息和候选股查询接口
"""

from fastapi import APIRouter, HTTPException, Depends, Query
import logging
from datetime import datetime, date
from typing import Optional, List

from database.operations import DatabaseOperations
from database.models import ApiResponse, CandidateStock
from config import ResponseCode

logger = logging.getLogger(__name__)
router = APIRouter()

# 依赖注入
async def get_db():
    return DatabaseOperations()

@router.get("/stocks/candidates",
           response_model=ApiResponse,
           summary="获取候选股票列表",
           description="获取指定日期的候选股票列表，按综合评分排序")
async def get_candidate_stocks(
    trade_date: Optional[str] = Query(None, description="交易日期，格式为YYYY-MM-DD"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    db: DatabaseOperations = Depends(get_db)
):
    """获取候选股票列表"""
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
            raise HTTPException(
                status_code=ResponseCode.NOT_FOUND,
                detail="未找到有效的交易日期数据"
            )
        
        logger.info(f"获取候选股票列表，日期: {target_date}, 限制: {limit}")
        
        # 获取候选股票
        candidates = await db.get_candidate_stocks(target_date, limit)
        
        # 转换为字典格式
        candidates_data = []
        for candidate in candidates:
            candidate_dict = {
                'ts_code': candidate.ts_code,
                'name': candidate.name,
                'close': float(candidate.close),
                'pct_chg': float(candidate.pct_chg),
                'turnover_rate': float(candidate.turnover_rate),
                'volume_ratio': float(candidate.volume_ratio),
                'total_score': float(candidate.total_score),
                'rank_position': candidate.rank_position,
                'reason': candidate.reason,
                'market_cap': float(candidate.market_cap) if candidate.market_cap else None,
                'amount': float(candidate.amount) if candidate.amount else None
            }
            candidates_data.append(candidate_dict)
        
        return ApiResponse(
            code=ResponseCode.SUCCESS,
            message=f"获取到 {len(candidates)} 只候选股票",
            data={
                'trade_date': target_date.strftime('%Y-%m-%d'),
                'candidates': candidates_data,
                'total_count': len(candidates)
            },
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取候选股票列表失败: {e}")
        raise HTTPException(
            status_code=ResponseCode.INTERNAL_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )
