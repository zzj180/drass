import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Grid,
  Chip,
  Divider,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Paper,
} from '@mui/material';
import {
  Security as SecurityIcon,
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  Person as PersonIcon,
  Computer as ComputerIcon,
  Language as LanguageIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  AccessTime as TimeIcon,
  LocationOn as LocationIcon,
  Fingerprint as FingerprintIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// 日志详情类型
export interface LogDetail {
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

// 样式化组件
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

const InfoCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  '&:last-child': {
    marginBottom: 0,
  },
}));

interface LogDetailDialogProps {
  open: boolean;
  onClose: () => void;
  logDetail: LogDetail | null;
}

const LogDetailDialog: React.FC<LogDetailDialogProps> = ({
  open,
  onClose,
  logDetail,
}) => {
  if (!logDetail) return null;

  // 解析用户代理信息
  const parseUserAgent = (userAgent: string) => {
    const browser = userAgent.includes('Chrome') ? 'Chrome' : 
                   userAgent.includes('Firefox') ? 'Firefox' : 
                   userAgent.includes('Safari') ? 'Safari' : 
                   userAgent.includes('Edge') ? 'Edge' : 'Unknown';
    
    const os = userAgent.includes('Windows') ? 'Windows' : 
               userAgent.includes('Mac') ? 'macOS' : 
               userAgent.includes('Linux') ? 'Linux' : 
               userAgent.includes('Android') ? 'Android' : 
               userAgent.includes('iOS') ? 'iOS' : 'Unknown';
    
    return { browser, os };
  };

  const { browser, os } = parseUserAgent(logDetail.userAgent);

  // 获取状态图标
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  // 获取严重程度图标
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <ErrorIcon color="error" />;
      case 'high':
        return <WarningIcon color="warning" />;
      case 'medium':
        return <InfoIcon color="info" />;
      case 'low':
        return <CheckCircleIcon color="success" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: '70vh' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SecurityIcon color="primary" />
            <Typography variant="h6">审计日志详情</Typography>
          </Box>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent dividers>
        <Box sx={{ mt: 1 }}>
          {/* 基本信息 */}
          <InfoCard>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <InfoIcon color="primary" />
                基本信息
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <TimeIcon color="action" />
                    <Typography variant="subtitle2" color="text.secondary">时间</Typography>
                  </Box>
                  <Typography variant="body1">
                    {new Date(logDetail.timestamp).toLocaleString()}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <PersonIcon color="action" />
                    <Typography variant="subtitle2" color="text.secondary">用户</Typography>
                  </Box>
                  <Typography variant="body1">{logDetail.userName}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <SecurityIcon color="action" />
                    <Typography variant="subtitle2" color="text.secondary">操作</Typography>
                  </Box>
                  <Typography variant="body1">{logDetail.action}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <InfoIcon color="action" />
                    <Typography variant="subtitle2" color="text.secondary">资源</Typography>
                  </Box>
                  <Typography variant="body1">{logDetail.resource}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    {getStatusIcon(logDetail.status)}
                    <Typography variant="subtitle2" color="text.secondary">状态</Typography>
                  </Box>
                  <StatusChip label={logDetail.status} status={logDetail.status} size="small" />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    {getSeverityIcon(logDetail.severity)}
                    <Typography variant="subtitle2" color="text.secondary">严重程度</Typography>
                  </Box>
                  <SeverityChip label={logDetail.severity} severity={logDetail.severity} size="small" />
                </Grid>
              </Grid>
            </CardContent>
          </InfoCard>

          {/* 网络信息 */}
          <InfoCard>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LocationIcon color="primary" />
                网络信息
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <ComputerIcon color="action" />
                    <Typography variant="subtitle2" color="text.secondary">IP地址</Typography>
                  </Box>
                  <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
                    {logDetail.ipAddress}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <LanguageIcon color="action" />
                    <Typography variant="subtitle2" color="text.secondary">浏览器</Typography>
                  </Box>
                  <Typography variant="body1">{browser}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <ComputerIcon color="action" />
                    <Typography variant="subtitle2" color="text.secondary">操作系统</Typography>
                  </Box>
                  <Typography variant="body1">{os}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <FingerprintIcon color="action" />
                    <Typography variant="subtitle2" color="text.secondary">资源类型</Typography>
                  </Box>
                  <Typography variant="body1">{logDetail.resourceType}</Typography>
                </Grid>
              </Grid>
            </CardContent>
          </InfoCard>

          {/* 详细信息 */}
          <InfoCard>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <InfoIcon color="primary" />
                详细信息
              </Typography>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {logDetail.details}
              </Typography>
            </CardContent>
          </InfoCard>

          {/* 技术信息 */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">技术信息</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    请求ID
                  </Typography>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                    {logDetail.requestId || 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    会话ID
                  </Typography>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                    {logDetail.sessionId || 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    用户代理
                  </Typography>
                  <Paper sx={{ p: 2, backgroundColor: 'grey.50' }}>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
                      {logDetail.userAgent}
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>

          {/* 附加数据 */}
          {logDetail.additionalData && Object.keys(logDetail.additionalData).length > 0 && (
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">附加数据</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <List dense>
                  {Object.entries(logDetail.additionalData).map(([key, value]) => (
                    <ListItem key={key} divider>
                      <ListItemText
                        primary={key}
                        secondary={typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                        secondaryTypographyProps={{
                          sx: { fontFamily: 'monospace', whiteSpace: 'pre-wrap' }
                        }}
                      />
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
          )}
        </Box>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose} variant="contained">
          关闭
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default LogDetailDialog;
