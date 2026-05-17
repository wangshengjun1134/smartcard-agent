import { FileType } from '../types/file';

/**
 * 文件图标映射配置
 */
export const iconMap: Record<FileType, { icon: string; color: string }> = {
  folder: { icon: '📁', color: '#FFB900' },
  pdf: { icon: '📄', color: '#E74C3C' },
  word: { icon: '📝', color: '#2B579A' },
  markdown: { icon: '📝', color: '#083FA1' },
  image: { icon: '🖼️', color: '#9B59B6' },
  text: { icon: '📄', color: '#95A5A6' },
  unknown: { icon: '📄', color: '#BDC3C7' },
};

/**
 * 文件扩展名到类型的映射
 */
const extensionMap: Record<string, FileType> = {
  // 文件夹
  '': 'folder',
  // PDF
  'pdf': 'pdf',
  // Word
  'doc': 'word',
  'docx': 'word',
  'docm': 'word',
  'dot': 'word',
  'dotx': 'word',
  'dotm': 'word',
  // Markdown
  'md': 'markdown',
  'mdx': 'markdown',
  'markdown': 'markdown',
  // 图片
  'jpg': 'image',
  'jpeg': 'image',
  'png': 'image',
  'gif': 'image',
  'bmp': 'image',
  'webp': 'image',
  'svg': 'image',
  'ico': 'image',
  // 文本
  'txt': 'text',
  'log': 'text',
  'csv': 'text',
  'json': 'text',
  'xml': 'text',
  'yaml': 'text',
  'yml': 'text',
  'ini': 'text',
  'conf': 'text',
  'cfg': 'text',
  // 代码文件也视为文本
  'js': 'text',
  'ts': 'text',
  'jsx': 'text',
  'tsx': 'text',
  'py': 'text',
  'java': 'text',
  'c': 'text',
  'cpp': 'text',
  'h': 'text',
  'hpp': 'text',
  'cs': 'text',
  'go': 'text',
  'rs': 'text',
  'rb': 'text',
  'php': 'text',
  'swift': 'text',
  'kt': 'text',
  'kts': 'text',
  'sh': 'text',
  'bash': 'text',
  'zsh': 'text',
  'ps1': 'text',
  'bat': 'text',
  'cmd': 'text',
  'sql': 'text',
  'html': 'text',
  'htm': 'text',
  'css': 'text',
  'scss': 'text',
  'sass': 'text',
  'less': 'text',
};

/**
 * 根据文件扩展名获取文件类型
 * @param extension 文件扩展名 (不含点号，如 "pdf")
 * @returns 文件类型
 */
export function getFileTypeFromExtension(extension: string): FileType {
  const ext = extension.toLowerCase().replace(/^\./, '');
  return extensionMap[ext] || 'unknown';
}

/**
 * 根据文件名获取文件类型
 * @param fileName 文件名 (如 "document.pdf")
 * @returns 文件类型
 */
export function getFileTypeFromName(fileName: string): FileType {
  if (!fileName || fileName.endsWith('/')) {
    return 'folder';
  }

  const lastDotIndex = fileName.lastIndexOf('.');
  if (lastDotIndex === -1 || lastDotIndex === 0) {
    return 'unknown';
  }

  const extension = fileName.slice(lastDotIndex + 1);
  return getFileTypeFromExtension(extension);
}

/**
 * 获取文件图标配置
 * @param type 文件类型
 * @returns 图标和颜色配置
 */
export function getFileIconConfig(type: FileType) {
  return iconMap[type] || iconMap.unknown;
}