# 系统提示词集成实现方案

## 一、背景与目标

### 1.1 当前状态
- **Dify 配置**：在 `apps/数据合规（父子段）.yml` 中定义了详细的系统提示词
- **LangChain 实现**：在 `services/main-app/app/chains/prompts.py` 中有简单的英文提示词
- **需求**：将 Dify 中定义的中文合规专家提示词迁移到 LangChain 系统

### 1.2 核心目标
1. 保持原有提示词的完整功能
2. 支持 Markdown 格式渲染
3. 支持 5000 字以上的详细回答
4. 支持文件上传和处理
5. 基于知识库的精确回答

## 二、实现方案

### 2.1 提示词模块重构

#### 2.1.1 创建新的提示词配置文件

```python
# services/main-app/app/chains/compliance_prompts.py

from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

class ResponseSection(Enum):
    """回答章节枚举"""
    PROBLEM_ANALYSIS = "问题分析"
    COMPLIANCE_REQUIREMENTS = "合规要求"
    SOLUTION = "解决方案"
    RISK_WARNING = "风险提示"
    REFERENCES = "参考依据"
    FOLLOW_UP = "后续建议"
    MONITORING = "实施监控"

@dataclass
class CompliancePromptConfig:
    """合规提示词配置"""
    role_definition: str
    core_capabilities: list
    working_principles: list
    response_format: Dict[ResponseSection, int]  # 章节和字数要求
    markdown_template: str
    min_word_count: int = 5000
    enable_emoji: bool = True
    knowledge_base_only: bool = True

# 数据合规专家系统提示词
DATA_COMPLIANCE_EXPERT_PROMPT = """
角色定义
你是一位专业的企业数据合规专家，拥有深厚的数据治理和法律合规背景。你的主要职责是基于企业内部合规知识库，为用户提供准确、专业的数据合规方案。

核心能力
• 数据分类分级指导
• 隐私保护措施建议
• 合规风险评估
• 政策解读与应用
• 最佳实践推荐
• 法规条款解释
• 合规流程设计
• 风险识别与预警

专业领域
• 《数据安全法》
• 《个人信息保护法》
• 《网络安全法》
• GDPR欧盟通用数据保护条例
• 行业数据安全标准
• 企业内部数据治理政策

工作原则
1. 准确性优先：所有回答必须基于知识库中的权威信息
2. 合规性保障：确保建议符合相关法律法规要求
3. 实用性导向：提供可操作的具体指导方案
4. 风险意识：主动识别并提醒潜在合规风险
5. 保密原则：严格保护企业敏感信息
6. 知识库依赖：严格仅使用企业内部合规知识库的数据内容
7. 内容完整性：确保回答内容详尽全面，字数必须达到{min_word_count}字以上
8. 格式规范：所有回答必须使用美化的Markdown格式进行渲染
9. 附件处理：根据用户上传的附件内容和选择的目的进行相应处理

回答格式要求
📋 标准回答结构（确保总字数达到{min_word_count}字以上）：

# 📋 问题分析（500-800字）
深入分析用户问题的核心要点和背景
识别涉及的合规领域和相关法规
评估问题的复杂程度和影响范围
明确需要解决的关键合规要求

# 🎯 合规要求（800-1200字）
详细列出相关的法律法规要求
引用具体的企业政策条款
说明适用的行业标准和最佳实践
分析合规要求的层次和优先级

# 💡 解决方案（1500-2000字）
提供详细的操作建议和实施步骤
设计完整的合规流程和控制措施
包含技术实施方案和管理制度
提供分阶段的实施计划和时间安排

# ⚠️ 风险提示（600-800字）
识别所有潜在的合规风险点
分析风险发生的可能性和影响程度
提供风险预防和应对措施
建立风险监控和预警机制

# 📚 参考依据（400-600字）
详细引用知识库中的具体政策条款
提供文档名称、章节和版本信息
确保所有引用的准确性和完整性
建立可追溯的信息来源链条

# 🔄 后续建议（500-700字）
提供相关的跟进措施和持续改进建议
建立定期评估和更新机制
规划长期的合规管理策略
设计培训和宣贯计划

# 📈 实施监控（400-600字）
建立关键绩效指标（KPI）体系
设计合规效果评估方法
制定定期审计和检查计划
建立持续改进机制

知识库使用要求
✅ 仅使用企业内部合规知识库的数据内容
❌ 禁止引用任何外部信息源
❌ 禁止使用通用知识或经验判断
❌ 禁止参考网络资源或公开资料

当前知识库内容：
{context}

用户问题：{input}

请基于以上要求和知识库内容，提供详细的合规建议。如果知识库中没有相关信息，请明确说明并建议适当的咨询渠道。
"""
```

#### 2.1.2 更新 prompts.py

```python
# services/main-app/app/chains/prompts.py

from app.chains.compliance_prompts import (
    DATA_COMPLIANCE_EXPERT_PROMPT,
    CompliancePromptConfig,
    ResponseSection
)

# 保留原有英文提示词
COMPLIANCE_SYSTEM_PROMPT_EN = """..."""

# 使用新的中文提示词
COMPLIANCE_SYSTEM_PROMPT = DATA_COMPLIANCE_EXPERT_PROMPT

# 配置对象
COMPLIANCE_CONFIG = CompliancePromptConfig(
    role_definition="企业数据合规专家",
    core_capabilities=[
        "数据分类分级指导",
        "隐私保护措施建议",
        "合规风险评估",
        "政策解读与应用",
        "最佳实践推荐",
        "法规条款解释",
        "合规流程设计",
        "风险识别与预警"
    ],
    working_principles=[
        "准确性优先",
        "合规性保障",
        "实用性导向",
        "风险意识",
        "保密原则",
        "知识库依赖",
        "内容完整性",
        "格式规范"
    ],
    response_format={
        ResponseSection.PROBLEM_ANALYSIS: 800,
        ResponseSection.COMPLIANCE_REQUIREMENTS: 1200,
        ResponseSection.SOLUTION: 2000,
        ResponseSection.RISK_WARNING: 800,
        ResponseSection.REFERENCES: 600,
        ResponseSection.FOLLOW_UP: 700,
        ResponseSection.MONITORING: 600
    },
    min_word_count=5000,
    enable_emoji=True,
    knowledge_base_only=True
)
```

### 2.2 RAG Chain 增强

#### 2.2.1 修改 ComplianceRAGChain

```python
# services/main-app/app/chains/compliance_rag_chain.py

class ComplianceRAGChain:
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        embeddings: Optional[OpenAIEmbeddings] = None,
        vector_store: Optional[Chroma] = None,
        enable_streaming: bool = False,
        enable_reranking: bool = False,
        enable_multi_query: bool = False,
        min_response_length: int = 5000,  # 最小回答长度
        language: str = "zh"  # 语言设置
    ):
        self.min_response_length = min_response_length
        self.language = language
        # ...

    def _enhance_response(self, response: str) -> str:
        """增强回答以满足字数要求"""
        if len(response) < self.min_response_length:
            # 添加更多细节和解释
            response = self._expand_response(response)

        # 确保 Markdown 格式正确
        response = self._format_markdown(response)

        return response

    def _expand_response(self, response: str) -> str:
        """扩展回答内容"""
        # 实现逻辑：
        # 1. 分析现有内容
        # 2. 添加更多案例说明
        # 3. 详细描述实施步骤
        # 4. 补充风险分析
        # 5. 增加最佳实践
        pass

    def _format_markdown(self, response: str) -> str:
        """格式化 Markdown"""
        # 确保正确的标题层级
        # 添加表格和列表
        # 插入 emoji 图标
        # 格式化代码块
        pass
```

### 2.3 文件上传处理

#### 2.3.1 创建文件处理服务

```python
# services/main-app/app/services/file_processor_service.py

from typing import Optional, Dict, Any
from enum import Enum

class FilePurpose(Enum):
    """文件处理目的"""
    UPDATE_KNOWLEDGE_BASE = "update_knowledge_base"
    GENERATE_COMPLIANCE_REPORT = "generate_compliance_report"

class FileProcessorService:
    """文件处理服务"""

    async def process_file(
        self,
        file_path: str,
        purpose: FilePurpose,
        business_scenario: Optional[str] = None
    ) -> Dict[str, Any]:
        """处理上传的文件"""

        # 1. 解析文件内容
        content = await self._extract_content(file_path)

        # 2. 根据目的处理
        if purpose == FilePurpose.UPDATE_KNOWLEDGE_BASE:
            result = await self._prepare_for_knowledge_base(content)
        elif purpose == FilePurpose.GENERATE_COMPLIANCE_REPORT:
            result = await self._generate_compliance_analysis(content, business_scenario)

        return result

    async def _extract_content(self, file_path: str) -> str:
        """提取文件内容"""
        # 调用 Document Processor 服务
        pass

    async def _prepare_for_knowledge_base(self, content: str) -> Dict[str, Any]:
        """准备知识库更新"""
        return {
            "action": "update",
            "content": content,
            "suggestions": self._analyze_for_kb_update(content)
        }

    async def _generate_compliance_analysis(
        self,
        content: str,
        scenario: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成合规分析报告"""
        return {
            "action": "analyze",
            "content": content,
            "scenario": scenario,
            "report": self._create_compliance_report(content, scenario)
        }
```

### 2.4 API 端点更新

#### 2.4.1 更新聊天端点

```python
# services/main-app/app/api/v1/chat.py

from fastapi import APIRouter, File, UploadFile, Form
from app.services.file_processor_service import FileProcessorService, FilePurpose

router = APIRouter()

@router.post("/chat/completions")
async def chat_completions(
    message: str = Form(...),
    file: Optional[UploadFile] = File(None),
    file_purpose: Optional[str] = Form(None),
    business_scenario: Optional[str] = Form(None),
    min_response_length: int = Form(5000),
    language: str = Form("zh")
):
    """增强的聊天端点，支持文件上传和处理"""

    # 1. 处理文件（如果有）
    file_context = None
    if file:
        file_processor = FileProcessorService()
        file_context = await file_processor.process_file(
            file,
            FilePurpose(file_purpose) if file_purpose else FilePurpose.GENERATE_COMPLIANCE_REPORT,
            business_scenario
        )

    # 2. 创建 RAG chain
    rag_chain = ComplianceRAGChain(
        min_response_length=min_response_length,
        language=language
    )

    # 3. 生成回答
    response = await rag_chain.ainvoke({
        "input": message,
        "file_context": file_context,
        "business_scenario": business_scenario
    })

    return response
```

### 2.5 前端集成

#### 2.5.1 更新 ChatInterface

```typescript
// frontend/src/components/ChatInterface/ChatInterface.tsx

interface FileAttachment {
  file: File;
  purpose: 'update_knowledge_base' | 'generate_compliance_report';
  businessScenario?: string;
}

const ChatInterface: React.FC = () => {
  const [attachedFiles, setAttachedFiles] = useState<FileAttachment[]>([]);
  const [minResponseLength, setMinResponseLength] = useState(5000);

  const handleSendMessage = async (message: string) => {
    const formData = new FormData();
    formData.append('message', message);
    formData.append('min_response_length', minResponseLength.toString());
    formData.append('language', i18n.language);

    // 添加文件
    attachedFiles.forEach((attachment, index) => {
      formData.append(`file_${index}`, attachment.file);
      formData.append(`file_purpose_${index}`, attachment.purpose);
      if (attachment.businessScenario) {
        formData.append(`business_scenario_${index}`, attachment.businessScenario);
      }
    });

    // 发送请求
    const response = await fetch('/api/v1/chat/completions', {
      method: 'POST',
      body: formData
    });

    // 处理 Markdown 响应
    const result = await response.json();
    // 渲染 Markdown
  };

  // ...
};
```

### 2.6 配置管理

#### 2.6.1 添加提示词配置

```python
# services/main-app/app/core/config.py

class Settings(BaseSettings):
    # ...

    # 提示词配置
    PROMPT_LANGUAGE: str = "zh"  # 默认中文
    MIN_RESPONSE_LENGTH: int = 5000  # 最小回答长度
    ENABLE_EMOJI: bool = True  # 启用 emoji
    ENABLE_MARKDOWN: bool = True  # 启用 Markdown
    KNOWLEDGE_BASE_ONLY: bool = True  # 仅使用知识库

    # 回答章节字数配置
    SECTION_WORD_COUNTS: Dict[str, int] = {
        "problem_analysis": 800,
        "compliance_requirements": 1200,
        "solution": 2000,
        "risk_warning": 800,
        "references": 600,
        "follow_up": 700,
        "monitoring": 600
    }
```

## 三、实施步骤

### 第一阶段：基础集成（1-2天）
1. 创建 `compliance_prompts.py` 文件
2. 迁移 Dify 提示词到新文件
3. 更新 `prompts.py` 引用
4. 测试基本功能

### 第二阶段：功能增强（2-3天）
1. 实现字数扩展逻辑
2. 完善 Markdown 格式化
3. 添加 emoji 支持
4. 实现知识库验证

### 第三阶段：文件处理（2-3天）
1. 创建文件处理服务
2. 集成 Document Processor
3. 实现不同处理目的的逻辑
4. 添加文件类型验证

### 第四阶段：前端支持（1-2天）
1. 更新聊天界面
2. 添加文件上传组件
3. 实现 Markdown 渲染
4. 添加配置选项

### 第五阶段：测试优化（1-2天）
1. 端到端测试
2. 性能优化
3. 错误处理
4. 文档更新

## 四、测试计划

### 4.1 单元测试
- 提示词格式化测试
- 字数统计测试
- Markdown 渲染测试
- 文件处理测试

### 4.2 集成测试
- RAG Chain 与新提示词集成
- 文件上传流程测试
- 多语言支持测试
- 知识库查询测试

### 4.3 性能测试
- 5000字回答生成时间
- 文件处理速度
- 并发请求处理
- 内存使用监控

## 五、注意事项

1. **兼容性**：保持与现有 API 的向后兼容
2. **性能**：长文本生成可能影响响应时间，需要优化
3. **存储**：长回答需要更多存储空间
4. **流式输出**：支持流式输出以改善用户体验
5. **错误处理**：完善的错误处理和用户提示

## 六、预期效果

1. **专业性提升**：回答更加专业、详细、结构化
2. **合规性保证**：严格基于知识库，避免错误信息
3. **用户体验改善**：Markdown 格式美观，emoji 增强可读性
4. **功能完整**：支持文件上传和多种处理目的
5. **可维护性**：模块化设计，易于维护和扩展