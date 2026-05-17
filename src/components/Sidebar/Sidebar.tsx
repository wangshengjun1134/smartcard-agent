import React, { useState, useRef } from 'react';
import { Session, Group } from '../../types/session';
import { SessionList } from './SessionList';
import { CreateGroupDialog } from '../Dialog/CreateGroupDialog';
import { GroupActionMenu } from '../Dialog/GroupActionMenu';
import { ConversationActionMenu } from '../Dialog/ConversationActionMenu';
import { ConfirmDialog } from '../Dialog/ConfirmDialog';
import { GroupSelectDialog } from '../Dialog/GroupSelectDialog';
import { UserMenu } from '../Dialog/UserMenu';
import { SettingsDialog } from '../Dialog/SettingsDialog';

export type ViewType = 'chat' | 'knowledge' | 'skills';

interface SidebarProps {
  sessions: Session[];
  groups: Group[];
  currentSessionId: string | null;
  currentView: ViewType;
  onNewSession: (groupId?: string) => void;
  onSelectSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
  onUpdateSessionTitle: (id: string, title: string) => void;
  onPinSession: (id: string) => void;
  onMoveSessionToGroup: (sessionId: string, groupId: string | undefined) => void;
  onCreateGroup: (name: string, icon: string) => void;
  onUpdateGroup: (id: string, name: string) => void;
  onDeleteGroup: (id: string) => void;
  onPinGroup: (id: string) => void;
  onViewChange: (view: ViewType) => void;
}

export function Sidebar({
  sessions,
  groups,
  currentSessionId,
  currentView,
  onNewSession,
  onSelectSession,
  onDeleteSession,
  onUpdateSessionTitle,
  onPinSession,
  onMoveSessionToGroup,
  onCreateGroup,
  onUpdateGroup,
  onDeleteGroup,
  onPinGroup,
  onViewChange,
}: SidebarProps) {
  // 分页状态
  const [displayLimit, setDisplayLimit] = useState(5);
  const isExpanded = displayLimit > 5;

  // 对话框状态
  const [showCreateGroup, setShowCreateGroup] = useState(false);

  // 菜单状态
  const [groupMenuState, setGroupMenuState] = useState<{
    isOpen: boolean;
    groupId: string | null;
    position: { x: number; y: number };
    isPinned: boolean;
    hasConversations: boolean;
    editingName: boolean;
  }>({
    isOpen: false,
    groupId: null,
    position: { x: 0, y: 0 },
    isPinned: false,
    hasConversations: false,
    editingName: false,
  });

  const [conversationMenuState, setConversationMenuState] = useState<{
    isOpen: boolean;
    sessionId: string | null;
    position: { x: number; y: number };
    isPinned: boolean;
    groupId?: string;
    editingName: boolean;
  }>({
    isOpen: false,
    sessionId: null,
    position: { x: 0, y: 0 },
    isPinned: false,
    groupId: undefined,
    editingName: false,
  });

  // 确认对话框状态
  const [confirmState, setConfirmState] = useState<{
    isOpen: boolean;
    type: 'group' | 'conversation' | null;
    id: string | null;
    title: string;
    message: string;
  }>({
    isOpen: false,
    type: null,
    id: null,
    title: '',
    message: '',
  });

  // 分组选择状态
  const [groupSelectState, setGroupSelectState] = useState<{
    isOpen: boolean;
    sessionId: string | null;
    currentGroupId?: string;
  }>({
    isOpen: false,
    sessionId: null,
    currentGroupId: undefined,
  });

  // 用户菜单状态
  const [userMenuState, setUserMenuState] = useState<{
    isOpen: boolean;
    bottom: number;
  }>({
    isOpen: false,
    bottom: 0,
  });

  // 设置对话框状态
  const [showSettings, setShowSettings] = useState(false);

  // inline 编辑状态
  const [editingValue, setEditingValue] = useState('');
  const editInputRef = useRef<HTMLInputElement>(null);
  const sidebarRef = useRef<HTMLDivElement>(null);

  // 处理分组菜单
  const handleGroupMenuOpen = (e: React.MouseEvent, group: Group, groupSessions: Session[]) => {
    e.stopPropagation();
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    setGroupMenuState({
      isOpen: true,
      groupId: group.id,
      position: { x: rect.left, y: rect.bottom + 4 },
      isPinned: group.isPinned || false,
      hasConversations: groupSessions.length > 0,
      editingName: false,
    });
  };

  // 处理对话菜单
  const handleConversationMenuOpen = (e: React.MouseEvent, session: Session) => {
    e.stopPropagation();
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    setConversationMenuState({
      isOpen: true,
      sessionId: session.id,
      position: { x: rect.left, y: rect.bottom + 4 },
      isPinned: session.isPinned || false,
      groupId: session.groupId,
      editingName: false,
    });
  };

  // 开始重命名分组
  const handleStartRenameGroup = () => {
    const group = groups.find(g => g.id === groupMenuState.groupId);
    if (group) {
      setEditingValue(group.name);
      setGroupMenuState(prev => ({ ...prev, editingName: true }));
      setTimeout(() => {
        if (editInputRef.current) {
          editInputRef.current.focus();
          editInputRef.current.select();
        }
      }, 0);
    }
  };

  // 完成重命名分组
  const handleFinishRenameGroup = () => {
    if (groupMenuState.groupId && editingValue.trim()) {
      onUpdateGroup(groupMenuState.groupId, editingValue.trim());
    }
    setGroupMenuState(prev => ({ ...prev, editingName: false }));
    setEditingValue('');
  };

  // 开始重命名对话
  const handleStartRenameConversation = () => {
    const session = sessions.find(s => s.id === conversationMenuState.sessionId);
    if (session) {
      setEditingValue(session.title);
      setConversationMenuState(prev => ({ ...prev, editingName: true }));
      setTimeout(() => {
        if (editInputRef.current) {
          editInputRef.current.focus();
          editInputRef.current.select();
        }
      }, 0);
    }
  };

  // 处理删除分组
  const handleDeleteGroup = () => {
    if (groupMenuState.groupId) {
      if (groupMenuState.hasConversations) {
        const group = groups.find(g => g.id === groupMenuState.groupId);
        setConfirmState({
          isOpen: true,
          type: 'group',
          id: groupMenuState.groupId,
          title: '删除分组',
          message: `确定要删除分组「${group?.name}」吗？该分组下的所有对话将一并删除。`,
        });
      } else {
        onDeleteGroup(groupMenuState.groupId);
      }
    }
  };

  // 处理删除对话
  const handleDeleteConversation = () => {
    if (conversationMenuState.sessionId) {
      const session = sessions.find(s => s.id === conversationMenuState.sessionId);
      setConfirmState({
        isOpen: true,
        type: 'conversation',
        id: conversationMenuState.sessionId,
        title: '删除对话',
        message: `确定要删除对话「${session?.title}」吗？`,
      });
    }
  };

  // 确认删除
  const handleConfirmDelete = () => {
    if (confirmState.type === 'group' && confirmState.id) {
      onDeleteGroup(confirmState.id);
    } else if (confirmState.type === 'conversation' && confirmState.id) {
      onDeleteSession(confirmState.id);
    }
    setConfirmState({ isOpen: false, type: null, id: null, title: '', message: '' });
  };

  // 处理移动到分组
  const handleMoveToGroup = () => {
    if (conversationMenuState.sessionId) {
      setGroupSelectState({
        isOpen: true,
        sessionId: conversationMenuState.sessionId,
        currentGroupId: conversationMenuState.groupId,
      });
    }
  };

  // 选择分组后移动
  const handleSelectGroup = (groupId: string | undefined) => {
    if (groupSelectState.sessionId) {
      onMoveSessionToGroup(groupSelectState.sessionId, groupId);
    }
    setGroupSelectState({ isOpen: false, sessionId: null, currentGroupId: undefined });
  };

  // 展开/收回分组
  const handleToggleExpand = () => {
    if (isExpanded) {
      setDisplayLimit(5);
    } else {
      setDisplayLimit(groups.length);
    }
  };

  // 显示的分组列表
  const displayedGroups = groups.slice(0, displayLimit);
  const canExpand = groups.length > 5;

  return (
    <div ref={sidebarRef} className="sidebar-container w-[260px] h-full flex flex-col p-4 flex-shrink-0 relative">
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
      <div className="mb-4">
        <button className="new-chat-btn w-full" onClick={() => {
          onNewSession();
          onViewChange('chat');
        }}>
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          新建对话
          <svg className="w-4 h-4 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </button>
      </div>

      {/* 知识库、技能库 */}
      <div className="mb-4 flex flex-col gap-1">
        <button
          className={`menu-item cursor-pointer w-full text-left ${currentView === 'knowledge' ? 'bg-[#f7f8fa] text-[#4b6ef3]' : ''}`}
          onClick={() => onViewChange('knowledge')}
        >
          <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          知识库
        </button>
        <button
          className={`menu-item cursor-pointer w-full text-left ${currentView === 'skills' ? 'bg-[#f7f8fa] text-[#4b6ef3]' : ''}`}
          onClick={() => onViewChange('skills')}
        >
          <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          技能库
        </button>
      </div>

      {/* 对话分组 + 最近对话 滚动区域 */}
      <div className="flex-1 overflow-y-auto">
        {/* 对话分组 */}
        <div className="mb-3">
          <div className="text-xs text-[#999] mb-2 pl-1">对话分组</div>

        {/* 新分组按钮 */}
        <div className="menu-item cursor-pointer" onClick={() => setShowCreateGroup(true)}>
          <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          新分组
        </div>

        {/* 分组列表 */}
        {displayedGroups.map((group) => {
          const groupSessions = sessions.filter(s => s.groupId === group.id);
          const isEditing = groupMenuState.editingName && groupMenuState.groupId === group.id;

          return (
            <div
              key={group.id}
              className={`menu-item group relative ${group.isPinned ? 'bg-[#f7f8fa] hover:bg-[#ececee]' : ''}`}
            >
              <i className={`${group.icon} text-lg text-[#333]`}></i>

              {isEditing ? (
                <input
                  ref={editInputRef}
                  type="text"
                  value={editingValue}
                  onChange={(e) => setEditingValue(e.target.value)}
                  onBlur={handleFinishRenameGroup}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleFinishRenameGroup();
                    if (e.key === 'Escape') {
                      setGroupMenuState(prev => ({ ...prev, editingName: false }));
                      setEditingValue('');
                    }
                  }}
                  className="flex-1 text-sm bg-transparent border-none outline-none text-[#1a1a1a]"
                />
              ) : (
                <span className="flex-1 text-sm">{group.name}</span>
              )}

              {/* 置顶标记 */}
              {group.isPinned && (
                <svg className="w-3 h-3 text-[#4b6ef3] mr-1" fill="currentColor" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
              )}

              {/* 对话数量 */}
              <span className="text-xs text-[#999] mr-2">{groupSessions.length}</span>

              {/* 三个点按钮 */}
              <button
                className="opacity-0 group-hover:opacity-100 hover:bg-[#e5e7eb] rounded p-1 transition-opacity"
                onClick={(e) => handleGroupMenuOpen(e, group, groupSessions)}
              >
                <svg className="w-4 h-4 text-[#555]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                </svg>
              </button>
            </div>
          );
        })}

        {/* 更多/收回按钮 */}
        {canExpand && (
          <button
            className="menu-item cursor-pointer"
            onClick={handleToggleExpand}
          >
            {isExpanded ? (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
                收回
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
                更多 ({groups.length - 5})
              </>
            )}
          </button>
        )}
      </div>

      {/* 最近对话 */}
        <div>
          <div className="text-xs text-[#999] mb-2 pl-1">最近对话</div>
          <SessionList
            sessions={sessions}
            currentSessionId={currentSessionId}
            onSelect={(id) => {
              onSelectSession(id);
              onViewChange('chat');
            }}
            onUpdateTitle={onUpdateSessionTitle}
            groups={groups}
            onMenuOpen={handleConversationMenuOpen}
            editingSessionId={conversationMenuState.editingName ? conversationMenuState.sessionId : null}
          />
        </div>
      </div>

      {/* 底部用户信息 */}
      <div
        className="flex items-center gap-3 pt-4 border-t border-[#ececee] mt-auto cursor-pointer hover:bg-[#f7f8fa] rounded-lg px-2 py-3 -mx-2 transition-colors"
        onClick={(e) => {
          if (sidebarRef.current) {
            const sidebarRect = sidebarRef.current.getBoundingClientRect();
            const buffRect = (e.currentTarget as HTMLElement).getBoundingClientRect();
            const bottom = sidebarRect.bottom - buffRect.top;
            setUserMenuState({
              isOpen: true,
              bottom,
            });
          }
        }}
      >
        <div className="w-8 h-8 rounded-full avatar-gradient flex items-center justify-center text-white text-xs font-semibold">
          B
        </div>
        <div className="text-sm font-medium text-[#1a1a1a]">Buff</div>
      </div>

      {/* 对话框 */}
      <CreateGroupDialog
        isOpen={showCreateGroup}
        onClose={() => setShowCreateGroup(false)}
        onConfirm={onCreateGroup}
      />

      <GroupActionMenu
        isOpen={groupMenuState.isOpen}
        onClose={() => setGroupMenuState(prev => ({ ...prev, isOpen: false }))}
        onRename={handleStartRenameGroup}
        onPin={() => {
          if (groupMenuState.groupId) {
            onPinGroup(groupMenuState.groupId);
          }
        }}
        onDelete={handleDeleteGroup}
        isPinned={groupMenuState.isPinned}
        position={groupMenuState.position}
      />

      <ConversationActionMenu
        isOpen={conversationMenuState.isOpen}
        onClose={() => setConversationMenuState(prev => ({ ...prev, isOpen: false }))}
        onRename={handleStartRenameConversation}
        onPin={() => {
          if (conversationMenuState.sessionId) {
            onPinSession(conversationMenuState.sessionId);
          }
        }}
        onMoveToGroup={handleMoveToGroup}
        onDelete={handleDeleteConversation}
        isPinned={conversationMenuState.isPinned}
        position={conversationMenuState.position}
      />

      <ConfirmDialog
        isOpen={confirmState.isOpen}
        title={confirmState.title}
        message={confirmState.message}
        onConfirm={handleConfirmDelete}
        onCancel={() => setConfirmState({ isOpen: false, type: null, id: null, title: '', message: '' })}
      />

      <GroupSelectDialog
        isOpen={groupSelectState.isOpen}
        onClose={() => setGroupSelectState({ isOpen: false, sessionId: null, currentGroupId: undefined })}
        groups={groups}
        currentGroupId={groupSelectState.currentGroupId}
        onSelect={handleSelectGroup}
      />

      <UserMenu
        isOpen={userMenuState.isOpen}
        onClose={() => setUserMenuState({ isOpen: false, bottom: 0 })}
        bottom={userMenuState.bottom}
        onOpenSettings={() => setShowSettings(true)}
      />

      <SettingsDialog
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
      />
    </div>
  );
}