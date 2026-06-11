/**
 * 知识库/文档相关类型定义
 */

/**
 * 文档处理状态
 */
export type DocumentStatus =
  | 'uploaded'
  | 'parsing'
  | 'chunking'
  | 'embedding'
  | 'ready'
  | 'error';

/**
 * 知识库/命名空间
 */
export interface KnowledgeBase {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * 文档记录
 */
export interface Document {
  id: string;
  kb_id: string;
  filename: string;
  file_path?: string;
  file_size?: number;
  mime_type?: string;
  status: DocumentStatus;
  error_message?: string;
  version: number;
  title?: string;
  source?: string;
  language: string;
  tags?: string[];
  permissions?: Record<string, unknown>;
  effective_from?: string;
  effective_until?: string;
  custom_meta?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
  uploadedBy?: string;
}

/**
 * 知识库表单数据 (用于上传文档)
 * 字段与 documents 表结构保持一致
 */
export interface KnowledgeFormData {
  // 自动填充字段
  file_name: string;        // 原始文件名
  file_hash: string;        // 文件哈希 (SHA-256)

  // documents 表字段
  title: string;            // 文档标题 (必填)
  source?: string;          // 来源说明 (如 "3GPP TS 102.221")
  language: string;         // 语言 (默认 zh)
  tags: string[];           // 标签列表
}

/**
 * 上传响应
 */
export interface UploadResponse {
  success: boolean;
  file_id: string;          // 上传后的文件ID
  message: string;
}

/**
 * 下拉选项接口
 */
export interface SelectOption {
  value: string;
  label: string;
}

/**
 * 语言选项常量
 */
export const LANGUAGES: SelectOption[] = [
  { value: 'zh', label: '中文' },
  { value: 'en', label: 'English' },
];

/**
 * 默认表单数据
 */
export const DEFAULT_FORM_DATA: KnowledgeFormData = {
  file_name: '',
  file_hash: '',
  title: '',
  source: '',
  language: 'zh',
  tags: [],
};
