import { useState, useMemo } from 'react';
import { ViewMode, FileNode } from '../../types/file';
import { useFileStructure } from '../../hooks/useFileStructure';
import { KnowledgeBaseHeader } from '../KnowledgeBase/KnowledgeBaseHeader';
import { FileGridView } from '../KnowledgeBase/FileGridView';
import { FileTreeView } from '../KnowledgeBase/FileTreeView';
import { FileDetailDrawer } from '../KnowledgeBase/FileDetailDrawer';

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

  // 获取文件结构数据
  const { fileStructure, loading, error } = useFileStructure();

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

  // 获取当前路径的面包屑信息
  const breadcrumb = useMemo(() => {
    if (!currentPath) {
      return [{ name: '知识库', path: '' }];
    }

    const parts = currentPath.split('/').filter(Boolean);
    const crumbs = [{ name: '知识库', path: '' }];

    let accumulatedPath = '';
    for (const part of parts) {
      accumulatedPath += '/' + part;
      crumbs.push({ name: part, path: accumulatedPath });
    }

    return crumbs;
  }, [currentPath]);

  // 处理单击 (选中文件)
  const handleFileClick = (file: FileNode) => {
    setSelectedFile(file);
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

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* 顶部栏 */}
      <KnowledgeBaseHeader
        viewMode={viewMode}
        onViewModeChange={handleViewModeChange}
      />

      {/* 内容区域 */}
      <div className="flex-1 overflow-y-auto">
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
            {/* 面包屑导航 (仅图标视图显示) */}
            {viewMode === 'icon' && currentPath && (
              <div className="flex items-center gap-2 px-4 py-2 bg-[#f7f8fa] dark:bg-[#333333] border-b border-[#ececee] dark:border-[#333333]">
                {/* 返回按钮 */}
                <button
                  className="flex items-center gap-1 px-2 py-1 rounded hover:bg-[#ececee] dark:hover:bg-[#404040] text-[#4a4a4a] dark:text-[#b3b3b3] text-sm"
                  onClick={handleGoBack}
                  aria-label="返回上级"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  返回
                </button>

                {/* 分隔线 */}
                <div className="w-px h-4 bg-[#ececee] dark:bg-[#404040]" />

                {/* 面包屑 */}
                <div className="flex items-center gap-1 text-sm">
                  {breadcrumb.map((crumb, index) => (
                    <span key={crumb.path}>
                      {index > 0 && (
                        <span className="text-[#999] dark:text-[#808080] mx-1">/</span>
                      )}
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
              />
            ) : (
              <FileTreeView
                files={fileStructure}
                selectedFileId={selectedFile?.id || null}
                onFileClick={handleFileClick}
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
    </div>
  );
}