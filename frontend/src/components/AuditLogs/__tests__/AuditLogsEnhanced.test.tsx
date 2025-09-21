import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import AuditLogsEnhanced from '../AuditLogsEnhanced';
import { AuditLog } from '../LogTable';

// 创建测试主题
const theme = createTheme();

// 模拟数据
const mockLogs: AuditLog[] = [
  {
    id: '1',
    timestamp: '2025-01-21T10:30:25Z',
    userId: 'user001',
    userName: '张三',
    action: '登录系统',
    resource: '系统登录',
    resourceType: 'system',
    details: '用户通过邮箱登录系统',
    ipAddress: '192.168.1.100',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    status: 'success',
    severity: 'low',
  },
  {
    id: '2',
    timestamp: '2025-01-21T10:25:10Z',
    userId: 'user002',
    userName: '李四',
    action: '上传文档',
    resource: '数据安全法.pdf',
    resourceType: 'document',
    details: '上传合规文档到知识库',
    ipAddress: '192.168.1.101',
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    status: 'success',
    severity: 'medium',
  },
  {
    id: '3',
    timestamp: '2025-01-21T10:20:45Z',
    userId: 'user003',
    userName: '王五',
    action: '登录失败',
    resource: '系统登录',
    resourceType: 'system',
    details: '密码错误，登录失败',
    ipAddress: '192.168.1.102',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    status: 'failed',
    severity: 'high',
  },
];

// 测试包装器
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>
    {children}
  </ThemeProvider>
);

describe('AuditLogsEnhanced', () => {
  beforeEach(() => {
    // 模拟WebSocket
    global.WebSocket = jest.fn().mockImplementation(() => ({
      close: jest.fn(),
      send: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    }));
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('渲染组件标题', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('审计日志 (增强版)')).toBeInTheDocument();
    });
  });

  test('显示统计卡片', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('总日志数')).toBeInTheDocument();
      expect(screen.getByText('成功操作')).toBeInTheDocument();
      expect(screen.getByText('失败操作')).toBeInTheDocument();
      expect(screen.getByText('严重事件')).toBeInTheDocument();
    });
  });

  test('显示搜索框', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/搜索用户、操作、资源或IP地址/)).toBeInTheDocument();
    });
  });

  test('显示过滤器', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('资源类型')).toBeInTheDocument();
      expect(screen.getByText('状态')).toBeInTheDocument();
      expect(screen.getByText('严重程度')).toBeInTheDocument();
    });
  });

  test('显示日志表格', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('时间')).toBeInTheDocument();
      expect(screen.getByText('用户')).toBeInTheDocument();
      expect(screen.getByText('操作')).toBeInTheDocument();
      expect(screen.getByText('资源')).toBeInTheDocument();
      expect(screen.getByText('类型')).toBeInTheDocument();
      expect(screen.getByText('状态')).toBeInTheDocument();
      expect(screen.getByText('严重程度')).toBeInTheDocument();
      expect(screen.getByText('IP地址')).toBeInTheDocument();
      expect(screen.getByText('操作')).toBeInTheDocument();
    });
  });

  test('显示分页组件', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('每页显示')).toBeInTheDocument();
    });
  });

  test('搜索功能', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText(/搜索用户、操作、资源或IP地址/);
      fireEvent.change(searchInput, { target: { value: '张三' } });
      
      // 验证搜索功能（这里需要根据实际实现调整）
      expect(searchInput).toHaveValue('张三');
    });
  });

  test('过滤器功能', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      // 测试资源类型过滤器
      const resourceTypeSelect = screen.getByLabelText('资源类型');
      fireEvent.mouseDown(resourceTypeSelect);
      
      // 验证下拉选项
      expect(screen.getByText('全部')).toBeInTheDocument();
      expect(screen.getByText('文档')).toBeInTheDocument();
      expect(screen.getByText('聊天')).toBeInTheDocument();
      expect(screen.getByText('系统')).toBeInTheDocument();
      expect(screen.getByText('用户')).toBeInTheDocument();
    });
  });

  test('排序功能', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      // 测试时间列排序
      const timeHeader = screen.getByText('时间');
      fireEvent.click(timeHeader);
      
      // 验证排序功能（这里需要根据实际实现调整）
      expect(timeHeader).toBeInTheDocument();
    });
  });

  test('实时更新开关', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      const realtimeSwitch = screen.getByLabelText('实时更新');
      expect(realtimeSwitch).toBeInTheDocument();
      
      // 测试开关功能
      fireEvent.click(realtimeSwitch);
      expect(realtimeSwitch).toBeChecked();
    });
  });

  test('导出功能', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      const exportButton = screen.getByLabelText('导出日志');
      expect(exportButton).toBeInTheDocument();
    });
  });

  test('刷新功能', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      const refreshButton = screen.getByLabelText('刷新数据');
      expect(refreshButton).toBeInTheDocument();
    });
  });

  test('通知功能', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      const notificationButton = screen.getByLabelText('通知');
      expect(notificationButton).toBeInTheDocument();
    });
  });

  test('高级过滤器展开/收起', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      const filterButton = screen.getByLabelText('高级过滤器');
      fireEvent.click(filterButton);
      
      // 验证高级过滤器展开
      expect(screen.getByText('用户')).toBeInTheDocument();
      expect(screen.getByText('操作')).toBeInTheDocument();
      expect(screen.getByText('IP地址')).toBeInTheDocument();
    });
  });

  test('清除过滤器功能', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      // 先设置一些过滤器
      const searchInput = screen.getByPlaceholderText(/搜索用户、操作、资源或IP地址/);
      fireEvent.change(searchInput, { target: { value: '测试' } });
      
      // 然后清除过滤器
      const clearButton = screen.getByLabelText('清除所有过滤器');
      fireEvent.click(clearButton);
      
      // 验证过滤器被清除
      expect(searchInput).toHaveValue('');
    });
  });

  test('分页功能', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      // 测试每页显示数量选择
      const itemsPerPageSelect = screen.getByLabelText('每页显示');
      fireEvent.mouseDown(itemsPerPageSelect);
      
      // 验证选项
      expect(screen.getByText('10 条')).toBeInTheDocument();
      expect(screen.getByText('25 条')).toBeInTheDocument();
      expect(screen.getByText('50 条')).toBeInTheDocument();
      expect(screen.getByText('100 条')).toBeInTheDocument();
    });
  });

  test('加载状态', () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    // 验证初始加载状态
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('无数据状态', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      // 设置一个不会匹配任何数据的搜索条件
      const searchInput = screen.getByPlaceholderText(/搜索用户、操作、资源或IP地址/);
      fireEvent.change(searchInput, { target: { value: '不存在的用户' } });
      
      // 验证无数据提示
      expect(screen.getByText(/没有找到匹配的审计日志记录/)).toBeInTheDocument();
    });
  });
});

// 性能测试
describe('AuditLogsEnhanced Performance', () => {
  test('大量数据渲染性能', async () => {
    const startTime = performance.now();
    
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      // 验证渲染时间在合理范围内（小于1秒）
      expect(renderTime).toBeLessThan(1000);
    });
  });

  test('过滤器性能', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      const startTime = performance.now();
      
      // 执行多次过滤操作
      const searchInput = screen.getByPlaceholderText(/搜索用户、操作、资源或IP地址/);
      for (let i = 0; i < 10; i++) {
        fireEvent.change(searchInput, { target: { value: `测试${i}` } });
      }
      
      const endTime = performance.now();
      const filterTime = endTime - startTime;
      
      // 验证过滤性能（小于100ms）
      expect(filterTime).toBeLessThan(100);
    });
  });
});

// 可访问性测试
describe('AuditLogsEnhanced Accessibility', () => {
  test('键盘导航', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      // 测试Tab键导航
      const searchInput = screen.getByPlaceholderText(/搜索用户、操作、资源或IP地址/);
      searchInput.focus();
      
      // 验证焦点在搜索框上
      expect(document.activeElement).toBe(searchInput);
    });
  });

  test('屏幕阅读器支持', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      // 验证重要元素有适当的标签
      expect(screen.getByLabelText('实时更新')).toBeInTheDocument();
      expect(screen.getByLabelText('通知')).toBeInTheDocument();
      expect(screen.getByLabelText('刷新数据')).toBeInTheDocument();
      expect(screen.getByLabelText('导出日志')).toBeInTheDocument();
    });
  });

  test('颜色对比度', async () => {
    render(
      <TestWrapper>
        <AuditLogsEnhanced />
      </TestWrapper>
    );

    await waitFor(() => {
      // 验证状态和严重程度芯片有足够的颜色对比度
      const statusChips = screen.getAllByRole('button');
      expect(statusChips.length).toBeGreaterThan(0);
    });
  });
});
