from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from utils.database import Base

class Consultation(Base):
    """咨询模型"""
    __tablename__ = "consultations"
    
    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(String(100), unique=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # 法律类别
    status = Column(String(20), default="pending")  # pending, processing, completed, cancelled
    priority = Column(Integer, default=0)  # 优先级：0-低，1-中，2-高
    estimated_time = Column(Integer)  # 预计处理时间（分钟）
    actual_time = Column(Integer)  # 实际处理时间（分钟）
    satisfaction_score = Column(Integer, nullable=True)  # 满意度评分
    feedback = Column(Text, nullable=True)  # 客户反馈
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # 关系
    customer = relationship("Customer", back_populates="consultations")
    user = relationship("User", back_populates="consultations")
    progress = relationship("ConsultationProgress", back_populates="consultation", cascade="all, delete-orphan")

class ConsultationProgress(Base):
    """咨询进度模型"""
    __tablename__ = "consultation_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey('consultations.id'), nullable=False)
    stage = Column(String(50), nullable=False)  # 阶段：受理、分析、解答、反馈
    status = Column(String(20), default="pending")  # pending, in_progress, completed
    description = Column(Text)
    operator_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # 关系
    consultation = relationship("Consultation", back_populates="progress")
