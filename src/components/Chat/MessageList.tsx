import { useEffect, useRef } from 'react';
import { Message } from '../../types/session';
import { MessageItem } from './MessageItem';
import { LoadingIndicator } from './LoadingIndicator';

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
  hasSession: boolean;
}

export function MessageList({ messages, isLoading, hasSession }: MessageListProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    if (containerRef.current && messages.length > 0) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  // 空状态：欢迎界面
  if (messages.length === 0 && !isLoading && !hasSession) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center pb-16">
        {/* 欢迎图标 */}
        <div className="text-5xl mb-4">
          <svg className="w-16 h-16 text-gradient-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ stroke: '#5870f6' }}>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zM14 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
          </svg>
        </div>
        {/* 欢迎文字 */}
        <div className="text-2xl text-[#1a1a1a] tracking-wide">
          你好，我是SmartCardAgent
        </div>
      </div>
    );
  }

  // 消息列表
  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto"
    >
      <div className="max-w-[700px] mx-auto px-5 py-4">
        {messages.map((message) => (
          <MessageItem key={message.id} message={message} />
        ))}
        {isLoading && <LoadingIndicator />}
      </div>
    </div>
  );
}