#!/usr/bin/env python3
"""
任务状态WebSocket服务器
提供实时任务状态推送和REST API查询
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# 配置
PROJECT_ROOT = Path(__file__).parent.parent
STATUS_FILE = PROJECT_ROOT / '.cursor' / 'task_status.json'
LOG_FILE = PROJECT_ROOT / 'logs' / 'task_monitor.log'

app = FastAPI(title="任务状态服务器", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.last_status = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # 发送当前状态
        current_status = load_task_status()
        await websocket.send_text(json.dumps({
            'type': 'initial_status',
            'data': current_status
        }))
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """广播消息到所有连接的客户端"""
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(connection)
        
        # 清理断开的连接
        for connection in disconnected:
            self.active_connections.remove(connection)

manager = ConnectionManager()

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

def get_milestone_progress(status_data: Dict) -> Dict:
    """计算里程碑进度"""
    milestones = {
        'stage1': {  # 阶段1：核心功能完善
            'name': '核心功能完善',
            'tasks': ['REQ1-DEMO-001', 'REQ1-DEMO-002', 'REQ1-DEMO-003', 'REQ1-DEMO-004', 'REQ1-DEMO-005',
                     'REQ3-AUDIT-001', 'REQ3-AUDIT-002', 'REQ3-AUDIT-003', 'REQ3-AUDIT-004', 'REQ3-AUDIT-005']
        },
        'stage2': {  # 阶段2：高级功能开发
            'name': '高级功能开发',
            'tasks': ['REQ1-MONITOR-001', 'REQ1-MONITOR-002', 'REQ1-MONITOR-003', 'REQ1-MONITOR-004', 'REQ1-MONITOR-005',
                     'REQ2-OPT-001', 'REQ2-OPT-002', 'REQ2-OPT-003', 'REQ2-OPT-004',
                     'REQ3-RT-001', 'REQ3-RT-002', 'REQ3-RT-003', 'REQ3-RT-004']
        },
        'stage3': {  # 阶段3：系统优化和部署
            'name': '系统优化和部署',
            'tasks': ['INT-001', 'INT-002', 'INT-003', 'INT-004', 'DEP-001', 'DEP-002', 'DEP-003']
        }
    }
    
    result = {}
    for stage_id, stage_info in milestones.items():
        stage_tasks = stage_info['tasks']
        completed_tasks = sum(1 for task_id in stage_tasks 
                             if status_data.get(task_id, {}).get('status') == 'completed')
        total_tasks = len(stage_tasks)
        
        result[stage_id] = {
            'name': stage_info['name'],
            'completed_tasks': completed_tasks,
            'total_tasks': total_tasks,
            'completion_rate': round((completed_tasks / total_tasks) * 100, 1) if total_tasks > 0 else 0
        }
    
    return result

@app.websocket("/ws/task-status")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接活跃
            data = await websocket.receive_text()
            # 可以处理客户端发送的命令
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/task-status")
async def get_task_status():
    """获取所有任务状态"""
    status_data = load_task_status()
    summary = get_progress_summary(status_data)
    milestones = get_milestone_progress(status_data)
    
    return JSONResponse({
        'status': 'success',
        'data': {
            'tasks': status_data,
            'summary': summary,
            'milestones': milestones,
            'updated_at': datetime.now().isoformat()
        }
    })

@app.get("/api/task-status/{task_id}")
async def get_task_detail(task_id: str):
    """获取特定任务状态"""
    status_data = load_task_status()
    
    if task_id not in status_data:
        return JSONResponse(
            status_code=404,
            content={'status': 'error', 'message': f'任务 {task_id} 不存在'}
        )
    
    return JSONResponse({
        'status': 'success',
        'data': status_data[task_id]
    })

@app.post("/api/task-status/{task_id}")
async def update_task_status(task_id: str, request_data: dict):
    """手动更新任务状态"""
    status_data = load_task_status()
    
    if task_id not in status_data:
        return JSONResponse(
            status_code=404,
            content={'status': 'error', 'message': f'任务 {task_id} 不存在'}
        )
    
    # 更新状态
    old_status = status_data[task_id]['status']
    new_status = request_data.get('status', old_status)
    note = request_data.get('note', '')
    
    status_data[task_id]['status'] = new_status
    status_data[task_id]['updated_at'] = datetime.now().isoformat()
    
    if new_status == 'completed':
        status_data[task_id]['progress'] = 100
    elif new_status == 'in_progress':
        status_data[task_id]['progress'] = max(
            status_data[task_id].get('progress', 0), 50
        )
    
    if note:
        if 'notes' not in status_data[task_id]:
            status_data[task_id]['notes'] = []
        status_data[task_id]['notes'].append({
            'timestamp': datetime.now().isoformat(),
            'note': note
        })
    
    # 保存状态
    STATUS_FILE.parent.mkdir(exist_ok=True)
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, indent=2, ensure_ascii=False)
    
    # 广播更新
    await manager.broadcast({
        'type': 'task_updated',
        'data': {
            'task_id': task_id,
            'task': status_data[task_id],
            'old_status': old_status,
            'new_status': new_status
        }
    })
    
    return JSONResponse({
        'status': 'success',
        'message': f'任务 {task_id} 状态已更新为 {new_status}'
    })

@app.get("/api/progress-summary")
async def get_progress_summary_api():
    """获取进度总结"""
    status_data = load_task_status()
    summary = get_progress_summary(status_data)
    milestones = get_milestone_progress(status_data)
    
    return JSONResponse({
        'status': 'success',
        'data': {
            'summary': summary,
            'milestones': milestones,
            'updated_at': datetime.now().isoformat()
        }
    })

@app.get("/api/task-logs")
async def get_task_logs(limit: int = 50):
    """获取任务变更日志"""
    logs = []
    
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 取最新的N条记录
                for line in lines[-limit:]:
                    try:
                        log_entry = json.loads(line.strip())
                        logs.append(log_entry)
                    except:
                        continue
        except:
            pass
    
    return JSONResponse({
        'status': 'success',
        'data': {
            'logs': logs[::-1],  # 倒序，最新的在前面
            'count': len(logs)
        }
    })

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "数据合规管理系统任务状态服务器",
        "version": "1.0.0",
        "endpoints": {
            "websocket": "/ws/task-status",
            "task_status": "/api/task-status",
            "progress_summary": "/api/progress-summary",
            "task_logs": "/api/task-logs"
        }
    }

async def status_monitor():
    """状态监控任务"""
    last_modified = 0
    
    while True:
        try:
            if STATUS_FILE.exists():
                current_modified = STATUS_FILE.stat().st_mtime
                
                if current_modified > last_modified:
                    last_modified = current_modified
                    
                    # 读取最新状态
                    status_data = load_task_status()
                    summary = get_progress_summary(status_data)
                    milestones = get_milestone_progress(status_data)
                    
                    # 广播状态更新
                    await manager.broadcast({
                        'type': 'status_updated',
                        'data': {
                            'tasks': status_data,
                            'summary': summary,
                            'milestones': milestones,
                            'updated_at': datetime.now().isoformat()
                        }
                    })
            
            await asyncio.sleep(2)  # 每2秒检查一次
            
        except Exception as e:
            print(f"状态监控错误: {e}")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    """启动时执行"""
    # 启动状态监控任务
    asyncio.create_task(status_monitor())
    print("🚀 任务状态服务器启动成功")
    print(f"📁 状态文件: {STATUS_FILE}")
    print(f"📝 日志文件: {LOG_FILE}")

if __name__ == "__main__":
    print("🌐 启动任务状态WebSocket服务器")
    print("=" * 50)
    print("📍 服务地址:")
    print("   HTTP API: http://localhost:8899")
    print("   WebSocket: ws://localhost:8899/ws/task-status")
    print("=" * 50)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8899,
        log_level="info"
    )

