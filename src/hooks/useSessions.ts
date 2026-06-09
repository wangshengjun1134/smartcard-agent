import { useState, useEffect, useCallback } from 'react';
import { Session, Message, Group } from '../types/session';
import { API_CONFIG } from '../config/api';
import { apiFetch } from '../utils/api';

// API response types
interface SessionResponse {
  id: string;
  title: string;
  created_at: number;
  updated_at: number;
  messages: MessageResponse[];
  group_id: string | null;
  is_pinned: boolean;
}

interface MessageResponse {
  id: string;
  role: string;
  content: string;
  thinking_process?: string;
  thinking_content?: string;
  created_at: number;
}

interface GroupResponse {
  id: string;
  name: string;
  icon: string;
  created_at: number;
  is_pinned: boolean;
}

// Convert API response to frontend type（纯函数，无副作用）
const toSession = (res: SessionResponse): Session => ({
  id: res.id,
  title: res.title,
  createdAt: res.created_at,
  updatedAt: res.updated_at,
  messages: res.messages.map(toMessage),
  groupId: res.group_id ?? undefined,
  isPinned: res.is_pinned,
});

const toMessage = (res: MessageResponse): Message => ({
  id: res.id,
  role: res.role as 'user' | 'assistant',
  content: res.content,
  thinkingProcess: res.thinking_process,
  thinkingContent: res.thinking_content,
  createdAt: res.created_at,
});

const toGroup = (res: GroupResponse): Group => ({
  id: res.id,
  name: res.name,
  icon: res.icon,
  createdAt: res.created_at,
  isPinned: res.is_pinned,
});

export function useSessions() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load data on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        const [sessionsData, groupsData] = await Promise.all([
          apiFetch<SessionResponse[]>(API_CONFIG.endpoints.session.list),
          apiFetch<GroupResponse[]>(API_CONFIG.endpoints.session.groups),
        ]);
        setSessions(sessionsData.map(toSession));
        setGroups(groupsData.map(toGroup));

        // Restore current session from localStorage (temporary)
        const savedId = localStorage.getItem('smartcard-agent-current-session');
        if (savedId && sessionsData.some(s => s.id === savedId)) {
          setCurrentSessionId(savedId);
        } else if (sessionsData.length > 0) {
          setCurrentSessionId(sessionsData[0].id);
        }
      } catch (error) {
        console.error('Failed to load sessions:', error);
      } finally {
        setIsLoading(false);
      }
    };
    loadData();
  }, []);

  // Persist current session ID
  useEffect(() => {
    if (!isLoading && currentSessionId) {
      localStorage.setItem('smartcard-agent-current-session', currentSessionId);
    }
  }, [currentSessionId, isLoading]);

  // Get current session
  const currentSession = sessions.find(s => s.id === currentSessionId) || null;

  // ========== Group Operations ==========

  const createGroup = useCallback(async (name: string, icon: string): Promise<Group> => {
    const data = await apiFetch<GroupResponse>(
      API_CONFIG.endpoints.session.createGroup,
      {
        method: 'POST',
        body: { name, icon },
        headers: { 'Content-Type': 'application/json' },
      }
    );
    const group = toGroup(data);
    setGroups(prev => [group, ...prev]);
    return group;
  }, []);

  const updateGroup = useCallback(async (id: string, name: string) => {
    await apiFetch<GroupResponse>(
      API_CONFIG.endpoints.session.updateGroup(id),
      {
        method: 'PUT',
        body: { name },
        headers: { 'Content-Type': 'application/json' },
      }
    );
    setGroups(prev =>
      prev.map(g => g.id === id ? { ...g, name } : g)
    );
  }, []);

  const deleteGroup = useCallback(async (id: string) => {
    await apiFetch<void>(
      API_CONFIG.endpoints.session.deleteGroup(id),
      { method: 'DELETE' }
    );
    setGroups(prev => prev.filter(g => g.id !== id));
    setSessions(prev => prev.filter(s => s.groupId !== id));
    if (currentSession?.groupId === id) {
      const remaining = sessions.filter(s => s.groupId !== id);
      setCurrentSessionId(remaining.length > 0 ? remaining[0].id : null);
    }
  }, [currentSession, sessions]);

  const pinGroup = useCallback(async (id: string) => {
    const group = groups.find(g => g.id === id);
    if (!group) return;
    const newPinned = !group.isPinned;
    await apiFetch<GroupResponse>(
      API_CONFIG.endpoints.session.updateGroup(id),
      {
        method: 'PUT',
        body: { is_pinned: newPinned },
        headers: { 'Content-Type': 'application/json' },
      }
    );
    setGroups(prev =>
      prev.map(g => g.id === id ? { ...g, isPinned: newPinned } : g)
    );
  }, [groups]);

  // ========== Session Operations ==========

  const createSession = useCallback(async (groupId?: string): Promise<Session> => {
    // 检查当前会话是否为空会话(没有消息),如果是则直接返回当前会话
    if (currentSession && currentSession.messages.length === 0) {
      return currentSession;
    }

    // 当前会话不为空,创建新会话
    const data = await apiFetch<SessionResponse>(
      API_CONFIG.endpoints.session.create,
      {
        method: 'POST',
        body: { title: '新会话', group_id: groupId },
        headers: { 'Content-Type': 'application/json' },
      }
    );
    const session = toSession(data);
    setSessions(prev => [session, ...prev]);
    setCurrentSessionId(session.id);
    return session;
  }, [currentSession]);

  const switchSession = useCallback((id: string) => {
    setCurrentSessionId(id);
  }, []);

  const deleteSession = useCallback(async (id: string) => {
    await apiFetch<void>(
      API_CONFIG.endpoints.session.delete(id),
      { method: 'DELETE' }
    );
    setSessions(prev => prev.filter(s => s.id !== id));
    if (currentSessionId === id) {
      const remaining = sessions.filter(s => s.id !== id);
      setCurrentSessionId(remaining.length > 0 ? remaining[0].id : null);
    }
  }, [currentSessionId, sessions]);

  const updateSessionTitle = useCallback(async (id: string, title: string) => {
    await apiFetch<SessionResponse>(
      API_CONFIG.endpoints.session.update(id),
      {
        method: 'PUT',
        body: { title },
        headers: { 'Content-Type': 'application/json' },
      }
    );
    setSessions(prev =>
      prev.map(s => s.id === id ? { ...s, title, updatedAt: Date.now() } : s)
    );
  }, []);

  const pinSession = useCallback(async (id: string) => {
    const session = sessions.find(s => s.id === id);
    if (!session) return;
    const newPinned = !session.isPinned;
    await apiFetch<SessionResponse>(
      API_CONFIG.endpoints.session.update(id),
      {
        method: 'PUT',
        body: { is_pinned: newPinned },
        headers: { 'Content-Type': 'application/json' },
      }
    );
    setSessions(prev =>
      prev.map(s => s.id === id ? { ...s, isPinned: newPinned, updatedAt: Date.now() } : s)
    );
  }, [sessions]);

  const moveSessionToGroup = useCallback(async (sessionId: string, groupId: string | undefined) => {
    await apiFetch<SessionResponse>(
      API_CONFIG.endpoints.session.update(sessionId),
      {
        method: 'PUT',
        body: { group_id: groupId },
        headers: { 'Content-Type': 'application/json' },
      }
    );
    setSessions(prev =>
      prev.map(s => s.id === sessionId ? { ...s, groupId, updatedAt: Date.now() } : s)
    );
  }, []);

  // ========== Message Operations ==========

  const addMessage = useCallback(async (sessionId: string, message: { role: string; content: string }): Promise<Message> => {
    const data = await apiFetch<MessageResponse>(
      API_CONFIG.endpoints.session.addMessage(sessionId),
      {
        method: 'POST',
        body: message,
        headers: { 'Content-Type': 'application/json' },
      }
    );
    const newMessage = toMessage(data);

    setSessions(prev =>
      prev.map(s => {
        if (s.id !== sessionId) return s;
        const updatedMessages = [...s.messages, newMessage];
        // Update title if first user message
        const newTitle = s.messages.length === 0 && message.role === 'user'
          ? message.content.slice(0, 30) + (message.content.length > 30 ? '...' : '')
          : s.title;
        return {
          ...s,
          messages: updatedMessages,
          updatedAt: Date.now(),
          title: newTitle,
        };
      })
    );

    return newMessage;
  }, []);

  // 流式更新消息内容（仅本地更新，不调用 API）
  const updateMessageContent = useCallback((sessionId: string, messageIndex: number, content: string, thinkingProcess?: string, thinkingContent?: string) => {
    setSessions(prev =>
      prev.map(s => {
        if (s.id !== sessionId) return s;
        const updatedMessages = [...s.messages];
        if (messageIndex >= 0 && messageIndex < updatedMessages.length) {
          updatedMessages[messageIndex] = {
            ...updatedMessages[messageIndex],
            content,
            ...(thinkingProcess !== undefined && { thinkingProcess }),
            ...(thinkingContent !== undefined && { thinkingContent }),
          };
        }
        return {
          ...s,
          messages: updatedMessages,
        };
      })
    );
  }, []);

  const getSessionsByGroup = useCallback((groupId: string | undefined) => {
    return sessions.filter(s => s.groupId === groupId);
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
    updateMessageContent,
    // Group operations
    createGroup,
    updateGroup,
    deleteGroup,
    pinGroup,
    // Session operations
    pinSession,
    moveSessionToGroup,
    getSessionsByGroup,
  };
}