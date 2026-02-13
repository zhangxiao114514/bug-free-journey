from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, Dict, Any
import time
import logging

from utils.config import config_manager

logger = logging.getLogger(__name__)

# 获取数据库配置
db_config = {
    'host': config_manager.get('database', 'host'),
    'port': config_manager.getint('database', 'port'),
    'user': config_manager.get('database', 'user'),
    'password': config_manager.get('database', 'password'),
    'database': config_manager.get('database', 'database'),
    'charset': config_manager.get('database', 'charset'),
}

# 构建数据库URL
DATABASE_URL = f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}?charset={db_config['charset']}"

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    pool_size=config_manager.getint('database', 'pool_size', 10),
    max_overflow=config_manager.getint('database', 'max_overflow', 20),
    pool_pre_ping=True,
    pool_recycle=3600,  # 连接回收时间
    pool_timeout=30,  # 连接池超时时间
    echo=False,  # 生产环境关闭SQL日志
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 数据库查询缓存
query_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = 300  # 缓存过期时间（秒）

def get_db() -> Generator[Session, None, None]:
    """获取数据库会话
    
    Yields:
        数据库会话
    """
    db = SessionLocal()
    start_time = time.time()
    try:
        yield db
    finally:
        execution_time = time.time() - start_time
        if execution_time > 1.0:  # 记录执行时间超过1秒的查询
            logger.warning(f"数据库会话执行时间较长: {execution_time:.2f}秒")
        db.close()

def init_db():
    """初始化数据库（创建所有表）"""
    # 导入所有模型，确保它们被注册
    from modules.system.models import User
    from modules.customer.models import Customer, CustomerTag
    from modules.message.models import Message
    from modules.consultation.models import Consultation, ConsultationProgress
    from modules.knowledge.models import KnowledgeBase, KnowledgeVersion
    from modules.document.models import Document, DocumentVersion
    from modules.notification.models import Notification
    from modules.analytics.models import AnalyticsData
    from modules.case.models import Case, CaseTag, CaseDocument, CaseProgress
    from modules.contract.models import ContractTemplate, Contract, ContractSignature
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)

def cache_query(key: str, func, *args, **kwargs):
    """缓存查询结果
    
    Args:
        key: 缓存键
        func: 查询函数
        *args: 函数参数
        **kwargs: 函数关键字参数
        
    Returns:
        查询结果
    """
    # 检查缓存是否存在且未过期
    if key in query_cache:
        cache_data = query_cache[key]
        if time.time() - cache_data['timestamp'] < CACHE_TTL:
            logger.debug(f"使用缓存查询结果: {key}")
            return cache_data['result']
    
    # 执行查询
    result = func(*args, **kwargs)
    
    # 更新缓存
    query_cache[key] = {
        'result': result,
        'timestamp': time.time()
    }
    
    # 清理过期缓存
    _cleanup_cache()
    
    return result

def _cleanup_cache():
    """清理过期缓存"""
    current_time = time.time()
    expired_keys = [key for key, data in query_cache.items() 
                   if current_time - data['timestamp'] >= CACHE_TTL]
    
    for key in expired_keys:
        del query_cache[key]
    
    if expired_keys:
        logger.debug(f"清理过期缓存: {len(expired_keys)}个")

def clear_cache():
    """清空所有缓存"""
    query_cache.clear()
    logger.info("数据库查询缓存已清空")
