import { useState, useRef, useEffect, useCallback } from 'react';
import { getApiUrl, getWebSocketUrl } from '../../config/api';
import { getCurrentWebviewWindow } from '@tauri-apps/api/webviewWindow';

interface ApduEntry {
  id: number;
  send: string;
  resp: string;
  duration: number;
  timestamp: string;
  isError?: boolean;
  source?: string; // 'agent' or 'console'
}

interface ReaderInfo {
  name: string;
  connected: boolean;
}

interface ApduConsoleProps {
  embedded?: boolean; // 嵌入模式（无标题栏）
}

const MAX_ENTRIES = 50;
const MAX_READER_NAME_LENGTH = 35;

// 智能截断读卡器名称
function truncateReaderName(fullName: string): string {
  if (fullName.length <= MAX_READER_NAME_LENGTH) {
    return fullName;
  }

  // 尝试提取序列号（括号中的数字）
  const serialMatch = fullName.match(/\((\d+)\)/);
  const serialSuffix = serialMatch ? serialMatch[1].slice(-6) : null;

  // 提取厂商 + 型号（前几个单词）
  const parts = fullName.split(/\s+/);
  let shortName = '';
  for (const part of parts) {
    if ((shortName + ' ' + part).length > 20) break;
    shortName = shortName ? shortName + ' ' + part : part;
  }

  // 组合：短名称 + 序列号后6位
  if (serialSuffix) {
    const truncated = `${shortName} …(${serialSuffix})`;
    if (truncated.length <= MAX_READER_NAME_LENGTH) {
      return truncated;
    }
  }

  // 回退：简单截断
  return fullName.slice(0, MAX_READER_NAME_LENGTH - 1) + '…';
}

function getCurrentTime(): string {
  const d = new Date();
  return [
    d.getHours().toString().padStart(2, '0'),
    d.getMinutes().toString().padStart(2, '0'),
    d.getSeconds().toString().padStart(2, '0'),
    d.getMilliseconds().toString().padStart(3, '0'),
  ].join(':').replace(/(\d{2}:\d{2}:\d{2}):(\d{3})/, '$1.$2');
}

// 图标组件
const MinimizeIcon = () => (
  <svg viewBox="0 0 10 10" className="w-2.5 h-2.5">
    <path d="M 0 5 L 10 5" stroke="currentColor" strokeWidth="1" />
  </svg>
);

const MaximizeIcon = () => (
  <svg viewBox="0 0 10 10" className="w-2.5 h-2.5">
    <rect
      x="0.5"
      y="0.5"
      width="9"
      height="9"
      stroke="currentColor"
      strokeWidth="1"
      fill="none"
    />
  </svg>
);

const CloseIcon = () => (
  <svg viewBox="0 0 10 10" className="w-2.5 h-2.5">
    <path
      d="M 0 0 L 10 10 M 10 0 L 0 10"
      stroke="currentColor"
      strokeWidth="1"
    />
  </svg>
);

const ChevronDownIcon = () => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    className="w-3 h-3"
  >
    <polyline points="6 9 12 15 18 9" />
  </svg>
);

const RefreshIcon = () => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    className="w-3.5 h-3.5"
  >
    <path d="M21 2v6h-6M3 22v-6h6" />
    <path d="M21 8A9 9 0 005.64 3.64L3 6M3 16a9 9 0 0015.36 4.36L21 18" />
  </svg>
);

const CheckCircleIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
    <circle cx="12" cy="12" r="6" />
  </svg>
);

const ConnectIcon = () => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    className="w-3.5 h-3.5"
  >
    <circle cx="12" cy="12" r="10" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

const ConnectedIcon = () => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    className="w-3.5 h-3.5"
  >
    <circle cx="12" cy="12" r="10" />
    <circle cx="12" cy="12" r="6" fill="currentColor" />
  </svg>
);

export default function ApduConsole({ embedded = false }: ApduConsoleProps) {
  const [readers, setReaders] = useState<ReaderInfo[]>([]);
  const [selectedReader, setSelectedReader] = useState<string | null>(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [entries, setEntries] = useState<ApduEntry[]>([]);
  const consoleRef = useRef<HTMLDivElement>(null);
  const entryIdRef = useRef(0);
  const wsRef = useRef<WebSocket | null>(null);
  const wsIdRef = useRef(0); // 用于跟踪 WebSocket 实例

  // 获取读卡器列表
  const fetchReaders = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const response = await fetch(getApiUrl('/api/smartcard/readers'));
      if (!response.ok) {
        throw new Error('Failed to fetch readers');
      }
      const data = await response.json();
      setReaders(data.readers);
    } catch (error) {
      console.error('Failed to fetch readers:', error);
      // 失败时使用空列表
      setReaders([]);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  // 组件加载时获取读卡器列表
  useEffect(() => {
    fetchReaders();
  }, [fetchReaders]);

  // WebSocket 连接 - 接收 agent 发送的 APDU 事件
  useEffect(() => {
    const currentWsId = ++wsIdRef.current; // 每个 effect 实例有唯一 ID
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    const connectWebSocket = () => {
      // 检查是否仍是当前 effect 实例
      if (wsIdRef.current !== currentWsId) return;

      try {
        const ws = new WebSocket(getWebSocketUrl());
        wsRef.current = ws;

        ws.onopen = () => {
          if (wsIdRef.current === currentWsId) {
            console.log('[WS] Connected to APDU event stream');
          }
        };

        ws.onmessage = (event) => {
          if (wsIdRef.current !== currentWsId) return;
          try {
            const message = JSON.parse(event.data);
            // 监听来自 skill 或 tool 的 APDU 事件（不包括 console 自己发送的）
            if (message.type === 'apdu_event' && (message.source === 'skill' || message.source === 'tool')) {
              // 收到 agent 发送的 APDU 事件，添加到控制台
              const { capdu, rapdu, sw, duration_ms, error } = message.data;
              const respDisplay = error
                ? `${rapdu} SW: ${sw} (${error})`
                : rapdu
                  ? `${rapdu} SW: ${sw}`
                  : `SW: ${sw}`;

              // 直接更新 entries state
              const newEntry: ApduEntry = {
                id: entryIdRef.current++,
                send: capdu,
                resp: respDisplay,
                duration: duration_ms,
                timestamp: getCurrentTime(),
                isError: !!error,
                source: message.source, // 'skill' 或 'tool'
              };
              setEntries((prev) => {
                const updated = [...prev, newEntry];
                return updated.slice(-MAX_ENTRIES);
              });
            }
          } catch (e) {
            // Ignore parse errors (ping/pong messages)
          }
        };

        ws.onerror = (error) => {
          if (wsIdRef.current === currentWsId) {
            console.error('[WS] Error:', error);
          }
        };

        ws.onclose = () => {
          if (wsIdRef.current === currentWsId) {
            console.log('[WS] Disconnected, reconnecting in 3s...');
            wsRef.current = null;
            // 自动重连
            reconnectTimer = setTimeout(connectWebSocket, 3000);
          }
        };
      } catch (e) {
        if (wsIdRef.current === currentWsId) {
          console.error('[WS] Connection failed:', e);
          // 重试
          reconnectTimer = setTimeout(connectWebSocket, 3000);
        }
      }
    };

    // 延迟连接，避免 React StrictMode 第一次 unmount 关闭连接
    const initTimer = setTimeout(connectWebSocket, 100);

    // Cleanup on unmount - 延迟清理，给下一个 effect 实例机会接管
    return () => {
      clearTimeout(initTimer);
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
      // 延迟关闭 WebSocket，如果是 StrictMode double-invoke，
      // 下一个 effect 实例会在 100ms 内接管 wsRef
      setTimeout(() => {
        // 只有当前 WebSocket ID 匹配时才关闭
        if (wsRef.current && wsIdRef.current === currentWsId) {
          wsRef.current.close();
          wsRef.current = null;
        }
      }, 200);
    };
  }, []);

  // 新条目添加时自动滚动到底部
  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [entries]);

  // 窗口控制（仅独立窗口模式使用）
  const handleMinimize = useCallback(async () => {
    const appWindow = getCurrentWebviewWindow();
    await appWindow.minimize();
  }, []);

  const handleToggleMaximize = useCallback(async () => {
    const appWindow = getCurrentWebviewWindow();
    await appWindow.toggleMaximize();
  }, []);

  const handleClose = useCallback(async () => {
    const appWindow = getCurrentWebviewWindow();
    await appWindow.close();
  }, []);

  // 读卡器选择
  const handleToggleDropdown = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      setIsDropdownOpen((prev) => !prev);
    },
    []
  );

  const handleSelectReader = useCallback((name: string) => {
    setSelectedReader(name);
    setIsDropdownOpen(false);
  }, []);

  // 点击外部关闭下拉
  useEffect(() => {
    const handleClickOutside = () => {
      setIsDropdownOpen(false);
    };
    document.addEventListener('click', handleClickOutside);
    return () =>
      document.removeEventListener('click', handleClickOutside);
  }, []);

  // 连接/断开
  const [isConnecting, setIsConnecting] = useState(false);

  const addEntry = useCallback(
    (sendApdu: string, respApdu: string, duration: number, isError = false, source: string = 'console') => {
      const newEntry: ApduEntry = {
        id: entryIdRef.current++,
        send: sendApdu,
        resp: respApdu,
        duration,
        timestamp: getCurrentTime(),
        isError,
        source,
      };
      setEntries((prev) => {
        const updated = [...prev, newEntry];
        return updated.slice(-MAX_ENTRIES);
      });
    },
    []
  );

  const handleToggleConnect = useCallback(async () => {
    if (!selectedReader) {
      addEntry('提示', '请先选择读卡器', 0, true);
      return;
    }

    setIsConnecting(true);
    try {
      if (!isConnected) {
        // 连接读卡器
        const response = await fetch(getApiUrl('/api/smartcard/connect'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reader: selectedReader }),
        });
        if (!response.ok) {
          const error = await response.json();
          addEntry(`连接失败 (${selectedReader})`, error.detail || '连接失败', 0, true);
          return;
        }
        const data = await response.json();
        console.log('[Connect] Response data:', data);
        setIsConnected(true);
        // 连接成功，将 ATR 以 APDU 形式显示在控制台
        if (data.atr) {
          addEntry(`ATR (${selectedReader})`, data.atr, 0);
        }
      } else {
        // 断开读卡器
        const response = await fetch(getApiUrl('/api/smartcard/disconnect'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reader: selectedReader }),
        });
        if (!response.ok) {
          const error = await response.json();
          addEntry(`断开失败 (${selectedReader})`, error.detail || '断开失败', 0, true);
          return;
        }
        setIsConnected(false);
      }
    } catch (error) {
      console.error('Connect/disconnect error:', error);
      const errorMsg = error instanceof Error ? error.message : '操作失败';
      addEntry('错误', errorMsg, 0, true);
    } finally {
      setIsConnecting(false);
    }
  }, [selectedReader, isConnected, addEntry]);

  // 嵌入模式下的容器样式
  const containerClass = embedded
    ? 'flex flex-col h-full bg-white text-[#1a1a1a] font-sans'
    : 'flex flex-col h-screen bg-[#fafafa] text-[#1a1a1a] font-sans p-4';

  return (
    <div className={containerClass}>
      {/* 标题栏 - 仅在独立窗口模式下显示 */}
      {!embedded && (
        <div
          className="bg-[#fafafa] h-8 flex items-center justify-between flex-shrink-0 rounded-xl px-3 -mt-1"
          data-tauri-drag-region
        >
          <div className="flex-1 flex items-center gap-2" data-tauri-drag-region />
          <div className="flex items-center" data-tauri-drag-region>
            <button
              className="w-11.5 h-8 flex items-center justify-center cursor-pointer bg-transparent border-none transition-[background] duration-150 hover:bg-[#e5e5e5]"
              onClick={handleMinimize}
            >
              <MinimizeIcon />
            </button>
            <button
              className="w-11.5 h-8 flex items-center justify-center cursor-pointer bg-transparent border-none transition-[background] duration-150 hover:bg-[#e5e5e5]"
              onClick={handleToggleMaximize}
            >
              <MaximizeIcon />
            </button>
            <button
              className="w-11.5 h-8 flex items-center justify-center cursor-pointer bg-transparent border-none transition-[background] duration-150 hover:bg-[#e81123] hover:text-white"
              onClick={handleClose}
            >
              <CloseIcon />
            </button>
          </div>
        </div>
      )}

      <div className={`flex-1 flex flex-col overflow-hidden ${embedded ? '' : 'rounded-xl bg-white shadow-sm'}`}>
      {/* 头部 */}
      <div className="bg-white px-4 h-[45px] flex items-center justify-end gap-3 flex-shrink-0">
        {/* 读卡器选择 */}
        <div className="relative flex items-center">
          <button
            className="flex items-center gap-1.5 px-2.5 py-1 bg-transparent border-none rounded-md cursor-pointer text-sm text-[#333] transition-[background] duration-150 hover:bg-[#e5e5e5]"
            onClick={handleToggleDropdown}
            title={selectedReader || undefined}
          >
            <span>{selectedReader ? truncateReaderName(selectedReader) : '请选择读卡器'}</span>
            <ChevronDownIcon />
          </button>
          {isDropdownOpen && (
            <div className="absolute top-full left-0 mt-1 bg-white rounded-lg shadow-lg z-[1000] p-1 min-w-[360px] max-w-[calc(100vw-32px)]">
              {readers.map((reader) => (
                <div
                  key={reader.name}
                  className={`flex items-center gap-2 px-3 py-2 cursor-pointer text-sm transition-[background] duration-150 ${
                    reader.name === selectedReader
                      ? 'bg-[#f0f2f5]'
                      : 'hover:bg-[#f7f8fa]'
                  }`}
                  onClick={() => handleSelectReader(reader.name)}
                  title={reader.name}
                >
                  <span
                    className={
                      reader.name === selectedReader
                        ? 'text-[#4b6ef3]'
                        : 'text-transparent'
                    }
                  >
                    <CheckCircleIcon />
                  </span>
                  <span className="truncate max-w-[280px]">{truncateReaderName(reader.name)}</span>
                  <span
                    className={`inline-flex items-center gap-1 text-[11px] px-1.5 py-0.5 rounded ml-auto flex-shrink-0 ${
                      reader.connected
                        ? 'bg-[#e6f7e6] text-[#52c41a]'
                        : 'bg-[#fff1f0] text-[#ff4d4f]'
                    }`}
                  >
                    {reader.connected ? '有卡' : '无卡'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 刷新按钮 */}
        <button
          className={`flex items-center gap-1.5 px-2.5 py-1 bg-transparent border-none rounded-md cursor-pointer text-sm transition-[background] duration-150 hover:bg-[#e5e5e5] text-[#333] ${
            isRefreshing ? 'opacity-50 cursor-not-allowed' : ''
          }`}
          onClick={fetchReaders}
          disabled={isRefreshing}
        >
          <span className={isRefreshing ? 'animate-spin' : ''}>
            <RefreshIcon />
          </span>
          <span>{isRefreshing ? '刷新中...' : '刷新'}</span>
        </button>

        {/* 连接/断开按钮 */}
        <button
          className={`flex items-center gap-1.5 px-2.5 py-1 bg-transparent border-none rounded-md cursor-pointer text-sm transition-[background] duration-150 hover:bg-[#e5e5e5] ${
            isConnected ? 'text-[#4b6ef3]' : 'text-[#333]'
          } ${isConnecting ? 'opacity-50 cursor-not-allowed' : ''}`}
          onClick={handleToggleConnect}
          disabled={isConnecting}
        >
          {isConnected ? <ConnectedIcon /> : <ConnectIcon />}
          <span>{isConnecting ? (isConnected ? '断开中...' : '连接中...') : (isConnected ? '断开' : '连接')}</span>
        </button>
      </div>

      {/* 控制台内容 */}
      <div ref={consoleRef} className="flex-1 p-4 overflow-y-auto bg-white">
        {entries.length === 0 ? (
          <div className="text-center text-[#999] py-10 text-sm font-mono italic">
            等待 APDU 指令...
          </div>
        ) : (
          entries.map((entry) => (
            <div
              key={entry.id}
              className={`mb-2 p-2 px-3 rounded text-[13px] leading-relaxed font-mono ${
                (entry.source === 'skill' || entry.source === 'tool')
                  ? 'bg-[#f0f7ff] border-l-2 border-[#4b6ef3]'
                  : 'bg-white'
              } ${entry.isError ? 'text-red-600' : ''}`}
            >
              <div className="flex justify-between items-start">
                <div className="flex items-start flex-1">
                  <span className={`font-bold w-4 mr-2 flex-shrink-0 ${entry.isError ? 'text-red-600' : (entry.source === 'skill' || entry.source === 'tool') ? 'text-[#4b6ef3]' : 'text-[#fa8c16]'}`}>
                    &gt;
                  </span>
                  <span className="break-all flex-1">{entry.send}</span>
                  {(entry.source === 'skill' || entry.source === 'tool') && (
                    <span className="text-[10px] text-[#4b6ef3] bg-[#e6f0ff] px-1.5 py-0.5 rounded ml-2 flex-shrink-0">
                      {entry.source === 'tool' ? 'AI' : 'Skill'}
                    </span>
                  )}
                </div>
                <span className={`text-[11px] w-[100px] text-right ml-3 flex-shrink-0 ${entry.isError ? 'text-red-400' : 'text-[#999]'}`}>
                  {entry.timestamp}
                </span>
              </div>
              <div className="flex justify-between items-start mt-1">
                <div className="flex items-start flex-1">
                  <span className={`font-bold w-4 mr-2 flex-shrink-0 ${entry.isError ? 'text-red-600' : 'text-[#4b6ef3]'}`}>
                    &lt;
                  </span>
                  <span className="break-all flex-1">{entry.resp}</span>
                </div>
                <span className={`text-xs w-[100px] text-right ml-3 flex-shrink-0 ${entry.isError ? 'text-red-400' : 'text-[#722ed1]'}`}>
                  {entry.duration} ms
                </span>
              </div>
            </div>
          ))
        )}
      </div>
      </div>
    </div>
  );
}
