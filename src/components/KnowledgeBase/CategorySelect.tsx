import { useState, useRef, useEffect } from 'react';
import { SelectOption } from '../../types/knowledge';

interface CategorySelectProps {
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
}

/**
 * 分类下拉选择组件
 * 支持展开/折叠、选中状态高亮、点击外部关闭
 */
export function CategorySelect({
  value,
  onChange,
  options,
  placeholder = '请选择',
}: CategorySelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // 获取当前选中选项的标签
  const selectedOption = options.find((opt) => opt.value === value);
  const selectedLabel = selectedOption?.label || placeholder;

  // 点击外部关闭下拉框
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 选择选项
  const handleSelect = (optionValue: string) => {
    onChange(optionValue);
    setIsOpen(false);
  };

  // 切换下拉框
  const handleToggle = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div ref={containerRef} className="category-select relative">
      {/* 触发器 */}
      <div
        className="select-trigger flex items-center justify-between px-3 py-2 border border-[#ececee] dark:border-[#333333] rounded-lg cursor-pointer bg-white dark:bg-[#222222] transition-colors hover:border-[#4b6ef3]"
        onClick={handleToggle}
      >
        <span
          className={`text-[13px] ${
            selectedOption
              ? 'text-[#1a1a1a] dark:text-white'
              : 'text-[#999] dark:text-[#808080]'
          }`}
        >
          {selectedLabel}
        </span>
        <svg
          className={`w-4 h-4 text-[#999] dark:text-[#808080] transition-transform ${
            isOpen ? 'rotate-180' : ''
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      {/* 下拉列表 */}
      {isOpen && (
        <div
          className="select-dropdown absolute top-full left-0 right-0 mt-1 bg-white dark:bg-[#222222] border border-[#ececee] dark:border-[#333333] rounded-lg z-10 shadow-lg max-h-[200px] overflow-y-auto"
        >
          {options.map((option) => (
            <div
              key={option.value}
              className={`select-option px-3 py-2 cursor-pointer text-[13px] transition-colors ${
                option.value === value
                  ? 'bg-[#4b6ef3]/10 text-[#4b6ef3]'
                  : 'text-[#1a1a1a] dark:text-white hover:bg-[#f7f8fa] dark:hover:bg-[#333333]'
              }`}
              onClick={() => handleSelect(option.value)}
            >
              {option.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}