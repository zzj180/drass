/**
 * 磐石数据合规分析系统 - 色彩系统配置
 * Bedrock Data Compliance Analysis System - Color System
 */

// 磐石主色调系统
export const bedrockColors = {
  // 1. 磐石蓝 (Bedrock Blue) - 主色调
  primary: {
    50: '#E3F2FD',
    100: '#BBDEFB', 
    200: '#90CAF9',
    300: '#64B5F6',
    400: '#4A90E2',  // 浅蓝辅助
    500: '#0052CC',  // 深蓝主色
    600: '#004BB8',
    700: '#003DA3',
    800: '#003366',  // 深蓝强调
    900: '#002244',
    main: '#0052CC',
    light: '#4A90E2',
    dark: '#003366',
    contrastText: '#FFFFFF',
  },

  // 2. 合规绿 (Compliance Green) - 成功状态
  success: {
    50: '#E8F5F0',
    100: '#C6E6DA',
    200: '#A0D7C2',
    300: '#7AC8AA',
    400: '#4ECDC4',  // 青绿辅助
    500: '#00B386',  // 翠绿主色
    600: '#00A378',
    700: '#009269',
    800: '#008B5A',  // 深绿强调
    900: '#006B45',
    main: '#00B386',
    light: '#4ECDC4',
    dark: '#008B5A',
    contrastText: '#FFFFFF',
  },

  // 3. 警告橙 (Alert Orange) - 警告状态
  warning: {
    50: '#FFF3E0',
    100: '#FFE0B2',
    200: '#FFCC80',
    300: '#FFB74D',
    400: '#FFB366',  // 浅橙辅助
    500: '#FF8C42',  // 活力橙主色
    600: '#F57C00',
    700: '#EF6C00',
    800: '#E6732A',  // 深橙强调
    900: '#BF360C',
    main: '#FF8C42',
    light: '#FFB366',
    dark: '#E6732A',
    contrastText: '#FFFFFF',
  },

  // 4. 风险红 (Risk Red) - 危险状态
  error: {
    50: '#FFEBEE',
    100: '#FFCDD2',
    200: '#EF9A9A',
    300: '#E57373',
    400: '#EC7063',  // 浅红辅助
    500: '#E74C3C',  // 警示红主色
    600: '#E53935',
    700: '#D32F2F',
    800: '#C0392B',  // 深红强调
    900: '#B71C1C',
    main: '#E74C3C',
    light: '#EC7063',
    dark: '#C0392B',
    contrastText: '#FFFFFF',
  },

  // 5. 数据紫 (Data Purple) - 分析功能
  secondary: {
    50: '#F3E5F5',
    100: '#E1BEE7',
    200: '#CE93D8',
    300: '#BA68C8',
    400: '#BB8FCE',  // 浅紫辅助
    500: '#8E44AD',  // 神秘紫主色
    600: '#8E24AA',
    700: '#7B1FA2',
    800: '#6C3483',  // 深紫强调
    900: '#4A148C',
    main: '#8E44AD',
    light: '#BB8FCE',
    dark: '#6C3483',
    contrastText: '#FFFFFF',
  },

  // 6. 信息青 (Info Cyan) - 信息提示
  info: {
    50: '#E0F7FA',
    100: '#B2EBF2',
    200: '#80DEEA',
    300: '#4DD0E1',
    400: '#5DADE2',  // 浅青辅助
    500: '#17A2B8',  // 清新青主色
    600: '#0097A7',
    700: '#00838F',
    800: '#138496',  // 深青强调
    900: '#006064',
    main: '#17A2B8',
    light: '#5DADE2',
    dark: '#138496',
    contrastText: '#FFFFFF',
  },

  // 中性色系统
  grey: {
    50: '#F8FAFC',   // 极浅灰蓝
    100: '#F1F5F9',  // 浅灰蓝
    200: '#E2E8F0',  // 浅灰
    300: '#CBD5E0',  // 中浅灰
    400: '#A0AEC0',  // 中灰
    500: '#718096',  // 标准灰
    600: '#4A5568',  // 深灰
    700: '#2D3748',  // 深灰蓝
    800: '#1A202C',  // 极深灰
    900: '#171923',  // 最深灰
  },

  // 背景色系统
  background: {
    default: '#F8FAFC',      // 主背景 - 极浅灰蓝
    paper: '#FFFFFF',        // 卡片背景 - 纯白
    dark: '#1A202C',         // 深色背景
    surface: '#F1F5F9',      // 表面色
    overlay: 'rgba(26, 32, 44, 0.6)', // 遮罩层
  },

  // 文字色系统
  text: {
    primary: '#2D3748',      // 主要文字 - 深灰蓝
    secondary: '#718096',    // 次要文字 - 中灰
    disabled: '#A0AEC0',     // 禁用文字 - 浅灰
    inverse: '#FFFFFF',      // 反色文字 - 白色
    hint: '#CBD5E0',         // 提示文字
  },

  // 边框色系统
  border: {
    light: '#E2E8F0',       // 浅色边框
    medium: '#CBD5E0',      // 中色边框
    dark: '#A0AEC0',        // 深色边框
    focus: '#4A90E2',       // 聚焦边框
  },

  // 状态色彩 - 用于表格行、卡片状态等
  status: {
    compliant: {
      bg: 'rgba(0, 179, 134, 0.1)',     // 合规背景
      border: 'rgba(0, 179, 134, 0.3)', // 合规边框
      text: '#008B5A',                  // 合规文字
    },
    risk: {
      bg: 'rgba(231, 76, 60, 0.1)',     // 风险背景
      border: 'rgba(231, 76, 60, 0.3)', // 风险边框
      text: '#C0392B',                  // 风险文字
    },
    warning: {
      bg: 'rgba(255, 140, 66, 0.1)',    // 警告背景
      border: 'rgba(255, 140, 66, 0.3)', // 警告边框
      text: '#E6732A',                  // 警告文字
    },
    analyzing: {
      bg: 'rgba(142, 68, 173, 0.1)',    // 分析中背景
      border: 'rgba(142, 68, 173, 0.3)', // 分析中边框
      text: '#6C3483',                  // 分析中文字
    },
    pending: {
      bg: 'rgba(113, 128, 150, 0.1)',   // 待处理背景
      border: 'rgba(113, 128, 150, 0.3)', // 待处理边框
      text: '#4A5568',                  // 待处理文字
    },
  },
};

// 深色模式色彩配置
export const bedrockDarkColors = {
  ...bedrockColors,
  
  // 深色模式背景调整
  background: {
    default: '#0F172A',      // 深色主背景
    paper: '#1E293B',        // 深色卡片背景
    dark: '#020617',         // 更深背景
    surface: '#334155',      // 深色表面
    overlay: 'rgba(15, 23, 42, 0.8)', // 深色遮罩
  },

  // 深色模式文字调整
  text: {
    primary: '#F8FAFC',      // 深色模式主文字
    secondary: '#CBD5E0',    // 深色模式次要文字
    disabled: '#64748B',     // 深色模式禁用文字
    inverse: '#1A202C',      // 深色模式反色文字
    hint: '#94A3B8',         // 深色模式提示文字
  },

  // 深色模式边框调整
  border: {
    light: 'rgba(255, 255, 255, 0.1)',  // 深色浅边框
    medium: 'rgba(255, 255, 255, 0.2)', // 深色中边框
    dark: 'rgba(255, 255, 255, 0.3)',   // 深色深边框
    focus: '#60A5FA',                   // 深色聚焦边框
  },
};

// 图表专用色彩配置
export const chartColors = {
  primary: ['#0052CC', '#4A90E2', '#7BB3F0', '#A8CCF5', '#D4E6FA'],
  success: ['#00B386', '#4ECDC4', '#7EDDD8', '#A8E6E1', '#D1F0ED'],
  warning: ['#FF8C42', '#FFB366', '#FFC999', '#FFD9B3', '#FFE6CC'],
  error: ['#E74C3C', '#EC7063', '#F1948A', '#F5B7B1', '#FADBD8'],
  purple: ['#8E44AD', '#BB8FCE', '#D7BDE2', '#E8DAEF', '#F4ECF7'],
  cyan: ['#17A2B8', '#5DADE2', '#85C1E9', '#AED6F1', '#D6EAF8'],
  gradient: {
    primary: 'linear-gradient(135deg, #0052CC 0%, #4A90E2 100%)',
    success: 'linear-gradient(135deg, #00B386 0%, #4ECDC4 100%)',
    warning: 'linear-gradient(135deg, #FF8C42 0%, #FFB366 100%)',
    error: 'linear-gradient(135deg, #E74C3C 0%, #EC7063 100%)',
    purple: 'linear-gradient(135deg, #8E44AD 0%, #BB8FCE 100%)',
    cyan: 'linear-gradient(135deg, #17A2B8 0%, #5DADE2 100%)',
  }
};

export default bedrockColors;
