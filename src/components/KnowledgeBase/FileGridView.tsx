import { useState } from 'react';
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
 */
export function FileGridView({
  files,
  selectedFileId,
  onFileClick,
  onDoubleClick,
  onMoveFile
}: FileGridViewProps) {
  // 拖拽状态：记录当前正在拖拽的文件
  const [draggingFileId, setDraggingFileId] = useState<string | null>(null);

  // 拖拽放置处理
  const handleDrop = (draggedFile: FileNode, targetFolder: FileNode) => {
    console.log(`Move ${draggedFile.name} to folder ${targetFolder.name}`);
    onMoveFile?.(draggedFile, targetFolder);
    setDraggingFileId(null);
  };

  return (
    <div className="file-grid">
      {files.map((file) => (
        <FileIconItem
          key={file.id}
          file={file}
          onClick={onFileClick}
          onDoubleClick={onDoubleClick}
          selected={selectedFileId === file.id}
          isDragging={draggingFileId === file.id}
          onDragStart={() => setDraggingFileId(file.id)}
          onDragEnd={() => setDraggingFileId(null)}
          onDrop={handleDrop}
        />
      ))}
    </div>
  );
}