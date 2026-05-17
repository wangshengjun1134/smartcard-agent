import { FileNode } from '../../types/file';
import { FileIconItem } from './FileIconItem';

interface FileGridViewProps {
  files: FileNode[];
  selectedFileId: string | null;
  onFileClick: (file: FileNode) => void;
  onDoubleClick: (file: FileNode) => void;
}

/**
 * 图标视图网格布局组件
 * 使用 CSS Grid 实现响应式布局
 */
export function FileGridView({ files, selectedFileId, onFileClick, onDoubleClick }: FileGridViewProps) {
  return (
    <div className="file-grid">
      {files.map((file) => (
        <FileIconItem
          key={file.id}
          file={file}
          onClick={onFileClick}
          onDoubleClick={onDoubleClick}
          selected={selectedFileId === file.id}
        />
      ))}
    </div>
  );
}