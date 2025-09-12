#!/usr/bin/env python3
"""
Figma助手交互式CLI工具
提供友好的命令行界面来使用Figma助手
"""

import os
import sys
import json
import yaml
import click
import logging
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax

from figma_assistant import FigmaAssistant, DevelopmentTask

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Rich控制台
console = Console()

class FigmaCLI:
    """Figma助手CLI类"""
    
    def __init__(self):
        self.assistant = None
        self.config_path = "apps/figma-assistant.yml"
        
    def setup_assistant(self):
        """设置助手实例"""
        try:
            self.assistant = FigmaAssistant(self.config_path)
            console.print("✅ Figma助手初始化成功", style="green")
        except Exception as e:
            console.print(f"❌ 初始化失败: {e}", style="red")
            return False
        return True
    
    def check_environment(self):
        """检查环境配置"""
        console.print("\n🔍 检查环境配置...", style="blue")
        
        # 检查环境变量
        env_vars = {
            "FIGMA_ACCESS_TOKEN": os.getenv("FIGMA_ACCESS_TOKEN"),
            "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN"),
            "GITHUB_OWNER": os.getenv("GITHUB_OWNER"),
            "GITHUB_REPOSITORY": os.getenv("GITHUB_REPOSITORY")
        }
        
        table = Table(title="环境变量检查")
        table.add_column("变量名", style="cyan")
        table.add_column("状态", style="green")
        table.add_column("值", style="yellow")
        
        for var_name, var_value in env_vars.items():
            status = "✅ 已设置" if var_value else "❌ 未设置"
            value = var_value[:20] + "..." if var_value and len(var_value) > 20 else var_value or "无"
            table.add_row(var_name, status, value)
        
        console.print(table)
        
        # 检查API连接
        if self.assistant:
            self._test_api_connections()
    
    def _test_api_connections(self):
        """测试API连接"""
        console.print("\n🔗 测试API连接...", style="blue")
        
        # 测试Figma API
        if self.assistant.figma_api:
            console.print("✅ Figma API已配置", style="green")
        else:
            console.print("❌ Figma API未配置", style="red")
        
        # 测试GitHub API
        if self.assistant.github_api:
            console.print("✅ GitHub API已配置", style="green")
        else:
            console.print("❌ GitHub API未配置", style="red")
    
    def interactive_analysis(self):
        """交互式分析流程"""
        console.print("\n🎨 Figma设计文件分析", style="blue")
        
        # 获取文件key
        file_key = Prompt.ask("请输入Figma文件key")
        if not file_key:
            console.print("❌ 文件key不能为空", style="red")
            return
        
        # 选择分析选项
        create_issues = Confirm.ask("是否创建GitHub Issues?")
        create_board = Confirm.ask("是否创建项目看板?")
        
        # 执行分析
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("分析Figma文件...", total=None)
            
            try:
                result = self.assistant.process_figma_file(file_key)
                progress.update(task, description="分析完成！")
                
                # 显示结果
                self._display_analysis_result(result)
                
                # 创建GitHub Issues
                if create_issues and result.get("tasks"):
                    self._create_github_issues(result["tasks"])
                
                # 创建项目看板
                if create_board and result.get("tasks"):
                    self._create_project_board(result["tasks"])
                
            except Exception as e:
                progress.update(task, description="分析失败")
                console.print(f"❌ 分析失败: {e}", style="red")
    
    def _display_analysis_result(self, result: dict):
        """显示分析结果"""
        console.print("\n📊 分析结果", style="blue")
        
        # 文件信息
        file_info = result.get("file_info", {})
        file_panel = Panel(
            f"文件名: {file_info.get('name', 'Unknown')}\n"
            f"版本: {file_info.get('version', 'Unknown')}\n"
            f"最后修改: {file_info.get('lastModified', 'Unknown')}",
            title="📁 文件信息",
            border_style="green"
        )
        console.print(file_panel)
        
        # 页面信息
        pages = result.get("pages", [])
        if pages:
            page_table = Table(title="📄 页面分析")
            page_table.add_column("页面名称", style="cyan")
            page_table.add_column("组件数量", style="green")
            page_table.add_column("布局类型", style="yellow")
            
            for page in pages:
                page_table.add_row(
                    page.get("name", "Unknown"),
                    str(len(page.get("components", []))),
                    page.get("layout", {}).get("type", "unknown")
                )
            
            console.print(page_table)
        
        # 任务信息
        tasks = result.get("tasks", [])
        if tasks:
            task_table = Table(title="📋 开发任务")
            task_table.add_column("任务", style="cyan")
            task_table.add_column("优先级", style="green")
            task_table.add_column("预估工时", style="yellow")
            task_table.add_column("依赖", style="red")
            
            for task in tasks:
                dependencies = ", ".join(task.get("dependencies", [])) or "无"
                task_table.add_row(
                    task.get("title", "Unknown"),
                    task.get("priority", "Unknown"),
                    f"{task.get('estimated_hours', 0)}h",
                    dependencies
                )
            
            console.print(task_table)
        
        # 保存结果
        if Confirm.ask("是否保存分析结果到文件?"):
            filename = Prompt.ask("请输入文件名", default="figma_analysis.json")
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                console.print(f"✅ 结果已保存到: {filename}", style="green")
            except Exception as e:
                console.print(f"❌ 保存失败: {e}", style="red")
    
    def _create_github_issues(self, tasks: List[dict]):
        """创建GitHub Issues"""
        if not self.assistant.github_api:
            console.print("❌ GitHub API未配置", style="red")
            return
        
        console.print("\n🚀 创建GitHub Issues", style="blue")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task_progress = progress.add_task("创建Issues...", total=len(tasks))
            
            created_issues = []
            for i, task_dict in enumerate(tasks):
                progress.update(task_progress, description=f"创建Issue {i+1}/{len(tasks)}")
                
                try:
                    task = DevelopmentTask(**task_dict)
                    issue = self.assistant.create_github_issues([task])[0]
                    created_issues.append(issue)
                except Exception as e:
                    console.print(f"❌ 创建Issue失败: {e}", style="red")
                
                progress.advance(task_progress)
            
            progress.update(task_progress, description="Issues创建完成！")
        
        console.print(f"✅ 成功创建 {len(created_issues)} 个Issues", style="green")
    
    def _create_project_board(self, tasks: List[dict]):
        """创建项目看板"""
        if not self.assistant.github_api:
            console.print("❌ GitHub API未配置", style="red")
            return
        
        console.print("\n📋 创建项目看板", style="blue")
        
        project_name = Prompt.ask("请输入项目名称", default="UI开发项目")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task_progress = progress.add_task("创建项目看板...", total=None)
            
            try:
                task_objects = [DevelopmentTask(**task_dict) for task_dict in tasks]
                board = self.assistant.create_project_board(project_name, task_objects)
                progress.update(task_progress, description="项目看板创建完成！")
                
                console.print(f"✅ 项目看板已创建: {board['html_url']}", style="green")
                
            except Exception as e:
                progress.update(task_progress, description="创建失败")
                console.print(f"❌ 创建项目看板失败: {e}", style="red")
    
    def batch_processing(self):
        """批量处理多个文件"""
        console.print("\n🔄 批量处理", style="blue")
        
        # 获取文件key列表
        file_keys_input = Prompt.ask("请输入Figma文件key（用逗号分隔）")
        if not file_keys_input:
            console.print("❌ 文件key不能为空", style="red")
            return
        
        file_keys = [key.strip() for key in file_keys_input.split(",")]
        
        # 选择选项
        create_issues = Confirm.ask("是否创建GitHub Issues?")
        create_board = Confirm.ask("是否创建项目看板?")
        
        # 批量处理
        all_results = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task_progress = progress.add_task("批量处理文件...", total=len(file_keys))
            
            for file_key in file_keys:
                progress.update(task_progress, description=f"处理文件: {file_key}")
                
                try:
                    result = self.assistant.process_figma_file(file_key)
                    all_results.append(result)
                except Exception as e:
                    console.print(f"❌ 处理文件 {file_key} 失败: {e}", style="red")
                
                progress.advance(task_progress)
            
            progress.update(task_progress, description="批量处理完成！")
        
        console.print(f"✅ 成功处理 {len(all_results)} 个文件", style="green")
        
        # 保存汇总结果
        if Confirm.ask("是否保存汇总结果?"):
            filename = Prompt.ask("请输入文件名", default="batch_analysis.json")
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(all_results, f, ensure_ascii=False, indent=2)
                console.print(f"✅ 汇总结果已保存到: {filename}", style="green")
            except Exception as e:
                console.print(f"❌ 保存失败: {e}", style="red")
    
    def webhook_setup(self):
        """Webhook设置指导"""
        console.print("\n🔗 Webhook设置", style="blue")
        
        webhook_info = """
        Figma Webhook配置步骤：
        
        1. 在Figma中进入文件设置
        2. 选择 "Integrations" > "Webhooks"
        3. 添加新的webhook：
           - URL: https://your-domain.com/webhook/figma
           - Events: 选择 "File update"
           - Secret: 设置webhook密钥
        
        4. 设置环境变量 FIGMA_WEBHOOK_SECRET
        
        5. 启动webhook服务：
           python scripts/figma_webhook.py
        """
        
        webhook_panel = Panel(webhook_info, title="📋 Webhook配置", border_style="blue")
        console.print(webhook_panel)
    
    def configuration_help(self):
        """配置帮助"""
        console.print("\n⚙️ 配置帮助", style="blue")
        
        config_info = """
        环境变量配置：
        
        FIGMA_ACCESS_TOKEN=your_figma_access_token
        GITHUB_TOKEN=your_github_token
        GITHUB_OWNER=your_github_username
        GITHUB_REPOSITORY=your_repository_name
        
        配置文件：apps/figma-assistant.yml
        
        获取API密钥：
        - Figma: Settings > Account > Personal access tokens
        - GitHub: Settings > Developer settings > Personal access tokens
        """
        
        config_panel = Panel(config_info, title="🔑 API配置", border_style="yellow")
        console.print(config_panel)

@click.command()
@click.option('--config', '-c', default='apps/figma-assistant.yml', help='配置文件路径')
@click.option('--file-key', '-f', help='Figma文件key')
@click.option('--create-issues', is_flag=True, help='创建GitHub Issues')
@click.option('--create-board', is_flag=True, help='创建项目看板')
@click.option('--output', '-o', help='输出文件路径')
@click.option('--interactive', '-i', is_flag=True, help='交互式模式')
def main(config, file_key, create_issues, create_board, output, interactive):
    """Figma UI开发助手CLI工具"""
    
    cli = FigmaCLI()
    cli.config_path = config
    
    # 显示欢迎信息
    welcome_text = """
    🎨 Figma UI开发助手
    
    通过Figma API获取设计文件，拆解UI页面，
    生成开发需求backlog并创建GitHub Issue
    """
    
    welcome_panel = Panel(welcome_text, title="欢迎使用", border_style="green")
    console.print(welcome_panel)
    
    # 初始化助手
    if not cli.setup_assistant():
        sys.exit(1)
    
    # 检查环境
    cli.check_environment()
    
    if interactive:
        # 交互式模式
        while True:
            console.print("\n" + "="*50)
            console.print("请选择操作:", style="bold blue")
            console.print("1. 🎨 分析Figma文件")
            console.print("2. 🔄 批量处理")
            console.print("3. 🔗 Webhook设置")
            console.print("4. ⚙️ 配置帮助")
            console.print("5. 🚪 退出")
            
            choice = Prompt.ask("请输入选项", choices=["1", "2", "3", "4", "5"])
            
            if choice == "1":
                cli.interactive_analysis()
            elif choice == "2":
                cli.batch_processing()
            elif choice == "3":
                cli.webhook_setup()
            elif choice == "4":
                cli.configuration_help()
            elif choice == "5":
                console.print("👋 再见！", style="green")
                break
    
    elif file_key:
        # 命令行模式
        try:
            result = cli.assistant.process_figma_file(file_key)
            
            if output:
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                console.print(f"✅ 结果已保存到: {output}", style="green")
            else:
                console.print(json.dumps(result, ensure_ascii=False, indent=2))
            
            if create_issues and result.get("tasks"):
                tasks = [DevelopmentTask(**task_dict) for task_dict in result["tasks"]]
                issues = cli.assistant.create_github_issues(tasks)
                console.print(f"✅ 成功创建 {len(issues)} 个GitHub Issues", style="green")
            
            if create_board and result.get("tasks"):
                project_name = f"UI开发项目-{len(result['tasks'])}个任务"
                tasks = [DevelopmentTask(**task_dict) for task_dict in result["tasks"]]
                board = cli.assistant.create_project_board(project_name, tasks)
                console.print(f"✅ 项目看板已创建: {board['html_url']}", style="green")
                
        except Exception as e:
            console.print(f"❌ 处理失败: {e}", style="red")
            sys.exit(1)
    
    else:
        # 默认显示帮助
        console.print("使用 --interactive 进入交互式模式", style="yellow")
        console.print("或使用 --file-key 指定Figma文件", style="yellow")

if __name__ == "__main__":
    main()








