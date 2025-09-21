import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  TextField,
  InputAdornment,
  Pagination,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  Grid,
  Avatar,
  Tooltip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Switch,
  FormControlLabel,
  Badge,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  Security as SecurityIcon,
  Person as PersonIcon,
  Description as DocumentIcon,
  Chat as ChatIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  Close as CloseIcon,
  GetApp as ExportIcon,
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// 审计日志数据类型
interface AuditLog {
  id: string;
  timestamp: string;
  userId: string;
  userName: string;
  action: string;
  resource: string;
  resourceType: 'document' | 'chat' | 'system' | 'user';
  details: string;
  ipAddress: string;
  userAgent: string;
  status: 'success' | 'failed' | 'warning';
  severity: 'low' | 'medium' | 'high' | 'critical';
}

// 样式化组件
const StyledCard = styled(Card)(({ theme }) => ({
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  color: 'white',
  marginBottom: theme.spacing(2),
}));

const StyledTableContainer = styled(TableContainer)(({ theme }) => ({
  borderRadius: theme.spacing(1),
  boxShadow: theme.shadows[3],
}));

const StatusChip = styled(Chip)<{ status: string }>(({ status }) => ({
  fontWeight: 600,
  ...(status === 'success' && {
    backgroundColor: '#4caf50',
    color: 'white',
  }),
  ...(status === 'failed' && {
    backgroundColor: '#f44336',
    color: 'white',
  }),
  ...(status === 'warning' && {
    backgroundColor: '#ff9800',
    color: 'white',
  }),
}));

const SeverityChip = styled(Chip)<{ severity: string }>(({ severity }) => ({
  fontWeight: 600,
  ...(severity === 'low' && {
    backgroundColor: '#2196f3',
    color: 'white',
  }),
  ...(severity === 'medium' && {
    backgroundColor: '#ff9800',
    color: 'white',
  }),
  ...(severity === 'high' && {
    backgroundColor: '#f44336',
    color: 'white',
  }),
  ...(severity === 'critical' && {
    backgroundColor: '#9c27b0',
    color: 'white',
  }),
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

// 日志详情类型
interface LogDetail {
  id: string;
  timestamp: string;
  userId: string;
  userName: string;
  action: string;
  resource: string;
  resourceType: string;
  details: string;
  ipAddress: string;
  userAgent: string;
  status: string;
  severity: string;
  requestId?: string;
  sessionId?: string;
  additionalData?: Record<string, any>;
}

const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // WebSocket和实时功能状态
  const [realtimeEnabled, setRealtimeEnabled] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [wsReconnecting, setWsReconnecting] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // 通知系统状态
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  
  // 日志详情对话框状态
  const [selectedLog, setSelectedLog] = useState<LogDetail | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  
  // 导出功能状态
  const [exporting, setExporting] = useState(false);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState<'csv' | 'json' | 'excel'>('csv');
  const [exportDateRange, setExportDateRange] = useState<{start: string, end: string}>({
    start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0]
  });

  // 模拟审计日志数据
  const mockLogs: AuditLog[] = [
    {
      id: '1',
      timestamp: '2025-01-20 14:30:25',
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
      timestamp: '2025-01-20 14:25:10',
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
      timestamp: '2025-01-20 14:20:45',
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
      timestamp: '2025-01-20 14:15:30',
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
      timestamp: '2025-01-20 14:10:15',
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
      timestamp: '2025-01-20 14:05:00',
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
  ];

  // WebSocket连接管理
  const connectWebSocket = useCallback(() => {
    if (!realtimeEnabled) return;
    
    try {
      const userId = 'current_user'; // 在实际应用中从认证系统获取
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
            // 添加新的审计日志到列表顶部
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
            
            // 添加通知
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
        
        // 自动重连
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
  }, [realtimeEnabled]);

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

  // 标记通知为已读
  const markNotificationAsRead = useCallback((notificationId: string) => {
    setNotifications(prev => 
      prev.map(notif => 
        notif.id === notificationId ? { ...notif, read: true } : notif
      )
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  }, []);

  // 清除所有通知
  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
    setUnreadCount(0);
  }, []);

  // 过滤日志
  const filteredLogs = logs.filter(log => {
    const matchesSearch = log.userName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.resource.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesType = filterType === 'all' || log.resourceType === filterType;
    const matchesStatus = filterStatus === 'all' || log.status === filterStatus;
    
    return matchesSearch && matchesType && matchesStatus;
  });

  // 导出日志功能
  const exportLogs = useCallback(async () => {
    setExporting(true);
    try {
      const logsToExport = filteredLogs;
      let content = '';
      let filename = '';
      
      if (exportFormat === 'csv') {
        const headers = ['时间', '用户', '操作', '资源', '类型', '状态', '严重程度', 'IP地址', '详情'];
        const csvContent = [
          headers.join(','),
          ...logsToExport.map(log => [
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
        content = csvContent;
        filename = `audit_logs_${new Date().toISOString().split('T')[0]}.csv`;
      } else if (exportFormat === 'json') {
        content = JSON.stringify(logsToExport, null, 2);
        filename = `audit_logs_${new Date().toISOString().split('T')[0]}.json`;
      }
      
      // 创建下载链接
      const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      addNotification({
        type: 'success',
        title: '导出成功',
        message: `已导出 ${logsToExport.length} 条日志记录`,
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
      setExportDialogOpen(false);
    }
  }, [filteredLogs, exportFormat, addNotification]);

  // 查看日志详情
  const viewLogDetail = useCallback((log: AuditLog) => {
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

  // 加载日志数据
  const loadLogs = useCallback(async () => {
    setLoading(true);
    try {
      // 在实际应用中，这里应该调用真实的API
      await new Promise(resolve => setTimeout(resolve, 1000));
      setLogs(mockLogs);
      setTotalPages(Math.ceil(mockLogs.length / 10));
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
  }, [addNotification]);

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

  // 分页
  const itemsPerPage = 10;
  const startIndex = (page - 1) * itemsPerPage;
  const paginatedLogs = filteredLogs.slice(startIndex, startIndex + itemsPerPage);

  // 获取资源类型图标
  const getResourceIcon = (type: string) => {
    switch (type) {
      case 'document':
        return <DocumentIcon />;
      case 'chat':
        return <ChatIcon />;
      case 'system':
        return <SettingsIcon />;
      case 'user':
        return <PersonIcon />;
      default:
        return <SecurityIcon />;
    }
  };

  // 获取统计信息
  const getStats = () => {
    const total = logs.length;
    const success = logs.filter(log => log.status === 'success').length;
    const failed = logs.filter(log => log.status === 'failed').length;
    const critical = logs.filter(log => log.severity === 'critical').length;
    
    return { total, success, failed, critical };
  };

  const stats = getStats();

  if (loading) {
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
          审计日志
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

      {/* 搜索和过滤 */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <TextField
            placeholder="搜索用户、操作或资源..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ minWidth: 300 }}
          />
          
          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel>资源类型</InputLabel>
            <Select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              label="资源类型"
            >
              <MenuItem value="all">全部</MenuItem>
              <MenuItem value="document">文档</MenuItem>
              <MenuItem value="chat">聊天</MenuItem>
              <MenuItem value="system">系统</MenuItem>
              <MenuItem value="user">用户</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel>状态</InputLabel>
            <Select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              label="状态"
            >
              <MenuItem value="all">全部</MenuItem>
              <MenuItem value="success">成功</MenuItem>
              <MenuItem value="failed">失败</MenuItem>
              <MenuItem value="warning">警告</MenuItem>
            </Select>
          </FormControl>
          
          <IconButton onClick={loadLogs} disabled={loading}>
            <RefreshIcon />
          </IconButton>
          
          <Tooltip title="导出日志">
            <IconButton onClick={() => setExportDialogOpen(true)}>
              <ExportIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Paper>

      {/* 日志表格 */}
      <StyledTableContainer>
        <Table>
          <TableHead>
            <TableRow sx={{ backgroundColor: 'primary.main' }}>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>时间</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>用户</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>操作</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>资源</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>类型</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>状态</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>严重程度</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>IP地址</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedLogs.map((log) => (
              <TableRow key={log.id} hover>
                <TableCell>{log.timestamp}</TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Avatar sx={{ width: 24, height: 24, fontSize: '0.75rem' }}>
                      {log.userName.charAt(0)}
                    </Avatar>
                    {log.userName}
                  </Box>
                </TableCell>
                <TableCell>{log.action}</TableCell>
                <TableCell>{log.resource}</TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {getResourceIcon(log.resourceType)}
                    {log.resourceType}
                  </Box>
                </TableCell>
                <TableCell>
                  <StatusChip label={log.status} status={log.status} size="small" />
                </TableCell>
                <TableCell>
                  <SeverityChip label={log.severity} severity={log.severity} size="small" />
                </TableCell>
                <TableCell>{log.ipAddress}</TableCell>
                <TableCell>
                  <Tooltip title="查看详情">
                    <IconButton size="small" onClick={() => viewLogDetail(log)}>
                      <ViewIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </StyledTableContainer>

      {/* 分页 */}
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
        <Pagination
          count={totalPages}
          page={page}
          onChange={(_, newPage) => setPage(newPage)}
          color="primary"
        />
      </Box>

      {filteredLogs.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          没有找到匹配的审计日志记录。
        </Alert>
      )}

      {/* 通知面板 */}
      {showNotifications && (
        <Paper
          sx={{
            position: 'fixed',
            top: 80,
            right: 20,
            width: 350,
            maxHeight: 500,
            overflow: 'auto',
            zIndex: 1300,
            boxShadow: 3,
          }}
        >
          <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="h6">通知</Typography>
              <Box>
                <IconButton size="small" onClick={clearAllNotifications}>
                  <CloseIcon />
                </IconButton>
              </Box>
            </Box>
          </Box>
          
          {notifications.length === 0 ? (
            <Box sx={{ p: 2, textAlign: 'center', color: 'text.secondary' }}>
              暂无通知
            </Box>
          ) : (
            <List sx={{ p: 0 }}>
              {notifications.map((notification, index) => (
                <React.Fragment key={notification.id}>
                  <ListItem
                    sx={{
                      backgroundColor: notification.read ? 'transparent' : 'action.hover',
                      cursor: 'pointer',
                    }}
                    onClick={() => markNotificationAsRead(notification.id)}
                  >
                    <ListItemIcon>
                      {notification.type === 'error' && <ErrorIcon color="error" />}
                      {notification.type === 'warning' && <WarningIcon color="warning" />}
                      {notification.type === 'info' && <InfoIcon color="info" />}
                      {notification.type === 'success' && <CheckCircleIcon color="success" />}
                    </ListItemIcon>
                    <ListItemText
                      primary={notification.title}
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            {notification.message}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {new Date(notification.timestamp).toLocaleString()}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < notifications.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
        </Paper>
      )}

      {/* 日志详情对话框 */}
      <Dialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SecurityIcon />
            审计日志详情
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedLog && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">时间</Typography>
                  <Typography variant="body1">{selectedLog.timestamp}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">用户</Typography>
                  <Typography variant="body1">{selectedLog.userName}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">操作</Typography>
                  <Typography variant="body1">{selectedLog.action}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">资源</Typography>
                  <Typography variant="body1">{selectedLog.resource}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">状态</Typography>
                  <StatusChip label={selectedLog.status} status={selectedLog.status} size="small" />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">严重程度</Typography>
                  <SeverityChip label={selectedLog.severity} severity={selectedLog.severity} size="small" />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">IP地址</Typography>
                  <Typography variant="body1">{selectedLog.ipAddress}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">请求ID</Typography>
                  <Typography variant="body1">{selectedLog.requestId}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">详情</Typography>
                  <Typography variant="body1">{selectedLog.details}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">用户代理</Typography>
                  <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                    {selectedLog.userAgent}
                  </Typography>
                </Grid>
                {selectedLog.additionalData && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="text.secondary">附加信息</Typography>
                    <Box sx={{ mt: 1 }}>
                      {Object.entries(selectedLog.additionalData).map(([key, value]) => (
                        <Chip
                          key={key}
                          label={`${key}: ${value}`}
                          size="small"
                          sx={{ mr: 1, mb: 1 }}
                        />
                      ))}
                    </Box>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailDialogOpen(false)}>关闭</Button>
        </DialogActions>
      </Dialog>

      {/* 导出对话框 */}
      <Dialog
        open={exportDialogOpen}
        onClose={() => setExportDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>导出审计日志</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>导出格式</InputLabel>
              <Select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value as 'csv' | 'json' | 'excel')}
                label="导出格式"
              >
                <MenuItem value="csv">CSV</MenuItem>
                <MenuItem value="json">JSON</MenuItem>
                <MenuItem value="excel">Excel</MenuItem>
              </Select>
            </FormControl>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>日期范围</Typography>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  type="date"
                  label="开始日期"
                  value={exportDateRange.start}
                  onChange={(e) => setExportDateRange(prev => ({ ...prev, start: e.target.value }))}
                  InputLabelProps={{ shrink: true }}
                />
                <TextField
                  type="date"
                  label="结束日期"
                  value={exportDateRange.end}
                  onChange={(e) => setExportDateRange(prev => ({ ...prev, end: e.target.value }))}
                  InputLabelProps={{ shrink: true }}
                />
              </Box>
            </Box>
            
            <Alert severity="info">
              将导出 {filteredLogs.length} 条日志记录
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialogOpen(false)}>取消</Button>
          <Button
            onClick={exportLogs}
            variant="contained"
            disabled={exporting}
            startIcon={exporting ? <CircularProgress size={16} /> : <ExportIcon />}
          >
            {exporting ? '导出中...' : '导出'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AuditLogs;
