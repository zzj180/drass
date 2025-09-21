"""
优化的向量存储服务 - 针对RAG检索性能优化
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings
import time

logger = logging.getLogger(__name__)


class OptimizedVectorStoreService:
    """优化的向量存储服务，专注于检索性能"""
    
    def __init__(self):
        self.vector_store = None
        self.collection_name = getattr(settings, 'VECTOR_STORE_COLLECTION', 'compliance_docs')
        self._initialized = False
        self._cache = {}  # 简单缓存
        self._cache_ttl = 300  # 5分钟缓存
        
        # 性能优化配置
        self.optimization_config = {
            "max_retrieval_docs": 3,  # 减少检索文档数量
            "similarity_threshold": 0.7,  # 相似度阈值
            "enable_caching": True,
            "batch_size": 50,
            "enable_compression": True
        }
    
    async def initialize(self):
        """初始化优化的向量存储"""
        if not self._initialized:
            await self._initialize_optimized_store()
            self._initialized = True
    
    async def _initialize_optimized_store(self):
        """初始化优化的向量存储配置"""
        try:
            vector_store_type = getattr(settings, 'VECTOR_STORE_TYPE', 'chromadb').lower()
            if vector_store_type in ["chroma", "chromadb"]:
                from langchain_community.vectorstores import Chroma
                from langchain_community.embeddings import HuggingFaceEmbeddings
                import os
                import shutil

                # 使用更轻量的嵌入模型
                embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    model_kwargs={'device': 'cpu'},  # 强制使用CPU以节省内存
                    encode_kwargs={'normalize_embeddings': True}  # 标准化嵌入
                )

                # 优化ChromaDB配置
                chroma_server_host = getattr(settings, 'CHROMA_SERVER_HOST', 'localhost')
                chroma_server_port = getattr(settings, 'CHROMA_SERVER_PORT', 8005)
                
                try:
                    import chromadb
                    client = chromadb.HttpClient(
                        host=chroma_server_host,
                        port=chroma_server_port,
                        settings=chromadb.Settings(
                            anonymized_telemetry=False,  # 禁用遥测
                            allow_reset=True
                        )
                    )
                    
                    # 测试连接
                    client.heartbeat()
                    logger.info(f"连接到ChromaDB服务器: {chroma_server_host}:{chroma_server_port}")
                    
                    # 创建优化的向量存储
                    self.vector_store = Chroma(
                        collection_name=self.collection_name,
                        embedding_function=embeddings,
                        client=client,
                        collection_metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
                    )
                    
                except Exception as server_error:
                    logger.warning(f"ChromaDB服务器不可用: {server_error}")
                    logger.info("回退到本地持久化")
                    
                    persist_dir = getattr(settings, 'CHROMA_PERSIST_DIRECTORY', './data/chroma')
                    
                    # 创建优化的本地存储
                    self.vector_store = Chroma(
                        collection_name=self.collection_name,
                        embedding_function=embeddings,
                        persist_directory=persist_dir,
                        collection_metadata={"hnsw:space": "cosine"}
                    )
                    
                logger.info("优化的向量存储初始化完成")
                
        except Exception as e:
            logger.error(f"初始化优化向量存储失败: {e}")
            raise
    
    async def optimized_search(
        self,
        query: str,
        k: int = None,
        filter: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """优化的文档搜索"""
        start_time = time.time()
        
        try:
            if not self.vector_store:
                logger.error("向量存储未初始化")
                return []
            
            # 使用优化的k值
            if k is None:
                k = self.optimization_config["max_retrieval_docs"]
            
            # 检查缓存
            if use_cache and self.optimization_config["enable_caching"]:
                cache_key = f"{query}_{k}_{str(filter)}"
                if cache_key in self._cache:
                    cached_result, timestamp = self._cache[cache_key]
                    if time.time() - timestamp < self._cache_ttl:
                        logger.info(f"使用缓存结果，查询时间: {time.time() - start_time:.3f}秒")
                        return cached_result
            
            # 执行相似度搜索
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=k * 2,  # 获取更多结果用于过滤
                filter=filter
            )
            
            # 应用相似度阈值过滤
            threshold = self.optimization_config["similarity_threshold"]
            filtered_results = []
            
            for doc, score in results:
                # 对于余弦相似度，分数越高越相似
                if score >= threshold:
                    filtered_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": score
                    })
                    
                    # 限制返回数量
                    if len(filtered_results) >= k:
                        break
            
            # 如果过滤后结果不足，返回前k个结果
            if len(filtered_results) < k:
                filtered_results = []
                for doc, score in results[:k]:
                    filtered_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": score
                    })
            
            # 缓存结果
            if use_cache and self.optimization_config["enable_caching"]:
                self._cache[cache_key] = (filtered_results, time.time())
                # 清理过期缓存
                self._cleanup_cache()
            
            search_time = time.time() - start_time
            logger.info(f"优化搜索完成: {len(filtered_results)}个结果, 耗时: {search_time:.3f}秒")
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"优化搜索失败: {e}")
            return []
    
    def _cleanup_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp > self._cache_ttl
        ]
        for key in expired_keys:
            del self._cache[key]
    
    async def batch_add_documents(
        self, 
        texts: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """批量添加文档，优化性能"""
        try:
            if not self.vector_store:
                logger.error("向量存储未初始化")
                return []
            
            # 转换为LangChain Document格式
            from langchain.schema import Document
            docs = [
                Document(
                    page_content=text,
                    metadata=metadata if metadata else {}
                )
                for text, metadata in zip(texts, metadatas or [{} for _ in texts])
            ]
            
            # 批量添加
            batch_size = self.optimization_config["batch_size"]
            ids = []
            
            for i in range(0, len(docs), batch_size):
                batch = docs[i:i + batch_size]
                batch_ids = self.vector_store.add_documents(batch)
                ids.extend(batch_ids)
                logger.info(f"批量添加文档: {len(batch)}个")
            
            logger.info(f"批量添加完成: 总计{len(texts)}个文档")
            return ids
            
        except Exception as e:
            logger.error(f"批量添加文档失败: {e}")
            return []
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        try:
            stats = {
                "cache_size": len(self._cache),
                "optimization_config": self.optimization_config,
                "status": "initialized" if self._initialized else "not_initialized"
            }
            
            if self.vector_store and hasattr(self.vector_store, "_collection"):
                collection = self.vector_store._collection
                stats["document_count"] = collection.count()
            
            return stats
            
        except Exception as e:
            logger.error(f"获取性能统计失败: {e}")
            return {"error": str(e)}
    
    def update_optimization_config(self, config: Dict[str, Any]):
        """更新优化配置"""
        self.optimization_config.update(config)
        logger.info(f"优化配置已更新: {config}")
    
    async def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("缓存已清空")
    
    def as_retriever(self, search_kwargs: Optional[Dict[str, Any]] = None):
        """创建检索器接口"""
        if not self.vector_store:
            raise ValueError("向量存储未初始化")
        
        # 返回底层向量存储的检索器
        return self.vector_store.as_retriever(search_kwargs=search_kwargs)
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            health = {
                "status": "healthy",
                "initialized": self._initialized,
                "cache_size": len(self._cache),
                "optimization_config": self.optimization_config
            }
            
            if self.vector_store:
                try:
                    # 测试向量存储连接
                    if hasattr(self.vector_store, '_collection'):
                        collection = self.vector_store._collection
                        health["document_count"] = collection.count()
                        health["vector_store_status"] = "connected"
                    else:
                        health["vector_store_status"] = "local"
                except Exception as e:
                    health["vector_store_status"] = f"error: {str(e)}"
                    health["status"] = "degraded"
            else:
                health["vector_store_status"] = "not_initialized"
                health["status"] = "unhealthy"
            
            return health
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "initialized": self._initialized
            }


# 单例实例
optimized_vector_store_service = OptimizedVectorStoreService()
