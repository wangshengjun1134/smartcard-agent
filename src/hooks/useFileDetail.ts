import { useState, useEffect, useCallback } from 'react';
import { FileDetail } from '../types/file';
import { getApiUrl, API_CONFIG } from '../config/api';

interface UseFileDetailReturn {
  detail: FileDetail | null;
  loading: boolean;
  error: Error | null;
}

/**
 * 文件详情 Hook
 * 获取单个文件的详细信息
 * @param fileId 文件 ID
 */
export function useFileDetail(fileId: string): UseFileDetailReturn {
  const [detail, setDetail] = useState<FileDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // 获取文件详情
  const fetchDetail = useCallback(async (id: string) => {
    if (!id) {
      setDetail(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(getApiUrl(API_CONFIG.endpoints.files.detail(id)));

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('文件不存在');
        }
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      if (data.status === 'ok' && data.data) {
        setDetail(data.data as FileDetail);
      } else {
        throw new Error('Invalid API response format');
      }
    } catch (err) {
      console.error('Failed to fetch file detail:', err);
      setError(err instanceof Error ? err : new Error('获取文件详情失败'));
    } finally {
      setLoading(false);
    }
  }, []);

  // fileId 变化时重新获取
  useEffect(() => {
    fetchDetail(fileId);
  }, [fileId, fetchDetail]);

  return {
    detail,
    loading,
    error,
  };
}