# ChatInterface组件功能规范

## 组件概述

ChatInterface是合规助手的核心UI组件，提供用户与AI助手的对话交互界面。参考Dify和ChatGPT的设计，实现流式对话、文件上传、历史记录等功能。

## 功能定义

### 1. 核心功能

#### 1.1 消息展示
- **用户消息**: 右侧对齐，蓝色背景
- **AI回复**: 左侧对齐，灰色背景
- **系统提示**: 居中显示，淡色背景
- **时间戳**: 每条消息显示发送时间
- **头像**: 用户和AI助手头像

#### 1.2 输入区域
- **文本输入框**: 
  - 支持多行输入（Shift+Enter换行）
  - 自动调整高度（最大5行）
  - 支持Markdown格式
  - 字数统计（显示当前/最大字数）
  
- **发送按钮**:
  - Enter发送（可配置）
  - 发送中禁用状态
  - 快捷键提示

#### 1.3 文件上传
- **支持格式**: PDF, DOCX, XLSX, PPTX, TXT, MD
- **拖拽上传**: 整个对话区域支持拖拽
- **上传进度**: 显示上传百分比
- **文件预览**: 显示文件名、大小、类型图标
- **批量上传**: 支持多文件同时上传

#### 1.4 流式响应
- **打字机效果**: 逐字显示AI回复
- **加载动画**: 三个点的跳动动画
- **中断按钮**: 停止生成按钮
- **部分渲染**: 支持Markdown实时渲染

### 2. 高级功能

#### 2.1 会话管理
- **新建会话**: 清空当前对话
- **会话列表**: 左侧边栏显示历史会话
- **会话重命名**: 自动或手动命名
- **会话删除**: 支持批量删除
- **会话搜索**: 按内容或标题搜索

#### 2.2 消息操作
- **复制**: 复制消息内容
- **编辑**: 编辑已发送消息并重新生成
- **重试**: 重新生成AI回复
- **删除**: 删除单条消息
- **引用**: 引用之前的消息

#### 2.3 提示词模板
- **快速访问**: /命令触发模板列表
- **模板分类**: 按场景分组（合规检查、风险评估等）
- **自定义模板**: 用户创建和保存模板
- **变量替换**: 支持占位符和变量

#### 2.4 知识库引用
- **引用显示**: 显示回答来源
- **查看原文**: 点击查看完整文档
- **相关度分数**: 显示匹配度
- **引用高亮**: 在原文中高亮引用部分

### 3. UI设计规范

#### 3.1 布局结构
```
┌──────────────────────────────────────────────┐
│  Header (标题栏)                              │
│  - Logo  - 会话标题  - 设置按钮                │
├──────────┬───────────────────────────────────┤
│          │                                   │
│  侧边栏   │      消息展示区                    │
│          │   ┌─────────────────────┐        │
│  会话列表  │   │  AI: 您好，我是...   │        │
│          │   └─────────────────────┘        │
│          │   ┌─────────────────────┐        │
│          │   │  用户: 请帮我分析...  │        │
│          │   └─────────────────────┘        │
│          │                                   │
├──────────┴───────────────────────────────────┤
│  输入区域                                      │
│  [📎] [输入框........................] [发送]  │
└──────────────────────────────────────────────┘
```

#### 3.2 响应式设计
- **桌面端**: 完整三栏布局
- **平板端**: 可收起侧边栏
- **移动端**: 底部输入，全屏对话

#### 3.3 主题支持
- **亮色主题**: 默认白色背景
- **暗色主题**: 深色背景护眼模式
- **主题切换**: 顶部快速切换按钮

### 4. 技术实现

#### 4.1 组件结构
```typescript
// 主组件
interface ChatInterfaceProps {
  sessionId?: string;
  userId: string;
  apiEndpoint: string;
  wsEndpoint?: string;
  enableUpload?: boolean;
  enableStreaming?: boolean;
  maxFileSize?: number;
  placeholder?: string;
}

// 子组件
- MessageList: 消息列表组件
- MessageItem: 单条消息组件
- InputArea: 输入区域组件
- FileUpload: 文件上传组件
- SessionSidebar: 会话侧边栏
- StreamingIndicator: 流式加载指示器
```

#### 4.2 状态管理
```typescript
// Redux State
interface ChatState {
  sessions: Session[];
  currentSession: string | null;
  messages: Message[];
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
  uploadProgress: number;
}

// Message类型
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  attachments?: Attachment[];
  references?: Reference[];
  status: 'sending' | 'sent' | 'error';
}
```

#### 4.3 WebSocket连接
```typescript
// WebSocket事件
- connect: 建立连接
- message: 接收消息
- stream_start: 开始流式响应
- stream_chunk: 接收流式数据块
- stream_end: 流式响应结束
- error: 错误处理
- disconnect: 断开连接
```

#### 4.4 API接口
```typescript
// REST API
POST /api/v1/chat/messages - 发送消息
GET /api/v1/chat/sessions - 获取会话列表
GET /api/v1/chat/sessions/:id - 获取会话详情
DELETE /api/v1/chat/sessions/:id - 删除会话
POST /api/v1/chat/upload - 上传文件

// WebSocket
WS /ws/chat - 实时通信连接
```

### 5. 性能优化

#### 5.1 虚拟滚动
- 大量消息时使用虚拟列表
- 只渲染可视区域的消息
- 动态加载历史消息

#### 5.2 消息缓存
- localStorage缓存最近会话
- IndexedDB存储历史记录
- 离线消息队列

#### 5.3 懒加载
- 图片和附件懒加载
- 代码高亮按需加载
- Markdown渲染器按需加载

### 6. 交互细节

#### 6.1 快捷键
- `Ctrl/Cmd + Enter`: 发送消息
- `Ctrl/Cmd + N`: 新建会话
- `Ctrl/Cmd + /`: 显示命令菜单
- `Esc`: 取消当前操作

#### 6.2 动画效果
- 消息滑入动画
- 加载状态动画
- 平滑滚动到底部
- 按钮hover效果

#### 6.3 错误处理
- 网络断开重连提示
- 发送失败重试
- 文件上传失败提示
- API错误友好提示

### 7. 无障碍支持

- **键盘导航**: 完全键盘可操作
- **屏幕阅读器**: ARIA标签支持
- **高对比度**: 支持高对比度模式
- **字体缩放**: 响应系统字体大小

## 实现优先级

### P0 - 必须实现（MVP）
1. 基础消息收发
2. 文本输入和发送
3. 消息展示
4. 流式响应显示
5. 基础错误处理

### P1 - 应该实现
1. 文件上传
2. 会话管理
3. 消息操作（复制、重试）
4. WebSocket实时通信
5. Markdown渲染

### P2 - 可以实现
1. 提示词模板
2. 知识库引用显示
3. 虚拟滚动优化
4. 主题切换
5. 导出对话

## 参考实现

### 开源项目参考
- [ChatGPT-Next-Web](https://github.com/ChatGPTNextWeb/ChatGPT-Next-Web)
- [Dify Web App](https://github.com/langgenius/dify)
- [Chatbot UI](https://github.com/mckaywrigley/chatbot-ui)

### UI库推荐
- Material-UI Chat组件
- Ant Design Comment组件
- React-Chat-UI
- Stream Chat React

## 测试要点

### 功能测试
- 消息发送和接收
- 文件上传各种格式
- 流式响应中断
- 会话切换保存
- 错误重试机制

### 性能测试
- 1000条消息渲染
- 大文件上传
- 长文本输入
- 并发消息处理

### 兼容性测试
- Chrome/Firefox/Safari
- 移动端适配
- 不同屏幕尺寸
- 网络环境（弱网）