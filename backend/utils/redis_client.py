"""
Redis客户端封装
提供缓存和会话管理功能
"""

import redis.asyncio as redis
import json
import logging
from typing import Any, Optional, Union
from datetime import timedelta

from config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    """异步Redis客户端封装"""
    
    def __init__(self):
        self.redis_pool = None
        self.redis_client = None
    
    async def init_redis(self):
        """初始化Redis连接"""
        try:
            # 创建Redis连接池
            self.redis_pool = redis.ConnectionPool(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
                max_connections=20
            )
            
            # 创建Redis客户端
            self.redis_client = redis.Redis(connection_pool=self.redis_pool)
            
            # 测试连接
            await self.redis_client.ping()
            
            logger.info(f"Redis连接成功: {settings.redis_host}:{settings.redis_port}")
            
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            raise
    
    async def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
        if self.redis_pool:
            await self.redis_pool.disconnect()
        logger.info("Redis连接已关闭")
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            if not self.redis_client:
                await self.init_redis()
            
            value = await self.redis_client.get(key)
            if value:
                try:
                    # 尝试解析JSON
                    return json.loads(value)
                except json.JSONDecodeError:
                    # 如果不是JSON，直接返回字符串
                    return value
            return None
            
        except Exception as e:
            logger.error(f"Redis获取数据失败 {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, expire: Optional[Union[int, timedelta]] = None) -> bool:
        """设置缓存值"""
        try:
            if not self.redis_client:
                await self.init_redis()
            
            # 如果是复杂对象，转换为JSON
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            # 设置值和过期时间
            result = await self.redis_client.set(key, value, ex=expire)
            return result
            
        except Exception as e:
            logger.error(f"Redis设置数据失败 {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            if not self.redis_client:
                await self.init_redis()
            
            result = await self.redis_client.delete(key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis删除数据失败 {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            if not self.redis_client:
                await self.init_redis()
            
            result = await self.redis_client.exists(key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis检查键存在失败 {key}: {e}")
            return False
    
    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """增加计数器"""
        try:
            if not self.redis_client:
                await self.init_redis()
            
            result = await self.redis_client.incr(key, amount)
            return result
            
        except Exception as e:
            logger.error(f"Redis增加计数器失败 {key}: {e}")
            return None
    
    async def expire(self, key: str, time: Union[int, timedelta]) -> bool:
        """设置键的过期时间"""
        try:
            if not self.redis_client:
                await self.init_redis()
            
            result = await self.redis_client.expire(key, time)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis设置过期时间失败 {key}: {e}")
            return False
    
    async def hset(self, name: str, key: str, value: Any) -> bool:
        """设置Hash字段值"""
        try:
            if not self.redis_client:
                await self.init_redis()
            
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            result = await self.redis_client.hset(name, key, value)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis设置Hash失败 {name}.{key}: {e}")
            return False
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """获取Hash字段值"""
        try:
            if not self.redis_client:
                await self.init_redis()
            
            value = await self.redis_client.hget(name, key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
            
        except Exception as e:
            logger.error(f"Redis获取Hash失败 {name}.{key}: {e}")
            return None
    
    async def hgetall(self, name: str) -> dict:
        """获取整个Hash"""
        try:
            if not self.redis_client:
                await self.init_redis()
            
            result = await self.redis_client.hgetall(name)
            
            # 尝试解析JSON值
            parsed_result = {}
            for k, v in result.items():
                try:
                    parsed_result[k] = json.loads(v)
                except json.JSONDecodeError:
                    parsed_result[k] = v
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"Redis获取Hash所有值失败 {name}: {e}")
            return {}
    
    async def cache_strategy_result(self, trade_date: str, results: list, expire_hours: int = 24):
        """缓存策略结果"""
        cache_key = f"strategy_results:{trade_date}"
        expire_time = timedelta(hours=expire_hours)
        
        success = await self.set(cache_key, results, expire_time)
        if success:
            logger.info(f"策略结果已缓存: {cache_key}")
        return success
    
    async def get_cached_strategy_result(self, trade_date: str) -> Optional[list]:
        """获取缓存的策略结果"""
        cache_key = f"strategy_results:{trade_date}"
        return await self.get(cache_key)
    
    async def cache_market_data(self, trade_date: str, data_type: str, data: Any, expire_hours: int = 6):
        """缓存市场数据"""
        cache_key = f"market_data:{trade_date}:{data_type}"
        expire_time = timedelta(hours=expire_hours)
        
        success = await self.set(cache_key, data, expire_time)
        if success:
            logger.info(f"市场数据已缓存: {cache_key}")
        return success
    
    async def get_cached_market_data(self, trade_date: str, data_type: str) -> Optional[Any]:
        """获取缓存的市场数据"""
        cache_key = f"market_data:{trade_date}:{data_type}"
        return await self.get(cache_key)
    
    async def clear_cache(self, pattern: str = None) -> int:
        """清理缓存"""
        try:
            if not self.redis_client:
                await self.init_redis()
            
            if pattern:
                # 清理匹配的键
                keys = await self.redis_client.keys(pattern)
                if keys:
                    deleted = await self.redis_client.delete(*keys)
                    logger.info(f"清理缓存: {deleted} 个键匹配 '{pattern}'")
                    return deleted
            else:
                # 清理所有缓存
                await self.redis_client.flushdb()
                logger.info("所有缓存已清理")
                return -1
            
            return 0
            
        except Exception as e:
            logger.error(f"Redis清理缓存失败: {e}")
            return 0

# 全局Redis客户端实例
redis_client = RedisClient()

# 缓存装饰器
def cache_result(key_prefix: str, expire_hours: int = 1):
    """缓存结果装饰器"""
    def decorator(func):
        import functools
        import hashlib
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            key_data = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            key_hash = hashlib.md5(key_data.encode()).hexdigest()[:8]
            cache_key = f"{key_prefix}:{key_hash}"
            
            # 尝试获取缓存
            cached_result = await redis_client.get(cache_key)
            if cached_result is not None:
                logger.debug(f"命中缓存: {cache_key}")
                return cached_result
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            
            if result is not None:
                expire_time = timedelta(hours=expire_hours)
                await redis_client.set(cache_key, result, expire_time)
                logger.debug(f"结果已缓存: {cache_key}")
            
            return result
        
        return wrapper
    return decorator
