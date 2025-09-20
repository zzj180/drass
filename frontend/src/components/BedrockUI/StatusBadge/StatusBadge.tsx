import React from 'react';
import {
  Chip,
  ChipProps,
  styled,
  useTheme,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Analytics as AnalyticsIcon,
} from '@mui/icons-material';
import { bedrockColors } from '../../../theme/bedrock/colors';
import { gradients } from '../../../theme/bedrock/gradients';

export type StatusBadgeVariant = 'compliant' | 'risk' | 'warning' | 'analyzing' | 'pending';
export type StatusBadgeSize = 'small' | 'medium' | 'large';

export interface StatusBadgeProps extends Omit<ChipProps, 'variant' | 'color' | 'size'> {
  status: StatusBadgeVariant;
  size?: StatusBadgeSize;
  showIcon?: boolean;
  pulse?: boolean;
  glow?: boolean;
}

// 状态配置映射
const statusConfig = {
  compliant: {
    label: '合规',
    icon: CheckCircleIcon,
    colors: bedrockColors.status.compliant,
    gradient: gradients.status.compliant,
  },
  risk: {
    label: '风险',
    icon: ErrorIcon,
    colors: bedrockColors.status.risk,
    gradient: gradients.status.risk,
  },
  warning: {
    label: '警告',
    icon: WarningIcon,
    colors: bedrockColors.status.warning,
    gradient: gradients.status.warning,
  },
  analyzing: {
    label: '分析中',
    icon: AnalyticsIcon,
    colors: bedrockColors.status.analyzing,
    gradient: gradients.status.analyzing,
  },
  pending: {
    label: '待处理',
    icon: ScheduleIcon,
    colors: bedrockColors.status.pending,
    gradient: gradients.status.pending,
  },
};

// 大小配置
const sizeConfig = {
  small: {
    height: 20,
    fontSize: '0.6875rem',
    padding: '0 6px',
    iconSize: 12,
  },
  medium: {
    height: 24,
    fontSize: '0.75rem',
    padding: '0 8px',
    iconSize: 16,
  },
  large: {
    height: 32,
    fontSize: '0.875rem',
    padding: '0 12px',
    iconSize: 18,
  },
};

// 样式化芯片组件
const StyledChip = styled(Chip, {
  shouldForwardProp: (prop) => 
    prop !== 'status' && 
    prop !== 'badgeSize' && 
    prop !== 'pulse' && 
    prop !== 'glow',
})<{
  status: StatusBadgeVariant;
  badgeSize: StatusBadgeSize;
  pulse?: boolean;
  glow?: boolean;
}>(({ status, badgeSize, pulse, glow }) => {
  const config = statusConfig[status];
  const sizeProps = sizeConfig[badgeSize];
  
  return {
    height: sizeProps.height,
    fontSize: sizeProps.fontSize,
    padding: sizeProps.padding,
    fontWeight: 600,
    borderRadius: sizeProps.height / 2,
    border: `1px solid ${config.colors.border}`,
    backgroundColor: config.colors.bg,
    color: config.colors.text,
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    
    // 发光效果
    ...(glow && {
      boxShadow: `0 0 10px ${config.colors.border}`,
    }),

    // 脉冲动画
    ...(pulse && {
      animation: 'statusPulse 2s ease-in-out infinite',
      '@keyframes statusPulse': {
        '0%, 100%': {
          opacity: 1,
          transform: 'scale(1)',
        },
        '50%': {
          opacity: 0.8,
          transform: 'scale(1.05)',
        },
      },
    }),

    // 悬停效果
    '&:hover': {
      backgroundColor: config.colors.bg,
      borderColor: config.colors.text,
      transform: 'translateY(-1px)',
      boxShadow: `0 2px 8px ${config.colors.border}`,
    },

    // 图标样式
    '& .MuiChip-icon': {
      color: config.colors.text,
      fontSize: sizeProps.iconSize,
      marginLeft: 4,
    },

    // 删除图标样式
    '& .MuiChip-deleteIcon': {
      color: config.colors.text,
      fontSize: sizeProps.iconSize,
      marginRight: 4,
      '&:hover': {
        color: config.colors.text,
        opacity: 0.8,
      },
    },
  };
});

// 渐变版本的状态徽章
const GradientStatusBadge = styled('div', {
  shouldForwardProp: (prop) => 
    prop !== 'status' && 
    prop !== 'badgeSize' && 
    prop !== 'pulse' && 
    prop !== 'glow',
})<{
  status: StatusBadgeVariant;
  badgeSize: StatusBadgeSize;
  pulse?: boolean;
  glow?: boolean;
}>(({ status, badgeSize, pulse, glow }) => {
  const config = statusConfig[status];
  const sizeProps = sizeConfig[badgeSize];
  
  return {
    display: 'inline-flex',
    alignItems: 'center',
    height: sizeProps.height,
    fontSize: sizeProps.fontSize,
    padding: sizeProps.padding,
    fontWeight: 600,
    borderRadius: sizeProps.height / 2,
    background: config.gradient,
    color: 'white',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    cursor: 'default',
    
    // 发光效果
    ...(glow && {
      boxShadow: `0 0 15px ${config.colors.border}`,
    }),

    // 脉冲动画
    ...(pulse && {
      animation: 'gradientPulse 2s ease-in-out infinite',
      '@keyframes gradientPulse': {
        '0%, 100%': {
          opacity: 1,
          transform: 'scale(1)',
        },
        '50%': {
          opacity: 0.9,
          transform: 'scale(1.05)',
        },
      },
    }),

    // 悬停效果
    '&:hover': {
      transform: 'translateY(-1px)',
      boxShadow: `0 4px 12px ${config.colors.border}`,
    },
  };
});

/**
 * 磐石状态徽章组件
 * 用于显示各种状态信息，支持多种样式和动画效果
 */
export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'medium',
  showIcon = true,
  pulse = false,
  glow = false,
  label,
  variant = 'filled',
  ...props
}) => {
  const theme = useTheme();
  const config = statusConfig[status];
  const StatusIcon = config.icon;

  const displayLabel = label || config.label;

  // 渐变版本
  if (variant === 'filled') {
    return (
      <GradientStatusBadge
        status={status}
        badgeSize={size}
        pulse={pulse}
        glow={glow}
      >
        {showIcon && <StatusIcon style={{ marginRight: 4, fontSize: sizeConfig[size].iconSize }} />}
        {displayLabel}
      </GradientStatusBadge>
    );
  }

  // 标准版本
  return (
    <StyledChip
      {...props}
      status={status}
      badgeSize={size}
      pulse={pulse}
      glow={glow}
      label={displayLabel}
      icon={showIcon ? <StatusIcon /> : undefined}
    />
  );
};

export default StatusBadge;
