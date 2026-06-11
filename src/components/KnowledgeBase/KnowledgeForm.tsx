import { KnowledgeFormData, LANGUAGES } from '../../types/knowledge';
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
 * 字段与 documents 表结构保持一致
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
      {/* 文件信息 */}
      <div className="form-section mb-4">
        <div className="form-section-title text-[13px] font-bold text-[#4a4a4a] dark:text-[#b3b3b3] mb-3">
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

      {/* 文档元数据 */}
      <div className="form-section mb-4">
        <div className="form-section-title text-[13px] font-bold text-[#4a4a4a] dark:text-[#b3b3b3] mb-3">
          文档信息
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

        {/* 来源说明 */}
        <div className="form-field mb-3">
          <label className="form-label block text-[13px] text-[#4a4a4a] dark:text-[#b3b3b3] mb-1">
            来源
          </label>
          <input
            type="text"
            value={formData.source || ''}
            onChange={(e) => handleInputChange('source', e.target.value)}
            placeholder="如 3GPP TS 102.221、GSMA SGP.23"
            className="form-input w-full px-3 py-2 border border-[#ececee] dark:border-[#333333] rounded-lg text-[13px] bg-white dark:bg-[#222222] text-[#1a1a1a] dark:text-white outline-none focus:border-[#4b6ef3] transition-colors"
          />
        </div>

        {/* 语言 */}
        <div className="form-field mb-3">
          <label className="form-label block text-[13px] text-[#4a4a4a] dark:text-[#b3b3b3] mb-1">
            语言
          </label>
          <CategorySelect
            value={formData.language}
            onChange={(value) => handleInputChange('language', value)}
            options={LANGUAGES}
            placeholder="请选择语言"
          />
        </div>
      </div>

      {/* 标签 */}
      <div className="form-section">
        <div className="form-section-title text-[13px] font-bold text-[#4a4a4a] dark:text-[#b3b3b3] mb-3">
          标签
        </div>

        <div className="form-field mb-3">
          <TagInput
            tags={formData.tags}
            onChange={handleTagsChange}
            placeholder="输入标签后按 Enter 添加"
          />
          <div className="form-hint text-[12px] text-[#999] dark:text-[#808080] mt-1">
            如: 5G, eSIM, 鉴权
          </div>
        </div>
      </div>
    </div>
  );
}
