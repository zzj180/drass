import React, { useState, useEffect } from 'react';
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
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
  Security as SecurityIcon,
  Person as PersonIcon,
  Description as DocumentIcon,
  Chat as ChatIcon,
  Settings as SettingsIcon,
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

const StatusChip = styled(Chip)<{ status: string }>(({ theme, status }) => ({
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

const SeverityChip = styled(Chip)<{ severity: string }>(({ theme, severity }) => ({
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

const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

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

  useEffect(() => {
    // 模拟加载数据
    const loadLogs = async () => {
      setLoading(true);
      // 模拟API调用延迟
      await new Promise(resolve => setTimeout(resolve, 1000));
      setLogs(mockLogs);
      setTotalPages(Math.ceil(mockLogs.length / 10));
      setLoading(false);
    };

    loadLogs();
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
      {/* 页面标题 */}
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 600, color: 'primary.main' }}>
        审计日志
      </Typography>

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
          
          <IconButton onClick={() => window.location.reload()}>
            <RefreshIcon />
          </IconButton>
          
          <IconButton>
            <DownloadIcon />
          </IconButton>
        </Box>
      </Paper>

      {/* 日志表格 */}
      <StyledTableContainer component={Paper}>
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
                    <IconButton size="small">
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
    </Box>
  );
};

export default AuditLogs;
