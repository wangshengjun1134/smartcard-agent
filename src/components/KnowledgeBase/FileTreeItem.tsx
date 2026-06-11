import { useRef, useState } from 'react';
import { FileNode } from '../../types/file';
import { FileIcon } from './FileIcon';
import { ContextMenu, ContextMenuItem } from './ContextMenu';

interface FileTreeItemProps {
  node: FileNode;
  level: number;
  expandedFolders: Set<string>;
  selectedFileId: string | null;
  editingId: string | null;
  onToggleFolder: (folderId: string) => void;
  onFileClick: (node: FileNode) => void;
  onRename?: (file: FileNode, newName: string) => void;
  onDelete?: (file: FileNode) => void;
  onStartEdit?: (file: FileNode) => void;
  onCancelEdit?: () => void;
  onCreateFolder?: (parentFolder?: FileNode) => void;
  onUploadFile?: (parentFolder?: FileNode) => void;
}

/**
 * 树状视图节点组件
 * 支持层级缩进、展开/折叠、选中状态、右键菜单、重命名
 */
export function FileTreeItem({
  node,
  level,
  expandedFolders,
  selectedFileId,
  editingId,
  onToggleFolder,
  onFileClick,
  onRename,
  onDelete,
  onStartEdit,
  onCancelEdit,
  onCreateFolder,
  onUploadFile,
}: FileTreeItemProps) {
  const isExpanded = expandedFolders.has(node.id);
  const isSelected = selectedFileId === node.id;
  const isEditing = editingId === node.id;
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null);
  const [editName, setEditName] = useState(node.name);
  const inputRef = useRef<HTMLInputElement>(null);

  // 右键菜单项 - 文件夹有更多选项
  const menuItems: ContextMenuItem[] = node.isFolder
    ? [
        { id: 'open', label: '打开', icon: 'fa-regular fa-folder-open' },
        { id: 'newFolder', label: '新建文件夹', icon: 'fa-regular fa-folder' },
        { id: 'upload', label: '上传文件', icon: 'fa-regular fa-file-arrow-up' },
        { id: 'divider', label: '', divider: true },
        { id: 'rename', label: '重命名', icon: 'fa-regular fa-pen' },
        { id: 'divider2', label: '', divider: true },
        { id: 'delete', label: '删除', icon: 'fa-regular fa-trash', danger: true },
      ]
    : [
        { id: 'open', label: '打开', icon: 'fa-regular fa-file' },
        { id: 'divider', label: '', divider: true },
        { id: 'rename', label: '重命名', icon: 'fa-regular fa-pen' },
        { id: 'divider2', label: '', divider: true },
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
        if (node.isFolder) {
          onToggleFolder(node.id);
        } else {
          onFileClick(node);
        }
        break;
      case 'newFolder':
        onCreateFolder?.(node);
        break;
      case 'upload':
        onUploadFile?.(node);
        break;
      case 'rename':
        onStartEdit?.(node);
        break;
      case 'delete':
        onDelete?.(node);
        break;
    }
  };

  const handleClick = () => {
    if (node.isFolder) {
      onToggleFolder(node.id);
    } else {
      onFileClick(node);
    }
  };

  // 编辑模式下自动聚焦
  const handleEditFocus = () => {
    inputRef.current?.select();
  };

  // 编辑完成
  const handleEditKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      if (editName.trim() && editName !== node.name) {
        onRename?.(node, editName.trim());
      }
      onCancelEdit?.();
    } else if (e.key === 'Escape') {
      setEditName(node.name);
      onCancelEdit?.();
    }
  };

  // 编辑失焦
  const handleEditBlur = () => {
    if (editName.trim() && editName !== node.name) {
      onRename?.(node, editName.trim());
    }
    onCancelEdit?.();
  };

  return (
    <div className="file-tree-node">
      {/* 当前节点 */}
      <div
        className={`file-tree-item ${isSelected ? 'selected' : ''}`}
        style={{ paddingLeft: `${level * 24 + 12}px` }}
        onClick={handleClick}
        onContextMenu={handleContextMenu}
        role="button"
        tabIndex={0}
        aria-selected={isSelected}
        aria-expanded={node.isFolder ? isExpanded : undefined}
      >
        {/* 文件夹展开/折叠箭头 */}
        {node.isFolder && (
          <span className="tree-expand-icon">
            <svg
              className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </span>
        )}

        {/* 文件图标 */}
        <span className="tree-file-icon">
          <FileIcon type={node.type} size="sm" />
        </span>

        {/* 文件名 */}
        {isEditing ? (
          <input
            ref={inputRef}
            type="text"
            className="tree-name-input"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            onFocus={handleEditFocus}
            onKeyDown={handleEditKeyDown}
            onBlur={handleEditBlur}
            autoFocus
          />
        ) : (
          <span className="tree-file-name">{node.name}</span>
        )}
      </div>

      {/* 子节点 (文件夹展开时显示) */}
      {node.isFolder && isExpanded && node.children && (
        <div className="file-tree-children">
          {node.children.map((child) => (
            <FileTreeItem
              key={child.id}
              node={child}
              level={level + 1}
              expandedFolders={expandedFolders}
              selectedFileId={selectedFileId}
              editingId={editingId}
              onToggleFolder={onToggleFolder}
              onFileClick={onFileClick}
              onRename={onRename}
              onDelete={onDelete}
              onStartEdit={onStartEdit}
              onCancelEdit={onCancelEdit}
              onCreateFolder={onCreateFolder}
              onUploadFile={onUploadFile}
            />
          ))}
        </div>
      )}

      {/* 右键菜单 */}
      {contextMenu && (
        <ContextMenu
          items={menuItems}
          position={contextMenu}
          onSelect={handleMenuSelect}
          onClose={() => setContextMenu(null)}
        />
      )}
    </div>
  );
}