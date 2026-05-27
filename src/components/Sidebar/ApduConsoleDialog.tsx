import React, { useState, useCallback, useRef, useEffect } from 'react';

// 全局类型声明
declare global {
  interface Window {
    apduConsole?: {
      log: (sendApdu: string, respApdu: string, duration: number) => void;
    };
  }
}

interface ApduEntry {
  id: number;
  send: string;
  resp: string;
  duration: number;
  time: string;
}

interface ApduConsoleDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

const MAX_ENTRIES = 50;

function nowTime(): string {
  const d = new Date();
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}.${d.getMilliseconds().toString().padStart(3, '0')}`;
}

function formatApdu(hexStr: string): string {
  const cleaned = hexStr.replace(/\s/g, '');
  const pairs = cleaned.match(/.{1,2}/g) || [];
  return pairs.join(' ');
}

function generateHex256(): string {
  let hex = '';
  for (let i = 0; i < 256; i++) {
    hex += i.toString(16).padStart(2, '0').toUpperCase();
  }
  return hex;
}

function generateRandomResponse(sendApdu: string): string {
  const cleaned = sendApdu.replace(/\s/g, '');
  const len = Math.min(cleaned.length / 2, 20);
  let resp = '';
  for (let i = 0; i < len; i++) {
    resp += Math.floor(Math.random() * 256).toString(16).padStart(2, '0').toUpperCase();
  }
  return resp + ' 90 00';
}

// 初始示例数据
const hex256 = generateHex256();
const initialSampleData: ApduEntry[] = [
  { id: 1, send: '00 A4 04 00 0E 32 50 41 59 2E 53 59 53 2E 44 44 46 30 31', resp: '6F 2C 84 0E 32 50 41 59 2E 53 59 53 2E 44 44 46 30 31 A5 1A 88 01 01 5F 2D 04 7A 68 2D 43 4E 9F 11 01 01 90 00', duration: 127, time: '14:32:05.127' },
  { id: 2, send: '00 B0 00 00 10', resp: '00 11 22 33 44 55 66 77 88 99 AA BB CC DD EE FF 90 00', duration: 45, time: '14:32:06.045' },
  { id: 3, send: '00 CA 9F 17 00', resp: '9F 17 01 02 90 00', duration: 32, time: '14:32:07.032' },
  { id: 4, send: '80 50 00 00 08 11 22 33 44 55 66 77 88', resp: '90 00', duration: 18, time: '14:32:08.018' },
  { id: 5, send: hex256, resp: hex256 + ' 90 00', duration: 256, time: '14:32:09.256' },
];

const ApduConsoleDialog: React.FC<ApduConsoleDialogProps> = ({ isOpen, onClose }) => {
  const [entries, setEntries] = useState<ApduEntry[]>(initialSampleData);
  const [inputValue, setInputValue] = useState('');
  const [nextId, setNextId] = useState(6);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const addEntry = useCallback((sendApdu: string, respApdu: string, duration: number) => {
    const newEntry: ApduEntry = {
      id: nextId,
      send: sendApdu,
      resp: respApdu,
      duration,
      time: nowTime(),
    };
    setNextId(nextId + 1);
    setEntries(prev => {
      const updated = [newEntry, ...prev];
      return updated.slice(0, MAX_ENTRIES);
    });
  }, [nextId]);

  const sendManualApdu = useCallback(() => {
    const trimmed = inputValue.trim();
    if (!trimmed) return;

    const lines = trimmed.split('\n').filter(line => line.trim());
    
    lines.forEach(line => {
      const sendApdu = line.trim();
      const respApdu = generateRandomResponse(sendApdu);
      const duration = Math.floor(Math.random() * 200) + 15;
      addEntry(sendApdu, respApdu, duration);
    });

    setInputValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [inputValue, addEntry]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      sendManualApdu();
    }
  }, [sendManualApdu]);

  const handleInputHeight = useCallback(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  }, []);

  // 暴露全局方法供外部调用
  useEffect(() => {
    window.apduConsole = {
      log: (sendApdu: string, respApdu: string, duration: number) => {
        addEntry(sendApdu, respApdu, duration);
      },
    };
    return () => {
      delete window.apduConsole;
    };
  }, [addEntry]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div 
        className="w-[600px] max-w-[90vw] bg-white rounded-lg shadow-xl flex flex-col"
        style={{ height: '70vh' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200">
          <span className="font-bold text-blue-500">APDU 实时打印控制台</span>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Console */}
        <div className="flex-1 overflow-y-auto p-3 bg-white">
          {entries.length === 0 ? (
            <div className="text-center text-gray-400 py-10 italic font-mono text-sm">
              等待 APDU 指令...
            </div>
          ) : (
            entries.map(entry => (
              <div 
                key={entry.id}
                className="bg-gray-50 border-l-2 border-blue-500 mb-1 px-3 py-1.5 rounded-r"
              >
                {/* Send line */}
                <div className="flex justify-between items-start mb-0.5">
                  <div className="flex items-start flex-1">
                    <span className="font-bold mr-2 text-orange-500 w-4 text-sm">&gt;</span>
                    <span className="font-mono text-sm break-all flex-1">{formatApdu(entry.send)}</span>
                  </div>
                  <span className="text-gray-400 text-xs w-[100px] text-right ml-3 pt-0.5 shrink-0">{entry.time}</span>
                </div>
                {/* Response line */}
                <div className="flex justify-between items-start">
                  <div className="flex items-start flex-1">
                    <span className="font-bold mr-2 text-blue-500 w-4 text-sm">&lt;</span>
                    <span className="font-mono text-sm break-all flex-1">{formatApdu(entry.resp)}</span>
                  </div>
                  <span className="text-purple-600 text-xs w-[100px] text-right ml-3 pt-0.5 shrink-0">{entry.duration} ms</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Input area */}
        <div className="flex gap-2 items-end px-4 py-2 bg-gray-50 border-t border-gray-200">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => {
              setInputValue(e.target.value);
              handleInputHeight();
            }}
            onKeyDown={handleKeyDown}
            placeholder="输入 APDU 指令 (支持多行，Ctrl+Enter 发送)"
            className="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm font-mono resize-none min-h-[36px] max-h-[120px] focus:border-blue-500 focus:outline-none"
            rows={1}
          />
          <button
            onClick={sendManualApdu}
            className="bg-blue-500 text-white px-4 py-1.5 rounded text-sm font-mono hover:bg-blue-400 transition-colors h-[36px] shrink-0"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  );
};

export default ApduConsoleDialog;