from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from utils.database import get_db
from modules.message.wecom_handler import wecom_handler
from modules.message.models import Message as MessageModel
from modules.customer.models import Customer

router = APIRouter()

@router.post("/send")
async def send_message(user_id: str, message: str):
    """发送企业微信消息"""
    try:
        result = wecom_handler.send_message(user_id, message)
        if result:
            return {"success": True, "message": "消息发送成功"}
        else:
            raise HTTPException(status_code=500, detail="消息发送失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送消息时出错: {str(e)}")

@router.post("/receive")
async def receive_message(data: Dict[str, Any]):
    """接收企业微信消息"""
    try:
        result = wecom_handler.receive_message(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"接收消息时出错: {str(e)}")

@router.get("/history/{customer_id}")
async def get_message_history(customer_id: int, db: Session = Depends(get_db)):
    """获取客户消息历史"""
    try:
        messages = db.query(MessageModel).filter(MessageModel.customer_id == customer_id).order_by(MessageModel.created_at.desc()).all()
        return {
            "success": True,
            "messages": [
                {
                    "id": msg.id,
                    "message_id": msg.message_id,
                    "type": msg.type,
                    "content": msg.content,
                    "priority": msg.priority,
                    "status": msg.status,
                    "created_at": msg.created_at,
                    "processed_at": msg.processed_at
                }
                for msg in messages
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取消息历史时出错: {str(e)}")

@router.get("/user/{user_id}")
async def get_user_info(user_id: str):
    """获取用户信息"""
    try:
        user_info = wecom_handler.get_user_info(user_id)
        return {"success": True, "user_info": user_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户信息时出错: {str(e)}")

@router.post("/menu")
async def create_menu(menu_data: Dict[str, Any]):
    """创建企业微信菜单"""
    try:
        result = wecom_handler.create_menu(menu_data)
        if result:
            return {"success": True, "message": "菜单创建成功"}
        else:
            raise HTTPException(status_code=500, detail="菜单创建失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建菜单时出错: {str(e)}")
