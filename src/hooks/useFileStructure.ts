import { useState, useEffect, useCallback } from 'react';
import { FileNode } from '../types/file';
import { mockFileStructure, delay } from '../mocks/fileData';

interface UseFileStructureReturn {
  fileStructure: FileNode[];
  loading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
}

/**
 * 获取和管理文件结构数据的 Hook
 * 初期使用 Mock 数据，预留 API 集成接口
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
      // 模拟 API 延迟
      await delay(300);

      // 使用 Mock 数据
      // TODO: 后期替换为真实 API 调用
      // const response = await fetch('/api/knowledge-base/structure');
      // const data = await response.json();
      setFileStructure(mockFileStructure);
    } catch (err) {
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