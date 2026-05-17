import { getCurrentWindow } from '@tauri-apps/api/window';

/**
 * 自定义标题栏组件
 * 提供窗口拖拽区域和控制按钮
 */
export function TitleBar() {
  const appWindow = getCurrentWindow();

  // 最小化
  const handleMinimize = async (e: React.MouseEvent) => {
    e.stopPropagation();
    await appWindow.minimize();
  };

  // 最大化/还原
  const handleMaximize = async (e: React.MouseEvent) => {
    e.stopPropagation();
    await appWindow.toggleMaximize();
  };

  // 关闭
  const handleClose = async (e: React.MouseEvent) => {
    e.stopPropagation();
    await appWindow.close();
  };

  return (
    <div 
      className="flex items-center justify-between h-[32px] bg-[#f7f7f9] dark:bg-[#111112] select-none flex-shrink-0 pl-2"
      data-tauri-drag-region
    >
      {/* 左侧空白区域 - 用于拖拽 */}
      <div className="flex-1" data-tauri-drag-region />

      {/* 窗口控制按钮 */}
      <div className="flex items-center">
        {/* 最小化 */}
        <button
          onClick={handleMinimize}
          className="w-[46px] h-[32px] flex items-center justify-center hover:bg-[#e5e5e5] dark:hover:bg-[#2a2a2a] transition-colors"
          aria-label="最小化"
        >
          <svg className="w-[10px] h-[10px] text-[#333] dark:text-[#ccc]" viewBox="0 0 10 10">
            <path d="M 0 5 L 10 5" stroke="currentColor" strokeWidth="1" />
          </svg>
        </button>

        {/* 最大化 */}
        <button
          onClick={handleMaximize}
          className="w-[46px] h-[32px] flex items-center justify-center hover:bg-[#e5e5e5] dark:hover:bg-[#2a2a2a] transition-colors"
          aria-label="最大化"
        >
          <svg className="w-[10px] h-[10px] text-[#333] dark:text-[#ccc]" viewBox="0 0 10 10">
            <rect x="0.5" y="0.5" width="9" height="9" stroke="currentColor" strokeWidth="1" fill="none" />
          </svg>
        </button>

        {/* 关闭 */}
        <button
          onClick={handleClose}
          className="w-[46px] h-[32px] flex items-center justify-center hover:bg-[#e81123] group transition-colors"
          aria-label="关闭"
        >
          <svg className="w-[10px] h-[10px] text-[#333] dark:text-[#ccc] group-hover:text-white" viewBox="0 0 10 10">
            <path d="M 0 0 L 10 10 M 10 0 L 0 10" stroke="currentColor" strokeWidth="1" />
          </svg>
        </button>
      </div>
    </div>
  );
}