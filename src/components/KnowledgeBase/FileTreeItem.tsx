import { FileNode } from '../../types/file';
import { FileIcon } from './FileIcon';

interface FileTreeItemProps {
  node: FileNode;
  level: number;
  expandedFolders: Set<string>;
  selectedFileId: string | null;
  onToggleFolder: (folderId: string) => void;
  onFileClick: (node: FileNode) => void;
}

/**
 * 树状视图节点组件
 * 支持层级缩进、展开/折叠、选中状态
 */
export function FileTreeItem({
  node,
  level,
  expandedFolders,
  selectedFileId,
  onToggleFolder,
  onFileClick,
}: FileTreeItemProps) {
  const isExpanded = expandedFolders.has(node.id);
  const isSelected = selectedFileId === node.id;

  const handleClick = () => {
    if (node.isFolder) {
      onToggleFolder(node.id);
    } else {
      onFileClick(node);
    }
  };

  return (
    <div className="file-tree-node">
      {/* 当前节点 */}
      <div
        className={`file-tree-item ${isSelected ? 'selected' : ''}`}
        style={{ paddingLeft: `${level * 24 + 12}px` }}
        onClick={handleClick}
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
        <span className="tree-file-name">
          {node.name}
        </span>
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
              onToggleFolder={onToggleFolder}
              onFileClick={onFileClick}
            />
          ))}
        </div>
      )}
    </div>
  );
}