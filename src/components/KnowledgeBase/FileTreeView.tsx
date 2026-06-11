import { useState } from 'react';
import { FileNode } from '../../types/file';
import { FileTreeItem } from './FileTreeItem';

interface FileTreeViewProps {
  files: FileNode[];
  selectedFileId: string | null;
  editingId: string | null;
  onFileClick: (file: FileNode) => void;
  onRename?: (file: FileNode, newName: string) => void;
  onDelete?: (file: FileNode) => void;
  onStartEdit?: (file: FileNode) => void;
  onCancelEdit?: () => void;
  onCreateFolder?: (parentFolder?: FileNode) => void;
  onUploadFile?: (parentFolder?: FileNode) => void;
}

/**
 * 树状视图容器组件
 * 管理文件夹展开状态，递归渲染树节点
 */
export function FileTreeView({
  files,
  selectedFileId,
  editingId,
  onFileClick,
  onRename,
  onDelete,
  onStartEdit,
  onCancelEdit,
  onCreateFolder,
  onUploadFile,
}: FileTreeViewProps) {
  // 管理已展开的文件夹 ID 集合
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());

  // 切换文件夹展开/折叠
  const handleToggleFolder = (folderId: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(folderId)) {
        next.delete(folderId);
      } else {
        next.add(folderId);
      }
      return next;
    });
  };

  return (
    <div className="file-tree">
      {files.map((node) => (
        <FileTreeItem
          key={node.id}
          node={node}
          level={0}
          expandedFolders={expandedFolders}
          selectedFileId={selectedFileId}
          editingId={editingId}
          onToggleFolder={handleToggleFolder}
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
  );
}