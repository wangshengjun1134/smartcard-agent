import { useState, useEffect, useRef } from 'react';

interface CreateGroupDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (name: string, icon: string) => void;
}

// Font Awesome 图标选项
const presetIcons = [
  'fa-regular fa-face-smile',
  'fa-regular fa-star',
  'fa-solid fa-bolt',
  'fa-solid fa-helmet-safety',
  'fa-regular fa-heart',
  'fa-regular fa-clock',
  'fa-regular fa-user',
  'fa-regular fa-image',
  'fa-regular fa-circle-dot',
  'fa-regular fa-folder',
  'fa-solid fa-sd-card',
  'fa-regular fa-mobile-screen',
  'fa-regular fa-location-dot',
  'fa-regular fa-fire',
  'fa-regular fa-lightbulb',
  'fa-regular fa-bookmark',
  'fa-regular fa-file-lines',
  'fa-regular fa-heart-pulse',
  'fa-regular fa-comments',
  'fa-solid fa-share-nodes',
  'fa-solid fa-users',
  'fa-regular fa-headphones',
  'fa-regular fa-hand-pointer',
  'fa-regular fa-cake-candles',
  'fa-regular fa-shirt',
  'fa-regular fa-magnifying-glass',
  'fa-regular fa-cube',
  'fa-regular fa-address-card',
  'fa-regular fa-house',
];

export function CreateGroupDialog({ isOpen, onClose, onConfirm }: CreateGroupDialogProps) {
  const [name, setName] = useState('');
  const [selectedIcon, setSelectedIcon] = useState('fa-regular fa-face-smile');
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
      onConfirm(name.trim(), selectedIcon);
      setName('');
      setSelectedIcon('fa-regular fa-face-smile');
      onClose();
    }
  };

  const handleCancel = () => {
    setName('');
    setSelectedIcon('fa-regular fa-face-smile');
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
          分组功能可将对话集中归类管理，并支持自定义图标，让对话更加自然有序。
        </p>

        {/* 输入框 */}
        <div className="flex items-center border border-[#1a1a1a] rounded-lg px-3 py-2 mb-5 transition-all focus-within:border-[#4b6ef3] focus-within:shadow-[0_0_0_2px_rgba(75,110,243,0.1)]">
          <i className={`${selectedIcon} text-lg mr-2 text-[#333]`}></i>
          <input
            ref={inputRef}
            type="text"
            placeholder="请输入分组名称"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="flex-1 outline-none text-base text-[#1a1a1a] placeholder:text-[#aaa]"
          />
        </div>

        {/* 图标网格 */}
        <div className="mb-6">
          <div className="text-xs text-[#999] mb-2">选择图标</div>
          <div className="grid grid-cols-8 gap-1 bg-[#f9f9fb] rounded-lg p-3 border border-[#eaeaea]">
            {presetIcons.map((iconClass) => (
              <div
                key={iconClass}
                className={`flex items-center justify-center w-[40px] h-[40px] cursor-pointer rounded-md transition-all ${
                  selectedIcon === iconClass
                    ? 'bg-[#eef0f5] border border-[#4b6ef3]'
                    : 'hover:bg-[#eef0f5]'
                }`}
                onClick={() => setSelectedIcon(iconClass)}
              >
                <i className={`${iconClass} text-xl text-[#333]`}></i>
              </div>
            ))}
          </div>
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