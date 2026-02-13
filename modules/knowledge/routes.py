from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from utils.database import get_db
from modules.knowledge.models import KnowledgeBase
from modules.knowledge.knowledge_manager import knowledge_manager
from modules.knowledge.search_engine import search_engine

router = APIRouter()

@router.post("/create", summary="创建知识库条目", description="创建新的知识库条目，用于存储法律相关的知识内容")
async def create_knowledge(
    title: str = Query(..., description="知识库条目标题"),
    content: str = Query(..., description="知识库条目内容"),
    category: str = Query(..., description="知识库条目分类"),
    subcategory: str = Query(None, description="知识库条目子分类"),
    keywords: str = Query(None, description="知识库条目关键词，多个关键词用逗号分隔"),
    db: Session = Depends(get_db)
):
    """
    创建知识库条目
    
    Args:
        title: 知识库条目标题
        content: 知识库条目内容
        category: 知识库条目分类
        subcategory: 知识库条目子分类
        keywords: 知识库条目关键词，多个关键词用逗号分隔
        db: 数据库会话
    
    Returns:
        创建结果，包含success和knowledge_id
    
    Example:
        请求:
        POST /api/knowledge/create
        {
            "title": "劳动合同法基本条款",
            "content": "劳动合同法是调整劳动关系的基本法律...",
            "category": "劳动法",
            "subcategory": "劳动合同",
            "keywords": "劳动合同,劳动法,劳动关系"
        }
        
        响应:
        {
            "success": true,
            "knowledge_id": 1
        }
    """
    try:
        knowledge = knowledge_manager.create_knowledge(
            title=title,
            content=content,
            category=category,
            subcategory=subcategory,
            keywords=keywords
        )
        return {"success": True, "knowledge_id": knowledge.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建知识库条目时出错: {str(e)}")

@router.get("/get/{knowledge_id}", summary="获取知识库条目", description="根据ID获取知识库条目的详细信息")
async def get_knowledge(knowledge_id: int, db: Session = Depends(get_db)):
    """
    获取知识库条目
    
    Args:
        knowledge_id: 知识库条目ID
        db: 数据库会话
    
    Returns:
        知识库条目详细信息
    
    Example:
        请求:
        GET /api/knowledge/get/1
        
        响应:
        {
            "success": true,
            "knowledge": {
                "id": 1,
                "title": "劳动合同法基本条款",
                "content": "劳动合同法是调整劳动关系的基本法律...",
                "category": "劳动法",
                "subcategory": "劳动合同",
                "keywords": "劳动合同,劳动法,劳动关系",
                "status": "active",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
    """
    try:
        knowledge = knowledge_manager.get_knowledge(knowledge_id)
        if knowledge:
            return {
                "success": True,
                "knowledge": {
                    "id": knowledge.id,
                    "title": knowledge.title,
                    "content": knowledge.content,
                    "category": knowledge.category,
                    "subcategory": knowledge.subcategory,
                    "keywords": knowledge.keywords,
                    "status": knowledge.status,
                    "created_at": knowledge.created_at,
                    "updated_at": knowledge.updated_at
                }
            }
        else:
            raise HTTPException(status_code=404, detail="知识库条目不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识库条目时出错: {str(e)}")

@router.put("/update/{knowledge_id}", summary="更新知识库条目", description="更新现有知识库条目的信息")
async def update_knowledge(
    knowledge_id: int,
    title: str = Query(None, description="知识库条目标题"),
    content: str = Query(None, description="知识库条目内容"),
    category: str = Query(None, description="知识库条目分类"),
    subcategory: str = Query(None, description="知识库条目子分类"),
    keywords: str = Query(None, description="知识库条目关键词，多个关键词用逗号分隔"),
    status: str = Query(None, description="知识库条目状态"),
    db: Session = Depends(get_db)
):
    """
    更新知识库条目
    
    Args:
        knowledge_id: 知识库条目ID
        title: 知识库条目标题
        content: 知识库条目内容
        category: 知识库条目分类
        subcategory: 知识库条目子分类
        keywords: 知识库条目关键词，多个关键词用逗号分隔
        status: 知识库条目状态
        db: 数据库会话
    
    Returns:
        更新结果
    
    Example:
        请求:
        PUT /api/knowledge/update/1
        {
            "title": "劳动合同法基本条款（修订版）",
            "content": "劳动合同法是调整劳动关系的基本法律...",
            "status": "active"
        }
        
        响应:
        {
            "success": true,
            "message": "知识库条目更新成功"
        }
    """
    try:
        updated = knowledge_manager.update_knowledge(
            knowledge_id=knowledge_id,
            title=title,
            content=content,
            category=category,
            subcategory=subcategory,
            keywords=keywords,
            status=status
        )
        if updated:
            return {"success": True, "message": "知识库条目更新成功"}
        else:
            raise HTTPException(status_code=404, detail="知识库条目不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新知识库条目时出错: {str(e)}")

@router.delete("/delete/{knowledge_id}", summary="删除知识库条目", description="根据ID删除知识库条目")
async def delete_knowledge(knowledge_id: int, db: Session = Depends(get_db)):
    """
    删除知识库条目
    
    Args:
        knowledge_id: 知识库条目ID
        db: 数据库会话
    
    Returns:
        删除结果
    
    Example:
        请求:
        DELETE /api/knowledge/delete/1
        
        响应:
        {
            "success": true,
            "message": "知识库条目删除成功"
        }
    """
    try:
        deleted = knowledge_manager.delete_knowledge(knowledge_id)
        if deleted:
            return {"success": True, "message": "知识库条目删除成功"}
        else:
            raise HTTPException(status_code=404, detail="知识库条目不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除知识库条目时出错: {str(e)}")

@router.get("/list", summary="获取知识库列表", description="获取知识库条目列表，支持分页和筛选")
async def list_knowledge(
    category: str = Query(None, description="知识库条目分类"),
    status: str = Query("active", description="知识库条目状态"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页大小"),
    db: Session = Depends(get_db)
):
    """
    获取知识库列表
    
    Args:
        category: 知识库条目分类
        status: 知识库条目状态
        page: 页码
        page_size: 每页大小
        db: 数据库会话
    
    Returns:
        知识库条目列表
    
    Example:
        请求:
        GET /api/knowledge/list?category=劳动法&page=1&page_size=10
        
        响应:
        {
            "success": true,
            "knowledges": [
                {
                    "id": 1,
                    "title": "劳动合同法基本条款",
                    "category": "劳动法",
                    "subcategory": "劳动合同",
                    "status": "active",
                    "created_at": "2024-01-01T00:00:00"
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 10
        }
    """
    try:
        knowledges = knowledge_manager.list_knowledge(
            category=category,
            status=status,
            page=page,
            page_size=page_size
        )
        total = knowledge_manager.count_knowledge(category=category, status=status)
        
        return {
            "success": True,
            "knowledges": [
                {
                    "id": k.id,
                    "title": k.title,
                    "category": k.category,
                    "subcategory": k.subcategory,
                    "status": k.status,
                    "created_at": k.created_at
                }
                for k in knowledges
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识库列表时出错: {str(e)}")

@router.get("/search", summary="搜索知识库", description="根据关键词搜索知识库条目")
async def search_knowledge(
    query: str = Query(..., description="搜索关键词"),
    top_k: int = Query(5, description="返回结果数量"),
    category: str = Query(None, description="知识库条目分类")
):
    """
    搜索知识库
    
    Args:
        query: 搜索关键词
        top_k: 返回结果数量
        category: 知识库条目分类
    
    Returns:
        搜索结果
    
    Example:
        请求:
        GET /api/knowledge/search?query=劳动合同&top_k=5
        
        响应:
        {
            "success": true,
            "results": [
                {
                    "id": 1,
                    "title": "劳动合同法基本条款",
                    "content": "劳动合同法是调整劳动关系的基本法律...",
                    "category": "劳动法",
                    "score": 0.95
                }
            ]
        }
    """
    try:
        results = search_engine.search(query, top_k=top_k, category=category)
        return {"success": True, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索知识库时出错: {str(e)}")

@router.post("/batch/create", summary="批量创建知识库条目", description="批量创建多个知识库条目")
async def batch_create_knowledge(
    knowledges: List[Dict[str, Any]] = Query(..., description="知识库条目列表"),
    db: Session = Depends(get_db)
):
    """
    批量创建知识库条目
    
    Args:
        knowledges: 知识库条目列表
        db: 数据库会话
    
    Returns:
        创建结果
    
    Example:
        请求:
        POST /api/knowledge/batch/create
        {
            "knowledges": [
                {
                    "title": "劳动合同法基本条款",
                    "content": "劳动合同法是调整劳动关系的基本法律...",
                    "category": "劳动法",
                    "subcategory": "劳动合同",
                    "keywords": "劳动合同,劳动法,劳动关系"
                },
                {
                    "title": "合同法基本原理",
                    "content": "合同法是调整平等主体之间合同关系的法律...",
                    "category": "合同法",
                    "subcategory": "合同原理",
                    "keywords": "合同法,合同原理"
                }
            ]
        }
        
        响应:
        {
            "success": true,
            "created_count": 2
        }
    """
    try:
        created_count = knowledge_manager.batch_create_knowledge(knowledges)
        return {"success": True, "created_count": created_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量创建知识库条目时出错: {str(e)}")

@router.post("/import", summary="从文件导入知识库", description="从指定文件URL导入知识库条目")
async def import_knowledge(
    file_url: str = Query(..., description="文件URL"),
    category: str = Query(..., description="知识库条目分类"),
    db: Session = Depends(get_db)
):
    """
    从文件导入知识库
    
    Args:
        file_url: 文件URL
        category: 知识库条目分类
        db: 数据库会话
    
    Returns:
        导入结果
    
    Example:
        请求:
        POST /api/knowledge/import
        {
            "file_url": "https://example.com/knowledge.json",
            "category": "劳动法"
        }
        
        响应:
        {
            "success": true,
            "imported_count": 10
        }
    """
    try:
        imported_count = knowledge_manager.import_knowledge(file_url, category)
        return {"success": True, "imported_count": imported_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入知识库时出错: {str(e)}")
