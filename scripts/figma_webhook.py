#!/usr/bin/env python3
"""
Figma Webhook处理器
实时接收Figma设计文件更新，自动触发分析流程
"""

import os
import json
import hmac
import hashlib
import logging
from typing import Dict, Any
from flask import Flask, request, jsonify
from datetime import datetime
import threading
import time

# 导入Figma助手
from figma_assistant import FigmaAssistant

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class FigmaWebhookHandler:
    """Figma Webhook处理器"""
    
    def __init__(self, webhook_secret: str = None):
        self.webhook_secret = webhook_secret
        self.assistant = FigmaAssistant()
        self.processing_queue = []
        self.is_processing = False
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """验证Webhook签名"""
        if not self.webhook_secret:
            logger.warning("Webhook secret未配置，跳过签名验证")
            return True
        
        expected_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    def process_webhook(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理Webhook事件"""
        event_type = event_data.get("event_type")
        file_key = event_data.get("file_key")
        
        logger.info(f"收到Webhook事件: {event_type}, 文件: {file_key}")
        
        if event_type == "FILE_UPDATE" and file_key:
            # 添加到处理队列
            self.processing_queue.append({
                "file_key": file_key,
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "event_data": event_data
            })
            
            # 启动后台处理
            if not self.is_processing:
                self._start_background_processing()
            
            return {"status": "queued", "message": "文件已加入处理队列"}
        
        return {"status": "ignored", "message": "事件类型不支持"}
    
    def _start_background_processing(self):
        """启动后台处理"""
        self.is_processing = True
        
        def process_queue():
            while self.processing_queue:
                try:
                    item = self.processing_queue.pop(0)
                    self._process_file_update(item)
                except Exception as e:
                    logger.error(f"处理文件更新失败: {e}")
                
                time.sleep(1)  # 避免过于频繁的API调用
            
            self.is_processing = False
        
        thread = threading.Thread(target=process_queue, daemon=True)
        thread.start()
    
    def _process_file_update(self, item: Dict[str, Any]):
        """处理文件更新"""
        file_key = item["file_key"]
        
        try:
            logger.info(f"开始处理文件更新: {file_key}")
            
            # 分析Figma文件
            result = self.assistant.process_figma_file(file_key)
            
            # 自动创建GitHub Issues（如果配置了GitHub）
            if self.assistant.github_api:
                tasks = result.get("tasks", [])
                if tasks:
                    # 创建项目看板
                    project_name = f"UI更新-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                    board = self.assistant.create_project_board(project_name, tasks)
                    
                    # 创建Issues
                    issues = self.assistant.create_github_issues(tasks)
                    
                    logger.info(f"成功创建 {len(issues)} 个Issues和项目看板")
            
            # 保存分析结果
            output_file = f"figma_analysis_{file_key}_{int(time.time())}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"分析结果已保存到: {output_file}")
            
        except Exception as e:
            logger.error(f"处理文件 {file_key} 失败: {e}")

# 创建Webhook处理器实例
webhook_handler = FigmaWebhookHandler(
    webhook_secret=os.getenv("FIGMA_WEBHOOK_SECRET")
)

@app.route('/webhook/figma', methods=['POST'])
def figma_webhook():
    """Figma Webhook端点"""
    try:
        # 获取请求数据
        payload = request.get_data()
        signature = request.headers.get('X-Figma-Signature', '')
        
        # 验证签名
        if not webhook_handler.verify_signature(payload, signature):
            return jsonify({"error": "签名验证失败"}), 401
        
        # 解析事件数据
        event_data = request.get_json()
        
        if not event_data:
            return jsonify({"error": "无效的请求数据"}), 400
        
        # 处理Webhook
        result = webhook_handler.process_webhook(event_data)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"处理Webhook失败: {e}")
        return jsonify({"error": "内部服务器错误"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "queue_length": len(webhook_handler.processing_queue),
        "is_processing": webhook_handler.is_processing
    })

@app.route('/process/<file_key>', methods=['POST'])
def process_file(file_key):
    """手动触发文件处理"""
    try:
        result = webhook_handler.assistant.process_figma_file(file_key)
        return jsonify({
            "status": "success",
            "result": result
        })
    except Exception as e:
        logger.error(f"手动处理文件失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """获取处理状态"""
    return jsonify({
        "queue_length": len(webhook_handler.processing_queue),
        "is_processing": webhook_handler.is_processing,
        "last_processed": webhook_handler.processing_queue[-1] if webhook_handler.processing_queue else None
    })

def main():
    """主函数"""
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    
    logger.info(f"启动Figma Webhook服务器，端口: {port}")
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug
    )

if __name__ == "__main__":
    main()








