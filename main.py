import os
import sys
import logging
from datetime import datetime
from fastapi import FastAPI, Request, status, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import traceback

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

# 导入配置管理器
from utils.config import config_manager

# 导入监控模块
from modules.system.monitoring import start_monitoring, system_monitor

# 导入安全模块
from utils.security import security_manager

# 导入客户管理后台任务
from modules.customer.tasks import start_customer_tasks

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

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    error_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
    logger.error(f"全局异常 [{error_id}]: {exc}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "服务器内部错误",
            "error_id": error_id,
            "timestamp": datetime.now().isoformat()
        }
    )

# 请求验证错误处理
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证错误处理"""
    error_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
    logger.warning(f"请求验证错误 [{error_id}]: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": "请求参数验证失败",
            "errors": exc.errors(),
            "error_id": error_id,
            "timestamp": datetime.now().isoformat()
        }
    )

# 404错误处理
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    """404错误处理"""
    error_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
    logger.warning(f"404错误 [{error_id}]: {request.url}")
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "Not Found",
            "detail": "请求的资源不存在",
            "path": request.url.path,
            "error_id": error_id,
            "timestamp": datetime.now().isoformat()
        }
    )

# 创建安全实例
security = HTTPBearer()

# 定义获取当前用户的依赖函数
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户"""
    token = credentials.credentials
    try:
        return security_manager.verify_token(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

# 导入路由
from modules.knowledge.routes import router as knowledge_router
from modules.qa.routes import router as qa_router
from modules.system.routes import router as system_router
from modules.message.routes import router as message_router
from modules.customer.routes import router as customer_router
from modules.consultation.routes import router as consultation_router
from modules.document.routes import router as document_router
from modules.case.routes import router as case_router
from modules.contract.routes import router as contract_router

# 注册路由（添加认证保护）
app.include_router(message_router, prefix="/api/message", tags=["message"])
app.include_router(knowledge_router, prefix="/api/knowledge", tags=["knowledge"])
app.include_router(qa_router, prefix="/api/qa", tags=["qa"])
app.include_router(system_router, prefix="/api/system", tags=["system"])
app.include_router(customer_router, prefix="/api/customer", tags=["customer"])
app.include_router(consultation_router, prefix="/api/consultation", tags=["consultation"])
app.include_router(document_router, prefix="/api/document", tags=["document"])
app.include_router(case_router, prefix="/api/case", tags=["case"])
app.include_router(contract_router, prefix="/api/contract", tags=["contract"])

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

@app.get("/api/system/health")
def system_health_check():
    """系统健康检查"""
    return system_monitor.get_system_status()

# 添加认证测试端点
@app.get("/api/test/auth")
async def test_auth(current_user: dict = Depends(get_current_user)):
    """测试认证"""
    return {
        "message": "认证成功",
        "user": current_user
    }

# 添加令牌生成端点
@app.post("/api/auth/token")
async def generate_token(user_id: int, role: str = "user"):
    """生成认证令牌"""
    token = security_manager.generate_token(user_id, role)
    return {
        "access_token": token,
        "token_type": "bearer"
    }

if __name__ == "__main__":
    # 启动监控服务
    start_monitoring()
    
    # 启动客户管理后台任务
    start_customer_tasks()
    
    # 启动Web服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config_manager.getboolean('general', 'debug', True)
    )
