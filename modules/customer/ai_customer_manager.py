import logging
import os
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from utils.database import get_db
from modules.customer.models import Customer, CustomerTag
from modules.customer.audit_manager import audit_manager

logger = logging.getLogger(__name__)

class AICustomerManager:
    """AI客户管理器"""
    
    def __init__(self):
        # 初始化模型和配置
        self.model_cache = {}
        self.scaler = StandardScaler()
        self.initialize_models()
    
    def initialize_models(self):
        """初始化机器学习模型"""
        try:
            # 客户分类模型
            self.cluster_model = KMeans(n_clusters=5, random_state=42)
            
            # 客户流失预测模型
            self.churn_model = RandomForestClassifier(n_estimators=100, random_state=42)
            
            logger.info("AI模型初始化成功")
        except Exception as e:
            logger.error(f"初始化模型时出错: {e}")
    
    def analyze_customer_behavior(self, customer_id: int) -> Dict[str, Any]:
        """分析客户行为
        
        Args:
            customer_id: 客户ID
            
        Returns:
            行为分析结果
        """
        db = next(get_db())
        try:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                raise ValueError(f"客户不存在: {customer_id}")
            
            # 收集客户行为数据
            behavior_data = {
                'consultation_count': self._get_consultation_count(customer_id),
                'avg_consultation_interval': self._get_avg_consultation_interval(customer_id),
                'satisfaction_score': self._get_satisfaction_score(customer_id),
                'response_rate': self._get_response_rate(customer_id),
                'active_days': self._get_active_days(customer_id),
                'last_active_days': self._get_last_active_days(customer),
                'tag_count': len(customer.tags)
            }
            
            return behavior_data
        finally:
            db.close()
    
    def predict_customer_category(self, customer_id: int) -> Dict[str, Any]:
        """预测客户分类
        
        Args:
            customer_id: 客户ID
            
        Returns:
            分类结果
        """
        try:
            # 分析客户行为
            behavior_data = self.analyze_customer_behavior(customer_id)
            
            # 准备特征
            features = np.array([list(behavior_data.values())])
            features_scaled = self.scaler.fit_transform(features)
            
            # 预测分类
            category_id = self.cluster_model.fit_predict(features_scaled)[0]
            
            # 映射分类结果
            categories = {
                0: '高价值活跃客户',
                1: '中等价值客户',
                2: '新客户',
                3: '低活跃客户',
                4: '流失风险客户'
            }
            
            category = categories.get(category_id, '未知客户类型')
            
            # 计算置信度
            confidence = np.random.uniform(0.7, 0.95)  # 模拟置信度
            
            result = {
                'customer_id': customer_id,
                'category': category,
                'confidence': confidence,
                'behavior_data': behavior_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # 提交审核
            audit_manager.create_audit(
                operation_type='customer_category_prediction',
                target_id=customer_id,
                data=result,
                description=f"预测客户 {customer_id} 分类为: {category}"
            )
            
            return result
        except Exception as e:
            logger.error(f"预测客户分类时出错: {e}")
            raise
    
    def predict_churn_risk(self, customer_id: int) -> Dict[str, Any]:
        """预测客户流失风险
        
        Args:
            customer_id: 客户ID
            
        Returns:
            流失风险预测结果
        """
        try:
            # 分析客户行为
            behavior_data = self.analyze_customer_behavior(customer_id)
            
            # 计算流失风险指标
            last_active_days = behavior_data['last_active_days']
            avg_interval = behavior_data['avg_consultation_interval']
            response_rate = behavior_data['response_rate']
            
            # 计算风险分数
            risk_score = 0
            if last_active_days > 30:
                risk_score += 0.4
            if avg_interval > 15:
                risk_score += 0.3
            if response_rate < 0.5:
                risk_score += 0.2
            if behavior_data['consultation_count'] < 3:
                risk_score += 0.1
            
            # 风险等级
            risk_level = '低' if risk_score < 0.3 else '中' if risk_score < 0.7 else '高'
            
            result = {
                'customer_id': customer_id,
                'risk_score': round(risk_score, 2),
                'risk_level': risk_level,
                'risk_factors': self._identify_risk_factors(behavior_data),
                'behavior_data': behavior_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # 提交审核
            audit_manager.create_audit(
                operation_type='churn_risk_prediction',
                target_id=customer_id,
                data=result,
                description=f"预测客户 {customer_id} 流失风险: {risk_level}"
            )
            
            return result
        except Exception as e:
            logger.error(f"预测客户流失风险时出错: {e}")
            raise
    
    def generate_tag_suggestions(self, customer_id: int) -> List[Dict[str, Any]]:
        """生成标签建议
        
        Args:
            customer_id: 客户ID
            
        Returns:
            标签建议列表
        """
        try:
            # 分析客户行为
            behavior_data = self.analyze_customer_behavior(customer_id)
            
            # 基于行为生成标签建议
            tag_suggestions = []
            
            # 基于咨询频率
            if behavior_data['consultation_count'] >= 10:
                tag_suggestions.append({'name': '高频咨询客户', 'confidence': 0.9})
            elif behavior_data['consultation_count'] >= 3:
                tag_suggestions.append({'name': '活跃客户', 'confidence': 0.8})
            
            # 基于满意度
            if behavior_data['satisfaction_score'] >= 4.5:
                tag_suggestions.append({'name': '高满意度客户', 'confidence': 0.85})
            elif behavior_data['satisfaction_score'] < 3:
                tag_suggestions.append({'name': '需关注客户', 'confidence': 0.75})
            
            # 基于活跃度
            if behavior_data['last_active_days'] <= 7:
                tag_suggestions.append({'name': '近期活跃', 'confidence': 0.9})
            elif behavior_data['last_active_days'] > 30:
                tag_suggestions.append({'name': '长期未活跃', 'confidence': 0.8})
            
            # 基于响应率
            if behavior_data['response_rate'] >= 0.8:
                tag_suggestions.append({'name': '高响应客户', 'confidence': 0.8})
            
            result = {
                'customer_id': customer_id,
                'tag_suggestions': tag_suggestions,
                'behavior_data': behavior_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # 提交审核
            audit_manager.create_audit(
                operation_type='tag_suggestion',
                target_id=customer_id,
                data=result,
                description=f"为客户 {customer_id} 生成标签建议"
            )
            
            return tag_suggestions
        except Exception as e:
            logger.error(f"生成标签建议时出错: {e}")
            raise
    
    def calculate_customer_value(self, customer_id: int) -> Dict[str, Any]:
        """计算客户价值
        
        Args:
            customer_id: 客户ID
            
        Returns:
            客户价值评估结果
        """
        try:
            # 分析客户行为
            behavior_data = self.analyze_customer_behavior(customer_id)
            
            # 计算客户价值
            consultation_count = behavior_data['consultation_count']
            satisfaction_score = behavior_data['satisfaction_score']
            active_days = behavior_data['active_days']
            response_rate = behavior_data['response_rate']
            
            # 价值计算公式
            value_score = (
                consultation_count * 0.3 +
                satisfaction_score * 0.25 +
                active_days * 0.2 +
                response_rate * 0.25
            )
            
            # 价值等级
            value_level = '高' if value_score >= 8 else '中' if value_score >= 4 else '低'
            
            # 预测生命周期价值
            predicted_lifetime_value = value_score * 12 * 3  # 简单预测3年价值
            
            result = {
                'customer_id': customer_id,
                'value_score': round(value_score, 2),
                'value_level': value_level,
                'predicted_lifetime_value': round(predicted_lifetime_value, 2),
                'value_factors': self._identify_value_factors(behavior_data),
                'behavior_data': behavior_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # 提交审核
            audit_manager.create_audit(
                operation_type='customer_value_calculation',
                target_id=customer_id,
                data=result,
                description=f"评估客户 {customer_id} 价值为: {value_level}"
            )
            
            return result
        except Exception as e:
            logger.error(f"计算客户价值时出错: {e}")
            raise
    
    def predict_customer_needs(self, customer_id: int) -> List[Dict[str, Any]]:
        """预测客户需求
        
        Args:
            customer_id: 客户ID
            
        Returns:
            需求预测结果
        """
        try:
            # 分析客户行为
            behavior_data = self.analyze_customer_behavior(customer_id)
            
            # 基于历史咨询分析需求
            consultation_categories = self._get_consultation_categories(customer_id)
            
            # 生成需求预测
            needs = []
            
            # 基于咨询类别
            if 'contract' in consultation_categories:
                needs.append({
                    'need': '合同审查服务',
                    'confidence': 0.85,
                    'reason': '历史咨询包含合同相关内容'
                })
            
            if 'labor' in consultation_categories:
                needs.append({
                    'need': '劳动法律咨询',
                    'confidence': 0.8,
                    'reason': '历史咨询包含劳动相关内容'
                })
            
            if 'family' in consultation_categories:
                needs.append({
                    'need': '婚姻家庭咨询',
                    'confidence': 0.75,
                    'reason': '历史咨询包含婚姻家庭相关内容'
                })
            
            # 基于活跃度
            if behavior_data['consultation_count'] >= 5:
                needs.append({
                    'need': '会员法律服务',
                    'confidence': 0.7,
                    'reason': '高频咨询客户，适合会员服务'
                })
            
            # 基于满意度
            if behavior_data['satisfaction_score'] >= 4.5:
                needs.append({
                    'need': '推荐新服务',
                    'confidence': 0.75,
                    'reason': '高满意度客户，愿意尝试新服务'
                })
            
            result = {
                'customer_id': customer_id,
                'needs': needs,
                'consultation_categories': consultation_categories,
                'behavior_data': behavior_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # 提交审核
            audit_manager.create_audit(
                operation_type='customer_needs_prediction',
                target_id=customer_id,
                data=result,
                description=f"预测客户 {customer_id} 需求"
            )
            
            return needs
        except Exception as e:
            logger.error(f"预测客户需求时出错: {e}")
            raise
    
    def suggest_follow_up(self, customer_id: int) -> Dict[str, Any]:
        """建议跟进策略
        
        Args:
            customer_id: 客户ID
            
        Returns:
            跟进建议
        """
        try:
            # 分析客户行为
            behavior_data = self.analyze_customer_behavior(customer_id)
            
            # 预测流失风险
            churn_result = self.predict_churn_risk(customer_id)
            
            # 生成跟进建议
            follow_up_suggestions = []
            
            # 基于活跃度
            if behavior_data['last_active_days'] > 30:
                follow_up_suggestions.append({
                    'type': '重新激活',
                    'content': '发送个性化问候，了解近期需求',
                    'priority': '高',
                    'timing': '立即'
                })
            
            # 基于流失风险
            if churn_result['risk_level'] == '高':
                follow_up_suggestions.append({
                    'type': '风险干预',
                    'content': '安排专人跟进，了解问题并提供解决方案',
                    'priority': '紧急',
                    'timing': '24小时内'
                })
            
            # 基于咨询频率
            if behavior_data['consultation_count'] >= 10:
                follow_up_suggestions.append({
                    'type': '价值提升',
                    'content': '推荐高级法律服务套餐，提供专属优惠',
                    'priority': '中',
                    'timing': '7天内'
                })
            
            # 基于满意度
            if behavior_data['satisfaction_score'] < 3:
                follow_up_suggestions.append({
                    'type': '满意度提升',
                    'content': '回访了解不满意原因，提供补偿方案',
                    'priority': '高',
                    'timing': '48小时内'
                })
            
            # 默认建议
            if not follow_up_suggestions:
                follow_up_suggestions.append({
                    'type': '常规维护',
                    'content': '定期发送法律资讯，保持联系',
                    'priority': '低',
                    'timing': '30天内'
                })
            
            result = {
                'customer_id': customer_id,
                'follow_up_suggestions': follow_up_suggestions,
                'churn_risk': churn_result['risk_level'],
                'behavior_data': behavior_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # 提交审核
            audit_manager.create_audit(
                operation_type='follow_up_suggestion',
                target_id=customer_id,
                data=result,
                description=f"为客户 {customer_id} 生成跟进建议"
            )
            
            return result
        except Exception as e:
            logger.error(f"生成跟进建议时出错: {e}")
            raise
    
    def batch_analyze_customers(self, customer_ids: List[int]) -> List[Dict[str, Any]]:
        """批量分析客户
        
        Args:
            customer_ids: 客户ID列表
            
        Returns:
            分析结果列表
        """
        results = []
        
        for customer_id in customer_ids:
            try:
                analysis = {
                    'customer_id': customer_id,
                    'category': self.predict_customer_category(customer_id),
                    'churn_risk': self.predict_churn_risk(customer_id),
                    'value': self.calculate_customer_value(customer_id),
                    'needs': self.predict_customer_needs(customer_id),
                    'follow_up': self.suggest_follow_up(customer_id)
                }
                results.append(analysis)
            except Exception as e:
                logger.error(f"分析客户 {customer_id} 时出错: {e}")
                results.append({
                    'customer_id': customer_id,
                    'error': str(e)
                })
        
        return results
    
    # 辅助方法
    def _get_consultation_count(self, customer_id: int) -> int:
        """获取咨询次数"""
        db = next(get_db())
        try:
            from modules.consultation.models import Consultation
            return db.query(Consultation).filter(
                Consultation.customer_id == customer_id
            ).count()
        finally:
            db.close()
    
    def _get_avg_consultation_interval(self, customer_id: int) -> float:
        """获取平均咨询间隔"""
        db = next(get_db())
        try:
            from modules.consultation.models import Consultation
            consultations = db.query(Consultation).filter(
                Consultation.customer_id == customer_id
            ).order_by(Consultation.created_at).all()
            
            if len(consultations) < 2:
                return 30  # 默认30天
            
            intervals = []
            for i in range(1, len(consultations)):
                interval = (consultations[i].created_at - consultations[i-1].created_at).days
                intervals.append(interval)
            
            return sum(intervals) / len(intervals) if intervals else 30
        finally:
            db.close()
    
    def _get_satisfaction_score(self, customer_id: int) -> float:
        """获取满意度评分"""
        db = next(get_db())
        try:
            from modules.consultation.models import Consultation
            consultations = db.query(Consultation).filter(
                Consultation.customer_id == customer_id,
                Consultation.satisfaction_score.isnot(None)
            ).all()
            
            if not consultations:
                return 3.0  # 默认3分
            
            total_score = sum(c.satisfaction_score for c in consultations)
            return total_score / len(consultations)
        finally:
            db.close()
    
    def _get_response_rate(self, customer_id: int) -> float:
        """获取响应率"""
        db = next(get_db())
        try:
            from modules.message.models import Message
            total_messages = db.query(Message).filter(
                Message.customer_id == customer_id
            ).count()
            
            if total_messages == 0:
                return 0.5  # 默认0.5
            
            # 简单模拟响应率
            return min(1.0, max(0.1, np.random.normal(0.7, 0.2)))
        finally:
            db.close()
    
    def _get_active_days(self, customer_id: int) -> int:
        """获取活跃天数"""
        db = next(get_db())
        try:
            from modules.consultation.models import Consultation
            consultations = db.query(Consultation).filter(
                Consultation.customer_id == customer_id
            ).all()
            
            if not consultations:
                return 0
            
            # 计算活跃天数
            active_dates = set()
            for consultation in consultations:
                active_dates.add(consultation.created_at.date())
            
            return len(active_dates)
        finally:
            db.close()
    
    def _get_last_active_days(self, customer: Customer) -> int:
        """获取最后活跃天数"""
        db = next(get_db())
        try:
            from modules.consultation.models import Consultation
            last_consultation = db.query(Consultation).filter(
                Consultation.customer_id == customer.id
            ).order_by(Consultation.created_at.desc()).first()
            
            if not last_consultation:
                return (datetime.now() - customer.created_at).days
            
            return (datetime.now() - last_consultation.created_at).days
        finally:
            db.close()
    
    def _get_consultation_categories(self, customer_id: int) -> List[str]:
        """获取咨询类别"""
        db = next(get_db())
        try:
            from modules.consultation.models import Consultation
            consultations = db.query(Consultation).filter(
                Consultation.customer_id == customer_id
            ).all()
            
            categories = set()
            for consultation in consultations:
                if consultation.category:
                    categories.add(consultation.category.lower())
            
            return list(categories)
        finally:
            db.close()
    
    def _identify_risk_factors(self, behavior_data: Dict[str, Any]) -> List[str]:
        """识别风险因素"""
        factors = []
        
        if behavior_data['last_active_days'] > 30:
            factors.append('长期未活跃')
        if behavior_data['avg_consultation_interval'] > 15:
            factors.append('咨询间隔过长')
        if behavior_data['response_rate'] < 0.5:
            factors.append('响应率低')
        if behavior_data['consultation_count'] < 3:
            factors.append('咨询次数少')
        if behavior_data['satisfaction_score'] < 3:
            factors.append('满意度低')
        
        return factors
    
    def _identify_value_factors(self, behavior_data: Dict[str, Any]) -> List[str]:
        """识别价值因素"""
        factors = []
        
        if behavior_data['consultation_count'] >= 10:
            factors.append('高频咨询')
        if behavior_data['satisfaction_score'] >= 4.5:
            factors.append('高满意度')
        if behavior_data['active_days'] >= 10:
            factors.append('高活跃度')
        if behavior_data['response_rate'] >= 0.8:
            factors.append('高响应率')
        
        return factors

# 创建AI客户管理器实例
ai_customer_manager = AICustomerManager()