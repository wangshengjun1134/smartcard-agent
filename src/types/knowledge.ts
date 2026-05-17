/**
 * 知识库上传相关类型定义
 */

/**
 * 下拉选项接口
 */
export interface SelectOption {
  value: string;
  label: string;
}

/**
 * 知识库表单数据
 */
export interface KnowledgeFormData {
  // 自动填充字段
  file_name: string;        // 原始文件名
  file_hash: string;        // 文件哈希 (SHA-256)

  // 规范识别字段
  title: string;            // 文档标题 (必填)
  spec_number: string;      // 规范编号
  version: string;          // 版本号
  organization: string;     // 发布组织
  doc_type: string;         // 文档类型

  // 分类字段
  tags: string[];           // 标签
  category: string;         // 分类
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
 * 组织选项常量
 */
export const ORGANIZATIONS: string[] = [
  'GSMA',
  'ETSI',
  '3GPP',
  'ISO',
  'ITU',
  '运营商自定义',
  '其他',
];

/**
 * 文档类型选项常量
 */
export const DOC_TYPES: SelectOption[] = [
  { value: 'spec', label: '规范' },
  { value: 'test-spec', label: '测试规范' },
  { value: 'tech-report', label: '技术报告' },
  { value: 'blog', label: '博客' },
  { value: 'other', label: '其他' },
];

/**
 * 分类选项常量
 */
export const CATEGORIES: SelectOption[] = [
  { value: 'physical', label: 'SIM卡物理接口' },
  { value: 'protocol', label: '协议' },
  { value: 'security', label: '安全' },
  { value: 'test', label: '测试' },
];

/**
 * 默认表单数据
 */
export const DEFAULT_FORM_DATA: KnowledgeFormData = {
  file_name: '',
  file_hash: '',
  title: '',
  spec_number: '',
  version: '',
  organization: '',
  doc_type: '',
  tags: [],
  category: '',
};