import { PaletteOptions } from '@mui/material/styles';
import { bedrockColors, bedrockDarkColors } from './bedrock/colors';

/**
 * Color palette configuration for the application
 * Enhanced with Bedrock Data Compliance System colors
 */
export const lightPalette: PaletteOptions = {
  mode: 'light',
  primary: {
    main: bedrockColors.primary.main, // 磐石蓝
    light: bedrockColors.primary.light,
    dark: bedrockColors.primary.dark,
    contrastText: bedrockColors.primary.contrastText,
  },
  secondary: {
    main: bedrockColors.secondary.main, // 数据紫
    light: bedrockColors.secondary.light,
    dark: bedrockColors.secondary.dark,
    contrastText: bedrockColors.secondary.contrastText,
  },
  error: {
    main: bedrockColors.error.main, // 风险红
    light: bedrockColors.error.light,
    dark: bedrockColors.error.dark,
    contrastText: bedrockColors.error.contrastText,
  },
  warning: {
    main: bedrockColors.warning.main, // 警告橙
    light: bedrockColors.warning.light,
    dark: bedrockColors.warning.dark,
    contrastText: bedrockColors.warning.contrastText,
  },
  info: {
    main: bedrockColors.info.main, // 信息青
    light: bedrockColors.info.light,
    dark: bedrockColors.info.dark,
    contrastText: bedrockColors.info.contrastText,
  },
  success: {
    main: bedrockColors.success.main, // 合规绿
    light: bedrockColors.success.light,
    dark: bedrockColors.success.dark,
    contrastText: bedrockColors.success.contrastText,
  },
  grey: bedrockColors.grey,
  background: {
    default: bedrockColors.background.default,
    paper: bedrockColors.background.paper,
  },
  text: {
    primary: bedrockColors.text.primary,
    secondary: bedrockColors.text.secondary,
    disabled: bedrockColors.text.disabled,
  },
  divider: 'rgba(0, 0, 0, 0.08)',
  action: {
    active: '#6b7280',
    hover: 'rgba(0, 0, 0, 0.04)',
    selected: 'rgba(0, 0, 0, 0.08)',
    disabled: '#9ca3af',
    disabledBackground: 'rgba(0, 0, 0, 0.12)',
  },
};

export const darkPalette: PaletteOptions = {
  mode: 'dark',
  primary: {
    main: bedrockDarkColors.primary.main, // 磐石蓝深色版
    light: bedrockDarkColors.primary.light,
    dark: bedrockDarkColors.primary.dark,
    contrastText: bedrockDarkColors.primary.contrastText,
  },
  secondary: {
    main: bedrockDarkColors.secondary.main, // 数据紫深色版
    light: bedrockDarkColors.secondary.light,
    dark: bedrockDarkColors.secondary.dark,
    contrastText: bedrockDarkColors.secondary.contrastText,
  },
  error: {
    main: bedrockDarkColors.error.main,
    light: bedrockDarkColors.error.light,
    dark: bedrockDarkColors.error.dark,
    contrastText: bedrockDarkColors.error.contrastText,
  },
  warning: {
    main: bedrockDarkColors.warning.main,
    light: bedrockDarkColors.warning.light,
    dark: bedrockDarkColors.warning.dark,
    contrastText: bedrockDarkColors.warning.contrastText,
  },
  info: {
    main: bedrockDarkColors.info.main,
    light: bedrockDarkColors.info.light,
    dark: bedrockDarkColors.info.dark,
    contrastText: bedrockDarkColors.info.contrastText,
  },
  success: {
    main: bedrockDarkColors.success.main,
    light: bedrockDarkColors.success.light,
    dark: bedrockDarkColors.success.dark,
    contrastText: bedrockDarkColors.success.contrastText,
  },
  grey: bedrockDarkColors.grey,
  background: {
    default: bedrockDarkColors.background.default,
    paper: bedrockDarkColors.background.paper,
  },
  text: {
    primary: bedrockDarkColors.text.primary,
    secondary: bedrockDarkColors.text.secondary,
    disabled: bedrockDarkColors.text.disabled,
  },
  divider: 'rgba(255, 255, 255, 0.12)',
  action: {
    active: '#cbd5e1',
    hover: 'rgba(255, 255, 255, 0.08)',
    selected: 'rgba(255, 255, 255, 0.12)',
    disabled: '#64748b',
    disabledBackground: 'rgba(255, 255, 255, 0.12)',
  },
};