import { useState, useEffect, useCallback } from 'react';
import { KnowledgeFormData, DEFAULT_FORM_DATA } from '../../types/knowledge';
import { useFileUpload } from '../../hooks/useFileUpload';
import { useFormValidation } from '../../hooks/useFormValidation';
import { FileUploadZone } from './FileUploadZone';
import { KnowledgeForm } from './KnowledgeForm';
import { DrawerFooter } from './DrawerFooter';

interface AddKnowledgeDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (file: File, data: KnowledgeFormData) => Promise<void>;
}

/**
 * 添加知识库抽屉组件
 */
export function AddKnowledgeDrawer({
  isOpen,
  onClose,
  onSubmit,
}: AddKnowledgeDrawerProps) {
  // 文件上传状态
  const { file, fileHash, isCalculatingHash, selectFile, clearFile } = useFileUpload();

  // 表单数据状态
  const [formData, setFormData] = useState<KnowledgeFormData>(DEFAULT_FORM_DATA);

  // 表单验证
  const { errors, validate, clearErrors } = useFormValidation();

  // 提交状态
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 抽屉打开时重置状态
  useEffect(() => {
    if (isOpen) {
      clearFile();
      setFormData(DEFAULT_FORM_DATA);
      clearErrors();
      setIsSubmitting(false);
    }
  }, [isOpen, clearFile, clearErrors]);

  // ESC 键关闭抽屉
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !isSubmitting) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isSubmitting, onClose]);

  // 文件选择后更新表单数据
  const handleFileSelect = useCallback(
    (selectedFile: File) => {
      selectFile(selectedFile);
      // 自动填充文件名
      setFormData((prev) => ({
        ...prev,
        file_name: selectedFile.name,
      }));
    },
    [selectFile]
  );

  // 文件清除
  const handleClearFile = useCallback(() => {
    clearFile();
    setFormData((prev) => ({
      ...prev,
      file_name: '',
      file_hash: '',
    }));
  }, [clearFile]);

  // 表单字段变更
  const handleFormChange = useCallback(
    (data: Partial<KnowledgeFormData>) => {
      setFormData((prev) => ({
        ...prev,
        ...data,
      }));
    },
    []
  );

  // 哈希计算完成后更新表单
  useEffect(() => {
    if (fileHash && !isCalculatingHash) {
      setFormData((prev) => ({
        ...prev,
        file_hash: fileHash,
      }));
    }
  }, [fileHash, isCalculatingHash]);

  // 取消操作
  const handleCancel = useCallback(() => {
    if (!isSubmitting) {
      onClose();
    }
  }, [isSubmitting, onClose]);

  // 确认提交
  const handleConfirm = useCallback(async () => {
    // 验证表单
    const isValid = validate(formData, !!file);
    if (!isValid) {
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(file!, formData);
      onClose();
    } catch (error) {
      console.error('Upload failed:', error);
      // TODO: 显示错误提示
    } finally {
      setIsSubmitting(false);
    }
  }, [formData, file, validate, onSubmit, onClose]);

  // 点击遮罩关闭
  const handleOverlayClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget && !isSubmitting) {
        onClose();
      }
    },
    [isSubmitting, onClose]
  );

  // 确认按钮禁用条件
  const isConfirmDisabled = !file || isCalculatingHash || !formData.title.trim();

  return (
    <>
      {/* 遮罩层 */}
      {isOpen && (
        <div
          className="drawer-overlay absolute inset-0 bg-[rgba(0,0,0,0.3)] z-[99]"
          onClick={handleOverlayClick}
        />
      )}

      {/* 抽屉容器 */}
      <div
        className={`add-knowledge-drawer bg-white dark:bg-[#222222] border-l border-[#ececee] dark:border-[#333333] flex flex-col transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* 头部 */}
        <div className="drawer-header h-[45px] flex items-center justify-between px-4 border-b border-[#ececee] dark:border-[#333333]">
          <span className="text-[14px] font-medium text-[#1a1a1a] dark:text-white">
            添加知识
          </span>
          <button
            type="button"
            onClick={handleCancel}
            disabled={isSubmitting}
            className="w-[28px] h-[28px] flex items-center justify-center rounded-full hover:bg-[#f7f8fa] dark:hover:bg-[#333333] text-[#999] dark:text-[#808080] transition-colors disabled:opacity-50"
            aria-label="关闭"
          >
            ×
          </button>
        </div>

        {/* 内容区域 */}
        <div className="drawer-content flex-1 overflow-y-auto p-4">
          {/* 文件上传区域 */}
          <div className="mb-4">
            <FileUploadZone
              file={file}
              fileHash={fileHash}
              isCalculatingHash={isCalculatingHash}
              onFileSelect={handleFileSelect}
              onClearFile={handleClearFile}
            />
            {errors.file && (
              <div className="text-[12px] text-[#e74c3c] mt-2">{errors.file}</div>
            )}
          </div>

          {/* 表单 */}
          {file && (
            <KnowledgeForm
              fileName={formData.file_name}
              fileHash={formData.file_hash}
              formData={formData}
              errors={errors}
              onChange={handleFormChange}
            />
          )}
        </div>

        {/* 底部按钮 */}
        {file && (
          <DrawerFooter
            loading={isSubmitting}
            disabled={isConfirmDisabled}
            onCancel={handleCancel}
            onConfirm={handleConfirm}
          />
        )}
      </div>
    </>
  );
}