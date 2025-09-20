import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Tabs,
  Tab,
  Alert,
  IconButton,
  Tooltip,
  Collapse
} from '@mui/material';
import {
  Assignment as TaskIcon,
  CheckCircle as CompletedIcon,
  RadioButtonUnchecked as PendingIcon,
  PlayCircle as InProgressIcon,
  Timeline as TimelineIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Notes as NotesIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';

// 类型定义
interface TaskStatus {
  name: string;
  status: 'pending' | 'in_progress' | 'completed';
  created_at: string;
  updated_at: string;
  progress: number;
  notes?: Array<{
    timestamp: string;
    note: string;
  }>;
}

interface TaskSummary {
  total_tasks: number;
  completed: number;
  in_progress: number;
  pending: number;
  completion_rate: number;
}

interface MilestoneProgress {
  name: string;
  completed_tasks: number;
  total_tasks: number;
  completion_rate: number;
}

interface TaskData {
  tasks: Record<string, TaskStatus>;
  summary: TaskSummary;
  milestones: Record<string, MilestoneProgress>;
  updated_at: string;
}

interface TaskLog {
  timestamp: string;
  task_id: string;
  task_name: string;
  old_status: string;
  new_status: string;
  note?: string;
}

// 状态颜色配置
const statusColors = {
  pending: 'default' as const,
  in_progress: 'warning' as const,
  completed: 'success' as const,
};

const statusIcons = {
  pending: PendingIcon,
  in_progress: InProgressIcon,
  completed: CompletedIcon,
};

// 任务卡片组件
const TaskCard: React.FC<{
  taskId: string;
  task: TaskStatus;
  onUpdate: (taskId: string, status: string, note?: string) => void;
}> = ({ taskId, task, onUpdate }) => {
  const [expanded, setExpanded] = useState(false);
  const [updateDialogOpen, setUpdateDialogOpen] = useState(false);
  const [newStatus, setNewStatus] = useState(task.status);
  const [note, setNote] = useState('');

  const StatusIcon = statusIcons[task.status];

  const handleUpdate = () => {
    onUpdate(taskId, newStatus, note);
    setUpdateDialogOpen(false);
    setNote('');
  };

  return (
    <>
      <Card sx={{ mb: 1, border: task.status === 'completed' ? '2px solid #4caf50' : 'none' }}>
        <CardContent sx={{ pb: '16px !important' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', flex: 1 }}>
              <StatusIcon 
                color={statusColors[task.status]} 
                sx={{ mr: 1 }}
              />
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                {task.name}
              </Typography>
            </Box>
            <Chip
              label={task.status === 'pending' ? '待开始' : 
                     task.status === 'in_progress' ? '进行中' : '已完成'}
              color={statusColors[task.status]}
              size="small"
              sx={{ ml: 1 }}
            />
          </Box>

          <Box sx={{ mb: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="caption" color="text.secondary">
                进度
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {task.progress}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={task.progress}
              color={task.status === 'completed' ? 'success' : 'primary'}
              sx={{ height: 6, borderRadius: 3 }}
            />
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="caption" color="text.secondary">
              更新时间: {format(new Date(task.updated_at), 'MM-dd HH:mm', { locale: zhCN })}
            </Typography>
            <Box>
              {task.notes && task.notes.length > 0 && (
                <Tooltip title="查看备注">
                  <IconButton
                    size="small"
                    onClick={() => setExpanded(!expanded)}
                  >
                    <NotesIcon fontSize="small" />
                    {expanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
                  </IconButton>
                </Tooltip>
              )}
              <Button
                size="small"
                variant="outlined"
                onClick={() => setUpdateDialogOpen(true)}
                sx={{ ml: 1 }}
              >
                更新
              </Button>
            </Box>
          </Box>

          <Collapse in={expanded}>
            <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid #e0e0e0' }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                备注记录:
              </Typography>
              {task.notes?.map((noteItem, index) => (
                <Box key={index} sx={{ mt: 1, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    {format(new Date(noteItem.timestamp), 'MM-dd HH:mm')}
                  </Typography>
                  <Typography variant="body2" sx={{ mt: 0.5 }}>
                    {noteItem.note}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Collapse>
        </CardContent>
      </Card>

      {/* 更新对话框 */}
      <Dialog open={updateDialogOpen} onClose={() => setUpdateDialogOpen(false)}>
        <DialogTitle>更新任务状态</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            任务: {task.name}
          </Typography>
          <TextField
            select
            fullWidth
            label="状态"
            value={newStatus}
            onChange={(e) => setNewStatus(e.target.value as any)}
            sx={{ mb: 2 }}
          >
            <MenuItem value="pending">待开始</MenuItem>
            <MenuItem value="in_progress">进行中</MenuItem>
            <MenuItem value="completed">已完成</MenuItem>
          </TextField>
          <TextField
            fullWidth
            label="备注"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            multiline
            rows={3}
            placeholder="添加备注信息（可选）"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUpdateDialogOpen(false)}>取消</Button>
          <Button onClick={handleUpdate} variant="contained">更新</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

// 进度总览卡片
const ProgressOverviewCard: React.FC<{ summary: TaskSummary }> = ({ summary }) => {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          📊 项目进度总览
        </Typography>
        
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2">整体完成率</Typography>
            <Typography variant="body2" fontWeight="bold">
              {summary.completion_rate}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={summary.completion_rate}
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={3}>
            <Box textAlign="center">
              <Typography variant="h4" color="text.secondary">
                {summary.total_tasks}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                总任务
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={3}>
            <Box textAlign="center">
              <Typography variant="h4" color="success.main">
                {summary.completed}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                已完成
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={3}>
            <Box textAlign="center">
              <Typography variant="h4" color="warning.main">
                {summary.in_progress}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                进行中
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={3}>
            <Box textAlign="center">
              <Typography variant="h4" color="text.secondary">
                {summary.pending}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                待开始
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

// 里程碑进度卡片
const MilestoneCard: React.FC<{ milestones: Record<string, MilestoneProgress> }> = ({ milestones }) => {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          🎯 里程碑进度
        </Typography>
        
        {Object.entries(milestones).map(([stageId, milestone]) => (
          <Box key={stageId} sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">
                {milestone.name}
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                {milestone.completion_rate}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={milestone.completion_rate}
              sx={{ height: 6, borderRadius: 3, mb: 0.5 }}
            />
            <Typography variant="caption" color="text.secondary">
              {milestone.completed_tasks}/{milestone.total_tasks} 任务完成
            </Typography>
          </Box>
        ))}
      </CardContent>
    </Card>
  );
};

// 主组件
export const TaskProgressDashboard: React.FC = () => {
  const { t } = useTranslation();
  const [taskData, setTaskData] = useState<TaskData | null>(null);
  const [taskLogs, setTaskLogs] = useState<TaskLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const wsRef = useRef<WebSocket | null>(null);

  // WebSocket连接
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        wsRef.current = new WebSocket('ws://localhost:8899/ws/task-status');
        
        wsRef.current.onopen = () => {
          console.log('任务状态WebSocket连接成功');
          setError(null);
        };
        
        wsRef.current.onmessage = (event) => {
          const message = JSON.parse(event.data);
          
          if (message.type === 'initial_status' || message.type === 'status_updated') {
            setTaskData(message.data);
            setLoading(false);
          } else if (message.type === 'task_updated') {
            // 单个任务更新
            setTaskData(prev => {
              if (!prev) return prev;
              return {
                ...prev,
                tasks: {
                  ...prev.tasks,
                  [message.data.task_id]: message.data.task
                }
              };
            });
          }
        };
        
        wsRef.current.onerror = (error) => {
          console.error('WebSocket错误:', error);
          setError('连接任务状态服务器失败');
        };
        
        wsRef.current.onclose = () => {
          console.log('WebSocket连接关闭，3秒后重连');
          setTimeout(connectWebSocket, 3000);
        };
      } catch (err) {
        setError('无法连接到任务状态服务器');
        setLoading(false);
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // 加载任务日志
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await fetch('http://localhost:8899/api/task-logs');
        const data = await response.json();
        if (data.status === 'success') {
          setTaskLogs(data.data.logs);
        }
      } catch (err) {
        console.error('加载任务日志失败:', err);
      }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 30000); // 每30秒刷新一次日志
    return () => clearInterval(interval);
  }, []);

  // 手动更新任务状态
  const handleUpdateTask = async (taskId: string, status: string, note?: string) => {
    try {
      const response = await fetch(`http://localhost:8899/api/task-status/${taskId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status, note }),
      });

      if (!response.ok) {
        throw new Error('更新失败');
      }

      // WebSocket会自动推送更新，这里不需要手动更新状态
    } catch (err) {
      setError('更新任务状态失败');
      console.error('更新任务状态失败:', err);
    }
  };

  // 刷新数据
  const handleRefresh = async () => {
    try {
      const response = await fetch('http://localhost:8899/api/task-status');
      const data = await response.json();
      if (data.status === 'success') {
        setTaskData(data.data);
      }
    } catch (err) {
      setError('刷新数据失败');
    }
  };

  // 过滤任务
  const filteredTasks = taskData ? Object.entries(taskData.tasks).filter(([_, task]) => {
    if (filterStatus === 'all') return true;
    return task.status === filterStatus;
  }) : [];

  if (loading) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography>加载任务状态中...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" action={
          <Button color="inherit" size="small" onClick={handleRefresh}>
            重试
          </Button>
        }>
          {error}
        </Alert>
      </Box>
    );
  }

  if (!taskData) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography>暂无任务数据</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          📋 任务进度跟踪
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
        >
          刷新
        </Button>
      </Box>

      {/* 进度总览 */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={8}>
          <ProgressOverviewCard summary={taskData.summary} />
        </Grid>
        <Grid item xs={12} md={4}>
          <MilestoneCard milestones={taskData.milestones} />
        </Grid>
      </Grid>

      {/* 标签页 */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="任务列表" />
          <Tab label="变更日志" />
        </Tabs>
      </Paper>

      {/* 任务列表标签页 */}
      {tabValue === 0 && (
        <Box>
          {/* 过滤器 */}
          <Box sx={{ mb: 2 }}>
            <TextField
              select
              size="small"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              sx={{ minWidth: 120 }}
            >
              <MenuItem value="all">全部任务</MenuItem>
              <MenuItem value="pending">待开始</MenuItem>
              <MenuItem value="in_progress">进行中</MenuItem>
              <MenuItem value="completed">已完成</MenuItem>
            </TextField>
          </Box>

          {/* 任务列表 */}
          <Grid container spacing={2}>
            {filteredTasks.map(([taskId, task]) => (
              <Grid item xs={12} md={6} lg={4} key={taskId}>
                <TaskCard
                  taskId={taskId}
                  task={task}
                  onUpdate={handleUpdateTask}
                />
              </Grid>
            ))}
          </Grid>

          {filteredTasks.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography color="text.secondary">
                没有符合条件的任务
              </Typography>
            </Box>
          )}
        </Box>
      )}

      {/* 变更日志标签页 */}
      {tabValue === 1 && (
        <Paper>
          <List>
            {taskLogs.map((log, index) => (
              <ListItem key={index} divider>
                <ListItemIcon>
                  <TimelineIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2">
                        {log.task_name}
                      </Typography>
                      <Chip
                        label={`${log.old_status} → ${log.new_status}`}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        {format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss', { locale: zhCN })}
                      </Typography>
                      {log.note && (
                        <Typography variant="body2" sx={{ mt: 0.5 }}>
                          备注: {log.note}
                        </Typography>
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
          
          {taskLogs.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography color="text.secondary">
                暂无变更日志
              </Typography>
            </Box>
          )}
        </Paper>
      )}
    </Box>
  );
};

