from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from utils.database import Base

class KnowledgeBase(Base):
    """知识库模型"""
    __tablename__ = "knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True)
    knowledge_id = Column(String(100), unique=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # 法律类别
    subcategory = Column(String(50))  # 子类别
    keywords = Column(Text)  # 关键词，逗号分隔
    tags = Column(Text)  # 标签，逗号分隔
    status = Column(String(20), default="active")  # active, inactive, draft
    version = Column(Integer, default=1)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # 关系
    versions = relationship("KnowledgeVersion", back_populates="knowledge", cascade="all, delete-orphan")

class KnowledgeVersion(Base):
    """知识库版本模型"""
    __tablename__ = "knowledge_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    knowledge_id = Column(Integer, ForeignKey('knowledge_base.id'), nullable=False)
    version = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    keywords = Column(Text)
    tags = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # 关系
    knowledge = relationship("KnowledgeBase", back_populates="versions")
