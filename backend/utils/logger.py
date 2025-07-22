"""
日志配置模块
提供统一的日志配置和格式化
"""

import logging
import logging.handlers
import os
from datetime import datetime
from config import settings

def setup_logger():
    """设置日志配置"""
    # 创建日志目录
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 设置日志级别
    log_level = logging.DEBUG if settings.debug else logging.INFO
    
    # 配置根日志器
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # 控制台输出
            logging.StreamHandler(),
            # 文件输出（按日期轮转）
            logging.handlers.TimedRotatingFileHandler(
                filename=os.path.join(log_dir, 'app.log'),
                when='midnight',
                interval=1,
                backupCount=30,
                encoding='utf-8'
            ),
            # 错误日志文件
            logging.handlers.TimedRotatingFileHandler(
                filename=os.path.join(log_dir, 'error.log'),
                when='midnight',
                interval=1,
                backupCount=30,
                encoding='utf-8'
            )
        ]
    )
    
    # 设置错误日志只记录ERROR及以上级别
    error_handler = logging.getLogger().handlers[2]
    error_handler.setLevel(logging.ERROR)
    
    # 设置第三方库日志级别
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('asyncpg').setLevel(logging.WARNING)
    logging.getLogger('tushare').setLevel(logging.WARNING)
    
    # 记录启动信息
    logger = logging.getLogger(__name__)
    logger.info("="*50)
    logger.info("A股连续涨停板量化选股系统启动")
    logger.info(f"日志级别: {logging.getLevelName(log_level)}")
    logger.info(f"日志目录: {os.path.abspath(log_dir)}")
    logger.info("="*50)

class LogFormatter(logging.Formatter):
    """自定义日志格式化器"""
    
    # 颜色码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }
    
    def format(self, record):
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        # 添加进程信息
        record.process_info = f"[PID:{os.getpid()}]"
        
        return super().format(record)

def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器"""
    return logging.getLogger(name)

def log_execution_time(func):
    """日志执行时间装饰器"""
    import functools
    import time
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} 执行完成，耗时: {execution_time:.2f}秒")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} 执行失败，耗时: {execution_time:.2f}秒，错误: {e}")
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} 执行完成，耗时: {execution_time:.2f}秒")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} 执行失败，耗时: {execution_time:.2f}秒，错误: {e}")
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

def log_api_request(func):
    """日志API请求装饰器"""
    import functools
    from fastapi import Request
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        # 查找Request对象
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if request:
            logger.info(f"API请求: {request.method} {request.url.path} - {request.client.host}")
        
        try:
            result = await func(*args, **kwargs)
            if request:
                logger.info(f"API响应: {request.method} {request.url.path} - 成功")
            return result
        except Exception as e:
            if request:
                logger.error(f"API错误: {request.method} {request.url.path} - {str(e)}")
            raise
    
    return wrapper
