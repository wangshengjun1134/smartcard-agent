import { useState, useCallback, useMemo } from 'react';
import { KnowledgeFormData } from '../types/knowledge';

interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
}

type ValidationRules = Partial<Record<keyof KnowledgeFormData, ValidationRule>>;

interface UseFormValidationReturn {
  isValid: boolean;
  errors: Record<string, string>;
  validate: (data: KnowledgeFormData, hasFile: boolean) => boolean;
  clearErrors: () => void;
}

// 默认验证规则
const defaultRules: ValidationRules = {
  title: { required: true, minLength: 2 },
};

/**
 * 表单验证 Hook
 */
export function useFormValidation(customRules?: ValidationRules): UseFormValidationReturn {
  const [errors, setErrors] = useState<Record<string, string>>({});

  // 合并验证规则
  const rules = useMemo(() => {
    return { ...defaultRules, ...customRules };
  }, [customRules]);

  // 验证单个字段
  const validateField = useCallback(
    (_field: keyof KnowledgeFormData, value: string | string[], rule: ValidationRule): string | null => {
      // 必填验证
      if (rule.required) {
        if (typeof value === 'string' && value.trim() === '') {
          return '此字段为必填项';
        }
        if (Array.isArray(value) && value.length === 0) {
          return '此字段为必填项';
        }
      }

      // 最小长度验证 (仅字符串)
      if (rule.minLength && typeof value === 'string') {
        if (value.trim().length < rule.minLength) {
          return `最少需要 ${rule.minLength} 个字符`;
        }
      }

      // 最大长度验证 (仅字符串)
      if (rule.maxLength && typeof value === 'string') {
        if (value.trim().length > rule.maxLength) {
          return `最多 ${rule.maxLength} 个字符`;
        }
      }

      return null;
    },
    []
  );

  // 验证整个表单
  const validate = useCallback(
    (data: KnowledgeFormData, hasFile: boolean): boolean => {
      const newErrors: Record<string, string> = {};

      // 验证文件是否已选择
      if (!hasFile) {
        newErrors.file = '请选择要上传的文件';
      }

      // 验证每个字段
      for (const [field, rule] of Object.entries(rules)) {
        if (rule) {
          const value = data[field as keyof KnowledgeFormData];
          const error = validateField(field as keyof KnowledgeFormData, value as string | string[], rule);
          if (error) {
            newErrors[field] = error;
          }
        }
      }

      setErrors(newErrors);
      return Object.keys(newErrors).length === 0;
    },
    [rules, validateField]
  );

  // 清除错误
  const clearErrors = useCallback(() => {
    setErrors({});
  }, []);

  // 计算是否有效
  const isValid = Object.keys(errors).length === 0;

  return {
    isValid,
    errors,
    validate,
    clearErrors,
  };
}