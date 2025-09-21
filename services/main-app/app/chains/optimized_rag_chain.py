"""
优化的RAG检索链 - 专注于性能优化
"""

import logging
import time
from typing import List, Dict, Any, Optional
from langchain.chains import RetrievalQA
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from app.core.config import settings
from app.chains.prompts import COMPLIANCE_SYSTEM_PROMPT, COMPLIANCE_QA_PROMPT

logger = logging.getLogger(__name__)


class OptimizedRAGChain:
    """优化的RAG链，专注于检索性能"""
    
    def __init__(
        self,
        llm: Optional[Any] = None,
        vector_store: Optional[Any] = None,
        max_docs: int = 3,
        similarity_threshold: float = 0.7
    ):
        """
        初始化优化的RAG链
        
        Args:
            llm: 语言模型实例
            vector_store: 向量存储实例
            max_docs: 最大检索文档数量
            similarity_threshold: 相似度阈值
        """
        self.llm = llm
        self.vector_store = vector_store
        self.max_docs = max_docs
        self.similarity_threshold = similarity_threshold
        
        # 性能统计
        self.stats = {
            "total_queries": 0,
            "total_time": 0.0,
            "avg_response_time": 0.0,
            "cache_hits": 0
        }
        
        # 初始化检索器
        if self.vector_store:
            self._setup_optimized_retriever()
            self._setup_optimized_chain()
    
    def _setup_optimized_retriever(self):
        """设置优化的检索器"""
        if not self.vector_store:
            raise ValueError("向量存储是必需的")
        
        # 创建优化的检索器
        self.retriever = self.vector_store.as_retriever(
            search_kwargs={
                "k": self.max_docs
            }
        )
        
        logger.info(f"优化检索器已设置: max_docs={self.max_docs}, threshold={self.similarity_threshold}")
    
    def _setup_optimized_chain(self):
        """设置优化的链"""
        # 简化的提示模板，减少token使用
        optimized_prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个数据合规专家。基于提供的文档内容回答问题，保持简洁准确。"),
            ("human", "文档内容：\n{context}\n\n问题：{input}\n\n回答：")
        ])
        
        # 创建文档链
        document_chain = create_stuff_documents_chain(
            self.llm,
            optimized_prompt
        )
        
        # 创建检索链
        self.retrieval_chain = create_retrieval_chain(
            self.retriever,
            document_chain
        )
        
        logger.info("优化RAG链已设置")
    
    async def ainvoke(
        self,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """异步调用优化的RAG链"""
        start_time = time.time()
        
        try:
            # 更新统计
            self.stats["total_queries"] += 1
            
            # 执行检索和生成
            result = await self.retrieval_chain.ainvoke(input_data, config)
            
            # 计算响应时间
            response_time = time.time() - start_time
            self.stats["total_time"] += response_time
            self.stats["avg_response_time"] = self.stats["total_time"] / self.stats["total_queries"]
            
            # 添加性能信息
            result["performance"] = {
                "response_time": response_time,
                "docs_retrieved": len(result.get("context", [])),
                "avg_response_time": self.stats["avg_response_time"]
            }
            
            logger.info(f"优化RAG查询完成: {response_time:.3f}秒, 检索文档: {len(result.get('context', []))}个")
            
            return result
            
        except Exception as e:
            logger.error(f"优化RAG查询失败: {e}")
            # 返回fallback结果
            return {
                "answer": "抱歉，检索过程中出现错误。请稍后重试。",
                "context": [],
                "performance": {
                    "response_time": time.time() - start_time,
                    "error": str(e)
                }
            }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return {
            **self.stats,
            "max_docs": self.max_docs,
            "similarity_threshold": self.similarity_threshold
        }
    
    def update_config(self, max_docs: int = None, similarity_threshold: float = None):
        """更新配置"""
        if max_docs is not None:
            self.max_docs = max_docs
        if similarity_threshold is not None:
            self.similarity_threshold = similarity_threshold
        
        # 重新设置检索器
        if self.vector_store:
            self._setup_optimized_retriever()
            self._setup_optimized_chain()
        
        logger.info(f"RAG配置已更新: max_docs={self.max_docs}, threshold={self.similarity_threshold}")


class FastRAGChain:
    """快速RAG链，用于简单查询"""
    
    def __init__(self, llm: Optional[Any] = None, vector_store: Optional[Any] = None):
        self.llm = llm
        self.vector_store = vector_store
        self.max_docs = 2  # 更少的文档
        self.similarity_threshold = 0.8  # 更高的阈值
        
        if self.vector_store:
            self._setup_fast_retriever()
    
    def _setup_fast_retriever(self):
        """设置快速检索器"""
        self.retriever = self.vector_store.as_retriever(
            search_kwargs={
                "k": self.max_docs
            }
        )
    
    async def quick_search(self, query: str) -> str:
        """快速搜索，返回最相关的文档片段"""
        try:
            # 直接检索
            docs = await self.retriever.ainvoke(query)
            
            if not docs:
                return "未找到相关文档。"
            
            # 返回最相关的文档内容
            return docs[0].page_content[:500] + "..." if len(docs[0].page_content) > 500 else docs[0].page_content
            
        except Exception as e:
            logger.error(f"快速搜索失败: {e}")
            return "搜索过程中出现错误。"


class AdaptiveRAGChain:
    """自适应RAG链，根据查询复杂度调整策略"""
    
    def __init__(self, llm: Optional[Any] = None, vector_store: Optional[Any] = None):
        self.llm = llm
        self.vector_store = vector_store
        
        # 创建不同复杂度的链
        self.fast_chain = FastRAGChain(llm, vector_store)
        self.standard_chain = OptimizedRAGChain(llm, vector_store, max_docs=3)
        self.detailed_chain = OptimizedRAGChain(llm, vector_store, max_docs=5)
    
    def _classify_query_complexity(self, query: str) -> str:
        """根据查询内容分类复杂度"""
        # 简单规则分类
        simple_keywords = ["是什么", "定义", "简单", "快速"]
        complex_keywords = ["分析", "详细", "完整", "全面", "深入"]
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in simple_keywords):
            return "simple"
        elif any(keyword in query_lower for keyword in complex_keywords):
            return "complex"
        else:
            return "standard"
    
    async def ainvoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """自适应调用"""
        query = input_data.get("input", "")
        complexity = self._classify_query_complexity(query)
        
        logger.info(f"查询复杂度分类: {complexity}")
        
        if complexity == "simple":
            # 使用快速链
            result = await self.fast_chain.quick_search(query)
            return {
                "answer": result,
                "context": [],
                "strategy": "fast"
            }
        elif complexity == "complex":
            # 使用详细链
            return await self.detailed_chain.ainvoke(input_data)
        else:
            # 使用标准链
            return await self.standard_chain.ainvoke(input_data)
