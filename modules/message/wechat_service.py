import asyncio
import logging

from utils.config import config_manager
from modules.message.wecom_handler import wecom_handler

logger = logging.getLogger(__name__)

class MessageService:
    """消息服务类"""
    
    def __init__(self):
        self.is_running = False
        self.service_type = 'wecom'  # 固定为企业微信服务
    
    async def start(self):
        """启动消息服务"""
        try:
            # 启动企业微信服务
            logger.info("正在启动企业微信服务...")
            # 企业微信服务不需要持续运行，使用API调用
            logger.info("企业微信服务启动成功")
            self.is_running = True
        except Exception as e:
            logger.error(f"启动消息服务时出错: {e}")
            self.is_running = False
    
    async def stop(self):
        """停止消息服务"""
        try:
            if self.is_running:
                logger.info("正在停止消息服务...")
                self.is_running = False
                logger.info("消息服务已停止")
        except Exception as e:
            logger.error(f"停止消息服务时出错: {e}")
    
    def get_status(self) -> dict:
        """获取服务状态"""
        return {
            'service_type': self.service_type,
            'is_running': self.is_running
        }
    
    def send_message(self, user_id: str, message: str) -> bool:
        """发送消息
        
        Args:
            user_id: 用户ID
            message: 消息内容
            
        Returns:
            是否发送成功
        """
        # 使用企业微信发送
        return wecom_handler.send_message(user_id, message)
    
    def receive_message(self, data: dict) -> dict:
        """接收消息
        
        Args:
            data: 消息数据
            
        Returns:
            处理结果
        """
        # 处理企业微信消息
        return wecom_handler.receive_message(data)

# 创建消息服务实例
message_service = MessageService()

async def main():
    """主函数"""
    try:
        await message_service.start()
        # 保持运行
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在退出...")
        await message_service.stop()

if __name__ == "__main__":
    asyncio.run(main())
