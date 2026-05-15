import { useState, useEffect, useCallback } from 'react';
import { Session, Message } from '../types/session';
import {
  loadSessions,
  saveSessions,
  loadCurrentSessionId,
  saveCurrentSessionId,
  generateId,
} from '../utils/storage';

export function useSessions() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 初始化加载
  useEffect(() => {
    const savedSessions = loadSessions();
    const savedCurrentId = loadCurrentSessionId();

    setSessions(savedSessions);
    setCurrentSessionId(savedCurrentId);
    setIsLoading(false);
  }, []);

  // 持久化 sessions
  useEffect(() => {
    if (!isLoading) {
      saveSessions(sessions);
    }
  }, [sessions, isLoading]);

  // 持久化 currentSessionId
  useEffect(() => {
    if (!isLoading) {
      saveCurrentSessionId(currentSessionId);
    }
  }, [currentSessionId, isLoading]);

  // 获取当前会话
  const currentSession = sessions.find(s => s.id === currentSessionId) || null;

  // 创建新会话
  const createSession = useCallback(() => {
    const newSession: Session = {
      id: generateId(),
      title: '新会话',
      createdAt: Date.now(),
      updatedAt: Date.now(),
      messages: [],
    };

    setSessions(prev => [newSession, ...prev]);
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
      prev.map(s =>
        s.id === id
          ? { ...s, title, updatedAt: Date.now() }
          : s
      )
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
      prev.map(s =>
        s.id === sessionId
          ? {
              ...s,
              messages: [...s.messages, newMessage],
              updatedAt: Date.now(),
              // 根据第一条用户消息自动生成标题
              title: s.messages.length === 0 && message.role === 'user'
                ? message.content.slice(0, 30) + (message.content.length > 30 ? '...' : '')
                : s.title,
            }
          : s
      )
    );

    return newMessage;
  }, []);

  return {
    sessions,
    currentSession,
    currentSessionId,
    isLoading,
    createSession,
    switchSession,
    deleteSession,
    updateSessionTitle,
    addMessage,
  };
}