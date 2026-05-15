import { useState, useEffect, useCallback } from 'react';
import { Session, Message, Group } from '../types/session';
import {
  loadSessions,
  saveSessions,
  loadCurrentSessionId,
  saveCurrentSessionId,
  loadGroups,
  saveGroups,
  generateId,
} from '../utils/storage';

// 排序函数：置顶优先 + 更新时间降序
function sortItems<T extends { isPinned?: boolean; updatedAt?: number; createdAt?: number }>(items: T[]): T[] {
  return [...items].sort((a, b) => {
    // 置顶优先
    if (a.isPinned && !b.isPinned) return -1;
    if (!a.isPinned && b.isPinned) return 1;
    // 更新时间降序
    const aTime = a.updatedAt || a.createdAt || 0;
    const bTime = b.updatedAt || b.createdAt || 0;
    return bTime - aTime;
  });
}

export function useSessions() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 初始化加载
  useEffect(() => {
    const savedSessions = loadSessions();
    const savedGroups = loadGroups();
    const savedCurrentId = loadCurrentSessionId();

    setSessions(sortItems(savedSessions));
    setGroups(sortItems(savedGroups));
    setCurrentSessionId(savedCurrentId);
    setIsLoading(false);
  }, []);

  // 持久化 sessions
  useEffect(() => {
    if (!isLoading) {
      saveSessions(sessions);
    }
  }, [sessions, isLoading]);

  // 持久化 groups
  useEffect(() => {
    if (!isLoading) {
      saveGroups(groups);
    }
  }, [groups, isLoading]);

  // 持久化 currentSessionId
  useEffect(() => {
    if (!isLoading) {
      saveCurrentSessionId(currentSessionId);
    }
  }, [currentSessionId, isLoading]);

  // 获取当前会话
  const currentSession = sessions.find(s => s.id === currentSessionId) || null;

  // ========== 分组操作 ==========

  // 创建新分组（默认置顶）
  const createGroup = useCallback((name: string, icon: string) => {
    const newGroup: Group = {
      id: generateId(),
      name,
      icon,
      createdAt: Date.now(),
      isPinned: true, // 新建分组默认置顶
    };

    setGroups(prev => sortItems([newGroup, ...prev]));
    return newGroup;
  }, []);

  // 更新分组（重命名）
  const updateGroup = useCallback((id: string, name: string) => {
    setGroups(prev =>
      prev.map(g =>
        g.id === id
          ? { ...g, name }
          : g
      )
    );
  }, []);

  // 删除分组
  const deleteGroup = useCallback((id: string) => {
    // 删除分组及其所有会话
    setGroups(prev => prev.filter(g => g.id !== id));
    setSessions(prev => prev.filter(s => s.groupId !== id));

    // 如果当前会话属于该分组，切换到最近的会话
    if (currentSession?.groupId === id) {
      const remainingSessions = sessions.filter(s => s.groupId !== id);
      setCurrentSessionId(remainingSessions.length > 0 ? remainingSessions[0].id : null);
    }
  }, [currentSession, sessions]);

  // 置顶分组
  const pinGroup = useCallback((id: string) => {
    setGroups(prev =>
      sortItems(prev.map(g =>
        g.id === id
          ? { ...g, isPinned: !g.isPinned }
          : g
      ))
    );
  }, []);

  // ========== 会话操作 ==========

  // 创建新会话
  const createSession = useCallback((groupId?: string) => {
    const newSession: Session = {
      id: generateId(),
      title: '新会话',
      createdAt: Date.now(),
      updatedAt: Date.now(),
      messages: [],
      groupId,
      isPinned: false,
    };

    setSessions(prev => sortItems([newSession, ...prev]));
    setCurrentSessionId(newSession.id);

    return newSession;
  }, []);

  // 切换会话
  const switchSession = useCallback((id: string) => {
    setCurrentSessionId(id);
  }, []);

  // 删除会话
  const deleteSession = useCallback((id: string) => {
    setSessions(prev => prev.filter(s => s.id !== id));

    // 如果删除的是当前会话，切换到最近的会话
    if (currentSessionId === id) {
      const remainingSessions = sessions.filter(s => s.id !== id);
      setCurrentSessionId(remainingSessions.length > 0 ? remainingSessions[0].id : null);
    }
  }, [currentSessionId, sessions]);

  // 更新会话标题
  const updateSessionTitle = useCallback((id: string, title: string) => {
    setSessions(prev =>
      sortItems(prev.map(s =>
        s.id === id
          ? { ...s, title, updatedAt: Date.now() }
          : s
      ))
    );
  }, []);

  // 置顶会话
  const pinSession = useCallback((id: string) => {
    setSessions(prev =>
      sortItems(prev.map(s =>
        s.id === id
          ? { ...s, isPinned: !s.isPinned, updatedAt: Date.now() }
          : s
      ))
    );
  }, []);

  // 移动会话到分组
  const moveSessionToGroup = useCallback((sessionId: string, groupId: string | undefined) => {
    setSessions(prev =>
      sortItems(prev.map(s =>
        s.id === sessionId
          ? { ...s, groupId, updatedAt: Date.now() }
          : s
      ))
    );
  }, []);

  // 添加消息
  const addMessage = useCallback((sessionId: string, message: Omit<Message, 'id' | 'createdAt'>) => {
    const newMessage: Message = {
      id: generateId(),
      role: message.role,
      content: message.content,
      createdAt: Date.now(),
    };

    setSessions(prev =>
      sortItems(prev.map(s =>
        s.id === sessionId
          ? {
              ...s,
              messages: [...s.messages, newMessage],
              updatedAt: Date.now(),
              title: s.messages.length === 0 && message.role === 'user'
                ? message.content.slice(0, 30) + (message.content.length > 30 ? '...' : '')
                : s.title,
            }
          : s
      ))
    );

    return newMessage;
  }, []);

  // 获取某个分组下的会话
  const getSessionsByGroup = useCallback((groupId: string | undefined) => {
    return sortItems(sessions.filter(s => s.groupId === groupId));
  }, [sessions]);

  return {
    sessions,
    groups,
    currentSession,
    currentSessionId,
    isLoading,
    createSession,
    switchSession,
    deleteSession,
    updateSessionTitle,
    addMessage,
    // 分组操作
    createGroup,
    updateGroup,
    deleteGroup,
    pinGroup,
    // 会话操作
    pinSession,
    moveSessionToGroup,
    getSessionsByGroup,
  };
}