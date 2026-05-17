import { ViewMode } from '../../types/file';
import { ViewToggleButton } from './ViewToggleButton';

interface KnowledgeBaseHeaderProps {
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  onAddClick: () => void;
}

/**
 * 知识库页面顶部栏组件
 * 包含视图切换按钮和添加文件按钮
 */
export function KnowledgeBaseHeader({ viewMode, onViewModeChange, onAddClick }: KnowledgeBaseHeaderProps) {
  return (
    <header className="flex items-center justify-between px-6 h-[45px] bg-white dark:bg-[#222222] border-b border-[#ececee] dark:border-[#333333] flex-shrink-0">
      {/* 左侧：标题 */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-[#1a1a1a] dark:text-white">
          知识库
        </span>
      </div>

      {/* 右侧：视图切换 + 添加按钮 */}
      <div className="flex items-center gap-2">
        {/* 视图切换按钮 */}
        <ViewToggleButton mode={viewMode} onChange={onViewModeChange} />

        {/* 添加文件按钮 */}
        <button
          onClick={onAddClick}
          className="circle-btn w-[28px] h-[28px] bg-[#4b6ef3]/10 text-[#4b6ef3] hover:bg-[#4b6ef3]/20 dark:bg-[#4b6ef3]/20 dark:text-[#4b6ef3] dark:hover:bg-[#4b6ef3]/30"
          title="添加知识"
          aria-label="添加知识"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </div>
    </header>
  );
}