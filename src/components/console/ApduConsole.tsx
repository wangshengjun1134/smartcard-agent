import { useState, useRef, useEffect, useCallback } from 'react';

interface ApduEntry {
  id: number;
  send: string;
  resp: string;
  duration: number;
  timestamp: string;
  isError?: boolean;
}

interface ReaderInfo {
  name: string;
  connected: boolean;
}

const MAX_ENTRIES = 50;
const MAX_READER_NAME_LENGTH = 35;

// API 基础 URL
const API_BASE = 'http://127.0.0.1:8000/api';

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

const ReaderIcon = () => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    className="w-3.5 h-3.5"
  >
    <rect x="2" y="6" width="20" height="12" rx="2" />
    <line x1="6" y1="10" x2="6" y2="14" />
    <line x1="10" y1="10" x2="10" y2="14" />
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

const SendIcon = () => (
  <svg
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
    strokeWidth="2"
    className="w-3.5 h-3.5"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M5 10l7-7m0 0l7 7m-7-7v18"
    />
  </svg>
);

export default function ApduConsole() {
  const [readers, setReaders] = useState<ReaderInfo[]>([]);
  const [selectedReader, setSelectedReader] = useState<string | null>(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [entries, setEntries] = useState<ApduEntry[]>([]);
  const [inputValue, setInputValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const consoleRef = useRef<HTMLDivElement>(null);
  const entryIdRef = useRef(0);

  // 获取读卡器列表
  const fetchReaders = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const response = await fetch(`${API_BASE}/smartcard/readers`);
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

  // 新条目添加时自动滚动到底部
  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [entries]);

  // 窗口控制
  const handleMinimize = useCallback(async () => {
    if (window.__TAURI__?.webviewWindow) {
      const appWindow =
        window.__TAURI__.webviewWindow.getCurrentWebviewWindow();
      await appWindow.minimize();
    }
  }, []);

  const handleToggleMaximize = useCallback(async () => {
    if (window.__TAURI__?.webviewWindow) {
      const appWindow =
        window.__TAURI__.webviewWindow.getCurrentWebviewWindow();
      await appWindow.toggleMaximize();
    }
  }, []);

  const handleClose = useCallback(async () => {
    if (window.__TAURI__?.webviewWindow) {
      const appWindow =
        window.__TAURI__.webviewWindow.getCurrentWebviewWindow();
      await appWindow.close();
    }
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
    (sendApdu: string, respApdu: string, duration: number, isError = false) => {
      const newEntry: ApduEntry = {
        id: entryIdRef.current++,
        send: sendApdu,
        resp: respApdu,
        duration,
        timestamp: getCurrentTime(),
        isError,
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
        const response = await fetch(`${API_BASE}/smartcard/connect`, {
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
        const response = await fetch(`${API_BASE}/smartcard/disconnect`, {
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
  }, [selectedReader, isConnected]);

  // 输入处理
  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setInputValue(e.target.value);
      if (textareaRef.current) {
        textareaRef.current.style.height = '32px';
        textareaRef.current.style.height =
          Math.min(textareaRef.current.scrollHeight, 120) + 'px';
      }
    },
    []
  );

  const handleSendApdu = useCallback(async () => {
    const trimmed = inputValue.trim();
    if (!trimmed) return;

    const lines = trimmed.split('\n').filter((line) => line.trim());
    for (const line of lines) {
      // 清理输入并格式化为空格分隔
      const cleaned = line.trim().replace(/\s/g, '');
      const formattedApdu = cleaned.match(/.{1,2}/g)?.join(' ') || cleaned;

      try {
        const response = await fetch(`${API_BASE}/smartcard/apdu`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            reader: selectedReader || '',
            apdu: formattedApdu,
          }),
        });
        if (!response.ok) {
          const error = await response.json();
          addEntry(formattedApdu, error.detail || '发送失败', 0, true);
          continue;
        }
        const data = await response.json();
        addEntry(data.apdu, data.response, data.duration);
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : '网络错误';
        addEntry(formattedApdu, errorMsg, 0, true);
      }
    }

    setInputValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = '32px';
    }
  }, [inputValue, selectedReader, addEntry]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendApdu();
      }
    },
    [handleSendApdu]
  );

  const hasInput = inputValue.trim().length > 0;
  const currentReaderInfo = readers.find((r) => r.name === selectedReader);

  return (
    <div className="flex flex-col h-screen bg-[#fafafa] text-[#1a1a1a] font-sans p-4">
      {/* 标题栏 - 在容器外部 */}
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

      <div className="flex-1 flex flex-col rounded-xl overflow-hidden bg-white shadow-sm">
      {/* 头部 */}
      <div className="bg-white px-4 h-[45px] flex items-center justify-end gap-3 flex-shrink-0">
        {/* 读卡器选择 */}
        <div className="relative flex items-center">
          <button
            className="flex items-center gap-1.5 px-2.5 py-1 bg-transparent border-none rounded-md cursor-pointer text-sm text-[#333] transition-[background] duration-150 hover:bg-[#e5e5e5]"
            onClick={handleToggleDropdown}
            title={selectedReader || undefined}
          >
            <ReaderIcon />
            <span>{selectedReader ? truncateReaderName(selectedReader) : '请选择读卡器'}</span>
            <ChevronDownIcon />
          </button>
          {isDropdownOpen && (
            <div className="absolute top-full right-0 mt-1 bg-white rounded-lg shadow-lg z-[1000] p-1 min-w-[360px]">
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
              className={`bg-white mb-2 p-2 px-3 rounded text-[13px] leading-relaxed font-mono ${
                entry.isError ? 'border-l-4 border-red-500 text-red-600' : ''
              }`}
            >
              <div className="flex justify-between items-start">
                <div className="flex items-start flex-1">
                  <span className={`font-bold w-4 mr-2 flex-shrink-0 ${entry.isError ? 'text-red-600' : 'text-[#fa8c16]'}`}>
                    &gt;
                  </span>
                  <span className="break-all flex-1">{entry.send}</span>
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

      {/* 输入区域 */}
      <div className="bg-white p-3 flex-shrink-0">
        <div className="bg-[#fafafa] rounded-2xl p-3 pb-2">
          <textarea
            ref={textareaRef}
            className="w-full text-[13px] font-mono bg-transparent border-none outline-none resize-none min-h-[32px] max-h-[120px] text-[#1a1a1a] placeholder:text-[#999]"
            placeholder="输入 APDU 指令 (Enter 发送, Shift+Enter 换行)"
            rows={1}
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
          />
          <div className="flex justify-end items-center mt-2">
            <button
              className={`w-7 h-7 rounded-full flex items-center justify-center border-none transition-[background] duration-150 cursor-pointer ${
                hasInput
                  ? 'bg-[#4b6ef3] cursor-pointer'
                  : 'bg-[#ccc] cursor-not-allowed'
              }`}
              onClick={handleSendApdu}
              disabled={!hasInput}
            >
              <SendIcon />
            </button>
          </div>
        </div>
      </div>
      </div>
    </div>
  );
}
