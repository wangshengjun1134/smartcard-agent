import { useState, useCallback } from 'react';
import { calculateFileHash } from '../utils/fileHash';

interface UseFileSelectionReturn {
  file: File | null;
  fileHash: string;
  isCalculatingHash: boolean;
  selectFile: (file: File) => void;
  clearFile: () => void;
}

/**
 * 文件选择 Hook
 * 管理文件选择状态和哈希计算
 */
export function useFileSelection(): UseFileSelectionReturn {
  const [file, setFile] = useState<File | null>(null);
  const [fileHash, setFileHash] = useState<string>('');
  const [isCalculatingHash, setIsCalculatingHash] = useState(false);

  // 选择文件
  const selectFile = useCallback(async (selectedFile: File) => {
    setFile(selectedFile);
    setFileHash('');
    setIsCalculatingHash(true);

    // 计算文件哈希
    try {
      const hash = await calculateFileHash(selectedFile);
      setFileHash(hash);
    } catch (error) {
      console.error('Failed to calculate file hash:', error);
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