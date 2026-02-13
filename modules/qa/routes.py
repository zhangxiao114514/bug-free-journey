from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any
from sqlalchemy.orm import Session

from utils.database import get_db
from modules.qa.qa_manager import qa_manager
from modules.qa.intent_classifier import intent_classifier

router = APIRouter()

@router.post("/answer", summary="回答用户问题", description="根据用户问题和客户ID生成回答")
async def answer_question(
    customer_id: int = Query(..., description="客户ID"),
    query: str = Query(..., description="用户问题")
):
    """
    回答用户问题
    
    Args:
        customer_id: 客户ID
        query: 用户问题
    
    Returns:
        回答结果
    
    Example:
        请求:
        POST /api/qa/answer
        {
            "customer_id": 1,
            "query": "什么是劳动合同法？"
        }
        
        响应:
        {
            "success": true,
            "answer": "劳动合同法是调整劳动关系的基本法律...",
            "confidence": 0.95,
            "intent": "labor_dispute"
        }
    """
    try:
        result = qa_manager.answer(customer_id, query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回答问题时出错: {str(e)}")

@router.post("/classify", summary="意图识别", description="识别用户问题的意图")
async def classify_intent(query: str = Query(..., description="用户问题")):
    """
    意图识别
    
    Args:
        query: 用户问题
    
    Returns:
        意图识别结果
    
    Example:
        请求:
        POST /api/qa/classify
        {
            "query": "什么是劳动合同法？"
        }
        
        响应:
        {
            "success": true,
            "intent": {
                "intent": "labor_dispute",
                "confidence": 0.95
            }
        }
    """
    try:
        result = intent_classifier.classify(query)
        return {"success": True, "intent": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"意图识别时出错: {str(e)}")

@router.post("/dialogue/clear", summary="清除对话历史", description="清除指定客户的对话历史")
async def clear_dialogue(customer_id: int = Query(..., description="客户ID")):
    """
    清除对话历史
    
    Args:
        customer_id: 客户ID
    
    Returns:
        清除结果
    
    Example:
        请求:
        POST /api/qa/dialogue/clear
        {
            "customer_id": 1
        }
        
        响应:
        {
            "success": true,
            "message": "对话历史已清除"
        }
    """
    try:
        qa_manager.clear_dialogue(customer_id)
        return {"success": True, "message": "对话历史已清除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除对话历史时出错: {str(e)}")

@router.post("/dialogue/cleanup", summary="清理过期对话", description="清理所有过期的对话历史")
async def cleanup_dialogues():
    """
    清理过期对话
    
    Returns:
        清理结果
    
    Example:
        请求:
        POST /api/qa/dialogue/cleanup
        
        响应:
        {
            "success": true,
            "message": "过期对话已清理"
        }
    """
    try:
        qa_manager.cleanup_expired_dialogues()
        return {"success": True, "message": "过期对话已清理"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理过期对话时出错: {str(e)}")

@router.get("/status", summary="获取问答系统状态", description="获取问答系统的当前状态")
async def get_qa_status():
    """
    获取问答系统状态
    
    Returns:
        问答系统状态
    
    Example:
        请求:
        GET /api/qa/status
        
        响应:
        {
            "success": true,
            "status": "running",
            "intent_classifier": "loaded",
            "knowledge_base": "available"
        }
    """
    try:
        # 这里可以添加获取问答系统状态的逻辑
        return {
            "success": True,
            "status": "running",
            "intent_classifier": "loaded",
            "knowledge_base": "available"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取问答系统状态时出错: {str(e)}")

@router.post("/feedback", summary="提交问答反馈", description="提交用户对问答结果的反馈")
async def submit_feedback(
    customer_id: int = Query(..., description="客户ID"),
    question: str = Query(..., description="用户问题"),
    answer: str = Query(..., description="系统回答"),
    rating: int = Query(..., description="评分，范围1-5"),
    feedback: str = Query(None, description="详细反馈")
):
    """
    提交问答反馈
    
    Args:
        customer_id: 客户ID
        question: 用户问题
        answer: 系统回答
        rating: 评分，范围1-5
        feedback: 详细反馈
    
    Returns:
        反馈提交结果
    
    Example:
        请求:
        POST /api/qa/feedback
        {
            "customer_id": 1,
            "question": "什么是劳动合同法？",
            "answer": "劳动合同法是调整劳动关系的基本法律...",
            "rating": 5,
            "feedback": "回答很详细，对我很有帮助"
        }
        
        响应:
        {
            "success": true,
            "message": "反馈提交成功"
        }
    """
    try:
        # 这里可以添加处理反馈的逻辑
        # 例如保存反馈到数据库，用于后续优化
        return {"success": True, "message": "反馈提交成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交反馈时出错: {str(e)}")
