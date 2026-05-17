import { ViewMode } from '../../types/file';
import { ViewToggleButton } from './ViewToggleButton';

interface KnowledgeBaseHeaderProps {
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  onAddClick: () => void;
  onCreateFolder: () => void;
}

/**
 * 知识库页面顶部栏组件
 * 包含新建文件夹、视图切换和添加文件按钮
 */
export function KnowledgeBaseHeader({ 
  viewMode, 
  onViewModeChange, 
  onAddClick,
  onCreateFolder 
}: KnowledgeBaseHeaderProps) {
  return (
    <header className="flex items-center justify-end px-6 h-[45px] bg-[#f7f7f9] dark:bg-[#111112] border-b border-[#ececee] dark:border-[#333333] flex-shrink-0">
      {/* 右侧：按钮组 */}
      <div className="flex items-center gap-2">
        {/* 新建文件夹按钮 */}
        <button
          onClick={onCreateFolder}
          className="circle-btn w-[28px] h-[28px] text-[#666] dark:text-[#a0a0a0] hover:bg-[#ececee] dark:hover:bg-[#333333]"
          title="新建文件夹"
          aria-label="新建文件夹"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
        </button>

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