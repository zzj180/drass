# 系统提示词集成状态报告

## 📋 审查日期
2025-09-16

## ✅ 已实现的功能

### 1. 核心提示词迁移
- ✅ **完成** - 从Dify配置文件(`apps/数据合规（父子段）.yml`)成功迁移了2888字符的中文提示词
- ✅ **完成** - 创建了独立的`compliance_prompts.py`模块，包含完整的提示词定义
- ✅ **完成** - 在`prompts.py`中成功集成了新的中文提示词
- ✅ **完成** - RAG链(`compliance_rag_chain.py`)已使用新的系统提示词

### 2. 文档处理能力
- ✅ **完成** - `DocumentService`支持多种文件格式（PDF、DOCX、XLSX、TXT、MD、CSV、图片）
- ✅ **完成** - 本地文档处理器(`local_processor.py`)运行在5003端口，提供fallback支持
- ✅ **完成** - 文档上传API端点(`/api/v1/documents/upload`和`/api/v1/documents/batch`)
- ✅ **完成** - 文档文本提取和分块功能

### 3. 知识库管理
- ✅ **完成** - `VectorStoreService`提供向量存储功能
- ✅ **完成** - 知识库API端点（创建、查询、搜索）
- ✅ **完成** - 支持ChromaDB作为默认向量数据库
- ✅ **完成** - 文档添加到向量存储的功能

### 4. 聊天服务
- ✅ **完成** - `ChatService`集成了RAG链
- ✅ **完成** - 支持流式响应（SSE和WebSocket）
- ✅ **完成** - 支持对话历史管理
- ✅ **完成** - 可选择是否使用知识库（`use_knowledge_base`参数）

### 5. LLM配置
- ✅ **完成** - 支持本地Qwen3-8B-MLX模型
- ✅ **完成** - 支持多种LLM提供商（OpenRouter、OpenAI、vLLM）
- ✅ **完成** - 配置了`max_tokens`参数（可支持长文本生成）

## ⏳ 待实现的功能

### 1. 5000字强制展开逻辑 🔴 高优先级
**位置**: `services/main-app/app/chains/compliance_rag_chain.py`
```python
# 需要在_format_response方法中添加字数检查和扩展逻辑
def _format_response(self, response: Any) -> Dict[str, Any]:
    # 添加字数统计和扩展逻辑
    word_count = len(response.split())
    if word_count < 5000:
        # 触发扩展生成
        pass
```

### 2. Markdown格式化增强 🟡 中优先级
**位置**: 新建`services/main-app/app/utils/markdown_formatter.py`
```python
class MarkdownFormatter:
    """处理Markdown格式化和美化"""
    def format_compliance_response(self, text: str) -> str:
        # 添加emoji
        # 格式化标题
        # 处理列表
        # 添加表格支持
```

### 3. 文件附件处理流程 🔴 高优先级
**位置**: 扩展`services/main-app/app/api/v1/chat.py`
```python
@router.post("/with-attachment")
async def chat_with_attachment(
    file: UploadFile,
    purpose: str,  # "update_knowledge" 或 "generate_report"
    messages: List[ChatMessage],
    # ...
):
    # 处理文件
    # 根据purpose决定处理方式
    # 集成到聊天流程
```

### 4. 响应质量验证 🟡 中优先级
**位置**: `services/main-app/app/chains/validators/`
```python
class ComplianceResponseValidator:
    def validate_word_count(self, text: str) -> bool
    def validate_structure(self, text: str) -> bool
    def validate_markdown_format(self, text: str) -> bool
```

### 5. 提示词配置管理 🟢 低优先级
**位置**: `services/main-app/app/core/config.py`
```python
# 添加提示词相关配置
COMPLIANCE_MIN_WORD_COUNT = 5000
COMPLIANCE_ENABLE_EMOJI = True
COMPLIANCE_ENABLE_MARKDOWN = True
```

## 🔨 实施建议

### 第一阶段（立即实施）
1. **实现5000字强制展开逻辑**
   - 修改`compliance_rag_chain.py`，在生成响应后检查字数
   - 如果不足5000字，使用扩展提示词重新生成
   - 可以使用迭代生成方式，逐步扩展内容

2. **添加文件附件处理**
   - 在聊天API中添加文件上传支持
   - 根据用户选择的目的（更新知识库/生成报告）处理文件
   - 将文件内容集成到提示词上下文中

### 第二阶段（下周实施）
3. **Markdown格式化器**
   - 创建专门的Markdown格式化工具类
   - 自动添加emoji和格式美化
   - 确保输出符合Dify的Markdown规范

4. **响应验证器**
   - 实现响应质量检查
   - 确保满足所有格式和内容要求

### 第三阶段（可选优化）
5. **配置管理优化**
   - 将所有提示词相关配置集中管理
   - 支持运行时动态调整

## 📝 测试清单

- [ ] 测试5000字生成功能
- [ ] 测试文件上传和处理
- [ ] 测试Markdown格式化效果
- [ ] 测试知识库更新流程
- [ ] 测试报告生成功能
- [ ] 测试流式响应中的格式保持

## 🎯 下一步行动

1. 立即开始实现5000字强制展开逻辑
2. 设计文件附件处理的API接口
3. 编写相应的测试用例