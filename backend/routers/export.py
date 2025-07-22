"""
数据导出API路由
提供数据导出功能接口
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging
import io
import csv
import json
from datetime import datetime, date
from typing import Optional, List

from database.operations import DatabaseOperations
from database.models import ApiResponse
from config import ResponseCode

logger = logging.getLogger(__name__)
router = APIRouter()

# 请求模型
class ExportRequest(BaseModel):
    export_type: str  # candidates, strategy_results, market_data
    trade_date: Optional[str] = None
    format: str = "csv"  # csv, json, excel
    filters: Optional[dict] = None

# 依赖注入
async def get_db():
    return DatabaseOperations()

@router.post("/export",
            summary="导出数据",
            description="导出候选股票、策略结果或市场数据")
async def export_data(
    request: ExportRequest,
    db: DatabaseOperations = Depends(get_db)
):
    """导出数据"""
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
        else:
            target_date = await db.get_latest_trade_date()
        
        logger.info(f"导出数据: {request.export_type}, 日期: {target_date}, 格式: {request.format}")
        
        # 根据导出类型获取数据
        if request.export_type == "candidates":
            data = await db.get_candidate_stocks(target_date, limit=1000)
            data_list = [{
                'ts_code': item.ts_code,
                'name': item.name,
                'close': float(item.close),
                'pct_chg': float(item.pct_chg),
                'turnover_rate': float(item.turnover_rate),
                'volume_ratio': float(item.volume_ratio),
                'total_score': float(item.total_score),
                'rank_position': item.rank_position,
                'reason': item.reason
            } for item in data]
            filename = f"candidates_{target_date.strftime('%Y%m%d')}"
            
        elif request.export_type == "strategy_results":
            data = await db.get_strategy_results(target_date, limit=1000)
            data_list = [{
                'ts_code': item.ts_code,
                'trade_date': item.trade_date.strftime('%Y-%m-%d'),
                'total_score': float(item.total_score),
                'volume_price_score': float(item.volume_price_score),
                'chip_score': float(item.chip_score),
                'dragon_tiger_score': float(item.dragon_tiger_score),
                'theme_score': float(item.theme_score),
                'money_flow_score': float(item.money_flow_score),
                'rank_position': item.rank_position,
                'is_candidate': item.is_candidate,
                'reason': item.reason
            } for item in data]
            filename = f"strategy_results_{target_date.strftime('%Y%m%d')}"
            
        else:
            raise HTTPException(
                status_code=ResponseCode.BAD_REQUEST,
                detail=f"不支持的导出类型: {request.export_type}"
            )
        
        # 根据格式导出数据
        if request.format == "csv":
            return _export_csv(data_list, filename)
        elif request.format == "json":
            return _export_json(data_list, filename)
        else:
            raise HTTPException(
                status_code=ResponseCode.BAD_REQUEST,
                detail=f"不支持的导出格式: {request.format}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出数据失败: {e}")
        raise HTTPException(
            status_code=ResponseCode.INTERNAL_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )

def _export_csv(data_list: List[dict], filename: str) -> StreamingResponse:
    """导出CSV格式"""
    output = io.StringIO()
    
    if data_list:
        writer = csv.DictWriter(output, fieldnames=data_list[0].keys())
        writer.writeheader()
        writer.writerows(data_list)
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
    )

def _export_json(data_list: List[dict], filename: str) -> StreamingResponse:
    """导出JSON格式"""
    json_data = json.dumps({
        'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_count': len(data_list),
        'data': data_list
    }, ensure_ascii=False, indent=2)
    
    return StreamingResponse(
        io.BytesIO(json_data.encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}.json"}
    )
