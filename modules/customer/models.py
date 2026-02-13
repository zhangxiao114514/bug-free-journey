from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Table, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from utils.database import Base

# 客户和标签的多对多关系表
customer_tag_association = Table(
    'customer_tag_association',
    Base.metadata,
    Column('customer_id', Integer, ForeignKey('customers.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('customer_tags.id'), primary_key=True)
)

class Customer(Base):
    """客户模型"""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    wechat_id = Column(String(100), unique=True, index=True)
    nickname = Column(String(100))
    avatar = Column(String(255))
    phone = Column(String(20))
    email = Column(String(100))
    real_name = Column(String(50))
    id_card = Column(String(20))
    address = Column(Text)
    status = Column(String(20), default="active")  # active, inactive
    
    # AI相关字段
    customer_category = Column(String(50))  # 客户分类
    churn_risk = Column(String(20))  # 流失风险等级
    churn_risk_score = Column(Float)  # 流失风险分数
    customer_value = Column(String(20))  # 客户价值等级
    customer_value_score = Column(Float)  # 客户价值分数
    predicted_lifetime_value = Column(Float)  # 预测生命周期价值
    last_ai_analysis = Column(DateTime)  # 最后AI分析时间
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    messages = relationship("Message", back_populates="customer")
    consultations = relationship("Consultation", back_populates="customer")
    tags = relationship("CustomerTag", secondary=customer_tag_association, back_populates="customers")
    audits = relationship("AIAudit", back_populates="customer", foreign_keys="AIAudit.target_id")

class CustomerTag(Base):
    """客户标签模型"""
    __tablename__ = "customer_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    color = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    customers = relationship("Customer", secondary=customer_tag_association, back_populates="tags")

class AIAudit(Base):
    """AI操作审核模型"""
    __tablename__ = "ai_audits"
    
    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(String(100), unique=True, index=True)  # 审核ID
    operation_type = Column(String(100), nullable=False)  # 操作类型
    target_id = Column(Integer, nullable=False)  # 目标ID（如客户ID）
    status = Column(String(20), default="pending")  # pending, approved, rejected, expired
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    data = Column(Text)  # 审核数据（JSON格式）
    description = Column(Text)  # 描述
    approver_id = Column(Integer)  # 审核人ID
    approval_comments = Column(Text)  # 审核意见
    approval_time = Column(DateTime)  # 审核时间
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    customer = relationship("Customer", back_populates="audits", foreign_keys=[target_id])
