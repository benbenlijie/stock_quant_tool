"""
系统设置API路由
提供策略参数配置和系统设置管理接口
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
from datetime import datetime
from typing import Dict, Any

from database.operations import DatabaseOperations
from database.models import ApiResponse
from config import ResponseCode

logger = logging.getLogger(__name__)
router = APIRouter()

# 请求模型
class SettingUpdateRequest(BaseModel):
    setting_key: str
    setting_value: str

# 依赖注入
async def get_db():
    return DatabaseOperations()

@router.get("/settings",
           response_model=ApiResponse,
           summary="获取系统设置",
           description="获取所有系统设置和策略参数")
async def get_settings(
    db: DatabaseOperations = Depends(get_db)
):
    """获取系统设置"""
    try:
        logger.info("获取系统设置")
        
        # 获取所有设置
        settings = await db.get_user_settings()
        
        return ApiResponse(
            code=ResponseCode.SUCCESS,
            message="系统设置获取成功",
            data={
                'settings': settings,
                'count': len(settings)
            },
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"获取系统设置失败: {e}")
        raise HTTPException(
            status_code=ResponseCode.INTERNAL_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )

@router.put("/settings",
           response_model=ApiResponse,
           summary="更新系统设置",
           description="更新单个系统设置项")
async def update_setting(
    request: SettingUpdateRequest,
    db: DatabaseOperations = Depends(get_db)
):
    """更新系统设置"""
    try:
        logger.info(f"更新系统设置: {request.setting_key} = {request.setting_value}")
        
        # 更新设置
        success = await db.update_user_setting(request.setting_key, request.setting_value)
        
        if success:
            return ApiResponse(
                code=ResponseCode.SUCCESS,
                message="系统设置更新成功",
                data={
                    'setting_key': request.setting_key,
                    'setting_value': request.setting_value,
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                timestamp=datetime.now()
            )
        else:
            raise HTTPException(
                status_code=ResponseCode.NOT_FOUND,
                detail=f"设置项 {request.setting_key} 不存在"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新系统设置失败: {e}")
        raise HTTPException(
            status_code=ResponseCode.INTERNAL_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )
