/**
 * 磐石数据合规分析系统 - 动画配置
 * Bedrock Data Compliance Analysis System - Animation Configuration
 */

// 动画时长配置
export const durations = {
  shortest: 150,
  shorter: 200,
  short: 250,
  standard: 300,
  complex: 375,
  enteringScreen: 225,
  leavingScreen: 195,
  long: 500,
  extended: 750,
};

// 缓动函数配置
export const easings = {
  // Material Design 缓动
  easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
  easeOut: 'cubic-bezier(0.0, 0, 0.2, 1)',
  easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
  sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
  
  // 自定义缓动
  bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  elastic: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
  smooth: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
  gentle: 'cubic-bezier(0.25, 0.1, 0.25, 1)',
};

// 关键帧动画定义
export const keyframes = {
  // 淡入动画
  fadeIn: `
    @keyframes fadeIn {
      from {
        opacity: 0;
      }
      to {
        opacity: 1;
      }
    }
  `,

  // 淡出动画
  fadeOut: `
    @keyframes fadeOut {
      from {
        opacity: 1;
      }
      to {
        opacity: 0;
      }
    }
  `,

  // 滑入动画
  slideInUp: `
    @keyframes slideInUp {
      from {
        transform: translateY(100%);
        opacity: 0;
      }
      to {
        transform: translateY(0);
        opacity: 1;
      }
    }
  `,

  slideInDown: `
    @keyframes slideInDown {
      from {
        transform: translateY(-100%);
        opacity: 0;
      }
      to {
        transform: translateY(0);
        opacity: 1;
      }
    }
  `,

  slideInLeft: `
    @keyframes slideInLeft {
      from {
        transform: translateX(-100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
  `,

  slideInRight: `
    @keyframes slideInRight {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
  `,

  // 缩放动画
  scaleIn: `
    @keyframes scaleIn {
      from {
        transform: scale(0);
        opacity: 0;
      }
      to {
        transform: scale(1);
        opacity: 1;
      }
    }
  `,

  scaleOut: `
    @keyframes scaleOut {
      from {
        transform: scale(1);
        opacity: 1;
      }
      to {
        transform: scale(0);
        opacity: 0;
      }
    }
  `,

  // 脉冲动画
  pulse: `
    @keyframes pulse {
      0% {
        transform: scale(1);
        opacity: 1;
      }
      50% {
        transform: scale(1.05);
        opacity: 0.8;
      }
      100% {
        transform: scale(1);
        opacity: 1;
      }
    }
  `,

  // 心跳动画
  heartbeat: `
    @keyframes heartbeat {
      0% {
        transform: scale(1);
      }
      14% {
        transform: scale(1.1);
      }
      28% {
        transform: scale(1);
      }
      42% {
        transform: scale(1.1);
      }
      70% {
        transform: scale(1);
      }
    }
  `,

  // 摇摆动画
  wobble: `
    @keyframes wobble {
      0% {
        transform: translateX(0%);
      }
      15% {
        transform: translateX(-25%) rotate(-5deg);
      }
      30% {
        transform: translateX(20%) rotate(3deg);
      }
      45% {
        transform: translateX(-15%) rotate(-3deg);
      }
      60% {
        transform: translateX(10%) rotate(2deg);
      }
      75% {
        transform: translateX(-5%) rotate(-1deg);
      }
      100% {
        transform: translateX(0%);
      }
    }
  `,

  // 旋转动画
  rotate: `
    @keyframes rotate {
      from {
        transform: rotate(0deg);
      }
      to {
        transform: rotate(360deg);
      }
    }
  `,

  // 闪烁动画
  blink: `
    @keyframes blink {
      0%, 50% {
        opacity: 1;
      }
      51%, 100% {
        opacity: 0;
      }
    }
  `,

  // 弹跳动画
  bounce: `
    @keyframes bounce {
      0%, 20%, 53%, 80%, 100% {
        transform: translate3d(0, 0, 0);
      }
      40%, 43% {
        transform: translate3d(0, -30px, 0);
      }
      70% {
        transform: translate3d(0, -15px, 0);
      }
      90% {
        transform: translate3d(0, -4px, 0);
      }
    }
  `,

  // 摇动动画
  shake: `
    @keyframes shake {
      0%, 100% {
        transform: translateX(0);
      }
      10%, 30%, 50%, 70%, 90% {
        transform: translateX(-10px);
      }
      20%, 40%, 60%, 80% {
        transform: translateX(10px);
      }
    }
  `,

  // 数据流动画
  dataFlow: `
    @keyframes dataFlow {
      0% {
        transform: translateX(-100%);
        opacity: 0;
      }
      50% {
        opacity: 1;
      }
      100% {
        transform: translateX(100%);
        opacity: 0;
      }
    }
  `,

  // 扫描线动画
  scanLine: `
    @keyframes scanLine {
      0% {
        transform: translateX(-100%);
      }
      100% {
        transform: translateX(100%);
      }
    }
  `,

  // 光晕动画
  glow: `
    @keyframes glow {
      0%, 100% {
        box-shadow: 0 0 5px rgba(74, 144, 226, 0.5);
      }
      50% {
        box-shadow: 0 0 20px rgba(74, 144, 226, 0.8), 0 0 30px rgba(74, 144, 226, 0.6);
      }
    }
  `,

  // 进度条动画
  progressBar: `
    @keyframes progressBar {
      0% {
        width: 0%;
      }
      100% {
        width: var(--progress-width, 100%);
      }
    }
  `,

  // 骨架屏动画
  skeleton: `
    @keyframes skeleton {
      0% {
        background-position: -200px 0;
      }
      100% {
        background-position: calc(200px + 100%) 0;
      }
    }
  `,

  // 打字机效果
  typewriter: `
    @keyframes typewriter {
      from {
        width: 0;
      }
      to {
        width: 100%;
      }
    }
  `,

  // 渐变流动
  gradientFlow: `
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
};

// 预定义动画组合
export const animations = {
  // 页面进入动画
  pageEnter: {
    animation: 'fadeIn 0.3s ease-out',
    keyframes: keyframes.fadeIn,
  },

  // 页面退出动画
  pageExit: {
    animation: 'fadeOut 0.2s ease-in',
    keyframes: keyframes.fadeOut,
  },

  // 卡片悬停动画
  cardHover: {
    transition: `transform ${durations.short}ms ${easings.easeOut}, box-shadow ${durations.short}ms ${easings.easeOut}`,
    transform: 'translateY(-4px)',
    boxShadow: '0 8px 25px rgba(0, 82, 204, 0.15)',
  },

  // 按钮点击动画
  buttonClick: {
    transition: `transform ${durations.shortest}ms ${easings.sharp}`,
    transform: 'scale(0.95)',
  },

  // 输入框聚焦动画
  inputFocus: {
    transition: `border-color ${durations.short}ms ${easings.easeOut}, box-shadow ${durations.short}ms ${easings.easeOut}`,
    borderColor: '#4A90E2',
    boxShadow: '0 0 0 2px rgba(74, 144, 226, 0.2)',
  },

  // 加载动画
  loading: {
    animation: `rotate ${durations.extended}ms linear infinite`,
    keyframes: keyframes.rotate,
  },

  // 成功动画
  success: {
    animation: `scaleIn ${durations.standard}ms ${easings.bounce}`,
    keyframes: keyframes.scaleIn,
  },

  // 错误动画
  error: {
    animation: `shake ${durations.complex}ms ${easings.easeInOut}`,
    keyframes: keyframes.shake,
  },

  // 数据更新动画
  dataUpdate: {
    animation: `pulse ${durations.standard}ms ${easings.easeInOut}`,
    keyframes: keyframes.pulse,
  },

  // 状态变化动画
  statusChange: {
    transition: `all ${durations.standard}ms ${easings.easeInOut}`,
  },

  // 骨架屏加载动画
  skeletonLoading: {
    animation: `skeleton ${durations.extended}ms ease-in-out infinite`,
    keyframes: keyframes.skeleton,
    background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
    backgroundSize: '200px 100%',
  },

  // 数据流动画
  dataFlowAnimation: {
    animation: `dataFlow ${durations.long * 2}ms ${easings.easeInOut} infinite`,
    keyframes: keyframes.dataFlow,
  },

  // 扫描线动画
  scanLineAnimation: {
    animation: `scanLine ${durations.long}ms ${easings.easeInOut} infinite`,
    keyframes: keyframes.scanLine,
  },

  // 光晕效果动画
  glowAnimation: {
    animation: `glow ${durations.long}ms ${easings.easeInOut} infinite alternate`,
    keyframes: keyframes.glow,
  },

  // 渐变流动动画
  gradientFlowAnimation: {
    animation: `gradientFlow ${durations.long * 2}ms ${easings.easeInOut} infinite`,
    keyframes: keyframes.gradientFlow,
    backgroundSize: '200% 200%',
  },
};

// 动画工具函数
export const animationUtils = {
  // 创建延迟动画
  createDelayedAnimation: (animationName: string, delay: number) => ({
    animation: `${animationName} ${durations.standard}ms ${easings.easeOut} ${delay}ms both`,
  }),

  // 创建交错动画
  createStaggeredAnimation: (animationName: string, index: number, staggerDelay: number = 100) => ({
    animation: `${animationName} ${durations.standard}ms ${easings.easeOut} ${index * staggerDelay}ms both`,
  }),

  // 创建无限动画
  createInfiniteAnimation: (animationName: string, duration: number = durations.standard) => ({
    animation: `${animationName} ${duration}ms ${easings.easeInOut} infinite`,
  }),

  // 创建悬停动画
  createHoverAnimation: (transform: string = 'translateY(-2px)', duration: number = durations.short) => ({
    transition: `transform ${duration}ms ${easings.easeOut}`,
    '&:hover': {
      transform,
    },
  }),

  // 创建点击动画
  createClickAnimation: (scale: number = 0.95, duration: number = durations.shortest) => ({
    transition: `transform ${duration}ms ${easings.sharp}`,
    '&:active': {
      transform: `scale(${scale})`,
    },
  }),
};

// 响应式动画配置
export const responsiveAnimations = {
  // 移动端减少动画
  mobile: {
    '@media (prefers-reduced-motion: reduce)': {
      animation: 'none',
      transition: 'none',
    },
    '@media (max-width: 768px)': {
      animationDuration: '0.2s',
      transitionDuration: '0.2s',
    },
  },

  // 高性能模式
  performanceMode: {
    willChange: 'transform, opacity',
    backfaceVisibility: 'hidden',
    perspective: 1000,
  },
};

export default animations;
