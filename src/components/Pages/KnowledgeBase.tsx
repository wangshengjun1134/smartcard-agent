export function KnowledgeBase() {
  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* 知识库顶部栏 */}
      <header className="flex items-center justify-end px-6 h-[45px] bg-white border-b border-[#ececee] flex-shrink-0">
        <div className="flex items-center gap-2 ml-auto">
          <button
            className="circle-btn w-[28px] h-[28px] bg-[#4b6ef3]/10 text-[#4b6ef3] hover:bg-[#4b6ef3]/20"
            title="添加知识"
            aria-label="添加知识"
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
              placeholder="搜索知识库..."
              className="w-full pl-10 pr-4 py-2.5 bg-[#f7f8fa] border border-[#ececee] rounded-lg text-sm focus:outline-none focus:border-[#4b6ef3] focus:ring-1 focus:ring-[#4b6ef3]"
            />
          </div>
        </div>

        {/* 知识列表 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* 示例知识卡片 */}
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="bg-[#f7f8fa] rounded-lg p-4 hover:bg-[#ececee] transition-colors cursor-pointer group"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="w-10 h-10 rounded-lg bg-[#4b6ef3]/10 flex items-center justify-center">
                  <svg className="w-5 h-5 text-[#4b6ef3]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <button className="opacity-0 group-hover:opacity-100 p-1 hover:bg-white rounded transition-opacity">
                  <svg className="w-4 h-4 text-[#999]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                  </svg>
                </button>
              </div>
              <h3 className="font-medium text-[#1a1a1a] mb-1">智能卡规范文档 {i}</h3>
              <p className="text-xs text-[#999] line-clamp-2">
                ISO/IEC 7816 智能卡国际标准文档，包含卡片物理特性、电气接口、传输协议等规范内容。
              </p>
              <div className="mt-3 flex items-center gap-2 text-xs text-[#999]">
                <span>12 篇文档</span>
                <span>·</span>
                <span>更新于 3 天前</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}