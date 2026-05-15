import { useState, useEffect, useRef } from 'react';

interface CreateGroupDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (name: string, icon: string) => void;
}

// 预设图标选项
const presetIcons = [
  { icon: '🧳', label: '旅行' },
  { icon: '💎', label: '投资' },
  { icon: '📋', label: '作业' },
  { icon: '❤️', label: '健康' },
  { icon: '💻', label: '代码' },
];

export function CreateGroupDialog({ isOpen, onClose, onConfirm }: CreateGroupDialogProps) {
  const [name, setName] = useState('');
  const [selectedIcon, setSelectedIcon] = useState('🧳');
  const inputRef = useRef<HTMLInputElement>(null);

  // 打开时自动聚焦输入框
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // ESC 关闭
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleConfirm = () => {
    if (name.trim()) {
      console.log('CreateGroupDialog: onConfirm called with', name.trim(), selectedIcon);
      onConfirm(name.trim(), selectedIcon);
      setName('');
      setSelectedIcon('🧳');
      onClose();
    }
  };

  const handleCancel = () => {
    setName('');
    setSelectedIcon('🧳');
    onClose();
  };

  return (
    <div 
      className="fixed inset-0 bg-black/30 flex items-center justify-center z-50"
      onClick={(e) => {
        if (e.target === e.currentTarget) handleCancel();
      }}
    >
      <div className="bg-white w-[420px] rounded-xl p-6 shadow-lg border border-[#f0f0f0]">
        {/* 头部 */}
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-[#1a1a1a]">创建分组</h2>
          <span 
            className="text-xl text-[#888] cursor-pointer hover:text-[#333] transition-colors"
            onClick={handleCancel}
          >
            ×
          </span>
        </div>

        {/* 描述 */}
        <p className="text-sm text-[#666] leading-relaxed mb-5">
          分组功能可将对话集中归类管理，并支持自定义指示，让对话更加自然有序。
        </p>

        {/* 输入框 */}
        <div className="flex items-center border border-[#1a1a1a] rounded-lg px-3 py-2 mb-5 transition-all focus-within:border-[#4b6ef3] focus-within:shadow-[0_0_0_2px_rgba(75,110,243,0.1)]">
          <span className="text-lg mr-2">{selectedIcon}</span>
          <input
            ref={inputRef}
            type="text"
            placeholder="请输入分组名称"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="flex-1 outline-none text-base text-[#1a1a1a] placeholder:text-[#aaa]"
          />
        </div>

        {/* 图标标签 */}
        <div className="flex flex-wrap gap-2.5 mb-8">
          {presetIcons.map((item) => (
            <div
              key={item.icon}
              className={`flex items-center gap-1.5 bg-white border rounded-md px-3 py-1.5 text-sm cursor-pointer transition-all ${
                selectedIcon === item.icon
                  ? 'border-[#4b6ef3] bg-[#f7f8fa]'
                  : 'border-[#e5e7eb] hover:bg-[#f7f8fa] hover:border-[#d1d5db]'
              }`}
              onClick={() => setSelectedIcon(item.icon)}
            >
              <span>{item.icon}</span>
              <span className="text-[#333]">{item.label}</span>
            </div>
          ))}
        </div>

        {/* 底部按钮 */}
        <div className="flex justify-end gap-3">
          <button
            className="px-6 py-2 rounded-lg text-sm border border-[#e5e7eb] bg-white text-[#333] hover:bg-[#f7f8fa] hover:border-[#d1d5db] transition-all"
            onClick={handleCancel}
          >
            取消
          </button>
          <button
            className={`px-6 py-2 rounded-lg text-sm border border-transparent transition-all ${
              name.trim()
                ? 'bg-[#4b6ef3] text-white hover:bg-[#3b5fdb] cursor-pointer'
                : 'bg-[#d1d5db] text-[#9ca3af] cursor-not-allowed'
            }`}
            onClick={handleConfirm}
            disabled={!name.trim()}
          >
            确定
          </button>
        </div>
      </div>
    </div>
  );
}