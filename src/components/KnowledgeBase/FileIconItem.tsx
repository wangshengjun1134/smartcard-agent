import { FileNode } from '../../types/file';
import { FileIcon } from './FileIcon';

interface FileIconItemProps {
  file: FileNode;
  onClick: (file: FileNode) => void;
  onDoubleClick?: (file: FileNode) => void;
  selected?: boolean;
}

/**
 * 图标视图中的单个文件项组件
 * 类似 Windows 中图标样式
 * - 单击: 选中
 * - 双击: 文件夹进入 / 文件打开抽屉
 */
export function FileIconItem({ file, onClick, onDoubleClick, selected = false }: FileIconItemProps) {
  return (
    <div
      className={`file-icon-item ${selected ? 'selected' : ''}`}
      onClick={() => onClick(file)}
      onDoubleClick={() => onDoubleClick?.(file)}
      role="button"
      tabIndex={0}
      aria-selected={selected}
    >
      <div className="file-icon">
        <FileIcon type={file.type} size="lg" />
      </div>
      <div className="file-name">
        {file.name}
      </div>
    </div>
  );
}