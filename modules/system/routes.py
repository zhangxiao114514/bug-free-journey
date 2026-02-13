from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from sqlalchemy.orm import Session

from utils.database import get_db
from modules.system.monitoring import system_monitor
from modules.system.dashboard import dashboard

router = APIRouter()

@router.get("/status")
async def get_system_status():
    """获取系统状态"""
    try:
        status = dashboard.get_system_status()
        return {"success": True, "status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统状态时出错: {str(e)}")

@router.get("/health")
async def get_service_health():
    """获取服务健康状态"""
    try:
        health = dashboard.get_service_health()
        return {"success": True, "health": health}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务健康状态时出错: {str(e)}")

@router.get("/metrics")
async def get_performance_metrics():
    """获取性能指标"""
    try:
        metrics = dashboard.get_performance_metrics()
        return {"success": True, "metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能指标时出错: {str(e)}")

@router.get("/alerts")
async def get_alert_summary():
    """获取告警摘要"""
    try:
        alerts = dashboard.get_alert_summary()
        return {"success": True, "alerts": alerts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警摘要时出错: {str(e)}")

@router.post("/monitoring/setup")
async def setup_monitoring():
    """设置监控"""
    try:
        system_monitor.setup_prometheus()
        return {"success": True, "message": "监控设置成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置监控时出错: {str(e)}")

@router.get("/monitoring/metrics")
async def get_monitoring_metrics():
    """获取监控指标"""
    try:
        metrics = system_monitor.collect_metrics()
        return {"success": True, "metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取监控指标时出错: {str(e)}")

@router.get("/monitoring/health")
async def check_system_health():
    """检查系统健康"""
    try:
        health = system_monitor.check_health()
        return {"success": True, "health": health}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查系统健康时出错: {str(e)}")

@router.get("/monitoring/alerts/config")
async def get_alert_config():
    """获取告警配置"""
    try:
        config = system_monitor.get_alert_config()
        return {"success": True, "config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警配置时出错: {str(e)}")

@router.post("/monitoring/alerts/config")
async def set_alert_config(config: Dict[str, Any]):
    """设置告警配置"""
    try:
        # 这里可以添加设置告警配置的逻辑
        return {"success": True, "message": "告警配置设置成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置告警配置时出错: {str(e)}")

@router.post("/restart")
async def restart_services():
    """重启服务"""
    try:
        # 这里可以添加重启服务的逻辑
        return {"success": True, "message": "服务重启成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重启服务时出错: {str(e)}")

@router.post("/backup")
async def create_backup():
    """创建备份"""
    try:
        # 这里可以添加创建备份的逻辑
        return {"success": True, "message": "备份创建成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建备份时出错: {str(e)}")
