import { useEffect } from 'react';
import { Group } from '../../types/session';

interface GroupSelectDialogProps {
  isOpen: boolean;
  onClose: () => void;
  groups: Group[];
  currentGroupId?: string;
  onSelect: (groupId: string | undefined) => void;
}

export function GroupSelectDialog({
  isOpen,
  onClose,
  groups,
  currentGroupId,
  onSelect,
}: GroupSelectDialogProps) {
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
      className="fixed inset-0 bg-black/30 flex items-center justify-center z-[60]"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="bg-white w-[320px] rounded-xl p-4 shadow-lg border border-[#f0f0f0]">
        <h2 className="text-base font-semibold text-[#1a1a1a] mb-4">选择分组</h2>
        
        <div className="flex flex-col gap-1">
          {/* 无分组选项 */}
          <div
            className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm cursor-pointer transition-colors ${
              !currentGroupId
                ? 'bg-[#f7f8fa] text-[#4b6ef3]'
                : 'text-[#1a1a1a] hover:bg-[#f7f8fa]'
            }`}
            onClick={() => {
              onSelect(undefined);
              onClose();
            }}
          >
            <span className="text-lg">📁</span>
            <span>无分组</span>
          </div>

          {/* 分组列表 */}
          {groups.map((group) => (
            <div
              key={group.id}
              className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm cursor-pointer transition-colors ${
                currentGroupId === group.id
                  ? 'bg-[#f7f8fa] text-[#4b6ef3]'
                  : 'text-[#1a1a1a] hover:bg-[#f7f8fa]'
              }`}
              onClick={() => {
                if (currentGroupId !== group.id) {
                  onSelect(group.id);
                  onClose();
                }
              }}
            >
              <i className={`${group.icon} text-lg text-[#333]`}></i>
              <span>{group.name}</span>
              {group.isPinned && (
                <svg className="w-3.5 h-3.5 text-[#4b6ef3] ml-auto" fill="currentColor" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
              )}
            </div>
          ))}
        </div>

        <button
          className="w-full mt-3 px-3 py-2.5 rounded-lg text-sm text-[#666] hover:bg-[#f7f8fa] transition-colors"
          onClick={onClose}
        >
          取消
        </button>
      </div>
    </div>
  );
}