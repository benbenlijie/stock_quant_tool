"""
频率限制的 Tushare API 客户端
实现API调用频率控制、缓存机制和错误重试
"""

import asyncio
import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
import pandas as pd
import tushare as ts
import logging
from functools import wraps

from config import settings

logger = logging.getLogger(__name__)

class RateLimitedTushareClient:
    """
    带频率限制和缓存的 Tushare API 客户端
    
    特性：
    - API调用频率控制（每分钟最多1000次）
    - 智能缓存机制（减少重复调用）
    - 自动重试和错误恢复
    - 调用统计和监控
    """
    
    def __init__(self, cache_dir: str = "cache", cache_ttl: int = 3600):
        """
        初始化客户端
        
        Args:
            cache_dir: 缓存目录
            cache_ttl: 缓存过期时间（秒），默认1小时
        """
        self.token = settings.tushare_token
        self.pro = None
        self.cache_dir = Path(cache_dir)
        self.cache_ttl = cache_ttl
        
        # 频率控制
        self.call_history = []  # 调用历史记录
        self.max_calls_per_minute = 900  # 留一些余量，不要用满1000
        self.min_interval = 0.1  # 最小调用间隔（秒）
        
        # 统计信息
        self.stats = {
            'total_calls': 0,
            'cache_hits': 0,
            'api_errors': 0,
            'rate_limit_hits': 0
        }
        
        self._init_client()
        self._ensure_cache_dir()
    
    def _init_client(self):
        """初始化 Tushare Pro 客户端"""
        try:
            ts.set_token(self.token)
            self.pro = ts.pro_api()
            logger.info("Tushare Pro API 初始化成功")
        except Exception as e:
            logger.error(f"Tushare Pro API 初始化失败: {e}")
            raise
    
    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_cache_key(self, method: str, **kwargs) -> str:
        """生成缓存键"""
        # 创建一个包含方法名和参数的字符串
        key_data = f"{method}_{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{cache_key}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """检查缓存是否有效"""
        if not cache_path.exists():
            return False
        
        # 检查文件修改时间
        file_time = cache_path.stat().st_mtime
        current_time = time.time()
        return (current_time - file_time) < self.cache_ttl
    
    def _save_to_cache(self, cache_key: str, data: Any):
        """保存数据到缓存"""
        try:
            cache_path = self._get_cache_path(cache_key)
            
            # 将 DataFrame 转换为可序列化的格式
            if isinstance(data, pd.DataFrame):
                cache_data = {
                    'type': 'dataframe',
                    'data': data.to_json(orient='records', date_format='iso'),
                    'columns': data.columns.tolist(),
                    'timestamp': time.time()
                }
            else:
                cache_data = {
                    'type': 'other',
                    'data': data,
                    'timestamp': time.time()
                }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")
    
    def _load_from_cache(self, cache_key: str) -> Optional[Any]:
        """从缓存加载数据"""
        try:
            cache_path = self._get_cache_path(cache_key)
            
            if not self._is_cache_valid(cache_path):
                return None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            if cache_data['type'] == 'dataframe':
                # 重构 DataFrame
                df_data = json.loads(cache_data['data'])
                df = pd.DataFrame(df_data)
                if cache_data['columns']:
                    df = df.reindex(columns=cache_data['columns'])
                return df
            else:
                return cache_data['data']
                
        except Exception as e:
            logger.warning(f"加载缓存失败: {e}")
            return None
    
    async def _wait_for_rate_limit(self):
        """智能频率控制"""
        current_time = time.time()
        
        # 清理1分钟前的调用记录
        self.call_history = [t for t in self.call_history if current_time - t < 60]
        
        # 检查是否超过每分钟限制
        if len(self.call_history) >= self.max_calls_per_minute:
            # 计算需要等待的时间
            oldest_call = min(self.call_history)
            wait_time = 60 - (current_time - oldest_call) + 1
            
            logger.warning(f"达到频率限制，等待 {wait_time:.2f} 秒")
            self.stats['rate_limit_hits'] += 1
            await asyncio.sleep(wait_time)
        
        # 确保最小调用间隔
        if self.call_history:
            last_call = max(self.call_history)
            elapsed = current_time - last_call
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
        
        # 记录此次调用时间
        self.call_history.append(time.time())
    
    def _api_call_wrapper(self, method_name: str):
        """API调用装饰器"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = self._generate_cache_key(method_name, **kwargs)
                
                # 尝试从缓存获取
                cached_data = self._load_from_cache(cache_key)
                if cached_data is not None:
                    self.stats['cache_hits'] += 1
                    logger.debug(f"缓存命中: {method_name}")
                    return cached_data
                
                # 频率控制
                await self._wait_for_rate_limit()
                
                # 调用API
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        self.stats['total_calls'] += 1
                        
                        # 在线程池中执行同步API调用
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(None, func, *args, **kwargs)
                        
                        # 保存到缓存
                        self._save_to_cache(cache_key, result)
                        
                        logger.debug(f"API调用成功: {method_name}")
                        return result
                        
                    except Exception as e:
                        self.stats['api_errors'] += 1
                        error_msg = str(e)
                        
                        # 检查是否是频率限制错误
                        if "每分钟最多访问" in error_msg or "访问过于频繁" in error_msg:
                            logger.warning(f"触发频率限制: {error_msg}")
                            # 等待更长时间
                            wait_time = 60 + attempt * 30
                            logger.info(f"等待 {wait_time} 秒后重试...")
                            await asyncio.sleep(wait_time)
                            continue
                        
                        # 其他错误
                        if attempt == max_retries - 1:
                            logger.error(f"API调用失败 {method_name}: {e}")
                            raise
                        else:
                            logger.warning(f"API调用失败，重试中 ({attempt + 1}/{max_retries}): {e}")
                            await asyncio.sleep(2 ** attempt)  # 指数退避
                            continue
                
            return wrapper
        return decorator
    
    @_api_call_wrapper("daily")
    def _get_daily_data(self, trade_date: str = None, ts_code: str = None):
        """获取日线数据"""
        return self.pro.daily(
            trade_date=trade_date,
            ts_code=ts_code,
            fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount'
        )
    
    @_api_call_wrapper("daily_basic")
    def _get_daily_basic(self, trade_date: str = None, ts_code: str = None):
        """获取每日基本面数据"""
        return self.pro.daily_basic(
            trade_date=trade_date,
            ts_code=ts_code,
            fields='ts_code,trade_date,turnover_rate,turnover_rate_f,volume_ratio,pe,pb,ps,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv'
        )
    
    @_api_call_wrapper("limit_list")
    def _get_limit_list(self, trade_date: str):
        """获取涨跌停股票列表"""
        return self.pro.limit_list(trade_date=trade_date)
    
    @_api_call_wrapper("moneyflow")
    def _get_money_flow(self, trade_date: str = None, ts_code: str = None):
        """获取资金流向数据"""
        return self.pro.moneyflow(
            trade_date=trade_date,
            ts_code=ts_code,
            fields='ts_code,trade_date,buy_sm_amount,buy_md_amount,buy_lg_amount,buy_elg_amount,sell_sm_amount,sell_md_amount,sell_lg_amount,sell_elg_amount,net_mf_amount'
        )
    
    @_api_call_wrapper("top_list")
    def _get_top_list(self, trade_date: str):
        """获取龙虎榜数据"""
        return self.pro.top_list(trade_date=trade_date)
    
    @_api_call_wrapper("stock_basic")
    def _get_stock_basic(self):
        """获取股票基本信息"""
        return self.pro.stock_basic(
            exchange='',
            list_status='L',
            fields='ts_code,symbol,name,area,industry,market,list_date,is_hs'
        )
    
    # 公共接口方法
    async def get_daily_data(self, trade_date: str = None, ts_code: str = None) -> pd.DataFrame:
        """获取日线数据"""
        return await self._get_daily_data(trade_date=trade_date, ts_code=ts_code)
    
    async def get_daily_basic(self, trade_date: str = None, ts_code: str = None) -> pd.DataFrame:
        """获取每日基本面数据"""
        return await self._get_daily_basic(trade_date=trade_date, ts_code=ts_code)
    
    async def get_limit_list(self, trade_date: str) -> pd.DataFrame:
        """获取涨跌停股票列表"""
        return await self._get_limit_list(trade_date=trade_date)
    
    async def get_money_flow(self, trade_date: str = None, ts_code: str = None) -> pd.DataFrame:
        """获取资金流向数据"""
        return await self._get_money_flow(trade_date=trade_date, ts_code=ts_code)
    
    async def get_top_list(self, trade_date: str) -> pd.DataFrame:
        """获取龙虎榜数据"""
        return await self._get_top_list(trade_date=trade_date)
    
    async def get_stock_basic(self) -> pd.DataFrame:
        """获取股票基本信息"""
        return await self._get_stock_basic()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取调用统计信息"""
        cache_hit_rate = 0
        if self.stats['total_calls'] + self.stats['cache_hits'] > 0:
            cache_hit_rate = self.stats['cache_hits'] / (self.stats['total_calls'] + self.stats['cache_hits'])
        
        return {
            **self.stats,
            'cache_hit_rate': f"{cache_hit_rate:.2%}",
            'calls_last_minute': len(self.call_history),
            'max_calls_per_minute': self.max_calls_per_minute
        }
    
    def clear_cache(self, older_than_hours: int = 24):
        """清理过期缓存"""
        try:
            current_time = time.time()
            cutoff_time = current_time - (older_than_hours * 3600)
            
            cleared_count = 0
            for cache_file in self.cache_dir.glob("*.json"):
                if cache_file.stat().st_mtime < cutoff_time:
                    cache_file.unlink()
                    cleared_count += 1
            
            logger.info(f"清理了 {cleared_count} 个过期缓存文件")
            
        except Exception as e:
            logger.warning(f"清理缓存失败: {e}")

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 尝试获取一条简单数据
            df = await self.get_stock_basic()
            return len(df) > 0
        except Exception as e:
            logger.error(f"Tushare API 健康检查失败: {e}")
            return False