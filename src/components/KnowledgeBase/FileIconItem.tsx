import { DragEvent, useRef, useState } from 'react';
import { FileNode } from '../../types/file';
import { FileIcon } from './FileIcon';
import { ContextMenu, ContextMenuItem } from './ContextMenu';

interface FileIconItemProps {
  file: FileNode;
  onClick: (file: FileNode) => void;
  onDoubleClick?: (file: FileNode) => void;
  selected?: boolean;
  isDragging?: boolean;
  onDragStart?: () => void;
  onDragEnd?: () => void;
  onDrop?: (draggedFile: FileNode, targetFolder: FileNode) => void;
  editing?: boolean;
  onRename?: (file: FileNode, newName: string) => void;
  onDelete?: (file: FileNode) => void;
  onStartEdit?: (file: FileNode) => void;
  onCancelEdit?: () => void;
}

/**
 * 图标视图中的单个文件项组件
 * 支持拖拽到文件夹、右键菜单、重命名
 */
export function FileIconItem({
  file,
  onClick,
  onDoubleClick,
  selected = false,
  isDragging = false,
  onDragStart,
  onDragEnd,
  onDrop,
  editing = false,
  onRename,
  onDelete,
  onStartEdit,
  onCancelEdit,
}: FileIconItemProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null);
  const [editName, setEditName] = useState(file.name);
  const inputRef = useRef<HTMLInputElement>(null);

  // 右键菜单项
  const menuItems: ContextMenuItem[] = file.isFolder
    ? [
        { id: 'open', label: '打开', icon: 'fa-regular fa-folder-open' },
        { id: 'rename', label: '重命名', icon: 'fa-regular fa-pen' },
        { id: 'divider', label: '', divider: true },
        { id: 'delete', label: '删除', icon: 'fa-regular fa-trash', danger: true },
      ]
    : [
        { id: 'open', label: '打开', icon: 'fa-regular fa-file' },
        { id: 'rename', label: '重命名', icon: 'fa-regular fa-pen' },
        { id: 'divider', label: '', divider: true },
        { id: 'delete', label: '删除', icon: 'fa-regular fa-trash', danger: true },
      ];

  // 右键菜单处理
  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setContextMenu({ x: e.clientX, y: e.clientY });
  };

  // 菜单项选择
  const handleMenuSelect = (id: string) => {
    switch (id) {
      case 'open':
        onDoubleClick?.(file);
        break;
      case 'rename':
        onStartEdit?.(file);
        break;
      case 'delete':
        onDelete?.(file);
        break;
    }
  };

  // 开始拖拽
  const handleDragStart = (e: DragEvent<HTMLDivElement>) => {
    e.dataTransfer.setData(
      'application/json',
      JSON.stringify({
        id: file.id,
        name: file.name,
        path: file.path,
        type: file.type,
        isFolder: file.isFolder,
      })
    );
    e.dataTransfer.effectAllowed = 'move';
    onDragStart?.();
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
          // 不能拖到自己，不能拖到自己的子文件夹
          if (draggedFile.id !== file.id && !draggedFile.path.startsWith(file.path + '/')) {
            onDrop?.(draggedFile, file);
          }
        }
      } catch {
        // 忽略解析错误
      }
    }
  };

  // 编辑模式下自动聚焦
  const handleEditFocus = () => {
    // 选中文本便于修改
    inputRef.current?.select();
  };

  // 编辑完成
  const handleEditKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      if (editName.trim() && editName !== file.name) {
        onRename?.(file, editName.trim());
      }
      onCancelEdit?.();
    } else if (e.key === 'Escape') {
      setEditName(file.name);
      onCancelEdit?.();
    }
  };

  // 编辑失焦
  const handleEditBlur = () => {
    if (editName.trim() && editName !== file.name) {
      onRename?.(file, editName.trim());
    }
    onCancelEdit?.();
  };

  // 组合类名
  const classNames = [
    'file-icon-item',
    selected ? 'selected' : '',
    isDragOver ? 'drag-over' : '',
    isDragging ? 'dragging' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <>
      <div
        className={classNames}
        onClick={() => onClick(file)}
        onDoubleClick={() => onDoubleClick?.(file)}
        onContextMenu={handleContextMenu}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        draggable={!editing}
        role="button"
        tabIndex={0}
        aria-selected={selected}
      >
        <div className="file-icon">
          <FileIcon type={file.type} size="lg" />
        </div>
        <div className="file-name">
          {editing ? (
            <input
              ref={inputRef}
              type="text"
              className="file-name-input"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              onFocus={handleEditFocus}
              onKeyDown={handleEditKeyDown}
              onBlur={handleEditBlur}
              autoFocus
            />
          ) : (
            file.name
          )}
        </div>
      </div>

      {/* 右键菜单 */}
      {contextMenu && (
        <ContextMenu
          items={menuItems}
          position={contextMenu}
          onSelect={handleMenuSelect}
          onClose={() => setContextMenu(null)}
        />
      )}
    </>
  );
}