import { useState, DragEvent } from 'react';
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
  isDropTarget?: boolean;
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
  isDropTarget = false
}: FileIconItemProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  // 开始拖拽
  const handleDragStart = (e: DragEvent<HTMLDivElement>) => {
    e.dataTransfer.setData('text/plain', JSON.stringify({
      id: file.id,
      name: file.name,
      path: file.path,
      isFolder: file.isFolder
    }));
    setIsDragging(true);
    onDragStart?.(file);
  };

  // 结束拖拽
  const handleDragEnd = () => {
    setIsDragging(false);
    onDragEnd?.();
  };

  // 拖拽进入 (仅文件夹可接收)
  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    if (file.isFolder) {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(true);
    }
  };

  // 拖拽离开
  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  // 放置 (仅文件夹可接收)
  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (file.isFolder) {
      try {
        const draggedData = JSON.parse(e.dataTransfer.getData('text/plain'));
        if (draggedData.id !== file.id) {
          onDrop?.(draggedData as FileNode, file);
        }
      } catch {
        // 忽略解析错误
      }
    }
  };

  return (
    <div
      className={`file-icon-item ${selected ? 'selected' : ''} ${isDragging ? 'opacity-50' : ''} ${isDragOver || isDropTarget ? 'bg-[#4b6ef3]/10 border-[#4b6ef3]' : ''}`}
      onClick={() => onClick(file)}
      onDoubleClick={() => onDoubleClick?.(file)}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      draggable={!file.isFolder || true}
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