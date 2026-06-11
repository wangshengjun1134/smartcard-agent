/// <reference types="vite/client" />

/**
 * API Configuration
 * Centralized configuration for backend API endpoints
 *
 * Services:
 * - Agent Service (port 8001): Agent chat, session, config, smartcard
 * - RAG Service (port 8002): Files, RAG query
 */

// Service base URLs - can be overridden via environment variables
const AGENT_BASE_URL = import.meta.env.VITE_AGENT_BASE_URL || 'http://localhost:8001';
const RAG_BASE_URL = import.meta.env.VITE_RAG_BASE_URL || 'http://localhost:8002';

/**
 * API endpoints configuration
 */
export const API_CONFIG = {
  agentBaseUrl: AGENT_BASE_URL,
  ragBaseUrl: RAG_BASE_URL,
  endpoints: {
    // RAG Service endpoints (port 8002)
    files: {
      tree: '/api/files/tree',
      upload: '/api/files/upload',
      detail: (fileId: string) => `/api/files/${fileId}`,
      createFolder: '/api/files/folder',
      move: '/api/files/move',
      rename: (fileId: string) => `/api/files/${fileId}/rename`,
      delete: (fileId: string) => `/api/files/${fileId}`,
    },
    documents: {
      upload: '/api/documents/upload',
      list: '/api/documents/list',
      detail: (docId: string) => `/api/documents/${docId}`,
      update: (docId: string) => `/api/documents/${docId}`,
      delete: (docId: string) => `/api/documents/${docId}`,
    },
    knowledgeBases: {
      list: '/api/knowledge-bases/list',
      create: '/api/knowledge-bases',
      detail: (kbId: string) => `/api/knowledge-bases/${kbId}`,
      update: (kbId: string) => `/api/knowledge-bases/${kbId}`,
      delete: (kbId: string) => `/api/knowledge-bases/${kbId}`,
    },
    rag: {
      query: '/api/rag/query',
      search: '/api/rag/search',
      info: '/api/rag/info',
    },
    // Agent Service endpoints (port 8001)
    session: {
      list: '/api/session/list',
      create: '/api/session/create',
      detail: (sessionId: string) => `/api/session/${sessionId}`,
      update: (sessionId: string) => `/api/session/${sessionId}`,
      delete: (sessionId: string) => `/api/session/${sessionId}`,
      messages: (sessionId: string) => `/api/session/${sessionId}/messages`,
      addMessage: (sessionId: string) => `/api/session/${sessionId}/messages`,
      groups: '/api/session/groups',
      createGroup: '/api/session/groups',
      updateGroup: (groupId: string) => `/api/session/groups/${groupId}`,
      deleteGroup: (groupId: string) => `/api/session/groups/${groupId}`,
    },
    config: {
      getApi: '/api/config/api',
      saveApi: '/api/config/api',
      testApi: '/api/config/api/test',
    },
    agent: {
      chat: '/api/agent/chat',
      chatStream: '/api/agent/chat/stream',
      status: '/api/agent/status',
      skills: '/api/agent/skills',
    },
    smartcard: {
      readers: '/api/smartcard/readers',
      connect: '/api/smartcard/connect',
      disconnect: '/api/smartcard/disconnect',
    },
    health: '/health',
  },
};

/**
 * Get base URL based on endpoint path
 * @param path - API endpoint path
 * @returns Base URL for the service
 */
function getBaseUrlForPath(path: string): string {
  // RAG service handles files, documents, knowledge-bases, and rag endpoints
  if (
    path.startsWith('/api/files') ||
    path.startsWith('/api/documents') ||
    path.startsWith('/api/knowledge-bases') ||
    path.startsWith('/api/rag')
  ) {
    return RAG_BASE_URL;
  }
  // Agent service handles all other endpoints
  return AGENT_BASE_URL;
}

/**
 * Build full API URL for an endpoint
 * @param endpoint - API endpoint path
 * @returns Full URL
 */
export function getApiUrl(endpoint: string): string {
  const baseUrl = getBaseUrlForPath(endpoint);
  return `${baseUrl}${endpoint}`;
}

/**
 * Get WebSocket URL for APDU events
 * @returns WebSocket URL
 */
export function getWebSocketUrl(): string {
  return `${AGENT_BASE_URL.replace('http', 'ws')}/ws/apdu`;
}

/**
 * Default headers for API requests
 */
export const DEFAULT_HEADERS = {
  'Accept': 'application/json',
};

/**
 * File upload constraints
 */
export const FILE_UPLOAD_CONSTRAINTS = {
  maxFileSizeMB: 50,
  allowedExtensions: ['.pdf', '.doc', '.docx', '.md', '.markdown', '.txt', '.png', '.jpg', '.jpeg', '.gif', '.webp'],
};