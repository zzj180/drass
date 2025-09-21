"""
RAG性能优化配置
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class RAGPerformanceConfig(BaseModel):
    """RAG性能优化配置"""
    
    # 检索优化配置
    MAX_RETRIEVAL_DOCS: int = Field(default=3, description="最大检索文档数量")
    MIN_RETRIEVAL_DOCS: int = Field(default=1, description="最小检索文档数量")
    SIMILARITY_THRESHOLD: float = Field(default=0.7, description="相似度阈值")
    
    # 缓存配置
    ENABLE_CACHE: bool = Field(default=True, description="启用缓存")
    CACHE_TTL: int = Field(default=300, description="缓存生存时间(秒)")
    MAX_CACHE_SIZE: int = Field(default=1000, description="最大缓存大小")
    
    # 响应类型配置
    RESPONSE_TYPE_CONFIGS: Dict[str, Dict[str, Any]] = Field(
        default={
            "quick": {
                "max_docs": 1,
                "similarity_threshold": 0.8,
                "max_tokens": 128,
                "timeout": 5,
                "description": "快速回答，适合简单问题"
            },
            "standard": {
                "max_docs": 3,
                "similarity_threshold": 0.7,
                "max_tokens": 256,
                "timeout": 10,
                "description": "标准回答，适合一般问题"
            },
            "detailed": {
                "max_docs": 5,
                "similarity_threshold": 0.6,
                "max_tokens": 512,
                "timeout": 20,
                "description": "详细回答，适合复杂问题"
            }
        }
    )
    
    # 性能监控配置
    ENABLE_PERFORMANCE_MONITORING: bool = Field(default=True, description="启用性能监控")
    LOG_SLOW_QUERIES: bool = Field(default=True, description="记录慢查询")
    SLOW_QUERY_THRESHOLD: float = Field(default=3.0, description="慢查询阈值(秒)")
    
    # 自适应配置
    ENABLE_ADAPTIVE_RAG: bool = Field(default=True, description="启用自适应RAG")
    QUERY_CLASSIFICATION_ENABLED: bool = Field(default=True, description="启用查询分类")
    
    def get_config_for_type(self, response_type: str) -> Dict[str, Any]:
        """获取特定响应类型的配置"""
        return self.RESPONSE_TYPE_CONFIGS.get(response_type, self.RESPONSE_TYPE_CONFIGS["standard"])
    
    def get_optimal_docs_count(self, query_length: int, response_type: str = "standard") -> int:
        """根据查询长度和响应类型获取最优文档数量"""
        config = self.get_config_for_type(response_type)
        base_docs = config["max_docs"]
        
        # 根据查询长度调整
        if query_length < 20:
            return max(1, base_docs - 1)
        elif query_length > 100:
            return min(5, base_docs + 1)
        else:
            return base_docs
    
    def get_optimal_threshold(self, response_type: str = "standard") -> float:
        """获取最优相似度阈值"""
        config = self.get_config_for_type(response_type)
        return config["similarity_threshold"]
    
    def get_optimal_timeout(self, response_type: str = "standard") -> int:
        """获取最优超时时间"""
        config = self.get_config_for_type(response_type)
        return config["timeout"]


class ChromaDBOptimizationConfig(BaseModel):
    """ChromaDB优化配置"""
    
    # 索引配置
    HNSW_SPACE: str = Field(default="cosine", description="HNSW空间类型")
    HNSW_CONSTRUCTION_EF: int = Field(default=200, description="HNSW构建参数")
    HNSW_SEARCH_EF: int = Field(default=50, description="HNSW搜索参数")
    
    # 存储配置
    PERSIST_DIRECTORY: str = Field(default="./data/chroma", description="持久化目录")
    COLLECTION_METADATA: Dict[str, Any] = Field(
        default={"hnsw:space": "cosine", "hnsw:construction_ef": 200},
        description="集合元数据"
    )
    
    # 连接配置
    CONNECTION_TIMEOUT: int = Field(default=30, description="连接超时(秒)")
    MAX_RETRIES: int = Field(default=3, description="最大重试次数")
    
    # 缓存配置
    ENABLE_QUERY_CACHE: bool = Field(default=True, description="启用查询缓存")
    QUERY_CACHE_SIZE: int = Field(default=500, description="查询缓存大小")


class EmbeddingOptimizationConfig(BaseModel):
    """嵌入模型优化配置"""
    
    # 模型配置
    MODEL_NAME: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", description="嵌入模型名称")
    DEVICE: str = Field(default="cpu", description="设备类型")
    NORMALIZE_EMBEDDINGS: bool = Field(default=True, description="标准化嵌入")
    
    # 批处理配置
    BATCH_SIZE: int = Field(default=32, description="批处理大小")
    MAX_SEQUENCE_LENGTH: int = Field(default=512, description="最大序列长度")
    
    # 缓存配置
    ENABLE_EMBEDDING_CACHE: bool = Field(default=True, description="启用嵌入缓存")
    EMBEDDING_CACHE_SIZE: int = Field(default=1000, description="嵌入缓存大小")


# 全局配置实例
rag_performance_config = RAGPerformanceConfig()
chromadb_optimization_config = ChromaDBOptimizationConfig()
embedding_optimization_config = EmbeddingOptimizationConfig()
