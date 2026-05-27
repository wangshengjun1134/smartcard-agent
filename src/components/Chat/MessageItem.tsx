import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { useEffect, useState } from 'react';
import { Message } from '../../types/session';

interface MessageItemProps {
  message: Message;
}

// 复制文本到剪贴板（支持 fallback）
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

// 提取代码文本的辅助函数
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
  const [isDark, setIsDark] = useState(false);

  // 检测当前主题
  useEffect(() => {
    const checkDark = () => {
      setIsDark(document.documentElement.classList.contains('dark'));
    };
    checkDark();

    // 监听主题变化
    const observer = new MutationObserver(checkDark);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });

    return () => observer.disconnect();
  }, []);

  // 动态加载对应主题的高亮样式
  useEffect(() => {
    const linkId = 'hljs-theme';
    const existingLink = document.getElementById(linkId) as HTMLLinkElement;

    const themeUrl = isDark
      ? 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/styles/github-dark.min.css'
      : 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/styles/github.min.css';

    if (existingLink) {
      existingLink.href = themeUrl;
    } else {
      const link = document.createElement('link');
      link.id = linkId;
      link.rel = 'stylesheet';
      link.href = themeUrl;
      document.head.appendChild(link);
    }
  }, [isDark]);

  return (
    <div className={`mb-4 ${isUser ? 'flex justify-end' : ''}`}>
      <div className={`${isUser ? 'message-user max-w-[80%]' : 'message-ai'}`}>
        {/* 消息内容 */}
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
                        onClick={(e) => {
                          copyToClipboard(codeText).then(success => {
                            const btn = e.currentTarget;
                            const original = btn.innerText;
                            if (success) {
                              btn.innerText = '✓ 已复制';
                            } else {
                              btn.innerText = '复制失败';
                            }
                            setTimeout(() => btn.innerText = original, 1500);
                          });
                        }}
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