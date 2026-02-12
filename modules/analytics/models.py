from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from utils.database import Base

class AnalyticsData(Base):
    """统计分析数据模型"""
    __tablename__ = "analytics_data"
    
    id = Column(Integer, primary_key=True, index=True)
    data_type = Column(String(50), nullable=False)  # consultation, message, document, satisfaction
    category = Column(String(50))  # 分类
    subcategory = Column(String(50))  # 子分类
    value = Column(Integer, nullable=False)  # 数值
    value_float = Column(Float, nullable=True)  # 浮点数值
    description = Column(Text)
    date = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())
