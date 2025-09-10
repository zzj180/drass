import { createTheme, ThemeOptions } from '@mui/material/styles';
import { lightPalette, darkPalette } from './palette';
import { typography } from './typography';
import { components } from './components';

/**
 * Create a theme instance with the specified mode
 */
export const createAppTheme = (mode: 'light' | 'dark' = 'light') => {
  const themeOptions: ThemeOptions = {
    palette: mode === 'light' ? lightPalette : darkPalette,
    typography,
    components,
    shape: {
      borderRadius: 8,
    },
    spacing: 8,
    transitions: {
      easing: {
        easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
        easeOut: 'cubic-bezier(0.0, 0, 0.2, 1)',
        easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
        sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
      },
      duration: {
        shortest: 150,
        shorter: 200,
        short: 250,
        standard: 300,
        complex: 375,
        enteringScreen: 225,
        leavingScreen: 195,
      },
    },
  };

  return createTheme(themeOptions);
};

/**
 * Default light theme
 */
export const lightTheme = createAppTheme('light');

/**
 * Dark theme
 */
export const darkTheme = createAppTheme('dark');

/**
 * Default theme export (light mode)
 */
export const theme = lightTheme;