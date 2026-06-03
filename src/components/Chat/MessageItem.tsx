import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { Message } from '../../types/session';
import { isDarkMode, watchThemeChange, ensureHighlightThemeLoaded } from '../../utils/theme';

interface MessageItemProps {
  message: Message;
}

/**
 * 复制文本到剪贴板（支持 fallback）
 */
async function copyToClipboard(text: string): Promise<boolean> {
  try {
    // 首先尝试现代 API
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }

    // Fallback: 使用传统方法
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.left = '-9999px';
    textarea.style.top = '-9999px';
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();

    const success = document.execCommand('copy');
    document.body.removeChild(textarea);
    return success;
  } catch (err) {
    console.error('Copy failed:', err);
    return false;
  }
}

/**
 * 提取代码文本的辅助函数
 */
function extractCodeText(element: React.ReactElement | null | undefined): string {
  if (!element) return '';

  const children = element.props?.children;

  if (typeof children === 'string') return children;
  if (typeof children === 'number') return String(children);
  if (Array.isArray(children)) {
    return children.map(child => {
      if (typeof child === 'string' || typeof child === 'number') return String(child);
      if (React.isValidElement(child)) return extractCodeText(child);
      return '';
    }).join('');
  }
  if (React.isValidElement(children)) {
    return extractCodeText(children);
  }

  return '';
}

export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user';
  const [showThinking, setShowThinking] = useState(false);

  // 使用ref存储取消监听函数，避免重复创建
  const unwatchRef = useRef<(() => void) | null>(null);

  // 检测当前主题并监听变化（优化：只创建一次observer）
  useEffect(() => {
    // 确保高亮样式已加载
    ensureHighlightThemeLoaded(isDarkMode());

    // 监听主题变化（使用统一的工具函数）
    unwatchRef.current = watchThemeChange((newIsDark) => {
      ensureHighlightThemeLoaded(newIsDark);
    });

    return () => {
      // 清理监听
      if (unwatchRef.current) {
        unwatchRef.current();
        unwatchRef.current = null;
      }
    };
  }, []); // 空依赖数组，只在组件挂载时执行一次

  const hasThinking = !isUser && message.thinkingContent;

  // 复制按钮点击处理
  const handleCopyClick = async (e: React.MouseEvent<HTMLButtonElement>, codeText: string) => {
    const btn = e.currentTarget;
    const original = btn.innerText;

    const success = await copyToClipboard(codeText);

    if (success) {
      btn.innerText = '✓ 已复制';
    } else {
      btn.innerText = '复制失败';
    }

    setTimeout(() => btn.innerText = original, 1500);
  };

  return (
    <div className={`mb-4 ${isUser ? 'flex justify-end' : ''}`}>
      <div className={`${isUser ? 'message-user max-w-[80%]' : 'message-ai'}`}>
        {/* 思考过程折叠按钮 */}
        {hasThinking && (
          <div className="mb-2">
            <button
              onClick={() => setShowThinking(!showThinking)}
              className="flex items-center gap-2 text-xs text-gray-500 hover:text-gray-700 transition-colors"
            >
              <span className={`transform transition-transform ${showThinking ? 'rotate-90' : ''}`}>
                ▶
              </span>
              <span>思考过程</span>
            </button>
          </div>
        )}

        {/* 思考过程内容（纯文本，不使用Markdown） */}
        {hasThinking && showThinking && (
          <div className="mb-3 p-4 rounded-lg bg-gray-50 border border-gray-200 text-sm text-gray-600 whitespace-pre-wrap break-words">
            {message.thinkingContent}
          </div>
        )}

        {/* 消息内容（Markdown渲染） */}
        <div className="markdown-body text-[#1a1a1a] break-words leading-relaxed">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
            components={{
              pre: ({ children, ...props }) => {
                // Extract language from className (e.g., "language-java")
                const codeElement = children as React.ReactElement;
                const className = codeElement?.props?.className || '';
                const languageMatch = className.match(/language-(\w+)/);
                const language = languageMatch ? languageMatch[1] : 'code';

                // 提取代码文本用于复制
                const codeText = extractCodeText(codeElement);

                return (
                  <div className="code-block-wrapper">
                    <div className="code-block-header">
                      <span className="code-lang-tag">{language}</span>
                      <button
                        className="copy-btn"
                        onClick={(e) => handleCopyClick(e, codeText)}
                      >
                        复制
                      </button>
                    </div>
                    <pre className="code-block" {...props}>
                      {children}
                    </pre>
                  </div>
                );
              },
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}