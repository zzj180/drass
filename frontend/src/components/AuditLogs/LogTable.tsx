import React, { useMemo, useCallback } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Chip,
  IconButton,
  Tooltip,
  Avatar,
  Box,
  Typography,
  Skeleton,
  Paper,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  Security as SecurityIcon,
  Person as PersonIcon,
  Description as DocumentIcon,
  Chat as ChatIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// 审计日志数据类型
export interface AuditLog {
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

// 排序类型
export type SortField = 'timestamp' | 'userName' | 'action' | 'resource' | 'status' | 'severity';
export type SortDirection = 'asc' | 'desc';

export interface SortConfig {
  field: SortField;
  direction: SortDirection;
}

// 样式化组件
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

interface LogTableProps {
  logs: AuditLog[];
  loading?: boolean;
  sortConfig: SortConfig;
  onSort: (field: SortField) => void;
  onViewDetail: (log: AuditLog) => void;
  page: number;
  itemsPerPage: number;
}

const LogTable: React.FC<LogTableProps> = ({
  logs,
  loading = false,
  sortConfig,
  onSort,
  onViewDetail,
  page,
  itemsPerPage,
}) => {
  // 获取资源类型图标
  const getResourceIcon = useCallback((type: string) => {
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
  }, []);

  // 排序后的日志数据
  const sortedLogs = useMemo(() => {
    if (!logs.length) return [];
    
    return [...logs].sort((a, b) => {
      let aValue: any = a[sortConfig.field];
      let bValue: any = b[sortConfig.field];
      
      // 特殊处理时间字段
      if (sortConfig.field === 'timestamp') {
        aValue = new Date(aValue).getTime();
        bValue = new Date(bValue).getTime();
      }
      
      // 处理字符串比较
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }
      
      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [logs, sortConfig]);

  // 分页数据
  const paginatedLogs = useMemo(() => {
    const startIndex = (page - 1) * itemsPerPage;
    return sortedLogs.slice(startIndex, startIndex + itemsPerPage);
  }, [sortedLogs, page, itemsPerPage]);

  // 渲染加载骨架
  const renderSkeleton = () => (
    <>
      {Array.from({ length: itemsPerPage }).map((_, index) => (
        <TableRow key={index}>
          <TableCell><Skeleton /></TableCell>
          <TableCell><Skeleton /></TableCell>
          <TableCell><Skeleton /></TableCell>
          <TableCell><Skeleton /></TableCell>
          <TableCell><Skeleton /></TableCell>
          <TableCell><Skeleton /></TableCell>
          <TableCell><Skeleton /></TableCell>
          <TableCell><Skeleton /></TableCell>
          <TableCell><Skeleton /></TableCell>
        </TableRow>
      ))}
    </>
  );

  return (
    <StyledTableContainer component={Paper}>
      <Table stickyHeader>
        <TableHead>
          <TableRow sx={{ backgroundColor: 'primary.main' }}>
            <TableCell sx={{ color: 'white', fontWeight: 600 }}>
              <TableSortLabel
                active={sortConfig.field === 'timestamp'}
                direction={sortConfig.field === 'timestamp' ? sortConfig.direction : 'asc'}
                onClick={() => onSort('timestamp')}
                sx={{ color: 'white' }}
              >
                时间
              </TableSortLabel>
            </TableCell>
            <TableCell sx={{ color: 'white', fontWeight: 600 }}>
              <TableSortLabel
                active={sortConfig.field === 'userName'}
                direction={sortConfig.field === 'userName' ? sortConfig.direction : 'asc'}
                onClick={() => onSort('userName')}
                sx={{ color: 'white' }}
              >
                用户
              </TableSortLabel>
            </TableCell>
            <TableCell sx={{ color: 'white', fontWeight: 600 }}>
              <TableSortLabel
                active={sortConfig.field === 'action'}
                direction={sortConfig.field === 'action' ? sortConfig.direction : 'asc'}
                onClick={() => onSort('action')}
                sx={{ color: 'white' }}
              >
                操作
              </TableSortLabel>
            </TableCell>
            <TableCell sx={{ color: 'white', fontWeight: 600 }}>
              <TableSortLabel
                active={sortConfig.field === 'resource'}
                direction={sortConfig.field === 'resource' ? sortConfig.direction : 'asc'}
                onClick={() => onSort('resource')}
                sx={{ color: 'white' }}
              >
                资源
              </TableSortLabel>
            </TableCell>
            <TableCell sx={{ color: 'white', fontWeight: 600 }}>类型</TableCell>
            <TableCell sx={{ color: 'white', fontWeight: 600 }}>
              <TableSortLabel
                active={sortConfig.field === 'status'}
                direction={sortConfig.field === 'status' ? sortConfig.direction : 'asc'}
                onClick={() => onSort('status')}
                sx={{ color: 'white' }}
              >
                状态
              </TableSortLabel>
            </TableCell>
            <TableCell sx={{ color: 'white', fontWeight: 600 }}>
              <TableSortLabel
                active={sortConfig.field === 'severity'}
                direction={sortConfig.field === 'severity' ? sortConfig.direction : 'asc'}
                onClick={() => onSort('severity')}
                sx={{ color: 'white' }}
              >
                严重程度
              </TableSortLabel>
            </TableCell>
            <TableCell sx={{ color: 'white', fontWeight: 600 }}>IP地址</TableCell>
            <TableCell sx={{ color: 'white', fontWeight: 600 }}>操作</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {loading ? (
            renderSkeleton()
          ) : paginatedLogs.length > 0 ? (
            paginatedLogs.map((log) => (
              <TableRow key={log.id} hover>
                <TableCell>
                  <Typography variant="body2">
                    {new Date(log.timestamp).toLocaleString()}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Avatar sx={{ width: 24, height: 24, fontSize: '0.75rem' }}>
                      {log.userName.charAt(0)}
                    </Avatar>
                    <Typography variant="body2">{log.userName}</Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">{log.action}</Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {log.resource}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {getResourceIcon(log.resourceType)}
                    <Typography variant="body2">{log.resourceType}</Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <StatusChip label={log.status} status={log.status} size="small" />
                </TableCell>
                <TableCell>
                  <SeverityChip label={log.severity} severity={log.severity} size="small" />
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                    {log.ipAddress}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Tooltip title="查看详情">
                    <IconButton size="small" onClick={() => onViewDetail(log)}>
                      <ViewIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={9} sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body1" color="text.secondary">
                  没有找到匹配的审计日志记录
                </Typography>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </StyledTableContainer>
  );
};

export default LogTable;
