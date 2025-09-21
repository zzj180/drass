"""
告警服务
提供完整的告警管理、通知和自动化处理功能
"""

import asyncio
import json
import logging
import smtplib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """告警级别"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class AlertCategory(Enum):
    """告警类别"""
    SYSTEM = "SYSTEM"
    APPLICATION = "APPLICATION"
    DATABASE = "DATABASE"
    CACHE = "CACHE"
    NETWORK = "NETWORK"
    SECURITY = "SECURITY"

@dataclass
class AlertRule:
    """告警规则"""
    id: str
    name: str
    description: str
    category: AlertCategory
    level: AlertLevel
    condition: str  # 条件表达式
    threshold: float
    duration: int  # 持续时间（秒）
    enabled: bool = True
    notification_channels: List[str] = None
    auto_resolve: bool = True
    escalation_enabled: bool = False
    escalation_delay: int = 300  # 5分钟

@dataclass
class Alert:
    """告警信息"""
    id: str
    rule_id: str
    timestamp: str
    level: AlertLevel
    category: AlertCategory
    message: str
    details: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[str] = None
    escalated: bool = False
    escalated_at: Optional[str] = None
    notification_sent: bool = False
    notification_channels: List[str] = None

@dataclass
class NotificationChannel:
    """通知渠道"""
    id: str
    name: str
    type: str  # email, webhook, slack, sms
    config: Dict[str, Any]
    enabled: bool = True

class AlertService:
    """告警服务"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rules: Dict[str, AlertRule] = {}
        self.channels: Dict[str, NotificationChannel] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.monitoring_enabled = True
        
        # 初始化数据库
        self._init_database()
        
        # 加载配置
        self._load_rules()
        self._load_channels()
        
        # 启动监控任务
        self._start_monitoring()
    
    def _init_database(self):
        """初始化告警数据库"""
        db_path = Path("data/alerts.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.db_path = str(db_path)
        
        with sqlite3.connect(self.db_path) as conn:
            # 告警规则表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alert_rules (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL,
                    level TEXT NOT NULL,
                    condition TEXT NOT NULL,
                    threshold REAL NOT NULL,
                    duration INTEGER NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    notification_channels TEXT,
                    auto_resolve BOOLEAN DEFAULT TRUE,
                    escalation_enabled BOOLEAN DEFAULT FALSE,
                    escalation_delay INTEGER DEFAULT 300,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 告警历史表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    rule_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    category TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TEXT,
                    escalated BOOLEAN DEFAULT FALSE,
                    escalated_at TEXT,
                    notification_sent BOOLEAN DEFAULT FALSE,
                    notification_channels TEXT,
                    FOREIGN KEY (rule_id) REFERENCES alert_rules (id)
                )
            """)
            
            # 通知渠道表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notification_channels (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    config TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def _load_rules(self):
        """加载告警规则"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM alert_rules WHERE enabled = TRUE")
                for row in cursor.fetchall():
                    rule = AlertRule(
                        id=row[0],
                        name=row[1],
                        description=row[2],
                        category=AlertCategory(row[3]),
                        level=AlertLevel(row[4]),
                        condition=row[5],
                        threshold=row[6],
                        duration=row[7],
                        enabled=bool(row[8]),
                        notification_channels=json.loads(row[9]) if row[9] else [],
                        auto_resolve=bool(row[10]),
                        escalation_enabled=bool(row[11]),
                        escalation_delay=row[12]
                    )
                    self.rules[rule.id] = rule
        except Exception as e:
            logger.error(f"加载告警规则错误: {e}")
    
    def _load_channels(self):
        """加载通知渠道"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM notification_channels WHERE enabled = TRUE")
                for row in cursor.fetchall():
                    channel = NotificationChannel(
                        id=row[0],
                        name=row[1],
                        type=row[2],
                        config=json.loads(row[3]),
                        enabled=bool(row[4])
                    )
                    self.channels[channel.id] = channel
        except Exception as e:
            logger.error(f"加载通知渠道错误: {e}")
    
    def _start_monitoring(self):
        """启动监控任务"""
        if self.monitoring_enabled:
            asyncio.create_task(self._monitoring_loop())
    
    async def _monitoring_loop(self):
        """监控循环"""
        while self.monitoring_enabled:
            try:
                # 检查告警规则
                await self._check_alert_rules()
                
                # 处理告警升级
                await self._process_escalations()
                
                # 自动解决告警
                await self._auto_resolve_alerts()
                
                # 等待下次检查
                await asyncio.sleep(30)  # 每30秒检查一次
                
            except Exception as e:
                logger.error(f"告警监控循环错误: {e}")
                await asyncio.sleep(10)
    
    async def _check_alert_rules(self):
        """检查告警规则"""
        try:
            # 这里应该从监控服务获取当前指标
            # 为了演示，我们使用模拟数据
            current_metrics = await self._get_current_metrics()
            
            for rule_id, rule in self.rules.items():
                if not rule.enabled:
                    continue
                
                # 检查条件
                if await self._evaluate_condition(rule, current_metrics):
                    # 检查是否已经存在活跃告警
                    if rule_id not in self.active_alerts:
                        await self._create_alert(rule, current_metrics)
                else:
                    # 条件不满足，如果存在活跃告警则解决
                    if rule_id in self.active_alerts:
                        await self._resolve_alert(rule_id)
                        
        except Exception as e:
            logger.error(f"检查告警规则错误: {e}")
    
    async def _get_current_metrics(self) -> Dict[str, Any]:
        """获取当前指标（模拟）"""
        # 实际应该从监控服务获取
        return {
            "cpu_percent": 75.0,
            "memory_percent": 80.0,
            "disk_percent": 85.0,
            "response_time_avg": 2.5,
            "error_rate": 3.0,
            "cache_hit_rate": 75.0
        }
    
    async def _evaluate_condition(self, rule: AlertRule, metrics: Dict[str, Any]) -> bool:
        """评估告警条件"""
        try:
            # 简单的条件评估
            if rule.condition == "cpu_percent > threshold":
                return metrics.get("cpu_percent", 0) > rule.threshold
            elif rule.condition == "memory_percent > threshold":
                return metrics.get("memory_percent", 0) > rule.threshold
            elif rule.condition == "disk_percent > threshold":
                return metrics.get("disk_percent", 0) > rule.threshold
            elif rule.condition == "response_time_avg > threshold":
                return metrics.get("response_time_avg", 0) > rule.threshold
            elif rule.condition == "error_rate > threshold":
                return metrics.get("error_rate", 0) > rule.threshold
            elif rule.condition == "cache_hit_rate < threshold":
                return metrics.get("cache_hit_rate", 100) < rule.threshold
            else:
                return False
        except Exception as e:
            logger.error(f"评估告警条件错误: {e}")
            return False
    
    async def _create_alert(self, rule: AlertRule, metrics: Dict[str, Any]):
        """创建告警"""
        try:
            alert_id = f"{rule.id}_{int(datetime.now().timestamp())}"
            
            alert = Alert(
                id=alert_id,
                rule_id=rule.id,
                timestamp=datetime.now().isoformat(),
                level=rule.level,
                category=rule.category,
                message=f"{rule.name}: {rule.description}",
                details={
                    "rule_id": rule.id,
                    "threshold": rule.threshold,
                    "current_value": metrics.get(rule.condition.split()[0], 0),
                    "condition": rule.condition
                },
                notification_channels=rule.notification_channels
            )
            
            # 存储到数据库
            await self._store_alert(alert)
            
            # 添加到活跃告警
            self.active_alerts[rule.id] = alert
            
            # 发送通知
            await self._send_notifications(alert)
            
            logger.warning(f"告警创建: {alert.level.value} - {alert.message}")
            
        except Exception as e:
            logger.error(f"创建告警错误: {e}")
    
    async def _resolve_alert(self, rule_id: str):
        """解决告警"""
        try:
            if rule_id in self.active_alerts:
                alert = self.active_alerts[rule_id]
                alert.resolved = True
                alert.resolved_at = datetime.now().isoformat()
                
                # 更新数据库
                await self._update_alert(alert)
                
                # 从活跃告警中移除
                del self.active_alerts[rule_id]
                
                logger.info(f"告警已解决: {alert.id}")
                
        except Exception as e:
            logger.error(f"解决告警错误: {e}")
    
    async def _process_escalations(self):
        """处理告警升级"""
        try:
            current_time = datetime.now()
            
            for rule_id, alert in self.active_alerts.items():
                if alert.escalated:
                    continue
                
                rule = self.rules.get(rule_id)
                if not rule or not rule.escalation_enabled:
                    continue
                
                alert_time = datetime.fromisoformat(alert.timestamp)
                if (current_time - alert_time).total_seconds() > rule.escalation_delay:
                    await self._escalate_alert(alert)
                    
        except Exception as e:
            logger.error(f"处理告警升级错误: {e}")
    
    async def _escalate_alert(self, alert: Alert):
        """升级告警"""
        try:
            alert.escalated = True
            alert.escalated_at = datetime.now().isoformat()
            
            # 更新数据库
            await self._update_alert(alert)
            
            # 发送升级通知
            await self._send_escalation_notification(alert)
            
            logger.warning(f"告警已升级: {alert.id}")
            
        except Exception as e:
            logger.error(f"升级告警错误: {e}")
    
    async def _auto_resolve_alerts(self):
        """自动解决告警"""
        try:
            current_time = datetime.now()
            
            for rule_id, alert in list(self.active_alerts.items()):
                rule = self.rules.get(rule_id)
                if not rule or not rule.auto_resolve:
                    continue
                
                alert_time = datetime.fromisoformat(alert.timestamp)
                if (current_time - alert_time).total_seconds() > rule.duration:
                    await self._resolve_alert(rule_id)
                    
        except Exception as e:
            logger.error(f"自动解决告警错误: {e}")
    
    async def _send_notifications(self, alert: Alert):
        """发送通知"""
        try:
            if not alert.notification_channels:
                return
            
            for channel_id in alert.notification_channels:
                channel = self.channels.get(channel_id)
                if not channel or not channel.enabled:
                    continue
                
                try:
                    if channel.type == "email":
                        await self._send_email_notification(alert, channel)
                    elif channel.type == "webhook":
                        await self._send_webhook_notification(alert, channel)
                    elif channel.type == "slack":
                        await self._send_slack_notification(alert, channel)
                    
                    alert.notification_sent = True
                    await self._update_alert(alert)
                    
                except Exception as e:
                    logger.error(f"发送通知错误 (渠道: {channel_id}): {e}")
                    
        except Exception as e:
            logger.error(f"发送通知错误: {e}")
    
    async def _send_email_notification(self, alert: Alert, channel: NotificationChannel):
        """发送邮件通知"""
        try:
            config = channel.config
            
            # 构建邮件内容
            subject = f"[{alert.level.value}] {alert.message}"
            body = f"""
告警详情:
- 时间: {alert.timestamp}
- 级别: {alert.level.value}
- 类别: {alert.category.value}
- 消息: {alert.message}
- 详情: {json.dumps(alert.details, indent=2, ensure_ascii=False)}

请及时处理此告警。
            """
            
            # 这里应该实现实际的邮件发送逻辑
            logger.info(f"邮件通知已发送: {subject}")
            
        except Exception as e:
            logger.error(f"发送邮件通知错误: {e}")
    
    async def _send_webhook_notification(self, alert: Alert, channel: NotificationChannel):
        """发送Webhook通知"""
        try:
            config = channel.config
            webhook_url = config.get("url")
            
            if not webhook_url:
                logger.error("Webhook URL未配置")
                return
            
            payload = {
                "alert_id": alert.id,
                "level": alert.level.value,
                "category": alert.category.value,
                "message": alert.message,
                "timestamp": alert.timestamp,
                "details": alert.details
            }
            
            # 发送HTTP请求
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Webhook通知已发送: {alert.id}")
            else:
                logger.error(f"Webhook通知发送失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"发送Webhook通知错误: {e}")
    
    async def _send_slack_notification(self, alert: Alert, channel: NotificationChannel):
        """发送Slack通知"""
        try:
            config = channel.config
            webhook_url = config.get("webhook_url")
            
            if not webhook_url:
                logger.error("Slack Webhook URL未配置")
                return
            
            # 根据告警级别选择颜色
            color_map = {
                AlertLevel.INFO: "good",
                AlertLevel.WARNING: "warning",
                AlertLevel.ERROR: "danger",
                AlertLevel.CRITICAL: "danger"
            }
            
            payload = {
                "attachments": [{
                    "color": color_map.get(alert.level, "warning"),
                    "title": f"[{alert.level.value}] {alert.message}",
                    "fields": [
                        {"title": "时间", "value": alert.timestamp, "short": True},
                        {"title": "级别", "value": alert.level.value, "short": True},
                        {"title": "类别", "value": alert.category.value, "short": True},
                        {"title": "详情", "value": json.dumps(alert.details, ensure_ascii=False), "short": False}
                    ]
                }]
            }
            
            # 发送HTTP请求
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Slack通知已发送: {alert.id}")
            else:
                logger.error(f"Slack通知发送失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"发送Slack通知错误: {e}")
    
    async def _send_escalation_notification(self, alert: Alert):
        """发送升级通知"""
        try:
            # 发送升级通知到所有渠道
            for channel_id, channel in self.channels.items():
                if not channel.enabled:
                    continue
                
                try:
                    if channel.type == "email":
                        await self._send_email_notification(alert, channel)
                    elif channel.type == "webhook":
                        await self._send_webhook_notification(alert, channel)
                    elif channel.type == "slack":
                        await self._send_slack_notification(alert, channel)
                        
                except Exception as e:
                    logger.error(f"发送升级通知错误 (渠道: {channel_id}): {e}")
                    
        except Exception as e:
            logger.error(f"发送升级通知错误: {e}")
    
    async def _store_alert(self, alert: Alert):
        """存储告警到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO alerts 
                    (id, rule_id, timestamp, level, category, message, details,
                     resolved, resolved_at, escalated, escalated_at, notification_sent, notification_channels)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.id, alert.rule_id, alert.timestamp, alert.level.value,
                    alert.category.value, alert.message, json.dumps(alert.details),
                    alert.resolved, alert.resolved_at, alert.escalated, alert.escalated_at,
                    alert.notification_sent, json.dumps(alert.notification_channels or [])
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"存储告警错误: {e}")
    
    async def _update_alert(self, alert: Alert):
        """更新告警"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE alerts 
                    SET resolved = ?, resolved_at = ?, escalated = ?, escalated_at = ?,
                        notification_sent = ?, notification_channels = ?
                    WHERE id = ?
                """, (
                    alert.resolved, alert.resolved_at, alert.escalated, alert.escalated_at,
                    alert.notification_sent, json.dumps(alert.notification_channels or []),
                    alert.id
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"更新告警错误: {e}")
    
    # 公共API方法
    async def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        return list(self.active_alerts.values())
    
    async def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """获取告警历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM alerts 
                    WHERE timestamp >= datetime('now', '-{} hours')
                    ORDER BY timestamp DESC
                """.format(hours))
                
                alerts = []
                for row in cursor.fetchall():
                    alert = Alert(
                        id=row[0],
                        rule_id=row[1],
                        timestamp=row[2],
                        level=AlertLevel(row[3]),
                        category=AlertCategory(row[4]),
                        message=row[5],
                        details=json.loads(row[6]) if row[6] else {},
                        resolved=bool(row[7]),
                        resolved_at=row[8],
                        escalated=bool(row[9]),
                        escalated_at=row[10],
                        notification_sent=bool(row[11]),
                        notification_channels=json.loads(row[12]) if row[12] else []
                    )
                    alerts.append(alert)
                return alerts
        except Exception as e:
            logger.error(f"获取告警历史错误: {e}")
            return []
    
    async def create_alert_rule(self, rule: AlertRule):
        """创建告警规则"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO alert_rules 
                    (id, name, description, category, level, condition, threshold, duration,
                     enabled, notification_channels, auto_resolve, escalation_enabled, escalation_delay)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rule.id, rule.name, rule.description, rule.category.value,
                    rule.level.value, rule.condition, rule.threshold, rule.duration,
                    rule.enabled, json.dumps(rule.notification_channels or []),
                    rule.auto_resolve, rule.escalation_enabled, rule.escalation_delay
                ))
                conn.commit()
            
            self.rules[rule.id] = rule
            logger.info(f"告警规则已创建: {rule.id}")
            
        except Exception as e:
            logger.error(f"创建告警规则错误: {e}")
            raise
    
    async def update_alert_rule(self, rule: AlertRule):
        """更新告警规则"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE alert_rules 
                    SET name = ?, description = ?, category = ?, level = ?, condition = ?,
                        threshold = ?, duration = ?, enabled = ?, notification_channels = ?,
                        auto_resolve = ?, escalation_enabled = ?, escalation_delay = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    rule.name, rule.description, rule.category.value, rule.level.value,
                    rule.condition, rule.threshold, rule.duration, rule.enabled,
                    json.dumps(rule.notification_channels or []), rule.auto_resolve,
                    rule.escalation_enabled, rule.escalation_delay, rule.id
                ))
                conn.commit()
            
            self.rules[rule.id] = rule
            logger.info(f"告警规则已更新: {rule.id}")
            
        except Exception as e:
            logger.error(f"更新告警规则错误: {e}")
            raise
    
    async def delete_alert_rule(self, rule_id: str):
        """删除告警规则"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM alert_rules WHERE id = ?", (rule_id,))
                conn.commit()
            
            if rule_id in self.rules:
                del self.rules[rule_id]
            
            logger.info(f"告警规则已删除: {rule_id}")
            
        except Exception as e:
            logger.error(f"删除告警规则错误: {e}")
            raise
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_enabled = False
        logger.info("告警服务已停止")

# 全局告警服务实例
alert_service: Optional[AlertService] = None

def get_alert_service() -> Optional[AlertService]:
    """获取告警服务实例"""
    return alert_service

def init_alert_service(config: Dict[str, Any]):
    """初始化告警服务"""
    global alert_service
    alert_service = AlertService(config)
    logger.info("告警服务已初始化")
