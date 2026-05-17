export function SkillsBase() {
  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* 技能库顶部栏 */}
      <header className="flex items-center justify-end px-6 h-[45px] bg-white border-b border-[#ececee] flex-shrink-0">
        <div className="flex items-center gap-2 ml-auto">
          <button
            className="circle-btn w-[28px] h-[28px] bg-[#10b981]/10 text-[#10b981] hover:bg-[#10b981]/20"
            title="创建技能"
            aria-label="创建技能"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>
      </header>

      {/* 内容区域 */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* 搜索栏 */}
        <div className="mb-6">
          <div className="relative">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#999]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="搜索技能..."
              className="w-full pl-10 pr-4 py-2.5 bg-[#f7f8fa] border border-[#ececee] rounded-lg text-sm focus:outline-none focus:border-[#4b6ef3] focus:ring-1 focus:ring-[#4b6ef3]"
            />
          </div>
        </div>

        {/* 技能列表 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* 示例技能卡片 */}
          {[
            { name: 'APDU 命令解析', desc: '解析和构建 APDU 命令，支持各类智能卡指令格式' },
            { name: '卡片识别流程', desc: '自动识别智能卡类型，支持多种卡片协议' },
            { name: '数据导出工具', desc: '将卡片数据导出为多种格式，支持批量处理' },
            { name: '安全验证模块', desc: 'PIN 码验证、密钥管理等安全相关功能' },
            { name: '文件系统浏览', desc: '浏览和管理智能卡文件系统结构' },
            { name: '交易记录分析', desc: '解析和分析智能卡交易记录数据' },
          ].map((skill, i) => (
            <div
              key={i}
              className="bg-[#f7f8fa] rounded-lg p-4 hover:bg-[#ececee] transition-colors cursor-pointer group"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="w-10 h-10 rounded-lg bg-[#10b981]/10 flex items-center justify-center">
                  <svg className="w-5 h-5 text-[#10b981]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <button className="opacity-0 group-hover:opacity-100 p-1 hover:bg-white rounded transition-opacity">
                  <svg className="w-4 h-4 text-[#999]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                  </svg>
                </button>
              </div>
              <h3 className="font-medium text-[#1a1a1a] mb-1">{skill.name}</h3>
              <p className="text-xs text-[#999] line-clamp-2">
                {skill.desc}
              </p>
              <div className="mt-3 flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs text-[#999]">
                  <span className="px-2 py-0.5 bg-[#4b6ef3]/10 text-[#4b6ef3] rounded">自动化</span>
                </div>
                <div className="flex items-center gap-1 text-xs text-[#999]">
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                  </svg>
                  <span>{100 + i * 23}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}