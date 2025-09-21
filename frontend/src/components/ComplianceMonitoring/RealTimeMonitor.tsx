import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Alert,
  AlertTitle,
  LinearProgress,
  IconButton,
  Tooltip,
  Badge,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Paper,
  Switch,
  FormControlLabel,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress
} from '@mui/material';
import {
  Warning,
  Error,
  Info,
  CheckCircle,
  Timeline,
  Refresh,
  Settings,
  Notifications,
  Security,
  Assessment,
  TrendingUp,
  TrendingDown,
  TrendingFlat
} from '@mui/icons-material';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';

// Types
interface MonitoringMetric {
  value: number;
  unit: string;
  status: 'normal' | 'warning' | 'error';
  threshold?: number;
  timestamp: string;
}

interface MonitoringAlert {
  id: string;
  title: string;
  description: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  status: 'active' | 'acknowledged' | 'resolved' | 'suppressed';
  metric_type: string;
  threshold_value: number;
  actual_value: number;
  timestamp: string;
  acknowledged_by?: string;
  acknowledged_at?: string;
  resolved_at?: string;
  metadata?: any;
}

interface RiskIncident {
  id: string;
  incident_type: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  description: string;
  affected_resources: string[];
  detected_at: string;
  resolved_at?: string;
  mitigation_actions: string[];
  metadata?: any;
}

interface MonitoringData {
  timestamp: string;
  compliance_score: number;
  overall_status: 'healthy' | 'warning' | 'critical';
  metrics: Record<string, MonitoringMetric>;
  alerts: MonitoringAlert[];
  risk_incidents: RiskIncident[];
  metadata?: any;
}

interface RealTimeMonitorProps {
  userId?: string;
}

const RealTimeMonitor: React.FC<RealTimeMonitorProps> = ({ userId = 'default' }) => {
  const [monitoringData, setMonitoringData] = useState<MonitoringData | null>(null);
  const [alerts, setAlerts] = useState<MonitoringAlert[]>([]);
  const [riskIncidents, setRiskIncidents] = useState<RiskIncident[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [realtimeEnabled, setRealtimeEnabled] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAlertsDialog, setShowAlertsDialog] = useState(false);
  const [showIncidentsDialog, setShowIncidentsDialog] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // WebSocket connection management
  const connectWebSocket = useCallback(() => {
    if (!realtimeEnabled) return;

    try {
      const wsUrl = `ws://localhost:8888/api/v1/monitoring/ws/${userId}`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('Monitoring WebSocket connected');
        setIsConnected(true);
        setError(null);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      wsRef.current.onclose = () => {
        console.log('Monitoring WebSocket disconnected');
        setIsConnected(false);
        
        // Attempt to reconnect after 5 seconds
        if (realtimeEnabled) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, 5000);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('Monitoring WebSocket error:', error);
        setError('WebSocket连接错误');
      };

    } catch (err) {
      console.error('Error connecting to monitoring WebSocket:', err);
      setError('无法连接到监控服务');
    }
  }, [userId, realtimeEnabled]);

  const disconnectWebSocket = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'monitoring_update':
        setMonitoringData(data);
        setAlerts(data.alerts || []);
        setRiskIncidents(data.risk_incidents || []);
        break;
      case 'alert':
        setAlerts(prev => [data.alert, ...prev.filter(a => a.id !== data.alert.id)]);
        break;
      case 'risk_incident':
        setRiskIncidents(prev => [data.incident, ...prev.filter(i => i.id !== data.incident.id)]);
        break;
      case 'connection_status':
        console.log('Connection status:', data.status);
        break;
      case 'ping':
        // Respond to ping with pong
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: 'pong' }));
        }
        break;
      default:
        console.log('Unknown message type:', data.type);
    }
  };

  // Load initial data
  const loadInitialData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/v1/monitoring/status');
      if (!response.ok) throw new Error('Failed to load monitoring status');
      
      const status = await response.json();
      setIsMonitoring(status.is_monitoring || false);
      
      // Load current metrics
      const metricsResponse = await fetch('/api/v1/monitoring/metrics');
      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json();
        setMonitoringData(metricsData);
      }
      
      // Load alerts
      const alertsResponse = await fetch('/api/v1/monitoring/alerts');
      if (alertsResponse.ok) {
        const alertsData = await alertsResponse.json();
        setAlerts(alertsData.alerts || []);
      }
      
      // Load risk incidents
      const incidentsResponse = await fetch('/api/v1/monitoring/risk-incidents');
      if (incidentsResponse.ok) {
        const incidentsData = await incidentsResponse.json();
        setRiskIncidents(incidentsData.incidents || []);
      }
      
    } catch (err) {
      console.error('Error loading initial data:', err);
      setError('加载监控数据失败');
    } finally {
      setLoading(false);
    }
  }, []);

  // Start/stop monitoring
  const toggleMonitoring = async () => {
    try {
      const endpoint = isMonitoring ? '/api/v1/monitoring/stop' : '/api/v1/monitoring/start';
      const response = await fetch(endpoint, { method: 'POST' });
      
      if (response.ok) {
        setIsMonitoring(!isMonitoring);
      } else {
        throw new Error('Failed to toggle monitoring');
      }
    } catch (err) {
      console.error('Error toggling monitoring:', err);
      setError('切换监控状态失败');
    }
  };

  // Acknowledge alert
  const acknowledgeAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/v1/monitoring/alerts/${alertId}/acknowledge`, {
        method: 'POST'
      });
      
      if (response.ok) {
        setAlerts(prev => prev.map(alert => 
          alert.id === alertId 
            ? { ...alert, status: 'acknowledged' as const, acknowledged_at: new Date().toISOString() }
            : alert
        ));
      }
    } catch (err) {
      console.error('Error acknowledging alert:', err);
    }
  };

  // Resolve alert
  const resolveAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/v1/monitoring/alerts/${alertId}/resolve`, {
        method: 'POST'
      });
      
      if (response.ok) {
        setAlerts(prev => prev.map(alert => 
          alert.id === alertId 
            ? { ...alert, status: 'resolved' as const, resolved_at: new Date().toISOString() }
            : alert
        ));
      }
    } catch (err) {
      console.error('Error resolving alert:', err);
    }
  };

  // Effects
  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

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

  // Helper functions
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      case 'critical': return 'error';
      default: return 'default';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'error': return 'error';
      case 'warning': return 'warning';
      case 'info': return 'info';
      default: return 'default';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <Error />;
      case 'error': return <Error />;
      case 'warning': return <Warning />;
      case 'info': return <Info />;
      default: return <Info />;
    }
  };

  const getTrendIcon = (current: number, threshold: number) => {
    if (current > threshold) return <TrendingUp color="error" />;
    if (current < threshold * 0.8) return <TrendingDown color="success" />;
    return <TrendingFlat color="warning" />;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>加载监控数据中...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          实时合规监控
        </Typography>
        <Box display="flex" alignItems="center" gap={2}>
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
          <Chip
            icon={isConnected ? <CheckCircle /> : <Error />}
            label={isConnected ? '已连接' : '未连接'}
            color={isConnected ? 'success' : 'error'}
            variant="outlined"
          />
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadInitialData}
            disabled={loading}
          >
            刷新
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <AlertTitle>错误</AlertTitle>
          {error}
        </Alert>
      )}

      {/* Overall Status */}
      {monitoringData && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">系统状态</Typography>
              <Chip
                label={monitoringData.overall_status}
                color={getStatusColor(monitoringData.overall_status) as any}
                size="large"
              />
            </Box>
            <Box display="flex" alignItems="center" gap={2}>
              <Typography variant="body2" color="text.secondary">
                合规评分:
              </Typography>
              <LinearProgress
                variant="determinate"
                value={monitoringData.compliance_score}
                sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                color={monitoringData.compliance_score >= 80 ? 'success' : 
                       monitoringData.compliance_score >= 60 ? 'warning' : 'error'}
              />
              <Typography variant="h6" fontWeight="bold">
                {monitoringData.compliance_score.toFixed(1)}%
              </Typography>
            </Box>
            <Typography variant="caption" color="text.secondary" display="block" mt={1}>
              最后更新: {format(new Date(monitoringData.timestamp), 'yyyy-MM-dd HH:mm:ss', { locale: zhCN })}
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Metrics Grid */}
      {monitoringData && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          {Object.entries(monitoringData.metrics).map(([key, metric]) => (
            <Grid item xs={12} sm={6} md={4} key={key}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                    <Typography variant="subtitle2" color="text.secondary">
                      {key.replace(/_/g, ' ').toUpperCase()}
                    </Typography>
                    {metric.threshold && getTrendIcon(metric.value, metric.threshold)}
                  </Box>
                  <Typography variant="h4" fontWeight="bold">
                    {metric.value.toLocaleString()}
                    <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                      {metric.unit}
                    </Typography>
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1} mt={1}>
                    <Chip
                      label={metric.status}
                      size="small"
                      color={metric.status === 'normal' ? 'success' : 
                             metric.status === 'warning' ? 'warning' : 'error'}
                    />
                    {metric.threshold && (
                      <Typography variant="caption" color="text.secondary">
                        阈值: {metric.threshold}
                      </Typography>
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Alerts and Incidents */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">活跃告警</Typography>
                <Badge badgeContent={alerts.filter(a => a.status === 'active').length} color="error">
                  <IconButton onClick={() => setShowAlertsDialog(true)}>
                    <Notifications />
                  </IconButton>
                </Badge>
              </Box>
              <List>
                {alerts.slice(0, 5).map((alert) => (
                  <ListItem key={alert.id} divider>
                    <ListItemIcon>
                      {getSeverityIcon(alert.severity)}
                    </ListItemIcon>
                    <ListItemText
                      primary={alert.title}
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            {alert.description}
                          </Typography>
                          <Box display="flex" gap={1} mt={1}>
                            <Chip
                              label={alert.severity}
                              size="small"
                              color={getSeverityColor(alert.severity) as any}
                            />
                            <Chip
                              label={alert.status}
                              size="small"
                              variant="outlined"
                            />
                          </Box>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
                {alerts.length === 0 && (
                  <ListItem>
                    <ListItemText
                      primary="暂无活跃告警"
                      secondary="系统运行正常"
                    />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">风险事件</Typography>
                <Badge badgeContent={riskIncidents.length} color="warning">
                  <IconButton onClick={() => setShowIncidentsDialog(true)}>
                    <Security />
                  </IconButton>
                </Badge>
              </Box>
              <List>
                {riskIncidents.slice(0, 5).map((incident) => (
                  <ListItem key={incident.id} divider>
                    <ListItemIcon>
                      {getSeverityIcon(incident.severity)}
                    </ListItemIcon>
                    <ListItemText
                      primary={incident.incident_type}
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            {incident.description}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {format(new Date(incident.detected_at), 'MM-dd HH:mm', { locale: zhCN })}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
                {riskIncidents.length === 0 && (
                  <ListItem>
                    <ListItemText
                      primary="暂无风险事件"
                      secondary="系统安全状态良好"
                    />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alerts Dialog */}
      <Dialog open={showAlertsDialog} onClose={() => setShowAlertsDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>告警详情</DialogTitle>
        <DialogContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>标题</TableCell>
                  <TableCell>严重程度</TableCell>
                  <TableCell>状态</TableCell>
                  <TableCell>时间</TableCell>
                  <TableCell>操作</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {alerts.map((alert) => (
                  <TableRow key={alert.id}>
                    <TableCell>
                      <Typography variant="subtitle2">{alert.title}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {alert.description}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={alert.severity}
                        color={getSeverityColor(alert.severity) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={alert.status}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      {format(new Date(alert.timestamp), 'MM-dd HH:mm', { locale: zhCN })}
                    </TableCell>
                    <TableCell>
                      {alert.status === 'active' && (
                        <Box display="flex" gap={1}>
                          <Button
                            size="small"
                            onClick={() => acknowledgeAlert(alert.id)}
                          >
                            确认
                          </Button>
                          <Button
                            size="small"
                            color="success"
                            onClick={() => resolveAlert(alert.id)}
                          >
                            解决
                          </Button>
                        </Box>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowAlertsDialog(false)}>关闭</Button>
        </DialogActions>
      </Dialog>

      {/* Incidents Dialog */}
      <Dialog open={showIncidentsDialog} onClose={() => setShowIncidentsDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>风险事件详情</DialogTitle>
        <DialogContent>
          <List>
            {riskIncidents.map((incident) => (
              <React.Fragment key={incident.id}>
                <ListItem>
                  <ListItemIcon>
                    {getSeverityIcon(incident.severity)}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="subtitle1">{incident.incident_type}</Typography>
                        <Chip
                          label={incident.severity}
                          color={getSeverityColor(incident.severity) as any}
                          size="small"
                        />
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          {incident.description}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          检测时间: {format(new Date(incident.detected_at), 'yyyy-MM-dd HH:mm:ss', { locale: zhCN })}
                        </Typography>
                        {incident.affected_resources.length > 0 && (
                          <Box mt={1}>
                            <Typography variant="caption" color="text.secondary">
                              受影响资源: {incident.affected_resources.join(', ')}
                            </Typography>
                          </Box>
                        )}
                        {incident.mitigation_actions.length > 0 && (
                          <Box mt={1}>
                            <Typography variant="caption" color="text.secondary">
                              缓解措施: {incident.mitigation_actions.join(', ')}
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
                <Divider />
              </React.Fragment>
            ))}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowIncidentsDialog(false)}>关闭</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RealTimeMonitor;
