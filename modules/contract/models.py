from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from utils.database import Base

class ContractType(str, enum.Enum):
    """合同类型枚举"""
    EMPLOYMENT = "employment"  # 劳动合同
    SERVICE = "service"  # 服务合同
    SALES = "sales"  # 销售合同
    LEASE = "lease"  # 租赁合同
    PARTNERSHIP = "partnership"  # 合作合同
    NON_DISCLOSURE = "non_disclosure"  # 保密协议
    FRANCHISE = "franchise"  # 特许经营合同
    LOAN = "loan"  # 借款合同
    INSURANCE = "insurance"  # 保险合同
    OTHER = "other"  # 其他合同

class ContractStatus(str, enum.Enum):
    """合同状态枚举"""
    DRAFT = "draft"  # 草稿
    ACTIVE = "active"  # 活跃
    ARCHIVED = "archived"  # 已归档

class ContractTemplate(Base):
    """合同模板模型"""
    __tablename__ = "contract_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(50), unique=True, index=True, nullable=False)  # 模板编号
    name = Column(String(200), nullable=False)  # 模板名称
    description = Column(Text)  # 模板描述
    contract_type = Column(Enum(ContractType), nullable=False)  # 合同类型
    status = Column(Enum(ContractStatus), default=ContractStatus.DRAFT)  # 模板状态
    content = Column(Text, nullable=False)  # 模板内容（支持变量占位符）
    variables = Column(Text)  # 变量定义（JSON格式）
    created_by = Column(Integer, ForeignKey("users.id"))  # 创建人
    updated_by = Column(Integer, ForeignKey("users.id"))  # 更新人
    created_at = Column(DateTime, server_default=func.now())  # 创建时间
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())  # 更新时间
    
    # 关系
    creator = relationship("User", foreign_keys=[created_by], backref="created_templates")
    updater = relationship("User", foreign_keys=[updated_by], backref="updated_templates")
    contracts = relationship("Contract", back_populates="template")

class Contract(Base):
    """合同模型"""
    __tablename__ = "contracts"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(String(50), unique=True, index=True, nullable=False)  # 合同编号
    template_id = Column(Integer, ForeignKey("contract_templates.id"))  # 关联模板
    name = Column(String(200), nullable=False)  # 合同名称
    parties = Column(Text)  # 合同各方信息（JSON格式）
    variables = Column(Text)  # 变量值（JSON格式）
    content = Column(Text, nullable=False)  # 生成的合同内容
    status = Column(String(50), default="draft")  # 合同状态
    start_date = Column(DateTime)  # 开始日期
    end_date = Column(DateTime)  # 结束日期
    customer_id = Column(Integer, ForeignKey("customers.id"))  # 关联客户
    user_id = Column(Integer, ForeignKey("users.id"))  # 处理人
    created_at = Column(DateTime, server_default=func.now())  # 创建时间
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())  # 更新时间
    
    # 关系
    template = relationship("ContractTemplate", back_populates="contracts")
    customer = relationship("Customer", backref="contracts")
    user = relationship("User", backref="contracts")

class ContractSignature(Base):
    """合同签名模型"""
    __tablename__ = "contract_signatures"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)  # 关联合同
    signer_name = Column(String(100), nullable=False)  # 签名人姓名
    signer_role = Column(String(100))  # 签名人角色
    signature_data = Column(Text)  # 签名数据
    signed_at = Column(DateTime, server_default=func.now())  # 签名时间
    
    # 关系
    contract = relationship("Contract", backref="signatures")
