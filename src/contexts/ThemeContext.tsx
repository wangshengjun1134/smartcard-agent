import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { isDarkMode, setThemeMode, initializeTheme, watchThemeChange } from '../utils/theme';

interface ThemeContextType {
  isDarkMode: boolean;
  toggleDarkMode: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  // 初始化时从本地存储或系统偏好加载主题
  useEffect(() => {
    initializeTheme();
  }, []);

  // 监听主题变化，更新状态
  const [darkMode, setDarkModeState] = useState(isDarkMode());
  
  useEffect(() => {
    const unwatch = watchThemeChange((isDark) => {
      setDarkModeState(isDark);
    });
    return unwatch;
  }, []);

  const toggleDarkMode = () => {
    const newIsDark = !darkMode;
    setThemeMode(newIsDark);
    setDarkModeState(newIsDark);
  };

  return (
    <ThemeContext.Provider value={{ isDarkMode: darkMode, toggleDarkMode }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}