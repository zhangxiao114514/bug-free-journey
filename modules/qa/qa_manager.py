import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from utils.config import config_manager
from modules.qa.intent_classifier import intent_classifier
from modules.knowledge.search_engine import search_engine

logger = logging.getLogger(__name__)

class QAManager:
    """问答管理器"""
    
    def __init__(self):
        self.dialogue_history = {}
        self.confidence_threshold = config_manager.getfloat('qa', 'confidence_threshold', 0.7)
        self.max_dialogue_rounds = config_manager.getint('qa', 'max_dialogue_rounds', 10)
        self.dialogue_timeout = config_manager.getint('qa', 'dialogue_timeout', 86400)
    
    def answer(self, customer_id: int, query: str) -> Dict[str, Any]:
        """回答用户问题
        
        Args:
            customer_id: 客户ID
            query: 用户问题
            
        Returns:
            回答结果
        """
        try:
            # 获取对话历史
            dialogue = self._get_dialogue(customer_id)
            
            # 意图识别
            intent_result = intent_classifier.classify(query)
            intent = intent_result['intent']
            confidence = intent_result['confidence']
            
            logger.info(f"客户 {customer_id} 意图识别: {intent} (置信度: {confidence:.2f})")
            
            # 根据意图生成回答
            if confidence >= self.confidence_threshold:
                # 高置信度意图，使用知识库或规则回答
                answer_result = self._generate_answer_by_intent(intent, query, dialogue)
            else:
                # 低置信度意图，使用知识库搜索
                answer_result = self._generate_answer_by_search(query)
            
            # 更新对话历史
            self._update_dialogue(customer_id, query, answer_result)
            
            # 检查是否需要升级到人工客服
            if not answer_result['success'] or answer_result.get('need_human', False):
                answer_result['escalate_to_human'] = True
            
            return answer_result
            
        except Exception as e:
            logger.error(f"回答问题时出错: {e}")
            return {
                'success': False,
                'answer': '抱歉，我现在无法回答您的问题，请稍后再试。',
                'escalate_to_human': True,
                'error': str(e)
            }
    
    def _get_dialogue(self, customer_id: int) -> Dict[str, Any]:
        """获取对话历史
        
        Args:
            customer_id: 客户ID
            
        Returns:
            对话历史
        """
        if customer_id not in self.dialogue_history:
            # 创建新对话
            self.dialogue_history[customer_id] = {
                'rounds': [],
                'created_at': datetime.now(),
                'last_active_at': datetime.now(),
                'context': {}
            }
        else:
            # 检查对话是否超时
            dialogue = self.dialogue_history[customer_id]
            if (datetime.now() - dialogue['last_active_at']).total_seconds() > self.dialogue_timeout:
                # 对话超时，重置对话
                self.dialogue_history[customer_id] = {
                    'rounds': [],
                    'created_at': datetime.now(),
                    'last_active_at': datetime.now(),
                    'context': {}
                }
        
        return self.dialogue_history[customer_id]
    
    def _update_dialogue(self, customer_id: int, query: str, answer_result: Dict[str, Any]):
        """更新对话历史
        
        Args:
            customer_id: 客户ID
            query: 用户问题
            answer_result: 回答结果
        """
        dialogue = self.dialogue_history[customer_id]
        
        # 添加对话轮次
        dialogue['rounds'].append({
            'query': query,
            'answer': answer_result.get('answer', ''),
            'intent': answer_result.get('intent', ''),
            'timestamp': datetime.now()
        })
        
        # 限制对话轮次
        if len(dialogue['rounds']) > self.max_dialogue_rounds:
            dialogue['rounds'] = dialogue['rounds'][-self.max_dialogue_rounds:]
        
        # 更新最后活跃时间
        dialogue['last_active_at'] = datetime.now()
        
        # 更新上下文
        if 'context' in answer_result:
            dialogue['context'].update(answer_result['context'])
    
    def _generate_answer_by_intent(self, intent: str, query: str, dialogue: Dict[str, Any]) -> Dict[str, Any]:
        """根据意图生成回答
        
        Args:
            intent: 意图
            query: 用户问题
            dialogue: 对话历史
            
        Returns:
            回答结果
        """
        # 意图处理映射
        intent_handlers = {
            'greeting': self._handle_greeting,
            'thanks': self._handle_thanks,
            'contract_consultation': self._handle_contract_consultation,
            'labor_dispute': self._handle_labor_dispute,
            'civil_litigation': self._handle_civil_litigation,
            'criminal_defense': self._handle_criminal_defense,
            'property_rights': self._handle_property_rights,
            'marriage_family': self._handle_marriage_family,
            'intellectual_property': self._handle_intellectual_property,
            'administrative_law': self._handle_administrative_law,
            'company_law': self._handle_company_law,
            'other_legal_issues': self._handle_other_legal_issues,
            'inquiry': self._handle_inquiry,
            'complaint': self._handle_complaint
        }
        
        # 调用对应的处理函数
        if intent in intent_handlers:
            return intent_handlers[intent](query, dialogue)
        else:
            # 其他意图，使用知识库搜索
            return self._generate_answer_by_search(query)
    
    def _generate_answer_by_search(self, query: str) -> Dict[str, Any]:
        """通过知识库搜索生成回答
        
        Args:
            query: 用户问题
            
        Returns:
            回答结果
        """
        # 搜索知识库
        search_results = search_engine.search(query, top_k=3)
        
        if search_results:
            # 使用搜索结果生成回答
            best_result = search_results[0]
            answer = self._format_answer_from_knowledge(best_result)
            
            return {
                'success': True,
                'answer': answer,
                'knowledge_id': best_result.get('knowledge_id'),
                'confidence': best_result.get('similarity', 0.0) if 'similarity' in best_result else 0.0
            }
        else:
            # 无搜索结果
            return {
                'success': False,
                'answer': '抱歉，我没有找到相关的法律信息。',
                'need_human': True
            }
    
    def _handle_greeting(self, query: str, dialogue: Dict[str, Any]) -> Dict[str, Any]:
        """处理问候"""
        return {
            'success': True,
            'answer': '您好！我是微信法律客服助手，有什么法律问题可以咨询我。'
        }
    
    def _handle_thanks(self, query: str, dialogue: Dict[str, Any]) -> Dict[str, Any]:
        """处理感谢"""
        return {
            'success': True,
            'answer': '不客气！如果您还有其他法律问题，随时可以咨询我。'
        }
    
    def _handle_contract_consultation(self, query: str, dialogue: Dict[str, Any]) -> Dict[str, Any]:
        """处理合同咨询"""
        return self._generate_answer_by_search(query)
    
    def _handle_labor_dispute(self, query: str, dialogue: Dict[str, Any]) -> Dict[str, Any]:
        """处理劳动纠纷"""
        return self._generate_answer_by_search(query)
    
    def _handle_civil_litigation(self, query: str, dialogue: Dict[str, Any]) -> Dict[str, Any]:
        """处理民事诉讼"""
        return self._generate_answer_by_search(query)
    
    def _handle_criminal_defense(self, query: str, dialogue: Dict[str, Any]) -> Dict[str, Any]:
        """处理刑事辩护"""
        return self._generate_answer_by_search(query)
    
    def _handle_property_rights(self, query: str, dialogue: Dict[str, Any]) -> Dict[str, Any]:
        """处理财产权利"""
        return self._generate_answer_by_search(query)
    
    def _handle_marriage_family(self, query: str, dialogue: Dict[str, Any]) -> Dict[str, Any]:
        """处理婚姻家庭"""
        return self._generate_answer_by_search(query)
    
    def _handle_intellectual_property(self, query: str, dialogue: Dict[str, Any]) -> Dict[str, Any]:
        """处理知识产权"""
        return self._generate_answer_by_search(query)
    
    def _handle_administrative_law(self, query: str, dialogue: Dict[str, Any]) -> Dict[str, Any]:
        """处理行政法"""
        return self._generate_answer_by_search(query)
    
    def _handle_company_law(self, query: str, dialogue: Dict[str, Any]) -> Dict[str, Any]:
        """处理公司法"""
        return self._generate_answer_by_search(query)
    
    def _handle_other_legal_issues(self, query: str, dialogue: Dict[str, Any]) -> Dict[str, Any]:
        """处理其他法律问题"""
        return self._generate_answer_by_search(query)
    
    def _handle_inquiry(self, query: str, dialogue: Dict[str, Any]) -> Dict[str, Any]:
        """处理询问"""
        return self._generate_answer_by_search(query)
    
    def _handle_complaint(self, query: str, dialogue: Dict[str, Any]) -> Dict[str, Any]:
        """处理投诉"""
        return {
            'success': True,
            'answer': '非常抱歉给您带来不便。您的问题已经记录，我们的客服人员会尽快与您联系。',
            'escalate_to_human': True
        }
    
    def _format_answer_from_knowledge(self, knowledge: Dict[str, Any]) -> str:
        """从知识库结果格式化回答
        
        Args:
            knowledge: 知识库结果
            
        Returns:
            格式化后的回答
        """
        title = knowledge.get('title', '')
        content = knowledge.get('content', '')
        
        # 提取内容的前500字符
        content_summary = content[:500]
        if len(content) > 500:
            content_summary += '...'
        
        # 格式化回答
        answer = f"关于'{title}'的相关法律信息：\n\n{content_summary}"
        
        return answer
    
    def clear_dialogue(self, customer_id: int):
        """清除对话历史
        
        Args:
            customer_id: 客户ID
        """
        if customer_id in self.dialogue_history:
            del self.dialogue_history[customer_id]
    
    def cleanup_expired_dialogues(self):
        """清理过期对话"""
        expired_customers = []
        current_time = datetime.now()
        
        for customer_id, dialogue in self.dialogue_history.items():
            last_active = dialogue['last_active_at']
            if (current_time - last_active).total_seconds() > self.dialogue_timeout:
                expired_customers.append(customer_id)
        
        for customer_id in expired_customers:
            del self.dialogue_history[customer_id]
            logger.info(f"清理过期对话: 客户 {customer_id}")

# 创建问答管理器实例
qa_manager = QAManager()
