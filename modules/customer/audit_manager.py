import logging
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from utils.database import get_db
from modules.customer.models import AIAudit

logger = logging.getLogger(__name__)

class AuditManager:
    """审核管理器"""
    
    def __init__(self):
        # 审核状态定义
        self.AUDIT_STATUS = {
            'PENDING': 'pending',      # 待审核
            'APPROVED': 'approved',    # 已通过
            'REJECTED': 'rejected',    # 已拒绝
            'EXPIRED': 'expired'       # 已过期
        }
        
        # 操作类型定义
        self.OPERATION_TYPES = {
            'CUSTOMER_CATEGORY': 'customer_category_prediction',
            'CHURN_RISK': 'churn_risk_prediction',
            'TAG_SUGGESTION': 'tag_suggestion',
            'CUSTOMER_VALUE': 'customer_value_calculation',
            'CUSTOMER_NEEDS': 'customer_needs_prediction',
            'FOLLOW_UP': 'follow_up_suggestion'
        }
        
        # 优先级定义
        self.PRIORITIES = {
            'LOW': 'low',
            'MEDIUM': 'medium',
            'HIGH': 'high',
            'URGENT': 'urgent'
        }
    
    def create_audit(self, operation_type: str, target_id: int, data: Dict[str, Any], 
                    description: str = None, priority: str = 'medium') -> AIAudit:
        """创建审核记录
        
        Args:
            operation_type: 操作类型
            target_id: 目标ID（如客户ID）
            data: 审核数据
            description: 审核描述
            priority: 优先级
            
        Returns:
            创建的审核记录
        """
        db = next(get_db())
        try:
            # 生成审核ID
            audit_id = f"AUDIT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{target_id}_{operation_type[:3]}"
            
            # 创建审核记录
            audit = AIAudit(
                audit_id=audit_id,
                operation_type=operation_type,
                target_id=target_id,
                status=self.AUDIT_STATUS['PENDING'],
                priority=priority,
                data=json.dumps(data, ensure_ascii=False),
                description=description,
                created_at=datetime.now()
            )
            
            db.add(audit)
            db.commit()
            db.refresh(audit)
            
            logger.info(f"创建审核记录成功: {audit_id} - {operation_type}")
            
            # 发送审核通知
            self._send_audit_notification(audit)
            
            return audit
        except Exception as e:
            db.rollback()
            logger.error(f"创建审核记录时出错: {e}")
            raise
        finally:
            db.close()
    
    def approve_audit(self, audit_id: int, approver_id: int, comments: str = None) -> AIAudit:
        """通过审核
        
        Args:
            audit_id: 审核ID
            approver_id: 审核人ID
            comments: 审核意见
            
        Returns:
            更新后的审核记录
        """
        db = next(get_db())
        try:
            # 查找审核记录
            audit = db.query(AIAudit).filter(AIAudit.id == audit_id).first()
            if not audit:
                raise ValueError(f"审核记录不存在: {audit_id}")
            
            if audit.status != self.AUDIT_STATUS['PENDING']:
                raise ValueError(f"审核记录状态不是待审核: {audit.status}")
            
            # 更新审核状态
            audit.status = self.AUDIT_STATUS['APPROVED']
            audit.approver_id = approver_id
            audit.approval_comments = comments
            audit.approval_time = datetime.now()
            audit.updated_at = datetime.now()
            
            db.commit()
            db.refresh(audit)
            
            logger.info(f"审核通过: {audit.audit_id} - {audit.operation_type}")
            
            # 执行审核通过后的操作
            self._execute_approved_operation(audit)
            
            return audit
        except Exception as e:
            db.rollback()
            logger.error(f"通过审核时出错: {e}")
            raise
        finally:
            db.close()
    
    def reject_audit(self, audit_id: int, approver_id: int, comments: str = None) -> AIAudit:
        """拒绝审核
        
        Args:
            audit_id: 审核ID
            approver_id: 审核人ID
            comments: 拒绝原因
            
        Returns:
            更新后的审核记录
        """
        db = next(get_db())
        try:
            # 查找审核记录
            audit = db.query(AIAudit).filter(AIAudit.id == audit_id).first()
            if not audit:
                raise ValueError(f"审核记录不存在: {audit_id}")
            
            if audit.status != self.AUDIT_STATUS['PENDING']:
                raise ValueError(f"审核记录状态不是待审核: {audit.status}")
            
            # 更新审核状态
            audit.status = self.AUDIT_STATUS['REJECTED']
            audit.approver_id = approver_id
            audit.approval_comments = comments
            audit.approval_time = datetime.now()
            audit.updated_at = datetime.now()
            
            db.commit()
            db.refresh(audit)
            
            logger.info(f"审核拒绝: {audit.audit_id} - {audit.operation_type}")
            
            return audit
        except Exception as e:
            db.rollback()
            logger.error(f"拒绝审核时出错: {e}")
            raise
        finally:
            db.close()
    
    def get_audit(self, audit_id: int) -> Optional[AIAudit]:
        """获取审核记录
        
        Args:
            audit_id: 审核ID
            
        Returns:
            审核记录
        """
        db = next(get_db())
        try:
            return db.query(AIAudit).filter(AIAudit.id == audit_id).first()
        finally:
            db.close()
    
    def get_audit_by_audit_id(self, audit_id: str) -> Optional[AIAudit]:
        """通过审核ID获取审核记录
        
        Args:
            audit_id: 审核ID字符串
            
        Returns:
            审核记录
        """
        db = next(get_db())
        try:
            return db.query(AIAudit).filter(AIAudit.audit_id == audit_id).first()
        finally:
            db.close()
    
    def list_audits(self, **filters) -> List[AIAudit]:
        """列出审核记录
        
        Args:
            filters: 过滤条件
            
        Returns:
            审核记录列表
        """
        db = next(get_db())
        try:
            query = db.query(AIAudit)
            
            # 应用过滤条件
            if 'status' in filters:
                query = query.filter(AIAudit.status == filters['status'])
            
            if 'operation_type' in filters:
                query = query.filter(AIAudit.operation_type == filters['operation_type'])
            
            if 'target_id' in filters:
                query = query.filter(AIAudit.target_id == filters['target_id'])
            
            if 'priority' in filters:
                query = query.filter(AIAudit.priority == filters['priority'])
            
            if 'start_date' in filters:
                query = query.filter(AIAudit.created_at >= filters['start_date'])
            
            if 'end_date' in filters:
                query = query.filter(AIAudit.created_at <= filters['end_date'])
            
            # 排序
            order_by = filters.get('order_by', 'created_at')
            order_desc = filters.get('order_desc', True)
            
            if order_desc:
                query = query.order_by(getattr(AIAudit, order_by).desc())
            else:
                query = query.order_by(getattr(AIAudit, order_by).asc())
            
            # 分页
            limit = filters.get('limit', 100)
            offset = filters.get('offset', 0)
            
            return query.offset(offset).limit(limit).all()
        finally:
            db.close()
    
    def get_pending_audits(self, priority: str = None, limit: int = 50) -> List[AIAudit]:
        """获取待审核记录
        
        Args:
            priority: 优先级过滤
            limit: 限制数量
            
        Returns:
            待审核记录列表
        """
        filters = {
            'status': self.AUDIT_STATUS['PENDING'],
            'limit': limit,
            'order_by': 'priority',
            'order_desc': True
        }
        
        if priority:
            filters['priority'] = priority
        
        return self.list_audits(**filters)
    
    def update_audit_status(self, audit_id: int, status: str, comments: str = None) -> AIAudit:
        """更新审核状态
        
        Args:
            audit_id: 审核ID
            status: 新状态
            comments: 备注
            
        Returns:
            更新后的审核记录
        """
        db = next(get_db())
        try:
            # 查找审核记录
            audit = db.query(AIAudit).filter(AIAudit.id == audit_id).first()
            if not audit:
                raise ValueError(f"审核记录不存在: {audit_id}")
            
            # 更新状态
            audit.status = status
            if comments:
                audit.approval_comments = comments
            audit.updated_at = datetime.now()
            
            db.commit()
            db.refresh(audit)
            
            logger.info(f"更新审核状态: {audit.audit_id} - {status}")
            
            return audit
        except Exception as e:
            db.rollback()
            logger.error(f"更新审核状态时出错: {e}")
            raise
        finally:
            db.close()
    
    def expire_old_audits(self, days: int = 7) -> int:
        """过期旧审核记录
        
        Args:
            days: 过期天数
            
        Returns:
            过期的记录数量
        """
        db = next(get_db())
        try:
            # 计算过期时间
            expire_time = datetime.now() - timedelta(days=days)
            
            # 查找过期的待审核记录
            audits = db.query(AIAudit).filter(
                AIAudit.status == self.AUDIT_STATUS['PENDING'],
                AIAudit.created_at < expire_time
            ).all()
            
            # 更新状态
            expired_count = 0
            for audit in audits:
                audit.status = self.AUDIT_STATUS['EXPIRED']
                audit.updated_at = datetime.now()
                expired_count += 1
            
            db.commit()
            
            logger.info(f"过期审核记录: {expired_count} 条")
            
            return expired_count
        except Exception as e:
            db.rollback()
            logger.error(f"过期审核记录时出错: {e}")
            raise
        finally:
            db.close()
    
    def get_audit_statistics(self, days: int = 30) -> Dict[str, Any]:
        """获取审核统计
        
        Args:
            days: 统计天数
            
        Returns:
            统计数据
        """
        db = next(get_db())
        try:
            # 计算统计开始时间
            start_time = datetime.now() - timedelta(days=days)
            
            # 总审核数
            total_audits = db.query(AIAudit).filter(
                AIAudit.created_at >= start_time
            ).count()
            
            # 按状态统计
            status_stats = {}
            for status in self.AUDIT_STATUS.values():
                count = db.query(AIAudit).filter(
                    AIAudit.created_at >= start_time,
                    AIAudit.status == status
                ).count()
                status_stats[status] = count
            
            # 按操作类型统计
            type_stats = {}
            audits_by_type = db.query(
                AIAudit.operation_type,
                db.func.count(AIAudit.id)
            ).filter(
                AIAudit.created_at >= start_time
            ).group_by(AIAudit.operation_type).all()
            
            for operation_type, count in audits_by_type:
                type_stats[operation_type] = count
            
            # 按优先级统计
            priority_stats = {}
            audits_by_priority = db.query(
                AIAudit.priority,
                db.func.count(AIAudit.id)
            ).filter(
                AIAudit.created_at >= start_time
            ).group_by(AIAudit.priority).all()
            
            for priority, count in audits_by_priority:
                priority_stats[priority] = count
            
            # 平均审核时间
            approved_audits = db.query(AIAudit).filter(
                AIAudit.created_at >= start_time,
                AIAudit.status == self.AUDIT_STATUS['APPROVED'],
                AIAudit.approval_time.isnot(None)
            ).all()
            
            avg_processing_time = 0
            if approved_audits:
                total_time = sum(
                    (audit.approval_time - audit.created_at).total_seconds()
                    for audit in approved_audits
                )
                avg_processing_time = total_time / len(approved_audits)
            
            return {
                'total_audits': total_audits,
                'status_stats': status_stats,
                'type_stats': type_stats,
                'priority_stats': priority_stats,
                'avg_processing_time_seconds': avg_processing_time,
                'start_time': start_time.isoformat(),
                'end_time': datetime.now().isoformat()
            }
        finally:
            db.close()
    
    def batch_approve_audits(self, audit_ids: List[int], approver_id: int, comments: str = None) -> int:
        """批量通过审核
        
        Args:
            audit_ids: 审核ID列表
            approver_id: 审核人ID
            comments: 审核意见
            
        Returns:
            通过的审核数量
        """
        approved_count = 0
        
        for audit_id in audit_ids:
            try:
                self.approve_audit(audit_id, approver_id, comments)
                approved_count += 1
            except Exception as e:
                logger.error(f"批量通过审核时出错 (ID: {audit_id}): {e}")
        
        return approved_count
    
    def batch_reject_audits(self, audit_ids: List[int], approver_id: int, comments: str = None) -> int:
        """批量拒绝审核
        
        Args:
            audit_ids: 审核ID列表
            approver_id: 审核人ID
            comments: 拒绝原因
            
        Returns:
            拒绝的审核数量
        """
        rejected_count = 0
        
        for audit_id in audit_ids:
            try:
                self.reject_audit(audit_id, approver_id, comments)
                rejected_count += 1
            except Exception as e:
                logger.error(f"批量拒绝审核时出错 (ID: {audit_id}): {e}")
        
        return rejected_count
    
    # 内部方法
    def _send_audit_notification(self, audit: AIAudit):
        """发送审核通知
        
        Args:
            audit: 审核记录
        """
        try:
            # 构建通知消息
            notification_message = f"【新审核通知】\n"
            notification_message += f"审核ID: {audit.audit_id}\n"
            notification_message += f"操作类型: {audit.operation_type}\n"
            notification_message += f"目标ID: {audit.target_id}\n"
            notification_message += f"优先级: {audit.priority}\n"
            notification_message += f"创建时间: {audit.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            if audit.description:
                notification_message += f"描述: {audit.description}\n"
            
            # 这里可以集成到消息系统发送通知
            # 例如发送到企业微信、邮件等
            logger.info(f"发送审核通知: {notification_message[:100]}...")
            
        except Exception as e:
            logger.error(f"发送审核通知时出错: {e}")
    
    def _execute_approved_operation(self, audit: AIAudit):
        """执行审核通过后的操作
        
        Args:
            audit: 审核记录
        """
        try:
            # 解析审核数据
            data = json.loads(audit.data)
            operation_type = audit.operation_type
            target_id = audit.target_id
            
            logger.info(f"执行审核通过操作: {operation_type} - 目标ID: {target_id}")
            
            # 根据操作类型执行不同的操作
            if operation_type == self.OPERATION_TYPES['CUSTOMER_CATEGORY']:
                # 更新客户分类
                self._update_customer_category(target_id, data)
                
            elif operation_type == self.OPERATION_TYPES['CHURN_RISK']:
                # 处理流失风险预警
                self._handle_churn_risk(target_id, data)
                
            elif operation_type == self.OPERATION_TYPES['TAG_SUGGESTION']:
                # 应用标签建议
                self._apply_tag_suggestions(target_id, data)
                
            elif operation_type == self.OPERATION_TYPES['CUSTOMER_VALUE']:
                # 更新客户价值
                self._update_customer_value(target_id, data)
                
            elif operation_type == self.OPERATION_TYPES['CUSTOMER_NEEDS']:
                # 处理客户需求
                self._handle_customer_needs(target_id, data)
                
            elif operation_type == self.OPERATION_TYPES['FOLLOW_UP']:
                # 处理跟进建议
                self._handle_follow_up_suggestions(target_id, data)
                
        except Exception as e:
            logger.error(f"执行审核通过操作时出错: {e}")
    
    def _update_customer_category(self, customer_id: int, data: Dict[str, Any]):
        """更新客户分类
        
        Args:
            customer_id: 客户ID
            data: 分类数据
        """
        db = next(get_db())
        try:
            from modules.customer.models import Customer
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                customer.customer_category = data.get('category')
                customer.last_ai_analysis = datetime.now()
                db.commit()
                logger.info(f"更新客户分类: {customer_id} -> {data.get('category')}")
        except Exception as e:
            db.rollback()
            logger.error(f"更新客户分类时出错: {e}")
        finally:
            db.close()
    
    def _handle_churn_risk(self, customer_id: int, data: Dict[str, Any]):
        """处理流失风险预警
        
        Args:
            customer_id: 客户ID
            data: 风险数据
        """
        db = next(get_db())
        try:
            from modules.customer.models import Customer
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                customer.churn_risk = data.get('risk_level')
                customer.churn_risk_score = data.get('risk_score')
                customer.last_ai_analysis = datetime.now()
                db.commit()
                logger.info(f"处理客户流失风险: {customer_id} -> {data.get('risk_level')}")
        except Exception as e:
            db.rollback()
            logger.error(f"处理客户流失风险时出错: {e}")
        finally:
            db.close()
    
    def _apply_tag_suggestions(self, customer_id: int, data: Dict[str, Any]):
        """应用标签建议
        
        Args:
            customer_id: 客户ID
            data: 标签建议数据
        """
        db = next(get_db())
        try:
            from modules.customer.models import Customer, CustomerTag
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                tag_suggestions = data.get('tag_suggestions', [])
                for tag_suggestion in tag_suggestions:
                    # 检查标签是否存在
                    tag = db.query(CustomerTag).filter(
                        CustomerTag.name == tag_suggestion['name']
                    ).first()
                    if not tag:
                        # 创建新标签
                        tag = CustomerTag(
                            name=tag_suggestion['name'],
                            description=f"AI生成标签 - 置信度: {tag_suggestion.get('confidence', 0)}"
                        )
                        db.add(tag)
                    
                    # 添加标签到客户
                    if tag not in customer.tags:
                        customer.tags.append(tag)
                
                customer.last_ai_analysis = datetime.now()
                db.commit()
                logger.info(f"应用标签建议: {customer_id} -> {len(tag_suggestions)}个标签")
        except Exception as e:
            db.rollback()
            logger.error(f"应用标签建议时出错: {e}")
        finally:
            db.close()
    
    def _update_customer_value(self, customer_id: int, data: Dict[str, Any]):
        """更新客户价值
        
        Args:
            customer_id: 客户ID
            data: 价值评估数据
        """
        db = next(get_db())
        try:
            from modules.customer.models import Customer
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                customer.customer_value = data.get('value_level')
                customer.customer_value_score = data.get('value_score')
                customer.predicted_lifetime_value = data.get('predicted_lifetime_value')
                customer.last_ai_analysis = datetime.now()
                db.commit()
                logger.info(f"更新客户价值: {customer_id} -> {data.get('value_level')}")
        except Exception as e:
            db.rollback()
            logger.error(f"更新客户价值时出错: {e}")
        finally:
            db.close()
    
    def _handle_customer_needs(self, customer_id: int, data: Dict[str, Any]):
        """处理客户需求
        
        Args:
            customer_id: 客户ID
            data: 需求预测数据
        """
        try:
            # 这里可以实现更复杂的需求处理逻辑
            # 例如创建服务建议、推荐相关服务等
            needs = data.get('needs', [])
            logger.info(f"处理客户需求: {customer_id} -> {len(needs)}个需求")
            
            # 可以在这里发送需求通知给相关人员
            if needs:
                notification_message = f"客户 {customer_id} 的需求预测:\n"
                for need in needs:
                    notification_message += f"- {need['need']} (置信度: {need['confidence']})\n"
                    notification_message += f"  原因: {need['reason']}\n"
                logger.info(f"发送需求通知: {notification_message[:100]}...")
        except Exception as e:
            logger.error(f"处理客户需求时出错: {e}")
    
    def _handle_follow_up_suggestions(self, customer_id: int, data: Dict[str, Any]):
        """处理跟进建议
        
        Args:
            customer_id: 客户ID
            data: 跟进建议数据
        """
        try:
            # 这里可以实现更复杂的跟进处理逻辑
            # 例如创建跟进任务、发送提醒等
            follow_up_suggestions = data.get('follow_up_suggestions', [])
            logger.info(f"处理跟进建议: {customer_id} -> {len(follow_up_suggestions)}个建议")
            
            # 可以在这里创建跟进任务
            for suggestion in follow_up_suggestions:
                logger.info(f"创建跟进任务: {suggestion['type']} - 优先级: {suggestion['priority']}")
                logger.info(f"内容: {suggestion['content']}")
                logger.info(f"时间要求: {suggestion['timing']}")
        except Exception as e:
            logger.error(f"处理跟进建议时出错: {e}")

# 创建审核管理器实例
audit_manager = AuditManager()