/**
 * 磐石数据合规分析系统 - 渐变配置
 * Bedrock Data Compliance Analysis System - Gradient Configuration
 */

// 主要渐变配置
export const gradients = {
  // 主色调渐变
  primary: {
    light: 'linear-gradient(135deg, #4A90E2 0%, #7BB3F0 100%)',
    main: 'linear-gradient(135deg, #0052CC 0%, #4A90E2 100%)',
    dark: 'linear-gradient(135deg, #003366 0%, #0052CC 100%)',
    vertical: 'linear-gradient(180deg, #0052CC 0%, #4A90E2 100%)',
    radial: 'radial-gradient(circle, #4A90E2 0%, #0052CC 100%)',
  },

  // 成功状态渐变
  success: {
    light: 'linear-gradient(135deg, #4ECDC4 0%, #7EDDD8 100%)',
    main: 'linear-gradient(135deg, #00B386 0%, #4ECDC4 100%)',
    dark: 'linear-gradient(135deg, #008B5A 0%, #00B386 100%)',
    vertical: 'linear-gradient(180deg, #00B386 0%, #4ECDC4 100%)',
    radial: 'radial-gradient(circle, #4ECDC4 0%, #00B386 100%)',
  },

  // 警告状态渐变
  warning: {
    light: 'linear-gradient(135deg, #FFB366 0%, #FFC999 100%)',
    main: 'linear-gradient(135deg, #FF8C42 0%, #FFB366 100%)',
    dark: 'linear-gradient(135deg, #E6732A 0%, #FF8C42 100%)',
    vertical: 'linear-gradient(180deg, #FF8C42 0%, #FFB366 100%)',
    radial: 'radial-gradient(circle, #FFB366 0%, #FF8C42 100%)',
  },

  // 错误状态渐变
  error: {
    light: 'linear-gradient(135deg, #EC7063 0%, #F1948A 100%)',
    main: 'linear-gradient(135deg, #E74C3C 0%, #EC7063 100%)',
    dark: 'linear-gradient(135deg, #C0392B 0%, #E74C3C 100%)',
    vertical: 'linear-gradient(180deg, #E74C3C 0%, #EC7063 100%)',
    radial: 'radial-gradient(circle, #EC7063 0%, #E74C3C 100%)',
  },

  // 次要色渐变
  secondary: {
    light: 'linear-gradient(135deg, #BB8FCE 0%, #D7BDE2 100%)',
    main: 'linear-gradient(135deg, #8E44AD 0%, #BB8FCE 100%)',
    dark: 'linear-gradient(135deg, #6C3483 0%, #8E44AD 100%)',
    vertical: 'linear-gradient(180deg, #8E44AD 0%, #BB8FCE 100%)',
    radial: 'radial-gradient(circle, #BB8FCE 0%, #8E44AD 100%)',
  },

  // 信息状态渐变
  info: {
    light: 'linear-gradient(135deg, #5DADE2 0%, #85C1E9 100%)',
    main: 'linear-gradient(135deg, #17A2B8 0%, #5DADE2 100%)',
    dark: 'linear-gradient(135deg, #138496 0%, #17A2B8 100%)',
    vertical: 'linear-gradient(180deg, #17A2B8 0%, #5DADE2 100%)',
    radial: 'radial-gradient(circle, #5DADE2 0%, #17A2B8 100%)',
  },

  // 背景渐变
  background: {
    light: 'linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%)',
    main: 'linear-gradient(135deg, #F1F5F9 0%, #E2E8F0 100%)',
    dark: 'linear-gradient(135deg, #1A202C 0%, #2D3748 100%)',
    hero: 'linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #334155 100%)',
    card: 'linear-gradient(145deg, #FFFFFF 0%, #F8FAFC 100%)',
    darkCard: 'linear-gradient(145deg, #1E293B 0%, #334155 100%)',
  },

  // 特殊效果渐变
  special: {
    // 数据流效果
    dataFlow: 'linear-gradient(90deg, transparent 0%, #4A90E2 50%, transparent 100%)',
    // 扫描线效果
    scanLine: 'linear-gradient(90deg, transparent 0%, #00B386 25%, #4ECDC4 50%, #00B386 75%, transparent 100%)',
    // 光晕效果
    glow: 'radial-gradient(circle, rgba(74, 144, 226, 0.3) 0%, transparent 70%)',
    // 脉冲效果
    pulse: 'radial-gradient(circle, rgba(0, 82, 204, 0.8) 0%, rgba(0, 82, 204, 0.2) 50%, transparent 100%)',
  },

  // 图表渐变
  chart: {
    area: {
      primary: 'linear-gradient(180deg, rgba(74, 144, 226, 0.3) 0%, rgba(74, 144, 226, 0.05) 100%)',
      success: 'linear-gradient(180deg, rgba(78, 205, 196, 0.3) 0%, rgba(78, 205, 196, 0.05) 100%)',
      warning: 'linear-gradient(180deg, rgba(255, 179, 102, 0.3) 0%, rgba(255, 179, 102, 0.05) 100%)',
      error: 'linear-gradient(180deg, rgba(236, 112, 99, 0.3) 0%, rgba(236, 112, 99, 0.05) 100%)',
    },
    bar: {
      primary: 'linear-gradient(0deg, #0052CC 0%, #4A90E2 100%)',
      success: 'linear-gradient(0deg, #00B386 0%, #4ECDC4 100%)',
      warning: 'linear-gradient(0deg, #FF8C42 0%, #FFB366 100%)',
      error: 'linear-gradient(0deg, #E74C3C 0%, #EC7063 100%)',
    }
  },

  // 状态指示器渐变
  status: {
    compliant: 'linear-gradient(135deg, #00B386 0%, #4ECDC4 100%)',
    risk: 'linear-gradient(135deg, #E74C3C 0%, #EC7063 100%)',
    warning: 'linear-gradient(135deg, #FF8C42 0%, #FFB366 100%)',
    analyzing: 'linear-gradient(135deg, #8E44AD 0%, #BB8FCE 100%)',
    pending: 'linear-gradient(135deg, #718096 0%, #A0AEC0 100%)',
  },

  // 按钮渐变
  button: {
    primary: {
      normal: 'linear-gradient(135deg, #0052CC 0%, #4A90E2 100%)',
      hover: 'linear-gradient(135deg, #003DA3 0%, #4A90E2 100%)',
      active: 'linear-gradient(135deg, #003366 0%, #0052CC 100%)',
      disabled: 'linear-gradient(135deg, #CBD5E0 0%, #E2E8F0 100%)',
    },
    success: {
      normal: 'linear-gradient(135deg, #00B386 0%, #4ECDC4 100%)',
      hover: 'linear-gradient(135deg, #009269 0%, #4ECDC4 100%)',
      active: 'linear-gradient(135deg, #008B5A 0%, #00B386 100%)',
    },
    warning: {
      normal: 'linear-gradient(135deg, #FF8C42 0%, #FFB366 100%)',
      hover: 'linear-gradient(135deg, #EF6C00 0%, #FFB366 100%)',
      active: 'linear-gradient(135deg, #E6732A 0%, #FF8C42 100%)',
    },
    error: {
      normal: 'linear-gradient(135deg, #E74C3C 0%, #EC7063 100%)',
      hover: 'linear-gradient(135deg, #D32F2F 0%, #EC7063 100%)',
      active: 'linear-gradient(135deg, #C0392B 0%, #E74C3C 100%)',
    },
  },

  // 边框渐变
  border: {
    primary: 'linear-gradient(135deg, #4A90E2, #7BB3F0)',
    success: 'linear-gradient(135deg, #4ECDC4, #7EDDD8)',
    warning: 'linear-gradient(135deg, #FFB366, #FFC999)',
    error: 'linear-gradient(135deg, #EC7063, #F1948A)',
    info: 'linear-gradient(135deg, #5DADE2, #85C1E9)',
    focus: 'linear-gradient(135deg, #4A90E2, #0052CC)',
  },
};

// CSS 自定义属性生成器
export const generateGradientCSS = () => {
  const cssVars: Record<string, string> = {};
  
  Object.entries(gradients).forEach(([category, categoryGradients]) => {
    if (typeof categoryGradients === 'object') {
      Object.entries(categoryGradients).forEach(([key, value]) => {
        if (typeof value === 'string') {
          cssVars[`--gradient-${category}-${key}`] = value;
        } else if (typeof value === 'object') {
          Object.entries(value).forEach(([subKey, subValue]) => {
            if (typeof subValue === 'string') {
              cssVars[`--gradient-${category}-${key}-${subKey}`] = subValue;
            }
          });
        }
      });
    }
  });
  
  return cssVars;
};

// 动态渐变生成器
export const createGradient = (
  colors: string[],
  direction: number = 135,
  type: 'linear' | 'radial' = 'linear'
): string => {
  if (type === 'radial') {
    return `radial-gradient(circle, ${colors.join(', ')})`;
  }
  return `linear-gradient(${direction}deg, ${colors.join(', ')})`;
};

// 渐变动画关键帧
export const gradientAnimations = {
  shimmer: `
    @keyframes shimmer {
      0% {
        background-position: -200px 0;
      }
      100% {
        background-position: calc(200px + 100%) 0;
      }
    }
  `,
  pulse: `
    @keyframes gradientPulse {
      0%, 100% {
        opacity: 1;
      }
      50% {
        opacity: 0.7;
      }
    }
  `,
  flow: `
    @keyframes gradientFlow {
      0% {
        background-position: 0% 50%;
      }
      50% {
        background-position: 100% 50%;
      }
      100% {
        background-position: 0% 50%;
      }
    }
  `,
  rotate: `
    @keyframes gradientRotate {
      0% {
        transform: rotate(0deg);
      }
      100% {
        transform: rotate(360deg);
      }
    }
  `,
};

export default gradients;
