from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from utils.database import Base

class Message(Base):
    """消息模型"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(100), unique=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    type = Column(String(20), nullable=False)  # text, image, voice, video, file
    content = Column(Text)
    media_url = Column(String(255))
    media_path = Column(String(255))
    priority = Column(Integer, default=0)  # 优先级：0-低，1-中，2-高
    status = Column(String(20), default="pending")  # pending, processing, processed, failed
    retry_count = Column(Integer, default=0)
    intent = Column(String(50))
    entities = Column(Text)  # JSON格式存储实体信息
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    processed_at = Column(DateTime, nullable=True)
    
    # 关系
    customer = relationship("Customer", back_populates="messages")
