import { ViewMode } from '../../types/file';

interface ViewToggleButtonProps {
  mode: ViewMode;
  onChange: (mode: ViewMode) => void;
}

/**
 * 视图模式切换按钮组件
 * 显示当前模式对应图标，点击切换
 */
export function ViewToggleButton({ mode, onChange }: ViewToggleButtonProps) {
  const handleClick = () => {
    const nextMode: ViewMode = mode === 'icon' ? 'tree' : 'icon';
    onChange(nextMode);
  };

  return (
    <button
      className="circle-btn w-[28px] h-[28px] dark:text-[#a0a0a0] dark:hover:bg-[#333333]"
      onClick={handleClick}
      title={mode === 'icon' ? '切换为树状视图' : '切换为图标视图'}
      aria-label={`切换为${mode === 'icon' ? '树状' : '图标'}视图`}
    >
      {mode === 'icon' ? (
        // 图标视图时显示树状图标 (可切换到树状)
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
        </svg>
      ) : (
        // 树状视图时显示网格图标 (可切换到图标)
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
        </svg>
      )}
    </button>
  );
}