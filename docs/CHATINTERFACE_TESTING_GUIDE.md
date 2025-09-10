# ChatInterface组件测试指南

## 测试策略概述

基于ChatInterface组件规范，制定分层测试策略，确保每个功能点的可测试性和质量保证。

## 1. 单元测试（Unit Tests）

### 1.1 组件渲染测试

#### MessageList组件测试
```typescript
// frontend/src/components/ChatInterface/__tests__/MessageList.test.tsx
import { render, screen } from '@testing-library/react';
import { MessageList } from '../MessageList';

describe('MessageList', () => {
  it('应该正确渲染消息列表', () => {
    const messages = [
      { id: '1', role: 'user', content: '你好', timestamp: new Date() },
      { id: '2', role: 'assistant', content: '您好！', timestamp: new Date() }
    ];
    
    render(<MessageList messages={messages} />);
    expect(screen.getByText('你好')).toBeInTheDocument();
    expect(screen.getByText('您好！')).toBeInTheDocument();
  });

  it('应该自动滚动到底部', () => {
    // 测试滚动行为
  });

  it('应该支持虚拟滚动（大量消息）', () => {
    // 测试1000+消息的渲染性能
  });
});
```

#### InputArea组件测试
```typescript
// frontend/src/components/ChatInterface/__tests__/InputArea.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { InputArea } from '../InputArea';

describe('InputArea', () => {
  it('应该处理文本输入', () => {
    const onSend = jest.fn();
    render(<InputArea onSend={onSend} />);
    
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: '测试消息' } });
    fireEvent.keyPress(input, { key: 'Enter', code: 13 });
    
    expect(onSend).toHaveBeenCalledWith('测试消息');
  });

  it('应该支持Shift+Enter换行', () => {
    // 测试多行输入
  });

  it('应该限制字符数（4096）', () => {
    // 测试字数限制
  });
});
```

### 1.2 Hook测试

#### useWebSocket测试
```typescript
// frontend/src/hooks/__tests__/useWebSocket.test.ts
import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '../useWebSocket';
import WS from 'jest-websocket-mock';

describe('useWebSocket', () => {
  let server: WS;

  beforeEach(() => {
    server = new WS('ws://localhost:8000/ws');
  });

  afterEach(() => {
    WS.clean();
  });

  it('应该建立WebSocket连接', async () => {
    const { result } = renderHook(() => 
      useWebSocket('ws://localhost:8000/ws')
    );

    await server.connected;
    expect(result.current.isConnected).toBe(true);
  });

  it('应该处理消息接收', async () => {
    const onMessage = jest.fn();
    renderHook(() => 
      useWebSocket('ws://localhost:8000/ws', { onMessage })
    );

    await server.connected;
    
    act(() => {
      server.send(JSON.stringify({ type: 'message', data: 'test' }));
    });

    expect(onMessage).toHaveBeenCalledWith({ type: 'message', data: 'test' });
  });

  it('应该自动重连', async () => {
    // 测试断线重连机制
  });
});
```

## 2. 集成测试（Integration Tests）

### 2.1 完整对话流程测试

```typescript
// frontend/src/components/ChatInterface/__tests__/ChatInterface.integration.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { ChatInterface } from '../ChatInterface';
import { mockStore } from '../../../test/utils';

describe('ChatInterface集成测试', () => {
  it('完整对话流程', async () => {
    const store = mockStore({
      chat: {
        messages: [],
        isLoading: false
      }
    });

    render(
      <Provider store={store}>
        <ChatInterface />
      </Provider>
    );

    // 1. 输入消息
    const input = screen.getByPlaceholderText('输入消息...');
    fireEvent.change(input, { target: { value: '什么是GDPR？' } });
    
    // 2. 发送消息
    const sendButton = screen.getByRole('button', { name: /发送/i });
    fireEvent.click(sendButton);

    // 3. 验证用户消息显示
    expect(screen.getByText('什么是GDPR？')).toBeInTheDocument();

    // 4. 验证加载状态
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();

    // 5. 等待AI回复
    await waitFor(() => {
      expect(screen.getByText(/GDPR是欧盟的数据保护法规/)).toBeInTheDocument();
    });

    // 6. 验证输入框清空
    expect(input).toHaveValue('');
  });
});
```

### 2.2 文件上传流程测试

```typescript
describe('文件上传集成测试', () => {
  it('拖拽上传文件', async () => {
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    
    const { container } = render(<ChatInterface enableUpload />);
    const dropZone = container.querySelector('.drop-zone');
    
    // 模拟拖拽
    fireEvent.dragEnter(dropZone, { dataTransfer: { files: [file] } });
    fireEvent.drop(dropZone, { dataTransfer: { files: [file] } });
    
    // 验证文件显示
    await waitFor(() => {
      expect(screen.getByText('test.pdf')).toBeInTheDocument();
    });
    
    // 验证上传进度
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
});
```

## 3. E2E测试（End-to-End Tests）

### 3.1 Playwright测试配置

```typescript
// tests/e2e/playwright.config.ts
import { PlaywrightTestConfig } from '@playwright/test';

const config: PlaywrightTestConfig = {
  testDir: './specs',
  timeout: 30000,
  use: {
    baseURL: 'http://localhost:5173',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'Chrome', use: { browserName: 'chromium' } },
    { name: 'Firefox', use: { browserName: 'firefox' } },
    { name: 'Safari', use: { browserName: 'webkit' } },
  ],
};

export default config;
```

### 3.2 E2E测试用例

```typescript
// tests/e2e/specs/chat.spec.ts
import { test, expect } from '@playwright/test';

test.describe('ChatInterface E2E测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('用户完整对话流程', async ({ page }) => {
    // 1. 登录
    await page.fill('[data-testid="username"]', 'testuser');
    await page.fill('[data-testid="password"]', 'testpass');
    await page.click('[data-testid="login-button"]');

    // 2. 等待聊天界面加载
    await page.waitForSelector('[data-testid="chat-interface"]');

    // 3. 发送消息
    await page.fill('[data-testid="message-input"]', '请解释GDPR');
    await page.press('[data-testid="message-input"]', 'Enter');

    // 4. 验证消息发送
    await expect(page.locator('text=请解释GDPR')).toBeVisible();

    // 5. 等待AI回复（流式）
    await expect(page.locator('[data-testid="streaming-message"]')).toBeVisible();
    
    // 6. 验证完整回复
    await expect(page.locator('text=/GDPR.*数据保护/')).toBeVisible({ timeout: 10000 });
  });

  test('文件上传和处理', async ({ page }) => {
    // 上传文件测试
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('test-files/sample.pdf');
    
    // 验证上传成功
    await expect(page.locator('text=sample.pdf')).toBeVisible();
  });

  test('会话管理', async ({ page }) => {
    // 创建新会话
    await page.click('[data-testid="new-session"]');
    
    // 验证会话切换
    await page.click('[data-testid="session-1"]');
    await expect(page.locator('[data-testid="session-1"]')).toHaveClass(/active/);
  });
});
```

## 4. 性能测试

### 4.1 组件性能测试

```typescript
// tests/performance/ChatInterface.perf.test.tsx
import { measurePerformance } from '@testing-library/react';

describe('ChatInterface性能测试', () => {
  it('渲染1000条消息的性能', async () => {
    const messages = Array.from({ length: 1000 }, (_, i) => ({
      id: `${i}`,
      role: i % 2 === 0 ? 'user' : 'assistant',
      content: `Message ${i}`,
      timestamp: new Date()
    }));

    const { renderTime } = await measurePerformance(
      <MessageList messages={messages} />
    );

    expect(renderTime).toBeLessThan(100); // 100ms内渲染完成
  });

  it('输入响应性能', async () => {
    // 测试输入延迟
  });
});
```

### 4.2 负载测试

```javascript
// tests/performance/locustfile.py
from locust import HttpUser, task, between

class ChatUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def send_message(self):
        self.client.post("/api/v1/chat/messages", json={
            "message": "测试消息",
            "session_id": self.session_id
        })
    
    @task(2)
    def upload_file(self):
        with open('test.pdf', 'rb') as f:
            self.client.post("/api/v1/documents/upload",
                           files={'file': f})
    
    def on_start(self):
        # 登录获取token
        response = self.client.post("/api/v1/auth/login", json={
            "username": "test",
            "password": "test"
        })
        self.token = response.json()["token"]
        self.session_id = "test-session"
```

## 5. 测试数据准备

### 5.1 Mock数据

```typescript
// frontend/src/test/mocks/chatMocks.ts
export const mockMessages = [
  {
    id: '1',
    role: 'user' as const,
    content: '什么是数据合规？',
    timestamp: new Date('2024-01-01T10:00:00'),
    status: 'sent' as const
  },
  {
    id: '2',
    role: 'assistant' as const,
    content: '数据合规是指...',
    timestamp: new Date('2024-01-01T10:00:10'),
    status: 'sent' as const,
    references: [
      {
        source: 'GDPR Article 5',
        relevance: 0.95,
        content: '...'
      }
    ]
  }
];

export const mockWebSocketMessage = {
  type: 'stream_chunk',
  data: {
    content: '这是',
    done: false
  }
};
```

### 5.2 测试环境配置

```bash
# .env.test
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_ENABLE_MOCKS=true
```

## 6. 测试执行计划

### 6.1 开发阶段测试

```bash
# 单元测试（开发时持续运行）
npm run test:watch

# 组件测试（提交前）
npm run test:components

# 集成测试（功能完成后）
npm run test:integration
```

### 6.2 CI/CD测试流程

```yaml
# .github/workflows/test.yml
name: Test ChatInterface

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install dependencies
        run: npm ci
        
      - name: Run unit tests
        run: npm test -- --coverage
        
      - name: Run integration tests
        run: npm run test:integration
        
      - name: Run E2E tests
        run: npx playwright test
        
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 7. 测试覆盖率目标

| 组件 | 目标覆盖率 | 优先级 |
|------|------------|--------|
| MessageList | 90% | P0 |
| InputArea | 90% | P0 |
| StreamingMessage | 85% | P0 |
| WebSocket Hooks | 85% | P0 |
| FileUpload | 80% | P1 |
| SessionManager | 80% | P1 |
| PromptTemplates | 75% | P2 |

## 8. 测试检查清单

### P0功能测试（必须）
- [ ] 消息发送和接收
- [ ] 消息正确显示
- [ ] 输入框功能
- [ ] 流式响应显示
- [ ] WebSocket连接
- [ ] 基础错误处理

### P1功能测试（重要）
- [ ] 文件上传
- [ ] 会话管理
- [ ] 消息操作（复制/编辑/重试）
- [ ] 自动重连
- [ ] 本地存储

### P2功能测试（增强）
- [ ] 提示词模板
- [ ] 知识库引用
- [ ] 响应式布局
- [ ] 主题切换
- [ ] 快捷键

## 9. Bug报告模板

```markdown
### Bug描述
[清晰描述问题]

### 重现步骤
1. 打开聊天界面
2. 输入消息"..."
3. 点击发送
4. 观察到错误

### 期望行为
[描述期望的正确行为]

### 实际行为
[描述实际发生的情况]

### 截图/录屏
[如有相关截图或录屏]

### 环境信息
- 浏览器: Chrome 120
- 操作系统: macOS 14
- 组件版本: 1.0.0

### 相关测试用例
- [ ] MessageList.test.tsx - Line 45
```

## 10. 测试工具和资源

### 测试工具
- **单元测试**: Vitest + React Testing Library
- **E2E测试**: Playwright
- **性能测试**: Lighthouse + Locust
- **Mock工具**: MSW (Mock Service Worker)
- **覆盖率**: C8 / Istanbul

### 参考资源
- [React Testing Library文档](https://testing-library.com/docs/react-testing-library/intro/)
- [Playwright文档](https://playwright.dev/)
- [Vitest文档](https://vitest.dev/)
- [MSW文档](https://mswjs.io/)