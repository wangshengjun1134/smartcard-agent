import { useState, useCallback } from 'react';
import { UploadResponse } from '../types/knowledge';

/**
 * 计算文件 SHA-256 哈希
 */
async function calculateHash(file: File): Promise<string> {
  const arrayBuffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
  return hashHex;
}

interface UseFileUploadReturn {
  file: File | null;
  fileHash: string;
  isCalculatingHash: boolean;
  selectFile: (file: File) => void;
  clearFile: () => void;
}

/**
 * 文件上传 Hook
 * 处理文件选择和哈希计算
 */
export function useFileUpload(): UseFileUploadReturn {
  const [file, setFile] = useState<File | null>(null);
  const [fileHash, setFileHash] = useState<string>('');
  const [isCalculatingHash, setIsCalculatingHash] = useState(false);

  // 选择文件
  const selectFile = useCallback(async (selectedFile: File) => {
    setFile(selectedFile);
    setFileHash('');
    setIsCalculatingHash(true);

    try {
      const hash = await calculateHash(selectedFile);
      setFileHash(hash);
    } catch (error) {
      console.error('Failed to calculate hash:', error);
      setFileHash('');
    } finally {
      setIsCalculatingHash(false);
    }
  }, []);

  // 清除文件
  const clearFile = useCallback(() => {
    setFile(null);
    setFileHash('');
    setIsCalculatingHash(false);
  }, []);

  return {
    file,
    fileHash,
    isCalculatingHash,
    selectFile,
    clearFile,
  };
}

/**
 * Mock 上传函数 (预留 API 集成)
 */
export async function mockUploadKnowledge(
  _file: File,
  _metadata: object
): Promise<UploadResponse> {
  // 模拟上传延迟
  await new Promise((resolve) => setTimeout(resolve, 1500));

  // 模拟成功响应
  return {
    success: true,
    file_id: `file-${Date.now()}`,
    message: '上传成功',
  };
}