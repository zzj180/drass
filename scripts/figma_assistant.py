#!/usr/bin/env python3
"""
Figma UI开发助手
通过Figma API获取设计文件，拆解UI页面，生成开发需求backlog并创建GitHub Issue
"""

import os
import json
import yaml
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import logging
from datetime import datetime
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class FigmaPage:
    """Figma页面信息"""
    id: str
    name: str
    components: List[Dict]
    layout: Dict
    styles: Dict

@dataclass
class DevelopmentTask:
    """开发任务信息"""
    title: str
    description: str
    priority: str
    estimated_hours: float
    dependencies: List[str]
    components: List[str]

class FigmaAPI:
    """Figma API客户端"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.figma.com/v1"
        self.headers = {
            "X-Figma-Token": access_token
        }
    
    def get_file(self, file_key: str) -> Dict:
        """获取Figma文件信息"""
        url = f"{self.base_url}/files/{file_key}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_file_nodes(self, file_key: str, node_ids: List[str]) -> Dict:
        """获取特定节点的信息"""
        node_ids_str = ",".join(node_ids)
        url = f"{self.base_url}/files/{file_key}/nodes?ids={node_ids_str}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_image_urls(self, file_key: str, node_ids: List[str], format: str = "png", scale: float = 2.0) -> Dict:
        """获取图片URL"""
        node_ids_str = ",".join(node_ids)
        url = f"{self.base_url}/images/{file_key}?ids={node_ids_str}&format={format}&scale={scale}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

class GitHubAPI:
    """GitHub API客户端"""
    
    def __init__(self, token: str, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def create_issue(self, title: str, body: str, labels: List[str] = None, assignees: List[str] = None) -> Dict:
        """创建GitHub Issue"""
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues"
        data = {
            "title": title,
            "body": body
        }
        if labels:
            data["labels"] = labels
        if assignees:
            data["assignees"] = assignees
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def create_project_board(self, name: str, description: str = "") -> Dict:
        """创建项目看板"""
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/projects"
        data = {
            "name": name,
            "body": description
        }
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

class UIAnalyzer:
    """UI结构分析器"""
    
    def __init__(self):
        self.component_patterns = {
            "button": ["button", "btn", "cta"],
            "input": ["input", "textfield", "form"],
            "card": ["card", "panel", "container"],
            "navigation": ["nav", "menu", "sidebar"],
            "modal": ["modal", "dialog", "popup"]
        }
    
    def analyze_page_structure(self, page_data: Dict) -> FigmaPage:
        """分析页面结构"""
        page_id = page_data.get("id", "")
        page_name = page_data.get("name", "")
        
        # 分析组件
        components = self._extract_components(page_data)
        
        # 分析布局
        layout = self._analyze_layout(page_data)
        
        # 分析样式
        styles = self._analyze_styles(page_data)
        
        return FigmaPage(
            id=page_id,
            name=page_name,
            components=components,
            layout=layout,
            styles=styles
        )
    
    def _extract_components(self, node_data: Dict) -> List[Dict]:
        """提取组件信息"""
        components = []
        
        def traverse_nodes(node):
            if node.get("type") == "COMPONENT" or node.get("type") == "INSTANCE":
                component_info = {
                    "id": node.get("id"),
                    "name": node.get("name"),
                    "type": node.get("type"),
                    "position": {
                        "x": node.get("absoluteBoundingBox", {}).get("x", 0),
                        "y": node.get("absoluteBoundingBox", {}).get("y", 0)
                    },
                    "size": {
                        "width": node.get("absoluteBoundingBox", {}).get("width", 0),
                        "height": node.get("absoluteBoundingBox", {}).get("height", 0)
                    }
                }
                components.append(component_info)
            
            # 递归遍历子节点
            if "children" in node:
                for child in node["children"]:
                    traverse_nodes(child)
        
        traverse_nodes(node_data)
        return components
    
    def _analyze_layout(self, node_data: Dict) -> Dict:
        """分析布局信息"""
        layout_info = {
            "type": "unknown",
            "direction": "vertical",
            "spacing": 0,
            "alignment": "start"
        }
        
        # 分析布局类型
        if "layoutMode" in node_data:
            layout_info["type"] = node_data["layoutMode"]
            layout_info["direction"] = "horizontal" if node_data["layoutMode"] == "HORIZONTAL" else "vertical"
        
        # 分析间距
        if "itemSpacing" in node_data:
            layout_info["spacing"] = node_data["itemSpacing"]
        
        return layout_info
    
    def _analyze_styles(self, node_data: Dict) -> Dict:
        """分析样式信息"""
        styles = {}
        
        # 提取颜色信息
        if "fills" in node_data and node_data["fills"]:
            fills = node_data["fills"]
            if isinstance(fills, list) and len(fills) > 0:
                fill = fills[0]
                if fill.get("type") == "SOLID":
                    styles["background_color"] = fill.get("color", {})
        
        # 提取字体信息
        if "style" in node_data and node_data["style"]:
            style = node_data["style"]
            styles["font_family"] = style.get("fontFamily")
            styles["font_size"] = style.get("fontSize")
            styles["font_weight"] = style.get("fontWeight")
        
        return styles

class DevelopmentTaskGenerator:
    """开发任务生成器"""
    
    def __init__(self):
        self.task_templates = {
            "component": {
                "title": "实现{component_name}组件",
                "description": "根据设计稿实现{component_name}组件，包括样式、交互和响应式设计",
                "priority": "medium",
                "estimated_hours": 4.0
            },
            "page": {
                "title": "开发{page_name}页面",
                "description": "实现{page_name}页面的完整功能，包括布局、组件集成和页面逻辑",
                "priority": "high",
                "estimated_hours": 16.0
            },
            "integration": {
                "title": "集成{component_name}到{page_name}",
                "description": "将{component_name}组件集成到{page_name}页面中，确保样式和交互一致",
                "priority": "medium",
                "estimated_hours": 2.0
            }
        }
    
    def generate_tasks_from_pages(self, pages: List[FigmaPage]) -> List[DevelopmentTask]:
        """从页面生成开发任务"""
        tasks = []
        
        for page in pages:
            # 生成页面级任务
            page_task = self._create_page_task(page)
            tasks.append(page_task)
            
            # 生成组件级任务
            component_tasks = self._create_component_tasks(page)
            tasks.extend(component_tasks)
            
            # 生成集成任务
            integration_tasks = self._create_integration_tasks(page)
            tasks.extend(integration_tasks)
        
        return tasks
    
    def _create_page_task(self, page: FigmaPage) -> DevelopmentTask:
        """创建页面级任务"""
        template = self.task_templates["page"]
        return DevelopmentTask(
            title=template["title"].format(page_name=page.name),
            description=template["description"].format(page_name=page.name),
            priority=template["priority"],
            estimated_hours=template["estimated_hours"],
            dependencies=[],
            components=[comp["name"] for comp in page.components]
        )
    
    def _create_component_tasks(self, page: FigmaPage) -> List[DevelopmentTask]:
        """创建组件级任务"""
        tasks = []
        template = self.task_templates["component"]
        
        for component in page.components:
            task = DevelopmentTask(
                title=template["title"].format(component_name=component["name"]),
                description=template["description"].format(component_name=component["name"]),
                priority=template["priority"],
                estimated_hours=template["estimated_hours"],
                dependencies=[],
                components=[component["name"]]
            )
            tasks.append(task)
        
        return tasks
    
    def _create_integration_tasks(self, page: FigmaPage) -> List[DevelopmentTask]:
        """创建集成任务"""
        tasks = []
        template = self.task_templates["integration"]
        
        for component in page.components:
            task = DevelopmentTask(
                title=template["title"].format(
                    component_name=component["name"],
                    page_name=page.name
                ),
                description=template["description"].format(
                    component_name=component["name"],
                    page_name=page.name
                ),
                priority=template["priority"],
                estimated_hours=template["estimated_hours"],
                dependencies=[f"实现{component['name']}组件", f"开发{page.name}页面"],
                components=[component["name"]]
            )
            tasks.append(task)
        
        return tasks

class FigmaAssistant:
    """Figma助手主类"""
    
    def __init__(self, config_path: str = "apps/figma-assistant.yml"):
        self.config = self._load_config(config_path)
        self.figma_api = None
        self.github_api = None
        self.ui_analyzer = UIAnalyzer()
        self.task_generator = DevelopmentTaskGenerator()
        
        self._setup_apis()
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"配置文件未找到: {config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"配置文件解析错误: {e}")
            raise
    
    def _setup_apis(self):
        """设置API客户端"""
        # 设置Figma API
        figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
        if figma_token:
            self.figma_api = FigmaAPI(figma_token)
        else:
            logger.warning("FIGMA_ACCESS_TOKEN未设置")
        
        # 设置GitHub API
        github_token = os.getenv("GITHUB_TOKEN")
        github_owner = os.getenv("GITHUB_OWNER")
        github_repo = os.getenv("GITHUB_REPOSITORY")
        
        if all([github_token, github_owner, github_repo]):
            self.github_api = GitHubAPI(github_token, github_owner, github_repo)
        else:
            logger.warning("GitHub相关环境变量未完全设置")
    
    def process_figma_file(self, file_key: str) -> Dict:
        """处理Figma文件"""
        if not self.figma_api:
            raise ValueError("Figma API未配置")
        
        logger.info(f"开始处理Figma文件: {file_key}")
        
        # 获取文件信息
        file_data = self.figma_api.get_file(file_key)
        logger.info(f"成功获取文件: {file_data.get('name', 'Unknown')}")
        
        # 分析页面
        pages = []
        for page in file_data.get("document", {}).get("children", []):
            if page.get("type") == "CANVAS":
                analyzed_page = self.ui_analyzer.analyze_page_structure(page)
                pages.append(analyzed_page)
                logger.info(f"分析页面: {analyzed_page.name}")
        
        # 生成开发任务
        tasks = self.task_generator.generate_tasks_from_pages(pages)
        logger.info(f"生成了 {len(tasks)} 个开发任务")
        
        # 生成分析报告
        report = self._generate_analysis_report(file_data, pages, tasks)
        
        return {
            "file_info": file_data,
            "pages": [self._page_to_dict(page) for page in pages],
            "tasks": [self._task_to_dict(task) for task in tasks],
            "report": report
        }
    
    def _generate_analysis_report(self, file_data: Dict, pages: List[FigmaPage], tasks: List[DevelopmentTask]) -> str:
        """生成分析报告"""
        report = f"""# Figma设计文件分析报告

## 文件信息
- **文件名**: {file_data.get('name', 'Unknown')}
- **最后修改**: {file_data.get('lastModified', 'Unknown')}
- **版本**: {file_data.get('version', 'Unknown')}

## 页面分析
共发现 {len(pages)} 个页面：

"""
        
        for page in pages:
            report += f"""### {page.name}
- **页面ID**: {page.id}
- **组件数量**: {len(page.components)}
- **布局类型**: {page.layout.get('type', 'unknown')}
- **主要组件**: {', '.join([comp['name'] for comp in page.components[:5]])}

"""
        
        report += f"""## 开发任务概览
共生成 {len(tasks)} 个开发任务：

"""
        
        for i, task in enumerate(tasks, 1):
            report += f"""### {i}. {task.title}
- **优先级**: {task.priority}
- **预估工时**: {task.estimated_hours} 小时
- **依赖**: {', '.join(task.dependencies) if task.dependencies else '无'}

"""
        
        return report
    
    def _page_to_dict(self, page: FigmaPage) -> Dict:
        """将页面对象转换为字典"""
        return {
            "id": page.id,
            "name": page.name,
            "components": page.components,
            "layout": page.layout,
            "styles": page.styles
        }
    
    def _task_to_dict(self, task: DevelopmentTask) -> Dict:
        """将任务对象转换为字典"""
        return {
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "estimated_hours": task.estimated_hours,
            "dependencies": task.dependencies,
            "components": task.components
        }
    
    def create_github_issues(self, tasks: List[DevelopmentTask], labels: List[str] = None) -> List[Dict]:
        """创建GitHub Issues"""
        if not self.github_api:
            raise ValueError("GitHub API未配置")
        
        if not labels:
            labels = ["ui-development", "figma-design"]
        
        created_issues = []
        
        for task in tasks:
            try:
                issue_body = self._format_issue_body(task)
                issue = self.github_api.create_issue(
                    title=task.title,
                    body=issue_body,
                    labels=labels
                )
                created_issues.append(issue)
                logger.info(f"成功创建Issue: {issue['html_url']}")
            except Exception as e:
                logger.error(f"创建Issue失败: {e}")
        
        return created_issues
    
    def _format_issue_body(self, task: DevelopmentTask) -> str:
        """格式化Issue内容"""
        body = f"""## 任务描述
{task.description}

## 任务详情
- **优先级**: {task.priority}
- **预估工时**: {task.estimated_hours} 小时
- **相关组件**: {', '.join(task.components)}

## 依赖关系
"""
        
        if task.dependencies:
            for dep in task.dependencies:
                body += f"- {dep}\n"
        else:
            body += "- 无依赖\n"
        
        body += f"""
## 验收标准
- [ ] 组件/页面功能完整实现
- [ ] 样式与设计稿一致
- [ ] 响应式设计适配
- [ ] 交互功能正常
- [ ] 代码质量符合规范

---
*此Issue由Figma助手自动生成*
"""
        
        return body
    
    def create_project_board(self, project_name: str, tasks: List[DevelopmentTask]) -> Dict:
        """创建项目看板"""
        if not self.github_api:
            raise ValueError("GitHub API未配置")
        
        try:
            project = self.github_api.create_project_board(
                name=project_name,
                description=f"基于Figma设计的UI开发项目，包含 {len(tasks)} 个任务"
            )
            logger.info(f"成功创建项目看板: {project['html_url']}")
            return project
        except Exception as e:
            logger.error(f"创建项目看板失败: {e}")
            raise

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Figma UI开发助手")
    parser.add_argument("--file-key", required=True, help="Figma文件key")
    parser.add_argument("--config", default="apps/figma-assistant.yml", help="配置文件路径")
    parser.add_argument("--create-issues", action="store_true", help="是否创建GitHub Issues")
    parser.add_argument("--create-board", action="store_true", help="是否创建项目看板")
    parser.add_argument("--project-name", help="项目看板名称")
    parser.add_argument("--output", help="输出文件路径")
    
    args = parser.parse_args()
    
    try:
        # 创建助手实例
        assistant = FigmaAssistant(args.config)
        
        # 处理Figma文件
        result = assistant.process_figma_file(args.file_key)
        
        # 输出结果
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info(f"结果已保存到: {args.output}")
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 创建GitHub Issues
        if args.create_issues:
            tasks = [DevelopmentTask(**task_dict) for task_dict in result["tasks"]]
            issues = assistant.create_github_issues(tasks)
            logger.info(f"成功创建 {len(issues)} 个GitHub Issues")
        
        # 创建项目看板
        if args.create_board:
            project_name = args.project_name or f"UI开发项目-{datetime.now().strftime('%Y%m%d')}"
            tasks = [DevelopmentTask(**task_dict) for task_dict in result["tasks"]]
            board = assistant.create_project_board(project_name, tasks)
            logger.info(f"项目看板已创建: {board['html_url']}")
        
    except Exception as e:
        logger.error(f"处理失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())








