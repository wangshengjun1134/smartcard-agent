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
 * 从后端 API 获取真实的文件树数据
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
      const response = await fetch(getApiUrl(API_CONFIG.endpoints.files.tree));

      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      if (data.status === 'ok' && Array.isArray(data.data)) {
        setFileStructure(data.data);
      } else {
        throw new Error('Invalid API response format');
      }
    } catch (err) {
      console.error('Failed to fetch file structure:', err);
      setError(err instanceof Error ? err : new Error('获取文件结构失败'));
      // 保留现有数据，避免因错误清空
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