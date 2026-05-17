import { FileNode } from '../../types/file';

interface FileBasicInfoProps {
  file: FileNode;
}

/**
 * 文件基本信息展示组件
 * 显示文件类型、大小、创建时间、修改时间、路径
 */
export function FileBasicInfo({ file }: FileBasicInfoProps) {
  // 格式化文件大小
  const formatSize = (bytes?: number) => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  };

  // 获取文件类型显示名称
  const getTypeName = () => {
    const typeNames: Record<string, string> = {
      folder: '文件夹',
      pdf: 'PDF 文档',
      word: 'Word 文档',
      markdown: 'Markdown 文档',
      image: '图片',
      text: '文本文件',
      unknown: '未知类型',
    };
    return typeNames[file.type] || '未知类型';
  };

  return (
    <div className="info-section">
      <div className="section-title">基本信息</div>

      <div className="info-item">
        <div className="info-label">文件类型</div>
        <div className="info-value">{getTypeName()}</div>
      </div>

      <div className="info-item">
        <div className="info-label">文件大小</div>
        <div className="info-value">{formatSize(file.size)}</div>
      </div>

      <div className="info-item">
        <div className="info-label">创建时间</div>
        <div className="info-value">{file.createdAt || '-'}</div>
      </div>

      <div className="info-item">
        <div className="info-label">修改时间</div>
        <div className="info-value">{file.modifiedAt || '-'}</div>
      </div>

      <div className="info-item">
        <div className="info-label">文件路径</div>
        <div className="info-value text-[#4b6ef3]">{file.path}</div>
      </div>
    </div>
  );
}