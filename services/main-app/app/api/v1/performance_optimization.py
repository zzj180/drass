"""
Performance Optimization API endpoints
Provides performance analysis, monitoring, and optimization functionality
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from app.services.performance_optimization_service import performance_optimization_service
from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/performance", tags=["performance"])


@router.get("/analysis")
async def run_performance_analysis(current_user: dict = Depends(get_current_user)):
    """Run comprehensive performance analysis"""
    try:
        analysis_result = await performance_optimization_service.run_performance_analysis()
        return {
            "success": True,
            "analysis": analysis_result
        }
    except Exception as e:
        logger.error(f"Performance analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_performance_metrics(
    days: int = Query(7, ge=1, le=30, description="Number of days to retrieve metrics for"),
    current_user: dict = Depends(get_current_user)
):
    """Get performance metrics history"""
    try:
        metrics_history = await performance_optimization_service.get_performance_history(days=days)
        return {
            "success": True,
            "metrics": metrics_history
        }
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize/{recommendation_id}")
async def run_optimization(
    recommendation_id: str,
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user)
):
    """Run a specific optimization based on recommendation ID"""
    try:
        optimization_result = await performance_optimization_service.run_optimization(recommendation_id)
        return {
            "success": True,
            "optimization": optimization_result
        }
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations")
async def get_optimization_recommendations(current_user: dict = Depends(get_current_user)):
    """Get current optimization recommendations"""
    try:
        # Run analysis to get current recommendations
        analysis_result = await performance_optimization_service.run_performance_analysis()
        recommendations = analysis_result.get("recommendations", [])
        
        return {
            "success": True,
            "recommendations": recommendations,
            "total_count": len(recommendations),
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_performance_dashboard(current_user: dict = Depends(get_current_user)):
    """Get performance dashboard data"""
    try:
        # Get current analysis
        analysis_result = await performance_optimization_service.run_performance_analysis()
        
        # Get historical metrics
        metrics_history = await performance_optimization_service.get_performance_history(days=7)
        
        # Prepare dashboard data
        dashboard_data = {
            "current_status": {
                "overall_score": analysis_result.get("overall_score", 0),
                "status": analysis_result.get("status", "unknown"),
                "timestamp": analysis_result.get("timestamp")
            },
            "system_metrics": analysis_result.get("system_metrics", {}),
            "application_metrics": analysis_result.get("application_metrics", {}),
            "database_metrics": analysis_result.get("database_metrics", {}),
            "recommendations": analysis_result.get("recommendations", []),
            "historical_trends": metrics_history.get("summary", {}),
            "recent_metrics": metrics_history.get("metrics", [])[-10:]  # Last 10 measurements
        }
        
        return {
            "success": True,
            "dashboard": dashboard_data
        }
    except Exception as e:
        logger.error(f"Failed to get performance dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def performance_health_check():
    """Health check for performance optimization service"""
    try:
        # Quick performance check
        analysis_result = await performance_optimization_service.run_performance_analysis()
        
        health_status = {
            "status": "healthy",
            "overall_score": analysis_result.get("overall_score", 0),
            "performance_status": analysis_result.get("status", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "service": "performance_optimization"
        }
        
        # Determine health status based on performance score
        if analysis_result.get("overall_score", 0) < 40:
            health_status["status"] = "critical"
        elif analysis_result.get("overall_score", 0) < 60:
            health_status["status"] = "warning"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Performance health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "service": "performance_optimization"
        }


@router.get("/thresholds")
async def get_performance_thresholds(current_user: dict = Depends(get_current_user)):
    """Get current performance thresholds"""
    try:
        thresholds = performance_optimization_service.thresholds
        return {
            "success": True,
            "thresholds": thresholds,
            "description": "Performance thresholds used for analysis and recommendations"
        }
    except Exception as e:
        logger.error(f"Failed to get performance thresholds: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/thresholds")
async def update_performance_thresholds(
    thresholds: Dict[str, float],
    current_user: dict = Depends(get_current_user)
):
    """Update performance thresholds"""
    try:
        # Validate thresholds
        valid_keys = set(performance_optimization_service.thresholds.keys())
        provided_keys = set(thresholds.keys())
        
        if not provided_keys.issubset(valid_keys):
            invalid_keys = provided_keys - valid_keys
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid threshold keys: {list(invalid_keys)}"
            )
        
        # Update thresholds
        performance_optimization_service.thresholds.update(thresholds)
        
        return {
            "success": True,
            "message": "Performance thresholds updated successfully",
            "updated_thresholds": thresholds
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update performance thresholds: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-info")
async def get_system_info(current_user: dict = Depends(get_current_user)):
    """Get detailed system information"""
    try:
        import psutil
        
        # Get detailed system information
        system_info = {
            "cpu": {
                "count": psutil.cpu_count(),
                "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                "usage_percent": psutil.cpu_percent(interval=1),
                "per_cpu_usage": psutil.cpu_percent(interval=1, percpu=True)
            },
            "memory": {
                "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                "used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
                "usage_percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
                "used_gb": round(psutil.disk_usage('/').used / (1024**3), 2),
                "free_gb": round(psutil.disk_usage('/').free / (1024**3), 2),
                "usage_percent": round((psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100, 2)
            },
            "network": psutil.net_io_counters()._asdict(),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "system_info": system_info
        }
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stress-test")
async def run_stress_test(
    duration_seconds: int = Query(60, ge=10, le=300, description="Test duration in seconds"),
    concurrent_requests: int = Query(10, ge=1, le=100, description="Number of concurrent requests"),
    current_user: dict = Depends(get_current_user)
):
    """Run a stress test to measure system performance under load"""
    try:
        import asyncio
        import time
        import random
        
        logger.info(f"Starting stress test: {duration_seconds}s, {concurrent_requests} concurrent requests")
        
        stress_test_result = {
            "test_id": f"stress_test_{int(time.time())}",
            "started_at": datetime.now().isoformat(),
            "duration_seconds": duration_seconds,
            "concurrent_requests": concurrent_requests,
            "results": {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "average_response_time_ms": 0,
                "max_response_time_ms": 0,
                "min_response_time_ms": 0,
                "requests_per_second": 0
            }
        }
        
        # Simulate stress test
        start_time = time.time()
        response_times = []
        successful_requests = 0
        failed_requests = 0
        
        async def make_request():
            nonlocal successful_requests, failed_requests
            request_start = time.time()
            
            try:
                # Simulate API call
                await asyncio.sleep(random.uniform(0.1, 0.5))
                
                # Simulate occasional failures
                if random.random() < 0.05:  # 5% failure rate
                    raise Exception("Simulated failure")
                
                response_time = (time.time() - request_start) * 1000
                response_times.append(response_time)
                successful_requests += 1
                
            except Exception:
                failed_requests += 1
        
        # Run stress test
        while time.time() - start_time < duration_seconds:
            tasks = []
            for _ in range(concurrent_requests):
                tasks.append(make_request())
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Small delay between batches
            await asyncio.sleep(0.1)
        
        # Calculate results
        total_requests = successful_requests + failed_requests
        actual_duration = time.time() - start_time
        
        if response_times:
            stress_test_result["results"].update({
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "average_response_time_ms": round(sum(response_times) / len(response_times), 2),
                "max_response_time_ms": round(max(response_times), 2),
                "min_response_time_ms": round(min(response_times), 2),
                "requests_per_second": round(total_requests / actual_duration, 2),
                "success_rate_percent": round((successful_requests / total_requests) * 100, 2) if total_requests > 0 else 0
            })
        
        stress_test_result["completed_at"] = datetime.now().isoformat()
        stress_test_result["actual_duration_seconds"] = round(actual_duration, 2)
        
        logger.info(f"Stress test completed: {total_requests} requests, {successful_requests} successful")
        
        return {
            "success": True,
            "stress_test": stress_test_result
        }
        
    except Exception as e:
        logger.error(f"Stress test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
