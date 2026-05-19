import { useState, useCallback } from 'react';
import { FileNode } from '../types/file';
import { getApiUrl, API_CONFIG, FILE_UPLOAD_CONSTRAINTS } from '../config/api';

interface UploadState {
  uploading: boolean;
  progress: number; // 0-100
  error: Error | null;
}

interface UseFileUploadReturn {
  uploadState: UploadState;
  uploadFile: (file: File, parentId?: string) => Promise<FileNode | null>;
}

/**
 * 文件上传 Hook
 * 处理文件上传到知识库的后端 API 调用
 */
export function useFileUpload(): UseFileUploadReturn {
  const [uploadState, setUploadState] = useState<UploadState>({
    uploading: false,
    progress: 0,
    error: null,
  });

  // 验证文件
  const validateFile = (file: File): Error | null => {
    // 检查文件大小
    const maxSizeBytes = FILE_UPLOAD_CONSTRAINTS.maxFileSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      return new Error(`文件大小超过限制 (${FILE_UPLOAD_CONSTRAINTS.maxFileSizeMB}MB)`);
    }

    // 检查文件扩展名
    const fileName = file.name.toLowerCase();
    const ext = fileName.slice(fileName.lastIndexOf('.'));
    if (!FILE_UPLOAD_CONSTRAINTS.allowedExtensions.includes(ext)) {
      return new Error(`不支持的文件类型: ${ext}`);
    }

    return null;
  };

  // 上传文件
  const uploadFile = useCallback(async (file: File, parentId?: string): Promise<FileNode | null> => {
    // 验证文件
    const validationError = validateFile(file);
    if (validationError) {
      setUploadState({ uploading: false, progress: 0, error: validationError });
      return null;
    }

    setUploadState({ uploading: true, progress: 0, error: null });

    try {
      // 构建 FormData
      const formData = new FormData();
      formData.append('file', file);
      if (parentId) {
        formData.append('parent_id', parentId);
      }

      // 发送上传请求
      const response = await fetch(getApiUrl(API_CONFIG.endpoints.files.upload), {
        method: 'POST',
        body: formData,
      });

      setUploadState({ uploading: true, progress: 100, error: null });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(errorData.detail || `上传失败: ${response.status}`);
      }

      const data = await response.json();

      if (data.status === 'ok' && data.data) {
        setUploadState({ uploading: false, progress: 100, error: null });
        return data.data as FileNode;
      } else {
        throw new Error('Invalid API response format');
      }
    } catch (err) {
      console.error('Upload failed:', err);
      const error = err instanceof Error ? err : new Error('上传失败');
      setUploadState({ uploading: false, progress: 0, error });
      return null;
    }
  }, []);

  return {
    uploadState,
    uploadFile,
  };
}