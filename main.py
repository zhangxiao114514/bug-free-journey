import os
import sys
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

# 导入配置管理器
from utils.config import config_manager

# 配置日志
logging.basicConfig(
    level=getattr(logging, config_manager.get('general', 'log_level', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=config_manager.get('general', 'system_name', '企业微信法律客服系统'),
    version=config_manager.get('general', 'system_version', '1.0.0'),
    description='基于Python的智能企业微信法律客服系统'
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应设置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入路由
# from modules.message.routes import router as message_router
# from modules.knowledge.routes import router as knowledge_router
# from modules.qa.routes import router as qa_router
# from modules.customer.routes import router as customer_router
# from modules.consultation.routes import router as consultation_router
# from modules.document.routes import router as document_router
# from modules.system.routes import router as system_router
# from modules.notification.routes import router as notification_router
# from modules.analytics.routes import router as analytics_router
# from modules.security.routes import router as security_router

# 注册路由
# app.include_router(message_router, prefix="/api/message", tags=["message"])
# app.include_router(knowledge_router, prefix="/api/knowledge", tags=["knowledge"])
# app.include_router(qa_router, prefix="/api/qa", tags=["qa"])
# app.include_router(customer_router, prefix="/api/customer", tags=["customer"])
# app.include_router(consultation_router, prefix="/api/consultation", tags=["consultation"])
# app.include_router(document_router, prefix="/api/document", tags=["document"])
# app.include_router(system_router, prefix="/api/system", tags=["system"])
# app.include_router(notification_router, prefix="/api/notification", tags=["notification"])
# app.include_router(analytics_router, prefix="/api/analytics", tags=["analytics"])
# app.include_router(security_router, prefix="/api/security", tags=["security"])

@app.get("/")
def read_root():
    """根路径"""
    return {
        "message": "企业微信法律客服系统API",
        "version": config_manager.get('general', 'system_version', '1.0.0'),
        "status": "running"
    }

@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy"}

if __name__ == "__main__":
    # 启动Web服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config_manager.getboolean('general', 'debug', True)
    )
