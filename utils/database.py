from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from utils.config import config_manager

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
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """获取数据库会话
    
    Yields:
        数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
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
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
