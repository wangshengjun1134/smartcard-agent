import { useState, useEffect, useCallback } from 'react';
import { FileDetail } from '../types/file';
import { getMockFileDetail, delay } from '../mocks/fileData';

interface UseFileDetailReturn {
  detail: FileDetail | null;
  loading: boolean;
  error: Error | null;
}

/**
 * 获取文件详情和向量分片的 Hook
 * 初期使用 Mock 数据，预留 API 集成接口
 */
export function useFileDetail(fileId: string): UseFileDetailReturn {
  const [detail, setDetail] = useState<FileDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // 获取文件详情数据
  const fetchData = useCallback(async (id: string) => {
    if (!id) {
      setDetail(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 模拟 API 延迟
      await delay(200);

      // 使用 Mock 数据
      // TODO: 后期替换为真实 API 调用
      // const response = await fetch(`/api/knowledge-base/file/${id}`);
      // const data = await response.json();
      const data = getMockFileDetail(id);
      setDetail(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('获取文件详情失败'));
    } finally {
      setLoading(false);
    }
  }, []);

  // fileId 变化时重新获取数据
  useEffect(() => {
    fetchData(fileId);
  }, [fileId, fetchData]);

  return {
    detail,
    loading,
    error,
  };
}