interface NewSessionButtonProps {
  onClick: () => void;
}

export function NewSessionButton({ onClick }: NewSessionButtonProps) {
  return (
    <button
      onClick={onClick}
      className="w-full flex items-center gap-2 px-4 py-3 rounded-lg
                 bg-[#7C3AED]/10 hover:bg-[#7C3AED]/20 text-[#A78BFA]
                 transition-colors duration-200 font-medium"
      aria-label="新建会话"
    >
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
      </svg>
      新建会话
    </button>
  );
}