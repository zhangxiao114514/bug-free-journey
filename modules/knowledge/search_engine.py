import logging
from typing import List, Dict, Any, Optional
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from utils.database import get_db
from modules.knowledge.models import KnowledgeBase

logger = logging.getLogger(__name__)

class SearchEngine:
    """知识库搜索引擎"""
    
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载预训练模型"""
        try:
            # 加载中文BERT模型
            model_name = "hfl/chinese-bert-wwm-ext"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            self.model.eval()
            logger.info(f"加载预训练模型成功: {model_name}")
        except Exception as e:
            logger.error(f"加载预训练模型时出错: {e}")
            # 如果模型加载失败，使用关键词搜索
            self.tokenizer = None
            self.model = None
    
    def search(self, query: str, top_k: int = 5, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """搜索知识库
        
        Args:
            query: 查询语句
            top_k: 返回结果数量
            category: 分类过滤
            
        Returns:
            搜索结果列表
        """
        try:
            # 获取知识库数据
            knowledge_list = self._get_knowledge_list(category)
            
            if not knowledge_list:
                return []
            
            # 如果模型加载成功，使用语义搜索
            if self.model and self.tokenizer:
                results = self._semantic_search(query, knowledge_list, top_k)
            else:
                # 否则使用关键词搜索
                results = self._keyword_search(query, knowledge_list, top_k)
            
            return results
            
        except Exception as e:
            logger.error(f"搜索知识库时出错: {e}")
            return []
    
    def _get_knowledge_list(self, category: Optional[str] = None) -> List[KnowledgeBase]:
        """获取知识库列表
        
        Args:
            category: 分类过滤
            
        Returns:
            知识库列表
        """
        db = next(get_db())
        try:
            query = db.query(KnowledgeBase).filter(KnowledgeBase.status == "active")
            
            if category:
                query = query.filter(KnowledgeBase.category == category)
            
            return query.all()
        finally:
            db.close()
    
    def _semantic_search(self, query: str, knowledge_list: List[KnowledgeBase], top_k: int) -> List[Dict[str, Any]]:
        """语义搜索
        
        Args:
            query: 查询语句
            knowledge_list: 知识库列表
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        # 计算查询向量
        query_vector = self._get_embedding(query)
        
        # 计算知识库向量并计算相似度
        similarities = []
        for knowledge in knowledge_list:
            # 计算标题和内容的向量
            title_vector = self._get_embedding(knowledge.title)
            content_vector = self._get_embedding(knowledge.content[:1000])  # 只使用前1000字符
            
            # 计算相似度
            title_similarity = cosine_similarity([query_vector], [title_vector])[0][0]
            content_similarity = cosine_similarity([query_vector], [content_vector])[0][0]
            
            # 加权平均
            similarity = title_similarity * 0.6 + content_similarity * 0.4
            
            similarities.append((knowledge, similarity))
        
        # 排序并返回结果
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for knowledge, similarity in similarities[:top_k]:
            results.append({
                'id': knowledge.id,
                'title': knowledge.title,
                'content': knowledge.content,
                'category': knowledge.category,
                'subcategory': knowledge.subcategory,
                'similarity': float(similarity),
                'knowledge_id': knowledge.knowledge_id
            })
        
        return results
    
    def _keyword_search(self, query: str, knowledge_list: List[KnowledgeBase], top_k: int) -> List[Dict[str, Any]]:
        """关键词搜索
        
        Args:
            query: 查询语句
            knowledge_list: 知识库列表
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        # 提取查询关键词
        query_words = self._extract_keywords(query)
        
        # 计算关键词匹配度
        matches = []
        for knowledge in knowledge_list:
            score = 0
            
            # 标题匹配
            title_words = self._extract_keywords(knowledge.title)
            title_match = len(set(query_words) & set(title_words))
            score += title_match * 3
            
            # 内容匹配
            content_words = self._extract_keywords(knowledge.content)
            content_match = len(set(query_words) & set(content_words))
            score += content_match * 1
            
            # 关键词匹配
            if knowledge.keywords:
                keyword_words = self._extract_keywords(knowledge.keywords)
                keyword_match = len(set(query_words) & set(keyword_words))
                score += keyword_match * 2
            
            if score > 0:
                matches.append((knowledge, score))
        
        # 排序并返回结果
        matches.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for knowledge, score in matches[:top_k]:
            results.append({
                'id': knowledge.id,
                'title': knowledge.title,
                'content': knowledge.content,
                'category': knowledge.category,
                'subcategory': knowledge.subcategory,
                'score': score,
                'knowledge_id': knowledge.knowledge_id
            })
        
        return results
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """获取文本嵌入向量
        
        Args:
            text: 文本
            
        Returns:
            嵌入向量
        """
        try:
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
            
            # 计算平均池化
            embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            
            # 归一化
            embeddings = embeddings / np.linalg.norm(embeddings)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"获取文本嵌入时出错: {e}")
            # 返回随机向量作为 fallback
            return np.random.rand(768)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词
        
        Args:
            text: 文本
            
        Returns:
            关键词列表
        """
        import re
        
        # 移除标点符号
        text = re.sub(r'[\s\p{P}+]', ' ', text)
        
        # 分词（简单分词）
        words = text.split()
        
        # 过滤停用词
        stop_words = set(['的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'])
        words = [word for word in words if word not in stop_words and len(word) > 1]
        
        return words

# 创建搜索引擎实例
search_engine = SearchEngine()
