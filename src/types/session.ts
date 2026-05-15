export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: number;
}

export interface Session {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: Message[];
  groupId?: string;
  isPinned?: boolean;
}

export interface Group {
  id: string;
  name: string;
  icon: string;
  createdAt: number;
  isPinned?: boolean;
}

export type SessionState = {
  sessions: Session[];
  currentSessionId: string | null;
  isLoading: boolean;
};