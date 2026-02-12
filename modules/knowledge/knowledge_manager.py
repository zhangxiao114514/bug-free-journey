import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from utils.database import get_db
from modules.knowledge.models import KnowledgeBase, KnowledgeVersion

logger = logging.getLogger(__name__)

class KnowledgeManager:
    """知识库管理器"""
    
    def __init__(self):
        pass
    
    def create_knowledge(self, data: Dict[str, Any]) -> KnowledgeBase:
        """创建知识库条目
        
        Args:
            data: 知识库数据
            
        Returns:
            创建的知识库条目
        """
        db = next(get_db())
        try:
            # 生成知识库ID
            knowledge_id = f"KB_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
            
            # 创建知识库条目
            knowledge = KnowledgeBase(
                knowledge_id=knowledge_id,
                title=data['title'],
                content=data['content'],
                category=data['category'],
                subcategory=data.get('subcategory'),
                keywords=data.get('keywords'),
                tags=data.get('tags'),
                created_by=data.get('created_by')
            )
            
            db.add(knowledge)
            db.commit()
            db.refresh(knowledge)
            
            # 创建初始版本
            self._create_version(knowledge, data.get('created_by'))
            
            logger.info(f"创建知识库条目: {knowledge.title}")
            return knowledge
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建知识库条目时出错: {e}")
            raise
        finally:
            db.close()
    
    def update_knowledge(self, knowledge_id: int, data: Dict[str, Any]) -> KnowledgeBase:
        """更新知识库条目
        
        Args:
            knowledge_id: 知识库ID
            data: 更新数据
            
        Returns:
            更新后的知识库条目
        """
        db = next(get_db())
        try:
            # 查找知识库条目
            knowledge = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_id).first()
            if not knowledge:
                raise ValueError(f"知识库条目不存在: {knowledge_id}")
            
            # 保存旧版本
            old_data = {
                'title': knowledge.title,
                'content': knowledge.content,
                'keywords': knowledge.keywords,
                'tags': knowledge.tags
            }
            
            # 更新字段
            if 'title' in data:
                knowledge.title = data['title']
            if 'content' in data:
                knowledge.content = data['content']
            if 'category' in data:
                knowledge.category = data['category']
            if 'subcategory' in data:
                knowledge.subcategory = data['subcategory']
            if 'keywords' in data:
                knowledge.keywords = data['keywords']
            if 'tags' in data:
                knowledge.tags = data['tags']
            if 'status' in data:
                knowledge.status = data['status']
            if 'updated_by' in data:
                knowledge.updated_by = data['updated_by']
            
            # 增加版本号
            knowledge.version += 1
            
            db.commit()
            db.refresh(knowledge)
            
            # 创建新版本记录
            self._create_version(knowledge, data.get('updated_by'))
            
            # 清理旧版本（保持最新的10个版本）
            self._cleanup_old_versions(knowledge)
            
            logger.info(f"更新知识库条目: {knowledge.title}, 版本: {knowledge.version}")
            return knowledge
            
        except Exception as e:
            db.rollback()
            logger.error(f"更新知识库条目时出错: {e}")
            raise
        finally:
            db.close()
    
    def delete_knowledge(self, knowledge_id: int) -> bool:
        """删除知识库条目
        
        Args:
            knowledge_id: 知识库ID
            
        Returns:
            是否删除成功
        """
        db = next(get_db())
        try:
            # 查找知识库条目
            knowledge = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_id).first()
            if not knowledge:
                raise ValueError(f"知识库条目不存在: {knowledge_id}")
            
            # 删除相关版本
            db.query(KnowledgeVersion).filter(KnowledgeVersion.knowledge_id == knowledge_id).delete()
            
            # 删除知识库条目
            db.delete(knowledge)
            db.commit()
            
            logger.info(f"删除知识库条目: {knowledge.title}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"删除知识库条目时出错: {e}")
            raise
        finally:
            db.close()
    
    def get_knowledge(self, knowledge_id: int) -> Optional[KnowledgeBase]:
        """获取知识库条目
        
        Args:
            knowledge_id: 知识库ID
            
        Returns:
            知识库条目
        """
        db = next(get_db())
        try:
            knowledge = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_id).first()
            return knowledge
        finally:
            db.close()
    
    def list_knowledge(self, **filters) -> List[KnowledgeBase]:
        """列出知识库条目
        
        Args:
            filters: 过滤条件
            
        Returns:
            知识库条目列表
        """
        db = next(get_db())
        try:
            query = db.query(KnowledgeBase)
            
            # 应用过滤条件
            if 'category' in filters:
                query = query.filter(KnowledgeBase.category == filters['category'])
            if 'subcategory' in filters:
                query = query.filter(KnowledgeBase.subcategory == filters['subcategory'])
            if 'status' in filters:
                query = query.filter(KnowledgeBase.status == filters['status'])
            if 'keywords' in filters:
                # 简单的关键词匹配
                keyword = filters['keywords']
                query = query.filter(
                    (KnowledgeBase.title.contains(keyword)) |
                    (KnowledgeBase.content.contains(keyword)) |
                    (KnowledgeBase.keywords.contains(keyword))
                )
            
            # 排序
            query = query.order_by(KnowledgeBase.created_at.desc())
            
            return query.all()
        finally:
            db.close()
    
    def _create_version(self, knowledge: KnowledgeBase, user_id: Optional[int] = None):
        """创建知识库版本
        
        Args:
            knowledge: 知识库条目
            user_id: 用户ID
        """
        db = next(get_db())
        try:
            version = KnowledgeVersion(
                knowledge_id=knowledge.id,
                version=knowledge.version,
                title=knowledge.title,
                content=knowledge.content,
                keywords=knowledge.keywords,
                tags=knowledge.tags,
                created_by=user_id
            )
            db.add(version)
            db.commit()
        finally:
            db.close()
    
    def _cleanup_old_versions(self, knowledge: KnowledgeBase, max_versions: int = 10):
        """清理旧版本
        
        Args:
            knowledge: 知识库条目
            max_versions: 最大保留版本数
        """
        db = next(get_db())
        try:
            # 获取版本数量
            version_count = db.query(KnowledgeVersion).filter(
                KnowledgeVersion.knowledge_id == knowledge.id
            ).count()
            
            if version_count > max_versions:
                # 获取需要保留的版本
                versions_to_keep = db.query(KnowledgeVersion).filter(
                    KnowledgeVersion.knowledge_id == knowledge.id
                ).order_by(KnowledgeVersion.version.desc()).limit(max_versions).all()
                
                # 获取需要删除的版本ID
                keep_ids = [v.id for v in versions_to_keep]
                
                # 删除旧版本
                db.query(KnowledgeVersion).filter(
                    KnowledgeVersion.knowledge_id == knowledge.id,
                    KnowledgeVersion.id.notin_(keep_ids)
                ).delete(synchronize_session=False)
                
                db.commit()
                logger.info(f"清理知识库旧版本: {knowledge.title}, 保留 {max_versions} 个版本")
        finally:
            db.close()
    
    def get_version_history(self, knowledge_id: int) -> List[KnowledgeVersion]:
        """获取版本历史
        
        Args:
            knowledge_id: 知识库ID
            
        Returns:
            版本历史列表
        """
        db = next(get_db())
        try:
            versions = db.query(KnowledgeVersion).filter(
                KnowledgeVersion.knowledge_id == knowledge_id
            ).order_by(KnowledgeVersion.version.desc()).all()
            return versions
        finally:
            db.close()
    
    def rollback_to_version(self, knowledge_id: int, version: int, user_id: Optional[int] = None) -> KnowledgeBase:
        """回滚到指定版本
        
        Args:
            knowledge_id: 知识库ID
            version: 版本号
            user_id: 用户ID
            
        Returns:
            回滚后的知识库条目
        """
        db = next(get_db())
        try:
            # 查找知识库条目
            knowledge = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_id).first()
            if not knowledge:
                raise ValueError(f"知识库条目不存在: {knowledge_id}")
            
            # 查找指定版本
            old_version = db.query(KnowledgeVersion).filter(
                KnowledgeVersion.knowledge_id == knowledge_id,
                KnowledgeVersion.version == version
            ).first()
            
            if not old_version:
                raise ValueError(f"版本不存在: {version}")
            
            # 保存当前版本
            current_version_data = {
                'title': knowledge.title,
                'content': knowledge.content,
                'keywords': knowledge.keywords,
                'tags': knowledge.tags
            }
            
            # 回滚到旧版本
            knowledge.title = old_version.title
            knowledge.content = old_version.content
            knowledge.keywords = old_version.keywords
            knowledge.tags = old_version.tags
            
            # 增加版本号
            knowledge.version += 1
            if user_id:
                knowledge.updated_by = user_id
            
            db.commit()
            db.refresh(knowledge)
            
            # 创建新版本记录
            self._create_version(knowledge, user_id)
            
            logger.info(f"回滚知识库条目: {knowledge.title}, 版本: {knowledge.version}")
            return knowledge
            
        except Exception as e:
            db.rollback()
            logger.error(f"回滚知识库条目时出错: {e}")
            raise
        finally:
            db.close()

# 创建知识库管理器实例
knowledge_manager = KnowledgeManager()
