import { useState, useMemo, useCallback } from 'react';
import { ViewMode, FileNode } from '../../types/file';
import { KnowledgeFormData } from '../../types/knowledge';
import { useFileStructure } from '../../hooks/useFileStructure';
import { useFileUpload } from '../../hooks/useFileUpload';
import { useFileOperations } from '../../hooks/useFileOperations';
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

  // 获取文件结构数据
  const { fileStructure, loading, error, refresh } = useFileStructure();

  // 文件上传 Hook
  const { uploadState, uploadFile } = useFileUpload();

  // 文件操作 Hook
  const { createFolder, moveFile } = useFileOperations();

  // 根据当前路径获取当前显示的文件列表
  const currentFiles = useMemo(() => {
    if (!currentPath) {
      return fileStructure;
    }

    // 递归查找当前路径对应的文件夹
    const findFolder = (nodes: FileNode[], path: string): FileNode | null => {
      for (const node of nodes) {
        if (node.path === path && node.isFolder) {
          return node;
        }
        if (node.children) {
          const found = findFolder(node.children, path);
          if (found) return found;
        }
      }
      return null;
    };

    const folder = findFolder(fileStructure, currentPath);
    return folder?.children || [];
  }, [fileStructure, currentPath]);

  // 获取当前路径的面包屑信息 (去掉 "docs" 部分)
  const breadcrumb = useMemo(() => {
    if (!currentPath) {
      return [];
    }

    // 去掉路径中的 "/docs" 前缀
    const normalizedPath = currentPath.replace(/^\/docs/, '');
    const parts = normalizedPath.split('/').filter(Boolean);
    
    const crumbs = [];
    let accumulatedPath = '';
    for (const part of parts) {
      accumulatedPath += '/docs/' + part;
      crumbs.push({ name: part, path: accumulatedPath });
    }

    return crumbs;
  }, [currentPath]);

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

  // 返回上级文件夹
  const handleGoBack = () => {
    const parts = currentPath.split('/').filter(Boolean);
    parts.pop();
    setCurrentPath(parts.length > 0 ? '/' + parts.join('/') : '');
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
  const handleAddClick = useCallback(() => {
    setAddDrawerOpen(true);
  }, []);

  // 关闭添加知识抽屉
  const handleCloseAddDrawer = useCallback(() => {
    setAddDrawerOpen(false);
  }, []);

  // 处理知识上传
  const handleKnowledgeSubmit = useCallback(
    async (file: File, _data: KnowledgeFormData) => {
      try {
        // 查找当前目录的 parent_id
        let parentId: string | undefined = undefined;
        if (currentPath) {
          const findFolder = (nodes: FileNode[], path: string): FileNode | null => {
            for (const node of nodes) {
              if (node.path === path && node.isFolder) {
                return node;
              }
              if (node.children) {
                const found = findFolder(node.children, path);
                if (found) return found;
              }
            }
            return null;
          };
          const currentFolder = findFolder(fileStructure, currentPath);
          parentId = currentFolder?.id;
        }

        const result = await uploadFile(file, parentId);
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
    [uploadFile, uploadState, currentPath, fileStructure, refresh]
  );

  // 新建文件夹
  const handleCreateFolder = useCallback(async () => {
    // 生成文件夹名称
    const generateFolderName = (existingNames: string[]): string => {
      const baseName = '新建文件夹';
      if (!existingNames.includes(baseName)) {
        return baseName;
      }
      let counter = 2;
      while (existingNames.includes(`${baseName} (${counter})`)) {
        counter++;
      }
      return `${baseName} (${counter})`;
    };

    // 获取当前目录下已有的文件夹名称
    const existingNames = currentFiles
      .filter(f => f.isFolder)
      .map(f => f.name);

    const newFolderName = generateFolderName(existingNames);

    // 查找当前目录的 parent_id
    let parentId: string | undefined = undefined;
    if (currentPath) {
      const findFolder = (nodes: FileNode[], path: string): FileNode | null => {
        for (const node of nodes) {
          if (node.path === path && node.isFolder) {
            return node;
          }
          if (node.children) {
            const found = findFolder(node.children, path);
            if (found) return found;
          }
        }
        return null;
      };
      const currentFolder = findFolder(fileStructure, currentPath);
      parentId = currentFolder?.id;
    }

    // 调用后端 API 创建文件夹
    const result = await createFolder(newFolderName, parentId);
    if (result) {
      refresh();
    }
  }, [currentFiles, currentPath, fileStructure, createFolder, refresh]);

  // 拖拽移动文件
  const handleMoveFile = useCallback(async (draggedFile: FileNode, targetFolder: FileNode) => {
    // 调用后端 API 移动文件
    const result = await moveFile(draggedFile.id, targetFolder.id);
    if (result) {
      refresh();
    }
  }, [moveFile, refresh]);

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* 顶部栏 */}
      <KnowledgeBaseHeader
        viewMode={viewMode}
        onViewModeChange={handleViewModeChange}
        onAddClick={handleAddClick}
        onCreateFolder={handleCreateFolder}
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
                  onFileClick={handleFileClick}
                  onDoubleClick={handleDoubleClick}
                  onMoveFile={handleMoveFile}
                />
              ) : (
                <FileTreeView
                  files={fileStructure}
                  selectedFileId={selectedFile?.id || null}
                  onFileClick={handleTreeFileClick}
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
        />
      </div>
    </div>
  );
}