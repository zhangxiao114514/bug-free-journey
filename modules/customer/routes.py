# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, Field

from modules.customer.customer_manager import customer_manager
from modules.customer.ai_customer_manager import ai_customer_manager
from modules.customer.audit_manager import audit_manager

router = APIRouter(
    prefix="/api/customer",
    tags=["customer"],
    responses={404: {"description": "Not found"}},
)

class CustomerCreate(BaseModel):
    """客户创建模型"""
    nickname: str = Field(..., min_length=1, max_length=50, description="客户昵称")
    wechat_id: str = Field(..., min_length=1, max_length=100, description="微信ID")
    phone: Optional[str] = Field(None, regex=r"^1[3-9]\d{9}$", description="手机号码")
    email: Optional[str] = Field(None, description="邮箱地址")
    gender: Optional[str] = Field(None, regex=r"^(男|女)$", description="性别")
    birthday: Optional[str] = Field(None, description="生日")
    address: Optional[str] = Field(None, max_length=200, description="地址")
    company: Optional[str] = Field(None, max_length=100, description="公司")
    remark: Optional[str] = Field(None, max_length=500, description="备注")

class CustomerUpdate(BaseModel):
    """客户更新模型"""
    nickname: Optional[str] = Field(None, min_length=1, max_length=50, description="客户昵称")
    phone: Optional[str] = Field(None, regex=r"^1[3-9]\d{9}$", description="手机号码")
    email: Optional[str] = Field(None, description="邮箱地址")
    gender: Optional[str] = Field(None, regex=r"^(男|女)$", description="性别")
    birthday: Optional[str] = Field(None, description="生日")
    address: Optional[str] = Field(None, max_length=200, description="地址")
    company: Optional[str] = Field(None, max_length=100, description="公司")
    remark: Optional[str] = Field(None, max_length=500, description="备注")
    status: Optional[str] = Field(None, regex=r"^(active|inactive)$", description="状态")

class CustomerTagCreate(BaseModel):
    """客户标签创建模型"""
    name: str = Field(..., min_length=1, max_length=50, description="标签名称")
    description: Optional[str] = Field(None, max_length=200, description="标签描述")

class CustomerResponse(BaseModel):
    """客户响应模型"""
    id: int
    nickname: str
    wechat_id: str
    phone: Optional[str]
    email: Optional[str]
    gender: Optional[str]
    birthday: Optional[str]
    address: Optional[str]
    company: Optional[str]
    remark: Optional[str]
    status: str
    created_at: str
    updated_at: str
    tags: List[str]

    class Config:
        from_attributes = True

class CustomerTagResponse(BaseModel):
    """客户标签响应模型"""
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True

class CustomerProfileResponse(BaseModel):
    """客户画像响应模型"""
    customer_id: int
    nickname: str
    tags: List[str]
    咨询次数: int
    咨询类型分布: dict
    最近咨询时间: Optional[str]
    咨询满意度: float
    活跃程度: str
    潜在需求: List[str]

@router.post("/", response_model=CustomerResponse)
def create_customer(customer: CustomerCreate):
    """创建客户"""
    try:
        customer_data = customer.model_dump()
        created_customer = customer_manager.create_customer(customer_data)
        
        # 转换为响应模型
        tags = [tag.name for tag in created_customer.tags]
        return CustomerResponse(
            id=created_customer.id,
            nickname=created_customer.nickname,
            wechat_id=created_customer.wechat_id,
            phone=created_customer.phone,
            email=created_customer.email,
            gender=created_customer.gender,
            birthday=created_customer.birthday,
            address=created_customer.address,
            company=created_customer.company,
            remark=created_customer.remark,
            status=created_customer.status,
            created_at=created_customer.created_at.isoformat(),
            updated_at=created_customer.updated_at.isoformat(),
            tags=tags
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建客户失败: {str(e)}")

@router.get("/", response_model=List[CustomerResponse])
def list_customers(
    status: Optional[str] = Query(None, regex=r"^(active|inactive)$", description="状态"),
    nickname: Optional[str] = Query(None, description="昵称"),
    phone: Optional[str] = Query(None, description="手机号"),
    tag_id: Optional[int] = Query(None, description="标签ID")
):
    """列出客户"""
    try:
        filters = {}
        if status:
            filters["status"] = status
        if nickname:
            filters["nickname"] = nickname
        if phone:
            filters["phone"] = phone
        if tag_id:
            filters["tag_id"] = tag_id
        
        customers = customer_manager.list_customers(**filters)
        
        # 转换为响应模型
        result = []
        for customer in customers:
            tags = [tag.name for tag in customer.tags]
            result.append(CustomerResponse(
                id=customer.id,
                nickname=customer.nickname,
                wechat_id=customer.wechat_id,
                phone=customer.phone,
                email=customer.email,
                gender=customer.gender,
                birthday=customer.birthday,
                address=customer.address,
                company=customer.company,
                remark=customer.remark,
                status=customer.status,
                created_at=customer.created_at.isoformat(),
                updated_at=customer.updated_at.isoformat(),
                tags=tags
            ))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取客户列表失败: {str(e)}")

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int):
    """获取客户详情"""
    try:
        customer = customer_manager.get_customer(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="客户不存在")
        
        # 转换为响应模型
        tags = [tag.name for tag in customer.tags]
        return CustomerResponse(
            id=customer.id,
            nickname=customer.nickname,
            wechat_id=customer.wechat_id,
            phone=customer.phone,
            email=customer.email,
            gender=customer.gender,
            birthday=customer.birthday,
            address=customer.address,
            company=customer.company,
            remark=customer.remark,
            status=customer.status,
            created_at=customer.created_at.isoformat(),
            updated_at=customer.updated_at.isoformat(),
            tags=tags
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取客户详情失败: {str(e)}")

@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, customer: CustomerUpdate):
    """更新客户信息"""
    try:
        update_data = customer.model_dump(exclude_unset=True)
        updated_customer = customer_manager.update_customer(customer_id, update_data)
        
        # 转换为响应模型
        tags = [tag.name for tag in updated_customer.tags]
        return CustomerResponse(
            id=updated_customer.id,
            nickname=updated_customer.nickname,
            wechat_id=updated_customer.wechat_id,
            phone=updated_customer.phone,
            email=updated_customer.email,
            gender=updated_customer.gender,
            birthday=updated_customer.birthday,
            address=updated_customer.address,
            company=updated_customer.company,
            remark=updated_customer.remark,
            status=updated_customer.status,
            created_at=updated_customer.created_at.isoformat(),
            updated_at=updated_customer.updated_at.isoformat(),
            tags=tags
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新客户信息失败: {str(e)}")

@router.delete("/{customer_id}")
def delete_customer(customer_id: int):
    """删除客户"""
    try:
        customer_manager.delete_customer(customer_id)
        return {"message": "客户删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除客户失败: {str(e)}")

@router.post("/tags", response_model=CustomerTagResponse)
def create_tag(tag: CustomerTagCreate):
    """创建客户标签"""
    try:
        tag_data = tag.model_dump()
        created_tag = customer_manager.create_tag(tag_data)
        return CustomerTagResponse(
            id=created_tag.id,
            name=created_tag.name,
            description=created_tag.description
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建标签失败: {str(e)}")

@router.get("/tags/list", response_model=List[CustomerTagResponse])
def list_tags():
    """列出所有客户标签"""
    try:
        tags = customer_manager.list_tags()
        result = []
        for tag in tags:
            result.append(CustomerTagResponse(
                id=tag.id,
                name=tag.name,
                description=tag.description
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取标签列表失败: {str(e)}")

@router.post("/{customer_id}/tags/{tag_id}")
def add_tag_to_customer(customer_id: int, tag_id: int):
    """为客户添加标签"""
    try:
        customer_manager.add_tag_to_customer(customer_id, tag_id)
        return {"message": "标签添加成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加标签失败: {str(e)}")

@router.delete("/{customer_id}/tags/{tag_id}")
def remove_tag_from_customer(customer_id: int, tag_id: int):
    """从客户移除标签"""
    try:
        customer_manager.remove_tag_from_customer(customer_id, tag_id)
        return {"message": "标签移除成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"移除标签失败: {str(e)}")

@router.get("/{customer_id}/profile", response_model=CustomerProfileResponse)
def get_customer_profile(customer_id: int):
    """获取客户画像"""
    try:
        profile = customer_manager.analyze_customer_profile(customer_id)
        if not profile:
            raise HTTPException(status_code=404, detail="客户不存在")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取客户画像失败: {str(e)}")

# AI相关端点

class AIAuditResponse(BaseModel):
    """AI审核响应模型"""
    id: int
    audit_id: str
    operation_type: str
    target_id: int
    status: str
    priority: str
    description: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

@router.post("/{customer_id}/ai/category")
def predict_customer_category(customer_id: int):
    """预测客户分类"""
    try:
        result = ai_customer_manager.predict_customer_category(customer_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预测客户分类失败: {str(e)}")

@router.post("/{customer_id}/ai/churn-risk")
def predict_churn_risk(customer_id: int):
    """预测客户流失风险"""
    try:
        result = ai_customer_manager.predict_churn_risk(customer_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预测客户流失风险失败: {str(e)}")

@router.post("/{customer_id}/ai/tag-suggestions")
def generate_tag_suggestions(customer_id: int):
    """生成客户标签建议"""
    try:
        result = ai_customer_manager.generate_tag_suggestions(customer_id)
        return {"tag_suggestions": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成标签建议失败: {str(e)}")

@router.post("/{customer_id}/ai/value")
def calculate_customer_value(customer_id: int):
    """计算客户价值"""
    try:
        result = ai_customer_manager.calculate_customer_value(customer_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算客户价值失败: {str(e)}")

@router.post("/{customer_id}/ai/needs")
def predict_customer_needs(customer_id: int):
    """预测客户需求"""
    try:
        result = ai_customer_manager.predict_customer_needs(customer_id)
        return {"needs": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预测客户需求失败: {str(e)}")

@router.post("/{customer_id}/ai/follow-up")
def suggest_follow_up(customer_id: int):
    """生成客户跟进建议"""
    try:
        result = ai_customer_manager.suggest_follow_up(customer_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成跟进建议失败: {str(e)}")

class BatchAnalysisRequest(BaseModel):
    """批量分析请求模型"""
    customer_ids: List[int] = Field(..., min_items=1, max_items=100, description="客户ID列表")

@router.post("/ai/batch-analysis")
def batch_analyze_customers(request: BatchAnalysisRequest):
    """批量分析客户"""
    try:
        results = ai_customer_manager.batch_analyze_customers(request.customer_ids)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量分析客户失败: {str(e)}")

# 审核相关端点

@router.get("/audits/list", response_model=List[AIAuditResponse])
def list_audits(
    status: Optional[str] = Query(None, description="审核状态"),
    operation_type: Optional[str] = Query(None, description="操作类型"),
    priority: Optional[str] = Query(None, description="优先级"),
    limit: int = Query(50, ge=1, le=100, description="限制数量")
):
    """列出审核记录"""
    try:
        filters = {
            "limit": limit
        }
        if status:
            filters["status"] = status
        if operation_type:
            filters["operation_type"] = operation_type
        if priority:
            filters["priority"] = priority
        
        audits = audit_manager.list_audits(**filters)
        result = []
        for audit in audits:
            result.append(AIAuditResponse(
                id=audit.id,
                audit_id=audit.audit_id,
                operation_type=audit.operation_type,
                target_id=audit.target_id,
                status=audit.status,
                priority=audit.priority,
                description=audit.description,
                created_at=audit.created_at.isoformat(),
                updated_at=audit.updated_at.isoformat()
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取审核记录失败: {str(e)}")

@router.get("/audits/pending", response_model=List[AIAuditResponse])
def list_pending_audits(
    priority: Optional[str] = Query(None, description="优先级"),
    limit: int = Query(50, ge=1, le=100, description="限制数量")
):
    """列出待审核记录"""
    try:
        audits = audit_manager.get_pending_audits(priority=priority, limit=limit)
        result = []
        for audit in audits:
            result.append(AIAuditResponse(
                id=audit.id,
                audit_id=audit.audit_id,
                operation_type=audit.operation_type,
                target_id=audit.target_id,
                status=audit.status,
                priority=audit.priority,
                description=audit.description,
                created_at=audit.created_at.isoformat(),
                updated_at=audit.updated_at.isoformat()
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取待审核记录失败: {str(e)}")

class AuditActionRequest(BaseModel):
    """审核操作请求模型"""
    approver_id: int = Field(..., description="审核人ID")
    comments: Optional[str] = Field(None, description="审核意见")

@router.post("/audits/{audit_id}/approve")
def approve_audit(audit_id: int, request: AuditActionRequest):
    """通过审核"""
    try:
        audit = audit_manager.approve_audit(audit_id, request.approver_id, request.comments)
        return {
            "message": "审核通过成功",
            "audit_id": audit.audit_id,
            "status": audit.status
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"审核通过失败: {str(e)}")

@router.post("/audits/{audit_id}/reject")
def reject_audit(audit_id: int, request: AuditActionRequest):
    """拒绝审核"""
    try:
        audit = audit_manager.reject_audit(audit_id, request.approver_id, request.comments)
        return {
            "message": "审核拒绝成功",
            "audit_id": audit.audit_id,
            "status": audit.status
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"审核拒绝失败: {str(e)}")

class BatchAuditRequest(BaseModel):
    """批量审核请求模型"""
    audit_ids: List[int] = Field(..., min_items=1, max_items=50, description="审核ID列表")
    approver_id: int = Field(..., description="审核人ID")
    comments: Optional[str] = Field(None, description="审核意见")

@router.post("/audits/batch/approve")
def batch_approve_audits(request: BatchAuditRequest):
    """批量通过审核"""
    try:
        count = audit_manager.batch_approve_audits(
            request.audit_ids, 
            request.approver_id, 
            request.comments
        )
        return {
            "message": "批量审核通过成功",
            "approved_count": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量审核通过失败: {str(e)}")

@router.post("/audits/batch/reject")
def batch_reject_audits(request: BatchAuditRequest):
    """批量拒绝审核"""
    try:
        count = audit_manager.batch_reject_audits(
            request.audit_ids, 
            request.approver_id, 
            request.comments
        )
        return {
            "message": "批量审核拒绝成功",
            "rejected_count": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量审核拒绝失败: {str(e)}")

@router.get("/audits/statistics")
def get_audit_statistics(
    days: int = Query(30, ge=1, le=365, description="统计天数")
):
    """获取审核统计"""
    try:
        statistics = audit_manager.get_audit_statistics(days)
        return statistics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取审核统计失败: {str(e)}")
