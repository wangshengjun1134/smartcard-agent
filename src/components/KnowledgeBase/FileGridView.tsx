import { useState } from 'react';
import { FileNode } from '../../types/file';
import { FileIconItem } from './FileIconItem';
import { ContextMenu, ContextMenuItem } from './ContextMenu';

interface FileGridViewProps {
  files: FileNode[];
  selectedFileId: string | null;
  editingId: string | null;
  currentFolder: FileNode | null;
  onFileClick: (file: FileNode) => void;
  onDoubleClick: (file: FileNode) => void;
  onMoveFile?: (draggedFile: FileNode, targetFolder: FileNode) => void;
  onRename?: (file: FileNode, newName: string) => void;
  onDelete?: (file: FileNode) => void;
  onStartEdit?: (file: FileNode) => void;
  onCancelEdit?: () => void;
  onCreateFolder?: (parentFolder?: FileNode) => void;
  onUploadFile?: (parentFolder?: FileNode) => void;
}

/**
 * 图标视图网格布局组件
 */
export function FileGridView({
  files,
  selectedFileId,
  editingId,
  currentFolder,
  onFileClick,
  onDoubleClick,
  onMoveFile,
  onRename,
  onDelete,
  onStartEdit,
  onCancelEdit,
  onCreateFolder,
  onUploadFile,
}: FileGridViewProps) {
  // 拖拽状态：记录当前正在拖拽的文件
  const [draggingFileId, setDraggingFileId] = useState<string | null>(null);

  // 空白区域右键菜单状态
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null);

  // 空白区域右键菜单项
  const emptyAreaMenuItems: ContextMenuItem[] = [
    { id: 'newFolder', label: '新建文件夹', icon: 'fa-regular fa-folder' },
    { id: 'upload', label: '上传文件', icon: 'fa-regular fa-file-arrow-up' },
  ];

  // 空白区域右键菜单处理
  const handleContainerContextMenu = (e: React.MouseEvent) => {
    // 只有当点击的是容器本身（不是文件项）时才显示菜单
    if (e.target === e.currentTarget) {
      e.preventDefault();
      setContextMenu({ x: e.clientX, y: e.clientY });
    }
  };

  // 空白区域菜单项选择
  const handleMenuSelect = (id: string) => {
    switch (id) {
      case 'newFolder':
        onCreateFolder?.(currentFolder || undefined);
        break;
      case 'upload':
        onUploadFile?.(currentFolder || undefined);
        break;
    }
  };

  // 拖拽放置处理
  const handleDrop = (draggedFile: FileNode, targetFolder: FileNode) => {
    console.log(`Move ${draggedFile.name} to folder ${targetFolder.name}`);
    onMoveFile?.(draggedFile, targetFolder);
    setDraggingFileId(null);
  };

  return (
    <>
      <div
        className="file-grid"
        onContextMenu={handleContainerContextMenu}
      >
        {files.map((file) => (
          <FileIconItem
            key={file.id}
            file={file}
            onClick={onFileClick}
            onDoubleClick={onDoubleClick}
            selected={selectedFileId === file.id}
            editing={editingId === file.id}
            isDragging={draggingFileId === file.id}
            onDragStart={() => setDraggingFileId(file.id)}
            onDragEnd={() => setDraggingFileId(null)}
            onDrop={handleDrop}
            onRename={onRename}
            onDelete={onDelete}
            onStartEdit={onStartEdit}
            onCancelEdit={onCancelEdit}
          />
        ))}
      </div>

      {/* 空白区域右键菜单 */}
      {contextMenu && (
        <ContextMenu
          items={emptyAreaMenuItems}
          position={contextMenu}
          onSelect={handleMenuSelect}
          onClose={() => setContextMenu(null)}
        />
      )}
    </>
  );
}