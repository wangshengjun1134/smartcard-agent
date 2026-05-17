import { useState, useRef, KeyboardEvent } from 'react';

interface TagInputProps {
  tags: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
}

/**
 * 标签输入组件
 * 支持添加和删除标签
 */
export function TagInput({ tags, onChange, placeholder = '输入标签...' }: TagInputProps) {
  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // 添加标签
  const addTag = (tag: string) => {
    const trimmedTag = tag.trim();
    if (trimmedTag && !tags.includes(trimmedTag)) {
      onChange([...tags, trimmedTag]);
      setInputValue('');
    }
  };

  // 删除标签
  const removeTag = (index: number) => {
    const newTags = [...tags];
    newTags.splice(index, 1);
    onChange(newTags);
  };

  // 处理键盘事件
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTag(inputValue);
    } else if (e.key === 'Backspace' && inputValue === '' && tags.length > 0) {
      // 输入框为空时按 Backspace 删除最后一个标签
      removeTag(tags.length - 1);
    }
  };

  // 点击添加按钮
  const handleAddClick = () => {
    addTag(inputValue);
    inputRef.current?.focus();
  };

  // 点击容器聚焦输入框
  const handleContainerClick = () => {
    inputRef.current?.focus();
  };

  return (
    <div
      className="tag-input-container flex flex-wrap gap-2 p-2 border border-[#ececee] dark:border-[#333333] rounded-lg min-h-[40px] cursor-text"
      onClick={handleContainerClick}
    >
      {/* 已有标签 */}
      {tags.map((tag, index) => (
        <span
          key={`${tag}-${index}`}
          className="tag-chip inline-flex items-center gap-1 px-2 py-1 bg-[#f7f8fa] dark:bg-[#333333] rounded text-[13px] text-[#1a1a1a] dark:text-white"
        >
          {tag}
          <button
            type="button"
            className="remove-btn cursor-pointer opacity-60 hover:opacity-100 text-[#999] dark:text-[#808080] leading-none"
            onClick={(e) => {
              e.stopPropagation();
              removeTag(index);
            }}
            aria-label={`删除标签 ${tag}`}
          >
            ×
          </button>
        </span>
      ))}

      {/* 输入框 */}
      <input
        ref={inputRef}
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={tags.length === 0 ? placeholder : ''}
        className="tag-input flex-1 min-w-[80px] border-none outline-none bg-transparent text-[13px] text-[#1a1a1a] dark:text-white placeholder:text-[#999] dark:placeholder:text-[#808080]"
      />

      {/* 添加按钮 */}
      {inputValue.trim() && (
        <button
          type="button"
          className="add-tag-btn w-[24px] h-[24px] flex items-center justify-center rounded bg-[#4b6ef3]/10 text-[#4b6ef3] hover:bg-[#4b6ef3]/20 transition-colors"
          onClick={handleAddClick}
          aria-label="添加标签"
        >
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
      )}
    </div>
  );
}