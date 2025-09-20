import React from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  IconButton,
  Chip,
  LinearProgress,
  useTheme,
  styled,
} from '@mui/material';
import {
  MoreVert as MoreVertIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
} from '@mui/icons-material';
import { gradients } from '../../../theme/bedrock/gradients';
import { bedrockColors } from '../../../theme/bedrock/colors';

export type DataCardStatus = 'compliant' | 'risk' | 'warning' | 'analyzing' | 'pending';
export type DataCardTrend = 'up' | 'down' | 'stable';

export interface DataCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  status?: DataCardStatus;
  trend?: DataCardTrend;
  trendValue?: string;
  progress?: number;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  onClick?: () => void;
  loading?: boolean;
  className?: string;
}

// 状态颜色映射
const statusColors: Record<DataCardStatus, string> = {
  compliant: bedrockColors.success.main,
  risk: bedrockColors.error.main,
  warning: bedrockColors.warning.main,
  analyzing: bedrockColors.secondary.main,
  pending: bedrockColors.grey[500],
};

// 状态渐变映射
const statusGradients: Record<DataCardStatus, string> = {
  compliant: gradients.success.main,
  risk: gradients.error.main,
  warning: gradients.warning.main,
  analyzing: gradients.secondary.main,
  pending: gradients.background.main,
};

// 样式化卡片组件
const StyledCard = styled(Card, {
  shouldForwardProp: (prop) => prop !== 'status' && prop !== 'clickable',
})<{ status?: DataCardStatus; clickable?: boolean }>(({ theme, status, clickable }) => ({
  position: 'relative',
  borderRadius: 12,
  overflow: 'hidden',
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  cursor: clickable ? 'pointer' : 'default',
  
  // 渐变边框效果
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 3,
    background: status ? statusGradients[status] : gradients.primary.main,
    borderRadius: '12px 12px 0 0',
  },

  // 悬停效果
  ...(clickable && {
    '&:hover': {
      transform: 'translateY(-4px)',
      boxShadow: theme.shadows[8],
      '&::after': {
        content: '""',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: status ? statusGradients[status] : gradients.primary.main,
        opacity: 0.05,
        pointerEvents: 'none',
      },
    },
  }),

  // 加载状态
  '&.loading': {
    '&::after': {
      content: '""',
      position: 'absolute',
      top: 0,
      left: '-100%',
      width: '100%',
      height: '100%',
      background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent)',
      animation: 'shimmer 2s infinite',
    },
  },

  '@keyframes shimmer': {
    '0%': {
      left: '-100%',
    },
    '100%': {
      left: '100%',
    },
  },
}));

// 状态芯片组件
const StatusChip = styled(Chip)<{ status: DataCardStatus }>(({ status }) => ({
  background: bedrockColors.status[status].bg,
  color: bedrockColors.status[status].text,
  border: `1px solid ${bedrockColors.status[status].border}`,
  fontSize: '0.75rem',
  height: 24,
}));

// 趋势指示器组件
const TrendIndicator: React.FC<{ trend: DataCardTrend; value?: string }> = ({ trend, value }) => {
  const theme = useTheme();
  
  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return theme.palette.success.main;
      case 'down':
        return theme.palette.error.main;
      default:
        return theme.palette.text.secondary;
    }
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUpIcon fontSize="small" />;
      case 'down':
        return <TrendingDownIcon fontSize="small" />;
      default:
        return null;
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 0.5,
        color: getTrendColor(),
        fontSize: '0.875rem',
        fontWeight: 500,
      }}
    >
      {getTrendIcon()}
      {value && <span>{value}</span>}
    </Box>
  );
};

/**
 * 磐石数据卡片组件
 * 用于展示关键数据指标，支持多种状态和交互效果
 */
export const DataCard: React.FC<DataCardProps> = ({
  title,
  value,
  subtitle,
  status,
  trend,
  trendValue,
  progress,
  icon,
  action,
  onClick,
  loading = false,
  className,
}) => {
  const theme = useTheme();

  return (
    <StyledCard
      status={status}
      clickable={!!onClick}
      onClick={onClick}
      className={`${loading ? 'loading' : ''} ${className || ''}`}
      elevation={2}
    >
      <CardHeader
        avatar={
          icon && (
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: '12px',
                background: status ? statusGradients[status] : gradients.primary.main,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '1.5rem',
              }}
            >
              {icon}
            </Box>
          )
        }
        action={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {status && (
              <StatusChip
                status={status}
                label={status.charAt(0).toUpperCase() + status.slice(1)}
                size="small"
              />
            )}
            {action || (
              <IconButton size="small">
                <MoreVertIcon />
              </IconButton>
            )}
          </Box>
        }
        title={
          <Typography
            variant="h6"
            sx={{
              fontWeight: 600,
              color: 'text.primary',
              fontSize: '1rem',
            }}
          >
            {title}
          </Typography>
        }
        sx={{ pb: 1 }}
      />

      <CardContent sx={{ pt: 0 }}>
        <Box sx={{ mb: 2 }}>
          <Typography
            variant="h3"
            sx={{
              fontWeight: 700,
              color: status ? statusColors[status] : 'text.primary',
              fontSize: '2rem',
              lineHeight: 1.2,
              mb: 0.5,
            }}
          >
            {loading ? '...' : value}
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            {subtitle && (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            )}
            {trend && (
              <TrendIndicator trend={trend} value={trendValue} />
            )}
          </Box>
        </Box>

        {typeof progress === 'number' && (
          <Box sx={{ mb: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="caption" color="text.secondary">
                进度
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {Math.round(progress)}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{
                height: 6,
                borderRadius: 3,
                backgroundColor: theme.palette.grey[200],
                '& .MuiLinearProgress-bar': {
                  background: status ? statusGradients[status] : gradients.primary.main,
                  borderRadius: 3,
                },
              }}
            />
          </Box>
        )}
      </CardContent>
    </StyledCard>
  );
};

export default DataCard;
