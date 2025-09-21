import React from 'react';
import {
  Box,
  Pagination,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Chip,
  Tooltip,
  IconButton,
} from '@mui/material';
import {
  FirstPage as FirstPageIcon,
  LastPage as LastPageIcon,
  NavigateBefore as NavigateBeforeIcon,
  NavigateNext as NavigateNextIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

interface LogPaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
  onPageChange: (page: number) => void;
  onItemsPerPageChange: (itemsPerPage: number) => void;
  loading?: boolean;
}

const LogPagination: React.FC<LogPaginationProps> = ({
  currentPage,
  totalPages,
  totalItems,
  itemsPerPage,
  onPageChange,
  onItemsPerPageChange,
  loading = false,
}) => {
  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  const handlePageChange = (event: React.ChangeEvent<unknown>, page: number) => {
    onPageChange(page);
  };

  const handleFirstPage = () => {
    onPageChange(1);
  };

  const handleLastPage = () => {
    onPageChange(totalPages);
  };

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1);
    }
  };

  const getPageInfo = () => {
    if (totalItems === 0) {
      return '没有数据';
    }
    return `显示 ${startItem}-${endItem} 条，共 ${totalItems} 条记录`;
  };

  return (
    <Paper sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
      {/* 左侧信息 */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Typography variant="body2" color="text.secondary">
          {getPageInfo()}
        </Typography>
        
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>每页显示</InputLabel>
          <Select
            value={itemsPerPage}
            onChange={(e) => onItemsPerPageChange(Number(e.target.value))}
            label="每页显示"
            disabled={loading}
          >
            <MenuItem value={10}>10 条</MenuItem>
            <MenuItem value={25}>25 条</MenuItem>
            <MenuItem value={50}>50 条</MenuItem>
            <MenuItem value={100}>100 条</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* 中间分页控件 */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {/* 快速导航按钮 */}
        <Tooltip title="第一页">
          <IconButton
            onClick={handleFirstPage}
            disabled={currentPage === 1 || loading}
            size="small"
          >
            <FirstPageIcon />
          </IconButton>
        </Tooltip>
        
        <Tooltip title="上一页">
          <IconButton
            onClick={handlePreviousPage}
            disabled={currentPage === 1 || loading}
            size="small"
          >
            <NavigateBeforeIcon />
          </IconButton>
        </Tooltip>

        {/* 分页组件 */}
        <Pagination
          count={totalPages}
          page={currentPage}
          onChange={handlePageChange}
          color="primary"
          size="small"
          disabled={loading}
          showFirstButton={false}
          showLastButton={false}
          siblingCount={1}
          boundaryCount={1}
        />

        <Tooltip title="下一页">
          <IconButton
            onClick={handleNextPage}
            disabled={currentPage === totalPages || loading}
            size="small"
          >
            <NavigateNextIcon />
          </IconButton>
        </Tooltip>
        
        <Tooltip title="最后一页">
          <IconButton
            onClick={handleLastPage}
            disabled={currentPage === totalPages || loading}
            size="small"
          >
            <LastPageIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* 右侧信息 */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Chip
          label={`第 ${currentPage} 页，共 ${totalPages} 页`}
          size="small"
          color="primary"
          variant="outlined"
        />
        
        {loading && (
          <Tooltip title="正在加载数据...">
            <InfoIcon color="action" />
          </Tooltip>
        )}
      </Box>
    </Paper>
  );
};

export default LogPagination;
