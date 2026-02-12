import logging
import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from utils.config import config_manager
from utils.database import get_db
from modules.customer.models import Customer
from modules.message.models import Message as MessageModel
from modules.qa.qa_manager import qa_manager

logger = logging.getLogger(__name__)

class WeComHandler:
    """企业微信处理器"""
    
    def __init__(self):
        self.access_token = None
        self.token_expiry = None
    
    def get_access_token(self) -> str:
        """获取企业微信访问令牌
        
        Returns:
            访问令牌
        """
        # 检查令牌是否有效
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token
        
        # 获取配置
        corp_id = config_manager.get('wecom', 'corp_id')
        app_secret = config_manager.get('wecom', 'app_secret')
        
        if not corp_id or not app_secret:
            raise ValueError("企业微信配置不完整")
        
        # 请求访问令牌
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corp_id}&corpsecret={app_secret}"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            if data.get('errcode') == 0:
                self.access_token = data['access_token']
                # 设置过期时间（提前5分钟）
                self.token_expiry = datetime.now() + timedelta(seconds=data['expires_in'] - 300)
                logger.info("获取企业微信访问令牌成功")
                return self.access_token
            else:
                logger.error(f"获取企业微信访问令牌失败: {data}")
                raise Exception(f"获取访问令牌失败: {data.get('errmsg')}")
                
        except Exception as e:
            logger.error(f"获取访问令牌时出错: {e}")
            raise
    
    def send_message(self, user_id: str, message: str) -> bool:
        """发送企业微信消息
        
        Args:
            user_id: 用户ID
            message: 消息内容
            
        Returns:
            是否发送成功
        """
        try:
            access_token = self.get_access_token()
            agent_id = config_manager.get('wecom', 'agent_id')
            
            url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
            
            # 构建消息体
            payload = {
                "touser": user_id,
                "msgtype": "text",
                "agentid": agent_id,
                "text": {
                    "content": message
                },
                "safe": 0
            }
            
            response = requests.post(url, json=payload)
            data = response.json()
            
            if data.get('errcode') == 0:
                logger.info(f"发送企业微信消息成功: {user_id}")
                return True
            else:
                logger.error(f"发送企业微信消息失败: {data}")
                return False
                
        except Exception as e:
            logger.error(f"发送企业微信消息时出错: {e}")
            return False
    
    def receive_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """接收企业微信消息
        
        Args:
            data: 消息数据
            
        Returns:
            处理结果
        """
        try:
            # 解析消息
            message_type = data.get('MsgType')
            user_id = data.get('FromUserName')
            content = data.get('Content')
            message_id = data.get('MsgId')
            
            logger.info(f"收到企业微信消息: 类型={message_type}, 用户={user_id}, 内容={content[:50]}...")
            
            # 只处理文本消息
            if message_type != 'text' or not content:
                logger.info(f"跳过非文本消息: {message_type}")
                return {
                    'success': True,
                    'message': '跳过非文本消息'
                }
            
            # 处理客户信息
            customer = self._get_or_create_customer(user_id, data)
            
            # 创建消息记录
            message_data = {
                'customer_id': customer.id,
                'message_id': message_id,
                'type': message_type,
                'content': content,
                'priority': self._calculate_priority(content)
            }
            
            # 保存消息
            self._save_message(message_data)
            
            # 智能问答
            answer_result = qa_manager.answer(customer.id, content)
            
            # 自动回复
            if answer_result['success']:
                reply_message = answer_result['answer']
                self.send_message(user_id, reply_message)
                logger.info(f"自动回复企业微信消息: 用户={user_id}, 内容={reply_message[:50]}...")
            else:
                logger.warning(f"未能生成回复: {answer_result.get('error')}")
            
            return {
                'success': True,
                'customer_id': customer.id,
                'message_id': message_id,
                'answer': answer_result.get('answer'),
                'escalate_to_human': answer_result.get('escalate_to_human', False)
            }
            
        except Exception as e:
            logger.error(f"处理企业微信消息时出错: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_or_create_customer(self, user_id: str, message_data: Dict[str, Any]) -> Customer:
        """获取或创建客户信息
        
        Args:
            user_id: 用户ID
            message_data: 消息数据
            
        Returns:
            客户对象
        """
        db = next(get_db())
        try:
            # 查询客户
            customer = db.query(Customer).filter(Customer.wechat_id == user_id).first()
            
            if not customer:
                # 创建新客户
                nickname = message_data.get('FromUserName', user_id)
                
                customer = Customer(
                    wechat_id=user_id,
                    nickname=nickname,
                    status="active"
                )
                db.add(customer)
                db.commit()
                db.refresh(customer)
                logger.info(f"创建企业微信客户: {nickname}")
            
            return customer
        finally:
            db.close()
    
    def _save_message(self, message_data: Dict[str, Any]):
        """保存消息记录
        
        Args:
            message_data: 消息数据
        """
        db = next(get_db())
        try:
            message = MessageModel(**message_data)
            message.status = "processed"
            message.processed_at = datetime.now()
            db.add(message)
            db.commit()
        finally:
            db.close()
    
    def _calculate_priority(self, content: str) -> int:
        """计算消息优先级
        
        Args:
            content: 消息内容
            
        Returns:
            优先级
        """
        priority = 0
        
        # 关键词匹配
        high_priority_words = ['紧急', '求助', '法律', '律师', '起诉', '赔偿']
        medium_priority_words = ['咨询', '了解', '请问', '想知道']
        
        if any(word in content for word in high_priority_words):
            priority = 2  # 高优先级
        elif any(word in content for word in medium_priority_words):
            priority = 1  # 中优先级
        
        return priority
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息
        """
        try:
            access_token = self.get_access_token()
            
            url = f"https://qyapi.weixin.qq.com/cgi-bin/user/get?access_token={access_token}&userid={user_id}"
            
            response = requests.get(url)
            data = response.json()
            
            if data.get('errcode') == 0:
                logger.info(f"获取用户信息成功: {user_id}")
                return data
            else:
                logger.error(f"获取用户信息失败: {data}")
                return {}
                
        except Exception as e:
            logger.error(f"获取用户信息时出错: {e}")
            return {}
    
    def create_menu(self, menu_data: Dict[str, Any]) -> bool:
        """创建企业微信菜单
        
        Args:
            menu_data: 菜单数据
            
        Returns:
            是否创建成功
        """
        try:
            access_token = self.get_access_token()
            agent_id = config_manager.get('wecom', 'agent_id')
            
            url = f"https://qyapi.weixin.qq.com/cgi-bin/menu/create?access_token={access_token}&agentid={agent_id}"
            
            response = requests.post(url, json=menu_data)
            data = response.json()
            
            if data.get('errcode') == 0:
                logger.info("创建企业微信菜单成功")
                return True
            else:
                logger.error(f"创建企业微信菜单失败: {data}")
                return False
                
        except Exception as e:
            logger.error(f"创建企业微信菜单时出错: {e}")
            return False

# 创建企业微信处理器实例
wecom_handler = WeComHandler()
