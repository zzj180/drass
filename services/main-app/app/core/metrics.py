from typing import Dict, Any
import psutil
import asyncio
from datetime import datetime

from app.core.config import settings


async def get_metrics() -> Dict[str, Any]:
    """
    Get system and application metrics
    """
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Process metrics
    process = psutil.Process()
    process_memory = process.memory_info()
    
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            }
        },
        "process": {
            "memory_rss": process_memory.rss,
            "memory_vms": process_memory.vms,
            "cpu_percent": process.cpu_percent(),
            "num_threads": process.num_threads(),
            "create_time": process.create_time()
        },
        "application": {
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "version": "1.0.0"
        }
    }
    
    # Add service-specific metrics if available
    try:
        from app.services.vector_store import vector_store_service
        metrics["services"] = {
            "vector_store": await vector_store_service.get_metrics()
        }
    except:
        pass
    
    return metrics