"""
RAG优化服务 - 统一管理RAG性能优化
"""

import logging
import time
from typing import Dict, Any, Optional, List
from app.core.rag_performance_config import (
    rag_performance_config, 
    chromadb_optimization_config,
    embedding_optimization_config
)
from app.services.vector_store_optimized import optimized_vector_store_service
from app.chains.optimized_rag_chain import OptimizedRAGChain, AdaptiveRAGChain

logger = logging.getLogger(__name__)


class RAGOptimizationService:
    """RAG优化服务"""
    
    def __init__(self):
        self.vector_store = None
        self.rag_chains = {}
        self.performance_stats = {
            "total_queries": 0,
            "total_time": 0.0,
            "cache_hits": 0,
            "optimization_applied": []
        }
        self._initialized = False
    
    async def initialize(self):
        """初始化RAG优化服务"""
        if self._initialized:
            return
        
        try:
            # 初始化优化的向量存储
            await optimized_vector_store_service.initialize()
            self.vector_store = optimized_vector_store_service
            
            # 获取LLM服务
            from app.services.llm_service_enhanced import unified_llm_service
            llm = unified_llm_service
            
            # 延迟创建RAG链，避免在初始化时创建检索器
            self.rag_chains = {}
            self._llm = llm
            
            self._initialized = True
            logger.info("RAG优化服务初始化完成")
            
        except Exception as e:
            logger.error(f"RAG优化服务初始化失败: {e}")
            raise
    
    def _create_rag_chains(self):
        """创建RAG链"""
        try:
            self.rag_chains = {
                "fast": OptimizedRAGChain(
                    llm=self._llm,
                    vector_store=self.vector_store,
                    max_docs=1,
                    similarity_threshold=0.8
                ),
                "standard": OptimizedRAGChain(
                    llm=self._llm,
                    vector_store=self.vector_store,
                    max_docs=3,
                    similarity_threshold=0.7
                ),
                "detailed": OptimizedRAGChain(
                    llm=self._llm,
                    vector_store=self.vector_store,
                    max_docs=5,
                    similarity_threshold=0.6
                ),
                "adaptive": AdaptiveRAGChain(
                    llm=self._llm,
                    vector_store=self.vector_store
                )
            }
            logger.info("RAG链创建完成")
        except Exception as e:
            logger.error(f"创建RAG链失败: {e}")
            raise
    
    async def optimized_query(
        self,
        query: str,
        response_type: str = "standard",
        use_adaptive: bool = True
    ) -> Dict[str, Any]:
        """执行优化的RAG查询"""
        start_time = time.time()
        
        try:
            if not self._initialized:
                await self.initialize()
            
            # 更新统计
            self.performance_stats["total_queries"] += 1
            
            # 延迟创建RAG链
            if not self.rag_chains:
                self._create_rag_chains()
            
            # 选择RAG链
            if use_adaptive and "adaptive" in self.rag_chains:
                chain = self.rag_chains["adaptive"]
                strategy = "adaptive"
            else:
                chain = self.rag_chains.get(response_type, self.rag_chains["standard"])
                strategy = response_type
            
            # 执行查询
            result = await chain.ainvoke({"input": query})
            
            # 计算性能指标
            response_time = time.time() - start_time
            self.performance_stats["total_time"] += response_time
            
            # 添加优化信息
            result["optimization"] = {
                "strategy": strategy,
                "response_time": response_time,
                "docs_retrieved": len(result.get("context", [])),
                "cache_enabled": rag_performance_config.ENABLE_CACHE,
                "performance_stats": self.get_performance_stats()
            }
            
            logger.info(f"优化RAG查询完成: {strategy}策略, {response_time:.3f}秒")
            
            return result
            
        except Exception as e:
            logger.error(f"优化RAG查询失败: {e}")
            return {
                "answer": "抱歉，查询过程中出现错误。请稍后重试。",
                "context": [],
                "optimization": {
                    "error": str(e),
                    "response_time": time.time() - start_time
                }
            }
    
    async def batch_optimize_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """批量优化文档处理"""
        try:
            if not self._initialized:
                await self.initialize()
            
            start_time = time.time()
            
            # 提取文本和元数据
            texts = [doc.get("content", "") for doc in documents]
            metadatas = [doc.get("metadata", {}) for doc in documents]
            
            # 批量添加到向量存储
            ids = await self.vector_store.batch_add_documents(texts, metadatas)
            
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "documents_processed": len(documents),
                "processing_time": processing_time,
                "ids": ids,
                "optimization_applied": [
                    "批量处理",
                    "向量化优化",
                    "索引优化"
                ]
            }
            
            logger.info(f"批量文档优化完成: {len(documents)}个文档, {processing_time:.3f}秒")
            
            return result
            
        except Exception as e:
            logger.error(f"批量文档优化失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "documents_processed": 0
            }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        stats = {
            **self.performance_stats,
            "avg_response_time": (
                self.performance_stats["total_time"] / self.performance_stats["total_queries"]
                if self.performance_stats["total_queries"] > 0 else 0
            ),
            "cache_hit_rate": (
                self.performance_stats["cache_hits"] / self.performance_stats["total_queries"] * 100
                if self.performance_stats["total_queries"] > 0 else 0
            )
        }
        
        # 添加向量存储统计（同步版本）
        if self.vector_store:
            try:
                # 使用同步方法获取统计
                vector_stats = {
                    "cache_size": len(self.vector_store._cache) if hasattr(self.vector_store, '_cache') else 0,
                    "optimization_config": self.vector_store.optimization_config if hasattr(self.vector_store, 'optimization_config') else {},
                    "status": "initialized" if self.vector_store._initialized else "not_initialized"
                }
                stats["vector_store"] = vector_stats
            except Exception as e:
                stats["vector_store"] = {"error": f"无法获取向量存储统计: {str(e)}"}
        
        return stats
    
    def update_optimization_config(self, config: Dict[str, Any]):
        """更新优化配置"""
        try:
            # 更新全局配置
            if "max_retrieval_docs" in config:
                rag_performance_config.MAX_RETRIEVAL_DOCS = config["max_retrieval_docs"]
            
            if "similarity_threshold" in config:
                rag_performance_config.SIMILARITY_THRESHOLD = config["similarity_threshold"]
            
            if "enable_cache" in config:
                rag_performance_config.ENABLE_CACHE = config["enable_cache"]
            
            # 更新RAG链配置
            for chain_name, chain in self.rag_chains.items():
                if hasattr(chain, 'update_config'):
                    chain.update_config(
                        max_docs=config.get("max_retrieval_docs"),
                        similarity_threshold=config.get("similarity_threshold")
                    )
            
            # 更新向量存储配置
            if self.vector_store and hasattr(self.vector_store, 'update_optimization_config'):
                self.vector_store.update_optimization_config(config)
            
            self.performance_stats["optimization_applied"].append({
                "timestamp": time.time(),
                "config": config
            })
            
            logger.info(f"优化配置已更新: {config}")
            
        except Exception as e:
            logger.error(f"更新优化配置失败: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            health = {
                "status": "healthy",
                "initialized": self._initialized,
                "vector_store": "unknown",
                "rag_chains": len(self.rag_chains),
                "performance_stats": self.get_performance_stats()
            }
            
            if self.vector_store:
                try:
                    vector_health = await self.vector_store.health_check()
                    health["vector_store"] = vector_health.get("status", "unknown")
                except Exception as e:
                    health["vector_store"] = f"error: {str(e)}"
                    health["status"] = "degraded"
            
            return health
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "initialized": self._initialized
            }
    
    async def clear_cache(self):
        """清空缓存"""
        try:
            if self.vector_store and hasattr(self.vector_store, 'clear_cache'):
                await self.vector_store.clear_cache()
            
            self.performance_stats["cache_hits"] = 0
            logger.info("缓存已清空")
            
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")


# 全局实例
rag_optimization_service = RAGOptimizationService()
