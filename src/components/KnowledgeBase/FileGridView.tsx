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
  // 拖拽放置处理
  const handleDrop = (draggedFile: FileNode, targetFolder: FileNode) => {
    console.log(`Move ${draggedFile.name} to folder ${targetFolder.name}`);
    onMoveFile?.(draggedFile, targetFolder);
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
          onDrop={handleDrop}
        />
      ))}
    </div>
  );
}