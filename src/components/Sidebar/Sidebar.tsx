import { Session } from '../../types/session';
import { SessionList } from './SessionList';

interface SidebarProps {
  sessions: Session[];
  currentSessionId: string | null;
  onNewSession: () => void;
  onSelectSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
}

export function Sidebar({
  sessions,
  currentSessionId,
  onNewSession,
  onSelectSession,
  onDeleteSession,
}: SidebarProps) {
  return (
    <div className="sidebar-container w-[260px] h-full flex flex-col p-4 flex-shrink-0">
      {/* 顶部：Logo 和图标 */}
      <div className="flex items-center justify-between mb-4">
        <div className="text-base font-semibold text-[#1a1a1a]">SmartCardAgent</div>
        <div className="flex items-center gap-3">
          <button className="circle-btn w-[18px] h-[18px]" aria-label="搜索">
            <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </button>
          <button className="circle-btn w-[18px] h-[18px]" aria-label="文件夹">
            <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
          </button>
        </div>
      </div>

      {/* 新建对话按钮 */}
      <button className="new-chat-btn mb-5" onClick={onNewSession}>
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        新建对话
        <svg className="w-4 h-4 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      </button>

      {/* 对话分组 */}
      <div className="mb-5">
        <div className="text-xs text-[#999] mb-2 pl-1">对话分组</div>
        <div className="menu-item">
          <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          新分组
        </div>
      </div>

      {/* 最近对话 */}
      <div className="flex-1 overflow-y-auto mt-2">
        <div className="text-xs text-[#999] mb-2 pl-1">最近对话</div>
        <SessionList
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSelect={onSelectSession}
          onDelete={onDeleteSession}
        />
      </div>

      {/* 底部用户信息 */}
      <div className="flex items-center gap-3 pt-4 border-t border-[#ececee] mt-auto">
        <div className="w-8 h-8 rounded-full avatar-gradient flex items-center justify-center text-white text-xs font-semibold">
          B
        </div>
        <div className="text-sm font-medium text-[#1a1a1a]">Buff</div>
      </div>
    </div>
  );
}