"""
RAG优化API端点
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from app.services.rag_optimization_service import rag_optimization_service
from app.core.rag_performance_config import rag_performance_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/rag-optimization", tags=["RAG Optimization"])


class OptimizedQueryRequest(BaseModel):
    """优化查询请求"""
    query: str = Field(..., description="查询内容")
    response_type: str = Field(default="standard", description="响应类型: quick, standard, detailed")
    use_adaptive: bool = Field(default=True, description="是否使用自适应策略")
    max_tokens: Optional[int] = Field(default=None, description="最大token数量")


class OptimizedQueryResponse(BaseModel):
    """优化查询响应"""
    answer: str = Field(..., description="回答内容")
    context: List[Dict[str, Any]] = Field(default=[], description="检索到的文档上下文")
    optimization: Dict[str, Any] = Field(..., description="优化信息")
    performance: Dict[str, Any] = Field(..., description="性能指标")


class BatchOptimizeRequest(BaseModel):
    """批量优化请求"""
    documents: List[Dict[str, Any]] = Field(..., description="文档列表")
    enable_compression: bool = Field(default=True, description="启用压缩")


class OptimizationConfigRequest(BaseModel):
    """优化配置请求"""
    max_retrieval_docs: Optional[int] = Field(default=None, description="最大检索文档数量")
    similarity_threshold: Optional[float] = Field(default=None, description="相似度阈值")
    enable_cache: Optional[bool] = Field(default=None, description="启用缓存")
    cache_ttl: Optional[int] = Field(default=None, description="缓存生存时间")


@router.post("/query", response_model=OptimizedQueryResponse)
async def optimized_query(request: OptimizedQueryRequest):
    """执行优化的RAG查询"""
    try:
        logger.info(f"收到优化查询请求: {request.query[:100]}...")
        
        # 执行优化查询
        result = await rag_optimization_service.optimized_query(
            query=request.query,
            response_type=request.response_type,
            use_adaptive=request.use_adaptive
        )
        
        return OptimizedQueryResponse(
            answer=result.get("answer", ""),
            context=result.get("context", []),
            optimization=result.get("optimization", {}),
            performance=result.get("performance", {})
        )
        
    except Exception as e:
        logger.error(f"优化查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.post("/batch-optimize")
async def batch_optimize_documents(request: BatchOptimizeRequest):
    """批量优化文档处理"""
    try:
        logger.info(f"收到批量优化请求: {len(request.documents)}个文档")
        
        result = await rag_optimization_service.batch_optimize_documents(
            documents=request.documents
        )
        
        return {
            "success": result.get("success", False),
            "documents_processed": result.get("documents_processed", 0),
            "processing_time": result.get("processing_time", 0),
            "optimization_applied": result.get("optimization_applied", []),
            "error": result.get("error")
        }
        
    except Exception as e:
        logger.error(f"批量优化失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量优化失败: {str(e)}")


@router.get("/performance-stats")
async def get_performance_stats():
    """获取性能统计信息"""
    try:
        stats = rag_optimization_service.get_performance_stats()
        return {
            "status": "success",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"获取性能统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.post("/update-config")
async def update_optimization_config(request: OptimizationConfigRequest):
    """更新优化配置"""
    try:
        config = {}
        if request.max_retrieval_docs is not None:
            config["max_retrieval_docs"] = request.max_retrieval_docs
        if request.similarity_threshold is not None:
            config["similarity_threshold"] = request.similarity_threshold
        if request.enable_cache is not None:
            config["enable_cache"] = request.enable_cache
        if request.cache_ttl is not None:
            config["cache_ttl"] = request.cache_ttl
        
        rag_optimization_service.update_optimization_config(config)
        
        return {
            "status": "success",
            "message": "配置已更新",
            "updated_config": config
        }
        
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        health = await rag_optimization_service.health_check()
        return {
            "status": "success",
            "health": health
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.post("/clear-cache")
async def clear_cache():
    """清空缓存"""
    try:
        await rag_optimization_service.clear_cache()
        return {
            "status": "success",
            "message": "缓存已清空"
        }
        
    except Exception as e:
        logger.error(f"清空缓存失败: {e}")
        raise HTTPException(status_code=500, detail=f"清空缓存失败: {str(e)}")


@router.get("/config")
async def get_optimization_config():
    """获取当前优化配置"""
    try:
        return {
            "status": "success",
            "config": {
                "max_retrieval_docs": rag_performance_config.MAX_RETRIEVAL_DOCS,
                "similarity_threshold": rag_performance_config.SIMILARITY_THRESHOLD,
                "enable_cache": rag_performance_config.ENABLE_CACHE,
                "cache_ttl": rag_performance_config.CACHE_TTL,
                "response_type_configs": rag_performance_config.RESPONSE_TYPE_CONFIGS,
                "enable_performance_monitoring": rag_performance_config.ENABLE_PERFORMANCE_MONITORING,
                "enable_adaptive_rag": rag_performance_config.ENABLE_ADAPTIVE_RAG
            }
        }
        
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.get("/vector-store-stats")
async def get_vector_store_stats():
    """获取向量存储统计信息"""
    try:
        if rag_optimization_service.vector_store:
            stats = await rag_optimization_service.vector_store.get_performance_stats()
            return {
                "status": "success",
                "vector_store_stats": stats
            }
        else:
            return {
                "status": "error",
                "message": "向量存储未初始化"
            }
            
    except Exception as e:
        logger.error(f"获取向量存储统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取向量存储统计失败: {str(e)}")
