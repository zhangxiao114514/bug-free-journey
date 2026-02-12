import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from utils.database import get_db
from modules.consultation.models import Consultation, ConsultationProgress

logger = logging.getLogger(__name__)

class ConsultationManager:
    """咨询管理器"""
    
    def __init__(self):
        pass
    
    def create_consultation(self, data: Dict[str, Any]) -> Consultation:
        """创建咨询
        
        Args:
            data: 咨询数据
            
        Returns:
            创建的咨询
        """
        db = next(get_db())
        try:
            # 生成咨询ID
            consultation_id = f"CONSULT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
            
            # 创建咨询
            consultation = Consultation(
                consultation_id=consultation_id,
                customer_id=data['customer_id'],
                user_id=data.get('user_id'),
                title=data['title'],
                description=data.get('description'),
                category=data.get('category'),
                priority=data.get('priority', 0)
            )
            
            db.add(consultation)
            db.commit()
            db.refresh(consultation)
            
            # 创建初始进度
            self._create_initial_progress(consultation)
            
            logger.info(f"创建咨询成功: {consultation.title}")
            return consultation
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建咨询时出错: {e}")
            raise
        finally:
            db.close()
    
    def _create_initial_progress(self, consultation: Consultation):
        """创建初始进度
        
        Args:
            consultation: 咨询对象
        """
        db = next(get_db())
        try:
            # 创建受理阶段
            progress = ConsultationProgress(
                consultation_id=consultation.id,
                stage="受理",
                status="in_progress",
                description="咨询已受理，正在等待处理"
            )
            db.add(progress)
            db.commit()
        finally:
            db.close()
    
    def update_consultation(self, consultation_id: int, data: Dict[str, Any]) -> Consultation:
        """更新咨询信息
        
        Args:
            consultation_id: 咨询ID
            data: 更新数据
            
        Returns:
            更新后的咨询
        """
        db = next(get_db())
        try:
            # 查找咨询
            consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
            if not consultation:
                raise ValueError(f"咨询不存在: {consultation_id}")
            
            # 更新字段
            for key, value in data.items():
                if hasattr(consultation, key):
                    setattr(consultation, key, value)
            
            consultation.updated_at = datetime.now()
            db.commit()
            db.refresh(consultation)
            
            logger.info(f"更新咨询成功: {consultation.title}")
            return consultation
            
        except Exception as e:
            db.rollback()
            logger.error(f"更新咨询时出错: {e}")
            raise
        finally:
            db.close()
    
    def assign_consultation(self, consultation_id: int, user_id: int) -> Consultation:
        """分配咨询
        
        Args:
            consultation_id: 咨询ID
            user_id: 分配的用户ID
            
        Returns:
            分配后的咨询
        """
        return self.update_consultation(consultation_id, {'user_id': user_id})
    
    def update_progress(self, consultation_id: int, stage: str, status: str, description: str = None) -> ConsultationProgress:
        """更新咨询进度
        
        Args:
            consultation_id: 咨询ID
            stage: 阶段
            status: 状态
            description: 描述
            
        Returns:
            更新后的进度
        """
        db = next(get_db())
        try:
            # 查找咨询
            consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
            if not consultation:
                raise ValueError(f"咨询不存在: {consultation_id}")
            
            # 查找或创建进度
            progress = db.query(ConsultationProgress).filter(
                ConsultationProgress.consultation_id == consultation_id,
                ConsultationProgress.stage == stage
            ).first()
            
            if not progress:
                # 创建新进度
                progress = ConsultationProgress(
                    consultation_id=consultation_id,
                    stage=stage,
                    status=status,
                    description=description
                )
                db.add(progress)
            else:
                # 更新现有进度
                progress.status = status
                if description:
                    progress.description = description
                
                if status == "completed":
                    progress.completed_at = datetime.now()
            
            db.commit()
            db.refresh(progress)
            
            # 更新咨询状态
            self._update_consultation_status(consultation)
            
            logger.info(f"更新咨询进度: {consultation.title} - {stage} - {status}")
            return progress
            
        except Exception as e:
            db.rollback()
            logger.error(f"更新咨询进度时出错: {e}")
            raise
        finally:
            db.close()
    
    def _update_consultation_status(self, consultation: Consultation):
        """更新咨询状态
        
        Args:
            consultation: 咨询对象
        """
        db = next(get_db())
        try:
            # 获取所有进度
            progresses = db.query(ConsultationProgress).filter(
                ConsultationProgress.consultation_id == consultation.id
            ).all()
            
            if not progresses:
                return
            
            # 检查是否所有进度都已完成
            all_completed = all(p.status == "completed" for p in progresses)
            
            if all_completed:
                consultation.status = "completed"
                consultation.completed_at = datetime.now()
            else:
                consultation.status = "processing"
            
            db.commit()
        finally:
            db.close()
    
    def get_consultation(self, consultation_id: int) -> Optional[Consultation]:
        """获取咨询信息
        
        Args:
            consultation_id: 咨询ID
            
        Returns:
            咨询信息
        """
        db = next(get_db())
        try:
            return db.query(Consultation).filter(Consultation.id == consultation_id).first()
        finally:
            db.close()
    
    def list_consultations(self, **filters) -> List[Consultation]:
        """列出咨询
        
        Args:
            filters: 过滤条件
            
        Returns:
            咨询列表
        """
        db = next(get_db())
        try:
            query = db.query(Consultation)
            
            # 应用过滤条件
            if 'status' in filters:
                query = query.filter(Consultation.status == filters['status'])
            if 'customer_id' in filters:
                query = query.filter(Consultation.customer_id == filters['customer_id'])
            if 'user_id' in filters:
                query = query.filter(Consultation.user_id == filters['user_id'])
            if 'category' in filters:
                query = query.filter(Consultation.category == filters['category'])
            if 'priority' in filters:
                query = query.filter(Consultation.priority == filters['priority'])
            
            # 排序
            query = query.order_by(Consultation.created_at.desc())
            
            return query.all()
        finally:
            db.close()
    
    def get_consultation_progress(self, consultation_id: int) -> List[ConsultationProgress]:
        """获取咨询进度
        
        Args:
            consultation_id: 咨询ID
            
        Returns:
            进度列表
        """
        db = next(get_db())
        try:
            return db.query(ConsultationProgress).filter(
                ConsultationProgress.consultation_id == consultation_id
            ).order_by(ConsultationProgress.id).all()
        finally:
            db.close()
    
    def escalate_to_human(self, consultation_id: int, reason: str) -> Consultation:
        """升级到人工客服
        
        Args:
            consultation_id: 咨询ID
            reason: 升级原因
            
        Returns:
            升级后的咨询
        """
        db = next(get_db())
        try:
            # 查找咨询
            consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
            if not consultation:
                raise ValueError(f"咨询不存在: {consultation_id}")
            
            # 更新咨询状态
            consultation.status = "processing"
            consultation.description = f"{consultation.description}\n\n【升级原因】: {reason}" if consultation.description else f"【升级原因】: {reason}"
            
            # 创建人工处理进度
            progress = ConsultationProgress(
                consultation_id=consultation_id,
                stage="人工处理",
                status="in_progress",
                description=f"咨询已升级到人工客服，原因: {reason}"
            )
            db.add(progress)
            
            db.commit()
            db.refresh(consultation)
            
            logger.info(f"咨询已升级到人工客服: {consultation.title}")
            return consultation
            
        except Exception as e:
            db.rollback()
            logger.error(f"升级咨询时出错: {e}")
            raise
        finally:
            db.close()
    
    def complete_consultation(self, consultation_id: int, satisfaction_score: Optional[int] = None, feedback: Optional[str] = None) -> Consultation:
        """完成咨询
        
        Args:
            consultation_id: 咨询ID
            satisfaction_score: 满意度评分
            feedback: 客户反馈
            
        Returns:
            完成后的咨询
        """
        db = next(get_db())
        try:
            # 查找咨询
            consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
            if not consultation:
                raise ValueError(f"咨询不存在: {consultation_id}")
            
            # 更新咨询信息
            consultation.status = "completed"
            consultation.completed_at = datetime.now()
            
            if satisfaction_score is not None:
                consultation.satisfaction_score = satisfaction_score
            
            if feedback:
                consultation.feedback = feedback
            
            # 更新所有进度为完成
            progresses = db.query(ConsultationProgress).filter(
                ConsultationProgress.consultation_id == consultation_id
            ).all()
            
            for progress in progresses:
                if progress.status != "completed":
                    progress.status = "completed"
                    progress.completed_at = datetime.now()
            
            # 创建反馈阶段
            feedback_progress = ConsultationProgress(
                consultation_id=consultation_id,
                stage="反馈",
                status="completed",
                description="咨询已完成，感谢您的反馈"
            )
            db.add(feedback_progress)
            
            db.commit()
            db.refresh(consultation)
            
            logger.info(f"完成咨询: {consultation.title}")
            return consultation
            
        except Exception as e:
            db.rollback()
            logger.error(f"完成咨询时出错: {e}")
            raise
        finally:
            db.close()
    
    def get_pending_consultations(self) -> List[Consultation]:
        """获取待处理的咨询
        
        Returns:
            待处理咨询列表
        """
        db = next(get_db())
        try:
            return db.query(Consultation).filter(
                Consultation.status.in_(["pending", "processing"])
            ).order_by(Consultation.priority.desc(), Consultation.created_at.asc()).all()
        finally:
            db.close()
    
    def get_overdue_consultations(self, max_wait_time: int = 300) -> List[Consultation]:
        """获取超时的咨询
        
        Args:
            max_wait_time: 最大等待时间（秒）
            
        Returns:
            超时咨询列表
        """
        db = next(get_db())
        try:
            from sqlalchemy import func
            
            # 计算超时时间
            timeout_threshold = datetime.now() - timedelta(seconds=max_wait_time)
            
            # 查询超时咨询
            consultations = db.query(Consultation).filter(
                Consultation.status.in_(["pending", "processing"]),
                Consultation.created_at < timeout_threshold
            ).order_by(Consultation.created_at.asc()).all()
            
            return consultations
            
        except Exception as e:
            logger.error(f"获取超时咨询时出错: {e}")
            return []
        finally:
            db.close()
    
    def calculate_average_response_time(self) -> float:
        """计算平均响应时间
        
        Returns:
            平均响应时间（秒）
        """
        db = next(get_db())
        try:
            from sqlalchemy import func
            
            # 查询已完成的咨询
            consultations = db.query(Consultation).filter(
                Consultation.status == "completed",
                Consultation.completed_at.isnot(None)
            ).all()
            
            if not consultations:
                return 0.0
            
            # 计算总响应时间
            total_time = 0
            for consultation in consultations:
                response_time = (consultation.completed_at - consultation.created_at).total_seconds()
                total_time += response_time
            
            # 计算平均值
            average_time = total_time / len(consultations)
            return average_time
            
        except Exception as e:
            logger.error(f"计算平均响应时间时出错: {e}")
            return 0.0
        finally:
            db.close()

# 创建咨询管理器实例
import os
from datetime import timedelta
consultation_manager = ConsultationManager()
