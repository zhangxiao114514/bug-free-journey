# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import json

from modules.contract.contract_manager import contract_manager
from modules.contract.models import ContractStatus, ContractType

router = APIRouter(
    prefix="/api/contract",
    tags=["contract"],
    responses={404: {"description": "Not found"}},
)

class ContractTemplateCreate(BaseModel):
    """合同模板创建模型"""
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, max_length=500, description="模板描述")
    contract_type: str = Field(..., description="合同类型")
    content: str = Field(..., min_length=1, description="模板内容")
    variables: Optional[Dict[str, Any]] = Field(None, description="变量定义")
    created_by: Optional[int] = Field(None, description="创建者ID")
    updated_by: Optional[int] = Field(None, description="更新者ID")

class ContractTemplateUpdate(BaseModel):
    """合同模板更新模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, max_length=500, description="模板描述")
    contract_type: Optional[str] = Field(None, description="合同类型")
    content: Optional[str] = Field(None, min_length=1, description="模板内容")
    variables: Optional[Dict[str, Any]] = Field(None, description="变量定义")
    status: Optional[str] = Field(None, description="状态")
    updated_by: Optional[int] = Field(None, description="更新者ID")

class ContractGenerate(BaseModel):
    """合同生成模型"""
    template_id: int = Field(..., description="模板ID")
    name: Optional[str] = Field(None, max_length=100, description="合同名称")
    variables: Dict[str, Any] = Field(..., description="变量值")
    parties: Optional[Dict[str, Any]] = Field(None, description="合同当事人")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")
    customer_id: Optional[int] = Field(None, description="客户ID")
    user_id: Optional[int] = Field(None, description="用户ID")

class ContractUpdate(BaseModel):
    """合同更新模型"""
    name: Optional[str] = Field(None, max_length=100, description="合同名称")
    parties: Optional[Dict[str, Any]] = Field(None, description="合同当事人")
    variables: Optional[Dict[str, Any]] = Field(None, description="变量值")
    content: Optional[str] = Field(None, description="合同内容")
    status: Optional[str] = Field(None, description="状态")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")

class ContractSignatureCreate(BaseModel):
    """合同签名创建模型"""
    signer_name: str = Field(..., min_length=1, max_length=50, description="签名人姓名")
    signer_role: Optional[str] = Field(None, max_length=50, description="签名人角色")
    signature_data: Optional[str] = Field(None, description="签名数据")

class ContractTemplateResponse(BaseModel):
    """合同模板响应模型"""
    id: int
    template_id: str
    name: str
    description: Optional[str]
    contract_type: str
    status: str
    content: str
    variables: Optional[Dict[str, Any]]
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class ContractResponse(BaseModel):
    """合同响应模型"""
    id: int
    contract_id: str
    template_id: int
    name: str
    parties: Optional[Dict[str, Any]]
    variables: Optional[Dict[str, Any]]
    content: str
    status: str
    start_date: Optional[str]
    end_date: Optional[str]
    customer_id: Optional[int]
    user_id: Optional[int]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class ContractSignatureResponse(BaseModel):
    """合同签名响应模型"""
    id: int
    contract_id: int
    signer_name: str
    signer_role: Optional[str]
    signature_data: Optional[str]
    created_at: str

    class Config:
        from_attributes = True

class ContractPreviewResponse(BaseModel):
    """合同预览响应模型"""
    content: str

@router.post("/templates", response_model=ContractTemplateResponse)
def create_template(template: ContractTemplateCreate):
    """创建合同模板"""
    try:
        template_data = template.model_dump()
        created_template = contract_manager.create_template(template_data)
        
        # 解析variables JSON
        variables = None
        if created_template.variables:
            variables = json.loads(created_template.variables)
        
        return ContractTemplateResponse(
            id=created_template.id,
            template_id=created_template.template_id,
            name=created_template.name,
            description=created_template.description,
            contract_type=created_template.contract_type,
            status=created_template.status,
            content=created_template.content,
            variables=variables,
            created_by=created_template.created_by,
            updated_by=created_template.updated_by,
            created_at=created_template.created_at.isoformat(),
            updated_at=created_template.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建合同模板失败: {str(e)}")

@router.get("/templates", response_model=List[ContractTemplateResponse])
def list_templates(
    status: Optional[str] = Query(None, description="状态"),
    contract_type: Optional[str] = Query(None, description="合同类型")
):
    """列出合同模板"""
    try:
        filters = {}
        if status:
            filters["status"] = status
        if contract_type:
            filters["contract_type"] = contract_type
        
        templates = contract_manager.list_templates(**filters)
        result = []
        for template in templates:
            # 解析variables JSON
            variables = None
            if template.variables:
                variables = json.loads(template.variables)
            
            result.append(ContractTemplateResponse(
                id=template.id,
                template_id=template.template_id,
                name=template.name,
                description=template.description,
                contract_type=template.contract_type,
                status=template.status,
                content=template.content,
                variables=variables,
                created_by=template.created_by,
                updated_by=template.updated_by,
                created_at=template.created_at.isoformat(),
                updated_at=template.updated_at.isoformat()
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取合同模板列表失败: {str(e)}")

@router.get("/templates/{template_id}", response_model=ContractTemplateResponse)
def get_template(template_id: int):
    """获取合同模板"""
    try:
        template = contract_manager.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 解析variables JSON
        variables = None
        if template.variables:
            variables = json.loads(template.variables)
        
        return ContractTemplateResponse(
            id=template.id,
            template_id=template.template_id,
            name=template.name,
            description=template.description,
            contract_type=template.contract_type,
            status=template.status,
            content=template.content,
            variables=variables,
            created_by=template.created_by,
            updated_by=template.updated_by,
            created_at=template.created_at.isoformat(),
            updated_at=template.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取合同模板失败: {str(e)}")

@router.put("/templates/{template_id}", response_model=ContractTemplateResponse)
def update_template(template_id: int, template: ContractTemplateUpdate):
    """更新合同模板"""
    try:
        update_data = template.model_dump(exclude_unset=True)
        updated_template = contract_manager.update_template(template_id, update_data)
        
        # 解析variables JSON
        variables = None
        if updated_template.variables:
            variables = json.loads(updated_template.variables)
        
        return ContractTemplateResponse(
            id=updated_template.id,
            template_id=updated_template.template_id,
            name=updated_template.name,
            description=updated_template.description,
            contract_type=updated_template.contract_type,
            status=updated_template.status,
            content=updated_template.content,
            variables=variables,
            created_by=updated_template.created_by,
            updated_by=updated_template.updated_by,
            created_at=updated_template.created_at.isoformat(),
            updated_at=updated_template.updated_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新合同模板失败: {str(e)}")

@router.delete("/templates/{template_id}")
def delete_template(template_id: int):
    """删除合同模板"""
    try:
        contract_manager.delete_template(template_id)
        return {"message": "合同模板删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除合同模板失败: {str(e)}")

@router.post("/templates/{template_id}/activate", response_model=ContractTemplateResponse)
def activate_template(template_id: int):
    """激活合同模板"""
    try:
        activated_template = contract_manager.activate_template(template_id)
        
        # 解析variables JSON
        variables = None
        if activated_template.variables:
            variables = json.loads(activated_template.variables)
        
        return ContractTemplateResponse(
            id=activated_template.id,
            template_id=activated_template.template_id,
            name=activated_template.name,
            description=activated_template.description,
            contract_type=activated_template.contract_type,
            status=activated_template.status,
            content=activated_template.content,
            variables=variables,
            created_by=activated_template.created_by,
            updated_by=activated_template.updated_by,
            created_at=activated_template.created_at.isoformat(),
            updated_at=activated_template.updated_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"激活合同模板失败: {str(e)}")

@router.post("/templates/{template_id}/archive", response_model=ContractTemplateResponse)
def archive_template(template_id: int):
    """归档合同模板"""
    try:
        archived_template = contract_manager.archive_template(template_id)
        
        # 解析variables JSON
        variables = None
        if archived_template.variables:
            variables = json.loads(archived_template.variables)
        
        return ContractTemplateResponse(
            id=archived_template.id,
            template_id=archived_template.template_id,
            name=archived_template.name,
            description=archived_template.description,
            contract_type=archived_template.contract_type,
            status=archived_template.status,
            content=archived_template.content,
            variables=variables,
            created_by=archived_template.created_by,
            updated_by=archived_template.updated_by,
            created_at=archived_template.created_at.isoformat(),
            updated_at=archived_template.updated_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"归档合同模板失败: {str(e)}")

@router.post("/generate", response_model=ContractResponse)
def generate_contract(contract_data: ContractGenerate):
    """生成合同"""
    try:
        data = contract_data.model_dump()
        generated_contract = contract_manager.generate_contract(data)
        
        # 解析JSON字段
        parties = None
        if generated_contract.parties:
            parties = json.loads(generated_contract.parties)
        variables = None
        if generated_contract.variables:
            variables = json.loads(generated_contract.variables)
        
        return ContractResponse(
            id=generated_contract.id,
            contract_id=generated_contract.contract_id,
            template_id=generated_contract.template_id,
            name=generated_contract.name,
            parties=parties,
            variables=variables,
            content=generated_contract.content,
            status=generated_contract.status,
            start_date=generated_contract.start_date.isoformat() if generated_contract.start_date else None,
            end_date=generated_contract.end_date.isoformat() if generated_contract.end_date else None,
            customer_id=generated_contract.customer_id,
            user_id=generated_contract.user_id,
            created_at=generated_contract.created_at.isoformat(),
            updated_at=generated_contract.updated_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成合同失败: {str(e)}")

@router.get("/", response_model=List[ContractResponse])
def list_contracts(
    status: Optional[str] = Query(None, description="状态"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    template_id: Optional[int] = Query(None, description="模板ID")
):
    """列出合同"""
    try:
        filters = {}
        if status:
            filters["status"] = status
        if customer_id:
            filters["customer_id"] = customer_id
        if user_id:
            filters["user_id"] = user_id
        if template_id:
            filters["template_id"] = template_id
        
        contracts = contract_manager.list_contracts(**filters)
        result = []
        for contract in contracts:
            # 解析JSON字段
            parties = None
            if contract.parties:
                parties = json.loads(contract.parties)
            variables = None
            if contract.variables:
                variables = json.loads(contract.variables)
            
            result.append(ContractResponse(
                id=contract.id,
                contract_id=contract.contract_id,
                template_id=contract.template_id,
                name=contract.name,
                parties=parties,
                variables=variables,
                content=contract.content,
                status=contract.status,
                start_date=contract.start_date.isoformat() if contract.start_date else None,
                end_date=contract.end_date.isoformat() if contract.end_date else None,
                customer_id=contract.customer_id,
                user_id=contract.user_id,
                created_at=contract.created_at.isoformat(),
                updated_at=contract.updated_at.isoformat()
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取合同列表失败: {str(e)}")

@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(contract_id: int):
    """获取合同"""
    try:
        contract = contract_manager.get_contract(contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="合同不存在")
        
        # 解析JSON字段
        parties = None
        if contract.parties:
            parties = json.loads(contract.parties)
        variables = None
        if contract.variables:
            variables = json.loads(contract.variables)
        
        return ContractResponse(
            id=contract.id,
            contract_id=contract.contract_id,
            template_id=contract.template_id,
            name=contract.name,
            parties=parties,
            variables=variables,
            content=contract.content,
            status=contract.status,
            start_date=contract.start_date.isoformat() if contract.start_date else None,
            end_date=contract.end_date.isoformat() if contract.end_date else None,
            customer_id=contract.customer_id,
            user_id=contract.user_id,
            created_at=contract.created_at.isoformat(),
            updated_at=contract.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取合同失败: {str(e)}")

@router.put("/{contract_id}", response_model=ContractResponse)
def update_contract(contract_id: int, contract: ContractUpdate):
    """更新合同"""
    try:
        update_data = contract.model_dump(exclude_unset=True)
        updated_contract = contract_manager.update_contract(contract_id, update_data)
        
        # 解析JSON字段
        parties = None
        if updated_contract.parties:
            parties = json.loads(updated_contract.parties)
        variables = None
        if updated_contract.variables:
            variables = json.loads(updated_contract.variables)
        
        return ContractResponse(
            id=updated_contract.id,
            contract_id=updated_contract.contract_id,
            template_id=updated_contract.template_id,
            name=updated_contract.name,
            parties=parties,
            variables=variables,
            content=updated_contract.content,
            status=updated_contract.status,
            start_date=updated_contract.start_date.isoformat() if updated_contract.start_date else None,
            end_date=updated_contract.end_date.isoformat() if updated_contract.end_date else None,
            customer_id=updated_contract.customer_id,
            user_id=updated_contract.user_id,
            created_at=updated_contract.created_at.isoformat(),
            updated_at=updated_contract.updated_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新合同失败: {str(e)}")

@router.post("/{contract_id}/signatures", response_model=ContractSignatureResponse)
def add_contract_signature(contract_id: int, signature: ContractSignatureCreate):
    """添加合同签名"""
    try:
        signature_data = signature.model_dump()
        created_signature = contract_manager.add_contract_signature(contract_id, signature_data)
        return ContractSignatureResponse(
            id=created_signature.id,
            contract_id=created_signature.contract_id,
            signer_name=created_signature.signer_name,
            signer_role=created_signature.signer_role,
            signature_data=created_signature.signature_data,
            created_at=created_signature.created_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加合同签名失败: {str(e)}")

@router.post("/preview", response_model=ContractPreviewResponse)
def preview_contract(template_id: int = Query(..., description="模板ID"), variables: Optional[Dict[str, Any]] = Query(None, description="变量值")):
    """预览合同"""
    try:
        preview_content = contract_manager.preview_contract(template_id, variables or {})
        return ContractPreviewResponse(content=preview_content)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览合同失败: {str(e)}")
