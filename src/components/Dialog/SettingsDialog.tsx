import { useState, useEffect, useRef } from 'react';

interface SettingsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

type SettingsTab = 'account' | 'general' | 'knowledge' | 'skills' | 'about';

export function SettingsDialog({ isOpen, onClose }: SettingsDialogProps) {
  const [activeTab, setActiveTab] = useState<SettingsTab>('general');
  const modalRef = useRef<HTMLDivElement>(null);

  // 点击外部关闭
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  // ESC 关闭
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const menuItems: { id: SettingsTab; icon: string; label: string }[] = [
    { id: 'account', icon: 'fa-regular fa-user', label: '账号' },
    { id: 'general', icon: 'fa-solid fa-gear', label: '通用' },
    { id: 'knowledge', icon: 'fa-regular fa-book', label: '知识库' },
    { id: 'skills', icon: 'fa-regular fa-lightbulb', label: '技能库' },
    { id: 'about', icon: 'fa-regular fa-circle-info', label: '关于' },
  ];

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div
        ref={modalRef}
        className="w-[780px] h-[560px] bg-white rounded-xl shadow-[0_8px_30px_rgba(0,0,0,0.08)] flex flex-col overflow-hidden"
      >
        {/* 头部 */}
        <div className="flex justify-between items-center px-6 py-4 border-b border-[#f0f0f0]">
          <h2 className="text-lg font-medium text-[#1a1a1a]">设置</h2>
          <span
            className="text-xl text-[#999] cursor-pointer hover:text-[#333] transition-colors"
            onClick={onClose}
          >
            ×
          </span>
        </div>

        {/* 主体 */}
        <div className="flex flex-1 overflow-hidden">
          {/* 左侧菜单 */}
          <div className="w-[180px] px-3 py-4 bg-white border-r border-[#f0f0f0] flex flex-col gap-1">
            {menuItems.map((item) => (
              <div
                key={item.id}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm cursor-pointer transition-colors ${
                  activeTab === item.id
                    ? 'bg-[#f3f5f9] text-[#1a1a1a] font-medium'
                    : 'text-[#4a4a4a] hover:bg-[#f7f8fa]'
                }`}
                onClick={() => setActiveTab(item.id)}
              >
                <i className={`${item.icon} text-base w-[18px] text-center ${activeTab === item.id ? 'text-[#1a1a1a]' : 'text-[#666]'}`}></i>
                <span>{item.label}</span>
              </div>
            ))}
          </div>

          {/* 右侧内容区域 */}
          <div className="flex-1 px-8 py-6 overflow-y-auto">
            {activeTab === 'general' && (
              <div className="space-y-0">
                {/* 字号大小 */}
                <div className="flex justify-between items-center py-4 border-b border-[#f5f5f5]">
                  <div className="flex items-center gap-3 text-[15px] text-[#1a1a1a]">
                    <i className="fa-regular fa-font text-lg w-6 text-center text-[#888]"></i>
                    字号大小
                  </div>
                  <div>
                    <div className="flex items-center gap-5">
                      <div className="w-[160px] h-[3px] bg-[#e5e7eb] rounded relative">
                        <div className="w-3 h-3 bg-[#1a1a1a] rounded-full absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 border-2 border-white shadow"></div>
                      </div>
                    </div>
                    <div className="flex justify-between w-[160px] text-xs text-[#999] mt-1.5">
                      <span className="cursor-pointer hover:text-[#333]">更小</span>
                      <span className="text-[#1a1a1a] font-medium">标准</span>
                      <span className="cursor-pointer hover:text-[#333]">更大</span>
                      <span className="cursor-pointer hover:text-[#333]">超大</span>
                    </div>
                  </div>
                </div>

                {/* 主题色彩 */}
                <div className="flex justify-between items-center py-4 border-b border-[#f5f5f5]">
                  <div className="flex items-center gap-3 text-[15px] text-[#1a1a1a]">
                    <i className="fa-regular fa-sun text-lg w-6 text-center text-[#888]"></i>
                    主题色彩
                  </div>
                  <div className="flex items-center gap-1.5 text-sm text-[#666] cursor-pointer hover:text-[#1a1a1a]">
                    浅色模式
                    <i className="fa-solid fa-chevron-down text-xs"></i>
                  </div>
                </div>

                {/* 启动设置 */}
                <div className="flex justify-between items-center py-4 border-b border-[#f5f5f5]">
                  <div className="flex items-center gap-3 text-[15px] text-[#1a1a1a]">
                    <i className="fa-regular fa-clock text-lg w-6 text-center text-[#888]"></i>
                    启动设置
                  </div>
                  <div className="flex items-center gap-3 text-[#666] cursor-pointer hover:text-[#1a1a1a]">
                    <i className="fa-solid fa-chevron-right text-sm"></i>
                  </div>
                </div>

                {/* 默认设置 */}
                <div className="flex justify-between items-center py-4 border-b border-[#f5f5f5]">
                  <div className="flex items-center gap-3 text-[15px] text-[#1a1a1a]">
                    <i className="fa-solid fa-sliders text-lg w-6 text-center text-[#888]"></i>
                    默认设置
                  </div>
                  <div className="flex items-center gap-3 text-[#666] cursor-pointer hover:text-[#1a1a1a]">
                    <i className="fa-solid fa-chevron-right text-sm"></i>
                  </div>
                </div>

                {/* 文件下载位置 */}
                <div className="flex justify-between items-center py-4 border-b border-[#f5f5f5]">
                  <div className="flex items-center gap-3 text-[15px] text-[#1a1a1a]">
                    <i className="fa-regular fa-folder-open text-lg w-6 text-center text-[#888]"></i>
                    文件下载位置
                  </div>
                  <div className="bg-[#f7f8fa] px-4 py-2 rounded-lg flex items-center gap-3 text-sm text-[#1a1a1a] cursor-pointer hover:bg-[#eef0f5] transition-colors">
                    <span className="text-[#888]">C:\Users\DELL\Downloads</span>
                    <i className="fa-solid fa-chevron-right text-[#666]"></i>
                  </div>
                </div>

                {/* 下载前询问 */}
                <div className="flex justify-between items-center py-4 border-b border-[#f5f5f5]">
                  <div className="flex items-center gap-3 text-[15px] text-[#1a1a1a]">
                    <i className="fa-regular fa-bell text-lg w-6 text-center text-[#888]"></i>
                    下载前询问每个文件的保存位置
                  </div>
                  <div className="w-[40px] h-[22px] bg-[#d1d5db] rounded-full relative cursor-pointer">
                    <div className="w-[18px] h-[18px] bg-white rounded-full absolute top-[2px] left-[2px] shadow"></div>
                  </div>
                </div>

                {/* 下载完成后显示 */}
                <div className="flex justify-between items-center py-4">
                  <div className="flex items-center gap-3 text-[15px] text-[#1a1a1a]">
                    <i className="fa-regular fa-folder-open text-lg w-6 text-center text-[#888]"></i>
                    下载完成后显示下载内容
                  </div>
                  <div className="w-[40px] h-[22px] bg-[#d1d5db] rounded-full relative cursor-pointer">
                    <div className="w-[18px] h-[18px] bg-white rounded-full absolute top-[2px] left-[2px] shadow"></div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'account' && (
              <div className="text-center text-[#999] py-12">
                账号设置内容
              </div>
            )}

            {activeTab === 'knowledge' && (
              <div className="text-center text-[#999] py-12">
                知识库设置内容
              </div>
            )}

            {activeTab === 'skills' && (
              <div className="text-center text-[#999] py-12">
                技能库设置内容
              </div>
            )}

            {activeTab === 'about' && (
              <div className="text-center text-[#999] py-12">
                关于信息
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}