import { useState, useEffect, ReactNode } from 'react';

interface AppLayoutProps {
  sidebar: ReactNode;
  main: ReactNode;
  sidebarOpen?: boolean;
  onToggleSidebar?: () => void;
}

export function AppLayout({ sidebar, main, sidebarOpen: externalSidebarOpen, onToggleSidebar: externalToggleSidebar }: AppLayoutProps) {
  const [internalSidebarOpen, setInternalSidebarOpen] = useState(true);
  const [isMobile, setIsMobile] = useState(false);

  // 使用外部状态或内部状态
  const sidebarOpen = externalSidebarOpen !== undefined ? externalSidebarOpen : internalSidebarOpen;
  const toggleSidebar = externalToggleSidebar || (() => setInternalSidebarOpen(prev => !prev));

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
      if (window.innerWidth < 768 && externalSidebarOpen === undefined) {
        setInternalSidebarOpen(false);
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, [externalSidebarOpen]);

  return (
    <div className="flex h-screen w-full bg-[#f7f7f9] dark:bg-[#111112] overflow-hidden">
      {/* 侧边栏 */}
      {sidebarOpen && (
        <div className={`${isMobile ? 'absolute z-20 h-full' : 'relative'}`}>
          {sidebar}
        </div>
      )}

      {/* 移动端遮罩层 */}
      {isMobile && sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-10"
          onClick={toggleSidebar}
          aria-hidden="true"
        />
      )}

      {/* 主内容区 - 圆角设计 */}
      <div className="flex-1 flex flex-col h-full m-2 rounded-xl overflow-hidden bg-white dark:bg-[#222222] shadow-sm">
        {main}
      </div>
    </div>
  );
}