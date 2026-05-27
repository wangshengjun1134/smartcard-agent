/**
 * 统一的API请求工具
 * 提供统一的错误处理、请求封装和响应解析
 */

import { getApiUrl, DEFAULT_HEADERS } from '../config/api';

/**
 * API错误类
 * 统一的错误类型，便于错误处理
 */
export class ApiError extends Error {
  public readonly status: number;
  public readonly detail?: string;

  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

/**
 * 请求配置接口
 */
interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
  headers?: Record<string, string>;
  retries?: number;
  retryDelay?: number;
}

/**
 * 默认重试配置
 */
const DEFAULT_RETRIES = 3;
const DEFAULT_RETRY_DELAY = 500;

/**
 * 统一的fetch请求函数
 * 包含错误处理、重试机制和响应解析
 */
export async function apiFetch<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const {
    method = 'GET',
    body,
    headers = {},
    retries = DEFAULT_RETRIES,
    retryDelay = DEFAULT_RETRY_DELAY,
  } = options;

  const mergedHeaders = mergeHeaders(headers);

  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      const response = await fetch(getApiUrl(endpoint), {
        method,
        headers: mergedHeaders,
        body: body ? JSON.stringify(body) : undefined,
      });

      if (!response.ok) {
        const errorData = await parseErrorResponse(response);
        throw new ApiError(
          response.status,
          errorData.detail || `请求失败: ${response.status}`,
          errorData.detail
        );
      }

      return parseSuccessResponse<T>(response);
    } catch (error) {
      if (attempt < retries - 1) {
        // 指数退避重试
        const delay = retryDelay * Math.pow(2, attempt);
        await sleep(delay);
        console.warn(`API请求重试 (${attempt + 1}/${retries}): ${endpoint}`);
      } else {
        // 最后一次尝试失败，抛出错误
        if (error instanceof ApiError) {
          throw error;
        }
        throw new ApiError(
          0,
          error instanceof Error ? error.message : '网络请求失败'
        );
      }
    }
  }

  throw new ApiError(0, '超过最大重试次数');
}

/**
 * 解析错误响应
 */
async function parseErrorResponse(response: Response): Promise<{ detail?: string }> {
  try {
    return await response.json();
  } catch {
    return { detail: response.statusText };
  }
}

/**
 * 解析成功响应
 */
async function parseSuccessResponse<T>(response: Response): Promise<T> {
  const data = await response.json();
  
  // 处理标准API响应格式 { status: 'ok', data: ... }
  if (data && typeof data === 'object' && 'status' in data) {
    if (data.status === 'ok' && 'data' in data) {
      return data.data as T;
    }
    throw new ApiError(0, data.message || 'API响应格式错误');
  }
  
  return data as T;
}

/**
 * 合并请求头
 * 使用缓存避免重复创建对象
 */
const cachedHeaders: Map<string, Record<string, string>> = new Map();

function mergeHeaders(customHeaders: Record<string, string>): Record<string, string> {
  const cacheKey = JSON.stringify(customHeaders);
  
  if (cachedHeaders.has(cacheKey)) {
    return cachedHeaders.get(cacheKey)!;
  }
  
  const merged = {
    ...DEFAULT_HEADERS,
    ...customHeaders,
  };
  
  // 仅缓存有限的常用配置
  if (cachedHeaders.size < 10) {
    cachedHeaders.set(cacheKey, merged);
  }
  
  return merged;
}

/**
 * 常用headers预设
 * 避免每次请求创建新对象
 */
export const JSON_HEADERS: Record<string, string> = {
  ...DEFAULT_HEADERS,
  'Content-Type': 'application/json',
};

/**
 * 延迟函数
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * GET请求快捷方法
 */
export function apiGet<T>(endpoint: string): Promise<T> {
  return apiFetch<T>(endpoint, { method: 'GET' });
}

/**
 * POST请求快捷方法
 */
export function apiPost<T>(endpoint: string, body: unknown): Promise<T> {
  return apiFetch<T>(endpoint, {
    method: 'POST',
    body,
    headers: { 'Content-Type': 'application/json' },
  });
}

/**
 * PUT请求快捷方法
 */
export function apiPut<T>(endpoint: string, body: unknown): Promise<T> {
  return apiFetch<T>(endpoint, {
    method: 'PUT',
    body,
    headers: { 'Content-Type': 'application/json' },
  });
}

/**
 * DELETE请求快捷方法
 */
export function apiDelete<T>(endpoint: string): Promise<T> {
  return apiFetch<T>(endpoint, { method: 'DELETE' });
}