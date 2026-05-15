import { useEffect, useRef } from 'react';

interface ConversationActionMenuProps {
  isOpen: boolean;
  onClose: () => void;
  onRename: () => void;
  onPin: () => void;
  onMoveToGroup: () => void;
  onDelete: () => void;
  isPinned: boolean;
  position: { x: number; y: number };
}

export function ConversationActionMenu({
  isOpen,
  onClose,
  onRename,
  onPin,
  onMoveToGroup,
  onDelete,
  isPinned,
  position,
}: ConversationActionMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);

  // 点击外部关闭
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

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

  return (
    <div
      ref={menuRef}
      className="fixed w-[160px] bg-white rounded-xl shadow-[0_4px_16px_rgba(0,0,0,0.08),0_0_0_1px_rgba(0,0,0,0.02)] p-1.5 flex flex-col z-50"
      style={{
        left: position.x,
        top: position.y,
      }}
    >
      {/* 重命名 */}
      <div
        className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-[#1a1a1a] cursor-pointer hover:bg-[#f7f8fa] transition-colors"
        onClick={() => {
          onRename();
          onClose();
        }}
      >
        <svg className="w-4 h-4 text-[#555]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
        <span>重命名</span>
      </div>

      {/* 置顶 */}
      <div
        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-[#1a1a1a] cursor-pointer transition-colors ${
          isPinned ? 'bg-[#f7f8fa]' : 'hover:bg-[#f7f8fa]'
        }`}
        onClick={() => {
          onPin();
          onClose();
        }}
      >
        <svg className="w-4 h-4 text-[#555]" fill={isPinned ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
        </svg>
        <span>{isPinned ? '取消置顶' : '置顶此对话'}</span>
      </div>

      {/* 移动到分组 */}
      <div
        className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-[#1a1a1a] cursor-pointer hover:bg-[#f7f8fa] transition-colors"
        onClick={() => {
          onMoveToGroup();
          onClose();
        }}
      >
        <svg className="w-4 h-4 text-[#555]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
        </svg>
        <span>移动到分组</span>
      </div>

      {/* 删除 */}
      <div
        className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-[#ff4d4f] cursor-pointer hover:bg-[#f7f8fa] transition-colors"
        onClick={() => {
          onDelete();
          onClose();
        }}
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
        <span>删除此对话</span>
      </div>
    </div>
  );
}