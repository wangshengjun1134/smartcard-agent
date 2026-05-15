import React, { useRef, useEffect, useState } from 'react';
import { Session, Group } from '../../types/session';

interface SessionListProps {
  sessions: Session[];
  currentSessionId: string | null;
  onSelect: (id: string) => void;
  onUpdateTitle: (id: string, title: string) => void;
  groups: Group[];
  onMenuOpen: (e: React.MouseEvent, session: Session) => void;
  editingSessionId: string | null;
}

export function SessionList({
  sessions,
  currentSessionId,
  onSelect,
  onUpdateTitle,
  groups,
  onMenuOpen,
  editingSessionId,
}: SessionListProps) {
  const editInputRef = useRef<HTMLInputElement>(null);
  const [editingValue, setEditingValue] = useState('');

  // 当开始编辑时，设置初始值并聚焦
  useEffect(() => {
    if (editingSessionId) {
      const session = sessions.find(s => s.id === editingSessionId);
      if (session) {
        setEditingValue(session.title);
        setTimeout(() => {
          if (editInputRef.current) {
            editInputRef.current.focus();
            editInputRef.current.select();
          }
        }, 0);
      }
    }
  }, [editingSessionId, sessions]);

  if (sessions.length === 0) {
    return (
      <div className="text-xs text-[#999] py-4 text-center">
        暂无对话记录
      </div>
    );
  }

  const handleFinishEdit = (session: Session) => {
    if (editingValue.trim()) {
      onUpdateTitle(session.id, editingValue.trim());
    }
    setEditingValue('');
  };

  return (
    <div className="space-y-0">
      {sessions.map((session) => {
        const isEditing = editingSessionId === session.id;
        const group = session.groupId ? groups.find(g => g.id === session.groupId) : null;

        return (
          <div
            key={session.id}
            onClick={() => !editingSessionId && !isEditing && onSelect(session.id)}
            className={`session-item group relative ${session.id === currentSessionId ? 'active' : ''} ${session.isPinned ? 'bg-[#f7f8fa]' : ''}`}
          >
            <div className="flex items-center gap-2 flex-1 min-w-0">
              {/* 置顶标记 */}
              {session.isPinned && (
                <svg className="w-3 h-3 text-[#4b6ef3]" fill="currentColor" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
              )}

              {/* 分组图标 */}
              {group && (
                <span className="text-sm">{group.icon}</span>
              )}

              {/* 标题 */}
              {isEditing ? (
                <input
                  ref={editInputRef}
                  type="text"
                  value={editingValue}
                  onChange={(e) => setEditingValue(e.target.value)}
                  onBlur={() => handleFinishEdit(session)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleFinishEdit(session);
                    if (e.key === 'Escape') setEditingValue('');
                  }}
                  className="flex-1 text-sm bg-transparent border-none outline-none text-[#1a1a1a]"
                />
              ) : (
                <span className="truncate text-sm">{session.title}</span>
              )}
            </div>

            {/* 三个点菜单按钮 */}
            <button
              onClick={(e) => onMenuOpen(e, session)}
              className="opacity-0 group-hover:opacity-100 hover:bg-[#e5e7eb] rounded p-1 transition-opacity ml-2"
              aria-label="更多操作"
            >
              <svg className="w-4 h-4 text-[#555]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
              </svg>
            </button>
          </div>
        );
      })}
    </div>
  );
}