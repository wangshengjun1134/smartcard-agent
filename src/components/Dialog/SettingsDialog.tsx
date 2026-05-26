import { useState, useEffect, useRef } from 'react';
import { getApiUrl, API_CONFIG, DEFAULT_HEADERS } from '../../config/api';

interface SettingsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

type SettingsTab = 'account' | 'general' | 'knowledge' | 'skills' | 'about';

// 模型提供商配置
type Provider = 'coding_plan' | 'openai' | 'deepseek' | 'anthropic';

interface AccountSettings {
  provider: Provider;
  baseUrl: string;
  apiKey: string;
  model: string;
}

// 提供商默认配置
const PROVIDER_CONFIG: Record<Provider, { name: string; defaultUrl: string; models: string[] }> = {
  coding_plan: {
    name: '阿里 Coding Plan',
    defaultUrl: 'https://coding.dashscope.aliyuncs.com/v1',
    models: [
      'qwen3.6-plus',
      'kimi-k2.5',
      'glm-5',
      'MiniMax-M2.5',
      'qwen3.5-plus',
      'qwen3-max-2026-01-23',
      'qwen3-coder-next',
      'qwen3-coder-plus',
      'glm-4.7',
    ],
  },
  openai: {
    name: 'OpenAI',
    defaultUrl: 'https://api.openai.com/v1',
    models: [],
  },
  deepseek: {
    name: 'DeepSeek',
    defaultUrl: 'https://api.deepseek.com/v1',
    models: [],
  },
  anthropic: {
    name: 'Anthropic',
    defaultUrl: 'https://api.anthropic.com/v1',
    models: [],
  },
};

// 支持图片理解的模型
const VISION_MODELS = ['qwen3.6-plus', 'kimi-k2.5', 'qwen3.5-plus'];

// API 响应类型
interface ApiConfigResponse {
  id: string;
  provider: string;
  base_url: string;
  api_key: string;
  model: string | null;
}

interface TestConnectionResponse {
  success: boolean;
  message: string;
  latency_ms: number | null;
}

export function SettingsDialog({ isOpen, onClose }: SettingsDialogProps) {
  const [activeTab, setActiveTab] = useState<SettingsTab>('general');
  const modalRef = useRef<HTMLDivElement>(null);

  // 账号设置状态
  const [accountSettings, setAccountSettings] = useState<AccountSettings>({
    provider: 'coding_plan',
    baseUrl: '',
    apiKey: '',
    model: 'qwen3.5-plus',
  });

  // 操作状态
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<TestConnectionResponse | null>(null);
  const [isLoadingConfig, setIsLoadingConfig] = useState(false);

  // 下拉框状态
  const [showProviderDropdown, setShowProviderDropdown] = useState(false);

  // 加载已保存的配置
  useEffect(() => {
    if (isOpen && activeTab === 'account') {
      loadConfig();
    }
  }, [isOpen, activeTab]);

  const loadConfig = async () => {
    setIsLoadingConfig(true);
    try {
      const response = await fetch(getApiUrl(API_CONFIG.endpoints.config.getApi), {
        headers: DEFAULT_HEADERS,
      });
      if (response.ok) {
        const data: ApiConfigResponse | null = await response.json();
        if (data) {
          setAccountSettings({
            provider: data.provider as Provider,
            baseUrl: data.base_url,
            apiKey: data.api_key, // 显示脱敏后的 API key
            model: data.model || '',
          });
        }
      }
    } catch (error) {
      console.error('Failed to load config:', error);
    } finally {
      setIsLoadingConfig(false);
    }
  };

  // 保存配置
  const handleSaveConfig = async () => {
    if (!accountSettings.baseUrl || !accountSettings.apiKey) {
      alert('请填写 Base URL 和 API Key');
      return;
    }

    setIsSaving(true);
    try {
      const response = await fetch(getApiUrl(API_CONFIG.endpoints.config.saveApi), {
        method: 'POST',
        headers: {
          ...DEFAULT_HEADERS,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          provider: accountSettings.provider,
          base_url: accountSettings.baseUrl,
          api_key: accountSettings.apiKey,
          model: accountSettings.model,
        }),
      });

      if (response.ok) {
        alert('配置已保存');
      } else {
        alert('保存失败');
      }
    } catch (error) {
      console.error('Failed to save config:', error);
      alert('保存失败');
    } finally {
      setIsSaving(false);
    }
  };

  // 测试连接
  const handleTestConnection = async () => {
    if (!accountSettings.baseUrl || !accountSettings.apiKey) {
      setTestResult({ success: false, message: '请填写 Base URL 和 API Key', latency_ms: null });
      return;
    }

    setIsTesting(true);
    setTestResult(null);
    try {
      const response = await fetch(getApiUrl(API_CONFIG.endpoints.config.testApi), {
        method: 'POST',
        headers: {
          ...DEFAULT_HEADERS,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          provider: accountSettings.provider,
          base_url: accountSettings.baseUrl,
          api_key: accountSettings.apiKey,
          model: accountSettings.model,
        }),
      });

      if (response.ok) {
        const data: TestConnectionResponse = await response.json();
        setTestResult(data);
      } else {
        setTestResult({ success: false, message: '测试请求失败', latency_ms: null });
      }
    } catch (error) {
      console.error('Failed to test connection:', error);
      setTestResult({ success: false, message: '网络错误', latency_ms: null });
    } finally {
      setIsTesting(false);
    }
  };

  // 切换提供商时更新默认URL和清空模型选择
  const handleProviderChange = (provider: Provider) => {
    const config = PROVIDER_CONFIG[provider];
    setAccountSettings(prev => ({
      ...prev,
      provider,
      baseUrl: prev.baseUrl || config.defaultUrl,
      model: config.models.length > 0 ? config.models[0] : '',
    }));
    setTestResult(null); // 清除测试结果
  };

  // 点击外部关闭
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
        onClose();
        setShowProviderDropdown(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  // 点击内部关闭下拉框（非下拉框区域）
  useEffect(() => {
    const handleClickInside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (
        showProviderDropdown &&
        !target.closest('.provider-dropdown-trigger') &&
        !target.closest('.provider-dropdown-menu')
      ) {
        setShowProviderDropdown(false);
      }
    };

    if (isOpen && showProviderDropdown) {
      document.addEventListener('mousedown', handleClickInside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickInside);
    };
  }, [isOpen, showProviderDropdown]);

  // ESC 关闭
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
        setShowProviderDropdown(false);
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
        className="w-[780px] h-[560px] bg-white dark:bg-[#222222] rounded-xl shadow-[0_8px_30px_rgba(0,0,0,0.08)] dark:shadow-[0_8px_30px_rgba(0,0,0,0.3)] flex flex-col overflow-hidden"
      >
        {/* 头部 */}
        <div className="flex justify-between items-center px-6 py-4 border-b border-[#f0f0f0] dark:border-[#333333]">
          <h2 className="text-lg font-medium text-[#1a1a1a] dark:text-white">设置</h2>
          <span
            className="text-xl text-[#999] dark:text-[#808080] cursor-pointer hover:text-[#333] dark:hover:text-white transition-colors"
            onClick={onClose}
          >
            ×
          </span>
        </div>

        {/* 主体 */}
        <div className="flex flex-1 overflow-hidden">
          {/* 左侧菜单 */}
          <div className="w-[180px] px-3 py-4 bg-white dark:bg-[#222222] border-r border-[#f0f0f0] dark:border-[#333333] flex flex-col gap-1">
            {menuItems.map((item) => (
              <div
                key={item.id}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm cursor-pointer transition-colors ${
                  activeTab === item.id
                    ? 'bg-[#f3f5f9] dark:bg-[#333333] text-[#1a1a1a] dark:text-white font-medium'
                    : 'text-[#4a4a4a] dark:text-[#b3b3b3] hover:bg-[#f7f8fa] dark:hover:bg-[#2d2d2d]'
                }`}
                onClick={() => setActiveTab(item.id)}
              >
                <i className={`${item.icon} text-base w-[18px] text-center ${activeTab === item.id ? 'text-[#1a1a1a] dark:text-white' : 'text-[#666] dark:text-[#a0a0a0]'}`}></i>
                <span>{item.label}</span>
              </div>
            ))}
          </div>

          {/* 右侧内容区域 */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="flex-1 px-8 py-6 overflow-y-auto">
              {activeTab === 'general' && (
                <div className="space-y-0">
                  {/* 字号大小 */}
                  <div className="flex justify-between items-center py-4 border-b border-[#f5f5f5] dark:border-[#333333]">
                    <div className="flex items-center gap-3 text-[15px] text-[#1a1a1a] dark:text-white">
                      <i className="fa-regular fa-font text-lg w-6 text-center text-[#888] dark:text-[#808080]"></i>
                      字号大小
                    </div>
                    <div>
                      <div className="flex items-center gap-5">
                        <div className="w-[160px] h-[3px] bg-[#e5e7eb] dark:bg-[#404040] rounded relative">
                          <div className="w-3 h-3 bg-[#1a1a1a] dark:bg-white rounded-full absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 border-2 border-white dark:border-[#222222] shadow"></div>
                        </div>
                      </div>
                      <div className="flex justify-between w-[160px] text-xs text-[#999] dark:text-[#808080] mt-1.5">
                        <span className="cursor-pointer hover:text-[#333] dark:hover:text-white">更小</span>
                        <span className="text-[#1a1a1a] dark:text-white font-medium">标准</span>
                        <span className="cursor-pointer hover:text-[#333] dark:hover:text-white">更大</span>
                        <span className="cursor-pointer hover:text-[#333] dark:hover:text-white">超大</span>
                      </div>
                    </div>
                  </div>

                  {/* 主题色彩 */}
                  <div className="flex justify-between items-center py-4 border-b border-[#f5f5f5] dark:border-[#333333]">
                    <div className="flex items-center gap-3 text-[15px] text-[#1a1a1a] dark:text-white">
                      <i className="fa-regular fa-sun text-lg w-6 text-center text-[#888] dark:text-[#808080]"></i>
                      主题色彩
                    </div>
                    <div className="flex items-center gap-1.5 text-sm text-[#666] dark:text-[#a0a0a0] cursor-pointer hover:text-[#1a1a1a] dark:hover:text-white">
                      浅色模式
                      <i className="fa-solid fa-chevron-down text-xs"></i>
                    </div>
                  </div>

                  {/* 启动设置 */}
                  <div className="flex justify-between items-center py-4 border-b border-[#f5f5f5] dark:border-[#333333]">
                    <div className="flex items-center gap-3 text-[15px] text-[#1a1a1a] dark:text-white">
                      <i className="fa-regular fa-clock text-lg w-6 text-center text-[#888] dark:text-[#808080]"></i>
                      启动设置
                    </div>
                    <div className="flex items-center gap-3 text-[#666] dark:text-[#a0a0a0] cursor-pointer hover:text-[#1a1a1a] dark:hover:text-white">
                      <i className="fa-solid fa-chevron-right text-sm"></i>
                    </div>
                  </div>

                  {/* 默认设置 */}
                  <div className="flex justify-between items-center py-4 border-b border-[#f5f5f5] dark:border-[#333333]">
                    <div className="flex items-center gap-3 text-[15px] text-[#1a1a1a] dark:text-white">
                      <i className="fa-solid fa-sliders text-lg w-6 text-center text-[#888] dark:text-[#808080]"></i>
                      默认设置
                    </div>
                    <div className="flex items-center gap-3 text-[#666] dark:text-[#a0a0a0] cursor-pointer hover:text-[#1a1a1a] dark:hover:text-white">
                      <i className="fa-solid fa-chevron-right text-sm"></i>
                    </div>
                  </div>

                  {/* 文件下载位置 */}
                  <div className="flex justify-between items-center py-4 border-b border-[#f5f5f5] dark:border-[#333333]">
                    <div className="flex items-center gap-3 text-[15px] text-[#1a1a1a] dark:text-white">
                      <i className="fa-regular fa-folder-open text-lg w-6 text-center text-[#888] dark:text-[#808080]"></i>
                      文件下载位置
                    </div>
                    <div className="bg-[#f7f8fa] dark:bg-[#333333] px-4 py-2 rounded-lg flex items-center gap-3 text-sm text-[#1a1a1a] dark:text-white cursor-pointer hover:bg-[#eef0f5] dark:hover:bg-[#404040] transition-colors">
                      <span className="text-[#888] dark:text-[#808080]">C:\Users\DELL\Downloads</span>
                      <i className="fa-solid fa-chevron-right text-[#666] dark:text-[#a0a0a0]"></i>
                    </div>
                  </div>

                  {/* 下载前询问 */}
                  <div className="flex justify-between items-center py-4 border-b border-[#f5f5f5] dark:border-[#333333]">
                    <div className="flex items-center gap-3 text-[15px] text-[#1a1a1a] dark:text-white">
                      <i className="fa-regular fa-bell text-lg w-6 text-center text-[#888] dark:text-[#808080]"></i>
                      下载前询问每个文件的保存位置
                    </div>
                    <div className="w-[40px] h-[22px] bg-[#d1d5db] dark:bg-[#404040] rounded-full relative cursor-pointer">
                      <div className="w-[18px] h-[18px] bg-white rounded-full absolute top-[2px] left-[2px] shadow"></div>
                    </div>
                  </div>

                  {/* 下载完成后显示 */}
                  <div className="flex justify-between items-center py-4">
                    <div className="flex items-center gap-3 text-[15px] text-[#1a1a1a] dark:text-white">
                      <i className="fa-regular fa-folder-open text-lg w-6 text-center text-[#888] dark:text-[#808080]"></i>
                      下载完成后显示下载内容
                    </div>
                    <div className="w-[40px] h-[22px] bg-[#d1d5db] dark:bg-[#404040] rounded-full relative cursor-pointer">
                      <div className="w-[18px] h-[18px] bg-white rounded-full absolute top-[2px] left-[2px] shadow"></div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'account' && (
                <div className="space-y-0">
                  {isLoadingConfig && (
                    <div className="text-center text-[#999] py-4">加载配置中...</div>
                  )}

                  {/* 模型提供商 */}
                  <div className="flex justify-between items-center py-4 border-b border-[#f5f5f5] dark:border-[#333333] relative">
                    <div className="flex items-center gap-3 text-[15px] text-[#1a1a1a] dark:text-white">
                      <i className="fa-solid fa-cloud text-lg w-6 text-center text-[#888] dark:text-[#808080]"></i>
                      模型提供商
                    </div>
                    <div className="relative">
                      <div
                        className="provider-dropdown-trigger flex items-center gap-1.5 text-sm text-[#666] dark:text-[#a0a0a0] cursor-pointer hover:text-[#1a1a1a] dark:hover:text-white bg-[#f7f8fa] dark:bg-[#333333] px-3 py-1.5 rounded-lg min-w-[160px] justify-between"
                        onClick={() => setShowProviderDropdown(!showProviderDropdown)}
                      >
                        <span>{PROVIDER_CONFIG[accountSettings.provider].name}</span>
                        <i className={`fa-solid fa-chevron-down text-xs transition-transform ${showProviderDropdown ? 'rotate-180' : ''}`}></i>
                      </div>
                      {showProviderDropdown && (
                        <div className="provider-dropdown-menu absolute right-0 top-full mt-1 bg-white dark:bg-[#333333] rounded-lg shadow-lg border border-[#e5e7eb] dark:border-[#404040] py-1 z-10 min-w-[160px]">
                          {(Object.keys(PROVIDER_CONFIG) as Provider[]).map((p) => (
                            <div
                              key={p}
                              className={`px-4 py-2 text-sm cursor-pointer hover:bg-[#f7f8fa] dark:hover:bg-[#404040] ${
                                accountSettings.provider === p
                                  ? 'text-[#4b6ef3] bg-[#f7f8fa] dark:bg-[#404040]'
                                  : 'text-[#1a1a1a] dark:text-white'
                              }`}
                              onClick={() => {
                                handleProviderChange(p);
                                setShowProviderDropdown(false);
                              }}
                            >
                              {PROVIDER_CONFIG[p].name}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* 模型选择 - 仅阿里 Coding Plan 显示 */}
                  {accountSettings.provider === 'coding_plan' && (
                    <div className="flex justify-between items-center py-4 border-b border-[#f5f5f5] dark:border-[#333333]">
                      <div className="flex items-center gap-3 text-[15px] text-[#1a1a1a] dark:text-white">
                        <i className="fa-solid fa-microchip text-lg w-6 text-center text-[#888] dark:text-[#808080]"></i>
                        模型选择
                      </div>
                      <select
                        value={accountSettings.model}
                        onChange={(e) => setAccountSettings(prev => ({ ...prev, model: e.target.value }))}
                        className="bg-[#f7f8fa] dark:bg-[#333333] px-3 py-1.5 rounded-lg text-sm text-[#1a1a1a] dark:text-white border-none outline-none cursor-pointer min-w-[160px]"
                      >
                        {PROVIDER_CONFIG.coding_plan.models.map((m) => (
                          <option key={m} value={m}>
                            {m}
                            {VISION_MODELS.includes(m) && ' (支持图片)'}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  {/* Base URL */}
                  <div className="flex justify-between items-center py-4 border-b border-[#f5f5f5] dark:border-[#333333]">
                    <div className="flex items-center gap-3 text-[15px] text-[#1a1a1a] dark:text-white">
                      <i className="fa-solid fa-link text-lg w-6 text-center text-[#888] dark:text-[#808080]"></i>
                      Base URL
                    </div>
                    <input
                      type="text"
                      value={accountSettings.baseUrl}
                      onChange={(e) => setAccountSettings(prev => ({ ...prev, baseUrl: e.target.value }))}
                      placeholder={PROVIDER_CONFIG[accountSettings.provider].defaultUrl}
                      className="bg-[#f7f8fa] dark:bg-[#333333] px-3 py-1.5 rounded-lg text-sm text-[#1a1a1a] dark:text-white border-none outline-none min-w-[200px]"
                    />
                  </div>

                  {/* API Key */}
                  <div className="flex justify-between items-center py-4 border-b border-[#f5f5f5] dark:border-[#333333]">
                    <div className="flex items-center gap-3 text-[15px] text-[#1a1a1a] dark:text-white">
                      <i className="fa-solid fa-key text-lg w-6 text-center text-[#888] dark:text-[#808080]"></i>
                      API Key
                    </div>
                    <input
                      type="password"
                      value={accountSettings.apiKey}
                      onChange={(e) => setAccountSettings(prev => ({ ...prev, apiKey: e.target.value }))}
                      placeholder="sk-xxx"
                      className="bg-[#f7f8fa] dark:bg-[#333333] px-3 py-1.5 rounded-lg text-sm text-[#1a1a1a] dark:text-white border-none outline-none min-w-[200px]"
                    />
                  </div>

                  {/* 测试结果 */}
                  {testResult && (
                    <div className={`mt-4 p-3 rounded-lg text-sm ${
                      testResult.success
                        ? 'bg-[#e8f5e9] dark:bg-[#2d4a2e] text-[#2e7d32] dark:text-[#81c784]'
                        : 'bg-[#ffebee] dark:bg-[#4a2d2d] text-[#c62828] dark:text-[#ef9a9a]'
                    }`}>
                      <div className="flex items-center gap-2">
                        <i className={`fa-solid ${testResult.success ? 'fa-check-circle' : 'fa-times-circle'}`}></i>
                        <span>{testResult.message}</span>
                        {testResult.latency_ms && (
                          <span className="text-xs opacity-70">({testResult.latency_ms}ms)</span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* 提示信息 */}
                  {accountSettings.provider === 'coding_plan' && (
                    <div className="mt-4 p-4 bg-[#f7f8fa] dark:bg-[#333333] rounded-lg text-sm text-[#666] dark:text-[#a0a0a0]">
                      <div className="flex items-center gap-2 mb-2">
                        <i className="fa-solid fa-info-circle text-[#4b6ef3]"></i>
                        <span className="text-[#1a1a1a] dark:text-white font-medium">阿里 Coding Plan API</span>
                      </div>
                      <p className="leading-relaxed">
                        Coding Plan API 专用密钥格式为 sk-sp-xxx，支持多种大模型调用。
                        带"支持图片"标识的模型可处理图片输入。
                      </p>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'knowledge' && (
                <div className="text-center text-[#999] dark:text-[#808080] py-12">
                  知识库设置内容
                </div>
              )}

              {activeTab === 'skills' && (
                <div className="text-center text-[#999] dark:text-[#808080] py-12">
                  技能库设置内容
                </div>
              )}

              {activeTab === 'about' && (
                <div className="text-center text-[#999] dark:text-[#808080] py-12">
                  关于信息
                </div>
              )}
            </div>

            {/* 底部按钮区域 - 仅账号页面显示 */}
            {activeTab === 'account' && (
              <div className="px-8 py-4 border-t border-[#f5f5f5] dark:border-[#333333] flex justify-end gap-3">
                <button
                  onClick={handleTestConnection}
                  disabled={isTesting}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isTesting
                      ? 'bg-[#e5e7eb] dark:bg-[#404040] text-[#999] dark:text-[#808080] cursor-not-allowed'
                      : 'bg-[#f7f8fa] dark:bg-[#333333] text-[#1a1a1a] dark:text-white hover:bg-[#eef0f5] dark:hover:bg-[#404040]'
                  }`}
                >
                  {isTesting ? (
                    <span className="flex items-center gap-2">
                      <i className="fa-solid fa-spinner fa-spin"></i>
                      测试中...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <i className="fa-solid fa-plug"></i>
                      测试连接
                    </span>
                  )}
                </button>
                <button
                  onClick={handleSaveConfig}
                  disabled={isSaving}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isSaving
                      ? 'bg-[#4b6ef3]/70 text-white cursor-not-allowed'
                      : 'bg-[#4b6ef3] text-white hover:bg-[#3b5ed9]'
                  }`}
                >
                  {isSaving ? (
                    <span className="flex items-center gap-2">
                      <i className="fa-solid fa-spinner fa-spin"></i>
                      保存中...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <i className="fa-solid fa-save"></i>
                      保存配置
                    </span>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}