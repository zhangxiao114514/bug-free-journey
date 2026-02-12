import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from utils.database import get_db
from modules.customer.models import Customer, CustomerTag

logger = logging.getLogger(__name__)

class CustomerManager:
    """客户管理器"""
    
    def __init__(self):
        pass
    
    def create_customer(self, data: Dict[str, Any]) -> Customer:
        """创建客户
        
        Args:
            data: 客户数据
            
        Returns:
            创建的客户
        """
        db = next(get_db())
        try:
            # 检查是否已存在
            existing_customer = db.query(Customer).filter(
                Customer.wechat_id == data.get('wechat_id')
            ).first()
            
            if existing_customer:
                logger.warning(f"客户已存在: {data.get('wechat_id')}")
                return existing_customer
            
            # 创建客户
            customer = Customer(**data)
            db.add(customer)
            db.commit()
            db.refresh(customer)
            
            logger.info(f"创建客户成功: {customer.nickname}")
            return customer
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建客户时出错: {e}")
            raise
        finally:
            db.close()
    
    def update_customer(self, customer_id: int, data: Dict[str, Any]) -> Customer:
        """更新客户信息
        
        Args:
            customer_id: 客户ID
            data: 更新数据
            
        Returns:
            更新后的客户
        """
        db = next(get_db())
        try:
            # 查找客户
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                raise ValueError(f"客户不存在: {customer_id}")
            
            # 更新字段
            for key, value in data.items():
                if hasattr(customer, key):
                    setattr(customer, key, value)
            
            customer.updated_at = datetime.now()
            db.commit()
            db.refresh(customer)
            
            logger.info(f"更新客户成功: {customer.nickname}")
            return customer
            
        except Exception as e:
            db.rollback()
            logger.error(f"更新客户时出错: {e}")
            raise
        finally:
            db.close()
    
    def delete_customer(self, customer_id: int) -> bool:
        """删除客户
        
        Args:
            customer_id: 客户ID
            
        Returns:
            是否删除成功
        """
        db = next(get_db())
        try:
            # 查找客户
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                raise ValueError(f"客户不存在: {customer_id}")
            
            # 删除客户
            db.delete(customer)
            db.commit()
            
            logger.info(f"删除客户成功: {customer.nickname}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"删除客户时出错: {e}")
            raise
        finally:
            db.close()
    
    def get_customer(self, customer_id: int) -> Optional[Customer]:
        """获取客户信息
        
        Args:
            customer_id: 客户ID
            
        Returns:
            客户信息
        """
        db = next(get_db())
        try:
            return db.query(Customer).filter(Customer.id == customer_id).first()
        finally:
            db.close()
    
    def get_customer_by_wechat_id(self, wechat_id: str) -> Optional[Customer]:
        """通过微信ID获取客户信息
        
        Args:
            wechat_id: 微信ID
            
        Returns:
            客户信息
        """
        db = next(get_db())
        try:
            return db.query(Customer).filter(Customer.wechat_id == wechat_id).first()
        finally:
            db.close()
    
    def list_customers(self, **filters) -> List[Customer]:
        """列出客户
        
        Args:
            filters: 过滤条件
            
        Returns:
            客户列表
        """
        db = next(get_db())
        try:
            query = db.query(Customer)
            
            # 应用过滤条件
            if 'status' in filters:
                query = query.filter(Customer.status == filters['status'])
            if 'nickname' in filters:
                query = query.filter(Customer.nickname.contains(filters['nickname']))
            if 'phone' in filters:
                query = query.filter(Customer.phone == filters['phone'])
            if 'tag_id' in filters:
                # 根据标签过滤
                query = query.join(Customer.tags).filter(CustomerTag.id == filters['tag_id'])
            
            # 排序
            query = query.order_by(Customer.created_at.desc())
            
            return query.all()
        finally:
            db.close()
    
    def add_tag_to_customer(self, customer_id: int, tag_id: int) -> bool:
        """为客户添加标签
        
        Args:
            customer_id: 客户ID
            tag_id: 标签ID
            
        Returns:
            是否添加成功
        """
        db = next(get_db())
        try:
            # 查找客户
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                raise ValueError(f"客户不存在: {customer_id}")
            
            # 查找标签
            tag = db.query(CustomerTag).filter(CustomerTag.id == tag_id).first()
            if not tag:
                raise ValueError(f"标签不存在: {tag_id}")
            
            # 检查是否已存在
            if tag not in customer.tags:
                customer.tags.append(tag)
                db.commit()
                logger.info(f"为客户 {customer.nickname} 添加标签: {tag.name}")
            
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"为客户添加标签时出错: {e}")
            raise
        finally:
            db.close()
    
    def remove_tag_from_customer(self, customer_id: int, tag_id: int) -> bool:
        """从客户移除标签
        
        Args:
            customer_id: 客户ID
            tag_id: 标签ID
            
        Returns:
            是否移除成功
        """
        db = next(get_db())
        try:
            # 查找客户
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                raise ValueError(f"客户不存在: {customer_id}")
            
            # 查找标签
            tag = db.query(CustomerTag).filter(CustomerTag.id == tag_id).first()
            if not tag:
                raise ValueError(f"标签不存在: {tag_id}")
            
            # 移除标签
            if tag in customer.tags:
                customer.tags.remove(tag)
                db.commit()
                logger.info(f"从客户 {customer.nickname} 移除标签: {tag.name}")
            
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"从客户移除标签时出错: {e}")
            raise
        finally:
            db.close()
    
    def create_tag(self, data: Dict[str, Any]) -> CustomerTag:
        """创建标签
        
        Args:
            data: 标签数据
            
        Returns:
            创建的标签
        """
        db = next(get_db())
        try:
            # 检查是否已存在
            existing_tag = db.query(CustomerTag).filter(
                CustomerTag.name == data['name']
            ).first()
            
            if existing_tag:
                logger.warning(f"标签已存在: {data['name']}")
                return existing_tag
            
            # 创建标签
            tag = CustomerTag(**data)
            db.add(tag)
            db.commit()
            db.refresh(tag)
            
            logger.info(f"创建标签成功: {tag.name}")
            return tag
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建标签时出错: {e}")
            raise
        finally:
            db.close()
    
    def list_tags(self) -> List[CustomerTag]:
        """列出所有标签
        
        Returns:
            标签列表
        """
        db = next(get_db())
        try:
            return db.query(CustomerTag).order_by(CustomerTag.name).all()
        finally:
            db.close()
    
    def analyze_customer_profile(self, customer_id: int) -> Dict[str, Any]:
        """分析客户画像
        
        Args:
            customer_id: 客户ID
            
        Returns:
            客户画像分析结果
        """
        db = next(get_db())
        try:
            # 查找客户
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                raise ValueError(f"客户不存在: {customer_id}")
            
            # 分析客户数据
            profile = {
                'customer_id': customer.id,
                'nickname': customer.nickname,
                'tags': [tag.name for tag in customer.tags],
                '咨询次数': self._get_consultation_count(customer.id),
                '咨询类型分布': self._get_consultation_category_distribution(customer.id),
                '最近咨询时间': self._get_last_consultation_time(customer.id),
                '咨询满意度': self._get_consultation_satisfaction(customer.id),
                '活跃程度': self._calculate_activity_level(customer),
                '潜在需求': self._identify_potential_needs(customer)
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"分析客户画像时出错: {e}")
            return {}
        finally:
            db.close()
    
    def _get_consultation_count(self, customer_id: int) -> int:
        """获取客户咨询次数
        
        Args:
            customer_id: 客户ID
            
        Returns:
            咨询次数
        """
        db = next(get_db())
        try:
            from modules.consultation.models import Consultation
            return db.query(Consultation).filter(
                Consultation.customer_id == customer_id
            ).count()
        finally:
            db.close()
    
    def _get_consultation_category_distribution(self, customer_id: int) -> Dict[str, int]:
        """获取客户咨询类型分布
        
        Args:
            customer_id: 客户ID
            
        Returns:
            咨询类型分布
        """
        db = next(get_db())
        try:
            from modules.consultation.models import Consultation
            
            # 查询咨询类型分布
            consultations = db.query(Consultation).filter(
                Consultation.customer_id == customer_id
            ).all()
            
            distribution = {}
            for consultation in consultations:
                category = consultation.category or '其他'
                distribution[category] = distribution.get(category, 0) + 1
            
            return distribution
        finally:
            db.close()
    
    def _get_last_consultation_time(self, customer_id: int) -> Optional[str]:
        """获取客户最近咨询时间
        
        Args:
            customer_id: 客户ID
            
        Returns:
            最近咨询时间
        """
        db = next(get_db())
        try:
            from modules.consultation.models import Consultation
            
            consultation = db.query(Consultation).filter(
                Consultation.customer_id == customer_id
            ).order_by(Consultation.created_at.desc()).first()
            
            if consultation:
                return consultation.created_at.strftime('%Y-%m-%d %H:%M:%S')
            return None
        finally:
            db.close()
    
    def _get_consultation_satisfaction(self, customer_id: int) -> float:
        """获取客户咨询满意度
        
        Args:
            customer_id: 客户ID
            
        Returns:
            满意度评分
        """
        db = next(get_db())
        try:
            from modules.consultation.models import Consultation
            
            consultations = db.query(Consultation).filter(
                Consultation.customer_id == customer_id,
                Consultation.satisfaction_score.isnot(None)
            ).all()
            
            if consultations:
                total_score = sum(c.satisfaction_score for c in consultations)
                return total_score / len(consultations)
            return 0.0
        finally:
            db.close()
    
    def _calculate_activity_level(self, customer: Customer) -> str:
        """计算客户活跃程度
        
        Args:
            customer: 客户对象
            
        Returns:
            活跃程度
        """
        consultation_count = self._get_consultation_count(customer.id)
        
        if consultation_count >= 10:
            return "高活跃"
        elif consultation_count >= 3:
            return "中活跃"
        else:
            return "低活跃"
    
    def _identify_potential_needs(self, customer: Customer) -> List[str]:
        """识别客户潜在需求
        
        Args:
            customer: 客户对象
            
        Returns:
            潜在需求列表
        """
        potential_needs = []
        
        # 根据标签分析
        tag_names = [tag.name for tag in customer.tags]
        
        if '企业客户' in tag_names:
            potential_needs.append('公司法咨询')
            potential_needs.append('合同审查')
        
        if '个人客户' in tag_names:
            potential_needs.append('婚姻家庭咨询')
            potential_needs.append('房产咨询')
        
        if '劳动纠纷' in tag_names:
            potential_needs.append('劳动合同审查')
            potential_needs.append('工伤赔偿咨询')
        
        # 根据咨询历史分析
        category_distribution = self._get_consultation_category_distribution(customer.id)
        if 'contract_consultation' in category_distribution:
            potential_needs.append('合同模板服务')
        
        return list(set(potential_needs))[:3]  # 最多返回3个潜在需求

# 创建客户管理器实例
customer_manager = CustomerManager()
