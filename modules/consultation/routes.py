# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, Field

from modules.consultation.consultation_manager import consultation_manager

router = APIRouter(
    prefix="/api/consultation",
    tags=["consultation"],
    responses={404: {"description": "Not found"}},
)

class ConsultationCreate(BaseModel):
    """咨询创建模型"""
    customer_id: int = Field(..., description="客户ID")
    user_id: Optional[int] = Field(None, description="分配的用户ID")
    title: str = Field(..., min_length=1, max_length=100, description="咨询标题")
    description: Optional[str] = Field(None, max_length=500, description="咨询描述")
    category: Optional[str] = Field(None, description="咨询类别")
    priority: Optional[int] = Field(0, ge=0, le=5, description="优先级")

class ConsultationUpdate(BaseModel):
    """咨询更新模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=100, description="咨询标题")
    description: Optional[str] = Field(None, max_length=500, description="咨询描述")
    category: Optional[str] = Field(None, description="咨询类别")
    priority: Optional[int] = Field(None, ge=0, le=5, description="优先级")
    status: Optional[str] = Field(None, regex=r"^(pending|processing|completed|canceled)$", description="状态")

class ConsultationProgressUpdate(BaseModel):
    """咨询进度更新模型"""
    stage: str = Field(..., min_length=1, max_length=50, description="阶段")
    status: str = Field(..., regex=r"^(in_progress|completed|failed)$", description="状态")
    description: Optional[str] = Field(None, max_length=300, description="描述")

class ConsultationComplete(BaseModel):
    """咨询完成模型"""
    satisfaction_score: Optional[int] = Field(None, ge=1, le=5, description="满意度评分")
    feedback: Optional[str] = Field(None, max_length=500, description="客户反馈")

class ConsultationResponse(BaseModel):
    """咨询响应模型"""
    id: int
    consultation_id: str
    customer_id: int
    user_id: Optional[int]
    title: str
    description: Optional[str]
    category: Optional[str]
    priority: int
    status: str
    satisfaction_score: Optional[int]
    feedback: Optional[str]
    created_at: str
    updated_at: str
    completed_at: Optional[str]

    class Config:
        from_attributes = True

class ConsultationProgressResponse(BaseModel):
    """咨询进度响应模型"""
    id: int
    consultation_id: int
    stage: str
    status: str
    description: Optional[str]
    created_at: str
    completed_at: Optional[str]

    class Config:
        from_attributes = True

class ConsultationStatsResponse(BaseModel):
    """咨询统计响应模型"""
    total_consultations: int
    pending_consultations: int
    processing_consultations: int
    completed_consultations: int
    average_response_time: float

@router.post("/", response_model=ConsultationResponse)
def create_consultation(consultation: ConsultationCreate):
    """创建咨询"""
    try:
        consultation_data = consultation.model_dump()
        created_consultation = consultation_manager.create_consultation(consultation_data)
        return ConsultationResponse(
            id=created_consultation.id,
            consultation_id=created_consultation.consultation_id,
            customer_id=created_consultation.customer_id,
            user_id=created_consultation.user_id,
            title=created_consultation.title,
            description=created_consultation.description,
            category=created_consultation.category,
            priority=created_consultation.priority,
            status=created_consultation.status,
            satisfaction_score=created_consultation.satisfaction_score,
            feedback=created_consultation.feedback,
            created_at=created_consultation.created_at.isoformat(),
            updated_at=created_consultation.updated_at.isoformat(),
            completed_at=created_consultation.completed_at.isoformat() if created_consultation.completed_at else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建咨询失败: {str(e)}")

@router.get("/", response_model=List[ConsultationResponse])
def list_consultations(
    status: Optional[str] = Query(None, regex=r"^(pending|processing|completed|canceled)$", description="状态"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    category: Optional[str] = Query(None, description="咨询类别"),
    priority: Optional[int] = Query(None, ge=0, le=5, description="优先级")
):
    """列出咨询"""
    try:
        filters = {}
        if status:
            filters["status"] = status
        if customer_id:
            filters["customer_id"] = customer_id
        if user_id:
            filters["user_id"] = user_id
        if category:
            filters["category"] = category
        if priority is not None:
            filters["priority"] = priority
        
        consultations = consultation_manager.list_consultations(**filters)
        result = []
        for consultation in consultations:
            result.append(ConsultationResponse(
                id=consultation.id,
                consultation_id=consultation.consultation_id,
                customer_id=consultation.customer_id,
                user_id=consultation.user_id,
                title=consultation.title,
                description=consultation.description,
                category=consultation.category,
                priority=consultation.priority,
                status=consultation.status,
                satisfaction_score=consultation.satisfaction_score,
                feedback=consultation.feedback,
                created_at=consultation.created_at.isoformat(),
                updated_at=consultation.updated_at.isoformat(),
                completed_at=consultation.completed_at.isoformat() if consultation.completed_at else None
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取咨询列表失败: {str(e)}")

@router.get("/{consultation_id}", response_model=ConsultationResponse)
def get_consultation(consultation_id: int):
    """获取咨询详情"""
    try:
        consultation = consultation_manager.get_consultation(consultation_id)
        if not consultation:
            raise HTTPException(status_code=404, detail="咨询不存在")
        return ConsultationResponse(
            id=consultation.id,
            consultation_id=consultation.consultation_id,
            customer_id=consultation.customer_id,
            user_id=consultation.user_id,
            title=consultation.title,
            description=consultation.description,
            category=consultation.category,
            priority=consultation.priority,
            status=consultation.status,
            satisfaction_score=consultation.satisfaction_score,
            feedback=consultation.feedback,
            created_at=consultation.created_at.isoformat(),
            updated_at=consultation.updated_at.isoformat(),
            completed_at=consultation.completed_at.isoformat() if consultation.completed_at else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取咨询详情失败: {str(e)}")

@router.put("/{consultation_id}", response_model=ConsultationResponse)
def update_consultation(consultation_id: int, consultation: ConsultationUpdate):
    """更新咨询信息"""
    try:
        update_data = consultation.model_dump(exclude_unset=True)
        updated_consultation = consultation_manager.update_consultation(consultation_id, update_data)
        return ConsultationResponse(
            id=updated_consultation.id,
            consultation_id=updated_consultation.consultation_id,
            customer_id=updated_consultation.customer_id,
            user_id=updated_consultation.user_id,
            title=updated_consultation.title,
            description=updated_consultation.description,
            category=updated_consultation.category,
            priority=updated_consultation.priority,
            status=updated_consultation.status,
            satisfaction_score=updated_consultation.satisfaction_score,
            feedback=updated_consultation.feedback,
            created_at=updated_consultation.created_at.isoformat(),
            updated_at=updated_consultation.updated_at.isoformat(),
            completed_at=updated_consultation.completed_at.isoformat() if updated_consultation.completed_at else None
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新咨询信息失败: {str(e)}")

@router.post("/{consultation_id}/assign/{user_id}", response_model=ConsultationResponse)
def assign_consultation(consultation_id: int, user_id: int):
    """分配咨询"""
    try:
        assigned_consultation = consultation_manager.assign_consultation(consultation_id, user_id)
        return ConsultationResponse(
            id=assigned_consultation.id,
            consultation_id=assigned_consultation.consultation_id,
            customer_id=assigned_consultation.customer_id,
            user_id=assigned_consultation.user_id,
            title=assigned_consultation.title,
            description=assigned_consultation.description,
            category=assigned_consultation.category,
            priority=assigned_consultation.priority,
            status=assigned_consultation.status,
            satisfaction_score=assigned_consultation.satisfaction_score,
            feedback=assigned_consultation.feedback,
            created_at=assigned_consultation.created_at.isoformat(),
            updated_at=assigned_consultation.updated_at.isoformat(),
            completed_at=assigned_consultation.completed_at.isoformat() if assigned_consultation.completed_at else None
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分配咨询失败: {str(e)}")

@router.post("/{consultation_id}/progress", response_model=ConsultationProgressResponse)
def update_progress(consultation_id: int, progress: ConsultationProgressUpdate):
    """更新咨询进度"""
    try:
        updated_progress = consultation_manager.update_progress(
            consultation_id,
            progress.stage,
            progress.status,
            progress.description
        )
        return ConsultationProgressResponse(
            id=updated_progress.id,
            consultation_id=updated_progress.consultation_id,
            stage=updated_progress.stage,
            status=updated_progress.status,
            description=updated_progress.description,
            created_at=updated_progress.created_at.isoformat(),
            completed_at=updated_progress.completed_at.isoformat() if updated_progress.completed_at else None
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新咨询进度失败: {str(e)}")

@router.get("/{consultation_id}/progress", response_model=List[ConsultationProgressResponse])
def get_consultation_progress(consultation_id: int):
    """获取咨询进度"""
    try:
        progresses = consultation_manager.get_consultation_progress(consultation_id)
        result = []
        for progress in progresses:
            result.append(ConsultationProgressResponse(
                id=progress.id,
                consultation_id=progress.consultation_id,
                stage=progress.stage,
                status=progress.status,
                description=progress.description,
                created_at=progress.created_at.isoformat(),
                completed_at=progress.completed_at.isoformat() if progress.completed_at else None
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取咨询进度失败: {str(e)}")

@router.post("/{consultation_id}/escalate")
def escalate_consultation(consultation_id: int, reason: str = Query(..., min_length=1, max_length=200, description="升级原因")):
    """升级到人工客服"""
    try:
        consultation_manager.escalate_to_human(consultation_id, reason)
        return {"message": "咨询已升级到人工客服"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"升级咨询失败: {str(e)}")

@router.post("/{consultation_id}/complete", response_model=ConsultationResponse)
def complete_consultation(consultation_id: int, completion: ConsultationComplete):
    """完成咨询"""
    try:
        completed_consultation = consultation_manager.complete_consultation(
            consultation_id,
            completion.satisfaction_score,
            completion.feedback
        )
        return ConsultationResponse(
            id=completed_consultation.id,
            consultation_id=completed_consultation.consultation_id,
            customer_id=completed_consultation.customer_id,
            user_id=completed_consultation.user_id,
            title=completed_consultation.title,
            description=completed_consultation.description,
            category=completed_consultation.category,
            priority=completed_consultation.priority,
            status=completed_consultation.status,
            satisfaction_score=completed_consultation.satisfaction_score,
            feedback=completed_consultation.feedback,
            created_at=completed_consultation.created_at.isoformat(),
            updated_at=completed_consultation.updated_at.isoformat(),
            completed_at=completed_consultation.completed_at.isoformat() if completed_consultation.completed_at else None
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"完成咨询失败: {str(e)}")

@router.get("/stats/summary", response_model=ConsultationStatsResponse)
def get_consultation_stats():
    """获取咨询统计信息"""
    try:
        # 获取各种状态的咨询数量
        total = len(consultation_manager.list_consultations())
        pending = len(consultation_manager.list_consultations(status="pending"))
        processing = len(consultation_manager.list_consultations(status="processing"))
        completed = len(consultation_manager.list_consultations(status="completed"))
        
        # 获取平均响应时间
        average_response_time = consultation_manager.calculate_average_response_time()
        
        return ConsultationStatsResponse(
            total_consultations=total,
            pending_consultations=pending,
            processing_consultations=processing,
            completed_consultations=completed,
            average_response_time=average_response_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取咨询统计信息失败: {str(e)}")

@router.get("/stats/pending", response_model=List[ConsultationResponse])
def get_pending_consultations():
    """获取待处理的咨询"""
    try:
        consultations = consultation_manager.get_pending_consultations()
        result = []
        for consultation in consultations:
            result.append(ConsultationResponse(
                id=consultation.id,
                consultation_id=consultation.consultation_id,
                customer_id=consultation.customer_id,
                user_id=consultation.user_id,
                title=consultation.title,
                description=consultation.description,
                category=consultation.category,
                priority=consultation.priority,
                status=consultation.status,
                satisfaction_score=consultation.satisfaction_score,
                feedback=consultation.feedback,
                created_at=consultation.created_at.isoformat(),
                updated_at=consultation.updated_at.isoformat(),
                completed_at=consultation.completed_at.isoformat() if consultation.completed_at else None
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取待处理咨询失败: {str(e)}")

@router.get("/stats/overdue", response_model=List[ConsultationResponse])
def get_overdue_consultations(max_wait_time: int = Query(300, ge=60, le=3600, description="最大等待时间（秒）")):
    """获取超时的咨询"""
    try:
        consultations = consultation_manager.get_overdue_consultations(max_wait_time)
        result = []
        for consultation in consultations:
            result.append(ConsultationResponse(
                id=consultation.id,
                consultation_id=consultation.consultation_id,
                customer_id=consultation.customer_id,
                user_id=consultation.user_id,
                title=consultation.title,
                description=consultation.description,
                category=consultation.category,
                priority=consultation.priority,
                status=consultation.status,
                satisfaction_score=consultation.satisfaction_score,
                feedback=consultation.feedback,
                created_at=consultation.created_at.isoformat(),
                updated_at=consultation.updated_at.isoformat(),
                completed_at=consultation.completed_at.isoformat() if consultation.completed_at else None
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取超时咨询失败: {str(e)}")
