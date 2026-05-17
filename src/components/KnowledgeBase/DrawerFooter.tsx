interface DrawerFooterProps {
  loading: boolean;
  disabled: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

/**
 * 抽屉底部操作按钮组件
 */
export function DrawerFooter({
  loading,
  disabled,
  onCancel,
  onConfirm,
}: DrawerFooterProps) {
  return (
    <div className="drawer-footer flex justify-end gap-3 px-5 py-4 border-t border-[#ececee] dark:border-[#333333] bg-white dark:bg-[#222222]">
      {/* 取消按钮 */}
      <button
        type="button"
        onClick={onCancel}
        disabled={loading}
        className="btn-cancel px-4 py-2 border border-[#ececee] dark:border-[#333333] rounded-lg text-[13px] text-[#4a4a4a] dark:text-[#b3b3b3] bg-transparent hover:bg-[#f7f8fa] dark:hover:bg-[#333333] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        取消
      </button>

      {/* 确认按钮 */}
      <button
        type="button"
        onClick={onConfirm}
        disabled={disabled || loading}
        className="btn-confirm px-4 py-2 border-none rounded-lg text-[13px] text-white bg-[#4b6ef3] hover:bg-[#3a5bd9] transition-colors disabled:bg-[#d1d5db] dark:disabled:bg-[#404040] disabled:cursor-not-allowed"
      >
        {loading ? (
          <span className="flex items-center gap-2">
            <svg
              className="animate-spin w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            上传中...
          </span>
        ) : (
          '确认上传'
        )}
      </button>
    </div>
  );
}