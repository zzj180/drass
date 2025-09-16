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
  TablePagination,
  Chip,
  IconButton,
  Button,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Toolbar,
  Tooltip,
  CircularProgress,
  Alert,
  SelectChangeEvent,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { format } from 'date-fns';
import { zhCN, enUS } from 'date-fns/locale';
import axios from 'axios';
import { getApiUrl } from '../../config/config';

interface AccessLog {
  id: string;
  timestamp: string;
  action: 'upload' | 'update' | 'delete' | 'access' | 'search' | 'download' | 'reindex' | 'process';
  documentName: string;
  documentId: string;
  userId: string;
  userName: string;
  details?: string;
  status: 'success' | 'failed' | 'pending';
  metadata?: {
    fileSize?: number;
    processingTime?: number;
    queryText?: string;
    error?: string;
  };
}

const actionColors: Record<string, 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success' | 'default'> = {
  upload: 'success',
  update: 'info',
  delete: 'error',
  access: 'primary',
  search: 'secondary',
  download: 'default',
  reindex: 'warning',
  process: 'info',
};

export const AccessLogs: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [logs, setLogs] = useState<AccessLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [filterAction, setFilterAction] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [dateRange, setDateRange] = useState<string>('all');

  // Mock data for demonstration
  const mockLogs: AccessLog[] = [
    {
      id: '1',
      timestamp: new Date().toISOString(),
      action: 'upload',
      documentName: '合规政策文档.pdf',
      documentId: 'doc_001',
      userId: 'user_001',
      userName: '张三',
      details: '成功上传并索引文档',
      status: 'success',
      metadata: {
        fileSize: 2548576,
        processingTime: 3200,
      },
    },
    {
      id: '2',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      action: 'search',
      documentName: '多个文档',
      documentId: 'multiple',
      userId: 'user_002',
      userName: '李四',
      details: '搜索关键词：数据安全',
      status: 'success',
      metadata: {
        queryText: '数据安全',
      },
    },
    {
      id: '3',
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      action: 'update',
      documentName: '隐私保护条例.docx',
      documentId: 'doc_002',
      userId: 'user_001',
      userName: '张三',
      details: '更新文档内容并重新索引',
      status: 'success',
      metadata: {
        processingTime: 2100,
      },
    },
    {
      id: '4',
      timestamp: new Date(Date.now() - 10800000).toISOString(),
      action: 'access',
      documentName: 'ISO27001标准.pdf',
      documentId: 'doc_003',
      userId: 'user_003',
      userName: '王五',
      details: '查看文档详情',
      status: 'success',
    },
    {
      id: '5',
      timestamp: new Date(Date.now() - 14400000).toISOString(),
      action: 'download',
      documentName: '审计报告2024.xlsx',
      documentId: 'doc_004',
      userId: 'user_002',
      userName: '李四',
      details: '下载原始文档',
      status: 'success',
      metadata: {
        fileSize: 1024000,
      },
    },
    {
      id: '6',
      timestamp: new Date(Date.now() - 18000000).toISOString(),
      action: 'delete',
      documentName: '过期文档.txt',
      documentId: 'doc_005',
      userId: 'user_001',
      userName: '张三',
      details: '删除过期文档',
      status: 'success',
    },
    {
      id: '7',
      timestamp: new Date(Date.now() - 21600000).toISOString(),
      action: 'process',
      documentName: 'GDPR合规指南.pdf',
      documentId: 'doc_006',
      userId: 'system',
      userName: '系统',
      details: '文档处理失败：文件损坏',
      status: 'failed',
      metadata: {
        error: '文件损坏，无法解析',
      },
    },
    {
      id: '8',
      timestamp: new Date(Date.now() - 25200000).toISOString(),
      action: 'reindex',
      documentName: '全部文档',
      documentId: 'all',
      userId: 'admin',
      userName: '管理员',
      details: '重新索引知识库',
      status: 'pending',
      metadata: {
        processingTime: 45000,
      },
    },
  ];

  useEffect(() => {
    fetchLogs();
  }, [filterAction, dateRange]);

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);

    try {
      // In production, this would be an actual API call
      // const response = await axios.get(`${getApiUrl()}/api/v1/knowledge-base/access-logs`, {
      //   params: {
      //     action: filterAction !== 'all' ? filterAction : undefined,
      //     dateRange,
      //   },
      // });
      // setLogs(response.data);

      // Mock implementation
      setTimeout(() => {
        let filteredLogs = [...mockLogs];

        // Apply action filter
        if (filterAction !== 'all') {
          filteredLogs = filteredLogs.filter(log => log.action === filterAction);
        }

        // Apply date range filter
        const now = Date.now();
        switch (dateRange) {
          case 'today':
            filteredLogs = filteredLogs.filter(
              log => new Date(log.timestamp).getTime() > now - 86400000
            );
            break;
          case 'yesterday':
            filteredLogs = filteredLogs.filter(
              log => {
                const logTime = new Date(log.timestamp).getTime();
                return logTime > now - 172800000 && logTime < now - 86400000;
              }
            );
            break;
          case 'lastWeek':
            filteredLogs = filteredLogs.filter(
              log => new Date(log.timestamp).getTime() > now - 604800000
            );
            break;
          case 'lastMonth':
            filteredLogs = filteredLogs.filter(
              log => new Date(log.timestamp).getTime() > now - 2592000000
            );
            break;
        }

        setLogs(filteredLogs);
        setLoading(false);
      }, 500);
    } catch (err) {
      setError(t('errors.generic'));
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchLogs();
  };

  const handleExport = () => {
    // Export logs to CSV
    const csvContent = [
      ['时间', '操作', '文档', '用户', '详情', '状态'].join(','),
      ...logs.map(log => [
        format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss'),
        t(`accessLogs.actions.${log.action}`),
        log.documentName,
        log.userName,
        log.details || '',
        log.status,
      ].join(',')),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `access_logs_${format(new Date(), 'yyyyMMdd_HHmmss')}.csv`;
    link.click();
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleFilterChange = (event: SelectChangeEvent) => {
    setFilterAction(event.target.value);
    setPage(0);
  };

  const handleDateRangeChange = (event: SelectChangeEvent) => {
    setDateRange(event.target.value);
    setPage(0);
  };

  const handleClearFilters = () => {
    setFilterAction('all');
    setDateRange('all');
    setSearchQuery('');
    setPage(0);
  };

  const filteredLogs = logs.filter(log => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        log.documentName.toLowerCase().includes(query) ||
        log.userName.toLowerCase().includes(query) ||
        log.details?.toLowerCase().includes(query)
      );
    }
    return true;
  });

  const paginatedLogs = filteredLogs.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const locale = i18n.language === 'zh' ? zhCN : enUS;
    return format(date, 'yyyy-MM-dd HH:mm:ss', { locale });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'success';
      case 'failed':
        return 'error';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Paper elevation={2}>
        {/* Header */}
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h5" component="h2" gutterBottom>
            {t('accessLogs.title')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('accessLogs.subtitle')}
          </Typography>
        </Box>

        {/* Toolbar */}
        <Toolbar sx={{ pl: { sm: 2 }, pr: { xs: 1, sm: 1 } }}>
          <Box sx={{ flex: '1 1 100%', display: 'flex', gap: 2, alignItems: 'center' }}>
            {/* Search */}
            <TextField
              size="small"
              placeholder={t('common.search')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
              sx={{ minWidth: 200 }}
            />

            {/* Action Filter */}
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>{t('accessLogs.action')}</InputLabel>
              <Select
                value={filterAction}
                label={t('accessLogs.action')}
                onChange={handleFilterChange}
              >
                <MenuItem value="all">{t('accessLogs.filter.all')}</MenuItem>
                <MenuItem value="upload">{t('accessLogs.filter.upload')}</MenuItem>
                <MenuItem value="update">{t('accessLogs.filter.update')}</MenuItem>
                <MenuItem value="delete">{t('accessLogs.filter.delete')}</MenuItem>
                <MenuItem value="access">{t('accessLogs.filter.access')}</MenuItem>
                <MenuItem value="search">{t('accessLogs.filter.search')}</MenuItem>
                <MenuItem value="download">{t('accessLogs.filter.download')}</MenuItem>
              </Select>
            </FormControl>

            {/* Date Range Filter */}
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>{t('accessLogs.dateRange')}</InputLabel>
              <Select
                value={dateRange}
                label={t('accessLogs.dateRange')}
                onChange={handleDateRangeChange}
              >
                <MenuItem value="all">{t('accessLogs.filter.all')}</MenuItem>
                <MenuItem value="today">{t('accessLogs.today')}</MenuItem>
                <MenuItem value="yesterday">{t('accessLogs.yesterday')}</MenuItem>
                <MenuItem value="lastWeek">{t('accessLogs.lastWeek')}</MenuItem>
                <MenuItem value="lastMonth">{t('accessLogs.lastMonth')}</MenuItem>
              </Select>
            </FormControl>

            {/* Clear Filters */}
            {(filterAction !== 'all' || dateRange !== 'all' || searchQuery) && (
              <Tooltip title={t('accessLogs.clearFilters')}>
                <IconButton onClick={handleClearFilters} size="small">
                  <ClearIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>

          {/* Actions */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title={t('accessLogs.refreshLogs')}>
              <IconButton onClick={handleRefresh} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title={t('accessLogs.exportLogs')}>
              <IconButton onClick={handleExport} disabled={loading || logs.length === 0}>
                <DownloadIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Toolbar>

        {/* Table */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Box sx={{ p: 2 }}>
            <Alert severity="error">{error}</Alert>
          </Box>
        ) : filteredLogs.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography color="text.secondary">{t('accessLogs.noLogs')}</Typography>
          </Box>
        ) : (
          <>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>{t('accessLogs.time')}</TableCell>
                    <TableCell>{t('accessLogs.action')}</TableCell>
                    <TableCell>{t('accessLogs.document')}</TableCell>
                    <TableCell>{t('accessLogs.user')}</TableCell>
                    <TableCell>{t('accessLogs.details')}</TableCell>
                    <TableCell>{t('knowledgeBase.status')}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedLogs.map((log) => (
                    <TableRow key={log.id} hover>
                      <TableCell>
                        <Typography variant="body2">{formatTime(log.timestamp)}</Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={t(`accessLogs.actions.${log.action}`)}
                          size="small"
                          color={actionColors[log.action]}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                          {log.documentName}
                        </Typography>
                        {log.metadata?.fileSize && (
                          <Typography variant="caption" color="text.secondary">
                            {formatFileSize(log.metadata.fileSize)}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>{log.userName}</TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ maxWidth: 300 }}>
                          {log.details}
                        </Typography>
                        {log.metadata?.queryText && (
                          <Typography variant="caption" color="text.secondary">
                            "{log.metadata.queryText}"
                          </Typography>
                        )}
                        {log.metadata?.error && (
                          <Typography variant="caption" color="error">
                            {log.metadata.error}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={log.status}
                          size="small"
                          color={getStatusColor(log.status)}
                          variant="outlined"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {/* Pagination */}
            <TablePagination
              rowsPerPageOptions={[5, 10, 25, 50]}
              component="div"
              count={filteredLogs.length}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
              labelRowsPerPage={t('table.rowsPerPage')}
            />
          </>
        )}
      </Paper>
    </Box>
  );
};