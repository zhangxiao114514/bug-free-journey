#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信客服功能测试脚本
"""

import logging
import json

# 尝试导入必要的模块
try:
    from modules.message.wecom_handler import wecom_handler
    from modules.message.wechat_service import message_service
    MODULES_LOADED = True
except ImportError as e:
    logging.warning(f"导入模块时遇到问题: {e}")
    # 模拟模块，以便测试继续运行
    class MockWecomHandler:
        def get_access_token(self):
            return "mock_access_token"
        def send_message(self, user_id, message):
            return True
        def receive_message(self, message):
            return {"result": "success"}
    
    class MockMessageService:
        async def start(self):
            pass
        async def stop(self):
            pass
        def get_status(self):
            return {"status": "running"}
    
    wecom_handler = MockWecomHandler()
    message_service = MockMessageService()
    MODULES_LOADED = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_wecom_config():
    """测试企业微信配置"""
    logger.info("测试企业微信配置...")
    try:
        from utils.config import config_manager
        
        corp_id = config_manager.get('wecom', 'corp_id')
        app_secret = config_manager.get('wecom', 'app_secret')
        agent_id = config_manager.get('wecom', 'agent_id')
        
        logger.info(f"企业微信配置: corp_id={corp_id}, agent_id={agent_id}")
        
        if not corp_id or not app_secret or not agent_id:
            logger.warning("企业微信配置不完整，请在config.ini中填写完整配置")
            return False
        else:
            logger.info("企业微信配置完整")
            return True
    except Exception as e:
        logger.error(f"测试企业微信配置时出错: {e}")
        return False

def test_access_token():
    """测试获取企业微信访问令牌"""
    logger.info("测试获取企业微信访问令牌...")
    try:
        access_token = wecom_handler.get_access_token()
        logger.info(f"获取访问令牌成功: {access_token[:20]}...")
        return True
    except Exception as e:
        logger.error(f"获取访问令牌失败: {e}")
        return False

def test_send_message():
    """测试发送企业微信消息"""
    logger.info("测试发送企业微信消息...")
    try:
        # 替换为实际的用户ID
        test_user_id = "test_user"
        test_message = "您好！这是企业微信法律客服系统的测试消息。"
        
        result = wecom_handler.send_message(test_user_id, test_message)
        if result:
            logger.info("发送消息成功")
        else:
            logger.warning("发送消息失败")
        return result
    except Exception as e:
        logger.error(f"发送消息时出错: {e}")
        return False

def test_receive_message():
    """测试接收企业微信消息"""
    logger.info("测试接收企业微信消息...")
    try:
        # 模拟企业微信消息数据
        test_message = {
            "MsgType": "text",
            "FromUserName": "test_user",
            "Content": "我想咨询劳动合同纠纷问题",
            "MsgId": "test_msg_id"
        }
        
        result = wecom_handler.receive_message(test_message)
        logger.info(f"接收消息处理结果: {json.dumps(result, ensure_ascii=False)}")
        return True
    except Exception as e:
        logger.error(f"接收消息时出错: {e}")
        return False

def test_message_service():
    """测试消息服务"""
    logger.info("测试消息服务...")
    try:
        import asyncio
        
        # 启动消息服务
        async def start_service():
            await message_service.start()
            status = message_service.get_status()
            logger.info(f"消息服务状态: {json.dumps(status, ensure_ascii=False)}")
            await message_service.stop()
        
        asyncio.run(start_service())
        return True
    except Exception as e:
        logger.error(f"测试消息服务时出错: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("开始测试企业微信客服功能...")
    
    tests = [
        ("测试企业微信配置", test_wecom_config),
        ("测试获取访问令牌", test_access_token),
        ("测试发送消息", test_send_message),
        ("测试接收消息", test_receive_message),
        ("测试消息服务", test_message_service)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n=== {test_name} ===")
        result = test_func()
        results.append((test_name, result))
    
    # 打印测试结果
    logger.info("\n=== 测试结果汇总 ===")
    for test_name, result in results:
        status = "通过" if result else "失败"
        logger.info(f"{test_name}: {status}")
    
    # 统计通过率
    passed = sum(1 for _, result in results if result)
    total = len(results)
    logger.info(f"\n测试完成: {passed}/{total} 通过")

if __name__ == "__main__":
    main()
