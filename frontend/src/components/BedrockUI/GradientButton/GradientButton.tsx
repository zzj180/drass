import React from 'react';
import {
  Button,
  ButtonProps,
  CircularProgress,
  styled,
  useTheme,
} from '@mui/material';
import { gradients } from '../../../theme/bedrock/gradients';

export type GradientButtonVariant = 'primary' | 'success' | 'warning' | 'error' | 'info' | 'secondary';

export interface GradientButtonProps extends Omit<ButtonProps, 'variant' | 'color'> {
  variant?: GradientButtonVariant;
  loading?: boolean;
  glow?: boolean;
  pulse?: boolean;
}

// 样式化按钮组件
const StyledButton = styled(Button, {
  shouldForwardProp: (prop) => 
    prop !== 'gradientVariant' && 
    prop !== 'glow' && 
    prop !== 'pulse' && 
    prop !== 'loading',
})<{
  gradientVariant: GradientButtonVariant;
  glow?: boolean;
  pulse?: boolean;
  loading?: boolean;
}>(({ theme, gradientVariant, glow, pulse, loading, disabled }) => {
  const gradientMap = {
    primary: gradients.button.primary,
    success: gradients.button.success,
    warning: gradients.button.warning,
    error: gradients.button.error,
    info: gradients.info,
    secondary: gradients.secondary,
  };

  const currentGradient = gradientMap[gradientVariant] || gradientMap.primary;
  
  return {
    position: 'relative',
    borderRadius: 8,
    padding: '10px 24px',
    fontWeight: 600,
    fontSize: '0.875rem',
    textTransform: 'none',
    border: 'none',
    color: '#FFFFFF',
    background: disabled 
      ? gradients.button.primary.disabled 
      : currentGradient.normal,
    boxShadow: disabled 
      ? 'none' 
      : `0 4px 15px rgba(0, 82, 204, 0.3)`,
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    overflow: 'hidden',
    
    // 发光效果
    ...(glow && !disabled && {
      boxShadow: `0 4px 15px rgba(0, 82, 204, 0.4), 0 0 20px rgba(0, 82, 204, 0.2)`,
    }),

    // 脉冲动画
    ...(pulse && !disabled && {
      animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      '@keyframes pulse': {
        '0%, 100%': {
          opacity: 1,
        },
        '50%': {
          opacity: 0.8,
        },
      },
    }),

    // 悬停效果
    '&:hover': {
      background: disabled 
        ? gradients.button.primary.disabled 
        : currentGradient.hover,
      transform: disabled ? 'none' : 'translateY(-2px)',
      boxShadow: disabled 
        ? 'none' 
        : `0 8px 25px rgba(0, 82, 204, 0.4)`,
    },

    // 激活效果
    '&:active': {
      background: disabled 
        ? gradients.button.primary.disabled 
        : currentGradient.active,
      transform: disabled ? 'none' : 'translateY(0)',
    },

    // 聚焦效果
    '&:focus': {
      outline: 'none',
      boxShadow: disabled 
        ? 'none' 
        : `0 4px 15px rgba(0, 82, 204, 0.3), 0 0 0 3px rgba(74, 144, 226, 0.2)`,
    },

    // 禁用状态
    '&:disabled': {
      color: theme.palette.text.disabled,
      cursor: 'not-allowed',
    },

    // 加载状态
    ...(loading && {
      '&::after': {
        content: '""',
        position: 'absolute',
        top: 0,
        left: '-100%',
        width: '100%',
        height: '100%',
        background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent)',
        animation: 'shimmer 1.5s infinite',
      },
      '@keyframes shimmer': {
        '0%': {
          left: '-100%',
        },
        '100%': {
          left: '100%',
        },
      },
    }),

    // 大小变体
    '&.MuiButton-sizeLarge': {
      padding: '12px 32px',
      fontSize: '1rem',
    },
    '&.MuiButton-sizeSmall': {
      padding: '6px 16px',
      fontSize: '0.75rem',
    },
  };
});

// 加载指示器组件
const LoadingIndicator = styled(CircularProgress)(({ theme }) => ({
  color: 'inherit',
  marginRight: theme.spacing(1),
}));

/**
 * 磐石渐变按钮组件
 * 支持多种颜色变体、加载状态、发光效果等
 */
export const GradientButton: React.FC<GradientButtonProps> = ({
  variant = 'primary',
  loading = false,
  glow = false,
  pulse = false,
  children,
  disabled,
  startIcon,
  endIcon,
  ...props
}) => {
  const theme = useTheme();

  const isDisabled = disabled || loading;

  return (
    <StyledButton
      {...props}
      gradientVariant={variant}
      glow={glow && !isDisabled}
      pulse={pulse && !isDisabled}
      loading={loading}
      disabled={isDisabled}
      startIcon={
        loading ? (
          <LoadingIndicator size={16} thickness={2} />
        ) : (
          startIcon
        )
      }
      endIcon={!loading ? endIcon : undefined}
    >
      {children}
    </StyledButton>
  );
};

export default GradientButton;
