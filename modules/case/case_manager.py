import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from utils.database import get_db
from modules.case.models import Case, CaseTag, CaseDocument, CaseProgress, CaseStatus, CaseType

logger = logging.getLogger(__name__)

class CaseManager:
    """案例管理器"""
    
    def __init__(self):
        pass
    
    def create_case(self, data: Dict[str, Any]) -> Case:
        """创建案例
        
        Args:
            data: 案例数据
            
        Returns:
            创建的案例
        """
        db = next(get_db())
        try:
            # 生成案例编号
            case_id = f"CASE_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
            
            # 创建案例
            case = Case(
                case_id=case_id,
                title=data['title'],
                description=data.get('description'),
                case_type=data['case_type'],
                status=data.get('status', CaseStatus.PENDING),
                priority=data.get('priority', 0),
                customer_id=data['customer_id'],
                user_id=data.get('user_id')
            )
            
            db.add(case)
            db.commit()
            db.refresh(case)
            
            # 添加标签
            if 'tags' in data:
                for tag_name in data['tags']:
                    tag = CaseTag(
                        case_id=case.id,
                        tag_name=tag_name
                    )
                    db.add(tag)
            
            # 创建初始进度
            self._create_initial_progress(case)
            
            db.commit()
            logger.info(f"创建案例成功: {case.title}")
            return case
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建案例时出错: {e}")
            raise
        finally:
            db.close()
    
    def _create_initial_progress(self, case: Case):
        """创建初始进度
        
        Args:
            case: 案例对象
        """
        # 创建受理阶段
        progress = CaseProgress(
            case_id=case.id,
            stage="受理",
            status="in_progress",
            description="案例已受理，正在等待处理"
        )
        db = next(get_db())
        try:
            db.add(progress)
            db.commit()
        finally:
            db.close()
    
    def get_case(self, case_id: int) -> Optional[Case]:
        """获取案例信息
        
        Args:
            case_id: 案例ID
            
        Returns:
            案例信息
        """
        db = next(get_db())
        try:
            return db.query(Case).filter(Case.id == case_id).first()
        finally:
            db.close()
    
    def get_case_by_case_id(self, case_id: str) -> Optional[Case]:
        """通过案例编号获取案例信息
        
        Args:
            case_id: 案例编号
            
        Returns:
            案例信息
        """
        db = next(get_db())
        try:
            return db.query(Case).filter(Case.case_id == case_id).first()
        finally:
            db.close()
    
    def list_cases(self, **filters) -> List[Case]:
        """列出案例
        
        Args:
            filters: 过滤条件
            
        Returns:
            案例列表
        """
        db = next(get_db())
        try:
            query = db.query(Case)
            
            # 应用过滤条件
            if 'status' in filters:
                query = query.filter(Case.status == filters['status'])
            if 'case_type' in filters:
                query = query.filter(Case.case_type == filters['case_type'])
            if 'customer_id' in filters:
                query = query.filter(Case.customer_id == filters['customer_id'])
            if 'user_id' in filters:
                query = query.filter(Case.user_id == filters['user_id'])
            if 'priority' in filters:
                query = query.filter(Case.priority == filters['priority'])
            
            # 排序
            query = query.order_by(Case.priority.desc(), Case.created_at.desc())
            
            return query.all()
        finally:
            db.close()
    
    def update_case(self, case_id: int, data: Dict[str, Any]) -> Case:
        """更新案例信息
        
        Args:
            case_id: 案例ID
            data: 更新数据
            
        Returns:
            更新后的案例
        """
        db = next(get_db())
        try:
            # 查找案例
            case = db.query(Case).filter(Case.id == case_id).first()
            if not case:
                raise ValueError(f"案例不存在: {case_id}")
            
            # 更新字段
            for key, value in data.items():
                if key != 'tags' and hasattr(case, key):
                    setattr(case, key, value)
            
            # 更新标签
            if 'tags' in data:
                # 删除现有标签
                db.query(CaseTag).filter(CaseTag.case_id == case_id).delete()
                # 添加新标签
                for tag_name in data['tags']:
                    tag = CaseTag(
                        case_id=case_id,
                        tag_name=tag_name
                    )
                    db.add(tag)
            
            # 如果状态变为已完成，设置结束日期
            if 'status' in data and data['status'] == CaseStatus.COMPLETED:
                case.end_date = datetime.now()
            
            case.updated_at = datetime.now()
            db.commit()
            db.refresh(case)
            
            logger.info(f"更新案例成功: {case.title}")
            return case
            
        except Exception as e:
            db.rollback()
            logger.error(f"更新案例时出错: {e}")
            raise
        finally:
            db.close()
    
    def delete_case(self, case_id: int) -> bool:
        """删除案例
        
        Args:
            case_id: 案例ID
            
        Returns:
            是否删除成功
        """
        db = next(get_db())
        try:
            # 查找案例
            case = db.query(Case).filter(Case.id == case_id).first()
            if not case:
                raise ValueError(f"案例不存在: {case_id}")
            
            # 删除案例（级联删除相关的标签、文档和进度）
            db.delete(case)
            db.commit()
            
            logger.info(f"删除案例成功: {case.title}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"删除案例时出错: {e}")
            raise
        finally:
            db.close()
    
    def assign_case(self, case_id: int, user_id: int) -> Case:
        """分配案例
        
        Args:
            case_id: 案例ID
            user_id: 分配的用户ID
            
        Returns:
            分配后的案例
        """
        return self.update_case(case_id, {'user_id': user_id, 'status': CaseStatus.PROCESSING})
    
    def complete_case(self, case_id: int, satisfaction_score: Optional[int] = None, feedback: Optional[str] = None) -> Case:
        """完成案例
        
        Args:
            case_id: 案例ID
            satisfaction_score: 满意度评分
            feedback: 客户反馈
            
        Returns:
            完成后的案例
        """
        data = {
            'status': CaseStatus.COMPLETED,
            'end_date': datetime.now()
        }
        
        if satisfaction_score is not None:
            data['satisfaction_score'] = satisfaction_score
        
        if feedback:
            data['feedback'] = feedback
        
        case = self.update_case(case_id, data)
        
        # 更新所有进度为完成
        db = next(get_db())
        try:
            progresses = db.query(CaseProgress).filter(CaseProgress.case_id == case_id).all()
            for progress in progresses:
                if progress.status != "completed":
                    progress.status = "completed"
                    progress.completed_at = datetime.now()
            
            # 创建完成阶段
            completion_progress = CaseProgress(
                case_id=case_id,
                stage="完成",
                status="completed",
                description="案例已完成，感谢您的反馈"
            )
            db.add(completion_progress)
            db.commit()
        finally:
            db.close()
        
        return case
    
    def add_case_document(self, case_id: int, data: Dict[str, Any]) -> CaseDocument:
        """添加案例文档
        
        Args:
            case_id: 案例ID
            data: 文档数据
            
        Returns:
            创建的文档
        """
        db = next(get_db())
        try:
            # 检查案例是否存在
            case = db.query(Case).filter(Case.id == case_id).first()
            if not case:
                raise ValueError(f"案例不存在: {case_id}")
            
            # 创建文档
            document = CaseDocument(
                case_id=case_id,
                document_name=data['document_name'],
                document_path=data['document_path'],
                document_type=data.get('document_type'),
                description=data.get('description'),
                uploaded_by=data.get('uploaded_by')
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
            logger.info(f"添加案例文档成功: {document.document_name}")
            return document
            
        except Exception as e:
            db.rollback()
            logger.error(f"添加案例文档时出错: {e}")
            raise
        finally:
            db.close()
    
    def update_case_progress(self, case_id: int, stage: str, status: str, description: str = None) -> CaseProgress:
        """更新案例进度
        
        Args:
            case_id: 案例ID
            stage: 阶段
            status: 状态
            description: 描述
            
        Returns:
            更新后的进度
        """
        db = next(get_db())
        try:
            # 检查案例是否存在
            case = db.query(Case).filter(Case.id == case_id).first()
            if not case:
                raise ValueError(f"案例不存在: {case_id}")
            
            # 查找或创建进度
            progress = db.query(CaseProgress).filter(
                CaseProgress.case_id == case_id,
                CaseProgress.stage == stage
            ).first()
            
            if not progress:
                # 创建新进度
                progress = CaseProgress(
                    case_id=case_id,
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
            
            logger.info(f"更新案例进度: {case.title} - {stage} - {status}")
            return progress
            
        except Exception as e:
            db.rollback()
            logger.error(f"更新案例进度时出错: {e}")
            raise
        finally:
            db.close()
    
    def search_cases(self, keyword: str) -> List[Case]:
        """搜索案例
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            搜索结果列表
        """
        db = next(get_db())
        try:
            # 在标题、描述中搜索关键词
            query = db.query(Case).filter(
                (Case.title.ilike(f"%{keyword}%")) |
                (Case.description.ilike(f"%{keyword}%"))
            )
            
            # 也搜索标签
            tag_query = db.query(CaseTag.case_id).filter(
                CaseTag.tag_name.ilike(f"%{keyword}%")
            ).subquery()
            
            query = query.union(
                db.query(Case).filter(Case.id.in_(tag_query))
            )
            
            return query.order_by(Case.created_at.desc()).all()
        finally:
            db.close()
    
    def recommend_cases(self, case_id: int, limit: int = 5) -> List[Case]:
        """推荐相似案例
        
        Args:
            case_id: 当前案例ID
            limit: 推荐数量
            
        Returns:
            推荐案例列表
        """
        db = next(get_db())
        try:
            # 获取当前案例
            current_case = db.query(Case).filter(Case.id == case_id).first()
            if not current_case:
                return []
            
            # 基于案例类型和标签推荐
            # 1. 首先推荐相同类型的案例
            same_type_cases = db.query(Case).filter(
                Case.id != case_id,
                Case.case_type == current_case.case_type
            ).order_by(Case.created_at.desc()).limit(limit).all()
            
            if len(same_type_cases) >= limit:
                return same_type_cases
            
            # 2. 如果不够，再推荐其他类型的案例
            remaining_limit = limit - len(same_type_cases)
            other_cases = db.query(Case).filter(
                Case.id != case_id,
                Case.case_type != current_case.case_type
            ).order_by(Case.created_at.desc()).limit(remaining_limit).all()
            
            return same_type_cases + other_cases
        finally:
            db.close()
    
    def get_pending_cases(self) -> List[Case]:
        """获取待处理的案例
        
        Returns:
            待处理案例列表
        """
        return self.list_cases(status=CaseStatus.PENDING)
    
    def get_processing_cases(self) -> List[Case]:
        """获取处理中的案例
        
        Returns:
            处理中案例列表
        """
        return self.list_cases(status=CaseStatus.PROCESSING)
    
    def get_completed_cases(self) -> List[Case]:
        """获取已完成的案例
        
        Returns:
            已完成案例列表
        """
        return self.list_cases(status=CaseStatus.COMPLETED)

# 创建案例管理器实例
case_manager = CaseManager()
