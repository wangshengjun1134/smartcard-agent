/**
 * 主题检测和管理工具
 * 提供统一的主题检测和切换逻辑
 */

/**
 * 检测当前是否为深色模式
 * @returns 是否为深色模式
 */
export function isDarkMode(): boolean {
  return document.documentElement.classList.contains('dark');
}

/**
 * 设置主题模式
 * @param isDark 是否为深色模式
 */
export function setThemeMode(isDark: boolean): void {
  if (isDark) {
    document.documentElement.classList.add('dark');
    localStorage.setItem('theme', 'dark');
  } else {
    document.documentElement.classList.remove('dark');
    localStorage.setItem('theme', 'light');
  }
}

/**
 * 切换主题模式
 * @returns 切换后的模式（true表示深色）
 */
export function toggleTheme(): boolean {
  const newIsDark = !isDarkMode();
  setThemeMode(newIsDark);
  return newIsDark;
}

/**
 * 初始化主题
 * 从localStorage或系统偏好加载主题设置
 */
export function initializeTheme(): void {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark') {
    setThemeMode(true);
  } else if (savedTheme === 'light') {
    setThemeMode(false);
  } else {
    // 检查系统偏好
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    setThemeMode(prefersDark);
  }
}

/**
 * 获取系统主题偏好
 * @returns 系统是否偏好深色模式
 */
export function getSystemThemePreference(): boolean {
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

/**
 * 主题变更回调类型
 */
type ThemeChangeCallback = (isDark: boolean) => void;

/**
 * 监听主题变更
 * @param callback 主题变更回调
 * @returns 取消监听的函数
 */
export function watchThemeChange(callback: ThemeChangeCallback): () => void {
  // 监听DOM class变化
  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.attributeName === 'class') {
        callback(isDarkMode());
      }
    }
  });

  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class'],
  });

  // 监听系统偏好变化
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  const handleMediaChange = (e: MediaQueryListEvent) => {
    if (!localStorage.getItem('theme')) {
      setThemeMode(e.matches);
      callback(e.matches);
    }
  };
  mediaQuery.addEventListener('change', handleMediaChange);

  // 返回取消函数
  return () => {
    observer.disconnect();
    mediaQuery.removeEventListener('change', handleMediaChange);
  };
}

/**
 * 高亮代码样式URL配置
 */
const HLJS_THEME_LIGHT = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/styles/github.min.css';
const HLJS_THEME_DARK = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/styles/github-dark.min.css';
const HLJS_THEME_LINK_ID = 'hljs-theme';

/**
 * 加载或更新代码高亮主题样式
 * @param isDark 是否为深色模式
 */
export function loadHighlightTheme(isDark: boolean): void {
  const themeUrl = isDark ? HLJS_THEME_DARK : HLJS_THEME_LIGHT;
  const existingLink = document.getElementById(HLJS_THEME_LINK_ID) as HTMLLinkElement;

  if (existingLink) {
    // 已存在link元素，仅更新URL
    existingLink.href = themeUrl;
  } else {
    // 创建新的link元素
    const link = document.createElement('link');
    link.id = HLJS_THEME_LINK_ID;
    link.rel = 'stylesheet';
    link.href = themeUrl;
    document.head.appendChild(link);
  }
}

/**
 * 确保高亮样式已加载（单次加载）
 * 使用缓存避免重复加载
 */
let hljsThemeLoaded = false;
let currentHljsTheme: boolean | null = null;

export function ensureHighlightThemeLoaded(isDark: boolean): void {
  // 如果已加载且主题匹配，跳过
  if (hljsThemeLoaded && currentHljsTheme === isDark) {
    return;
  }

  loadHighlightTheme(isDark);
  hljsThemeLoaded = true;
  currentHljsTheme = isDark;
}