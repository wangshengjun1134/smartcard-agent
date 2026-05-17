import { DragEvent, useState } from 'react';
import { FileNode } from '../../types/file';
import { FileIcon } from './FileIcon';

interface FileIconItemProps {
  file: FileNode;
  onClick: (file: FileNode) => void;
  onDoubleClick?: (file: FileNode) => void;
  selected?: boolean;
  onDragStart?: (file: FileNode) => void;
  onDragEnd?: () => void;
  onDrop?: (draggedFile: FileNode, targetFolder: FileNode) => void;
}

/**
 * 图标视图中的单个文件项组件
 * 支持拖拽到文件夹
 */
export function FileIconItem({
  file,
  onClick,
  onDoubleClick,
  selected = false,
  onDragStart,
  onDragEnd,
  onDrop,
}: FileIconItemProps) {
  const [isDragOver, setIsDragOver] = useState(false);

  // 开始拖拽
  const handleDragStart = (e: DragEvent<HTMLDivElement>) => {
    e.dataTransfer.setData('application/json', JSON.stringify({
      id: file.id,
      name: file.name,
      path: file.path,
      type: file.type,
      isFolder: file.isFolder
    }));
    e.dataTransfer.effectAllowed = 'move';
    onDragStart?.(file);
  };

  // 结束拖拽
  const handleDragEnd = () => {
    onDragEnd?.();
  };

  // 拖拽进入目标
  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    if (file.isFolder) {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(true);
    }
  };

  // 拖拽在目标上方移动
  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    if (file.isFolder) {
      e.preventDefault();
      e.stopPropagation();
      e.dataTransfer.dropEffect = 'move';
    }
  };

  // 拖拽离开目标
  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  // 放置到目标
  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (file.isFolder) {
      try {
        const data = e.dataTransfer.getData('application/json');
        if (data) {
          const draggedFile = JSON.parse(data) as FileNode;
          if (draggedFile.id !== file.id && !draggedFile.isFolder) {
            // 只允许文件拖入文件夹，不允许文件夹拖入文件夹
            onDrop?.(draggedFile, file);
          }
        }
      } catch {
        // 忽略解析错误
      }
    }
  };

  // 组合类名
  const classNames = [
    'file-icon-item',
    selected ? 'selected' : '',
    isDragOver ? 'drag-over' : '',
  ].filter(Boolean).join(' ');

  return (
    <div
      className={classNames}
      onClick={() => onClick(file)}
      onDoubleClick={() => onDoubleClick?.(file)}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      draggable={true}
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