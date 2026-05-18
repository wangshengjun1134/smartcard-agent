import { useEffect, useRef } from 'react';
import { Message } from '../../types/session';
import { MessageItem } from './MessageItem';
import { LoadingIndicator } from './LoadingIndicator';
import iconImage from '../../images/icon.png';

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
        <div className="mb-4">
          <img src={iconImage} alt="SmartCardAgent" className="w-16 h-16" />
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