import { useEffect } from 'react';

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({ isOpen, title, message, onConfirm, onCancel }: ConfirmDialogProps) {
  // ESC 关闭
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onCancel();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black/30 flex items-center justify-center z-[60]"
      onClick={(e) => {
        if (e.target === e.currentTarget) onCancel();
      }}
    >
      <div className="bg-white w-[320px] rounded-xl p-6 shadow-lg border border-[#f0f0f0]">
        <h2 className="text-lg font-semibold text-[#1a1a1a] mb-3">{title}</h2>
        <p className="text-sm text-[#666] mb-6">{message}</p>
        
        <div className="flex justify-end gap-3">
          <button
            className="px-6 py-2 rounded-lg text-sm border border-[#e5e7eb] bg-white text-[#333] hover:bg-[#f7f8fa] hover:border-[#d1d5db] transition-all"
            onClick={onCancel}
          >
            取消
          </button>
          <button
            className="px-6 py-2 rounded-lg text-sm bg-[#ff4d4f] text-white hover:bg-[#ff7875] transition-all"
            onClick={onConfirm}
          >
            确定
          </button>
        </div>
      </div>
    </div>
  );
}