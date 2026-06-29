import { useState, useEffect, useCallback } from 'react';
import { FileNode } from '../types/file';
import { getApiUrl, API_CONFIG } from '../config/api';

interface UseFileStructureReturn {
  fileStructure: FileNode[];
  loading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
}

/**
 * 获取和管理文件结构数据的 Hook
 * 合并 files/tree（文件夹树）和 documents/list（文件列表）
 */
export function useFileStructure(): UseFileStructureReturn {
  const [fileStructure, setFileStructure] = useState<FileNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // 获取文件结构数据
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // 并行获取文件夹树和文档列表
      const [treeRes, docsRes] = await Promise.all([
        fetch(getApiUrl(API_CONFIG.endpoints.files.tree)),
        fetch(getApiUrl(API_CONFIG.endpoints.documents.list)),
      ]);

      if (!treeRes.ok) {
        throw new Error(`Tree API error: ${treeRes.status}`);
      }

      const treeData = await treeRes.json();
      if (treeData.status !== 'ok' || !Array.isArray(treeData.data)) {
        throw new Error('Invalid tree API response');
      }

      const treeNodes: FileNode[] = treeData.data;

      // 获取文档列表并挂载到对应文件夹
      if (docsRes.ok) {
        const docsData = await docsRes.json();
        if (docsData.status === 'ok' && docsData.data?.documents) {
          const docNodes: FileNode[] = docsData.data.documents.map((doc: any) => ({
            id: doc.id,
            name: doc.filename,
            type: detectFileType(doc.filename),
            path: doc.file_path || '',
            isFolder: false,
            size: doc.file_size,
            mimeType: doc.mime_type,
            createdAt: doc.createdAt,
            modifiedAt: doc.updatedAt,
            kb_id: doc.kb_id,           // 知识库 ID
            doc_id: doc.id,             // 文档 ID
            status: doc.status,         // 文档状态
            fileHash: doc.file_hash,    // 文件哈希
            _folderId: doc.folder_id || null, // 用于挂载到对应文件夹
          })) as (FileNode & { _folderId?: string | null })[];

          // 将文档挂载到对应文件夹下
          const mergedTree = nestDocumentsUnderFolders(treeNodes, docNodes);
          setFileStructure(mergedTree);
        } else {
          setFileStructure(treeNodes);
        }
      } else {
        // 文档 API 不可用，仅显示文件夹
        setFileStructure(treeNodes);
      }
    } catch (err) {
      console.error('Failed to fetch file structure:', err);
      setError(err instanceof Error ? err : new Error('获取文件结构失败'));
    } finally {
      setLoading(false);
    }
  }, []);

  // 初始加载
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // 刷新方法
  const refresh = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  return {
    fileStructure,
    loading,
    error,
    refresh,
  };
}

/**
 * 将文档节点挂载到对应文件夹下
 */
function nestDocumentsUnderFolders(
  folders: FileNode[],
  documents: (FileNode & { _folderId?: string | null })[]
): FileNode[] {
  // 按 folder_id 分组文档
  const docsByFolder: Record<string, FileNode[]> = {};
  const rootDocs: FileNode[] = [];

  for (const doc of documents) {
    const { _folderId, ...cleanDoc } = doc;
    if (_folderId) {
      if (!docsByFolder[_folderId]) {
        docsByFolder[_folderId] = [];
      }
      docsByFolder[_folderId].push(cleanDoc as FileNode);
    } else {
      rootDocs.push(cleanDoc as FileNode);
    }
  }

  // 递归挂载
  function attachDocs(nodes: FileNode[]): FileNode[] {
    return nodes.map((node) => {
      if (node.isFolder) {
        const childrenDocs = docsByFolder[node.id] || [];
        const nestedChildren = node.children ? attachDocs(node.children) : [];
        return {
          ...node,
          children: [...nestedChildren, ...childrenDocs],
        };
      }
      return node;
    });
  }

  // 根级文档直接附加到结果数组末尾
  return [...attachDocs(folders), ...rootDocs];
}

/**
 * 根据文件名检测文件类型
 */
function detectFileType(filename: string): FileNode['type'] {
  if (!filename) return 'unknown';
  const ext = filename.toLowerCase().split('.').pop() || '';
  const typeMap: Record<string, FileNode['type']> = {
    pdf: 'pdf',
    doc: 'word',
    docx: 'word',
    md: 'markdown',
    markdown: 'markdown',
    txt: 'text',
    png: 'image',
    jpg: 'image',
    jpeg: 'image',
    gif: 'image',
    webp: 'image',
  };
  return typeMap[ext] || 'unknown';
}