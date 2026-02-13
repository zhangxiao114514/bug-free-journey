import logging
import threading
import time
import schedule
from datetime import datetime, timedelta
from typing import List

from modules.customer.ai_customer_manager import ai_customer_manager
from modules.customer.audit_manager import audit_manager
from utils.database import get_db
from utils.config import config_manager

logger = logging.getLogger(__name__)

class CustomerTasks:
    """客户管理后台任务"""
    
    def __init__(self):
        self.is_running = False
        self.task_thread = None
        self.scheduled_tasks = []
        
        # 加载配置
        self.analysis_interval = config_manager.getint('ai', 'analysis_interval', 3600)
        self.max_customers_per_batch = config_manager.getint('ai', 'max_customers_per_batch', 100)
        
        logger.info(f"客户后台任务初始化完成: 分析间隔={self.analysis_interval}秒")
    
    def start(self):
        """启动后台任务"""
        if self.is_running:
            logger.warning("后台任务已经在运行中")
            return
        
        try:
            self.is_running = True
            
            # 初始化任务
            self._init_scheduled_tasks()
            
            # 启动任务线程
            self.task_thread = threading.Thread(target=self._task_loop, daemon=True)
            self.task_thread.start()
            
            logger.info("客户管理后台任务已启动")
            
        except Exception as e:
            logger.error(f"启动后台任务时出错: {e}")
            self.is_running = False
    
    def stop(self):
        """停止后台任务"""
        if not self.is_running:
            logger.warning("后台任务未运行")
            return
        
        try:
            self.is_running = False
            
            if self.task_thread:
                self.task_thread.join(timeout=5)
            
            logger.info("客户管理后台任务已停止")
            
        except Exception as e:
            logger.error(f"停止后台任务时出错: {e}")
    
    def _init_scheduled_tasks(self):
        """初始化定时任务"""
        # 每天凌晨2点执行客户分析
        schedule.every().day.at("02:00").do(self._perform_daily_customer_analysis)
        
        # 每小时执行审核过期检查
        schedule.every().hour.do(self._check_expired_audits)
        
        # 每周一凌晨3点执行模型更新
        schedule.every().monday.at("03:00").do(self._update_ai_models)
        
        # 每15分钟执行高风险客户检查
        schedule.every(15).minutes.do(self._check_high_risk_customers)
        
        logger.info("定时任务已初始化")
    
    def _task_loop(self):
        """任务循环"""
        while self.is_running:
            try:
                # 运行所有待执行的任务
                schedule.run_pending()
                
                # 睡眠1秒
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"任务循环出错: {e}")
                time.sleep(10)
    
    def _perform_daily_customer_analysis(self):
        """执行每日客户分析"""
        logger.info("开始执行每日客户分析任务")
        
        try:
            # 获取需要分析的客户列表
            customer_ids = self._get_customers_to_analyze()
            
            if not customer_ids:
                logger.info("没有客户需要分析")
                return
            
            logger.info(f"开始分析 {len(customer_ids)} 个客户")
            
            # 批量分析客户
            results = ai_customer_manager.batch_analyze_customers(customer_ids)
            
            # 记录分析结果
            analyzed_count = sum(1 for result in results if 'error' not in result)
            error_count = sum(1 for result in results if 'error' in result)
            
            logger.info(f"每日客户分析完成: 成功 {analyzed_count}, 失败 {error_count}")
            
        except Exception as e:
            logger.error(f"执行每日客户分析时出错: {e}")
    
    def _check_expired_audits(self):
        """检查过期审核"""
        logger.info("开始检查过期审核")
        
        try:
            # 过期7天的审核
            expired_count = audit_manager.expire_old_audits(days=7)
            logger.info(f"审核过期检查完成: 过期 {expired_count} 条记录")
            
        except Exception as e:
            logger.error(f"检查过期审核时出错: {e}")
    
    def _update_ai_models(self):
        """更新AI模型"""
        logger.info("开始更新AI模型")
        
        try:
            # 这里可以实现模型更新逻辑
            # 例如重新训练分类模型、更新特征权重等
            
            logger.info("AI模型更新完成")
            
        except Exception as e:
            logger.error(f"更新AI模型时出错: {e}")
    
    def _check_high_risk_customers(self):
        """检查高风险客户"""
        logger.info("开始检查高风险客户")
        
        try:
            # 获取高风险客户
            high_risk_customers = self._get_high_risk_customers()
            
            if not high_risk_customers:
                logger.info("没有高风险客户")
                return
            
            logger.info(f"发现 {len(high_risk_customers)} 个高风险客户")
            
            # 为高风险客户生成跟进建议
            for customer_id in high_risk_customers:
                try:
                    # 生成跟进建议
                    follow_up = ai_customer_manager.suggest_follow_up(customer_id)
                    logger.info(f"为高风险客户 {customer_id} 生成跟进建议")
                except Exception as e:
                    logger.error(f"为客户 {customer_id} 生成跟进建议时出错: {e}")
            
        except Exception as e:
            logger.error(f"检查高风险客户时出错: {e}")
    
    def _get_customers_to_analyze(self) -> List[int]:
        """获取需要分析的客户列表
        
        Returns:
            客户ID列表
        """
        db = next(get_db())
        try:
            from modules.customer.models import Customer
            
            # 获取最近30天有活动的客户
            cutoff_date = datetime.now() - timedelta(days=30)
            
            customers = db.query(Customer).filter(
                Customer.updated_at >= cutoff_date,
                Customer.status == 'active'
            ).all()
            
            return [customer.id for customer in customers]
        finally:
            db.close()
    
    def _get_high_risk_customers(self) -> List[int]:
        """获取高风险客户列表
        
        Returns:
            客户ID列表
        """
        db = next(get_db())
        try:
            from modules.customer.models import Customer
            
            # 获取流失风险为高的客户
            customers = db.query(Customer).filter(
                Customer.churn_risk == '高',
                Customer.status == 'active'
            ).all()
            
            return [customer.id for customer in customers]
        finally:
            db.close()
    
    def run_analysis_for_customer(self, customer_id: int):
        """手动触发客户分析
        
        Args:
            customer_id: 客户ID
        """
        try:
            # 分析客户
            analysis = {
                'category': ai_customer_manager.predict_customer_category(customer_id),
                'churn_risk': ai_customer_manager.predict_churn_risk(customer_id),
                'value': ai_customer_manager.calculate_customer_value(customer_id),
                'needs': ai_customer_manager.predict_customer_needs(customer_id),
                'follow_up': ai_customer_manager.suggest_follow_up(customer_id)
            }
            
            logger.info(f"手动分析客户 {customer_id} 完成")
            return analysis
        except Exception as e:
            logger.error(f"手动分析客户 {customer_id} 时出错: {e}")
            raise

# 创建后台任务实例
customer_tasks = CustomerTasks()

# 启动后台任务
def start_customer_tasks():
    """启动客户管理后台任务"""
    try:
        customer_tasks.start()
        logger.info("客户管理后台任务启动成功")
    except Exception as e:
        logger.error(f"启动客户管理后台任务时出错: {e}")

# 停止后台任务
def stop_customer_tasks():
    """停止客户管理后台任务"""
    try:
        customer_tasks.stop()
        logger.info("客户管理后台任务停止成功")
    except Exception as e:
        logger.error(f"停止客户管理后台任务时出错: {e}")