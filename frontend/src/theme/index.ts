import { createTheme, ThemeOptions } from '@mui/material/styles';
import { lightPalette, darkPalette } from './palette';
import { typography } from './typography';
import { components } from './components';
import { bedrockColors, bedrockDarkColors } from './bedrock/colors';
import { gradients } from './bedrock/gradients';
import { durations, easings } from './bedrock/animations';

/**
 * Create a theme instance with the specified mode
 */
export const createAppTheme = (mode: 'light' | 'dark' = 'light') => {
  const themeOptions: ThemeOptions = {
    palette: mode === 'light' ? lightPalette : darkPalette,
    typography,
    components,
    shape: {
      borderRadius: 12, // 增大圆角，更现代化
    },
    spacing: 8,
    transitions: {
      easing: {
        easeInOut: easings.easeInOut,
        easeOut: easings.easeOut,
        easeIn: easings.easeIn,
        sharp: easings.sharp,
      },
      duration: {
        shortest: durations.shortest,
        shorter: durations.shorter,
        short: durations.short,
        standard: durations.standard,
        complex: durations.complex,
        enteringScreen: durations.enteringScreen,
        leavingScreen: durations.leavingScreen,
      },
    },
  };

  return createTheme(themeOptions);
};

/**
 * Create Bedrock theme instance with enhanced styling
 */
export const createBedrockTheme = (mode: 'light' | 'dark' = 'light') => {
  const baseTheme = createAppTheme(mode);
  
  return createTheme({
    ...baseTheme,
    // 扩展主题以支持自定义属性
    customPalette: {
      bedrock: mode === 'light' ? bedrockColors : bedrockDarkColors,
      gradients,
    },
  });
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
 * Bedrock light theme
 */
export const bedrockLightTheme = createBedrockTheme('light');

/**
 * Bedrock dark theme
 */
export const bedrockDarkTheme = createBedrockTheme('dark');

/**
 * Default theme export (Bedrock light mode)
 */
export const theme = bedrockLightTheme;