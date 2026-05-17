/**
 * 文件类型枚举
 */
export type FileType =
  | 'folder'
  | 'pdf'
  | 'word'
  | 'markdown'
  | 'image'
  | 'text'
  | 'unknown';

/**
 * 文件节点数据结构
 */
export interface FileNode {
  id: string;                  // 文件唯一标识
  name: string;                // 文件名
  type: FileType;              // 文件类型
  path: string;                // 文件路径
  isFolder: boolean;           // 是否文件夹
  size?: number;               // 文件大小 (字节)
  createdAt?: string;          // 创建时间
  modifiedAt?: string;         // 修改时间
  children?: FileNode[];       // 子节点 (文件夹才有)
}

/**
 * 向量分片数据结构
 */
export interface VectorChunk {
  id: string;                  // 分片 ID
  content: string;             // 分片内容 (预览)
  startPosition: number;       // 起始位置
  endPosition: number;         // 结束位置
  indexedAt: string;           // 索引时间
}

/**
 * 文件详情数据结构 (包含向量分片)
 */
export interface FileDetail extends FileNode {
  chunks: VectorChunk[];       // 向量分片列表
  chunkCount: number;          // 分片数量
  indexed: boolean;            // 是否已索引
}

/**
 * 视图模式类型
 */
export type ViewMode = 'icon' | 'tree';