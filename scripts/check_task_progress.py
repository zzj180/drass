#!/usr/bin/env python3
"""
任务进度查询脚本
提供命令行方式查询任务状态和进度
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# 配置
PROJECT_ROOT = Path(__file__).parent.parent
STATUS_FILE = PROJECT_ROOT / '.cursor' / 'task_status.json'

def load_task_status() -> Dict:
    """加载任务状态"""
    if STATUS_FILE.exists():
        try:
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def get_progress_summary(status_data: Dict) -> Dict:
    """计算进度总结"""
    if not status_data:
        return {
            'total_tasks': 0,
            'completed': 0,
            'in_progress': 0,
            'pending': 0,
            'completion_rate': 0
        }
    
    total_tasks = len(status_data)
    completed = sum(1 for task in status_data.values() if task.get('status') == 'completed')
    in_progress = sum(1 for task in status_data.values() if task.get('status') == 'in_progress')
    pending = total_tasks - completed - in_progress
    
    return {
        'total_tasks': total_tasks,
        'completed': completed,
        'in_progress': in_progress,
        'pending': pending,
        'completion_rate': round((completed / total_tasks) * 100, 1) if total_tasks > 0 else 0
    }

def print_progress_bar(percentage: float, width: int = 30):
    """打印进度条"""
    filled = int(width * percentage / 100)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}] {percentage}%"

def show_summary():
    """显示进度总结"""
    status_data = load_task_status()
    summary = get_progress_summary(status_data)
    
    print("📊 数据合规管理系统 - 任务进度总览")
    print("=" * 50)
    print(f"总任务数: {summary['total_tasks']}")
    print(f"已完成: {summary['completed']} ✅")
    print(f"进行中: {summary['in_progress']} 🔄")
    print(f"待开始: {summary['pending']} ⏳")
    print()
    print("整体进度:")
    print(print_progress_bar(summary['completion_rate']))
    print()

def show_tasks(status_filter: str = None):
    """显示任务列表"""
    status_data = load_task_status()
    
    if not status_data:
        print("❌ 没有找到任务数据")
        return
    
    # 状态图标映射
    status_icons = {
        'pending': '⏳',
        'in_progress': '🔄',
        'completed': '✅'
    }
    
    # 过滤任务
    filtered_tasks = []
    for task_id, task_info in status_data.items():
        if status_filter and task_info.get('status') != status_filter:
            continue
        filtered_tasks.append((task_id, task_info))
    
    if not filtered_tasks:
        print(f"❌ 没有找到状态为 '{status_filter}' 的任务")
        return
    
    print(f"📋 任务列表 ({len(filtered_tasks)} 个任务)")
    if status_filter:
        print(f"筛选条件: {status_filter}")
    print("=" * 80)
    
    # 按需求分组
    req_groups = {
        'REQ1': '需求1：合规管理和风险识别',
        'REQ2': '需求2：文档处理优化',
        'REQ3': '需求3：审计日志功能',
        'INT': '集成测试',
        'DEP': '部署任务'
    }
    
    for prefix, group_name in req_groups.items():
        group_tasks = [(tid, tinfo) for tid, tinfo in filtered_tasks if tid.startswith(prefix)]
        
        if group_tasks:
            print(f"\n🎯 {group_name}")
            print("-" * 40)
            
            for task_id, task_info in group_tasks:
                status = task_info.get('status', 'unknown')
                icon = status_icons.get(status, '❓')
                progress = task_info.get('progress', 0)
                updated = task_info.get('updated_at', '')
                
                # 格式化更新时间
                if updated:
                    try:
                        dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                        time_str = dt.strftime('%m-%d %H:%M')
                    except:
                        time_str = updated[:16] if len(updated) > 16 else updated
                else:
                    time_str = '未知'
                
                print(f"  {icon} {task_id:<15} {task_info.get('name', '未命名')[:40]:<40} {progress:>3}% [{time_str}]")

def show_milestones():
    """显示里程碑进度"""
    status_data = load_task_status()
    
    milestones = {
        'stage1': {
            'name': '阶段1：核心功能完善',
            'tasks': ['REQ1-DEMO-001', 'REQ1-DEMO-002', 'REQ1-DEMO-003', 'REQ1-DEMO-004', 'REQ1-DEMO-005',
                     'REQ3-AUDIT-001', 'REQ3-AUDIT-002', 'REQ3-AUDIT-003', 'REQ3-AUDIT-004', 'REQ3-AUDIT-005']
        },
        'stage2': {
            'name': '阶段2：高级功能开发',
            'tasks': ['REQ1-MONITOR-001', 'REQ1-MONITOR-002', 'REQ1-MONITOR-003', 'REQ1-MONITOR-004', 'REQ1-MONITOR-005',
                     'REQ2-OPT-001', 'REQ2-OPT-002', 'REQ2-OPT-003', 'REQ2-OPT-004',
                     'REQ3-RT-001', 'REQ3-RT-002', 'REQ3-RT-003', 'REQ3-RT-004']
        },
        'stage3': {
            'name': '阶段3：系统优化和部署',
            'tasks': ['INT-001', 'INT-002', 'INT-003', 'INT-004', 'DEP-001', 'DEP-002', 'DEP-003']
        }
    }
    
    print("🎯 里程碑进度")
    print("=" * 50)
    
    for stage_id, stage_info in milestones.items():
        stage_tasks = stage_info['tasks']
        completed_tasks = sum(1 for task_id in stage_tasks 
                             if status_data.get(task_id, {}).get('status') == 'completed')
        total_tasks = len(stage_tasks)
        completion_rate = round((completed_tasks / total_tasks) * 100, 1) if total_tasks > 0 else 0
        
        print(f"\n📍 {stage_info['name']}")
        print(f"   进度: {completed_tasks}/{total_tasks} 任务完成")
        print(f"   {print_progress_bar(completion_rate)}")

def show_task_detail(task_id: str):
    """显示任务详情"""
    status_data = load_task_status()
    
    if task_id not in status_data:
        print(f"❌ 任务 {task_id} 不存在")
        return
    
    task = status_data[task_id]
    
    print(f"📋 任务详情: {task_id}")
    print("=" * 50)
    print(f"任务名称: {task.get('name', '未命名')}")
    print(f"当前状态: {task.get('status', '未知')}")
    print(f"完成进度: {task.get('progress', 0)}%")
    print(f"创建时间: {task.get('created_at', '未知')}")
    print(f"更新时间: {task.get('updated_at', '未知')}")
    
    # 显示备注
    notes = task.get('notes', [])
    if notes:
        print(f"\n📝 备注记录 ({len(notes)} 条):")
        print("-" * 30)
        for i, note in enumerate(reversed(notes[-5:]), 1):  # 显示最新的5条
            timestamp = note.get('timestamp', '')
            content = note.get('note', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%m-%d %H:%M')
                except:
                    time_str = timestamp[:16]
            else:
                time_str = '未知时间'
            
            print(f"  {i}. [{time_str}] {content}")
        
        if len(notes) > 5:
            print(f"  ... (还有 {len(notes) - 5} 条历史记录)")
    else:
        print("\n📝 暂无备注记录")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据合规管理系统任务进度查询')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 总览命令
    subparsers.add_parser('summary', help='显示进度总览')
    
    # 任务列表命令
    tasks_parser = subparsers.add_parser('tasks', help='显示任务列表')
    tasks_parser.add_argument('--status', choices=['pending', 'in_progress', 'completed'], 
                             help='按状态筛选任务')
    
    # 里程碑命令
    subparsers.add_parser('milestones', help='显示里程碑进度')
    
    # 任务详情命令
    detail_parser = subparsers.add_parser('detail', help='显示任务详情')
    detail_parser.add_argument('task_id', help='任务ID')
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        # 默认显示总览
        show_summary()
        return
    
    if args.command == 'summary':
        show_summary()
    elif args.command == 'tasks':
        show_tasks(args.status)
    elif args.command == 'milestones':
        show_milestones()
    elif args.command == 'detail':
        show_task_detail(args.task_id)

if __name__ == '__main__':
    main()

