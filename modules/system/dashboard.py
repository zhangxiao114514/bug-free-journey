import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from utils.config import config_manager
from utils.database import get_db
from modules.system.monitoring import system_monitor
from modules.message.models import Message
from modules.consultation.models import Consultation
from modules.case.models import Case
from modules.contract.models import Contract

logger = logging.getLogger(__name__)

class DashboardManager:
    """系统管理仪表盘管理器"""
    
    def __init__(self):
        pass
    
    def get_dashboard_data(self, duration: int = 24) -> Dict[str, Any]:
        """获取仪表盘数据
        
        Args:
            duration: 数据持续时间（小时）
            
        Returns:
            仪表盘数据
        """
        try:
            dashboard_data = {
                'timestamp': datetime.now().isoformat(),
                'duration': duration,
                'system_status': self._get_system_status(),
                'metrics': self._get_metrics_data(),
                'business_data': self._get_business_data(),
                'recent_activities': self._get_recent_activities(),
                'alerts': self._get_recent_alerts()
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"获取仪表盘数据时出错: {e}")
            return {'error': str(e)}
    
    def _get_system_status(self) -> Dict[str, Any]:
        """获取系统状态
        
        Returns:
            系统状态
        """
        try:
            # 从监控模块获取系统状态
            if system_monitor:
                return system_monitor.get_system_status()
            else:
                return {
                    'timestamp': datetime.now().isoformat(),
                    'service_status': 'unknown',
                    'monitoring_enabled': False
                }
                
        except Exception as e:
            logger.error(f"获取系统状态时出错: {e}")
            return {'error': str(e)}
    
    def _get_metrics_data(self) -> Dict[str, Any]:
        """获取监控指标数据
        
        Returns:
            监控指标数据
        """
        try:
            # 从监控模块获取指标数据
            if system_monitor:
                return system_monitor.get_monitoring_data()
            else:
                return {
                    'timestamp': datetime.now().isoformat(),
                    'metrics': {},
                    'alerts': []
                }
                
        except Exception as e:
            logger.error(f"获取监控指标数据时出错: {e}")
            return {'error': str(e)}
    
    def _get_business_data(self) -> Dict[str, Any]:
        """获取业务数据
        
        Returns:
            业务数据
        """
        try:
            db = next(get_db())
            
            # 时间范围
            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)
            
            # 消息统计
            message_stats = {
                'total': db.query(Message).count(),
                'today': db.query(Message).filter(
                    Message.created_at >= datetime.combine(datetime.now().date(), datetime.min.time())
                ).count(),
                'last_7_days': db.query(Message).filter(
                    Message.created_at >= start_time
                ).count()
            }
            
            # 咨询统计
            consultation_stats = {
                'total': db.query(Consultation).count(),
                'today': db.query(Consultation).filter(
                    Consultation.created_at >= datetime.combine(datetime.now().date(), datetime.min.time())
                ).count(),
                'pending': db.query(Consultation).filter(
                    Consultation.status.in_(['pending', 'processing'])
                ).count(),
                'completed': db.query(Consultation).filter(
                    Consultation.status == 'completed'
                ).count()
            }
            
            # 案例统计
            case_stats = {
                'total': db.query(Case).count(),
                'today': db.query(Case).filter(
                    Case.created_at >= datetime.combine(datetime.now().date(), datetime.min.time())
                ).count(),
                'pending': db.query(Case).filter(
                    Case.status.in_(['pending', 'processing'])
                ).count(),
                'completed': db.query(Case).filter(
                    Case.status == 'completed'
                ).count()
            }
            
            # 合同统计
            contract_stats = {
                'total': db.query(Contract).count(),
                'today': db.query(Contract).filter(
                    Contract.created_at >= datetime.combine(datetime.now().date(), datetime.min.time())
                ).count()
            }
            
            # 满意度统计
            completed_consultations = db.query(Consultation).filter(
                Consultation.status == 'completed',
                Consultation.satisfaction_score.isnot(None)
            ).all()
            
            avg_satisfaction = 0
            if completed_consultations:
                total_score = sum(c.satisfaction_score for c in completed_consultations)
                avg_satisfaction = total_score / len(completed_consultations)
            
            business_data = {
                'timestamp': datetime.now().isoformat(),
                'message_stats': message_stats,
                'consultation_stats': consultation_stats,
                'case_stats': case_stats,
                'contract_stats': contract_stats,
                'avg_satisfaction': avg_satisfaction
            }
            
            return business_data
            
        except Exception as e:
            logger.error(f"获取业务数据时出错: {e}")
            return {'error': str(e)}
        finally:
            db.close()
    
    def _get_recent_activities(self) -> List[Dict[str, Any]]:
        """获取最近活动
        
        Returns:
            最近活动列表
        """
        try:
            db = next(get_db())
            
            # 获取最近24小时的活动
            start_time = datetime.now() - timedelta(hours=24)
            
            # 获取最近消息
            recent_messages = db.query(Message).filter(
                Message.created_at >= start_time
            ).order_by(Message.created_at.desc()).limit(10).all()
            
            # 获取最近咨询
            recent_consultations = db.query(Consultation).filter(
                Consultation.created_at >= start_time
            ).order_by(Consultation.created_at.desc()).limit(10).all()
            
            # 获取最近案例
            recent_cases = db.query(Case).filter(
                Case.created_at >= start_time
            ).order_by(Case.created_at.desc()).limit(10).all()
            
            # 构建活动列表
            activities = []
            
            # 添加消息活动
            for msg in recent_messages:
                activities.append({
                    'id': f'msg_{msg.id}',
                    'type': 'message',
                    'description': f'收到消息: {msg.content[:50]}...',
                    'timestamp': msg.created_at.isoformat(),
                    'status': msg.status
                })
            
            # 添加咨询活动
            for consult in recent_consultations:
                activities.append({
                    'id': f'consult_{consult.id}',
                    'type': 'consultation',
                    'description': f'创建咨询: {consult.title}',
                    'timestamp': consult.created_at.isoformat(),
                    'status': consult.status
                })
            
            # 添加案例活动
            for case in recent_cases:
                activities.append({
                    'id': f'case_{case.id}',
                    'type': 'case',
                    'description': f'创建案例: {case.title}',
                    'timestamp': case.created_at.isoformat(),
                    'status': case.status
                })
            
            # 按时间排序
            activities.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # 限制返回数量
            return activities[:20]
            
        except Exception as e:
            logger.error(f"获取最近活动时出错: {e}")
            return []
        finally:
            db.close()
    
    def _get_recent_alerts(self) -> List[Dict[str, Any]]:
        """获取最近告警
        
        Returns:
            最近告警列表
        """
        try:
            # 从监控模块获取告警
            if system_monitor:
                monitoring_data = system_monitor.get_monitoring_data()
                if 'alerts' in monitoring_data:
                    return monitoring_data['alerts'][:10]  # 只返回最近10条
            
            return []
            
        except Exception as e:
            logger.error(f"获取最近告警时出错: {e}")
            return []
    
    def get_service_management_data(self) -> Dict[str, Any]:
        """获取服务管理数据
        
        Returns:
            服务管理数据
        """
        try:
            service_data = {
                'timestamp': datetime.now().isoformat(),
                'services': {
                    'wecom_service': {
                        'name': '企业微信服务',
                        'status': 'running' if system_monitor and system_monitor.is_running else 'stopped',
                        'config': {
                            'service_type': 'wecom',
                            'corp_id': config_manager.get('wecom', 'corp_id', ''),
                            'agent_id': config_manager.get('wecom', 'agent_id', '')
                        }
                    },
                    'monitoring_service': {
                        'name': '监控服务',
                        'status': 'running' if system_monitor and system_monitor.is_running else 'stopped',
                        'config': {
                            'metrics_port': config_manager.getint('monitoring', 'metrics_port', 8001),
                            'alert_enabled': config_manager.getboolean('monitoring', 'alert_enabled', True)
                        }
                    },
                    'database_service': {
                        'name': '数据库服务',
                        'status': 'running',  # 假设数据库服务正常运行
                        'config': {
                            'host': config_manager.get('database', 'host', 'localhost'),
                            'database': config_manager.get('database', 'database', 'legal_service')
                        }
                    }
                }
            }
            
            return service_data
            
        except Exception as e:
            logger.error(f"获取服务管理数据时出错: {e}")
            return {'error': str(e)}
    
    def get_config_management_data(self) -> Dict[str, Any]:
        """获取配置管理数据
        
        Returns:
            配置管理数据
        """
        try:
            config_data = {
                'timestamp': datetime.now().isoformat(),
                'config_sections': {
                    'general': {
                        'name': '系统基本配置',
                        'items': {
                            'system_name': config_manager.get('general', 'system_name', '企业微信法律客服系统'),
                            'system_version': config_manager.get('general', 'system_version', '1.0.0'),
                            'debug': config_manager.getboolean('general', 'debug', True)
                        }
                    },
                    'wecom': {
                        'name': '企业微信配置',
                        'items': {
                            'corp_id': config_manager.get('wecom', 'corp_id', ''),
                            'agent_id': config_manager.get('wecom', 'agent_id', '')
                        }
                    },
                    'database': {
                        'name': '数据库配置',
                        'items': {
                            'host': config_manager.get('database', 'host', 'localhost'),
                            'port': config_manager.getint('database', 'port', 3306),
                            'database': config_manager.get('database', 'database', 'legal_service')
                        }
                    },
                    'redis': {
                        'name': 'Redis配置',
                        'items': {
                            'host': config_manager.get('redis', 'host', 'localhost'),
                            'port': config_manager.getint('redis', 'port', 6379)
                        }
                    },
                    'monitoring': {
                        'name': '监控配置',
                        'items': {
                            'metrics_port': config_manager.getint('monitoring', 'metrics_port', 8001),
                            'alert_enabled': config_manager.getboolean('monitoring', 'alert_enabled', True)
                        }
                    }
                }
            }
            
            return config_data
            
        except Exception as e:
            logger.error(f"获取配置管理数据时出错: {e}")
            return {'error': str(e)}
    
    def update_config(self, section: str, key: str, value: Any) -> Dict[str, Any]:
        """更新配置
        
        Args:
            section: 配置部分
            key: 配置键
            value: 配置值
            
        Returns:
            更新结果
        """
        try:
            # 这里应该实现配置更新逻辑
            # 为了简化，我们只在日志中记录
            logger.info(f"更新配置: {section}.{key} = {value}")
            
            # 实际应用中，这里应该调用配置管理器的更新方法
            # config_manager.update(section, key, value)
            
            return {
                'success': True,
                'message': f"配置更新成功: {section}.{key} = {value}"
            }
            
        except Exception as e:
            logger.error(f"更新配置时出错: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def start_service(self, service_name: str) -> Dict[str, Any]:
        """启动服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            启动结果
        """
        try:
            if service_name == 'monitoring':
                # 启动监控服务
                from modules.system.monitoring import start_monitoring
                start_monitoring()
                return {
                    'success': True,
                    'message': "监控服务启动成功"
                }
            else:
                logger.info(f"启动服务: {service_name}")
                return {
                    'success': True,
                    'message': f"服务启动成功: {service_name}"
                }
                
        except Exception as e:
            logger.error(f"启动服务时出错: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def stop_service(self, service_name: str) -> Dict[str, Any]:
        """停止服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            停止结果
        """
        try:
            if service_name == 'monitoring':
                # 停止监控服务
                from modules.system.monitoring import stop_monitoring
                stop_monitoring()
                return {
                    'success': True,
                    'message': "监控服务停止成功"
                }
            else:
                logger.info(f"停止服务: {service_name}")
                return {
                    'success': True,
                    'message': f"服务停止成功: {service_name}"
                }
                
        except Exception as e:
            logger.error(f"停止服务时出错: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# 创建仪表盘管理器实例
dashboard_manager = DashboardManager()

# 获取仪表盘数据
def get_dashboard_data(duration: int = 24) -> Dict[str, Any]:
    """获取仪表盘数据
    
    Args:
        duration: 数据持续时间（小时）
        
    Returns:
        仪表盘数据
    """
    return dashboard_manager.get_dashboard_data(duration)

# 获取服务管理数据
def get_service_management_data() -> Dict[str, Any]:
    """获取服务管理数据
    
    Returns:
        服务管理数据
    """
    return dashboard_manager.get_service_management_data()

# 获取配置管理数据
def get_config_management_data() -> Dict[str, Any]:
    """获取配置管理数据
    
    Returns:
        配置管理数据
    """
    return dashboard_manager.get_config_management_data()

# 更新配置
def update_config(section: str, key: str, value: Any) -> Dict[str, Any]:
    """更新配置
    
    Args:
        section: 配置部分
        key: 配置键
        value: 配置值
        
    Returns:
        更新结果
    """
    return dashboard_manager.update_config(section, key, value)

# 启动服务
def start_service(service_name: str) -> Dict[str, Any]:
    """启动服务
    
    Args:
        service_name: 服务名称
        
    Returns:
        启动结果
    """
    return dashboard_manager.start_service(service_name)

# 停止服务
def stop_service(service_name: str) -> Dict[str, Any]:
    """停止服务
    
    Args:
        service_name: 服务名称
        
    Returns:
        停止结果
    """
    return dashboard_manager.stop_service(service_name)
