import { useState } from 'react';
import { useSessions } from './hooks/useSessions';
import { AppLayout } from './components/layout/AppLayout';
import { Sidebar, ViewType } from './components/Sidebar/Sidebar';
import { MessageList } from './components/Chat/MessageList';
import { ChatInput } from './components/Chat/ChatInput';
import { ChatHeader } from './components/Chat/ChatHeader';
import { KnowledgeBase } from './components/Pages/KnowledgeBase';
import { SkillsBase } from './components/Pages/SkillsBase';
import { ThinkingPanel } from './components/Chat/ThinkingPanel';
import { ThemeProvider } from './contexts/ThemeContext';
import { getApiUrl, API_CONFIG, DEFAULT_HEADERS } from './config/api';
import iconImage from './images/icon.png';

// SSE event types for routing decision
interface RoutingDecision {
  type: 'routing';
  from: string;
  to: string;
  reason: string;
  confidence?: number;
}

function App() {
  const [currentView, setCurrentView] = useState<ViewType>('chat');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  
  // Thinking process state
  const [thinkingSteps, setThinkingSteps] = useState<string[]>([]);
  const [routingDecision, setRoutingDecision] = useState<RoutingDecision | null>(null);
  const [showThinking, setShowThinking] = useState(true);

  const {
    sessions,
    groups,
    currentSession,
    currentSessionId,
    isLoading,
    createSession,
    switchSession,
    deleteSession,
    updateSessionTitle,
    addMessage,
    updateMessageContent,
    createGroup,
    updateGroup,
    deleteGroup,
    pinGroup,
    pinSession,
    moveSessionToGroup,
  } = useSessions();

  // 发送消息处理（流式响应）
  const handleSendMessage = async (content: string) => {
    // 清除之前的思考过程
    setThinkingSteps([]);
    setRoutingDecision(null);
    
    // 如果没有当前会话，先创建一个
    let sessionId = currentSessionId;
    if (!sessionId) {
      const newSession = await createSession();
      sessionId = newSession.id;
    }

    // 获取当前消息数量（用于计算 assistant 消息索引）
    const currentMessagesCount = sessions.find(s => s.id === sessionId)?.messages.length ?? 0;

    // 添加用户消息
    await addMessage(sessionId, { role: 'user', content });

    // 添加空的 assistant 消息（用于流式更新）
    await addMessage(sessionId, { role: 'assistant', content: '' });

    // assistant 消息索引 = 用户消息后 + assistant 消息
    const assistantMessageIndex = currentMessagesCount + 1;

    // 调用后端 Agent 流式 API
    try {
      const response = await fetch(getApiUrl(API_CONFIG.endpoints.agent.chatStream), {
        method: 'POST',
        headers: {
          ...DEFAULT_HEADERS,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        updateMessageContent(sessionId, assistantMessageIndex, `请求失败: ${errorData.detail || response.statusText}`);
        return;
      }

      // 处理 SSE 流式响应
      const reader = response.body?.getReader();
      if (!reader) {
        updateMessageContent(sessionId, assistantMessageIndex, '无法读取响应流');
        return;
      }

      const decoder = new TextDecoder();
      let accumulatedContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              // 处理思考过程事件
              if (data.type === 'thinking' || data.type === 'thinking_chunk') {
                setThinkingSteps(prev => [...prev, data.content]);
              } 
              // 处理路由决策事件
              else if (data.type === 'routing') {
                setRoutingDecision({
                  type: 'routing',
                  from: data.from,
                  to: data.to,
                  reason: data.reason,
                  confidence: data.confidence,
                });
              }
              // 处理内容事件
              else if (data.type === 'content') {
                // 累积内容并更新消息
                accumulatedContent += data.content;
                updateMessageContent(sessionId, assistantMessageIndex, accumulatedContent);
              } 
              // 处理完成事件
              else if (data.type === 'done') {
                // 流式结束，更新最终消息
                updateMessageContent(sessionId, assistantMessageIndex, data.response || accumulatedContent);
                // 3秒后自动隐藏思考过程面板
                setTimeout(() => setShowThinking(false), 3000);
              }
              // 处理节点执行状态事件
              else if (data.type === 'node') {
                console.log(`[Node] ${data.node} - ${data.status || 'executed'}`);
              }
              // 处理错误事件
              else if (data.type === 'error') {
                console.error(`[Error] ${data.error}`);
              }
            } catch (e) {
              console.error('Parse SSE error:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Agent API error:', error);
      updateMessageContent(sessionId, assistantMessageIndex, `网络错误: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  };

  if (isLoading) {
    return (
      <div className="h-screen bg-[#ffffff] flex items-center justify-center">
        <div className="text-[#999]">加载中...</div>
      </div>
    );
  }

  // 根据视图渲染不同的主内容
  const renderMainContent = () => {
    if (currentView === 'knowledge') {
      return <KnowledgeBase />;
    }
    if (currentView === 'skills') {
      return <SkillsBase />;
    }
    // 默认聊天视图
    const hasMessages = (currentSession?.messages?.length ?? 0) > 0;

    return (
      <div className="flex-1 flex flex-col min-h-0">
        {/* 聊天顶部栏 */}
        <ChatHeader
          sidebarOpen={sidebarOpen}
          onToggleSidebar={() => setSidebarOpen(prev => !prev)}
        />

        {/* 内容区域 */}
        {hasMessages ? (
          <>
            {/* 思考过程面板 */}
            {(thinkingSteps.length > 0 || routingDecision) && showThinking && (
              <div className="max-w-[700px] mx-auto px-5 pt-2">
                <ThinkingPanel
                  steps={thinkingSteps}
                  routing={routingDecision}
                  collapsed={false}
                />
              </div>
            )}
            
            {/* 消息列表 */}
            <div className="flex-1 min-h-0 flex flex-col">
              <MessageList
                messages={currentSession?.messages || []}
                isLoading={false}
                hasSession={!!currentSessionId}
              />
            </div>
            {/* 输入区域 - 底部 */}
            <div className="flex flex-col items-center pb-3 shrink-0">
              <ChatInput
                onSend={handleSendMessage}
                disabled={false}
              />
            </div>
          </>
        ) : (
          /* 无消息时 - 整体居中 */
          <div className="flex-1 flex flex-col items-center justify-center">
            {/* 欢迎图标 */}
            <div className="mb-4">
              <img src={iconImage} alt="SmartCardAgent" className="w-16 h-16" />
            </div>
            {/* 欢迎文字 */}
            <div className="text-2xl text-[#1a1a1a] tracking-wide mb-8">
              你好，我是SmartCardAgent
            </div>
            {/* 输入框 */}
            <ChatInput
              onSend={handleSendMessage}
              disabled={false}
            />
          </div>
        )}
      </div>
    );
  };

  return (
    <ThemeProvider>
      <AppLayout
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen(prev => !prev)}
        sidebar={
          <Sidebar
            sessions={sessions}
            groups={groups}
            currentSessionId={currentSessionId}
            currentView={currentView}
            onNewSession={createSession}
            onSelectSession={switchSession}
            onDeleteSession={deleteSession}
            onUpdateSessionTitle={updateSessionTitle}
            onPinSession={pinSession}
            onMoveSessionToGroup={moveSessionToGroup}
            onCreateGroup={createGroup}
            onUpdateGroup={updateGroup}
            onDeleteGroup={deleteGroup}
            onPinGroup={pinGroup}
            onViewChange={setCurrentView}
          />
        }
        main={renderMainContent()}
      />
    </ThemeProvider>
  );
}

export default App;