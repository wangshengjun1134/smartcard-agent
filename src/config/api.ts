/// <reference types="vite/client" />

/**
 * API Configuration
 * Centralized configuration for backend API endpoints
 */

// API base URL - defaults to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * API endpoints configuration
 */
export const API_CONFIG = {
  baseUrl: API_BASE_URL,
  endpoints: {
    files: {
      tree: '/api/files/tree',
      upload: '/api/files/upload',
      detail: (fileId: string) => `/api/files/${fileId}`,
      createFolder: '/api/files/folder',
      move: '/api/files/move',
    },
    health: '/health',
  },
};

/**
 * Build full API URL for an endpoint
 * @param endpoint - API endpoint path
 * @returns Full URL
 */
export function getApiUrl(endpoint: string): string {
  return `${API_CONFIG.baseUrl}${endpoint}`;
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
  maxFileSizeMB: 50, // Frontend limit (50MB)
  allowedExtensions: ['.pdf', '.doc', '.docx', '.md', '.markdown', '.txt', '.png', '.jpg', '.jpeg', '.gif', '.webp'],
};