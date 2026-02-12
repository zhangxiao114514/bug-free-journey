from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from utils.database import Base

class CaseStatus(str, enum.Enum):
    """案例状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CLOSED = "closed"

class CaseType(str, enum.Enum):
    """案例类型枚举"""
    CONTRACT = "contract"
    LABOR = "labor"
    CIVIL = "civil"
    CRIMINAL = "criminal"
    PROPERTY = "property"
    MARRIAGE = "marriage"
    INTELLECTUAL = "intellectual"
    ADMINISTRATIVE = "administrative"
    COMPANY = "company"
    OTHER = "other"

class Case(Base):
    """案例模型"""
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), unique=True, index=True, nullable=False)  # 案例编号
    title = Column(String(200), nullable=False)  # 案例标题
    description = Column(Text)  # 案例描述
    case_type = Column(Enum(CaseType), nullable=False)  # 案例类型
    status = Column(Enum(CaseStatus), default=CaseStatus.PENDING)  # 案例状态
    priority = Column(Integer, default=0)  # 优先级
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)  # 关联客户
    user_id = Column(Integer, ForeignKey("users.id"))  # 处理人
    start_date = Column(DateTime, server_default=func.now())  # 开始日期
    end_date = Column(DateTime)  # 结束日期
    satisfaction_score = Column(Integer)  # 满意度评分
    feedback = Column(Text)  # 客户反馈
    created_at = Column(DateTime, server_default=func.now())  # 创建时间
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())  # 更新时间
    
    # 关系
    customer = relationship("Customer", backref="cases")
    user = relationship("User", backref="cases")
    tags = relationship("CaseTag", back_populates="case", cascade="all, delete-orphan")
    documents = relationship("CaseDocument", back_populates="case", cascade="all, delete-orphan")
    progresses = relationship("CaseProgress", back_populates="case", cascade="all, delete-orphan")

class CaseTag(Base):
    """案例标签模型"""
    __tablename__ = "case_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)  # 关联案例
    tag_name = Column(String(50), nullable=False)  # 标签名称
    created_at = Column(DateTime, server_default=func.now())  # 创建时间
    
    # 关系
    case = relationship("Case", back_populates="tags")

class CaseDocument(Base):
    """案例文档模型"""
    __tablename__ = "case_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)  # 关联案例
    document_name = Column(String(200), nullable=False)  # 文档名称
    document_path = Column(String(500), nullable=False)  # 文档路径
    document_type = Column(String(50))  # 文档类型
    description = Column(Text)  # 文档描述
    uploaded_by = Column(Integer, ForeignKey("users.id"))  # 上传人
    uploaded_at = Column(DateTime, server_default=func.now())  # 上传时间
    
    # 关系
    case = relationship("Case", back_populates="documents")
    uploader = relationship("User", backref="uploaded_documents")

class CaseProgress(Base):
    """案例进度模型"""
    __tablename__ = "case_progresses"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)  # 关联案例
    stage = Column(String(100), nullable=False)  # 阶段名称
    description = Column(Text)  # 阶段描述
    status = Column(String(50), default="in_progress")  # 阶段状态
    started_at = Column(DateTime, server_default=func.now())  # 开始时间
    completed_at = Column(DateTime)  # 完成时间
    
    # 关系
    case = relationship("Case", back_populates="progresses")
