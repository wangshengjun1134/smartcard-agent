import { useState, useRef, DragEvent, ChangeEvent } from 'react';

interface FileUploadZoneProps {
  file: File | null;
  fileHash: string;
  isCalculatingHash: boolean;
  onFileSelect: (file: File) => void;
  onClearFile: () => void;
}

/**
 * 获取文件类型图标
 */
function getFileIcon(fileName: string): string {
  const ext = fileName.split('.').pop()?.toLowerCase() || '';

  if (ext === 'pdf') return '📄';
  if (['doc', 'docx'].includes(ext)) return '📝';
  if (['md', 'markdown'].includes(ext)) return '📝';
  if (['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg'].includes(ext)) return '🖼️';
  if (['txt', 'csv', 'json'].includes(ext)) return '📄';

  return '📄';
}

/**
 * 格式化文件大小
 */
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

/**
 * 文件拖拽上传区域组件
 */
export function FileUploadZone({
  file,
  fileHash,
  isCalculatingHash,
  onFileSelect,
  onClearFile,
}: FileUploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 处理拖拽进入
  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  // 处理拖拽离开
  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  // 处理拖拽放置
  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const droppedFile = files[0];
      // 验证文件类型
      const validExtensions = ['pdf', 'doc', 'docx', 'md', 'txt', 'png', 'jpg', 'jpeg'];
      const ext = droppedFile.name.split('.').pop()?.toLowerCase() || '';
      if (validExtensions.includes(ext) || droppedFile.type.startsWith('image/')) {
        onFileSelect(droppedFile);
      }
    }
  };

  // 处理点击选择文件
  const handleClick = () => {
    if (!file) {
      fileInputRef.current?.click();
    }
  };

  // 处理文件选择
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onFileSelect(files[0]);
    }
    // 清空 input 值以便重复选择同一文件
    e.target.value = '';
  };

  // 处理清除文件
  const handleClearClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onClearFile();
  };

  return (
    <div
      className={`upload-zone relative flex flex-col items-center justify-center p-6 border-2 rounded-xl cursor-pointer transition-all ${
        file
          ? 'border-solid border-[#4b6ef3] bg-[#4b6ef3]/5'
          : isDragOver
          ? 'border-dashed border-[#4b6ef3] bg-[#4b6ef3]/10'
          : 'border-dashed border-[#ececee] dark:border-[#333333] bg-transparent hover:border-[#4b6ef3]/50'
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      {/* 隐藏的文件输入 */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.doc,.docx,.md,.txt,.png,.jpg,.jpeg"
        onChange={handleFileChange}
        className="hidden"
      />

      {/* 已选文件信息 */}
      {file ? (
        <div className="file-info flex items-center gap-3 w-full">
          {/* 文件图标 */}
          <div className="file-icon w-[40px] h-[40px] flex items-center justify-center text-[24px]">
            {getFileIcon(file.name)}
          </div>

          {/* 文件详情 */}
          <div className="file-details flex-1 min-w-0">
            <div className="file-name text-[13px] font-medium text-[#1a1a1a] dark:text-white truncate">
              {file.name}
            </div>
            <div className="file-size text-[12px] text-[#999] dark:text-[#808080]">
              {formatFileSize(file.size)}
            </div>
            {/* 哈希值 */}
            <div className="file-hash text-[11px] text-[#999] dark:text-[#808080] font-mono mt-1">
              {isCalculatingHash ? (
                <span className="text-[#4b6ef3]">计算哈希中...</span>
              ) : fileHash ? (
                `SHA-256: ${fileHash.slice(0, 16)}...`
              ) : null}
            </div>
          </div>

          {/* 清除按钮 */}
          <button
            type="button"
            className="clear-btn w-[28px] h-[28px] flex items-center justify-center rounded-full bg-[#f7f8fa] dark:bg-[#333333] text-[#999] dark:text-[#808080] hover:bg-[#ececee] dark:hover:bg-[#404040] transition-colors"
            onClick={handleClearClick}
            aria-label="清除文件"
          >
            ×
          </button>
        </div>
      ) : (
        <>
          {/* 上传图标 */}
          <div className="upload-icon w-[48px] h-[48px] flex items-center justify-center mb-3">
            <svg
              className="w-10 h-10 text-[#999] dark:text-[#808080]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>

          {/* 提示文字 */}
          <div className="upload-text text-[14px] text-[#1a1a1a] dark:text-white mb-1">
            拖拽文件到此处或点击上传
          </div>
          <div className="upload-hint text-[12px] text-[#999] dark:text-[#808080]">
            支持格式: PDF, Word, Markdown, TXT, 图片
          </div>
        </>
      )}
    </div>
  );
}