import { useSessions } from './hooks/useSessions';
import { AppLayout } from './components/layout/AppLayout';
import { Sidebar } from './components/Sidebar/Sidebar';
import { MessageList } from './components/Chat/MessageList';
import { ChatInput } from './components/Chat/ChatInput';

function App() {
  const {
    sessions,
    currentSession,
    currentSessionId,
    isLoading,
    createSession,
    switchSession,
    deleteSession,
    addMessage,
  } = useSessions();

  // 发送消息处理
  const handleSendMessage = (content: string) => {
    // 如果没有当前会话，先创建一个
    let sessionId = currentSessionId;
    if (!sessionId) {
      const newSession = createSession();
      sessionId = newSession.id;
    }

    // 添加用户消息
    addMessage(sessionId, { role: 'user', content });

    // TODO: 调用后端 Agent API
    // 模拟 AI 响应（后续替换为真实 API）
    setTimeout(() => {
      addMessage(sessionId!, {
        role: 'assistant',
        content: '这是一个模拟响应。请配置后端 Agent API 以获得真实回复。',
      });
    }, 1000);
  };

  if (isLoading) {
    return (
      <div className="h-screen bg-[#ffffff] flex items-center justify-center">
        <div className="text-[#999]">加载中...</div>
      </div>
    );
  }

  return (
    <AppLayout
      sidebar={
        <Sidebar
          sessions={sessions}
          currentSessionId={currentSessionId}
          onNewSession={createSession}
          onSelectSession={switchSession}
          onDeleteSession={deleteSession}
        />
      }
      main={
        <div className="h-full flex flex-col">
          {/* 消息区域 */}
          <MessageList
            messages={currentSession?.messages || []}
            isLoading={false}
            hasSession={!!currentSessionId}
          />

          {/* 输入区域 */}
          <div className="flex flex-col items-center pb-3">
            <ChatInput
              onSend={handleSendMessage}
              disabled={false}
            />
            {/* 底部提示 */}
            <div className="text-xs text-[#999] text-center py-3">
              按住 右Alt 随时随地语音输入
            </div>
          </div>
        </div>
      }
    />
  );
}

export default App;