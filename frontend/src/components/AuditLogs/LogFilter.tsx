import React from 'react';
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Tooltip,
  Paper,
  Typography,
  Button,
  Collapse,
  Grid,
  Autocomplete,
  DatePicker,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { zhCN } from 'date-fns/locale';

// 过滤器类型定义
export interface LogFilter {
  searchTerm: string;
  resourceType: string;
  status: string;
  severity: string;
  userId: string;
  dateRange: {
    start: Date | null;
    end: Date | null;
  };
  ipAddress: string;
  action: string;
}

interface LogFilterProps {
  filter: LogFilter;
  onFilterChange: (filter: LogFilter) => void;
  onClearFilter: () => void;
  availableUsers: string[];
  availableActions: string[];
  availableIpAddresses: string[];
}

const LogFilter: React.FC<LogFilterProps> = ({
  filter,
  onFilterChange,
  onClearFilter,
  availableUsers,
  availableActions,
  availableIpAddresses,
}) => {
  const [expanded, setExpanded] = React.useState(false);

  const handleFilterChange = (field: keyof LogFilter, value: any) => {
    onFilterChange({
      ...filter,
      [field]: value,
    });
  };

  const handleDateRangeChange = (field: 'start' | 'end', value: Date | null) => {
    onFilterChange({
      ...filter,
      dateRange: {
        ...filter.dateRange,
        [field]: value,
      },
    });
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (filter.searchTerm) count++;
    if (filter.resourceType !== 'all') count++;
    if (filter.status !== 'all') count++;
    if (filter.severity !== 'all') count++;
    if (filter.userId !== 'all') count++;
    if (filter.dateRange.start || filter.dateRange.end) count++;
    if (filter.ipAddress) count++;
    if (filter.action !== 'all') count++;
    return count;
  };

  const activeFilterCount = getActiveFilterCount();

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={zhCN}>
      <Paper sx={{ p: 2, mb: 2 }}>
        {/* 基础过滤器 */}
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap', mb: 2 }}>
          <TextField
            placeholder="搜索用户、操作、资源或IP地址..."
            value={filter.searchTerm}
            onChange={(e) => handleFilterChange('searchTerm', e.target.value)}
            InputProps={{
              startAdornment: <SearchIcon />,
            }}
            sx={{ minWidth: 300 }}
          />
          
          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel>资源类型</InputLabel>
            <Select
              value={filter.resourceType}
              onChange={(e) => handleFilterChange('resourceType', e.target.value)}
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
              value={filter.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              label="状态"
            >
              <MenuItem value="all">全部</MenuItem>
              <MenuItem value="success">成功</MenuItem>
              <MenuItem value="failed">失败</MenuItem>
              <MenuItem value="warning">警告</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel>严重程度</InputLabel>
            <Select
              value={filter.severity}
              onChange={(e) => handleFilterChange('severity', e.target.value)}
              label="严重程度"
            >
              <MenuItem value="all">全部</MenuItem>
              <MenuItem value="low">低</MenuItem>
              <MenuItem value="medium">中</MenuItem>
              <MenuItem value="high">高</MenuItem>
              <MenuItem value="critical">严重</MenuItem>
            </Select>
          </FormControl>
          
          <Tooltip title="高级过滤器">
            <IconButton
              onClick={() => setExpanded(!expanded)}
              color={activeFilterCount > 0 ? 'primary' : 'default'}
            >
              <FilterIcon />
              {activeFilterCount > 0 && (
                <Chip
                  label={activeFilterCount}
                  size="small"
                  color="primary"
                  sx={{ ml: 1, minWidth: 20, height: 20 }}
                />
              )}
            </IconButton>
          </Tooltip>
          
          {activeFilterCount > 0 && (
            <Tooltip title="清除所有过滤器">
              <IconButton onClick={onClearFilter} color="error">
                <ClearIcon />
              </IconButton>
            </Tooltip>
          )}
        </Box>

        {/* 高级过滤器 */}
        <Collapse in={expanded}>
          <Box sx={{ borderTop: 1, borderColor: 'divider', pt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Autocomplete
                  options={availableUsers}
                  value={filter.userId === 'all' ? null : filter.userId}
                  onChange={(_, value) => handleFilterChange('userId', value || 'all')}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="用户"
                      placeholder="选择用户"
                    />
                  )}
                />
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Autocomplete
                  options={availableActions}
                  value={filter.action === 'all' ? null : filter.action}
                  onChange={(_, value) => handleFilterChange('action', value || 'all')}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="操作"
                      placeholder="选择操作"
                    />
                  )}
                />
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Autocomplete
                  options={availableIpAddresses}
                  value={filter.ipAddress || ''}
                  onChange={(_, value) => handleFilterChange('ipAddress', value || '')}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="IP地址"
                      placeholder="输入IP地址"
                    />
                  )}
                />
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                  <DatePicker
                    label="开始日期"
                    value={filter.dateRange.start}
                    onChange={(value) => handleDateRangeChange('start', value)}
                    slotProps={{
                      textField: {
                        size: 'small',
                        fullWidth: true,
                      },
                    }}
                  />
                </Box>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <DatePicker
                  label="结束日期"
                  value={filter.dateRange.end}
                  onChange={(value) => handleDateRangeChange('end', value)}
                  slotProps={{
                    textField: {
                      size: 'small',
                      fullWidth: true,
                    },
                  }}
                />
              </Grid>
            </Grid>
          </Box>
        </Collapse>

        {/* 活动过滤器标签 */}
        {activeFilterCount > 0 && (
          <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Typography variant="body2" color="text.secondary" sx={{ alignSelf: 'center' }}>
              活动过滤器:
            </Typography>
            {filter.searchTerm && (
              <Chip
                label={`搜索: ${filter.searchTerm}`}
                onDelete={() => handleFilterChange('searchTerm', '')}
                size="small"
              />
            )}
            {filter.resourceType !== 'all' && (
              <Chip
                label={`类型: ${filter.resourceType}`}
                onDelete={() => handleFilterChange('resourceType', 'all')}
                size="small"
              />
            )}
            {filter.status !== 'all' && (
              <Chip
                label={`状态: ${filter.status}`}
                onDelete={() => handleFilterChange('status', 'all')}
                size="small"
              />
            )}
            {filter.severity !== 'all' && (
              <Chip
                label={`严重程度: ${filter.severity}`}
                onDelete={() => handleFilterChange('severity', 'all')}
                size="small"
              />
            )}
            {filter.userId !== 'all' && (
              <Chip
                label={`用户: ${filter.userId}`}
                onDelete={() => handleFilterChange('userId', 'all')}
                size="small"
              />
            )}
            {filter.action !== 'all' && (
              <Chip
                label={`操作: ${filter.action}`}
                onDelete={() => handleFilterChange('action', 'all')}
                size="small"
              />
            )}
            {filter.ipAddress && (
              <Chip
                label={`IP: ${filter.ipAddress}`}
                onDelete={() => handleFilterChange('ipAddress', '')}
                size="small"
              />
            )}
            {(filter.dateRange.start || filter.dateRange.end) && (
              <Chip
                label={`日期: ${filter.dateRange.start?.toLocaleDateString() || '开始'} - ${filter.dateRange.end?.toLocaleDateString() || '结束'}`}
                onDelete={() => handleFilterChange('dateRange', { start: null, end: null })}
                size="small"
              />
            )}
          </Box>
        )}
      </Paper>
    </LocalizationProvider>
  );
};

export default LogFilter;
