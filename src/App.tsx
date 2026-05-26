import { useState } from 'react';
import { useSessions } from './hooks/useSessions';
import { AppLayout } from './components/layout/AppLayout';
import { Sidebar, ViewType } from './components/Sidebar/Sidebar';
import { MessageList } from './components/Chat/MessageList';
import { ChatInput } from './components/Chat/ChatInput';
import { ChatHeader } from './components/Chat/ChatHeader';
import { KnowledgeBase } from './components/Pages/KnowledgeBase';
import { SkillsBase } from './components/Pages/SkillsBase';
import { ThemeProvider } from './contexts/ThemeContext';
import { getApiUrl, API_CONFIG, DEFAULT_HEADERS } from './config/api';
import iconImage from './images/icon.png';

function App() {
  const [currentView, setCurrentView] = useState<ViewType>('chat');
  const [sidebarOpen, setSidebarOpen] = useState(true);

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
    createGroup,
    updateGroup,
    deleteGroup,
    pinGroup,
    pinSession,
    moveSessionToGroup,
  } = useSessions();

  // 发送消息处理
  const handleSendMessage = async (content: string) => {
    // 如果没有当前会话，先创建一个
    let sessionId = currentSessionId;
    if (!sessionId) {
      const newSession = await createSession();
      sessionId = newSession.id;
    }

    // 添加用户消息
    await addMessage(sessionId, { role: 'user', content });

    // 调用后端 Agent API
    try {
      const response = await fetch(getApiUrl(API_CONFIG.endpoints.agent.chat), {
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

      if (response.ok) {
        const data = await response.json();
        await addMessage(sessionId, {
          role: 'assistant',
          content: data.response || 'Agent 返回空响应',
        });
      } else {
        const errorData = await response.json();
        await addMessage(sessionId, {
          role: 'assistant',
          content: `请求失败: ${errorData.detail || response.statusText}`,
        });
      }
    } catch (error) {
      console.error('Agent API error:', error);
      await addMessage(sessionId, {
        role: 'assistant',
        content: `网络错误: ${error instanceof Error ? error.message : '未知错误'}`,
      });
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