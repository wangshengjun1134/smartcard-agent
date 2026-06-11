import { useState, useMemo, useCallback } from 'react';
import { ViewMode, FileNode } from '../../types/file';
import { KnowledgeFormData } from '../../types/knowledge';
import { useFileStructure } from '../../hooks/useFileStructure';
import { useFileUpload } from '../../hooks/useFileUpload';
import { useFileOperations } from '../../hooks/useFileOperations';
import { findFolderByPath, buildBreadcrumb, getParentPath, getFolderNames, generateUniqueFolderName } from '../../utils/fileUtils';
import { KnowledgeBaseHeader } from '../KnowledgeBase/KnowledgeBaseHeader';
import { FileGridView } from '../KnowledgeBase/FileGridView';
import { FileTreeView } from '../KnowledgeBase/FileTreeView';
import { FileDetailDrawer } from '../KnowledgeBase/FileDetailDrawer';
import { AddKnowledgeDrawer } from '../KnowledgeBase/AddKnowledgeDrawer';

/**
 * 知识库页面主组件
 * 管理视图模式、路径导航和抽屉状态
 */
export function KnowledgeBase() {
  // 视图模式状态 (默认图标视图)
  const [viewMode, setViewMode] = useState<ViewMode>('icon');

  // 当前路径状态 (用于图标视图导航)
  const [currentPath, setCurrentPath] = useState<string>('');

  // 选中文件和抽屉状态
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // 添加知识抽屉状态
  const [addDrawerOpen, setAddDrawerOpen] = useState(false);

  // 上传目标文件夹（树状视图右键目录时设置）
  const [uploadTargetFolder, setUploadTargetFolder] = useState<FileNode | null>(null);

  // 编辑状态：正在编辑的文件 ID
  const [editingId, setEditingId] = useState<string | null>(null);

  // 获取文件结构数据
  const { fileStructure, loading, error, refresh } = useFileStructure();

  // 文件上传 Hook
  const { uploadState, uploadFile } = useFileUpload();

  // 文件操作 Hook
  const { createFolder, moveFile, renameFile, deleteFile } = useFileOperations();

  // 根据当前路径获取当前显示的文件列表（使用统一的工具函数）
  const currentFiles = useMemo(() => {
    if (!currentPath) {
      return fileStructure;
    }

    const folder = findFolderByPath(fileStructure, currentPath);
    return folder?.children || [];
  }, [fileStructure, currentPath]);

  // 获取当前路径的面包屑信息（使用统一的工具函数）
  const breadcrumb = useMemo(() => {
    return buildBreadcrumb(currentPath);
  }, [currentPath]);

  // 查找当前目录的 parent_id（使用统一的工具函数）
  const getCurrentFolderId = useCallback(() => {
    if (!currentPath) return undefined;
    const currentFolder = findFolderByPath(fileStructure, currentPath);
    return currentFolder?.id;
  }, [currentPath, fileStructure]);

  // 处理单击 (选中文件) - 图标视图
  const handleFileClick = (file: FileNode) => {
    setSelectedFile(file);
  };

  // 处理树形视图单击 (选中文件并打开抽屉)
  const handleTreeFileClick = (file: FileNode) => {
    setSelectedFile(file);
    // 如果是文件，直接打开抽屉
    if (!file.isFolder) {
      setDrawerOpen(true);
    }
  };

  // 处理双击 (文件夹进入 / 文件打开抽屉)
  const handleDoubleClick = (file: FileNode) => {
    if (file.isFolder) {
      // 进入文件夹
      setCurrentPath(file.path);
      setSelectedFile(null);
    } else {
      // 打开文件详情抽屉
      setSelectedFile(file);
      setDrawerOpen(true);
    }
  };

  // 返回上级文件夹（使用统一的工具函数）
  const handleGoBack = () => {
    setCurrentPath(getParentPath(currentPath));
  };

  // 点击面包屑导航
  const handleBreadcrumbClick = (path: string) => {
    setCurrentPath(path);
    setSelectedFile(null);
  };

  // 关闭抽屉
  const handleCloseDrawer = () => {
    setDrawerOpen(false);
    // 延迟清空选中文件，等抽屉动画完成
    setTimeout(() => setSelectedFile(null), 300);
  };

  // 切换视图模式
  const handleViewModeChange = (mode: ViewMode) => {
    setViewMode(mode);
    // 切换到树状视图时清除路径导航
    if (mode === 'tree') {
      setCurrentPath('');
      setSelectedFile(null);
    }
  };

  // 打开添加知识抽屉
  // parentFolder: 树状视图右键目录时传入
  const handleAddClick = useCallback((parentFolder?: FileNode) => {
    setUploadTargetFolder(parentFolder || null);
    setAddDrawerOpen(true);
  }, []);

  // 关闭添加知识抽屉
  const handleCloseAddDrawer = useCallback(() => {
    setAddDrawerOpen(false);
    setUploadTargetFolder(null);
  }, []);

  // 处理知识上传
  const handleKnowledgeSubmit = useCallback(
    async (file: File, data: KnowledgeFormData, kbId: string, folderId?: string) => {
      try {
        // 构建上传参数 (与 documents 表字段对应)
        const params = {
          kb_id: kbId,
          folder_id: folderId,
          title: data.title || file.name,
          source: data.source || undefined,
          language: data.language || 'zh',
          tags: data.tags.length > 0 ? data.tags : undefined,
        };

        const result = await uploadFile(file, params);

        if (result) {
          // 上传成功后刷新文件列表
          refresh();
        } else {
          throw new Error(uploadState.error?.message || '上传失败');
        }
      } catch (error) {
        console.error('Upload failed:', error);
        throw error;
      }
    },
    [uploadFile, uploadState, refresh]
  );

  // 新建文件夹（使用统一的工具函数）
  // parentFolder: 树状视图右键目录时传入，图标视图空白区域时不传
  const handleCreateFolder = useCallback(async (parentFolder?: FileNode) => {
    // 确定目标目录的文件列表和 parent_id
    const targetFiles = parentFolder?.children || currentFiles;
    const parentId = parentFolder?.id || getCurrentFolderId();

    // 获取目标目录下已有的文件夹名称
    const existingNames = getFolderNames(targetFiles);
    const newFolderName = generateUniqueFolderName(existingNames);

    // 调用后端 API 创建文件夹
    const result = await createFolder(newFolderName, parentId);
    if (result) {
      // 选中新创建的文件夹
      setSelectedFile(result);
      refresh();
    }
  }, [currentFiles, getCurrentFolderId, createFolder, refresh]);

  // 拖拽移动文件
  const handleMoveFile = useCallback(async (draggedFile: FileNode, targetFolder: FileNode) => {
    // 调用后端 API 移动文件
    const result = await moveFile(draggedFile.id, targetFolder.id);
    if (result) {
      refresh();
    }
  }, [moveFile, refresh]);

  // 开始编辑文件名
  const handleStartEdit = useCallback((file: FileNode) => {
    setEditingId(file.id);
  }, []);

  // 取消编辑
  const handleCancelEdit = useCallback(() => {
    setEditingId(null);
  }, []);

  // 重命名文件/文件夹
  const handleRename = useCallback(async (file: FileNode, newName: string) => {
    const result = await renameFile(file.id, newName);
    if (result) {
      setEditingId(null);
      refresh();
    }
  }, [renameFile, refresh]);

  // 删除文件/文件夹
  const handleDelete = useCallback(async (file: FileNode) => {
    const result = await deleteFile(file.id);
    if (result) {
      // 清除选中状态
      if (selectedFile?.id === file.id) {
        setSelectedFile(null);
      }
      refresh();
    }
  }, [deleteFile, selectedFile, refresh]);

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* 顶部栏 */}
      <KnowledgeBaseHeader
        viewMode={viewMode}
        onViewModeChange={handleViewModeChange}
        onAddClick={() => handleAddClick(findFolderByPath(fileStructure, currentPath) || undefined)}
        onCreateFolder={() => handleCreateFolder(findFolderByPath(fileStructure, currentPath) || undefined)}
      />

      {/* 内容区域容器 */}
      <div className="flex-1 relative min-h-0">
        {/* 滚动内容 */}
        <div className="absolute inset-0 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-[#999] dark:text-[#808080]">加载中...</div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-[#ff4d4f]">加载失败: {error.message}</div>
            </div>
          ) : fileStructure.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="text-[#1a1a1a] dark:text-white text-lg mb-2">
                知识库为空
              </div>
              <div className="text-[#999] dark:text-[#808080] text-sm">
                点击右上角 + 添加知识文档
              </div>
            </div>
          ) : (
            <>
              {/* 面包屑导航 (仅图标视图显示，且不在根目录时) */}
              {viewMode === 'icon' && breadcrumb.length > 0 && (
                <div className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-[#222222]">
                  {/* 返回按钮 */}
                  <button
                    className="flex items-center gap-1 px-2 py-1 rounded hover:bg-[#ececee] dark:hover:bg-[#333333] text-[#4a4a4a] dark:text-[#b3b3b3] text-sm"
                    onClick={handleGoBack}
                    aria-label="返回上级"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                    返回
                  </button>

                  {/* 分隔线 */}
                  <div className="w-px h-4 bg-[#ececee] dark:bg-[#333333]" />

                  {/* 面包屑 */}
                  <div className="flex items-center gap-1 text-sm">
                    {breadcrumb.map((crumb, index) => (
                      <span key={crumb.path}>
                        <span className="text-[#999] dark:text-[#808080] mx-1">/</span>
                        <button
                          className={`hover:text-[#4b6ef3] ${
                            index === breadcrumb.length - 1
                              ? 'text-[#1a1a1a] dark:text-white font-medium'
                              : 'text-[#4a4a4a] dark:text-[#b3b3b3]'
                          }`}
                          onClick={() => handleBreadcrumbClick(crumb.path)}
                        >
                          {crumb.name}
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* 根据视图模式渲染对应组件 */}
              {viewMode === 'icon' ? (
                <FileGridView
                  files={currentFiles}
                  selectedFileId={selectedFile?.id || null}
                  editingId={editingId}
                  currentFolder={findFolderByPath(fileStructure, currentPath) || null}
                  onFileClick={handleFileClick}
                  onDoubleClick={handleDoubleClick}
                  onMoveFile={handleMoveFile}
                  onRename={handleRename}
                  onDelete={handleDelete}
                  onStartEdit={handleStartEdit}
                  onCancelEdit={handleCancelEdit}
                  onCreateFolder={handleCreateFolder}
                  onUploadFile={handleAddClick}
                />
              ) : (
                <FileTreeView
                  files={fileStructure}
                  selectedFileId={selectedFile?.id || null}
                  editingId={editingId}
                  onFileClick={handleTreeFileClick}
                  onRename={handleRename}
                  onDelete={handleDelete}
                  onStartEdit={handleStartEdit}
                  onCancelEdit={handleCancelEdit}
                  onCreateFolder={handleCreateFolder}
                  onUploadFile={handleAddClick}
                />
              )}
            </>
          )}
        </div>

        {/* 文件详情抽屉 */}
        <FileDetailDrawer
          file={selectedFile}
          isOpen={drawerOpen}
          onClose={handleCloseDrawer}
        />

        {/* 添加知识抽屉 */}
        <AddKnowledgeDrawer
          isOpen={addDrawerOpen}
          onClose={handleCloseAddDrawer}
          onSubmit={handleKnowledgeSubmit}
          parentFolder={uploadTargetFolder || undefined}
        />
      </div>
    </div>
  );
}