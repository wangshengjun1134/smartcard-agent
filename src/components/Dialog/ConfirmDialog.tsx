import { useDialogClose } from '../../hooks/useDialog';

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({ isOpen, title, message, onConfirm, onCancel }: ConfirmDialogProps) {
  // 使用统一的对话框关闭Hook（ESC取消）
  const dialogRef = useDialogClose<HTMLDivElement>(isOpen, onCancel);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/30 flex items-center justify-center z-[60]"
      onClick={(e) => {
        if (e.target === e.currentTarget) onCancel();
      }}
    >
      <div 
        ref={dialogRef}
        className="bg-white dark:bg-[#222222] w-[320px] rounded-xl p-6 shadow-lg border border-[#f0f0f0] dark:border-[#333333]"
      >
        <h2 className="text-lg font-semibold text-[#1a1a1a] dark:text-white mb-3">{title}</h2>
        <p className="text-sm text-[#666] dark:text-[#b3b3b3] mb-6">{message}</p>

        <div className="flex justify-end gap-3">
          <button
            className="px-6 py-2 rounded-lg text-sm border border-[#e5e7eb] dark:border-[#404040] bg-white dark:bg-[#333333] text-[#333] dark:text-white hover:bg-[#f7f8fa] dark:hover:bg-[#404040] hover:border-[#d1d5db] transition-all"
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