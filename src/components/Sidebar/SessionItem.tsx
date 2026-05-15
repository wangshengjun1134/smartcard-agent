import { Session } from '../../types/session';
import { formatRelativeTime } from '../../utils/storage';

interface SessionItemProps {
  session: Session;
  isActive: boolean;
  onClick: () => void;
  onDelete: () => void;
}

export function SessionItem({ session, isActive, onClick, onDelete }: SessionItemProps) {
  return (
    <div
      onClick={onClick}
      className={`
        session-item group relative
        ${isActive ? 'active bg-[#7C3AED]/20' : ''}
      `}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
    >
      {/* 会话标题 */}
      <h3 className="text-sm font-medium truncate text-[#F8FAFC]">
        {session.title}
      </h3>

      {/* 时间和消息数 */}
      <div className="flex items-center gap-2 mt-1 text-xs text-[#64748B]">
        <span>{formatRelativeTime(session.updatedAt)}</span>
        <span>{session.messages.length} 条消息</span>
      </div>

      {/* 删除按钮 */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          if (confirm('确定删除此会话吗？')) {
            onDelete();
          }
        }}
        className="absolute right-2 top-1/2 -translate-y-1/2
                   p-1 rounded opacity-0 group-hover:opacity-100
                   hover:bg-[#EF4444]/20 text-[#64748B] hover:text-[#EF4444]
                   transition-opacity duration-200"
        aria-label={`删除会话 ${session.title}`}
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      </button>
    </div>
  );
}