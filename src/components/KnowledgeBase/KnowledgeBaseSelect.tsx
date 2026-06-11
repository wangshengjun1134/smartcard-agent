import { useState, useRef, useEffect } from 'react';
import { KnowledgeBase } from '../../types/knowledge';

interface KnowledgeBaseSelectProps {
  value: string;
  onChange: (value: string) => void;
  options: KnowledgeBase[];
  placeholder?: string;
}

/**
 * 知识库选择下拉组件
 */
export function KnowledgeBaseSelect({
  value,
  onChange,
  options,
  placeholder = '请选择知识库',
}: KnowledgeBaseSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedOption = options.find((opt) => opt.id === value);
  const selectedLabel = selectedOption?.name || placeholder;

  // 点击外部关闭
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (kbId: string) => {
    onChange(kbId);
    setIsOpen(false);
  };

  const handleToggle = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div ref={containerRef} className="kb-select relative">
      <div
        className="select-trigger flex items-center justify-between px-3 py-2 border border-[#ececee] dark:border-[#333333] rounded-lg cursor-pointer bg-white dark:bg-[#222222] transition-colors hover:border-[#4b6ef3]"
        onClick={handleToggle}
      >
        <span
          className={`text-[13px] truncate ${
            selectedOption
              ? 'text-[#1a1a1a] dark:text-white'
              : 'text-[#999] dark:text-[#808080]'
          }`}
        >
          {selectedLabel}
        </span>
        <svg
          className={`w-4 h-4 text-[#999] dark:text-[#808080] transition-transform flex-shrink-0 ml-2 ${
            isOpen ? 'rotate-180' : ''
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      {isOpen && (
        <div className="select-dropdown absolute top-full left-0 right-0 mt-1 bg-white dark:bg-[#222222] border border-[#ececee] dark:border-[#333333] rounded-lg z-10 shadow-lg max-h-[200px] overflow-y-auto">
          {options.map((kb) => (
            <div
              key={kb.id}
              className={`select-option px-3 py-2 cursor-pointer text-[13px] transition-colors ${
                kb.id === value
                  ? 'bg-[#4b6ef3]/10 text-[#4b6ef3]'
                  : 'text-[#1a1a1a] dark:text-white hover:bg-[#f7f8fa] dark:hover:bg-[#333333]'
              }`}
              onClick={() => handleSelect(kb.id)}
            >
              <div className="font-medium">{kb.name}</div>
              {kb.description && (
                <div className="text-[11px] text-[#999] dark:text-[#808080] mt-0.5 truncate">
                  {kb.description}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
