import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import { lightTheme, darkTheme } from '@/theme';

type ThemeMode = 'light' | 'dark' | 'system';

interface ThemeContextType {
  mode: ThemeMode;
  actualMode: 'light' | 'dark';
  toggleTheme: () => void;
  setThemeMode: (mode: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

/**
 * Get system preference for theme
 */
const getSystemTheme = (): 'light' | 'dark' => {
  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return 'light';
};

/**
 * Hook for managing theme state
 */
export const useThemeMode = () => {
  const [mode, setMode] = useState<ThemeMode>(() => {
    const savedMode = localStorage.getItem('themeMode') as ThemeMode;
    return savedMode || 'system';
  });

  const [actualMode, setActualMode] = useState<'light' | 'dark'>(() => {
    const savedMode = localStorage.getItem('themeMode') as ThemeMode;
    if (savedMode === 'system' || !savedMode) {
      return getSystemTheme();
    }
    return savedMode as 'light' | 'dark';
  });

  useEffect(() => {
    // Save theme preference
    localStorage.setItem('themeMode', mode);

    // Update actual mode based on preference
    if (mode === 'system') {
      const systemTheme = getSystemTheme();
      setActualMode(systemTheme);

      // Listen for system theme changes
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = (e: MediaQueryListEvent) => {
        setActualMode(e.matches ? 'dark' : 'light');
      };

      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    } else {
      setActualMode(mode as 'light' | 'dark');
    }
  }, [mode]);

  const toggleTheme = useCallback(() => {
    setMode((prevMode) => {
      if (prevMode === 'light') return 'dark';
      if (prevMode === 'dark') return 'system';
      return 'light';
    });
  }, []);

  const setThemeMode = useCallback((newMode: ThemeMode) => {
    setMode(newMode);
  }, []);

  return {
    mode,
    actualMode,
    toggleTheme,
    setThemeMode,
  };
};

/**
 * Theme Provider Component
 */
export const CustomThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const themeState = useThemeMode();
  const theme = themeState.actualMode === 'dark' ? darkTheme : lightTheme;

  return (
    <ThemeContext.Provider value={themeState}>
      <MuiThemeProvider theme={theme}>{children}</MuiThemeProvider>
    </ThemeContext.Provider>
  );
};

/**
 * Hook to use theme context
 */
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a CustomThemeProvider');
  }
  return context;
};