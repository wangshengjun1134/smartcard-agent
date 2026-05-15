import { Session } from '../../types/session';

interface SessionListProps {
  sessions: Session[];
  currentSessionId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

export function SessionList({ sessions, currentSessionId, onSelect, onDelete }: SessionListProps) {
  if (sessions.length === 0) {
    return (
      <div className="text-xs text-[#999] py-4 text-center">
        暂无对话记录
      </div>
    );
  }

  return (
    <div className="space-y-0">
      {sessions.map((session) => (
        <div
          key={session.id}
          onClick={() => onSelect(session.id)}
          className={`session-item group relative ${session.id === currentSessionId ? 'active' : ''}`}
        >
          {session.title}
          {/* 删除按钮 */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              if (confirm('确定删除此对话吗？')) {
                onDelete(session.id);
              }
            }}
            className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-[#e5e7eb] text-[#666] hover:text-[#EF4444] transition-opacity"
            aria-label="删除"
          >
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      ))}
    </div>
  );
}