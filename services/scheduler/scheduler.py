#!/usr/bin/env python3
"""
定时任务调度服务
负责知识库更新、数据清理、备份等定时任务
"""

import os
import logging
import requests
from datetime import datetime
from typing import Dict, Any

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
import yaml

# 配置日志
logger.add(
    "/app/logs/scheduler.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO"
)

# 环境变量
API_URL = os.getenv('API_URL', 'http://api:5001')
API_KEY = os.getenv('DIFY_API_KEY', '')

# 定时任务配置
KNOWLEDGE_BASE_UPDATE_CRON = os.getenv('KNOWLEDGE_BASE_UPDATE_CRON', '0 2 * * *')
CLEANUP_CRON = os.getenv('CLEANUP_CRON', '0 3 * * 0')
BACKUP_CRON = os.getenv('BACKUP_CRON', '0 4 * * *')

class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        self.scheduler = BlockingScheduler()
        self.api_headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
        self._setup_jobs()
    
    def _setup_jobs(self):
        """设置定时任务"""
        # 知识库更新任务
        if KNOWLEDGE_BASE_UPDATE_CRON:
            self.scheduler.add_job(
                func=self.update_knowledge_base,
                trigger=CronTrigger.from_crontab(KNOWLEDGE_BASE_UPDATE_CRON),
                id='knowledge_base_update',
                name='Knowledge Base Update',
                replace_existing=True
            )
            logger.info(f"Scheduled knowledge base update: {KNOWLEDGE_BASE_UPDATE_CRON}")
        
        # 清理任务
        if CLEANUP_CRON:
            self.scheduler.add_job(
                func=self.cleanup_old_data,
                trigger=CronTrigger.from_crontab(CLEANUP_CRON),
                id='cleanup_old_data',
                name='Data Cleanup',
                replace_existing=True
            )
            logger.info(f"Scheduled cleanup: {CLEANUP_CRON}")
        
        # 备份任务
        if BACKUP_CRON:
            self.scheduler.add_job(
                func=self.backup_data,
                trigger=CronTrigger.from_crontab(BACKUP_CRON),
                id='backup_data',
                name='Data Backup',
                replace_existing=True
            )
            logger.info(f"Scheduled backup: {BACKUP_CRON}")
        
        # 健康检查任务（每5分钟）
        self.scheduler.add_job(
            func=self.health_check,
            trigger='interval',
            minutes=5,
            id='health_check',
            name='Health Check',
            replace_existing=True
        )
    
    def update_knowledge_base(self):
        """更新知识库任务"""
        try:
            logger.info("Starting knowledge base update...")
            
            # 检查是否有待处理的文档
            response = requests.get(
                f"{API_URL}/v1/knowledge-base/pending-documents",
                headers=self.api_headers,
                timeout=30
            )
            
            if response.status_code == 200:
                pending_docs = response.json().get('documents', [])
                
                if pending_docs:
                    logger.info(f"Found {len(pending_docs)} pending documents")
                    
                    # 处理每个待处理文档
                    for doc in pending_docs:
                        self._process_document(doc)
                else:
                    logger.info("No pending documents to process")
            else:
                logger.error(f"Failed to fetch pending documents: {response.status_code}")
            
            # 触发知识库索引重建
            self._rebuild_index()
            
            logger.info("Knowledge base update completed")
            
        except Exception as e:
            logger.error(f"Knowledge base update failed: {e}")
    
    def _process_document(self, doc: Dict[str, Any]):
        """处理单个文档"""
        try:
            doc_id = doc.get('id')
            doc_path = doc.get('path')
            
            logger.info(f"Processing document: {doc_id}")
            
            # 调用文档处理API
            response = requests.post(
                f"{API_URL}/v1/knowledge-base/process-document",
                json={'document_id': doc_id, 'path': doc_path},
                headers=self.api_headers,
                timeout=60
            )
            
            if response.status_code == 200:
                logger.info(f"Document {doc_id} processed successfully")
            else:
                logger.error(f"Failed to process document {doc_id}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error processing document {doc.get('id')}: {e}")
    
    def _rebuild_index(self):
        """重建知识库索引"""
        try:
            logger.info("Rebuilding knowledge base index...")
            
            response = requests.post(
                f"{API_URL}/v1/knowledge-base/rebuild-index",
                headers=self.api_headers,
                timeout=120
            )
            
            if response.status_code == 200:
                logger.info("Index rebuilt successfully")
            else:
                logger.error(f"Failed to rebuild index: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error rebuilding index: {e}")
    
    def cleanup_old_data(self):
        """清理旧数据任务"""
        try:
            logger.info("Starting data cleanup...")
            
            # 清理临时文件
            self._cleanup_temp_files()
            
            # 清理过期的对话记录
            self._cleanup_old_conversations()
            
            # 清理旧的日志文件
            self._cleanup_old_logs()
            
            logger.info("Data cleanup completed")
            
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
    
    def _cleanup_temp_files(self):
        """清理临时文件"""
        try:
            temp_dirs = ['/app/temp', '/app/uploads/temp']
            
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    # 删除超过24小时的文件
                    import time
                    current_time = time.time()
                    
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            file_age = current_time - os.path.getmtime(file_path)
                            
                            if file_age > 86400:  # 24 hours
                                os.remove(file_path)
                                logger.debug(f"Deleted temp file: {file_path}")
            
            logger.info("Temp files cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning temp files: {e}")
    
    def _cleanup_old_conversations(self):
        """清理过期的对话记录"""
        try:
            # 清理超过30天的对话记录
            response = requests.delete(
                f"{API_URL}/v1/conversations/cleanup",
                params={'days': 30},
                headers=self.api_headers,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Cleaned up {result.get('deleted_count', 0)} old conversations")
            else:
                logger.error(f"Failed to cleanup conversations: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error cleaning conversations: {e}")
    
    def _cleanup_old_logs(self):
        """清理旧日志文件"""
        try:
            log_dir = '/app/logs'
            if os.path.exists(log_dir):
                import time
                current_time = time.time()
                
                for file in os.listdir(log_dir):
                    if file.endswith('.log'):
                        file_path = os.path.join(log_dir, file)
                        file_age = current_time - os.path.getmtime(file_path)
                        
                        # 删除超过30天的日志
                        if file_age > 2592000:  # 30 days
                            os.remove(file_path)
                            logger.info(f"Deleted old log file: {file_path}")
            
        except Exception as e:
            logger.error(f"Error cleaning logs: {e}")
    
    def backup_data(self):
        """备份数据任务"""
        try:
            logger.info("Starting data backup...")
            
            backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 备份数据库
            self._backup_database(backup_timestamp)
            
            # 备份知识库
            self._backup_knowledge_base(backup_timestamp)
            
            # 备份配置文件
            self._backup_configs(backup_timestamp)
            
            logger.info(f"Data backup completed: {backup_timestamp}")
            
        except Exception as e:
            logger.error(f"Data backup failed: {e}")
    
    def _backup_database(self, timestamp: str):
        """备份数据库"""
        try:
            # 触发数据库备份
            response = requests.post(
                f"{API_URL}/v1/admin/backup/database",
                json={'timestamp': timestamp},
                headers=self.api_headers,
                timeout=300
            )
            
            if response.status_code == 200:
                logger.info(f"Database backup completed: {timestamp}")
            else:
                logger.error(f"Database backup failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
    
    def _backup_knowledge_base(self, timestamp: str):
        """备份知识库"""
        try:
            # 触发知识库备份
            response = requests.post(
                f"{API_URL}/v1/admin/backup/knowledge-base",
                json={'timestamp': timestamp},
                headers=self.api_headers,
                timeout=300
            )
            
            if response.status_code == 200:
                logger.info(f"Knowledge base backup completed: {timestamp}")
            else:
                logger.error(f"Knowledge base backup failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error backing up knowledge base: {e}")
    
    def _backup_configs(self, timestamp: str):
        """备份配置文件"""
        try:
            import shutil
            import tarfile
            
            backup_dir = f"/app/backups/{timestamp}"
            os.makedirs(backup_dir, exist_ok=True)
            
            # 备份配置目录
            config_dirs = ['/app/config', '/app/data/config']
            
            for config_dir in config_dirs:
                if os.path.exists(config_dir):
                    dir_name = os.path.basename(config_dir)
                    backup_path = os.path.join(backup_dir, dir_name)
                    shutil.copytree(config_dir, backup_path)
            
            # 创建tar.gz压缩包
            tar_path = f"/app/backups/config_backup_{timestamp}.tar.gz"
            with tarfile.open(tar_path, "w:gz") as tar:
                tar.add(backup_dir, arcname=os.path.basename(backup_dir))
            
            # 清理临时目录
            shutil.rmtree(backup_dir)
            
            logger.info(f"Config backup completed: {tar_path}")
            
        except Exception as e:
            logger.error(f"Error backing up configs: {e}")
    
    def health_check(self):
        """健康检查"""
        try:
            # 检查API服务
            response = requests.get(
                f"{API_URL}/health",
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug("API service is healthy")
            else:
                logger.warning(f"API service health check failed: {response.status_code}")
            
            # 检查数据库连接
            response = requests.get(
                f"{API_URL}/v1/admin/health/database",
                headers=self.api_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug("Database connection is healthy")
            else:
                logger.warning(f"Database health check failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    def start(self):
        """启动调度器"""
        try:
            logger.info("Starting task scheduler...")
            logger.info(f"Scheduled jobs: {[job.name for job in self.scheduler.get_jobs()]}")
            
            self.scheduler.start()
            
        except KeyboardInterrupt:
            logger.info("Scheduler interrupted by user")
            self.scheduler.shutdown()
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            self.scheduler.shutdown()

def main():
    """主函数"""
    # 创建必要的目录
    os.makedirs('/app/logs', exist_ok=True)
    os.makedirs('/app/backups', exist_ok=True)
    
    # 创建并启动调度器
    scheduler = TaskScheduler()
    scheduler.start()

if __name__ == '__main__':
    main()