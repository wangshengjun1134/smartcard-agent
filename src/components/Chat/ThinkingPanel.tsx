import { useState } from 'react';

interface RoutingDecision {
  type: 'routing';
  from: string;
  to: string;
  reason: string;
  confidence?: number;
}

interface ThinkingPanelProps {
  steps: string[];
  routing: RoutingDecision | null;
  collapsed?: boolean;
}

export function ThinkingPanel({ steps, routing, collapsed = false }: ThinkingPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(collapsed);

  if (steps.length === 0 && !routing) {
    return null;
  }

  return (
    <div className="thinking-panel bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
      {/* Header - always visible */}
      <div
        className="flex items-center justify-between px-4 py-2 cursor-pointer hover:bg-gray-100 transition-colors"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <div className="flex items-center gap-2">
          <span className="text-lg">🧠</span>
          <span className="font-medium text-gray-700">思考过程</span>
          {steps.length > 0 && (
            <span className="text-xs text-gray-400 ml-2">
              ({steps.length} 步)
            </span>
          )}
        </div>
        <button className="text-gray-400 hover:text-gray-600 transition-colors">
          {isCollapsed ? '▼' : '▲'}
        </button>
      </div>

      {/* Content - collapsible */}
      {!isCollapsed && (
        <div className="px-4 py-3 border-t border-gray-200">
          {/* Thinking steps */}
          {steps.length > 0 && (
            <div className="space-y-1.5 mb-3">
              {steps.map((step, index) => (
                <div
                  key={index}
                  className="flex items-start gap-2 text-sm text-gray-600"
                >
                  <span className="text-gray-400 font-mono shrink-0">
                    {index + 1}.
                  </span>
                  <span className="flex-1">{step}</span>
                </div>
              ))}
            </div>
          )}

          {/* Routing decision */}
          {routing && (
            <div className="mt-3 pt-3 border-t border-gray-100">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">📍</span>
                <span className="font-medium text-gray-700">路由决策</span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <div className="flex items-center gap-1">
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                    {routing.from}
                  </span>
                  <span className="text-gray-400">→</span>
                  <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs font-medium">
                    {routing.to}
                  </span>
                </div>
                {routing.confidence && (
                  <span className="text-gray-400 text-xs">
                    置信度: {routing.confidence.toFixed(2)}
                  </span>
                )}
              </div>
              {routing.reason && (
                <div className="mt-2 text-sm text-gray-500">
                  {routing.reason}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}