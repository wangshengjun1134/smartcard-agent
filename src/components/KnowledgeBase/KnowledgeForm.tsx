import { KnowledgeFormData, ORGANIZATIONS, DOC_TYPES, CATEGORIES } from '../../types/knowledge';
import { TagInput } from './TagInput';
import { CategorySelect } from './CategorySelect';

interface KnowledgeFormProps {
  fileName: string;
  fileHash: string;
  formData: KnowledgeFormData;
  errors: Record<string, string>;
  onChange: (data: Partial<KnowledgeFormData>) => void;
}

/**
 * 知识库元数据表单组件
 */
export function KnowledgeForm({
  fileName,
  fileHash,
  formData,
  errors,
  onChange,
}: KnowledgeFormProps) {
  // 处理输入字段变更
  const handleInputChange = (field: keyof KnowledgeFormData, value: string) => {
    onChange({ [field]: value });
  };

  // 处理标签变更
  const handleTagsChange = (tags: string[]) => {
    onChange({ tags });
  };

  return (
    <div className="knowledge-form">
      {/* 自动填充字段 */}
      <div className="form-section mb-4">
        <div className="form-section-title text-[13px] font-medium text-[#4a4a4a] dark:text-[#b3b3b3] mb-3">
          文件信息
        </div>

        {/* 文件名 (只读) */}
        <div className="form-field mb-3">
          <label className="form-label block text-[13px] text-[#4a4a4a] dark:text-[#b3b3b3] mb-1">
            文件名
          </label>
          <input
            type="text"
            value={fileName}
            disabled
            className="form-input w-full px-3 py-2 border border-[#ececee] dark:border-[#333333] rounded-lg text-[13px] bg-[#f7f8fa] dark:bg-[#333333] text-[#1a1a1a] dark:text-white disabled:opacity-70"
          />
        </div>

        {/* 文件哈希 (只读) */}
        <div className="form-field mb-3">
          <label className="form-label block text-[13px] text-[#4a4a4a] dark:text-[#b3b3b3] mb-1">
            文件哈希
          </label>
          <input
            type="text"
            value={fileHash ? `${fileHash.slice(0, 16)}...` : ''}
            disabled
            placeholder="计算中..."
            className="form-input w-full px-3 py-2 border border-[#ececee] dark:border-[#333333] rounded-lg text-[13px] bg-[#f7f8fa] dark:bg-[#333333] text-[#1a1a1a] dark:text-white font-mono disabled:opacity-70"
          />
        </div>
      </div>

      {/* 规范识别字段 */}
      <div className="form-section mb-4">
        <div className="form-section-title text-[13px] font-medium text-[#4a4a4a] dark:text-[#b3b3b3] mb-3">
          规范信息
        </div>

        {/* 文档标题 (必填) */}
        <div className="form-field mb-3">
          <label className="form-label block text-[13px] text-[#4a4a4a] dark:text-[#b3b3b3] mb-1">
            文档标题 <span className="text-[#e74c3c]">*</span>
          </label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => handleInputChange('title', e.target.value)}
            placeholder="请输入文档标题"
            className={`form-input w-full px-3 py-2 border rounded-lg text-[13px] bg-white dark:bg-[#222222] text-[#1a1a1a] dark:text-white outline-none transition-colors ${
              errors.title
                ? 'border-[#e74c3c] focus:border-[#e74c3c]'
                : 'border-[#ececee] dark:border-[#333333] focus:border-[#4b6ef3]'
            }`}
          />
          {errors.title && (
            <div className="form-error text-[12px] text-[#e74c3c] mt-1">{errors.title}</div>
          )}
        </div>

        {/* 规范编号 */}
        <div className="form-field mb-3">
          <label className="form-label block text-[13px] text-[#4a4a4a] dark:text-[#b3b3b3] mb-1">
            规范编号
          </label>
          <input
            type="text"
            value={formData.spec_number}
            onChange={(e) => handleInputChange('spec_number', e.target.value)}
            placeholder="如 TS 102 221、SGP.23"
            className="form-input w-full px-3 py-2 border border-[#ececee] dark:border-[#333333] rounded-lg text-[13px] bg-white dark:bg-[#222222] text-[#1a1a1a] dark:text-white outline-none focus:border-[#4b6ef3] transition-colors"
          />
        </div>

        {/* 版本号 */}
        <div className="form-field mb-3">
          <label className="form-label block text-[13px] text-[#4a4a4a] dark:text-[#b3b3b3] mb-1">
            版本号
          </label>
          <input
            type="text"
            value={formData.version}
            onChange={(e) => handleInputChange('version', e.target.value)}
            placeholder="如 v17.0.0、1.16"
            className="form-input w-full px-3 py-2 border border-[#ececee] dark:border-[#333333] rounded-lg text-[13px] bg-white dark:bg-[#222222] text-[#1a1a1a] dark:text-white outline-none focus:border-[#4b6ef3] transition-colors"
          />
        </div>

        {/* 发布组织 */}
        <div className="form-field mb-3">
          <label className="form-label block text-[13px] text-[#4a4a4a] dark:text-[#b3b3b3] mb-1">
            发布组织
          </label>
          <CategorySelect
            value={formData.organization}
            onChange={(value) => handleInputChange('organization', value)}
            options={ORGANIZATIONS.map((org) => ({ value: org, label: org }))}
            placeholder="请选择组织"
          />
        </div>

        {/* 文档类型 */}
        <div className="form-field mb-3">
          <label className="form-label block text-[13px] text-[#4a4a4a] dark:text-[#b3b3b3] mb-1">
            文档类型
          </label>
          <CategorySelect
            value={formData.doc_type}
            onChange={(value) => handleInputChange('doc_type', value)}
            options={DOC_TYPES}
            placeholder="请选择类型"
          />
        </div>
      </div>

      {/* 分类字段 */}
      <div className="form-section">
        <div className="form-section-title text-[13px] font-medium text-[#4a4a4a] dark:text-[#b3b3b3] mb-3">
          分类信息
        </div>

        {/* 标签 */}
        <div className="form-field mb-3">
          <label className="form-label block text-[13px] text-[#4a4a4a] dark:text-[#b3b3b3] mb-1">
            标签
          </label>
          <TagInput
            tags={formData.tags}
            onChange={handleTagsChange}
            placeholder="输入标签后按 Enter 添加"
          />
          <div className="form-hint text-[12px] text-[#999] dark:text-[#808080] mt-1">
            如: 5G, eSIM, 鉴权
          </div>
        </div>

        {/* 分类 */}
        <div className="form-field mb-3">
          <label className="form-label block text-[13px] text-[#4a4a4a] dark:text-[#b3b3b3] mb-1">
            分类
          </label>
          <CategorySelect
            value={formData.category}
            onChange={(value) => handleInputChange('category', value)}
            options={CATEGORIES}
            placeholder="请选择分类"
          />
        </div>
      </div>
    </div>
  );
}