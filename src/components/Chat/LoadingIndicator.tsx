export function LoadingIndicator() {
  return (
    <div className="flex items-center gap-2 py-3">
      <div className="flex gap-1">
        <span className="w-2 h-2 bg-[#5870f6] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
        <span className="w-2 h-2 bg-[#5870f6] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
        <span className="w-2 h-2 bg-[#5870f6] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
      <span className="text-sm text-[#999] ml-2">正在思考...</span>
    </div>
  );
}