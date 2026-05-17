import { useEffect, useRef } from 'react';
import { useTheme } from '../../contexts/ThemeContext';

interface UserMenuProps {
  isOpen: boolean;
  onClose: () => void;
  bottom: number;
  onOpenSettings: () => void;
}

export function UserMenu({ isOpen, onClose, bottom, onOpenSettings }: UserMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);
  const { isDarkMode, toggleDarkMode } = useTheme();

  // 点击外部关闭
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  // ESC 关闭
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      ref={menuRef}
      className="absolute left-4 right-4 bg-white dark:bg-[#222222] rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.02)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.3)] p-2 flex flex-col z-50"
      style={{
        bottom: `${bottom + 8}px`,
      }}
    >
      {/* 设置 */}
      <div
        className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-[#1a1a1a] dark:text-white cursor-pointer hover:bg-[#f7f8fa] dark:hover:bg-[#333333] transition-colors"
        onClick={() => {
          onClose();
          onOpenSettings();
        }}
      >
        <i className="fa-solid fa-gear text-lg w-6 text-center text-[#4a4a4a] dark:text-[#a0a0a0]"></i>
        <span>设置</span>
      </div>

      {/* 深色/浅色模式 */}
      <div
        className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-[#1a1a1a] dark:text-white cursor-pointer hover:bg-[#f7f8fa] dark:hover:bg-[#333333] transition-colors"
        onClick={toggleDarkMode}
      >
        {isDarkMode ? (
          <>
            <i className="fa-regular fa-sun text-lg w-6 text-center text-[#4a4a4a] dark:text-[#a0a0a0]"></i>
            <span>浅色模式</span>
          </>
        ) : (
          <>
            <i className="fa-regular fa-moon text-lg w-6 text-center text-[#4a4a4a] dark:text-[#a0a0a0]"></i>
            <span>深色模式</span>
          </>
        )}
      </div>

      {/* 客服中心 */}
      <div
        className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-[#1a1a1a] dark:text-white cursor-pointer hover:bg-[#f7f8fa] dark:hover:bg-[#333333] transition-colors"
        onClick={onClose}
      >
        <i className="fa-regular fa-headset text-lg w-6 text-center text-[#4a4a4a] dark:text-[#a0a0a0]"></i>
        <span>客服中心</span>
      </div>

      {/* 分割线 */}
      <div className="h-px bg-[#f0f0f0] dark:bg-[#333333] mx-3 my-1" />

      {/* 退出登录 */}
      <div
        className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-[#ff4d4f] cursor-pointer hover:bg-[#f7f8fa] dark:hover:bg-[#333333] transition-colors"
        onClick={onClose}
      >
        <i className="fa-solid fa-arrow-right-from-bracket text-lg w-6 text-center"></i>
        <span>退出登录</span>
      </div>
    </div>
  );
}