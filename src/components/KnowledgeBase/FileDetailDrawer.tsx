import { FileNode } from '../../types/file';
import { useFileDetail } from '../../hooks/useFileDetail';
import { useDialogClose } from '../../hooks/useDialog';
import { FileBasicInfo } from './FileBasicInfo';
import { VectorChunksList } from './VectorChunksList';

interface FileDetailDrawerProps {
  file: FileNode | null;
  isOpen: boolean;
  onClose: () => void;
}

/**
 * 文件详情抽屉组件
 * 从右侧滑入，显示文件信息和向量分片
 */
export function FileDetailDrawer({ file, isOpen, onClose }: FileDetailDrawerProps) {
  // 使用统一的对话框关闭Hook
  const drawerRef = useDialogClose<HTMLDivElement>(isOpen, onClose);
  
  // 获取文件详情
  const { detail, loading, error } = useFileDetail(file?.id || '');

  // 点击遮罩层关闭
  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!file) return null;

  return (
    <>
      {/* 遮罩层 */}
      {isOpen && (
        <div
          className="drawer-overlay"
          onClick={handleOverlayClick}
          aria-hidden="true"
        />
      )}

      {/* 抽屉主体 */}
      <div
        ref={drawerRef}
        className={`file-drawer ${isOpen ? 'open' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-label="文件详情"
      >
        {/* Header */}
        <div className="drawer-header">
          <div className="flex items-center gap-3">
            <span className="text-lg font-medium text-[#1a1a1a] dark:text-white">
              {file.name}
            </span>
          </div>
          <button
            className="w-[28px] h-[28px] rounded-full flex items-center justify-center hover:bg-[#f7f8fa] dark:hover:bg-[#333333] transition-colors"
            onClick={onClose}
            aria-label="关闭抽屉"
          >
            <svg className="w-4 h-4 text-[#999] dark:text-[#808080]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 内容区域 */}
        <div className="drawer-content">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-[#999] dark:text-[#808080]">加载中...</div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-[#ff4d4f]">加载失败: {error.message}</div>
            </div>
          ) : detail ? (
            <>
              {/* 基本信息 */}
              <FileBasicInfo file={detail} />

              {/* 向量分片 */}
              <VectorChunksList detail={detail} />
            </>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-[#999] dark:text-[#808080]">暂无数据</div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}