"""
生产环境监控API端点
提供监控数据查询、告警管理和仪表盘数据接口
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.services.production_monitoring_service import (
    get_monitoring_service, 
    ProductionMonitoringService,
    record_request_metrics
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/monitoring", tags=["生产环境监控"])

def get_monitoring() -> ProductionMonitoringService:
    """获取监控服务依赖"""
    monitoring = get_monitoring_service()
    if not monitoring:
        raise HTTPException(status_code=503, detail="监控服务未初始化")
    return monitoring

@router.get("/health")
async def health_check():
    """监控服务健康检查"""
    try:
        monitoring = get_monitoring_service()
        if monitoring and monitoring.monitoring_enabled:
            return {
                "status": "healthy",
                "message": "监控服务正常运行",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "unhealthy",
                "message": "监控服务未运行",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"监控服务健康检查错误: {e}")
        raise HTTPException(status_code=500, detail=f"监控服务错误: {str(e)}")

@router.get("/dashboard")
async def get_dashboard_data(monitoring: ProductionMonitoringService = Depends(get_monitoring)):
    """获取监控仪表盘数据"""
    try:
        dashboard_data = await monitoring.get_dashboard_data()
        return {
            "status": "success",
            "data": dashboard_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取仪表盘数据错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取仪表盘数据失败: {str(e)}")

@router.get("/system-metrics")
async def get_system_metrics(
    hours: int = Query(24, description="获取最近N小时的系统指标"),
    monitoring: ProductionMonitoringService = Depends(get_monitoring)
):
    """获取系统指标"""
    try:
        if hours < 1 or hours > 168:  # 限制在1小时到7天之间
            raise HTTPException(status_code=400, detail="时间范围必须在1-168小时之间")
        
        metrics = await monitoring.get_system_metrics(hours=hours)
        return {
            "status": "success",
            "data": {
                "metrics": metrics,
                "count": len(metrics),
                "time_range_hours": hours
            },
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取系统指标错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统指标失败: {str(e)}")

@router.get("/application-metrics")
async def get_application_metrics(
    hours: int = Query(24, description="获取最近N小时的应用指标"),
    monitoring: ProductionMonitoringService = Depends(get_monitoring)
):
    """获取应用指标"""
    try:
        if hours < 1 or hours > 168:  # 限制在1小时到7天之间
            raise HTTPException(status_code=400, detail="时间范围必须在1-168小时之间")
        
        metrics = await monitoring.get_application_metrics(hours=hours)
        return {
            "status": "success",
            "data": {
                "metrics": metrics,
                "count": len(metrics),
                "time_range_hours": hours
            },
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取应用指标错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取应用指标失败: {str(e)}")

@router.get("/alerts")
async def get_alerts(
    resolved: Optional[bool] = Query(None, description="过滤已解决/未解决的告警"),
    hours: int = Query(24, description="获取最近N小时的告警"),
    monitoring: ProductionMonitoringService = Depends(get_monitoring)
):
    """获取告警信息"""
    try:
        if hours < 1 or hours > 168:  # 限制在1小时到7天之间
            raise HTTPException(status_code=400, detail="时间范围必须在1-168小时之间")
        
        alerts = await monitoring.get_alerts(resolved=resolved, hours=hours)
        
        # 统计告警数量
        alert_stats = {
            "total": len(alerts),
            "critical": len([a for a in alerts if a.get('level') == 'CRITICAL']),
            "error": len([a for a in alerts if a.get('level') == 'ERROR']),
            "warning": len([a for a in alerts if a.get('level') == 'WARNING']),
            "info": len([a for a in alerts if a.get('level') == 'INFO']),
            "resolved": len([a for a in alerts if a.get('resolved', False)]),
            "unresolved": len([a for a in alerts if not a.get('resolved', False)])
        }
        
        return {
            "status": "success",
            "data": {
                "alerts": alerts,
                "statistics": alert_stats,
                "time_range_hours": hours
            },
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取告警信息错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取告警信息失败: {str(e)}")

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    monitoring: ProductionMonitoringService = Depends(get_monitoring)
):
    """解决告警"""
    try:
        await monitoring.resolve_alert(alert_id)
        return {
            "status": "success",
            "message": f"告警 {alert_id} 已解决",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"解决告警错误: {e}")
        raise HTTPException(status_code=500, detail=f"解决告警失败: {str(e)}")

@router.get("/status")
async def get_monitoring_status(monitoring: ProductionMonitoringService = Depends(get_monitoring)):
    """获取监控状态"""
    try:
        # 获取最新指标
        system_metrics = await monitoring.get_system_metrics(hours=1)
        app_metrics = await monitoring.get_application_metrics(hours=1)
        alerts = await monitoring.get_alerts(resolved=False, hours=24)
        
        # 判断系统状态
        critical_alerts = [a for a in alerts if a.get('level') == 'CRITICAL']
        error_alerts = [a for a in alerts if a.get('level') == 'ERROR']
        
        if critical_alerts:
            status = "critical"
            message = f"系统严重告警: {len(critical_alerts)}个"
        elif error_alerts:
            status = "error"
            message = f"系统错误告警: {len(error_alerts)}个"
        elif alerts:
            status = "warning"
            message = f"系统警告: {len(alerts)}个"
        else:
            status = "healthy"
            message = "系统运行正常"
        
        # 获取最新指标
        latest_system = system_metrics[0] if system_metrics else {}
        latest_app = app_metrics[0] if app_metrics else {}
        
        return {
            "status": "success",
            "data": {
                "system_status": status,
                "message": message,
                "last_updated": datetime.now().isoformat(),
                "metrics": {
                    "system": {
                        "cpu_percent": latest_system.get('cpu_percent', 0),
                        "memory_percent": latest_system.get('memory_percent', 0),
                        "disk_percent": latest_system.get('disk_percent', 0)
                    },
                    "application": {
                        "response_time_avg": latest_app.get('response_time_avg', 0),
                        "requests_per_second": latest_app.get('requests_per_second', 0),
                        "error_rate": latest_app.get('error_rate', 0),
                        "cache_hit_rate": latest_app.get('cache_hit_rate', 0)
                    }
                },
                "alerts": {
                    "total": len(alerts),
                    "critical": len(critical_alerts),
                    "error": len(error_alerts),
                    "warning": len([a for a in alerts if a.get('level') == 'WARNING'])
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取监控状态错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取监控状态失败: {str(e)}")

@router.get("/performance")
async def get_performance_summary(
    hours: int = Query(24, description="获取最近N小时的性能摘要"),
    monitoring: ProductionMonitoringService = Depends(get_monitoring)
):
    """获取性能摘要"""
    try:
        if hours < 1 or hours > 168:
            raise HTTPException(status_code=400, detail="时间范围必须在1-168小时之间")
        
        # 获取应用指标
        app_metrics = await monitoring.get_application_metrics(hours=hours)
        
        if not app_metrics:
            return {
                "status": "success",
                "data": {
                    "message": "暂无性能数据",
                    "time_range_hours": hours
                },
                "timestamp": datetime.now().isoformat()
            }
        
        # 计算性能统计
        response_times = [m.get('response_time_avg', 0) for m in app_metrics if m.get('response_time_avg')]
        error_rates = [m.get('error_rate', 0) for m in app_metrics if m.get('error_rate')]
        rps_values = [m.get('requests_per_second', 0) for m in app_metrics if m.get('requests_per_second')]
        cache_rates = [m.get('cache_hit_rate', 0) for m in app_metrics if m.get('cache_hit_rate')]
        
        performance_summary = {
            "response_time": {
                "avg": sum(response_times) / len(response_times) if response_times else 0,
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "p95": sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0
            },
            "error_rate": {
                "avg": sum(error_rates) / len(error_rates) if error_rates else 0,
                "max": max(error_rates) if error_rates else 0
            },
            "throughput": {
                "avg_rps": sum(rps_values) / len(rps_values) if rps_values else 0,
                "max_rps": max(rps_values) if rps_values else 0,
                "total_requests": sum(rps_values) * 3600 if rps_values else 0  # 估算总请求数
            },
            "cache": {
                "avg_hit_rate": sum(cache_rates) / len(cache_rates) if cache_rates else 0,
                "min_hit_rate": min(cache_rates) if cache_rates else 0
            }
        }
        
        return {
            "status": "success",
            "data": {
                "performance": performance_summary,
                "time_range_hours": hours,
                "data_points": len(app_metrics)
            },
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取性能摘要错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取性能摘要失败: {str(e)}")

@router.post("/record-metrics")
async def record_metrics(
    response_time: float,
    status_code: int,
    endpoint: str
):
    """记录请求指标"""
    try:
        record_request_metrics(response_time, status_code, endpoint)
        return {
            "status": "success",
            "message": "指标记录成功",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"记录指标错误: {e}")
        raise HTTPException(status_code=500, detail=f"记录指标失败: {str(e)}")

@router.get("/config")
async def get_monitoring_config(monitoring: ProductionMonitoringService = Depends(get_monitoring)):
    """获取监控配置"""
    try:
        return {
            "status": "success",
            "data": {
                "monitoring_enabled": monitoring.monitoring_enabled,
                "thresholds": monitoring.thresholds,
                "monitoring_interval": monitoring.config.get('monitoring_interval', 30),
                "alerts_enabled": {
                    "email": monitoring.config.get('alerts', {}).get('email', {}).get('enabled', False),
                    "webhook": monitoring.config.get('alerts', {}).get('webhook', {}).get('enabled', False)
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取监控配置错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取监控配置失败: {str(e)}")

@router.get("/export")
async def export_monitoring_data(
    data_type: str = Query("all", description="数据类型: system, application, alerts, all"),
    hours: int = Query(24, description="导出最近N小时的数据"),
    format: str = Query("json", description="导出格式: json, csv"),
    monitoring: ProductionMonitoringService = Depends(get_monitoring)
):
    """导出监控数据"""
    try:
        if hours < 1 or hours > 168:
            raise HTTPException(status_code=400, detail="时间范围必须在1-168小时之间")
        
        if data_type not in ["system", "application", "alerts", "all"]:
            raise HTTPException(status_code=400, detail="数据类型必须是: system, application, alerts, all")
        
        if format not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="导出格式必须是: json, csv")
        
        export_data = {}
        
        if data_type in ["system", "all"]:
            export_data["system_metrics"] = await monitoring.get_system_metrics(hours=hours)
        
        if data_type in ["application", "all"]:
            export_data["application_metrics"] = await monitoring.get_application_metrics(hours=hours)
        
        if data_type in ["alerts", "all"]:
            export_data["alerts"] = await monitoring.get_alerts(hours=hours)
        
        if format == "csv":
            # 这里可以实现CSV导出逻辑
            return {
                "status": "success",
                "message": "CSV导出功能待实现",
                "data": export_data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "success",
                "data": export_data,
                "export_info": {
                    "data_type": data_type,
                    "time_range_hours": hours,
                    "format": format,
                    "total_records": sum(len(v) if isinstance(v, list) else 1 for v in export_data.values())
                },
                "timestamp": datetime.now().isoformat()
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出监控数据错误: {e}")
        raise HTTPException(status_code=500, detail=f"导出监控数据失败: {str(e)}")
