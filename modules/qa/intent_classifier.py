import logging
from typing import Dict, Any, List, Tuple
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

from utils.config import config_manager

logger = logging.getLogger(__name__)

class IntentClassifier:
    """意图分类器"""
    
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.intent_labels = self._get_intent_labels()
        self._load_model()
    
    def _get_intent_labels(self) -> List[str]:
        """获取意图标签列表
        
        Returns:
            意图标签列表
        """
        # 法律相关意图标签
        return [
            "contract_consultation",  # 合同咨询
            "labor_dispute",  # 劳动纠纷
            "civil_litigation",  # 民事诉讼
            "criminal_defense",  # 刑事辩护
            "property_rights",  # 财产权利
            "marriage_family",  # 婚姻家庭
            "intellectual_property",  # 知识产权
            "administrative_law",  # 行政法
            "company_law",  # 公司法
            "other_legal_issues",  # 其他法律问题
            "greeting",  # 问候
            "thanks",  # 感谢
            "inquiry",  # 询问
            "complaint",  # 投诉
            "other"
        ]
    
    def _load_model(self):
        """加载预训练模型"""
        try:
            model_name = config_manager.get('ai', 'model_name', 'hfl/chinese-bert-wwm-ext')
            
            # 加载分词器
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # 加载分类模型
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=len(self.intent_labels)
            )
            
            # 如果有本地模型，加载本地模型
            model_path = config_manager.get('ai', 'intent_model_path')
            if model_path and os.path.exists(model_path):
                self.model.load_state_dict(torch.load(os.path.join(model_path, 'model.pth')))
                logger.info(f"加载本地意图模型: {model_path}")
            
            self.model.eval()
            logger.info(f"加载意图分类模型成功: {model_name}")
            
        except Exception as e:
            logger.error(f"加载意图分类模型时出错: {e}")
            # 模型加载失败时，使用规则分类作为 fallback
            self.tokenizer = None
            self.model = None
    
    def classify(self, text: str) -> Dict[str, Any]:
        """分类意图
        
        Args:
            text: 输入文本
            
        Returns:
            分类结果，包含意图标签和置信度
        """
        try:
            # 如果模型加载成功，使用模型分类
            if self.model and self.tokenizer:
                return self._model_classify(text)
            else:
                # 否则使用规则分类
                return self._rule_classify(text)
                
        except Exception as e:
            logger.error(f"分类意图时出错: {e}")
            # 返回默认结果
            return {
                'intent': 'other',
                'confidence': 0.5,
                'intent_id': len(self.intent_labels) - 1
            }
    
    def _model_classify(self, text: str) -> Dict[str, Any]:
        """使用模型分类意图
        
        Args:
            text: 输入文本
            
        Returns:
            分类结果
        """
        # 编码文本
        inputs = self.tokenizer(
            text,
            max_length=512,
            padding=True,
            truncation=True,
            return_tensors="pt"
        )
        
        # 获取模型输出
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # 计算概率
        probabilities = torch.softmax(outputs.logits, dim=1).squeeze().numpy()
        
        # 获取最大概率的意图
        max_index = probabilities.argmax()
        intent = self.intent_labels[max_index]
        confidence = float(probabilities[max_index])
        
        return {
            'intent': intent,
            'confidence': confidence,
            'intent_id': max_index,
            'probabilities': {label: float(prob) for label, prob in zip(self.intent_labels, probabilities)}
        }
    
    def _rule_classify(self, text: str) -> Dict[str, Any]:
        """使用规则分类意图
        
        Args:
            text: 输入文本
            
        Returns:
            分类结果
        """
        text = text.lower()
        
        # 规则匹配
        intent_rules = [
            ("contract_consultation", ["合同", "协议", "条款", "签约", "违约"]),
            ("labor_dispute", ["工资", "加班", "辞职", "解雇", "劳动合同"]),
            ("civil_litigation", ["起诉", "诉讼", "法院", "判决书", "打官司"]),
            ("criminal_defense", ["犯罪", "刑法", "辩护", "拘留", "逮捕"]),
            ("property_rights", ["房产", "财产", "继承", "赠与", "产权"]),
            ("marriage_family", ["离婚", "结婚", "财产分割", "子女抚养", "家庭纠纷"]),
            ("intellectual_property", ["专利", "商标", "版权", "知识产权", "侵权"]),
            ("administrative_law", ["行政", "政府", "许可", "处罚", "行政诉讼"]),
            ("company_law", ["公司", "股权", "股东", "破产", "并购"]),
            ("greeting", ["你好", "您好", "hi", "hello", "早上好", "下午好"]),
            ("thanks", ["谢谢", "感谢", "感激", "多谢"]),
            ("inquiry", ["请问", "想知道", "咨询", "了解", "如何"]),
            ("complaint", ["投诉", "不满", "问题", "错误", "失误"])
        ]
        
        # 匹配规则
        for intent, keywords in intent_rules:
            if any(keyword in text for keyword in keywords):
                return {
                    'intent': intent,
                    'confidence': 0.8,
                    'intent_id': self.intent_labels.index(intent)
                }
        
        # 默认为其他
        return {
            'intent': 'other',
            'confidence': 0.5,
            'intent_id': len(self.intent_labels) - 1
        }
    
    def get_intent_info(self, intent: str) -> Dict[str, Any]:
        """获取意图信息
        
        Args:
            intent: 意图标签
            
        Returns:
            意图信息
        """
        intent_info = {
            "contract_consultation": {"name": "合同咨询", "description": "合同相关的法律咨询"},
            "labor_dispute": {"name": "劳动纠纷", "description": "劳动权益相关的法律咨询"},
            "civil_litigation": {"name": "民事诉讼", "description": "民事诉讼相关的法律咨询"},
            "criminal_defense": {"name": "刑事辩护", "description": "刑事诉讼相关的法律咨询"},
            "property_rights": {"name": "财产权利", "description": "财产权益相关的法律咨询"},
            "marriage_family": {"name": "婚姻家庭", "description": "婚姻家庭相关的法律咨询"},
            "intellectual_property": {"name": "知识产权", "description": "知识产权相关的法律咨询"},
            "administrative_law": {"name": "行政法", "description": "行政法律相关的法律咨询"},
            "company_law": {"name": "公司法", "description": "公司法律相关的法律咨询"},
            "other_legal_issues": {"name": "其他法律问题", "description": "其他法律相关的咨询"},
            "greeting": {"name": "问候", "description": "用户问候"},
            "thanks": {"name": "感谢", "description": "用户感谢"},
            "inquiry": {"name": "询问", "description": "用户询问"},
            "complaint": {"name": "投诉", "description": "用户投诉"},
            "other": {"name": "其他", "description": "其他类型的请求"}
        }
        
        return intent_info.get(intent, intent_info["other"])

# 创建意图分类器实例
import os
intent_classifier = IntentClassifier()
