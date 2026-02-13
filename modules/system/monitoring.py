import logging
import time
import threading
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List
from prometheus_client import Counter, Gauge, Histogram, start_http_server

from utils.config import config_manager
from utils.database import get_db
from modules.message.models import Message
from modules.consultation.models import Consultation
from modules.case.models import Case

logger = logging.getLogger(__name__)

# Prometheus 指标定义
# 消息处理指标
message_counter = Counter('wecom_messages_total', 'Total number of messages processed', ['type'])
message_error_counter = Counter('wecom_messages_errors_total', 'Total number of message processing errors')
message_processing_time = Histogram('wecom_message_processing_seconds', 'Message processing time in seconds')
message_queue_length = Gauge('wecom_message_queue_length', 'Message queue length')

# 系统指标
system_cpu_usage = Gauge('system_cpu_usage_percent', 'System CPU usage percentage')
system_memory_usage = Gauge('system_memory_usage_percent', 'System memory usage percentage')
system_disk_usage = Gauge('system_disk_usage_percent', 'System disk usage percentage')
system_network_bytes_sent = Counter('system_network_bytes_sent_total', 'Total bytes sent over network')
system_network_bytes_recv = Counter('system_network_bytes_recv_total', 'Total bytes received over network')

# 服务指标
service_up = Gauge('service_up', 'Service status (1=up, 0=down)')
service_response_time = Gauge('service_response_time_seconds', 'Service response time in seconds')
service_requests_total = Counter('service_requests_total', 'Total number of service requests', ['method', 'endpoint', 'status'])

# 数据库指标
database_connections = Gauge('database_connections_total', 'Total database connections')
database_connection_errors = Counter('database_connection_errors_total', 'Total database connection errors')
database_query_time = Histogram('database_query_seconds', 'Database query time in seconds')

# Redis指标
redis_connections = Gauge('redis_connections_total', 'Total Redis connections')
redis_connection_errors = Counter('redis_connection_errors_total', 'Total Redis connection errors')
redis_commands_total = Counter('redis_commands_total', 'Total Redis commands executed', ['command'])

# 业务指标
consultation_counter = Counter('consultations_total', 'Total number of consultations', ['status'])
case_counter = Counter('cases_total', 'Total number of cases', ['status'])
satisfaction_score = Gauge('average_satisfaction_score', 'Average customer satisfaction score')
knowledge_base_size = Gauge('knowledge_base_size_total', 'Total number of knowledge base entries')
contract_templates_total = Gauge('contract_templates_total', 'Total number of contract templates')

class SystemMonitor:
    """系统监控类"""
    
    def __init__(self):
        self.is_running = False
        self.monitoring_thread = None
        self.alert_thread = None
        self.metrics_port = config_manager.getint('monitoring', 'metrics_port', 8001)
        self.alert_enabled = config_manager.getboolean('monitoring', 'alert_enabled', True)
        self.alert_threshold_response_time = config_manager.getfloat('monitoring', 'alert_threshold_response_time', 5)
        self.alert_threshold_error_rate = config_manager.getfloat('monitoring', 'alert_threshold_error_rate', 0.1)
        self.alert_notification_channels = config_manager.get('monitoring', 'alert_notification_channels', 'wecom,email').split(',')
        self.metrics_data = {}
        self.alert_history = []
    
    def start(self):
        """启动监控"""
        if self.is_running:
            logger.warning("监控已经在运行中")
            return
        
        try:
            # 启动 Prometheus 指标服务器
            start_http_server(self.metrics_port)
            logger.info(f"Prometheus 指标服务器已启动，端口: {self.metrics_port}")
            
            # 启动监控线程
            self.is_running = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            
            # 启动告警线程
            if self.alert_enabled:
                self.alert_thread = threading.Thread(target=self._alert_loop, daemon=True)
                self.alert_thread.start()
            
            logger.info("系统监控已启动")
            service_up.set(1)
            
        except Exception as e:
            logger.error(f"启动监控时出错: {e}")
            self.is_running = False
            service_up.set(0)
    
    def stop(self):
        """停止监控"""
        if not self.is_running:
            logger.warning("监控未运行")
            return
        
        try:
            self.is_running = False
            
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)
            
            if self.alert_thread:
                self.alert_thread.join(timeout=5)
            
            logger.info("系统监控已停止")
            service_up.set(0)
            
        except Exception as e:
            logger.error(f"停止监控时出错: {e}")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                # 收集系统指标
                self._collect_system_metrics()
                
                # 收集业务指标
                self._collect_business_metrics()
                
                # 收集服务指标
                self._collect_service_metrics()
                
                # 保存监控数据
                self._save_monitoring_data()
                
                # 睡眠一段时间
                time.sleep(60)  # 每分钟收集一次
                
            except Exception as e:
                logger.error(f"监控循环出错: {e}")
                time.sleep(60)
    
    def _alert_loop(self):
        """告警循环"""
        while self.is_running:
            try:
                # 检查告警条件
                self._check_alerts()
                
                # 睡眠一段时间
                time.sleep(300)  # 每5分钟检查一次
                
            except Exception as e:
                logger.error(f"告警循环出错: {e}")
                time.sleep(300)
    
    def _collect_system_metrics(self):
        """收集系统指标"""
        try:
            # CPU 使用率
            cpu_usage = psutil.cpu_percent(interval=1)
            system_cpu_usage.set(cpu_usage)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            system_memory_usage.set(memory_usage)
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            system_disk_usage.set(disk_usage)
            
            # 网络指标
            net_io = psutil.net_io_counters()
            system_network_bytes_sent.inc(net_io.bytes_sent)
            system_network_bytes_recv.inc(net_io.bytes_recv)
            
            self.metrics_data['system'] = {
                'timestamp': datetime.now().isoformat(),
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'disk_usage': disk_usage,
                'network_bytes_sent': net_io.bytes_sent,
                'network_bytes_recv': net_io.bytes_recv
            }
            
            logger.debug(f"系统指标: CPU={cpu_usage:.1f}%, 内存={memory_usage:.1f}%, 磁盘={disk_usage:.1f}%, 发送字节={net_io.bytes_sent}, 接收字节={net_io.bytes_recv}")
            
        except Exception as e:
            logger.error(f"收集系统指标时出错: {e}")
    
    def _collect_business_metrics(self):
        """收集业务指标"""
        try:
            db = next(get_db())
            
            # 数据库连接池状态
            from sqlalchemy import inspect
            inspector = inspect(db.bind)
            pool_size = getattr(inspector.pool, '_pool_size', 0)
            pool_overflow = getattr(inspector.pool, '_max_overflow', 0)
            pool_used = getattr(inspector.pool, '_checkedout', 0)
            database_connections.set(pool_used)
            
            # 消息处理量
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            # 今天的消息数
            today_messages = db.query(Message).filter(
                Message.created_at >= datetime.combine(today, datetime.min.time())
            ).count()
            
            # 昨天的消息数
            yesterday_messages = db.query(Message).filter(
                Message.created_at >= datetime.combine(yesterday, datetime.min.time()),
                Message.created_at < datetime.combine(today, datetime.min.time())
            ).count()
            
            # 咨询数
            today_consultations = db.query(Consultation).filter(
                Consultation.created_at >= datetime.combine(today, datetime.min.time())
            ).count()
            
            # 案例数
            today_cases = db.query(Case).filter(
                Case.created_at >= datetime.combine(today, datetime.min.time())
            ).count()
            
            # 满意度评分
            completed_consultations = db.query(Consultation).filter(
                Consultation.status == 'completed',
                Consultation.satisfaction_score.isnot(None)
            ).all()
            
            avg_satisfaction = 0
            if completed_consultations:
                total_score = sum(c.satisfaction_score for c in completed_consultations)
                avg_satisfaction = total_score / len(completed_consultations)
                satisfaction_score.set(avg_satisfaction)
            
            # 知识库大小
            from modules.knowledge.models import KnowledgeBase
            knowledge_count = db.query(KnowledgeBase).count()
            knowledge_base_size.set(knowledge_count)
            
            # 合同模板数量
            from modules.contract.models import ContractTemplate
            template_count = db.query(ContractTemplate).count()
            contract_templates_total.set(template_count)
            
            self.metrics_data['business'] = {
                'timestamp': datetime.now().isoformat(),
                'today_messages': today_messages,
                'yesterday_messages': yesterday_messages,
                'today_consultations': today_consultations,
                'today_cases': today_cases,
                'avg_satisfaction': avg_satisfaction,
                'knowledge_base_size': knowledge_count,
                'contract_templates_count': template_count,
                'database_connections': pool_used
            }
            
            logger.debug(f"业务指标: 今日消息={today_messages}, 昨日消息={yesterday_messages}, 今日咨询={today_consultations}, 今日案例={today_cases}, 平均满意度={avg_satisfaction:.1f}, 知识库大小={knowledge_count}, 合同模板数={template_count}, 数据库连接数={pool_used}")
            
        except Exception as e:
            logger.error(f"收集业务指标时出错: {e}")
            database_connection_errors.inc()
        finally:
            db.close()
    
    def _collect_service_metrics(self):
        """收集服务指标"""
        try:
            # 模拟响应时间（实际应用中应该测量真实的响应时间）
            response_time = 0.1 + (time.time() % 0.5)  # 模拟 0.1-0.6 秒的响应时间
            service_response_time.set(response_time)
            
            # 服务状态
            service_up.set(1)
            
            # Redis连接状态
            try:
                from modules.message.wechat_service import message_service
                if message_service.redis_client:
                    # 检查Redis连接
                    message_service.redis_client.ping()
                    redis_connections.set(1)
                    
                    # 获取消息队列长度
                    queue_length = message_service.redis_client.llen(message_service.message_queue)
                    message_queue_length.set(queue_length)
                    
                    # 获取处理中队列长度
                    processing_length = message_service.redis_client.scard(message_service.processing_queue)
                    
                    # 获取失败队列长度
                    failed_length = message_service.redis_client.scard(message_service.failed_queue)
                    
                    logger.debug(f"Redis指标: 连接正常, 消息队列长度={queue_length}, 处理中={processing_length}, 失败={failed_length}")
                else:
                    redis_connections.set(0)
                    message_queue_length.set(0)
                    logger.debug("Redis指标: 连接不可用")
            except Exception as e:
                logger.error(f"收集Redis指标时出错: {e}")
                redis_connection_errors.inc()
                redis_connections.set(0)
            
            self.metrics_data['service'] = {
                'timestamp': datetime.now().isoformat(),
                'response_time': response_time,
                'status': 'up'
            }
            
            logger.debug(f"服务指标: 响应时间={response_time:.3f}秒, 状态=up")
            
        except Exception as e:
            logger.error(f"收集服务指标时出错: {e}")
            service_up.set(0)
    
    def _save_monitoring_data(self):
        """保存监控数据"""
        try:
            # 这里可以将监控数据保存到数据库或文件
            # 为了简化，我们只在日志中记录
            logger.debug("监控数据已更新")
            
        except Exception as e:
            logger.error(f"保存监控数据时出错: {e}")
    
    def _check_alerts(self):
        """检查告警条件"""
        try:
            # 检查系统指标
            if 'system' in self.metrics_data:
                system_data = self.metrics_data['system']
                cpu_usage = system_data.get('cpu_usage', 0)
                memory_usage = system_data.get('memory_usage', 0)
                disk_usage = system_data.get('disk_usage', 0)
                
                # CPU 使用率告警
                if cpu_usage > 80:
                    self._trigger_alert('high_cpu_usage', f'CPU使用率过高: {cpu_usage:.1f}%')
                
                # 内存使用率告警
                if memory_usage > 80:
                    self._trigger_alert('high_memory_usage', f'内存使用率过高: {memory_usage:.1f}%')
                
                # 磁盘使用率告警
                if disk_usage > 90:
                    self._trigger_alert('high_disk_usage', f'磁盘使用率过高: {disk_usage:.1f}%')
            
            # 检查服务指标
            if 'service' in self.metrics_data:
                service_data = self.metrics_data['service']
                response_time = service_data.get('response_time', 0)
                
                # 响应时间告警
                if response_time > config_manager.getfloat('monitoring', 'alert_threshold_response_time', 5):
                    self._trigger_alert('high_response_time', f'响应时间过长: {response_time:.3f}秒')
            
            # 检查业务指标
            if 'business' in self.metrics_data:
                business_data = self.metrics_data['business']
                today_messages = business_data.get('today_messages', 0)
                yesterday_messages = business_data.get('yesterday_messages', 1)
                
                # 消息量异常告警（今日消息量是昨日的5倍以上）
                if yesterday_messages > 0 and today_messages > yesterday_messages * 5:
                    self._trigger_alert('abnormal_message_volume', f'消息量异常增长: 今日{today_messages}, 昨日{yesterday_messages}')
            
        except Exception as e:
            logger.error(f"检查告警条件时出错: {e}")
    
    def _trigger_alert(self, alert_type: str, message: str):
        """触发告警
        
        Args:
            alert_type: 告警类型
            message: 告警消息
        """
        try:
            # 检查是否已经告警过（避免重复告警）
            alert_key = f"{alert_type}:{datetime.now().strftime('%Y%m%d%H')}"
            
            # 检查告警历史
            for alert in self.alert_history:
                if alert['key'] == alert_key and (datetime.now() - alert['timestamp']).total_seconds() < 3600:
                    # 1小时内已经告警过，跳过
                    return
            
            # 记录告警
            alert_data = {
                'key': alert_key,
                'type': alert_type,
                'message': message,
                'timestamp': datetime.now(),
                'level': 'warning' if alert_type in ['high_cpu_usage', 'high_memory_usage'] else 'critical'
            }
            
            self.alert_history.append(alert_data)
            
            # 保持告警历史不超过100条
            if len(self.alert_history) > 100:
                self.alert_history = self.alert_history[-100:]
            
            # 发送告警通知
            self._send_alert_notification(alert_data)
            
            logger.warning(f"告警: {alert_type} - {message}")
            
        except Exception as e:
            logger.error(f"触发告警时出错: {e}")
    
    def _send_alert_notification(self, alert_data: Dict[str, Any]):
        """发送告警通知
        
        Args:
            alert_data: 告警数据
        """
        try:
            # 获取通知渠道
            channels = config_manager.get('monitoring', 'alert_notification_channels', 'wecom').split(',')
            
            # 构建通知消息
            notification_message = f"【系统告警】\n类型: {alert_data['type']}\n级别: {alert_data['level']}\n消息: {alert_data['message']}\n时间: {alert_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 根据渠道发送通知
            for channel in channels:
                channel = channel.strip()
                if channel == 'wecom':
                    # 发送企业微信通知
                    self._send_wecom_notification(notification_message)
                elif channel == 'email':
                    # 发送邮件通知
                    self._send_email_notification(notification_message)
            
        except Exception as e:
            logger.error(f"发送告警通知时出错: {e}")
    
    def _send_wecom_notification(self, message: str):
        """发送企业微信通知
        
        Args:
            message: 通知消息
        """
        try:
            # 这里应该调用企业微信API发送通知
            # 为了简化，我们只在日志中记录
            logger.info(f"发送企业微信通知: {message[:100]}...")
            
        except Exception as e:
            logger.error(f"发送企业微信通知时出错: {e}")
    
    def _send_email_notification(self, message: str):
        """发送邮件通知
        
        Args:
            message: 通知消息
        """
        try:
            # 这里应该调用邮件API发送通知
            # 为了简化，我们只在日志中记录
            logger.info(f"发送邮件通知: {message[:100]}...")
            
        except Exception as e:
            logger.error(f"发送邮件通知时出错: {e}")
    
    def get_monitoring_data(self, duration: int = 24) -> Dict[str, Any]:
        """获取监控数据
        
        Args:
            duration: 数据持续时间（小时）
            
        Returns:
            监控数据
        """
        try:
            # 构建响应数据
            response = {
                'timestamp': datetime.now().isoformat(),
                'duration': duration,
                'metrics': self.metrics_data,
                'alerts': [
                    {
                        'type': alert['type'],
                        'message': alert['message'],
                        'timestamp': alert['timestamp'].isoformat(),
                        'level': alert['level']
                    }
                    for alert in self.alert_history
                    if (datetime.now() - alert['timestamp']).total_seconds() < duration * 3600
                ]
            }
            
            return response
            
        except Exception as e:
            logger.error(f"获取监控数据时出错: {e}")
            return {'error': str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态
        
        Returns:
            系统状态
        """
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'monitoring_enabled': self.is_running,
                'service_status': 'up' if service_up._value.get() == 1 else 'down',
                'metrics_port': config_manager.getint('monitoring', 'metrics_port', 8001),
                'alert_enabled': self.alert_enabled
            }
            
            # 添加系统指标
            if 'system' in self.metrics_data:
                status.update(self.metrics_data['system'])
            
            # 添加服务指标
            if 'service' in self.metrics_data:
                status.update(self.metrics_data['service'])
            
            return status
            
        except Exception as e:
            logger.error(f"获取系统状态时出错: {e}")
            return {'error': str(e)}

# 创建监控实例
system_monitor = SystemMonitor()

# 启动监控服务器
def start_monitoring():
    """启动监控"""
    try:
        system_monitor.start()
        logger.info("监控服务已启动")
    except Exception as e:
        logger.error(f"启动监控服务时出错: {e}")

def stop_monitoring():
    """停止监控"""
    try:
        system_monitor.stop()
        logger.info("监控服务已停止")
    except Exception as e:
        logger.error(f"停止监控服务时出错: {e}")

# 记录消息处理指标
def record_message_metric(message_type: str, processing_time: float, error: bool = False):
    """记录消息处理指标
    
    Args:
        message_type: 消息类型
        processing_time: 处理时间
        error: 是否出错
    """
    message_counter.labels(type=message_type).inc()
    message_processing_time.observe(processing_time)
    if error:
        message_error_counter.inc()

# 记录咨询指标
def record_consultation_metric(status: str):
    """记录咨询指标
    
    Args:
        status: 咨询状态
    """
    consultation_counter.labels(status=status).inc()

# 记录案例指标
def record_case_metric(status: str):
    """记录案例指标
    
    Args:
        status: 案例状态
    """
    case_counter.labels(status=status).inc()
