import { useState, useCallback } from 'react';
import { Document } from '../types/knowledge';
import { getApiUrl, API_CONFIG, FILE_UPLOAD_CONSTRAINTS } from '../config/api';

interface UploadState {
  uploading: boolean;
  progress: number; // 0-100
  error: Error | null;
}

interface UploadParams {
  kb_id: string;
  folder_id?: string;
  title?: string;
  source?: string;
  language?: string;
  tags?: string[];
  effective_from?: string;
  effective_until?: string;
  uploaded_by?: string;
}

interface UseFileUploadReturn {
  uploadState: UploadState;
  uploadFile: (file: File, params: UploadParams) => Promise<Document | null>;
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
  const uploadFile = useCallback(async (file: File, params: UploadParams): Promise<Document | null> => {
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
      formData.append('kb_id', params.kb_id);
      if (params.folder_id) {
        formData.append('folder_id', params.folder_id);
      }
      if (params.title) {
        formData.append('title', params.title);
      }
      if (params.source) {
        formData.append('source', params.source);
      }
      if (params.language) {
        formData.append('language', params.language);
      }
      if (params.tags && params.tags.length > 0) {
        formData.append('tags', JSON.stringify(params.tags));
      }
      if (params.effective_from) {
        formData.append('effective_from', params.effective_from);
      }
      if (params.effective_until) {
        formData.append('effective_until', params.effective_until);
      }
      if (params.uploaded_by) {
        formData.append('uploaded_by', params.uploaded_by);
      }

      // 发送上传请求
      const response = await fetch(getApiUrl(API_CONFIG.endpoints.documents.upload), {
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
        return data.data as Document;
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