from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Table
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
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    messages = relationship("Message", back_populates="customer")
    consultations = relationship("Consultation", back_populates="customer")
    tags = relationship("CustomerTag", secondary=customer_tag_association, back_populates="customers")

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
