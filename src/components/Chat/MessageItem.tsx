import { Message } from '../../types/session';

interface MessageItemProps {
  message: Message;
}

export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`mb-4 ${isUser ? 'flex justify-end' : ''}`}>
      <div className={`${isUser ? 'message-user max-w-[80%]' : 'message-ai'}`}>
        {/* 消息内容 */}
        <div className="text-[#1a1a1a] whitespace-pre-wrap break-words leading-relaxed">
          {message.content}
        </div>
      </div>
    </div>
  );
}