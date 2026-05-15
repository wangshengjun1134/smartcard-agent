import { Message } from '../../types/session';
import { formatRelativeTime } from '../../utils/storage';

interface MessageItemProps {
  message: Message;
}

export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`mb-4 ${isUser ? 'flex justify-end' : ''}`}>
      <div className={`${isUser ? 'message-user max-w-[80%]' : 'message-ai'}`}>
        {/* 角色标识 */}
        {!isUser && (
          <div className="text-xs font-medium mb-1 text-[#5870f6]">千问</div>
        )}
        
        {/* 消息内容 */}
        <div className="text-[#1a1a1a] whitespace-pre-wrap break-words leading-relaxed">
          {message.content}
        </div>

        {/* 时间戳 */}
        <div className="text-xs text-[#999] mt-2">
          {formatRelativeTime(message.createdAt)}
        </div>
      </div>
    </div>
  );
}