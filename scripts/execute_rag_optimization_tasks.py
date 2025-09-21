#!/usr/bin/env python3
"""
RAG性能优化任务执行脚本
自动执行和跟踪优化任务的进度
"""

import asyncio
import time
import json
import requests
import subprocess
import sys
from typing import Dict, Any, List
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rag_optimization_tasks.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RAGOptimizationTaskExecutor:
    """RAG优化任务执行器"""
    
    def __init__(self):
        self.base_url = "http://localhost:8888"
        self.tasks_status = {}
        self.start_time = None
        self.results = {}
        
    def log_task_start(self, task_name: str):
        """记录任务开始"""
        self.tasks_status[task_name] = {
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "success": False,
            "error": None
        }
        logger.info(f"🚀 开始执行任务: {task_name}")
    
    def log_task_complete(self, task_name: str, success: bool = True, error: str = None):
        """记录任务完成"""
        if task_name in self.tasks_status:
            self.tasks_status[task_name].update({
                "status": "completed" if success else "failed",
                "end_time": datetime.now().isoformat(),
                "success": success,
                "error": error
            })
        
        if success:
            logger.info(f"✅ 任务完成: {task_name}")
        else:
            logger.error(f"❌ 任务失败: {task_name} - {error}")
    
    async def check_service_health(self, service_name: str, url: str) -> bool:
        """检查服务健康状态"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ {service_name} 服务正常")
                return True
            else:
                logger.warning(f"⚠️ {service_name} 服务异常: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ {service_name} 服务不可用: {e}")
            return False
    
    async def task_1_1_check_services(self):
        """任务1.1：检查服务状态"""
        self.log_task_start("检查服务状态")
        
        services = {
            "VLLM服务": "http://localhost:8001/health",
            "嵌入服务": "http://localhost:8010/health", 
            "ChromaDB服务": "http://localhost:8005/api/v1/heartbeat",
            "后端API服务": "http://localhost:8888/health"
        }
        
        results = {}
        for service_name, url in services.items():
            results[service_name] = await self.check_service_health(service_name, url)
        
        success = all(results.values())
        self.log_task_complete("检查服务状态", success)
        self.results["service_health"] = results
        return success
    
    async def task_1_2_performance_baseline(self):
        """任务1.2：性能基准测试"""
        self.log_task_start("性能基准测试")
        
        try:
            # 运行现有性能测试
            result = subprocess.run([
                sys.executable, "test_performance_optimization.py"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("✅ 性能基准测试完成")
                self.log_task_complete("性能基准测试", True)
                return True
            else:
                logger.error(f"❌ 性能基准测试失败: {result.stderr}")
                self.log_task_complete("性能基准测试", False, result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            error = "性能测试超时"
            logger.error(f"❌ {error}")
            self.log_task_complete("性能基准测试", False, error)
            return False
        except Exception as e:
            error = f"性能测试异常: {e}"
            logger.error(f"❌ {error}")
            self.log_task_complete("性能基准测试", False, error)
            return False
    
    async def task_1_3_backup_config(self):
        """任务1.3：备份配置"""
        self.log_task_start("备份配置")
        
        try:
            import shutil
            import os
            
            backup_dir = f"./backup_rag_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(backup_dir, exist_ok=True)
            
            files_to_backup = [
                "services/main-app/app/services/vector_store.py",
                "services/main-app/app/chains/compliance_rag_chain.py",
                "services/main-app/app/api/v1/test.py"
            ]
            
            for file_path in files_to_backup:
                if os.path.exists(file_path):
                    shutil.copy2(file_path, backup_dir)
                    logger.info(f"✅ 已备份: {file_path}")
            
            self.results["backup_dir"] = backup_dir
            self.log_task_complete("备份配置", True)
            return True
            
        except Exception as e:
            error = f"备份失败: {e}"
            logger.error(f"❌ {error}")
            self.log_task_complete("备份配置", False, error)
            return False
    
    async def task_2_1_deploy_optimized_vector_store(self):
        """任务2.1：部署优化的向量存储"""
        self.log_task_start("部署优化向量存储")
        
        try:
            # 检查优化文件是否存在
            import os
            if not os.path.exists("services/main-app/app/services/vector_store_optimized.py"):
                error = "优化向量存储文件不存在"
                self.log_task_complete("部署优化向量存储", False, error)
                return False
            
            # 这里可以添加更多的部署逻辑
            logger.info("✅ 优化向量存储文件已就位")
            self.log_task_complete("部署优化向量存储", True)
            return True
            
        except Exception as e:
            error = f"部署失败: {e}"
            logger.error(f"❌ {error}")
            self.log_task_complete("部署优化向量存储", False, error)
            return False
    
    async def task_2_2_deploy_optimized_rag_chain(self):
        """任务2.2：部署优化的RAG链"""
        self.log_task_start("部署优化RAG链")
        
        try:
            # 检查优化文件是否存在
            import os
            if not os.path.exists("services/main-app/app/chains/optimized_rag_chain.py"):
                error = "优化RAG链文件不存在"
                self.log_task_complete("部署优化RAG链", False, error)
                return False
            
            logger.info("✅ 优化RAG链文件已就位")
            self.log_task_complete("部署优化RAG链", True)
            return True
            
        except Exception as e:
            error = f"部署失败: {e}"
            logger.error(f"❌ {error}")
            self.log_task_complete("部署优化RAG链", False, error)
            return False
    
    async def task_2_3_restart_backend_service(self):
        """任务2.3：重启后端服务"""
        self.log_task_start("重启后端服务")
        
        try:
            # 停止现有服务
            subprocess.run(["pkill", "-f", "uvicorn.*main-app"], capture_output=True)
            await asyncio.sleep(3)
            
            # 启动新服务
            process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "app.main:app", 
                "--host", "0.0.0.0", 
                "--port", "8888",
                "--reload"
            ], cwd="services/main-app")
            
            # 等待服务启动
            for i in range(30):
                try:
                    response = requests.get("http://localhost:8888/health", timeout=5)
                    if response.status_code == 200:
                        logger.info("✅ 后端服务重启成功")
                        self.log_task_complete("重启后端服务", True)
                        return True
                except:
                    pass
                await asyncio.sleep(1)
            
            error = "后端服务启动超时"
            logger.error(f"❌ {error}")
            self.log_task_complete("重启后端服务", False, error)
            return False
            
        except Exception as e:
            error = f"重启服务失败: {e}"
            logger.error(f"❌ {error}")
            self.log_task_complete("重启后端服务", False, error)
            return False
    
    async def task_3_1_functional_test(self):
        """任务3.1：功能测试"""
        self.log_task_start("功能测试")
        
        try:
            # 运行功能测试
            result = subprocess.run([
                sys.executable, "test_rag_performance_optimization.py"
            ], capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                logger.info("✅ 功能测试完成")
                self.log_task_complete("功能测试", True)
                return True
            else:
                logger.error(f"❌ 功能测试失败: {result.stderr}")
                self.log_task_complete("功能测试", False, result.stderr)
                return False
                
        except Exception as e:
            error = f"功能测试异常: {e}"
            logger.error(f"❌ {error}")
            self.log_task_complete("功能测试", False, error)
            return False
    
    async def task_3_2_performance_validation(self):
        """任务3.2：性能验证"""
        self.log_task_start("性能验证")
        
        try:
            # 执行性能测试
            test_queries = [
                "什么是数据合规？",
                "GDPR的主要要求是什么？",
                "请详细分析数据合规管理系统的实施步骤"
            ]
            
            performance_results = []
            for query in test_queries:
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/api/v1/test/chat",
                    json={
                        "message": query,
                        "use_rag": True,
                        "response_type": "standard"
                    },
                    timeout=30
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    response_time = end_time - start_time
                    performance_results.append({
                        "query": query,
                        "response_time": response_time,
                        "success": True
                    })
                    logger.info(f"✅ 查询测试: {response_time:.2f}秒")
                else:
                    performance_results.append({
                        "query": query,
                        "response_time": 0,
                        "success": False,
                        "error": f"HTTP {response.status_code}"
                    })
            
            success_rate = sum(1 for r in performance_results if r["success"]) / len(performance_results)
            avg_response_time = sum(r["response_time"] for r in performance_results if r["success"]) / max(1, sum(1 for r in performance_results if r["success"]))
            
            self.results["performance_validation"] = {
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "results": performance_results
            }
            
            if success_rate >= 0.8 and avg_response_time < 10:
                logger.info(f"✅ 性能验证通过: 成功率{success_rate:.1%}, 平均响应时间{avg_response_time:.2f}秒")
                self.log_task_complete("性能验证", True)
                return True
            else:
                error = f"性能不达标: 成功率{success_rate:.1%}, 平均响应时间{avg_response_time:.2f}秒"
                logger.error(f"❌ {error}")
                self.log_task_complete("性能验证", False, error)
                return False
                
        except Exception as e:
            error = f"性能验证异常: {e}"
            logger.error(f"❌ {error}")
            self.log_task_complete("性能验证", False, error)
            return False
    
    def generate_report(self):
        """生成执行报告"""
        report = {
            "execution_summary": {
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": datetime.now().isoformat(),
                "total_tasks": len(self.tasks_status),
                "completed_tasks": sum(1 for t in self.tasks_status.values() if t["success"]),
                "failed_tasks": sum(1 for t in self.tasks_status.values() if not t["success"]),
                "success_rate": sum(1 for t in self.tasks_status.values() if t["success"]) / len(self.tasks_status) if self.tasks_status else 0
            },
            "task_details": self.tasks_status,
            "results": self.results
        }
        
        # 保存报告
        report_file = f"rag_optimization_execution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📊 执行报告已保存: {report_file}")
        return report
    
    async def execute_all_tasks(self):
        """执行所有任务"""
        self.start_time = datetime.now()
        logger.info("🎯 开始执行RAG性能优化任务")
        
        # 第一阶段：环境准备和验证
        logger.info("📋 第一阶段：环境准备和验证")
        await self.task_1_1_check_services()
        await self.task_1_2_performance_baseline()
        await self.task_1_3_backup_config()
        
        # 第二阶段：核心优化实施
        logger.info("🚀 第二阶段：核心优化实施")
        await self.task_2_1_deploy_optimized_vector_store()
        await self.task_2_2_deploy_optimized_rag_chain()
        await self.task_2_3_restart_backend_service()
        
        # 第三阶段：测试和验证
        logger.info("🧪 第三阶段：测试和验证")
        await self.task_3_1_functional_test()
        await self.task_3_2_performance_validation()
        
        # 生成报告
        report = self.generate_report()
        
        # 打印总结
        logger.info("="*60)
        logger.info("📊 RAG性能优化任务执行完成")
        logger.info("="*60)
        logger.info(f"总任务数: {report['execution_summary']['total_tasks']}")
        logger.info(f"完成任务数: {report['execution_summary']['completed_tasks']}")
        logger.info(f"失败任务数: {report['execution_summary']['failed_tasks']}")
        logger.info(f"成功率: {report['execution_summary']['success_rate']:.1%}")
        
        if report['execution_summary']['success_rate'] >= 0.8:
            logger.info("🎉 优化任务执行成功！")
        else:
            logger.warning("⚠️ 部分任务执行失败，请检查日志")
        
        return report

async def main():
    """主函数"""
    executor = RAGOptimizationTaskExecutor()
    
    try:
        report = await executor.execute_all_tasks()
        
        # 根据执行结果决定退出码
        if report['execution_summary']['success_rate'] >= 0.8:
            sys.exit(0)  # 成功
        else:
            sys.exit(1)  # 失败
            
    except Exception as e:
        logger.error(f"❌ 执行过程中出现严重错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
