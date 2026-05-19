import { useState, useCallback } from 'react';
import { FileNode } from '../types/file';
import { getApiUrl, API_CONFIG } from '../config/api';

interface OperationState {
  loading: boolean;
  error: Error | null;
}

interface UseFileOperationsReturn {
  operationState: OperationState;
  createFolder: (name: string, parentId?: string) => Promise<FileNode | null>;
  moveFile: (fileId: string, targetFolderId?: string) => Promise<FileNode | null>;
}

/**
 * 文件操作 Hook
 * 处理文件夹创建和文件移动等操作
 */
export function useFileOperations(): UseFileOperationsReturn {
  const [operationState, setOperationState] = useState<OperationState>({
    loading: false,
    error: null,
  });

  // 创建文件夹
  const createFolder = useCallback(async (name: string, parentId?: string): Promise<FileNode | null> => {
    setOperationState({ loading: true, error: null });

    try {
      const response = await fetch(getApiUrl(API_CONFIG.endpoints.files.createFolder), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          parent_id: parentId || null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Create folder failed' }));
        throw new Error(errorData.detail || `创建文件夹失败: ${response.status}`);
      }

      const data = await response.json();

      if (data.status === 'ok' && data.data) {
        setOperationState({ loading: false, error: null });
        return data.data as FileNode;
      } else {
        throw new Error('Invalid API response format');
      }
    } catch (err) {
      console.error('Create folder failed:', err);
      const error = err instanceof Error ? err : new Error('创建文件夹失败');
      setOperationState({ loading: false, error });
      return null;
    }
  }, []);

  // 移动文件
  const moveFile = useCallback(async (fileId: string, targetFolderId?: string): Promise<FileNode | null> => {
    setOperationState({ loading: true, error: null });

    try {
      const response = await fetch(getApiUrl(API_CONFIG.endpoints.files.move), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_id: fileId,
          target_folder_id: targetFolderId || null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Move file failed' }));
        throw new Error(errorData.detail || `移动文件失败: ${response.status}`);
      }

      const data = await response.json();

      if (data.status === 'ok' && data.data) {
        setOperationState({ loading: false, error: null });
        return data.data as FileNode;
      } else {
        throw new Error('Invalid API response format');
      }
    } catch (err) {
      console.error('Move file failed:', err);
      const error = err instanceof Error ? err : new Error('移动文件失败');
      setOperationState({ loading: false, error });
      return null;
    }
  }, []);

  return {
    operationState,
    createFolder,
    moveFile,
  };
}