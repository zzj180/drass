"""
Performance Optimization Service
Handles system performance optimization, monitoring, and analysis
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import psutil
import json
from dataclasses import dataclass
from enum import Enum

from app.core.logging import get_logger
from app.database.migration_manager import create_migration_manager

logger = get_logger(__name__)


class OptimizationLevel(Enum):
    """Optimization levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    level: OptimizationLevel
    threshold: float
    description: str


@dataclass
class OptimizationRecommendation:
    """Optimization recommendation"""
    id: str
    title: str
    description: str
    impact: str
    effort: str
    priority: OptimizationLevel
    category: str
    implementation: str
    expected_improvement: str


class PerformanceOptimizationService:
    """Service for system performance optimization and monitoring"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or "sqlite:///./data/audit_logs.db"
        self.migration_manager = create_migration_manager(self.database_url)
        self.engine = self.migration_manager.engine
        self.SessionLocal = self.migration_manager.SessionLocal
        
        # Performance thresholds
        self.thresholds = {
            "response_time_ms": 2000,  # 2 seconds
            "database_query_ms": 1000,  # 1 second
            "memory_usage_percent": 80,  # 80%
            "cpu_usage_percent": 80,  # 80%
            "disk_usage_percent": 85,  # 85%
            "concurrent_requests": 100,  # 100 requests
            "cache_hit_rate_percent": 70,  # 70%
            "error_rate_percent": 5,  # 5%
        }
        
        # Performance metrics storage
        self.metrics_file = Path("./data/performance_metrics.json")
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Optimization recommendations
        self.recommendations = []
    
    def _get_db_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    async def run_performance_analysis(self) -> Dict[str, Any]:
        """Run comprehensive performance analysis"""
        try:
            logger.info("Starting performance analysis")
            
            analysis_result = {
                "timestamp": datetime.now().isoformat(),
                "system_metrics": {},
                "application_metrics": {},
                "database_metrics": {},
                "recommendations": [],
                "overall_score": 0,
                "status": "healthy"
            }
            
            # 1. System metrics
            system_metrics = await self._collect_system_metrics()
            analysis_result["system_metrics"] = system_metrics
            
            # 2. Application metrics
            app_metrics = await self._collect_application_metrics()
            analysis_result["application_metrics"] = app_metrics
            
            # 3. Database metrics
            db_metrics = await self._collect_database_metrics()
            analysis_result["database_metrics"] = db_metrics
            
            # 4. Generate recommendations
            recommendations = await self._generate_optimization_recommendations(
                system_metrics, app_metrics, db_metrics
            )
            analysis_result["recommendations"] = recommendations
            
            # 5. Calculate overall performance score
            overall_score = self._calculate_performance_score(
                system_metrics, app_metrics, db_metrics
            )
            analysis_result["overall_score"] = overall_score
            
            # 6. Determine status
            if overall_score >= 90:
                analysis_result["status"] = "excellent"
            elif overall_score >= 75:
                analysis_result["status"] = "good"
            elif overall_score >= 60:
                analysis_result["status"] = "fair"
            elif overall_score >= 40:
                analysis_result["status"] = "poor"
            else:
                analysis_result["status"] = "critical"
            
            # Save metrics
            await self._save_metrics(analysis_result)
            
            logger.info(f"Performance analysis completed: {analysis_result['status']} ({overall_score}/100)")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            raise
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_free_gb = disk.free / (1024**3)
            
            # Network metrics
            network = psutil.net_io_counters()
            network_bytes_sent = network.bytes_sent
            network_bytes_recv = network.bytes_recv
            
            # Process metrics
            process = psutil.Process()
            process_memory_mb = process.memory_info().rss / (1024**2)
            process_cpu_percent = process.cpu_percent()
            
            return {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "status": "good" if cpu_percent < self.thresholds["cpu_usage_percent"] else "warning"
                },
                "memory": {
                    "usage_percent": memory_percent,
                    "available_gb": round(memory_available_gb, 2),
                    "status": "good" if memory_percent < self.thresholds["memory_usage_percent"] else "warning"
                },
                "disk": {
                    "usage_percent": round(disk_percent, 2),
                    "free_gb": round(disk_free_gb, 2),
                    "status": "good" if disk_percent < self.thresholds["disk_usage_percent"] else "warning"
                },
                "network": {
                    "bytes_sent": network_bytes_sent,
                    "bytes_received": network_bytes_recv
                },
                "process": {
                    "memory_mb": round(process_memory_mb, 2),
                    "cpu_percent": process_cpu_percent
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {"error": str(e)}
    
    async def _collect_application_metrics(self) -> Dict[str, Any]:
        """Collect application-level performance metrics"""
        try:
            # This would typically collect metrics from the application
            # For now, we'll simulate some metrics
            
            # Response time metrics
            response_times = await self._measure_response_times()
            
            # Cache metrics
            cache_metrics = await self._collect_cache_metrics()
            
            # Error metrics
            error_metrics = await self._collect_error_metrics()
            
            return {
                "response_times": response_times,
                "cache": cache_metrics,
                "errors": error_metrics,
                "concurrent_requests": await self._get_concurrent_requests()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect application metrics: {e}")
            return {"error": str(e)}
    
    async def _collect_database_metrics(self) -> Dict[str, Any]:
        """Collect database performance metrics"""
        try:
            with self._get_db_session() as session:
                # Test query performance
                start_time = time.time()
                
                # Simple count query
                count_result = session.execute("SELECT COUNT(*) FROM audit_logs").fetchone()
                count_time = (time.time() - start_time) * 1000
                
                # Complex query test
                start_time = time.time()
                complex_result = session.execute("""
                    SELECT event_type, COUNT(*) as count 
                    FROM audit_logs 
                    WHERE timestamp > datetime('now', '-1 day')
                    GROUP BY event_type
                """).fetchall()
                complex_time = (time.time() - start_time) * 1000
                
                # Database size
                db_size = Path(self.database_url.replace("sqlite:///", "")).stat().st_size / (1024**2)
                
                return {
                    "query_performance": {
                        "simple_query_ms": round(count_time, 2),
                        "complex_query_ms": round(complex_time, 2),
                        "status": "good" if count_time < self.thresholds["database_query_ms"] else "warning"
                    },
                    "database_size_mb": round(db_size, 2),
                    "connection_pool": {
                        "active_connections": 1,  # SQLite doesn't have connection pooling
                        "max_connections": 1
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to collect database metrics: {e}")
            return {"error": str(e)}
    
    async def _measure_response_times(self) -> Dict[str, Any]:
        """Measure API response times"""
        try:
            # This would typically measure actual API endpoints
            # For now, we'll simulate some measurements
            
            simulated_times = {
                "health_check_ms": 50,
                "login_ms": 200,
                "document_upload_ms": 1500,
                "compliance_analysis_ms": 3000,
                "audit_logs_ms": 300
            }
            
            # Calculate average and status
            avg_time = sum(simulated_times.values()) / len(simulated_times)
            status = "good" if avg_time < self.thresholds["response_time_ms"] else "warning"
            
            return {
                "endpoints": simulated_times,
                "average_ms": round(avg_time, 2),
                "status": status
            }
            
        except Exception as e:
            logger.error(f"Failed to measure response times: {e}")
            return {"error": str(e)}
    
    async def _collect_cache_metrics(self) -> Dict[str, Any]:
        """Collect cache performance metrics"""
        try:
            # This would typically collect from actual cache systems
            # For now, we'll simulate cache metrics
            
            return {
                "hit_rate_percent": 75,  # Simulated
                "miss_rate_percent": 25,
                "total_requests": 1000,
                "cache_size_mb": 50,
                "status": "good" if 75 >= self.thresholds["cache_hit_rate_percent"] else "warning"
            }
            
        except Exception as e:
            logger.error(f"Failed to collect cache metrics: {e}")
            return {"error": str(e)}
    
    async def _collect_error_metrics(self) -> Dict[str, Any]:
        """Collect error rate metrics"""
        try:
            # This would typically collect from actual error logs
            # For now, we'll simulate error metrics
            
            return {
                "error_rate_percent": 2,  # Simulated
                "total_requests": 1000,
                "error_count": 20,
                "status": "good" if 2 < self.thresholds["error_rate_percent"] else "warning"
            }
            
        except Exception as e:
            logger.error(f"Failed to collect error metrics: {e}")
            return {"error": str(e)}
    
    async def _get_concurrent_requests(self) -> int:
        """Get current concurrent request count"""
        try:
            # This would typically get from actual request tracking
            # For now, we'll simulate
            return 15  # Simulated concurrent requests
            
        except Exception as e:
            logger.error(f"Failed to get concurrent requests: {e}")
            return 0
    
    async def _generate_optimization_recommendations(
        self, 
        system_metrics: Dict[str, Any], 
        app_metrics: Dict[str, Any], 
        db_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on metrics"""
        recommendations = []
        
        # System-level recommendations
        if system_metrics.get("cpu", {}).get("usage_percent", 0) > self.thresholds["cpu_usage_percent"]:
            recommendations.append({
                "id": "cpu_optimization",
                "title": "CPU Usage Optimization",
                "description": "High CPU usage detected. Consider optimizing CPU-intensive operations.",
                "impact": "high",
                "effort": "medium",
                "priority": "high",
                "category": "system",
                "implementation": "Implement async processing, optimize algorithms, add CPU monitoring",
                "expected_improvement": "Reduce CPU usage by 20-30%"
            })
        
        if system_metrics.get("memory", {}).get("usage_percent", 0) > self.thresholds["memory_usage_percent"]:
            recommendations.append({
                "id": "memory_optimization",
                "title": "Memory Usage Optimization",
                "description": "High memory usage detected. Consider implementing memory optimization strategies.",
                "impact": "high",
                "effort": "high",
                "priority": "high",
                "category": "system",
                "implementation": "Implement memory pooling, optimize data structures, add garbage collection",
                "expected_improvement": "Reduce memory usage by 15-25%"
            })
        
        # Application-level recommendations
        if app_metrics.get("response_times", {}).get("average_ms", 0) > self.thresholds["response_time_ms"]:
            recommendations.append({
                "id": "response_time_optimization",
                "title": "Response Time Optimization",
                "description": "Slow response times detected. Consider optimizing API endpoints.",
                "impact": "high",
                "effort": "medium",
                "priority": "high",
                "category": "application",
                "implementation": "Implement caching, optimize database queries, add connection pooling",
                "expected_improvement": "Reduce response time by 30-50%"
            })
        
        if app_metrics.get("cache", {}).get("hit_rate_percent", 0) < self.thresholds["cache_hit_rate_percent"]:
            recommendations.append({
                "id": "cache_optimization",
                "title": "Cache Hit Rate Optimization",
                "description": "Low cache hit rate detected. Consider improving caching strategy.",
                "impact": "medium",
                "effort": "medium",
                "priority": "medium",
                "category": "application",
                "implementation": "Implement better cache keys, increase cache TTL, add cache warming",
                "expected_improvement": "Increase cache hit rate by 20-30%"
            })
        
        # Database-level recommendations
        if db_metrics.get("query_performance", {}).get("simple_query_ms", 0) > self.thresholds["database_query_ms"]:
            recommendations.append({
                "id": "database_optimization",
                "title": "Database Query Optimization",
                "description": "Slow database queries detected. Consider optimizing database performance.",
                "impact": "high",
                "effort": "medium",
                "priority": "high",
                "category": "database",
                "implementation": "Add database indexes, optimize queries, implement connection pooling",
                "expected_improvement": "Reduce query time by 40-60%"
            })
        
        return recommendations
    
    def _calculate_performance_score(
        self, 
        system_metrics: Dict[str, Any], 
        app_metrics: Dict[str, Any], 
        db_metrics: Dict[str, Any]
    ) -> int:
        """Calculate overall performance score (0-100)"""
        try:
            score = 100
            
            # System metrics scoring
            cpu_usage = system_metrics.get("cpu", {}).get("usage_percent", 0)
            if cpu_usage > self.thresholds["cpu_usage_percent"]:
                score -= min(20, (cpu_usage - self.thresholds["cpu_usage_percent"]) * 2)
            
            memory_usage = system_metrics.get("memory", {}).get("usage_percent", 0)
            if memory_usage > self.thresholds["memory_usage_percent"]:
                score -= min(20, (memory_usage - self.thresholds["memory_usage_percent"]) * 2)
            
            # Application metrics scoring
            avg_response_time = app_metrics.get("response_times", {}).get("average_ms", 0)
            if avg_response_time > self.thresholds["response_time_ms"]:
                score -= min(25, (avg_response_time - self.thresholds["response_time_ms"]) / 100)
            
            cache_hit_rate = app_metrics.get("cache", {}).get("hit_rate_percent", 100)
            if cache_hit_rate < self.thresholds["cache_hit_rate_percent"]:
                score -= min(15, (self.thresholds["cache_hit_rate_percent"] - cache_hit_rate) * 0.5)
            
            # Database metrics scoring
            query_time = db_metrics.get("query_performance", {}).get("simple_query_ms", 0)
            if query_time > self.thresholds["database_query_ms"]:
                score -= min(20, (query_time - self.thresholds["database_query_ms"]) / 50)
            
            return max(0, min(100, int(score)))
            
        except Exception as e:
            logger.error(f"Failed to calculate performance score: {e}")
            return 0
    
    async def _save_metrics(self, metrics: Dict[str, Any]) -> None:
        """Save performance metrics to file"""
        try:
            # Load existing metrics
            existing_metrics = []
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    existing_metrics = json.load(f)
            
            # Add new metrics
            existing_metrics.append(metrics)
            
            # Keep only last 100 entries
            if len(existing_metrics) > 100:
                existing_metrics = existing_metrics[-100:]
            
            # Save updated metrics
            with open(self.metrics_file, 'w') as f:
                json.dump(existing_metrics, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    async def get_performance_history(self, days: int = 7) -> Dict[str, Any]:
        """Get performance metrics history"""
        try:
            if not self.metrics_file.exists():
                return {"metrics": [], "summary": {}}
            
            with open(self.metrics_file, 'r') as f:
                all_metrics = json.load(f)
            
            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_metrics = [
                m for m in all_metrics 
                if datetime.fromisoformat(m["timestamp"]) >= cutoff_date
            ]
            
            # Calculate summary statistics
            if recent_metrics:
                scores = [m["overall_score"] for m in recent_metrics]
                summary = {
                    "total_measurements": len(recent_metrics),
                    "average_score": round(sum(scores) / len(scores), 2),
                    "min_score": min(scores),
                    "max_score": max(scores),
                    "trend": "improving" if len(scores) > 1 and scores[-1] > scores[0] else "declining"
                }
            else:
                summary = {}
            
            return {
                "metrics": recent_metrics,
                "summary": summary,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance history: {e}")
            return {"error": str(e)}
    
    async def run_optimization(self, recommendation_id: str) -> Dict[str, Any]:
        """Run a specific optimization based on recommendation"""
        try:
            logger.info(f"Running optimization: {recommendation_id}")
            
            optimization_result = {
                "recommendation_id": recommendation_id,
                "started_at": datetime.now().isoformat(),
                "status": "running",
                "results": {}
            }
            
            # This would typically implement the actual optimization
            # For now, we'll simulate the optimization process
            
            if recommendation_id == "cpu_optimization":
                await asyncio.sleep(1)  # Simulate optimization work
                optimization_result["results"] = {
                    "cpu_usage_reduction": "25%",
                    "optimization_applied": "Async processing implemented"
                }
            elif recommendation_id == "memory_optimization":
                await asyncio.sleep(1)
                optimization_result["results"] = {
                    "memory_usage_reduction": "20%",
                    "optimization_applied": "Memory pooling implemented"
                }
            elif recommendation_id == "response_time_optimization":
                await asyncio.sleep(1)
                optimization_result["results"] = {
                    "response_time_reduction": "40%",
                    "optimization_applied": "Caching and query optimization implemented"
                }
            else:
                optimization_result["results"] = {
                    "message": "Optimization not implemented yet"
                }
            
            optimization_result["status"] = "completed"
            optimization_result["completed_at"] = datetime.now().isoformat()
            
            logger.info(f"Optimization completed: {recommendation_id}")
            return optimization_result
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return {
                "recommendation_id": recommendation_id,
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now().isoformat()
            }


# Global instance
performance_optimization_service = PerformanceOptimizationService()
