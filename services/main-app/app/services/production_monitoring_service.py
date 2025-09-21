"""
生产环境监控服务
提供全面的性能监控、告警和统计功能
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import psutil
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_sent: int
    network_recv: int
    load_average: List[float]

@dataclass
class ApplicationMetrics:
    """应用指标"""
    timestamp: str
    response_time_avg: float
    response_time_p95: float
    response_time_p99: float
    requests_per_second: float
    error_rate: float
    active_connections: int
    cache_hit_rate: float

@dataclass
class DatabaseMetrics:
    """数据库指标"""
    timestamp: str
    connection_pool_size: int
    active_connections: int
    query_time_avg: float
    slow_queries: int
    deadlocks: int

@dataclass
class Alert:
    """告警信息"""
    id: str
    timestamp: str
    level: str  # INFO, WARNING, ERROR, CRITICAL
    category: str  # SYSTEM, APPLICATION, DATABASE, CACHE
    message: str
    details: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[str] = None

class ProductionMonitoringService:
    """生产环境监控服务"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics_history = deque(maxlen=1000)  # 保留最近1000个指标
        self.alerts = []
        self.thresholds = config.get('thresholds', {})
        self.monitoring_enabled = True
        self.last_metrics_time = None
        
        # 初始化数据库
        self._init_database()
        
        # 启动监控任务
        self._start_monitoring()
    
    def _init_database(self):
        """初始化监控数据库"""
        db_path = Path("data/monitoring.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.db_path = str(db_path)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_percent REAL,
                    network_sent INTEGER,
                    network_recv INTEGER,
                    load_average TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS application_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    response_time_avg REAL,
                    response_time_p95 REAL,
                    response_time_p99 REAL,
                    requests_per_second REAL,
                    error_rate REAL,
                    active_connections INTEGER,
                    cache_hit_rate REAL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    category TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TEXT
                )
            """)
            
            conn.commit()
    
    def _start_monitoring(self):
        """启动监控任务"""
        if self.monitoring_enabled:
            asyncio.create_task(self._monitoring_loop())
    
    async def _monitoring_loop(self):
        """监控循环"""
        while self.monitoring_enabled:
            try:
                # 收集系统指标
                system_metrics = await self._collect_system_metrics()
                await self._store_metrics('system', system_metrics)
                
                # 收集应用指标
                app_metrics = await self._collect_application_metrics()
                await self._store_metrics('application', app_metrics)
                
                # 检查告警
                await self._check_alerts(system_metrics, app_metrics)
                
                # 等待下次监控
                await asyncio.sleep(self.config.get('monitoring_interval', 30))
                
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                await asyncio.sleep(10)
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # 网络统计
            network = psutil.net_io_counters()
            
            # 负载平均值
            load_avg = list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0.0, 0.0, 0.0]
            
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_sent=network.bytes_sent,
                network_recv=network.bytes_recv,
                load_average=load_avg
            )
        except Exception as e:
            logger.error(f"收集系统指标错误: {e}")
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                network_sent=0,
                network_recv=0,
                load_average=[0.0, 0.0, 0.0]
            )
    
    async def _collect_application_metrics(self) -> ApplicationMetrics:
        """收集应用指标"""
        try:
            # 从metrics_history计算应用指标
            if not self.metrics_history:
                return ApplicationMetrics(
                    timestamp=datetime.now().isoformat(),
                    response_time_avg=0.0,
                    response_time_p95=0.0,
                    response_time_p99=0.0,
                    requests_per_second=0.0,
                    error_rate=0.0,
                    active_connections=0,
                    cache_hit_rate=0.0
                )
            
            # 计算响应时间统计
            response_times = [m.get('response_time', 0) for m in self.metrics_history if 'response_time' in m]
            if response_times:
                response_times.sort()
                avg_time = sum(response_times) / len(response_times)
                p95_index = int(len(response_times) * 0.95)
                p99_index = int(len(response_times) * 0.99)
                p95_time = response_times[p95_index] if p95_index < len(response_times) else response_times[-1]
                p99_time = response_times[p99_index] if p99_index < len(response_times) else response_times[-1]
            else:
                avg_time = p95_time = p99_time = 0.0
            
            # 计算请求速率
            current_time = time.time()
            recent_requests = [m for m in self.metrics_history 
                             if current_time - m.get('timestamp', 0) < 60]  # 最近1分钟
            requests_per_second = len(recent_requests) / 60.0
            
            # 计算错误率
            total_requests = len(self.metrics_history)
            error_requests = len([m for m in self.metrics_history if m.get('status_code', 200) >= 400])
            error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0.0
            
            # 缓存命中率（模拟）
            cache_hit_rate = 85.0  # 实际应该从缓存服务获取
            
            return ApplicationMetrics(
                timestamp=datetime.now().isoformat(),
                response_time_avg=avg_time,
                response_time_p95=p95_time,
                response_time_p99=p99_time,
                requests_per_second=requests_per_second,
                error_rate=error_rate,
                active_connections=len(recent_requests),
                cache_hit_rate=cache_hit_rate
            )
        except Exception as e:
            logger.error(f"收集应用指标错误: {e}")
            return ApplicationMetrics(
                timestamp=datetime.now().isoformat(),
                response_time_avg=0.0,
                response_time_p95=0.0,
                response_time_p99=0.0,
                requests_per_second=0.0,
                error_rate=0.0,
                active_connections=0,
                cache_hit_rate=0.0
            )
    
    async def _store_metrics(self, metric_type: str, metrics: Any):
        """存储指标到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if metric_type == 'system':
                    conn.execute("""
                        INSERT INTO system_metrics 
                        (timestamp, cpu_percent, memory_percent, disk_percent, 
                         network_sent, network_recv, load_average)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        metrics.timestamp, metrics.cpu_percent, metrics.memory_percent,
                        metrics.disk_percent, metrics.network_sent, metrics.network_recv,
                        json.dumps(metrics.load_average)
                    ))
                elif metric_type == 'application':
                    conn.execute("""
                        INSERT INTO application_metrics 
                        (timestamp, response_time_avg, response_time_p95, response_time_p99,
                         requests_per_second, error_rate, active_connections, cache_hit_rate)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        metrics.timestamp, metrics.response_time_avg, metrics.response_time_p95,
                        metrics.response_time_p99, metrics.requests_per_second, metrics.error_rate,
                        metrics.active_connections, metrics.cache_hit_rate
                    ))
                conn.commit()
        except Exception as e:
            logger.error(f"存储指标错误: {e}")
    
    async def _check_alerts(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics):
        """检查告警条件"""
        try:
            # 系统告警
            if system_metrics.cpu_percent > self.thresholds.get('cpu_threshold', 80):
                await self._create_alert(
                    level='WARNING',
                    category='SYSTEM',
                    message=f'CPU使用率过高: {system_metrics.cpu_percent:.1f}%',
                    details={'cpu_percent': system_metrics.cpu_percent}
                )
            
            if system_metrics.memory_percent > self.thresholds.get('memory_threshold', 85):
                await self._create_alert(
                    level='WARNING',
                    category='SYSTEM',
                    message=f'内存使用率过高: {system_metrics.memory_percent:.1f}%',
                    details={'memory_percent': system_metrics.memory_percent}
                )
            
            if system_metrics.disk_percent > self.thresholds.get('disk_threshold', 90):
                await self._create_alert(
                    level='CRITICAL',
                    category='SYSTEM',
                    message=f'磁盘使用率过高: {system_metrics.disk_percent:.1f}%',
                    details={'disk_percent': system_metrics.disk_percent}
                )
            
            # 应用告警
            if app_metrics.response_time_avg > self.thresholds.get('response_time_threshold', 5.0):
                await self._create_alert(
                    level='WARNING',
                    category='APPLICATION',
                    message=f'响应时间过长: {app_metrics.response_time_avg:.2f}秒',
                    details={'response_time_avg': app_metrics.response_time_avg}
                )
            
            if app_metrics.error_rate > self.thresholds.get('error_rate_threshold', 5.0):
                await self._create_alert(
                    level='ERROR',
                    category='APPLICATION',
                    message=f'错误率过高: {app_metrics.error_rate:.1f}%',
                    details={'error_rate': app_metrics.error_rate}
                )
            
            if app_metrics.cache_hit_rate < self.thresholds.get('cache_hit_rate_threshold', 70):
                await self._create_alert(
                    level='WARNING',
                    category='CACHE',
                    message=f'缓存命中率过低: {app_metrics.cache_hit_rate:.1f}%',
                    details={'cache_hit_rate': app_metrics.cache_hit_rate}
                )
                
        except Exception as e:
            logger.error(f"检查告警错误: {e}")
    
    async def _create_alert(self, level: str, category: str, message: str, details: Dict[str, Any]):
        """创建告警"""
        alert_id = f"{category}_{int(time.time())}"
        
        alert = Alert(
            id=alert_id,
            timestamp=datetime.now().isoformat(),
            level=level,
            category=category,
            message=message,
            details=details
        )
        
        # 存储到数据库
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO alerts 
                    (id, timestamp, level, category, message, details, resolved, resolved_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.id, alert.timestamp, alert.level, alert.category,
                    alert.message, json.dumps(alert.details), alert.resolved, alert.resolved_at
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"存储告警错误: {e}")
        
        # 添加到内存列表
        self.alerts.append(alert)
        
        # 发送告警通知
        await self._send_alert_notification(alert)
        
        logger.warning(f"告警创建: {alert.level} - {alert.message}")
    
    async def _send_alert_notification(self, alert: Alert):
        """发送告警通知"""
        try:
            # 这里可以集成邮件、Slack、微信等通知方式
            if self.config.get('alerts', {}).get('email', {}).get('enabled', False):
                await self._send_email_alert(alert)
            
            if self.config.get('alerts', {}).get('webhook', {}).get('enabled', False):
                await self._send_webhook_alert(alert)
                
        except Exception as e:
            logger.error(f"发送告警通知错误: {e}")
    
    async def _send_email_alert(self, alert: Alert):
        """发送邮件告警"""
        # 实现邮件发送逻辑
        pass
    
    async def _send_webhook_alert(self, alert: Alert):
        """发送Webhook告警"""
        # 实现Webhook发送逻辑
        pass
    
    def record_request_metrics(self, response_time: float, status_code: int, endpoint: str):
        """记录请求指标"""
        try:
            metric = {
                'timestamp': time.time(),
                'response_time': response_time,
                'status_code': status_code,
                'endpoint': endpoint
            }
            self.metrics_history.append(metric)
        except Exception as e:
            logger.error(f"记录请求指标错误: {e}")
    
    async def get_system_metrics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取系统指标"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM system_metrics 
                    WHERE timestamp >= datetime('now', '-{} hours')
                    ORDER BY timestamp DESC
                """.format(hours))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取系统指标错误: {e}")
            return []
    
    async def get_application_metrics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取应用指标"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM application_metrics 
                    WHERE timestamp >= datetime('now', '-{} hours')
                    ORDER BY timestamp DESC
                """.format(hours))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取应用指标错误: {e}")
            return []
    
    async def get_alerts(self, resolved: Optional[bool] = None, hours: int = 24) -> List[Dict[str, Any]]:
        """获取告警信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT * FROM alerts 
                    WHERE timestamp >= datetime('now', '-{} hours')
                """.format(hours)
                
                if resolved is not None:
                    query += f" AND resolved = {1 if resolved else 0}"
                
                query += " ORDER BY timestamp DESC"
                
                cursor = conn.execute(query)
                columns = [description[0] for description in cursor.description]
                alerts = []
                for row in cursor.fetchall():
                    alert_dict = dict(zip(columns, row))
                    if alert_dict.get('details'):
                        alert_dict['details'] = json.loads(alert_dict['details'])
                    alerts.append(alert_dict)
                return alerts
        except Exception as e:
            logger.error(f"获取告警信息错误: {e}")
            return []
    
    async def resolve_alert(self, alert_id: str):
        """解决告警"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE alerts 
                    SET resolved = TRUE, resolved_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), alert_id))
                conn.commit()
            
            # 更新内存中的告警
            for alert in self.alerts:
                if alert.id == alert_id:
                    alert.resolved = True
                    alert.resolved_at = datetime.now().isoformat()
                    break
                    
        except Exception as e:
            logger.error(f"解决告警错误: {e}")
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表盘数据"""
        try:
            # 获取最新指标
            system_metrics = await self.get_system_metrics(hours=1)
            app_metrics = await self.get_application_metrics(hours=1)
            alerts = await self.get_alerts(resolved=False, hours=24)
            
            # 计算统计信息
            current_system = system_metrics[0] if system_metrics else {}
            current_app = app_metrics[0] if app_metrics else {}
            
            return {
                'system': {
                    'cpu_percent': current_system.get('cpu_percent', 0),
                    'memory_percent': current_system.get('memory_percent', 0),
                    'disk_percent': current_system.get('disk_percent', 0),
                    'load_average': json.loads(current_system.get('load_average', '[]'))
                },
                'application': {
                    'response_time_avg': current_app.get('response_time_avg', 0),
                    'response_time_p95': current_app.get('response_time_p95', 0),
                    'response_time_p99': current_app.get('response_time_p99', 0),
                    'requests_per_second': current_app.get('requests_per_second', 0),
                    'error_rate': current_app.get('error_rate', 0),
                    'active_connections': current_app.get('active_connections', 0),
                    'cache_hit_rate': current_app.get('cache_hit_rate', 0)
                },
                'alerts': {
                    'total': len(alerts),
                    'critical': len([a for a in alerts if a.get('level') == 'CRITICAL']),
                    'error': len([a for a in alerts if a.get('level') == 'ERROR']),
                    'warning': len([a for a in alerts if a.get('level') == 'WARNING']),
                    'recent': alerts[:10]  # 最近10个告警
                },
                'status': 'healthy' if len([a for a in alerts if a.get('level') in ['ERROR', 'CRITICAL']]) == 0 else 'warning'
            }
        except Exception as e:
            logger.error(f"获取仪表盘数据错误: {e}")
            return {
                'system': {},
                'application': {},
                'alerts': {'total': 0, 'critical': 0, 'error': 0, 'warning': 0, 'recent': []},
                'status': 'error'
            }
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_enabled = False
        logger.info("生产环境监控已停止")

# 全局监控服务实例
monitoring_service: Optional[ProductionMonitoringService] = None

def get_monitoring_service() -> Optional[ProductionMonitoringService]:
    """获取监控服务实例"""
    return monitoring_service

def init_monitoring_service(config: Dict[str, Any]):
    """初始化监控服务"""
    global monitoring_service
    monitoring_service = ProductionMonitoringService(config)
    logger.info("生产环境监控服务已初始化")

def record_request_metrics(response_time: float, status_code: int, endpoint: str):
    """记录请求指标（全局函数）"""
    if monitoring_service:
        monitoring_service.record_request_metrics(response_time, status_code, endpoint)
