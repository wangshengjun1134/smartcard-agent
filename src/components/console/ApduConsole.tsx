import { useState, useRef, useEffect, useCallback } from 'react';

interface ApduEntry {
  id: number;
  send: string;
  resp: string;
  duration: number;
  timestamp: string;
}

interface ReaderInfo {
  name: string;
  connected: boolean;
}

const MAX_ENTRIES = 50;

// API 基础 URL
const API_BASE = 'http://127.0.0.1:8000/api';

const sampleData = [
  {
    send: '00 A4 04 00 0E 32 50 41 59 2E 53 59 53 2E 44 44 46 30 31',
    resp: '6F 2C 84 0E 32 50 41 59 2E 53 59 53 2E 44 44 46 30 31 A5 1A 88 01 01 5F 2D 04 7A 68 2D 43 4E 9F 11 01 01 90 00',
    duration: 127,
  },
  {
    send: '00 B0 00 00 10',
    resp: '00 11 22 33 44 55 66 77 88 99 AA BB CC DD EE FF 90 00',
    duration: 45,
  },
  {
    send: '00 CA 9F 17 00',
    resp: '9F 17 01 02 90 00',
    duration: 32,
  },
  {
    send: '80 50 00 00 08 11 22 33 44 55 66 77 88',
    resp: '90 00',
    duration: 18,
  },
  {
    send: Array.from({ length: 256 }, (_, i) =>
      i.toString(16).padStart(2, '0').toUpperCase()
    ).join(' '),
    resp: Array.from({ length: 256 }, (_, i) =>
      i.toString(16).padStart(2, '0').toUpperCase()
    ).join(' ') + ' 90 00',
    duration: 256,
  },
];

function getCurrentTime(): string {
  const d = new Date();
  return [
    d.getHours().toString().padStart(2, '0'),
    d.getMinutes().toString().padStart(2, '0'),
    d.getSeconds().toString().padStart(2, '0'),
    d.getMilliseconds().toString().padStart(3, '0'),
  ].join(':').replace(/(\d{2}:\d{2}:\d{2}):(\d{3})/, '$1.$2');
}

function generateRandomResponse(sendApdu: string): string {
  const cleaned = sendApdu.replace(/\s/g, '');
  const len = Math.min(cleaned.length / 2, 20);
  const resp = Array.from({ length: len }, () =>
    Math.floor(Math.random() * 256)
      .toString(16)
      .padStart(2, '0')
      .toUpperCase()
  ).join(' ');
  return resp + ' 90 00';
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
  const [entries, setEntries] = useState<ApduEntry[]>(sampleData.map((d, i) => ({
    id: i,
    ...d,
    timestamp: '',
  })));
  const [inputValue, setInputValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const entryIdRef = useRef(sampleData.length);

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
  const handleToggleConnect = useCallback(() => {
    if (!selectedReader) {
      alert('请先选择读卡器');
      return;
    }
    setIsConnected((prev) => !prev);
  }, [selectedReader]);

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

  const addEntry = useCallback(
    (sendApdu: string, respApdu: string, duration: number) => {
      const newEntry: ApduEntry = {
        id: entryIdRef.current++,
        send: sendApdu,
        resp: respApdu,
        duration,
        timestamp: getCurrentTime(),
      };
      setEntries((prev) => {
        const updated = [newEntry, ...prev];
        return updated.slice(0, MAX_ENTRIES);
      });
    },
    []
  );

  const handleSendApdu = useCallback(() => {
    const trimmed = inputValue.trim();
    if (!trimmed) return;

    const lines = trimmed.split('\n').filter((line) => line.trim());
    lines.forEach((line) => {
      const sendApdu = line.trim();
      const respApdu = generateRandomResponse(sendApdu);
      const duration = Math.floor(Math.random() * 200) + 15;
      addEntry(sendApdu, respApdu, duration);
    });

    setInputValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = '32px';
    }
  }, [inputValue, addEntry]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        handleSendApdu();
      }
    },
    [handleSendApdu]
  );

  const hasInput = inputValue.trim().length > 0;
  const currentReaderInfo = readers.find((r) => r.name === selectedReader);

  return (
    <div className="flex flex-col h-screen bg-[#fafafa] text-[#1a1a1a] font-sans">
      {/* 标题栏 */}
      <div
        className="bg-[#f7f7f9] h-8 flex items-center justify-between flex-shrink-0"
        data-tauri-drag-region
      >
        <div className="flex-1 flex items-center pl-3 gap-2" data-tauri-drag-region />
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

      {/* 头部 */}
      <div className="bg-white px-4 h-[45px] flex items-center justify-end gap-3 border-b border-[#ececee] flex-shrink-0">
        {/* 读卡器选择 */}
        <div className="relative flex items-center">
          <button
            className="flex items-center gap-1.5 px-2.5 py-1 bg-transparent border-none rounded-md cursor-pointer text-sm text-[#333] transition-[background] duration-150 hover:bg-[#e5e5e5]"
            onClick={handleToggleDropdown}
          >
            <ReaderIcon />
            <span>{selectedReader || '请选择读卡器'}</span>
            <ChevronDownIcon />
          </button>
          {isDropdownOpen && (
            <div className="absolute top-full right-0 mt-1 bg-white rounded-lg shadow-lg min-w-[220px] z-[1000] p-1">
              {readers.map((reader) => (
                <div
                  key={reader.name}
                  className={`flex items-center gap-2 px-3 py-2 cursor-pointer text-sm transition-[background] duration-150 ${
                    reader.name === selectedReader
                      ? 'bg-[#f0f2f5]'
                      : 'hover:bg-[#f7f8fa]'
                  }`}
                  onClick={() => handleSelectReader(reader.name)}
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
                  <span>{reader.name}</span>
                  <span
                    className={`inline-flex items-center gap-1 text-[11px] px-1.5 py-0.5 rounded ml-auto ${
                      reader.connected
                        ? 'bg-[#e6f7e6] text-[#52c41a]'
                        : 'bg-[#fff1f0] text-[#ff4d4f]'
                    }`}
                  >
                    {reader.connected ? '已连接' : '未连接'}
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
          }`}
          onClick={handleToggleConnect}
        >
          {isConnected ? <ConnectedIcon /> : <ConnectIcon />}
          <span>{isConnected ? '断开' : '连接'}</span>
        </button>
      </div>

      {/* 控制台内容 */}
      <div className="flex-1 p-4 overflow-y-auto bg-[#fafafa]">
        {entries.length === 0 ? (
          <div className="text-center text-[#999] py-10 text-sm font-mono italic">
            等待 APDU 指令...
          </div>
        ) : (
          entries.map((entry) => (
            <div
              key={entry.id}
              className="bg-white mb-2 p-2 px-3 rounded text-[13px] leading-relaxed font-mono"
            >
              <div className="flex justify-between items-start">
                <div className="flex items-start flex-1">
                  <span className="font-bold w-4 mr-2 flex-shrink-0 text-[#fa8c16]">
                    &gt;
                  </span>
                  <span className="break-all flex-1">{entry.send}</span>
                </div>
                <span className="text-[#999] text-[11px] w-[100px] text-right ml-3 flex-shrink-0">
                  {entry.timestamp}
                </span>
              </div>
              <div className="flex justify-between items-start mt-1">
                <div className="flex items-start flex-1">
                  <span className="font-bold w-4 mr-2 flex-shrink-0 text-[#4b6ef3]">
                    &lt;
                  </span>
                  <span className="break-all flex-1">{entry.resp}</span>
                </div>
                <span className="text-[#722ed1] text-xs w-[100px] text-right ml-3 flex-shrink-0">
                  {entry.duration} ms
                </span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* 输入区域 */}
      <div className="bg-white border-t border-[#ececee] p-3 flex-shrink-0">
        <div className="bg-[#fafafa] rounded-2xl p-3 pb-2">
          <textarea
            ref={textareaRef}
            className="w-full text-[13px] font-mono bg-transparent border-none outline-none resize-none min-h-[32px] max-h-[120px] text-[#1a1a1a] placeholder:text-[#999]"
            placeholder="输入 APDU 指令 (Ctrl+Enter 发送)"
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
  );
}
