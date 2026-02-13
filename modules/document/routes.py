# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from typing import List, Optional
from pydantic import BaseModel, Field
import os
import tempfile

from modules.document.document_manager import document_manager

router = APIRouter(
    prefix="/api/document",
    tags=["document"],
    responses={404: {"description": "Not found"}},
)

class DocumentCreate(BaseModel):
    """文档创建模型"""
    customer_id: Optional[int] = Field(None, description="客户ID")
    title: Optional[str] = Field(None, max_length=100, description="文档标题")
    description: Optional[str] = Field(None, max_length=500, description="文档描述")
    created_by: Optional[int] = Field(None, description="创建者ID")

class DocumentUpdate(BaseModel):
    """文档更新模型"""
    title: Optional[str] = Field(None, max_length=100, description="文档标题")
    description: Optional[str] = Field(None, max_length=500, description="文档描述")
    status: Optional[str] = Field(None, regex=r"^(active|inactive|archived)$", description="状态")

class DocumentResponse(BaseModel):
    """文档响应模型"""
    id: int
    document_id: str
    customer_id: Optional[int]
    title: str
    description: Optional[str]
    file_name: str
    file_type: str
    file_size: int
    status: str
    ocr_processed: bool
    content_extracted: bool
    created_by: Optional[int]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class DocumentVersionResponse(BaseModel):
    """文档版本响应模型"""
    id: int
    document_id: int
    version: int
    file_name: str
    file_size: int
    created_by: Optional[int]
    created_at: str

    class Config:
        from_attributes = True

class DocumentAnalysisResponse(BaseModel):
    """文档分析响应模型"""
    document_id: int
    title: str
    file_type: str
    file_size: int
    content_analysis: dict
    risk_assessment: dict

@router.post("/", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(..., description="要上传的文件"),
    customer_id: Optional[int] = Form(None, description="客户ID"),
    title: Optional[str] = Form(None, description="文档标题"),
    description: Optional[str] = Form(None, description="文档描述"),
    created_by: Optional[int] = Form(None, description="创建者ID")
):
    """上传文档"""
    try:
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 准备文档数据
            document_data = {
                "customer_id": customer_id,
                "title": title,
                "description": description,
                "created_by": created_by
            }
            
            # 上传文档
            uploaded_document = document_manager.upload_document(temp_file_path, document_data)
            
            return DocumentResponse(
                id=uploaded_document.id,
                document_id=uploaded_document.document_id,
                customer_id=uploaded_document.customer_id,
                title=uploaded_document.title,
                description=uploaded_document.description,
                file_name=uploaded_document.file_name,
                file_type=uploaded_document.file_type,
                file_size=uploaded_document.file_size,
                status=uploaded_document.status,
                ocr_processed=uploaded_document.ocr_processed,
                content_extracted=uploaded_document.content_extracted,
                created_by=uploaded_document.created_by,
                created_at=uploaded_document.created_at.isoformat(),
                updated_at=uploaded_document.updated_at.isoformat()
            )
        finally:
            # 删除临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传文档失败: {str(e)}")

@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    customer_id: Optional[int] = Query(None, description="客户ID"),
    status: Optional[str] = Query(None, regex=r"^(active|inactive|archived)$", description="状态"),
    file_type: Optional[str] = Query(None, description="文件类型")
):
    """列出文档"""
    try:
        filters = {}
        if customer_id:
            filters["customer_id"] = customer_id
        if status:
            filters["status"] = status
        if file_type:
            filters["file_type"] = file_type
        
        documents = document_manager.list_documents(**filters)
        result = []
        for document in documents:
            result.append(DocumentResponse(
                id=document.id,
                document_id=document.document_id,
                customer_id=document.customer_id,
                title=document.title,
                description=document.description,
                file_name=document.file_name,
                file_type=document.file_type,
                file_size=document.file_size,
                status=document.status,
                ocr_processed=document.ocr_processed,
                content_extracted=document.content_extracted,
                created_by=document.created_by,
                created_at=document.created_at.isoformat(),
                updated_at=document.updated_at.isoformat()
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int):
    """获取文档详情"""
    try:
        document = document_manager.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        return DocumentResponse(
            id=document.id,
            document_id=document.document_id,
            customer_id=document.customer_id,
            title=document.title,
            description=document.description,
            file_name=document.file_name,
            file_type=document.file_type,
            file_size=document.file_size,
            status=document.status,
            ocr_processed=document.ocr_processed,
            content_extracted=document.content_extracted,
            created_by=document.created_by,
            created_at=document.created_at.isoformat(),
            updated_at=document.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档详情失败: {str(e)}")

@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(document_id: int, document: DocumentUpdate):
    """更新文档信息"""
    try:
        update_data = document.model_dump(exclude_unset=True)
        updated_document = document_manager.update_document(document_id, update_data)
        return DocumentResponse(
            id=updated_document.id,
            document_id=updated_document.document_id,
            customer_id=updated_document.customer_id,
            title=updated_document.title,
            description=updated_document.description,
            file_name=updated_document.file_name,
            file_type=updated_document.file_type,
            file_size=updated_document.file_size,
            status=updated_document.status,
            ocr_processed=updated_document.ocr_processed,
            content_extracted=updated_document.content_extracted,
            created_by=updated_document.created_by,
            created_at=updated_document.created_at.isoformat(),
            updated_at=updated_document.updated_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新文档信息失败: {str(e)}")

@router.delete("/{document_id}")
def delete_document(document_id: int):
    """删除文档"""
    try:
        document_manager.delete_document(document_id)
        return {"message": "文档删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")

@router.get("/{document_id}/versions", response_model=List[DocumentVersionResponse])
def get_document_versions(document_id: int):
    """获取文档版本"""
    try:
        versions = document_manager.get_document_versions(document_id)
        result = []
        for version in versions:
            result.append(DocumentVersionResponse(
                id=version.id,
                document_id=version.document_id,
                version=version.version,
                file_name=version.file_name,
                file_size=version.file_size,
                created_by=version.created_by,
                created_at=version.created_at.isoformat()
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档版本失败: {str(e)}")

@router.get("/{document_id}/analyze", response_model=DocumentAnalysisResponse)
def analyze_document(document_id: int):
    """分析文档"""
    try:
        analysis = document_manager.analyze_document(document_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="文档不存在")
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析文档失败: {str(e)}")
