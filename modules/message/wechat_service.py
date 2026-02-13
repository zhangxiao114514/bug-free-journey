import asyncio
import logging
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import redis

from utils.config import config_manager
from modules.message.wecom_handler import wecom_handler
from modules.message.models import Message as MessageModel
from utils.database import get_db

logger = logging.getLogger(__name__)

class MessageService:
    """消息服务类"""
    
    def __init__(self):
        self.is_running = False
        self.service_type = 'wecom'  # 固定为企业微信服务
        self.redis_client = None
        self.redis_pool = None
        self.message_queue = 'message:queue'
        self.processing_queue = 'message:processing'
        self.failed_queue = 'message:failed'
        self.consumer_task = None
    
    async def start(self):
        """启动消息服务"""
        try:
            # 启动企业微信服务
            logger.info("正在启动企业微信服务...")
            
            # 初始化Redis连接
            self._init_redis()
            
            # 启动消息消费者
            self.consumer_task = asyncio.create_task(self._consume_messages())
            
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
                
                # 停止消息消费者
                if self.consumer_task:
                    self.consumer_task.cancel()
                    try:
                        await self.consumer_task
                    except asyncio.CancelledError:
                        pass
                
                # 关闭Redis连接
                if self.redis_client:
                    self.redis_client.close()
                if self.redis_pool:
                    self.redis_pool.disconnect()
                    self.redis_pool = None
                
                self.is_running = False
                logger.info("消息服务已停止")
        except Exception as e:
            logger.error(f"停止消息服务时出错: {e}")
    
    def _init_redis(self):
        """初始化Redis连接池"""
        try:
            redis_config = {
                'host': config_manager.get('redis', 'host', 'localhost'),
                'port': config_manager.getint('redis', 'port', 6379),
                'password': config_manager.get('redis', 'password', ''),
                'db': config_manager.getint('redis', 'db', 0),
                'max_connections': config_manager.getint('redis', 'max_connections', 50),
                'decode_responses': True,  # 自动解码响应
                'socket_connect_timeout': 5,  # 连接超时
                'socket_timeout': 5,  # 读取超时
                'retry_on_timeout': True,  # 超时重试
                'health_check_interval': 30,  # 健康检查间隔
            }
            
            # 创建Redis连接池
            self.redis_pool = redis.ConnectionPool(**redis_config)
            self.redis_client = redis.Redis(connection_pool=self.redis_pool)
            
            # 测试连接
            self.redis_client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.warning(f"Redis连接失败，将使用内存队列: {e}")
            # Redis连接失败时，使用内存队列
            self.redis_client = None
            self.redis_pool = None
    
    def _reconnect_redis(self):
        """重新连接Redis"""
        try:
            logger.info("尝试重新连接Redis")
            self._init_redis()
            return self.redis_client is not None
        except Exception as e:
            logger.error(f"Redis重连失败: {e}")
            return False
    
    async def _consume_messages(self):
        """消费消息队列"""
        batch_size = 10  # 批量处理消息数量
        batch_timeout = 0.5  # 批量处理超时时间（秒）
        
        while self.is_running:
            try:
                if self.redis_client:
                    try:
                        # 批量获取消息
                        messages = []
                        start_time = time.time()
                        
                        # 批量拉取消息
                        while len(messages) < batch_size and time.time() - start_time < batch_timeout:
                            message_data = self.redis_client.brpop(self.message_queue, timeout=0.1)
                            if message_data:
                                message_id, message_json = message_data
                                message = json.loads(message_json)
                                messages.append(message)
                            else:
                                break
                        
                        # 批量处理消息
                        if messages:
                            logger.info(f"批量处理 {len(messages)} 条消息")
                            await asyncio.gather(*[self._process_message(msg) for msg in messages])
                    except redis.RedisError as e:
                        logger.warning(f"Redis操作失败: {e}")
                        # 尝试重新连接
                        self._reconnect_redis()
                        await asyncio.sleep(2)
                else:
                    # Redis不可用时，短暂休眠
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"消费消息时出错: {e}")
                await asyncio.sleep(1)
    
    async def _process_message(self, message: Dict[str, Any]):
        """处理消息
        
        Args:
            message: 消息数据
        """
        message_id = message.get('message_id')
        
        # 检查是否需要延迟处理
        next_retry_at = message.get('next_retry_at')
        if next_retry_at:
            try:
                retry_time = datetime.fromisoformat(next_retry_at)
                if datetime.now() < retry_time:
                    # 未达到重试时间，重新放回队列
                    if self.redis_client:
                        try:
                            self.redis_client.lpush(self.message_queue, json.dumps(message))
                            logger.info(f"消息 {message_id} 未达到重试时间，重新放回队列")
                        except redis.RedisError as e:
                            logger.warning(f"Redis操作失败(放回队列): {e}")
                            # 尝试重新连接
                            self._reconnect_redis()
                    return
            except Exception as e:
                logger.error(f"解析重试时间时出错: {e}")
        
        try:
            # 将消息移到处理中队列
            if self.redis_client:
                try:
                    self.redis_client.sadd(self.processing_queue, message_id)
                except redis.RedisError as e:
                    logger.warning(f"Redis操作失败(添加处理中队列): {e}")
                    # 尝试重新连接
                    self._reconnect_redis()
            
            # 处理消息
            user_id = message.get('user_id')
            content = message.get('content')
            
            logger.info(f"处理消息: 用户={user_id}, 内容={content[:50]}...")
            
            # 发送消息
            success = wecom_handler.send_message(user_id, content)
            
            if success:
                logger.info(f"消息发送成功: {message_id}")
                # 从处理中队列移除
                if self.redis_client:
                    try:
                        self.redis_client.srem(self.processing_queue, message_id)
                    except redis.RedisError as e:
                        logger.warning(f"Redis操作失败(移除处理中队列): {e}")
                        # 尝试重新连接
                        self._reconnect_redis()
            else:
                logger.warning(f"消息发送失败: {message_id}")
                # 将消息移到失败队列
                if self.redis_client:
                    try:
                        self.redis_client.srem(self.processing_queue, message_id)
                        self.redis_client.sadd(self.failed_queue, message_id)
                        self.redis_client.set(f"message:failed:{message_id}", json.dumps(message))
                    except redis.RedisError as e:
                        logger.warning(f"Redis操作失败(添加失败队列): {e}")
                        # 尝试重新连接
                        self._reconnect_redis()
                    
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")
            # 将消息移到失败队列
            if self.redis_client:
                try:
                    self.redis_client.srem(self.processing_queue, message_id)
                    self.redis_client.sadd(self.failed_queue, message_id)
                    self.redis_client.set(f"message:failed:{message_id}", json.dumps(message))
                except redis.RedisError as e:
                    logger.warning(f"Redis操作失败(错误处理): {e}")
                    # 尝试重新连接
                    self._reconnect_redis()
    
    def get_status(self) -> dict:
        """获取服务状态"""
        queue_size = 0
        processing_size = 0
        failed_size = 0
        
        if self.redis_client:
            try:
                queue_size = self.redis_client.llen(self.message_queue)
                processing_size = self.redis_client.scard(self.processing_queue)
                failed_size = self.redis_client.scard(self.failed_queue)
            except Exception as e:
                logger.warning(f"获取队列状态时出错: {e}")
        
        return {
            'service_type': self.service_type,
            'is_running': self.is_running,
            'redis_connected': self.redis_client is not None,
            'message_queue_size': queue_size,
            'processing_queue_size': processing_size,
            'failed_queue_size': failed_size
        }
    
    def send_message(self, user_id: str, message: str) -> bool:
        """发送消息
        
        Args:
            user_id: 用户ID
            message: 消息内容
            
        Returns:
            是否发送成功
        """
        try:
            # 创建消息ID
            message_id = str(uuid.uuid4())
            
            # 构建消息数据
            message_data = {
                'message_id': message_id,
                'user_id': user_id,
                'content': message,
                'created_at': datetime.now().isoformat(),
                'retry_count': 0
            }
            
            # 加入消息队列
            if self.redis_client:
                self.redis_client.lpush(self.message_queue, json.dumps(message_data))
                logger.info(f"消息已加入队列: {message_id}")
                return True
            else:
                # Redis不可用时，直接发送
                return wecom_handler.send_message(user_id, message)
        except Exception as e:
            logger.error(f"发送消息时出错: {e}")
            return False
    
    def receive_message(self, data: dict) -> dict:
        """接收消息
        
        Args:
            data: 消息数据
            
        Returns:
            处理结果
        """
        # 处理企业微信消息
        return wecom_handler.receive_message(data)
    
    def retry_failed_messages(self, limit: int = 10) -> int:
        """重试失败消息
        
        Args:
            limit: 重试消息数量
            
        Returns:
            重试的消息数量
        """
        if not self.redis_client:
            return 0
        
        try:
            failed_messages = self.redis_client.smembers(self.failed_queue)
            retry_count = 0
            
            for message_id in failed_messages:
                if retry_count >= limit:
                    break
                
                message_data = self.redis_client.get(f"message:failed:{message_id}")
                if message_data:
                    message = json.loads(message_data)
                    retry_count_current = message.get('retry_count', 0) + 1
                    
                    # 检查是否超过最大重试次数
                    if retry_count_current > 5:  # 最大重试次数
                        logger.warning(f"消息 {message_id} 超过最大重试次数，放弃重试")
                        self.redis_client.srem(self.failed_queue, message_id)
                        self.redis_client.delete(f"message:failed:{message_id}")
                        continue
                    
                    # 指数退避策略
                    delay = min(2 ** (retry_count_current - 1), 30)  # 最大延迟30秒
                    message['retry_count'] = retry_count_current
                    message['retry_delay'] = delay
                    
                    # 添加重试时间戳
                    message['next_retry_at'] = (datetime.now() + timedelta(seconds=delay)).isoformat()
                    
                    # 重新加入队列
                    self.redis_client.lpush(self.message_queue, json.dumps(message))
                    self.redis_client.srem(self.failed_queue, message_id)
                    self.redis_client.delete(f"message:failed:{message_id}")
                    
                    retry_count += 1
                    logger.info(f"重试消息: {message_id}, 重试次数: {retry_count_current}, 延迟: {delay}秒")
            
            return retry_count
        except Exception as e:
            logger.error(f"重试失败消息时出错: {e}")
            return 0
    
    def clear_failed_messages(self) -> int:
        """清理失败消息
        
        Returns:
            清理的消息数量
        """
        if not self.redis_client:
            return 0
        
        try:
            failed_messages = self.redis_client.smembers(self.failed_queue)
            cleared_count = 0
            
            for message_id in failed_messages:
                self.redis_client.delete(f"message:failed:{message_id}")
                cleared_count += 1
            
            self.redis_client.delete(self.failed_queue)
            logger.info(f"清理了 {cleared_count} 条失败消息")
            return cleared_count
        except Exception as e:
            logger.error(f"清理失败消息时出错: {e}")
            return 0

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
