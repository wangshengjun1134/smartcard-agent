/**
 * 文件操作工具函数
 * 提供文件查找、格式化等通用操作
 */

import { FileNode } from '../types/file';

/**
 * 在文件树中查找指定路径的文件夹
 * @param nodes 文件节点数组
 * @param path 要查找的路径
 * @returns 找到的文件夹节点，未找到返回null
 */
export function findFolderByPath(
  nodes: FileNode[],
  path: string
): FileNode | null {
  for (const node of nodes) {
    if (node.path === path && node.isFolder) {
      return node;
    }
    if (node.children) {
      const found = findFolderByPath(node.children, path);
      if (found) return found;
    }
  }
  return null;
}

/**
 * 在文件树中查找指定ID的节点
 * @param nodes 文件节点数组
 * @param id 要查找的ID
 * @returns 找到的节点，未找到返回null
 */
export function findNodeById(
  nodes: FileNode[],
  id: string
): FileNode | null {
  for (const node of nodes) {
    if (node.id === id) {
      return node;
    }
    if (node.children) {
      const found = findNodeById(node.children, id);
      if (found) return found;
    }
  }
  return null;
}

/**
 * 获取文件扩展名
 * @param fileName 文件名
 * @returns 扩展名（不含点号）
 */
export function getFileExtension(fileName: string): string {
  const lastDotIndex = fileName.lastIndexOf('.');
  if (lastDotIndex === -1 || lastDotIndex === 0) {
    return '';
  }
  return fileName.slice(lastDotIndex + 1).toLowerCase();
}

/**
 * 格式化文件大小
 * @param bytes 文件大小（字节）
 * @returns 格式化后的字符串
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

/**
 * 生成唯一的文件夹名称
 * @param existingNames 已存在的名称列表
 * @param baseName 基础名称（默认"新建文件夹"）
 * @returns 唯一的文件夹名称
 */
export function generateUniqueFolderName(
  existingNames: string[],
  baseName: string = '新建文件夹'
): string {
  if (!existingNames.includes(baseName)) {
    return baseName;
  }
  
  let counter = 2;
  while (existingNames.includes(`${baseName} (${counter})`)) {
    counter++;
  }
  return `${baseName} (${counter})`;
}

/**
 * 获取当前目录下的文件夹名称列表
 * @param files 文件列表
 * @returns 文件夹名称数组
 */
export function getFolderNames(files: FileNode[]): string[] {
  return files
    .filter(f => f.isFolder)
    .map(f => f.name);
}

/**
 * 构建面包屑导航路径
 * @param currentPath 当前路径
 * @param prefixToRemove 要移除的路径前缀（如 "/docs"）
 * @returns 面包屑数组
 */
export function buildBreadcrumb(
  currentPath: string,
  prefixToRemove: string = '/docs'
): Array<{ name: string; path: string }> {
  if (!currentPath) {
    return [];
  }

  const normalizedPath = currentPath.replace(new RegExp(`^${prefixToRemove}`), '');
  const parts = normalizedPath.split('/').filter(Boolean);

  const crumbs: Array<{ name: string; path: string }> = [];
  let accumulatedPath = '';
  
  for (const part of parts) {
    accumulatedPath += `${prefixToRemove}/${part}`;
    crumbs.push({ name: part, path: accumulatedPath });
  }

  return crumbs;
}

/**
 * 获取上级路径
 * @param currentPath 当前路径
 * @param prefixToRemove 要移除的路径前缀
 * @returns 上级路径，根目录返回空字符串
 */
export function getParentPath(
  currentPath: string,
  prefixToRemove: string = '/docs'
): string {
  const normalizedPath = currentPath.replace(new RegExp(`^${prefixToRemove}`), '');
  const parts = normalizedPath.split('/').filter(Boolean);
  parts.pop();

  if (parts.length === 0) {
    return '';
  }
  return `${prefixToRemove}/${parts.join('/')}`;
}

/**
 * 获取文件图标emoji
 * @param fileName 文件名
 * @returns 图标emoji
 */
export function getFileIconEmoji(fileName: string): string {
  const ext = getFileExtension(fileName);

  if (ext === 'pdf') return '📄';
  if (['doc', 'docx', 'docm', 'dot', 'dotx', 'dotm'].includes(ext)) return '📝';
  if (['md', 'mdx', 'markdown'].includes(ext)) return '📝';
  if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico'].includes(ext)) return '🖼️';
  if (['txt', 'log', 'csv', 'json', 'xml', 'yaml', 'yml', 'ini', 'conf', 'cfg'].includes(ext)) return '📄';

  return '📄';
}

/**
 * 判断文件是否为图片
 * @param fileName 文件名
 * @returns 是否为图片文件
 */
export function isImageFile(fileName: string): boolean {
  const ext = getFileExtension(fileName);
  return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico'].includes(ext);
}

/**
 * 判断文件类型是否支持上传
 * @param fileName 文件名
 * @returns 是否支持
 */
export function isSupportedUploadType(fileName: string): boolean {
  const ext = getFileExtension(fileName);
  const supportedExtensions = [
    'pdf', 'doc', 'docx', 'md', 'txt', 'markdown',
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg',
  ];
  return supportedExtensions.includes(ext);
}