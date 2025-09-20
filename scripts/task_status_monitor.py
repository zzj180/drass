#!/usr/bin/env python3
"""
数据合规管理系统任务状态自动监控脚本
支持文件变化监控和自动状态更新
"""

import os
import json
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 配置文件路径
PROJECT_ROOT = Path(__file__).parent.parent
STATUS_FILE = PROJECT_ROOT / '.cursor' / 'task_status.json'
LOG_FILE = PROJECT_ROOT / 'logs' / 'task_monitor.log'

# 文件路径到任务ID的映射
FILE_TASK_MAPPING = {
    # 需求1：合规管理和风险识别
    'demo_datasets.py': 'REQ1-DEMO-001',
    'compliance_demo_service.py': 'REQ1-DEMO-002',
    'DataIngestionDemo.tsx': 'REQ1-DEMO-003',
    'compliance_demo.py': 'REQ1-DEMO-005',
    'monitoring_service.py': 'REQ1-MONITOR-001',
    'RealTimeMonitor.tsx': 'REQ1-MONITOR-003',
    
    # 需求2：文档处理优化
    'BatchUploadProgress.tsx': 'REQ2-OPT-001',
    'document_preprocessor.py': 'REQ2-OPT-002',
    
    # 需求3：审计日志
    'audit_log.py': 'REQ3-AUDIT-001',
    'audit_service.py': 'REQ3-AUDIT-002',
    'audit.py': 'REQ3-AUDIT-004',
    'audit_websocket.py': 'REQ3-RT-001',
    'AccessLogs.tsx': 'REQ3-RT-002',
}

# 任务完成检查条件
COMPLETION_CHECKS = {
    'REQ1-DEMO-001': {
        'file_pattern': r'DEMO_DATASETS\s*=\s*{',
        'min_lines': 20,
        'required_keys': ['personal_data', 'financial_data']
    },
    'REQ1-DEMO-002': {
        'file_pattern': r'class ComplianceDemoService:',
        'min_lines': 50,
        'required_methods': ['process_demo_data', '_classify_data']
    },
    'REQ1-DEMO-003': {
        'file_pattern': r'export const DataIngestionDemo',
        'min_lines': 30,
        'required_props': ['onDataProcessed']
    },
    'REQ3-AUDIT-001': {
        'file_pattern': r'class AuditLog\(Base\):',
        'min_lines': 15,
        'required_fields': ['timestamp', 'event_type', 'user_id']
    },
    'REQ3-AUDIT-002': {
        'file_pattern': r'class AuditService:',
        'min_lines': 80,
        'required_methods': ['log_audit_event', 'get_audit_logs']
    }
}


class TaskStatusMonitor(FileSystemEventHandler):
    """任务状态监控器"""
    
    def __init__(self):
        self.status_data = self.load_status()
        self.ensure_status_file()
        
    def load_status(self) -> Dict:
        """加载任务状态数据"""
        if STATUS_FILE.exists():
            try:
                with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {}
    
    def save_status(self):
        """保存任务状态数据"""
        STATUS_FILE.parent.mkdir(exist_ok=True)
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.status_data, f, indent=2, ensure_ascii=False)
    
    def ensure_status_file(self):
        """确保状态文件存在并初始化所有任务"""
        all_tasks = {
            # 需求1任务
            'REQ1-DEMO-001': {'name': '创建演示数据模板', 'status': 'pending'},
            'REQ1-DEMO-002': {'name': '实现ComplianceDemoService', 'status': 'pending'},
            'REQ1-DEMO-003': {'name': '开发DataIngestionDemo组件', 'status': 'pending'},
            'REQ1-DEMO-004': {'name': '集成合规规则引擎', 'status': 'pending'},
            'REQ1-DEMO-005': {'name': 'API接口开发和测试', 'status': 'pending'},
            'REQ1-MONITOR-001': {'name': 'ComplianceMonitoringService开发', 'status': 'pending'},
            'REQ1-MONITOR-002': {'name': '实时监控WebSocket服务', 'status': 'pending'},
            'REQ1-MONITOR-003': {'name': 'RealTimeMonitor前端组件', 'status': 'pending'},
            'REQ1-MONITOR-004': {'name': '告警规则引擎开发', 'status': 'pending'},
            'REQ1-MONITOR-005': {'name': '监控面板集成测试', 'status': 'pending'},
            
            # 需求2任务
            'REQ2-OPT-001': {'name': 'BatchUploadProgress组件开发', 'status': 'pending'},
            'REQ2-OPT-002': {'name': 'DocumentPreprocessor服务', 'status': 'pending'},
            'REQ2-OPT-003': {'name': '敏感信息检测算法', 'status': 'pending'},
            'REQ2-OPT-004': {'name': '文档预览功能', 'status': 'pending'},
            
            # 需求3任务
            'REQ3-AUDIT-001': {'name': '设计审计日志数据模型', 'status': 'pending'},
            'REQ3-AUDIT-002': {'name': '实现AuditService核心功能', 'status': 'pending'},
            'REQ3-AUDIT-003': {'name': '集成审计事件到现有API', 'status': 'pending'},
            'REQ3-AUDIT-004': {'name': '审计日志查询API开发', 'status': 'pending'},
            'REQ3-AUDIT-005': {'name': '数据库迁移和索引优化', 'status': 'pending'},
            'REQ3-RT-001': {'name': 'AuditWebSocketManager开发', 'status': 'pending'},
            'REQ3-RT-002': {'name': '前端AccessLogs组件增强', 'status': 'pending'},
            'REQ3-RT-003': {'name': '日志导出功能', 'status': 'pending'},
            'REQ3-RT-004': {'name': '实时通知系统', 'status': 'pending'},
            
            # 集成测试任务
            'INT-001': {'name': '端到端功能测试', 'status': 'pending'},
            'INT-002': {'name': '性能压力测试', 'status': 'pending'},
            'INT-003': {'name': '安全测试和漏洞扫描', 'status': 'pending'},
            'INT-004': {'name': '数据库性能优化', 'status': 'pending'},
            
            # 部署任务
            'DEP-001': {'name': '生产环境配置', 'status': 'pending'},
            'DEP-002': {'name': '数据迁移和备份', 'status': 'pending'},
            'DEP-003': {'name': '监控和日志配置', 'status': 'pending'},
        }
        
        # 合并现有状态，保留已有进度
        for task_id, task_info in all_tasks.items():
            if task_id not in self.status_data:
                self.status_data[task_id] = {
                    'name': task_info['name'],
                    'status': task_info['status'],
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'progress': 0,
                    'notes': []
                }
        
        self.save_status()
    
    def on_modified(self, event):
        """文件修改事件处理"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        filename = file_path.name
        
        if filename in FILE_TASK_MAPPING:
            task_id = FILE_TASK_MAPPING[filename]
            self.check_and_update_task(task_id, file_path)
    
    def on_created(self, event):
        """文件创建事件处理"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        filename = file_path.name
        
        if filename in FILE_TASK_MAPPING:
            task_id = FILE_TASK_MAPPING[filename]
            self.update_task_status(task_id, 'in_progress', f'文件已创建: {filename}')
            self.check_and_update_task(task_id, file_path)
    
    def check_and_update_task(self, task_id: str, file_path: Path):
        """检查任务完成情况并更新状态"""
        if task_id in COMPLETION_CHECKS:
            if self.is_task_completed(task_id, file_path):
                self.update_task_status(task_id, 'completed', f'任务自动检测完成: {file_path.name}')
            else:
                self.update_task_status(task_id, 'in_progress', f'文件已修改: {file_path.name}')
        else:
            # 没有特定检查条件的任务，根据文件存在性判断
            if file_path.exists() and file_path.stat().st_size > 100:  # 文件大于100字节
                self.update_task_status(task_id, 'in_progress', f'文件已修改: {file_path.name}')
    
    def is_task_completed(self, task_id: str, file_path: Path) -> bool:
        """检查任务是否完成"""
        if not file_path.exists():
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except:
                return False
        
        check_config = COMPLETION_CHECKS[task_id]
        
        # 检查文件模式匹配
        if 'file_pattern' in check_config:
            if not re.search(check_config['file_pattern'], content):
                return False
        
        # 检查最小行数
        if 'min_lines' in check_config:
            lines = content.split('\n')
            if len(lines) < check_config['min_lines']:
                return False
        
        # 检查必需的方法或键
        if 'required_methods' in check_config:
            for method in check_config['required_methods']:
                if f'def {method}' not in content and f'async def {method}' not in content:
                    return False
        
        if 'required_keys' in check_config:
            for key in check_config['required_keys']:
                if f'"{key}"' not in content and f"'{key}'" not in content:
                    return False
        
        if 'required_fields' in check_config:
            for field in check_config['required_fields']:
                if field not in content:
                    return False
        
        if 'required_props' in check_config:
            for prop in check_config['required_props']:
                if prop not in content:
                    return False
        
        return True
    
    def update_task_status(self, task_id: str, status: str, note: str = None):
        """更新任务状态"""
        if task_id not in self.status_data:
            return
        
        old_status = self.status_data[task_id]['status']
        if old_status != status:
            self.status_data[task_id]['status'] = status
            self.status_data[task_id]['updated_at'] = datetime.now().isoformat()
            
            # 更新进度
            if status == 'completed':
                self.status_data[task_id]['progress'] = 100
            elif status == 'in_progress':
                self.status_data[task_id]['progress'] = max(
                    self.status_data[task_id].get('progress', 0), 50
                )
            
            # 添加备注
            if note:
                if 'notes' not in self.status_data[task_id]:
                    self.status_data[task_id]['notes'] = []
                self.status_data[task_id]['notes'].append({
                    'timestamp': datetime.now().isoformat(),
                    'note': note
                })
            
            self.save_status()
            self.log_status_change(task_id, old_status, status, note)
    
    def log_status_change(self, task_id: str, old_status: str, new_status: str, note: str = None):
        """记录状态变化日志"""
        LOG_FILE.parent.mkdir(exist_ok=True)
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'task_id': task_id,
            'task_name': self.status_data[task_id]['name'],
            'old_status': old_status,
            'new_status': new_status,
            'note': note
        }
        
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 任务 {task_id} 状态: {old_status} → {new_status}")
        if note:
            print(f"    备注: {note}")
    
    def get_progress_summary(self) -> Dict:
        """获取进度总结"""
        total_tasks = len(self.status_data)
        completed = sum(1 for task in self.status_data.values() if task['status'] == 'completed')
        in_progress = sum(1 for task in self.status_data.values() if task['status'] == 'in_progress')
        pending = total_tasks - completed - in_progress
        
        return {
            'total_tasks': total_tasks,
            'completed': completed,
            'in_progress': in_progress,
            'pending': pending,
            'completion_rate': round((completed / total_tasks) * 100, 1) if total_tasks > 0 else 0
        }


def main():
    """主函数"""
    print("🚀 启动数据合规管理系统任务状态监控器")
    print("=" * 50)
    
    # 创建监控器
    monitor = TaskStatusMonitor()
    
    # 显示初始状态
    summary = monitor.get_progress_summary()
    print(f"📊 任务总览:")
    print(f"   总任务数: {summary['total_tasks']}")
    print(f"   已完成: {summary['completed']}")
    print(f"   进行中: {summary['in_progress']}")
    print(f"   待开始: {summary['pending']}")
    print(f"   完成率: {summary['completion_rate']}%")
    print("=" * 50)
    
    # 设置文件监控
    observer = Observer()
    
    # 监控关键目录
    watch_dirs = [
        PROJECT_ROOT / 'services' / 'main-app' / 'app' / 'services',
        PROJECT_ROOT / 'services' / 'main-app' / 'app' / 'api',
        PROJECT_ROOT / 'services' / 'main-app' / 'app' / 'models',
        PROJECT_ROOT / 'services' / 'main-app' / 'app' / 'data',
        PROJECT_ROOT / 'services' / 'main-app' / 'app' / 'websocket',
        PROJECT_ROOT / 'frontend' / 'src' / 'components',
    ]
    
    for watch_dir in watch_dirs:
        if watch_dir.exists():
            observer.schedule(monitor, str(watch_dir), recursive=True)
            print(f"📁 监控目录: {watch_dir}")
    
    print("=" * 50)
    print("🔍 开始监控文件变化...")
    print("按 Ctrl+C 停止监控")
    
    # 启动监控
    observer.start()
    
    try:
        while True:
            time.sleep(10)  # 每10秒显示一次进度
            summary = monitor.get_progress_summary()
            print(f"\r⏰ {datetime.now().strftime('%H:%M:%S')} | "
                  f"完成率: {summary['completion_rate']}% "
                  f"({summary['completed']}/{summary['total_tasks']})", end='', flush=True)
    except KeyboardInterrupt:
        observer.stop()
        print("\n\n🛑 监控已停止")
        
        # 显示最终状态
        summary = monitor.get_progress_summary()
        print(f"\n📈 最终进度报告:")
        print(f"   完成率: {summary['completion_rate']}%")
        print(f"   已完成任务: {summary['completed']}")
        print(f"   进行中任务: {summary['in_progress']}")
        print(f"   待开始任务: {summary['pending']}")
    
    observer.join()


if __name__ == '__main__':
    main()

