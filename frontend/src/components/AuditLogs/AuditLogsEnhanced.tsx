import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  Avatar,
  Alert,
  CircularProgress,
  Switch,
  FormControlLabel,
  Badge,
  IconButton,
  Tooltip,
  Chip,
} from '@mui/material';
import {
  Security as SecurityIcon,
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon,
  Notifications as NotificationsIcon,
  Refresh as RefreshIcon,
  GetApp as ExportIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// 导入子组件
import LogFilter, { LogFilter as LogFilterType } from './LogFilter';
import LogTable, { AuditLog, SortField, SortConfig } from './LogTable';
import LogDetailDialog, { LogDetail } from './LogDetailDialog';
import LogPagination from './LogPagination';

// 样式化组件
const StyledCard = styled(Card)(({ theme }) => ({
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  color: 'white',
  marginBottom: theme.spacing(2),
}));

// 通知类型
interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

const AuditLogsEnhanced: React.FC = () => {
  // 状态管理
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [filteredLogs, setFilteredLogs] = useState<AuditLog[]>([]);
  
  // 过滤和搜索
  const [filter, setFilter] = useState<LogFilterType>({
    searchTerm: '',
    resourceType: 'all',
    status: 'all',
    severity: 'all',
    userId: 'all',
    dateRange: { start: null, end: null },
    ipAddress: '',
    action: 'all',
  });
  
  // 排序
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    field: 'timestamp',
    direction: 'desc',
  });
  
  // 分页
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(25);
  
  // WebSocket和实时功能
  const [realtimeEnabled, setRealtimeEnabled] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [wsReconnecting, setWsReconnecting] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // 通知系统
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  
  // 日志详情
  const [selectedLog, setSelectedLog] = useState<LogDetail | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  
  // 导出功能
  const [exporting, setExporting] = useState(false);

  // 模拟审计日志数据
  const mockLogs: AuditLog[] = useMemo(() => [
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
      userId: 'user001',
      userName: '张三',
      action: '上传文档',
      resource: '数据安全法.pdf',
      resourceType: 'document',
      details: '上传合规文档到知识库',
      ipAddress: '192.168.1.100',
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      status: 'success',
      severity: 'medium',
    },
    {
      id: '3',
      timestamp: '2025-01-21T10:20:45Z',
      userId: 'user001',
      userName: '张三',
      action: '合规分析',
      resource: '数据合规分析助手',
      resourceType: 'chat',
      details: '询问个人信息保护相关问题',
      ipAddress: '192.168.1.100',
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      status: 'success',
      severity: 'low',
    },
    {
      id: '4',
      timestamp: '2025-01-21T10:15:30Z',
      userId: 'user002',
      userName: '李四',
      action: '删除文档',
      resource: '旧版政策.docx',
      resourceType: 'document',
      details: '删除过期的合规文档',
      ipAddress: '192.168.1.101',
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
      status: 'success',
      severity: 'medium',
    },
    {
      id: '5',
      timestamp: '2025-01-21T10:10:15Z',
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
    {
      id: '6',
      timestamp: '2025-01-21T10:05:00Z',
      userId: 'user001',
      userName: '张三',
      action: '修改设置',
      resource: '系统设置',
      resourceType: 'system',
      details: '修改数据保留期限设置',
      ipAddress: '192.168.1.100',
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      status: 'success',
      severity: 'high',
    },
    {
      id: '7',
      timestamp: '2025-01-21T09:55:30Z',
      userId: 'user004',
      userName: '赵六',
      action: '数据导出',
      resource: '用户数据导出',
      resourceType: 'system',
      details: '导出用户个人信息数据',
      ipAddress: '192.168.1.103',
      userAgent: 'Mozilla/5.0 (Linux; x86_64) AppleWebKit/537.36',
      status: 'success',
      severity: 'critical',
    },
    {
      id: '8',
      timestamp: '2025-01-21T09:50:15Z',
      userId: 'user002',
      userName: '李四',
      action: '权限变更',
      resource: '用户权限管理',
      resourceType: 'user',
      details: '修改用户访问权限',
      ipAddress: '192.168.1.101',
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
      status: 'success',
      severity: 'high',
    },
  ], []);

  // 获取可用的过滤选项
  const availableUsers = useMemo(() => 
    Array.from(new Set(logs.map(log => log.userName))), [logs]
  );
  
  const availableActions = useMemo(() => 
    Array.from(new Set(logs.map(log => log.action))), [logs]
  );
  
  const availableIpAddresses = useMemo(() => 
    Array.from(new Set(logs.map(log => log.ipAddress))), [logs]
  );

  // 过滤日志
  const applyFilters = useCallback((logs: AuditLog[], filter: LogFilterType) => {
    return logs.filter(log => {
      // 搜索过滤
      const searchLower = filter.searchTerm.toLowerCase();
      const matchesSearch = !filter.searchTerm || 
        log.userName.toLowerCase().includes(searchLower) ||
        log.action.toLowerCase().includes(searchLower) ||
        log.resource.toLowerCase().includes(searchLower) ||
        log.ipAddress.toLowerCase().includes(searchLower) ||
        log.details.toLowerCase().includes(searchLower);
      
      // 资源类型过滤
      const matchesType = filter.resourceType === 'all' || log.resourceType === filter.resourceType;
      
      // 状态过滤
      const matchesStatus = filter.status === 'all' || log.status === filter.status;
      
      // 严重程度过滤
      const matchesSeverity = filter.severity === 'all' || log.severity === filter.severity;
      
      // 用户过滤
      const matchesUser = filter.userId === 'all' || log.userName === filter.userId;
      
      // 操作过滤
      const matchesAction = filter.action === 'all' || log.action === filter.action;
      
      // IP地址过滤
      const matchesIp = !filter.ipAddress || log.ipAddress.includes(filter.ipAddress);
      
      // 日期范围过滤
      const logDate = new Date(log.timestamp);
      const matchesDateRange = (!filter.dateRange.start || logDate >= filter.dateRange.start) &&
                              (!filter.dateRange.end || logDate <= filter.dateRange.end);
      
      return matchesSearch && matchesType && matchesStatus && matchesSeverity && 
             matchesUser && matchesAction && matchesIp && matchesDateRange;
    });
  }, []);

  // 应用过滤
  useEffect(() => {
    const filtered = applyFilters(logs, filter);
    setFilteredLogs(filtered);
    setCurrentPage(1); // 重置到第一页
  }, [logs, filter, applyFilters]);

  // 计算总页数
  const totalPages = Math.ceil(filteredLogs.length / itemsPerPage);

  // 排序处理
  const handleSort = useCallback((field: SortField) => {
    setSortConfig(prev => ({
      field,
      direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  }, []);

  // 分页处理
  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
  }, []);

  const handleItemsPerPageChange = useCallback((newItemsPerPage: number) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1);
  }, []);

  // 查看日志详情
  const handleViewDetail = useCallback((log: AuditLog) => {
    const logDetail: LogDetail = {
      id: log.id,
      timestamp: log.timestamp,
      userId: log.userId,
      userName: log.userName,
      action: log.action,
      resource: log.resource,
      resourceType: log.resourceType,
      details: log.details,
      ipAddress: log.ipAddress,
      userAgent: log.userAgent,
      status: log.status,
      severity: log.severity,
      requestId: `req_${log.id}`,
      sessionId: `session_${log.userId}`,
      additionalData: {
        browser: log.userAgent.includes('Chrome') ? 'Chrome' : 
                log.userAgent.includes('Firefox') ? 'Firefox' : 
                log.userAgent.includes('Safari') ? 'Safari' : 'Unknown',
        os: log.userAgent.includes('Windows') ? 'Windows' : 
            log.userAgent.includes('Mac') ? 'macOS' : 
            log.userAgent.includes('Linux') ? 'Linux' : 'Unknown',
      }
    };
    
    setSelectedLog(logDetail);
    setDetailDialogOpen(true);
  }, []);

  // 添加通知
  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      read: false,
    };
    
    setNotifications(prev => [newNotification, ...prev]);
    setUnreadCount(prev => prev + 1);
  }, []);

  // WebSocket连接管理
  const connectWebSocket = useCallback(() => {
    if (!realtimeEnabled) return;
    
    try {
      const userId = 'current_user';
      const wsUrl = `ws://localhost:8888/api/v1/ws/audit/${userId}`;
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        setWsConnected(true);
        setWsReconnecting(false);
        console.log('WebSocket连接已建立');
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'audit_event') {
            const newLog: AuditLog = {
              id: data.id,
              timestamp: data.timestamp,
              userId: data.user_id,
              userName: data.user_name || '未知用户',
              action: data.event_type,
              resource: data.resource || '系统',
              resourceType: data.resource_type || 'system',
              details: data.details || '',
              ipAddress: data.ip_address || '未知',
              userAgent: data.user_agent || '未知',
              status: data.status || 'success',
              severity: data.severity || 'low',
            };
            
            setLogs(prevLogs => [newLog, ...prevLogs]);
            
            addNotification({
              type: data.severity === 'critical' ? 'error' : 
                    data.severity === 'high' ? 'warning' : 'info',
              title: '新的审计事件',
              message: `${newLog.userName} 执行了 ${newLog.action}`,
            });
          }
        } catch (error) {
          console.error('解析WebSocket消息失败:', error);
        }
      };
      
      wsRef.current.onclose = () => {
        setWsConnected(false);
        console.log('WebSocket连接已关闭');
        
        if (realtimeEnabled) {
          setWsReconnecting(true);
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, 3000);
        }
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket错误:', error);
        setWsConnected(false);
      };
    } catch (error) {
      console.error('WebSocket连接失败:', error);
    }
  }, [realtimeEnabled, addNotification]);

  // 断开WebSocket连接
  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    setWsConnected(false);
    setWsReconnecting(false);
  }, []);

  // 加载日志数据
  const loadLogs = useCallback(async () => {
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      setLogs(mockLogs);
    } catch (error) {
      console.error('加载日志失败:', error);
      addNotification({
        type: 'error',
        title: '加载失败',
        message: '无法加载审计日志数据',
      });
    } finally {
      setLoading(false);
    }
  }, [mockLogs, addNotification]);

  // 导出日志
  const handleExport = useCallback(async () => {
    setExporting(true);
    try {
      const csvContent = [
        ['时间', '用户', '操作', '资源', '类型', '状态', '严重程度', 'IP地址', '详情'].join(','),
        ...filteredLogs.map(log => [
          log.timestamp,
          log.userName,
          log.action,
          log.resource,
          log.resourceType,
          log.status,
          log.severity,
          log.ipAddress,
          `"${log.details}"`
        ].join(','))
      ].join('\n');
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `audit_logs_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      addNotification({
        type: 'success',
        title: '导出成功',
        message: `已导出 ${filteredLogs.length} 条日志记录`,
      });
    } catch (error) {
      console.error('导出失败:', error);
      addNotification({
        type: 'error',
        title: '导出失败',
        message: '导出日志时发生错误',
      });
    } finally {
      setExporting(false);
    }
  }, [filteredLogs, addNotification]);

  // 获取统计信息
  const getStats = useCallback(() => {
    const total = logs.length;
    const success = logs.filter(log => log.status === 'success').length;
    const failed = logs.filter(log => log.status === 'failed').length;
    const critical = logs.filter(log => log.severity === 'critical').length;
    
    return { total, success, failed, critical };
  }, [logs]);

  const stats = getStats();

  // 初始化
  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  // WebSocket连接管理
  useEffect(() => {
    if (realtimeEnabled) {
      connectWebSocket();
    } else {
      disconnectWebSocket();
    }
    
    return () => {
      disconnectWebSocket();
    };
  }, [realtimeEnabled, connectWebSocket, disconnectWebSocket]);

  if (loading && logs.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* 页面标题和实时状态 */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main' }}>
          审计日志 (增强版)
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {/* 实时状态指示器 */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {wsConnected ? (
              <Tooltip title="实时连接正常">
                <WifiIcon color="success" />
              </Tooltip>
            ) : wsReconnecting ? (
              <Tooltip title="正在重连...">
                <CircularProgress size={20} />
              </Tooltip>
            ) : (
              <Tooltip title="实时连接断开">
                <WifiOffIcon color="error" />
              </Tooltip>
            )}
            
            <FormControlLabel
              control={
                <Switch
                  checked={realtimeEnabled}
                  onChange={(e) => setRealtimeEnabled(e.target.checked)}
                  color="primary"
                />
              }
              label="实时更新"
            />
          </Box>
          
          {/* 通知按钮 */}
          <Tooltip title="通知">
            <IconButton onClick={() => setShowNotifications(!showNotifications)}>
              <Badge badgeContent={unreadCount} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
          </Tooltip>
          
          {/* 刷新按钮 */}
          <Tooltip title="刷新数据">
            <IconButton onClick={loadLogs} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          
          {/* 导出按钮 */}
          <Tooltip title="导出日志">
            <IconButton onClick={handleExport} disabled={exporting || filteredLogs.length === 0}>
              <ExportIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* 统计卡片 */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StyledCard>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 600 }}>
                    {stats.total}
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                    总日志数
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)' }}>
                  <SecurityIcon />
                </Avatar>
              </Box>
            </CardContent>
          </StyledCard>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #4caf50 0%, #45a049 100%)', color: 'white' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 600 }}>
                    {stats.success}
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                    成功操作
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)' }}>
                  <SecurityIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)', color: 'white' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 600 }}>
                    {stats.failed}
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                    失败操作
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)' }}>
                  <SecurityIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #9c27b0 0%, #7b1fa2 100%)', color: 'white' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 600 }}>
                    {stats.critical}
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                    严重事件
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)' }}>
                  <SecurityIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 过滤器 */}
      <LogFilter
        filter={filter}
        onFilterChange={setFilter}
        onClearFilter={() => setFilter({
          searchTerm: '',
          resourceType: 'all',
          status: 'all',
          severity: 'all',
          userId: 'all',
          dateRange: { start: null, end: null },
          ipAddress: '',
          action: 'all',
        })}
        availableUsers={availableUsers}
        availableActions={availableActions}
        availableIpAddresses={availableIpAddresses}
      />

      {/* 日志表格 */}
      <LogTable
        logs={filteredLogs}
        loading={loading}
        sortConfig={sortConfig}
        onSort={handleSort}
        onViewDetail={handleViewDetail}
        page={currentPage}
        itemsPerPage={itemsPerPage}
      />

      {/* 分页 */}
      <Box sx={{ mt: 2 }}>
        <LogPagination
          currentPage={currentPage}
          totalPages={totalPages}
          totalItems={filteredLogs.length}
          itemsPerPage={itemsPerPage}
          onPageChange={handlePageChange}
          onItemsPerPageChange={handleItemsPerPageChange}
          loading={loading}
        />
      </Box>

      {/* 无数据提示 */}
      {filteredLogs.length === 0 && !loading && (
        <Alert severity="info" sx={{ mt: 2 }}>
          没有找到匹配的审计日志记录。请尝试调整过滤条件。
        </Alert>
      )}

      {/* 日志详情对话框 */}
      <LogDetailDialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        logDetail={selectedLog}
      />
    </Box>
  );
};

export default AuditLogsEnhanced;
