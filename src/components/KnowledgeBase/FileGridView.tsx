import { useState, useCallback } from 'react';
import { FileNode } from '../../types/file';
import { FileIconItem } from './FileIconItem';

interface FileGridViewProps {
  files: FileNode[];
  selectedFileId: string | null;
  onFileClick: (file: FileNode) => void;
  onDoubleClick: (file: FileNode) => void;
  onMoveFile?: (draggedFile: FileNode, targetFolder: FileNode) => void;
}

/**
 * 图标视图网格布局组件
 * 支持文件拖拽到文件夹
 */
export function FileGridView({ 
  files, 
  selectedFileId, 
  onFileClick, 
  onDoubleClick,
  onMoveFile
}: FileGridViewProps) {
  const [draggedFile, setDraggedFile] = useState<FileNode | null>(null);
  const [dropTargetId, setDropTargetId] = useState<string | null>(null);

  // 开始拖拽
  const handleDragStart = useCallback((file: FileNode) => {
    setDraggedFile(file);
    setDropTargetId(null);
  }, []);

  // 结束拖拽
  const handleDragEnd = useCallback(() => {
    setDraggedFile(null);
    setDropTargetId(null);
  }, []);

  // 放置到文件夹 - 使用 draggedFile 判断
  const handleDrop = useCallback((dragged: FileNode, targetFolder: FileNode) => {
    if (draggedFile && onMoveFile && dragged.id !== targetFolder.id) {
      console.log(`Move ${dragged.name} to ${targetFolder.name}`);
      onMoveFile(dragged, targetFolder);
    }
    setDraggedFile(null);
    setDropTargetId(null);
  }, [draggedFile, onMoveFile]);

  return (
    <div className="file-grid">
      {files.map((file) => (
        <FileIconItem
          key={file.id}
          file={file}
          onClick={onFileClick}
          onDoubleClick={onDoubleClick}
          selected={selectedFileId === file.id}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
          onDrop={handleDrop}
          isDropTarget={dropTargetId === file.id}
        />
      ))}
    </div>
  );
}