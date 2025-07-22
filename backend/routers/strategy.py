"""
策略计算API路由
提供策略重新计算和参数调整接口
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
from datetime import datetime, date
from typing import Optional, Dict, Any

from database.operations import DatabaseOperations
from database.models import ApiResponse
from services.strategy_engine import StrategyEngine
from services.scheduler import StrategyScheduler
from config import ResponseCode

logger = logging.getLogger(__name__)
router = APIRouter()

# 请求模型
class StrategyRecomputeRequest(BaseModel):
    trade_date: Optional[str] = None
    force_update: bool = False

class StrategyConfigUpdateRequest(BaseModel):
    config_updates: Dict[str, Any]

# 依赖注入
async def get_db():
    return DatabaseOperations()

async def get_strategy_engine():
    return StrategyEngine()

async def get_scheduler():
    return StrategyScheduler()

@router.post("/strategy/recompute",
            response_model=ApiResponse,
            summary="重新计算策略",
            description="手动触发策略重新计算，支持指定日期")
async def recompute_strategy(
    request: StrategyRecomputeRequest,
    scheduler: StrategyScheduler = Depends(get_scheduler)
):
    """重新计算策略"""
    try:
        # 解析日期参数
        target_date = None
        if request.trade_date:
            try:
                target_date = datetime.strptime(request.trade_date, '%Y-%m-%d').date()
            except ValueError:
                raise HTTPException(
                    status_code=ResponseCode.BAD_REQUEST,
                    detail="日期格式错误，请使用YYYY-MM-DD格式"
                )
        
        logger.info(f"手动触发策略重新计算，日期: {target_date}, 强制更新: {request.force_update}")
        
        # 执行策略计算
        success = await scheduler.manual_trigger(target_date)
        
        if success:
            return ApiResponse(
                code=ResponseCode.SUCCESS,
                message="策略重新计算完成",
                data={
                    'trade_date': target_date.strftime('%Y-%m-%d') if target_date else datetime.now().strftime('%Y-%m-%d'),
                    'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                timestamp=datetime.now()
            )
        else:
            raise HTTPException(
                status_code=ResponseCode.INTERNAL_ERROR,
                detail="策略重新计算失败"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"策略重新计算失败: {e}")
        raise HTTPException(
            status_code=ResponseCode.INTERNAL_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )

@router.put("/strategy/config",
           response_model=ApiResponse,
           summary="更新策略配置",
           description="更新策略参数配置")
async def update_strategy_config(
    request: StrategyConfigUpdateRequest,
    strategy_engine: StrategyEngine = Depends(get_strategy_engine)
):
    """更新策略配置"""
    try:
        logger.info(f"更新策略配置: {request.config_updates}")
        
        # 更新配置
        success = await strategy_engine.update_strategy_config(request.config_updates)
        
        if success:
            return ApiResponse(
                code=ResponseCode.SUCCESS,
                message="策略配置更新成功",
                data={
                    'updated_config': request.config_updates,
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                timestamp=datetime.now()
            )
        else:
            raise HTTPException(
                status_code=ResponseCode.INTERNAL_ERROR,
                detail="策略配置更新失败"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新策略配置失败: {e}")
        raise HTTPException(
            status_code=ResponseCode.INTERNAL_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )

@router.get("/strategy/status",
           response_model=ApiResponse,
           summary="获取策略状态",
           description="获取策略计算状态和进度")
async def get_strategy_status(
    scheduler: StrategyScheduler = Depends(get_scheduler)
):
    """获取策略状态"""
    try:
        status = scheduler.get_task_status()
        
        return ApiResponse(
            code=ResponseCode.SUCCESS,
            message="策略状态获取成功",
            data=status,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"获取策略状态失败: {e}")
        raise HTTPException(
            status_code=ResponseCode.INTERNAL_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )
