import { PaletteOptions } from '@mui/material/styles';

/**
 * Color palette configuration for the application
 */
export const lightPalette: PaletteOptions = {
  mode: 'light',
  primary: {
    main: '#2563eb', // Blue-600
    light: '#60a5fa', // Blue-400
    dark: '#1e40af', // Blue-800
    contrastText: '#ffffff',
  },
  secondary: {
    main: '#8b5cf6', // Violet-500
    light: '#a78bfa', // Violet-400
    dark: '#6d28d9', // Violet-700
    contrastText: '#ffffff',
  },
  error: {
    main: '#ef4444', // Red-500
    light: '#f87171', // Red-400
    dark: '#dc2626', // Red-600
    contrastText: '#ffffff',
  },
  warning: {
    main: '#f59e0b', // Amber-500
    light: '#fbbf24', // Amber-400
    dark: '#d97706', // Amber-600
    contrastText: '#000000',
  },
  info: {
    main: '#06b6d4', // Cyan-500
    light: '#22d3ee', // Cyan-400
    dark: '#0891b2', // Cyan-600
    contrastText: '#ffffff',
  },
  success: {
    main: '#10b981', // Emerald-500
    light: '#34d399', // Emerald-400
    dark: '#059669', // Emerald-600
    contrastText: '#ffffff',
  },
  grey: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  },
  background: {
    default: '#f9fafb',
    paper: '#ffffff',
  },
  text: {
    primary: '#111827',
    secondary: '#6b7280',
    disabled: '#9ca3af',
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
    main: '#60a5fa', // Blue-400
    light: '#93c5fd', // Blue-300
    dark: '#2563eb', // Blue-600
    contrastText: '#000000',
  },
  secondary: {
    main: '#a78bfa', // Violet-400
    light: '#c4b5fd', // Violet-300
    dark: '#8b5cf6', // Violet-500
    contrastText: '#000000',
  },
  error: {
    main: '#f87171', // Red-400
    light: '#fca5a5', // Red-300
    dark: '#ef4444', // Red-500
    contrastText: '#000000',
  },
  warning: {
    main: '#fbbf24', // Amber-400
    light: '#fcd34d', // Amber-300
    dark: '#f59e0b', // Amber-500
    contrastText: '#000000',
  },
  info: {
    main: '#22d3ee', // Cyan-400
    light: '#67e8f9', // Cyan-300
    dark: '#06b6d4', // Cyan-500
    contrastText: '#000000',
  },
  success: {
    main: '#34d399', // Emerald-400
    light: '#6ee7b7', // Emerald-300
    dark: '#10b981', // Emerald-500
    contrastText: '#000000',
  },
  grey: {
    50: '#111827',
    100: '#1f2937',
    200: '#374151',
    300: '#4b5563',
    400: '#6b7280',
    500: '#9ca3af',
    600: '#d1d5db',
    700: '#e5e7eb',
    800: '#f3f4f6',
    900: '#f9fafb',
  },
  background: {
    default: '#0f172a',
    paper: '#1e293b',
  },
  text: {
    primary: '#f9fafb',
    secondary: '#cbd5e1',
    disabled: '#64748b',
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