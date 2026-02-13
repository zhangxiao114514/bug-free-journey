# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, Field

from modules.case.case_manager import case_manager
from modules.case.models import CaseStatus, CaseType

router = APIRouter(
    prefix="/api/case",
    tags=["case"],
    responses={404: {"description": "Not found"}},
)

class CaseCreate(BaseModel):
    """案例创建模型"""
    title: str = Field(..., min_length=1, max_length=100, description="案例标题")
    description: Optional[str] = Field(None, max_length=500, description="案例描述")
    case_type: str = Field(..., description="案例类型")
    status: Optional[str] = Field(None, description="状态")
    priority: Optional[int] = Field(0, ge=0, le=5, description="优先级")
    customer_id: int = Field(..., description="客户ID")
    user_id: Optional[int] = Field(None, description="分配的用户ID")
    tags: Optional[List[str]] = Field(None, description="标签列表")

class CaseUpdate(BaseModel):
    """案例更新模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=100, description="案例标题")
    description: Optional[str] = Field(None, max_length=500, description="案例描述")
    case_type: Optional[str] = Field(None, description="案例类型")
    status: Optional[str] = Field(None, description="状态")
    priority: Optional[int] = Field(None, ge=0, le=5, description="优先级")
    user_id: Optional[int] = Field(None, description="分配的用户ID")
    tags: Optional[List[str]] = Field(None, description="标签列表")

class CaseComplete(BaseModel):
    """案例完成模型"""
    satisfaction_score: Optional[int] = Field(None, ge=1, le=5, description="满意度评分")
    feedback: Optional[str] = Field(None, max_length=500, description="客户反馈")

class CaseDocumentCreate(BaseModel):
    """案例文档创建模型"""
    document_name: str = Field(..., min_length=1, max_length=100, description="文档名称")
    document_path: str = Field(..., min_length=1, description="文档路径")
    document_type: Optional[str] = Field(None, description="文档类型")
    description: Optional[str] = Field(None, max_length=300, description="文档描述")
    uploaded_by: Optional[int] = Field(None, description="上传者ID")

class CaseProgressUpdate(BaseModel):
    """案例进度更新模型"""
    stage: str = Field(..., min_length=1, max_length=50, description="阶段")
    status: str = Field(..., regex=r"^(in_progress|completed|failed)$", description="状态")
    description: Optional[str] = Field(None, max_length=300, description="描述")

class CaseResponse(BaseModel):
    """案例响应模型"""
    id: int
    case_id: str
    title: str
    description: Optional[str]
    case_type: str
    status: str
    priority: int
    customer_id: int
    user_id: Optional[int]
    satisfaction_score: Optional[int]
    feedback: Optional[str]
    created_at: str
    updated_at: str
    end_date: Optional[str]
    tags: List[str]

    class Config:
        from_attributes = True

class CaseDocumentResponse(BaseModel):
    """案例文档响应模型"""
    id: int
    case_id: int
    document_name: str
    document_path: str
    document_type: Optional[str]
    description: Optional[str]
    uploaded_by: Optional[int]
    created_at: str

    class Config:
        from_attributes = True

class CaseProgressResponse(BaseModel):
    """案例进度响应模型"""
    id: int
    case_id: int
    stage: str
    status: str
    description: Optional[str]
    created_at: str
    completed_at: Optional[str]

    class Config:
        from_attributes = True

@router.post("/", response_model=CaseResponse)
def create_case(case: CaseCreate):
    """创建案例"""
    try:
        case_data = case.model_dump()
        created_case = case_manager.create_case(case_data)
        
        # 获取标签
        tags = []
        if hasattr(created_case, 'tags'):
            tags = [tag.tag_name for tag in created_case.tags]
        
        return CaseResponse(
            id=created_case.id,
            case_id=created_case.case_id,
            title=created_case.title,
            description=created_case.description,
            case_type=created_case.case_type,
            status=created_case.status,
            priority=created_case.priority,
            customer_id=created_case.customer_id,
            user_id=created_case.user_id,
            satisfaction_score=created_case.satisfaction_score,
            feedback=created_case.feedback,
            created_at=created_case.created_at.isoformat(),
            updated_at=created_case.updated_at.isoformat(),
            end_date=created_case.end_date.isoformat() if created_case.end_date else None,
            tags=tags
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建案例失败: {str(e)}")

@router.get("/", response_model=List[CaseResponse])
def list_cases(
    status: Optional[str] = Query(None, description="状态"),
    case_type: Optional[str] = Query(None, description="案例类型"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    priority: Optional[int] = Query(None, ge=0, le=5, description="优先级")
):
    """列出案例"""
    try:
        filters = {}
        if status:
            filters["status"] = status
        if case_type:
            filters["case_type"] = case_type
        if customer_id:
            filters["customer_id"] = customer_id
        if user_id:
            filters["user_id"] = user_id
        if priority is not None:
            filters["priority"] = priority
        
        cases = case_manager.list_cases(**filters)
        result = []
        for case in cases:
            # 获取标签
            tags = []
            if hasattr(case, 'tags'):
                tags = [tag.tag_name for tag in case.tags]
            
            result.append(CaseResponse(
                id=case.id,
                case_id=case.case_id,
                title=case.title,
                description=case.description,
                case_type=case.case_type,
                status=case.status,
                priority=case.priority,
                customer_id=case.customer_id,
                user_id=case.user_id,
                satisfaction_score=case.satisfaction_score,
                feedback=case.feedback,
                created_at=case.created_at.isoformat(),
                updated_at=case.updated_at.isoformat(),
                end_date=case.end_date.isoformat() if case.end_date else None,
                tags=tags
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取案例列表失败: {str(e)}")

@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: int):
    """获取案例详情"""
    try:
        case = case_manager.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="案例不存在")
        
        # 获取标签
        tags = []
        if hasattr(case, 'tags'):
            tags = [tag.tag_name for tag in case.tags]
        
        return CaseResponse(
            id=case.id,
            case_id=case.case_id,
            title=case.title,
            description=case.description,
            case_type=case.case_type,
            status=case.status,
            priority=case.priority,
            customer_id=case.customer_id,
            user_id=case.user_id,
            satisfaction_score=case.satisfaction_score,
            feedback=case.feedback,
            created_at=case.created_at.isoformat(),
            updated_at=case.updated_at.isoformat(),
            end_date=case.end_date.isoformat() if case.end_date else None,
            tags=tags
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取案例详情失败: {str(e)}")

@router.put("/{case_id}", response_model=CaseResponse)
def update_case(case_id: int, case: CaseUpdate):
    """更新案例信息"""
    try:
        update_data = case.model_dump(exclude_unset=True)
        updated_case = case_manager.update_case(case_id, update_data)
        
        # 获取标签
        tags = []
        if hasattr(updated_case, 'tags'):
            tags = [tag.tag_name for tag in updated_case.tags]
        
        return CaseResponse(
            id=updated_case.id,
            case_id=updated_case.case_id,
            title=updated_case.title,
            description=updated_case.description,
            case_type=updated_case.case_type,
            status=updated_case.status,
            priority=updated_case.priority,
            customer_id=updated_case.customer_id,
            user_id=updated_case.user_id,
            satisfaction_score=updated_case.satisfaction_score,
            feedback=updated_case.feedback,
            created_at=updated_case.created_at.isoformat(),
            updated_at=updated_case.updated_at.isoformat(),
            end_date=updated_case.end_date.isoformat() if updated_case.end_date else None,
            tags=tags
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新案例信息失败: {str(e)}")

@router.delete("/{case_id}")
def delete_case(case_id: int):
    """删除案例"""
    try:
        case_manager.delete_case(case_id)
        return {"message": "案例删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除案例失败: {str(e)}")

@router.post("/{case_id}/assign/{user_id}", response_model=CaseResponse)
def assign_case(case_id: int, user_id: int):
    """分配案例"""
    try:
        assigned_case = case_manager.assign_case(case_id, user_id)
        
        # 获取标签
        tags = []
        if hasattr(assigned_case, 'tags'):
            tags = [tag.tag_name for tag in assigned_case.tags]
        
        return CaseResponse(
            id=assigned_case.id,
            case_id=assigned_case.case_id,
            title=assigned_case.title,
            description=assigned_case.description,
            case_type=assigned_case.case_type,
            status=assigned_case.status,
            priority=assigned_case.priority,
            customer_id=assigned_case.customer_id,
            user_id=assigned_case.user_id,
            satisfaction_score=assigned_case.satisfaction_score,
            feedback=assigned_case.feedback,
            created_at=assigned_case.created_at.isoformat(),
            updated_at=assigned_case.updated_at.isoformat(),
            end_date=assigned_case.end_date.isoformat() if assigned_case.end_date else None,
            tags=tags
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分配案例失败: {str(e)}")

@router.post("/{case_id}/complete", response_model=CaseResponse)
def complete_case(case_id: int, completion: CaseComplete):
    """完成案例"""
    try:
        completed_case = case_manager.complete_case(
            case_id,
            completion.satisfaction_score,
            completion.feedback
        )
        
        # 获取标签
        tags = []
        if hasattr(completed_case, 'tags'):
            tags = [tag.tag_name for tag in completed_case.tags]
        
        return CaseResponse(
            id=completed_case.id,
            case_id=completed_case.case_id,
            title=completed_case.title,
            description=completed_case.description,
            case_type=completed_case.case_type,
            status=completed_case.status,
            priority=completed_case.priority,
            customer_id=completed_case.customer_id,
            user_id=completed_case.user_id,
            satisfaction_score=completed_case.satisfaction_score,
            feedback=completed_case.feedback,
            created_at=completed_case.created_at.isoformat(),
            updated_at=completed_case.updated_at.isoformat(),
            end_date=completed_case.end_date.isoformat() if completed_case.end_date else None,
            tags=tags
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"完成案例失败: {str(e)}")

@router.post("/{case_id}/documents", response_model=CaseDocumentResponse)
def add_case_document(case_id: int, document: CaseDocumentCreate):
    """添加案例文档"""
    try:
        document_data = document.model_dump()
        created_document = case_manager.add_case_document(case_id, document_data)
        return CaseDocumentResponse(
            id=created_document.id,
            case_id=created_document.case_id,
            document_name=created_document.document_name,
            document_path=created_document.document_path,
            document_type=created_document.document_type,
            description=created_document.description,
            uploaded_by=created_document.uploaded_by,
            created_at=created_document.created_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加案例文档失败: {str(e)}")

@router.post("/{case_id}/progress", response_model=CaseProgressResponse)
def update_case_progress(case_id: int, progress: CaseProgressUpdate):
    """更新案例进度"""
    try:
        updated_progress = case_manager.update_case_progress(
            case_id,
            progress.stage,
            progress.status,
            progress.description
        )
        return CaseProgressResponse(
            id=updated_progress.id,
            case_id=updated_progress.case_id,
            stage=updated_progress.stage,
            status=updated_progress.status,
            description=updated_progress.description,
            created_at=updated_progress.created_at.isoformat(),
            completed_at=updated_progress.completed_at.isoformat() if updated_progress.completed_at else None
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新案例进度失败: {str(e)}")

@router.get("/search/{keyword}", response_model=List[CaseResponse])
def search_cases(keyword: str):
    """搜索案例"""
    try:
        cases = case_manager.search_cases(keyword)
        result = []
        for case in cases:
            # 获取标签
            tags = []
            if hasattr(case, 'tags'):
                tags = [tag.tag_name for tag in case.tags]
            
            result.append(CaseResponse(
                id=case.id,
                case_id=case.case_id,
                title=case.title,
                description=case.description,
                case_type=case.case_type,
                status=case.status,
                priority=case.priority,
                customer_id=case.customer_id,
                user_id=case.user_id,
                satisfaction_score=case.satisfaction_score,
                feedback=case.feedback,
                created_at=case.created_at.isoformat(),
                updated_at=case.updated_at.isoformat(),
                end_date=case.end_date.isoformat() if case.end_date else None,
                tags=tags
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索案例失败: {str(e)}")

@router.get("/{case_id}/recommend", response_model=List[CaseResponse])
def recommend_cases(case_id: int, limit: int = Query(5, ge=1, le=20, description="推荐数量")):
    """推荐相似案例"""
    try:
        cases = case_manager.recommend_cases(case_id, limit)
        result = []
        for case in cases:
            # 获取标签
            tags = []
            if hasattr(case, 'tags'):
                tags = [tag.tag_name for tag in case.tags]
            
            result.append(CaseResponse(
                id=case.id,
                case_id=case.case_id,
                title=case.title,
                description=case.description,
                case_type=case.case_type,
                status=case.status,
                priority=case.priority,
                customer_id=case.customer_id,
                user_id=case.user_id,
                satisfaction_score=case.satisfaction_score,
                feedback=case.feedback,
                created_at=case.created_at.isoformat(),
                updated_at=case.updated_at.isoformat(),
                end_date=case.end_date.isoformat() if case.end_date else None,
                tags=tags
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推荐案例失败: {str(e)}")

@router.get("/stats/pending", response_model=List[CaseResponse])
def get_pending_cases():
    """获取待处理的案例"""
    try:
        cases = case_manager.get_pending_cases()
        result = []
        for case in cases:
            # 获取标签
            tags = []
            if hasattr(case, 'tags'):
                tags = [tag.tag_name for tag in case.tags]
            
            result.append(CaseResponse(
                id=case.id,
                case_id=case.case_id,
                title=case.title,
                description=case.description,
                case_type=case.case_type,
                status=case.status,
                priority=case.priority,
                customer_id=case.customer_id,
                user_id=case.user_id,
                satisfaction_score=case.satisfaction_score,
                feedback=case.feedback,
                created_at=case.created_at.isoformat(),
                updated_at=case.updated_at.isoformat(),
                end_date=case.end_date.isoformat() if case.end_date else None,
                tags=tags
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取待处理案例失败: {str(e)}")

@router.get("/stats/processing", response_model=List[CaseResponse])
def get_processing_cases():
    """获取处理中的案例"""
    try:
        cases = case_manager.get_processing_cases()
        result = []
        for case in cases:
            # 获取标签
            tags = []
            if hasattr(case, 'tags'):
                tags = [tag.tag_name for tag in case.tags]
            
            result.append(CaseResponse(
                id=case.id,
                case_id=case.case_id,
                title=case.title,
                description=case.description,
                case_type=case.case_type,
                status=case.status,
                priority=case.priority,
                customer_id=case.customer_id,
                user_id=case.user_id,
                satisfaction_score=case.satisfaction_score,
                feedback=case.feedback,
                created_at=case.created_at.isoformat(),
                updated_at=case.updated_at.isoformat(),
                end_date=case.end_date.isoformat() if case.end_date else None,
                tags=tags
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取处理中案例失败: {str(e)}")

@router.get("/stats/completed", response_model=List[CaseResponse])
def get_completed_cases():
    """获取已完成的案例"""
    try:
        cases = case_manager.get_completed_cases()
        result = []
        for case in cases:
            # 获取标签
            tags = []
            if hasattr(case, 'tags'):
                tags = [tag.tag_name for tag in case.tags]
            
            result.append(CaseResponse(
                id=case.id,
                case_id=case.case_id,
                title=case.title,
                description=case.description,
                case_type=case.case_type,
                status=case.status,
                priority=case.priority,
                customer_id=case.customer_id,
                user_id=case.user_id,
                satisfaction_score=case.satisfaction_score,
                feedback=case.feedback,
                created_at=case.created_at.isoformat(),
                updated_at=case.updated_at.isoformat(),
                end_date=case.end_date.isoformat() if case.end_date else None,
                tags=tags
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取已完成案例失败: {str(e)}")
