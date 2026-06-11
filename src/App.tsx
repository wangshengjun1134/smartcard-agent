import { useState, useRef } from 'react';
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
import ApduConsole from './components/console/ApduConsole';
import { getCurrentWebviewWindow } from '@tauri-apps/api/webviewWindow';
import { PhysicalSize } from '@tauri-apps/api/dpi';

function App() {
  // 检查是否为 APDU 控制台窗口 - 同步检测避免空白闪烁
  const params = new URLSearchParams(window.location.search);
  const isApduConsoleWindow = params.get('view') === 'apdu-console' || window.location.hash === '#apdu-console';

  // 调试日志
  console.log('[App] URL:', window.location.href);
  console.log('[App] hash:', window.location.hash);
  console.log('[App] search:', window.location.search);
  console.log('[App] isApduConsoleWindow:', isApduConsoleWindow);

  // 如果是 APDU 控制台窗口（独立窗口模式），直接渲染
  if (isApduConsoleWindow) {
    console.log('[App] Rendering ApduConsole (window mode)');
    return <ApduConsole />;
  }

  const [currentView, setCurrentView] = useState<ViewType>('chat');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showApduConsole, setShowApduConsole] = useState(false); // APDU 控制台面板显示状态
  const originalWindowWidthRef = useRef<number | null>(null); // 记录原始窗口宽度
  const [chatAreaFixedWidth, setChatAreaFixedWidth] = useState<number | null>(null); // 会话区域固定宽度（像素）
  const [windowSizeAdjusted, setWindowSizeAdjusted] = useState(false); // 记录是否调整了窗口大小

  // 侧边栏固定宽度
  const SIDEBAR_WIDTH = 260;

  // 切换 APDU 控制台显示（带窗口大小调整和居中）
  const toggleApduConsole = async () => {
    const appWindow = getCurrentWebviewWindow();
    const currentSize = await appWindow.innerSize();
    const isMaximized = await appWindow.isMaximized();

    if (!showApduConsole) {
      // 显示控制台
      originalWindowWidthRef.current = currentSize.width;

      if (isMaximized) {
        // 最大化状态：使用比例布局，会话 2/3，控制台 1/3
        const chatWidth = Math.round(currentSize.width - SIDEBAR_WIDTH);
        setChatAreaFixedWidth(Math.round(chatWidth * 2 / 3));
        setWindowSizeAdjusted(false);
      } else {
        // 非最大化：调整窗口大小并居中
        const chatWidth = Math.round(currentSize.width - SIDEBAR_WIDTH);
        const consoleWidth = Math.round(chatWidth * 0.5);
        const newWidth = Math.round(currentSize.width + consoleWidth);

        await appWindow.setSize(new PhysicalSize(newWidth, currentSize.height));
        // 等待窗口大小调整完成后再居中
        await new Promise(resolve => setTimeout(resolve, 50));
        await appWindow.center();

        setChatAreaFixedWidth(chatWidth);
        setWindowSizeAdjusted(true);
      }

      setShowApduConsole(true);
    } else {
      // 隐藏控制台
      if (windowSizeAdjusted && originalWindowWidthRef.current) {
        await appWindow.setSize(new PhysicalSize(originalWindowWidthRef.current, currentSize.height));
        await new Promise(resolve => setTimeout(resolve, 50));
        await appWindow.center();
      }
      originalWindowWidthRef.current = null;
      setChatAreaFixedWidth(null);
      setWindowSizeAdjusted(false);
      setShowApduConsole(false);
    }
  };

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
      let accumulatedThinking = '';  // 思考过程
      let accumulatedAnswer = '';    // 最终回答

      // 收集思考过程数据（用于保存到消息）
      const collectedThinkingSteps: string[] = [];
      let collectedRouting: any = null;

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
              if (data.type === 'thinking') {
                if (data.content?.trim()) {
                  collectedThinkingSteps.push(data.content);
                  accumulatedThinking += data.content + '\n\n';
                  // 只传 thinkingContent 和 answer 分开
                  updateMessageContent(sessionId, assistantMessageIndex, accumulatedAnswer, undefined, accumulatedThinking);
                }
              } else if (data.type === 'thinking_chunk') {
                if (data.content?.trim()) {
                  if (collectedThinkingSteps.length === 0) {
                    collectedThinkingSteps.push(data.content);
                  } else {
                    collectedThinkingSteps[collectedThinkingSteps.length - 1] += data.content;
                  }
                  accumulatedThinking += data.content;
                  updateMessageContent(sessionId, assistantMessageIndex, accumulatedAnswer, undefined, accumulatedThinking);
                }
              }
              // 处理路由决策事件
              else if (data.type === 'routing') {
                const routing = {
                  from: data.from,
                  to: data.to,
                  reason: data.reason,
                  confidence: data.confidence,
                };
                collectedRouting = routing;
              }
              // 处理内容事件（最终回答）
              else if (data.type === 'content') {
                accumulatedAnswer += data.content;
                updateMessageContent(sessionId, assistantMessageIndex, accumulatedAnswer, undefined, accumulatedThinking);
              }
              // 处理完成事件
              else if (data.type === 'done') {
                const finalAnswer = data.response || accumulatedAnswer;

                // 构建思考过程 JSON 数据用于保存
                const thinkingProcessData = {
                  steps: collectedThinkingSteps,
                  routing: collectedRouting ? {
                    from: collectedRouting.from,
                    to: collectedRouting.to,
                    reason: collectedRouting.reason,
                    confidence: collectedRouting.confidence,
                  } : undefined,
                };
                const thinkingProcessJson = collectedThinkingSteps.length > 0
                  ? JSON.stringify(thinkingProcessData)
                  : undefined;

                // content = 最终回答, thinkingProcess = JSON, thinkingContent = 原始思考文本
                updateMessageContent(sessionId, assistantMessageIndex, finalAnswer, thinkingProcessJson, accumulatedThinking);
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

    // Chat 视图 - 支持右侧 APDU 控制台面板
    const hasMessages = (currentSession?.messages?.length ?? 0) > 0;

    // 计算布局宽度
    const chatAreaStyle = showApduConsole && chatAreaFixedWidth
      ? { width: `${chatAreaFixedWidth}px` }
      : {};

    // 控制台宽度：如果窗口调整了，使用固定宽度；否则自动填充剩余空间
    const consoleStyle = windowSizeAdjusted && chatAreaFixedWidth
      ? { width: `${Math.round(chatAreaFixedWidth * 0.5)}px` }
      : {};

    // 只有当 chatAreaFixedWidth 有值时才算真正显示控制台
    const isConsoleVisible = showApduConsole && chatAreaFixedWidth !== null;

    return (
      <div className="flex-1 flex min-h-0">
        {/* 主聊天区域 - 显示控制台时使用固定宽度，隐藏时占全宽 */}
        <div
          className={`flex flex-col min-h-0 ${isConsoleVisible ? 'flex-shrink-0' : 'flex-1'}`}
          style={isConsoleVisible ? chatAreaStyle : {}}
        >
          {/* 聊天顶部栏 */}
          <ChatHeader
            sidebarOpen={sidebarOpen}
            onToggleSidebar={() => setSidebarOpen(prev => !prev)}
          />

          {/* 内容区域 */}
          {hasMessages ? (
            <>
              {/* 消息列表容器 - 允许内部滚动 */}
              <div className="flex-1 min-h-0 overflow-hidden flex flex-col">
                <MessageList
                  messages={currentSession?.messages || []}
                  isLoading={false}
                  hasSession={!!currentSessionId}
                />
              </div>
              {/* 输入区域 - 底部固定 */}
              <div className="flex flex-col items-center pb-3 shrink-0">
                <ChatInput
                  onSend={handleSendMessage}
                  disabled={false}
                  showApduConsole={showApduConsole}
                  onToggleApduConsole={toggleApduConsole}
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
                showApduConsole={showApduConsole}
                onToggleApduConsole={toggleApduConsole}
              />
            </div>
          )}
        </div>

        {/* APDU 控制台面板 */}
        {/* 窗口调整时：固定宽度（会话的 50%）；否则：自动填充剩余空间 */}
        {isConsoleVisible && (
          <div
            className={`min-h-0 border-l border-gray-200 ${windowSizeAdjusted ? 'flex-shrink-0' : 'flex-1'}`}
            style={consoleStyle}
          >
            <ApduConsole embedded={true} />
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