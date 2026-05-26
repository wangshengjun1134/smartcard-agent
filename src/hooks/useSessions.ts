import { useState, useEffect, useCallback } from 'react';
import { Session, Message, Group } from '../types/session';
import { getApiUrl, API_CONFIG, DEFAULT_HEADERS } from '../config/api';

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
  created_at: number;
}

interface GroupResponse {
  id: string;
  name: string;
  icon: string;
  created_at: number;
  is_pinned: boolean;
}

// Convert API response to frontend type
function toSession(res: SessionResponse): Session {
  return {
    id: res.id,
    title: res.title,
    createdAt: res.created_at,
    updatedAt: res.updated_at,
    messages: res.messages.map(toMessage),
    groupId: res.group_id,
    isPinned: res.is_pinned,
  };
}

function toMessage(res: MessageResponse): Message {
  return {
    id: res.id,
    role: res.role,
    content: res.content,
    createdAt: res.created_at,
  };
}

function toGroup(res: GroupResponse): Group {
  return {
    id: res.id,
    name: res.name,
    icon: res.icon,
    createdAt: res.created_at,
    isPinned: res.is_pinned,
  };
}

// API helper functions
async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...DEFAULT_HEADERS,
      ...options?.headers,
    },
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json();
}

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
          fetchJson<SessionResponse[]>(getApiUrl(API_CONFIG.endpoints.session.list)),
          fetchJson<GroupResponse[]>(getApiUrl(API_CONFIG.endpoints.session.groups)),
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
    const data = await fetchJson<GroupResponse>(getApiUrl(API_CONFIG.endpoints.session.createGroup), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, icon }),
    });
    const group = toGroup(data);
    setGroups(prev => [group, ...prev]);
    return group;
  }, []);

  const updateGroup = useCallback(async (id: string, name: string) => {
    await fetchJson<GroupResponse>(getApiUrl(API_CONFIG.endpoints.session.updateGroup(id)), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    setGroups(prev =>
      prev.map(g => g.id === id ? { ...g, name } : g)
    );
  }, []);

  const deleteGroup = useCallback(async (id: string) => {
    await fetchJson(getApiUrl(API_CONFIG.endpoints.session.deleteGroup(id)), {
      method: 'DELETE',
    });
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
    await fetchJson<GroupResponse>(getApiUrl(API_CONFIG.endpoints.session.updateGroup(id)), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_pinned: newPinned }),
    });
    setGroups(prev =>
      prev.map(g => g.id === id ? { ...g, isPinned: newPinned } : g)
    );
  }, [groups]);

  // ========== Session Operations ==========

  const createSession = useCallback(async (groupId?: string): Promise<Session> => {
    const data = await fetchJson<SessionResponse>(getApiUrl(API_CONFIG.endpoints.session.create), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: '新会话', group_id: groupId }),
    });
    const session = toSession(data);
    setSessions(prev => [session, ...prev]);
    setCurrentSessionId(session.id);
    return session;
  }, []);

  const switchSession = useCallback((id: string) => {
    setCurrentSessionId(id);
  }, []);

  const deleteSession = useCallback(async (id: string) => {
    await fetchJson(getApiUrl(API_CONFIG.endpoints.session.delete(id)), {
      method: 'DELETE',
    });
    setSessions(prev => prev.filter(s => s.id !== id));
    if (currentSessionId === id) {
      const remaining = sessions.filter(s => s.id !== id);
      setCurrentSessionId(remaining.length > 0 ? remaining[0].id : null);
    }
  }, [currentSessionId, sessions]);

  const updateSessionTitle = useCallback(async (id: string, title: string) => {
    await fetchJson<SessionResponse>(getApiUrl(API_CONFIG.endpoints.session.update(id)), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    });
    setSessions(prev =>
      prev.map(s => s.id === id ? { ...s, title, updatedAt: Date.now() } : s)
    );
  }, []);

  const pinSession = useCallback(async (id: string) => {
    const session = sessions.find(s => s.id === id);
    if (!session) return;
    const newPinned = !session.isPinned;
    await fetchJson<SessionResponse>(getApiUrl(API_CONFIG.endpoints.session.update(id)), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_pinned: newPinned }),
    });
    setSessions(prev =>
      prev.map(s => s.id === id ? { ...s, isPinned: newPinned, updatedAt: Date.now() } : s)
    );
  }, [sessions]);

  const moveSessionToGroup = useCallback(async (sessionId: string, groupId: string | undefined) => {
    await fetchJson<SessionResponse>(getApiUrl(API_CONFIG.endpoints.session.update(sessionId)), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ group_id: groupId }),
    });
    setSessions(prev =>
      prev.map(s => s.id === sessionId ? { ...s, groupId, updatedAt: Date.now() } : s)
    );
  }, []);

  // ========== Message Operations ==========

  const addMessage = useCallback(async (sessionId: string, message: { role: string; content: string }): Promise<Message> => {
    const data = await fetchJson<MessageResponse>(getApiUrl(API_CONFIG.endpoints.session.addMessage(sessionId)), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(message),
    });
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