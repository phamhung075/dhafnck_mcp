/**
 * Context Node Component
 * Individual node in the hierarchical context tree with health indicators
 */
import React, { useState, useRef } from 'react';
import { 
  ContextNodeProps, 
  HierarchicalContext, 
  ContextHealthStatus 
} from '../types/context-tree';

// Health status indicator component
function HealthIndicator({ status, score, issues }: { 
  status: ContextHealthStatus['status'];
  score: number;
  issues: ContextHealthStatus['issues'];
}) {
  const getStatusColor = () => {
    switch (status) {
      case 'healthy': return 'bg-green-500';
      case 'warning': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      case 'stale': return 'bg-gray-400';
      default: return 'bg-gray-300';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'healthy': return '✓';
      case 'warning': return '⚠';
      case 'error': return '✗';
      case 'stale': return '⟳';
      default: return '?';
    }
  };

  return (
    <div className="flex items-center gap-1">
      <div 
        className={`w-3 h-3 rounded-full ${getStatusColor()} flex items-center justify-center text-white text-xs`}
        title={`Status: ${status} | Score: ${score} | Issues: ${issues.length}`}
      >
        <span className="text-[8px]">{getStatusIcon()}</span>
      </div>
      <span className="text-xs text-gray-500">{score}</span>
      {issues.length > 0 && (
        <span className="text-xs text-red-500" title={`${issues.length} issues`}>
          ({issues.length})
        </span>
      )}
    </div>
  );
}

// Context level badge component
function LevelBadge({ level }: { level: 'global' | 'project' | 'task' }) {
  const getLevelConfig = () => {
    switch (level) {
      case 'global':
        return { bg: 'bg-emerald-100', text: 'text-emerald-800', label: 'G' };
      case 'project':
        return { bg: 'bg-blue-100', text: 'text-blue-800', label: 'P' };
      case 'task':
        return { bg: 'bg-amber-100', text: 'text-amber-800', label: 'T' };
    }
  };

  const config = getLevelConfig();
  return (
    <div className={`w-6 h-6 rounded ${config.bg} ${config.text} flex items-center justify-center text-xs font-medium`}>
      {config.label}
    </div>
  );
}

// Action buttons component
function ActionButtons({ 
  onValidate, 
  onResolve, 
  onDelegate,
  disabled = false 
}: {
  onValidate: () => void;
  onResolve: () => void;
  onDelegate: () => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
      <button
        onClick={(e) => { e.stopPropagation(); onValidate(); }}
        disabled={disabled}
        className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50"
        title="Validate inheritance"
      >
        ✓
      </button>
      <button
        onClick={(e) => { e.stopPropagation(); onResolve(); }}
        disabled={disabled}
        className="px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 rounded disabled:opacity-50"
        title="Resolve context"
      >
        ⟳
      </button>
      <button
        onClick={(e) => { e.stopPropagation(); onDelegate(); }}
        disabled={disabled}
        className="px-2 py-1 text-xs bg-green-100 hover:bg-green-200 rounded disabled:opacity-50"
        title="Delegate to parent"
      >
        ↑
      </button>
    </div>
  );
}

// Context details component
function ContextDetails({ context }: { context: HierarchicalContext }) {
  const { data } = context;
  
  return (
    <div className="text-xs text-gray-600 mt-1 space-y-1">
      {data.description && (
        <div className="truncate" title={data.description}>
          {data.description}
        </div>
      )}
      <div className="flex gap-2 text-[10px]">
        {data.status && (
          <span className="px-1 py-0.5 bg-gray-100 rounded">
            {data.status}
          </span>
        )}
        {data.priority && (
          <span className="px-1 py-0.5 bg-gray-100 rounded">
            {data.priority}
          </span>
        )}
        {data.assignees && data.assignees.length > 0 && (
          <span className="px-1 py-0.5 bg-gray-100 rounded">
            👥 {data.assignees.length}
          </span>
        )}
      </div>
      {data.labels && data.labels.length > 0 && (
        <div className="flex gap-1 flex-wrap">
          {data.labels.slice(0, 3).map((label: string, index: number) => (
            <span key={index} className="px-1 py-0.5 text-[10px] bg-blue-100 text-blue-700 rounded">
              {label}
            </span>
          ))}
          {data.labels.length > 3 && (
            <span className="text-[10px] text-gray-500">
              +{data.labels.length - 3}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

export function ContextNode({
  context,
  level,
  isSelected,
  isExpanded,
  children = [],
  healthStatus,
  onSelect,
  onToggleExpand,
  onDelegate,
  onValidate,
  onResolve,
  enableDragDrop = true,
  showHealth = true,
  className = ''
}: ContextNodeProps & { 
  enableDragDrop?: boolean; 
  showHealth?: boolean; 
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const dragRef = useRef<HTMLDivElement>(null);

  // Get node styling based on level and state
  const getNodeStyling = () => {
    const base = "relative group border rounded-lg p-3 cursor-pointer transition-all hover:shadow-md";
    
    let levelStyle = "";
    switch (level) {
      case 'global':
        levelStyle = "bg-emerald-50 border-emerald-200 hover:bg-emerald-100";
        break;
      case 'project':
        levelStyle = "bg-blue-50 border-blue-200 hover:bg-blue-100";
        break;
      case 'task':
        levelStyle = "bg-amber-50 border-amber-200 hover:bg-amber-100";
        break;
    }

    const selectionStyle = isSelected ? "ring-2 ring-blue-500 ring-opacity-50" : "";
    const draggingStyle = isDragging ? "opacity-50 scale-95" : "";
    
    return `${base} ${levelStyle} ${selectionStyle} ${draggingStyle} ${className}`;
  };

  // Drag and drop handlers
  const handleDragStart = (e: React.DragEvent) => {
    if (!enableDragDrop) return;
    
    setIsDragging(true);
    e.dataTransfer.setData('application/json', JSON.stringify({
      contextId: context.context_id,
      level: level,
      contextData: context
    }));
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragEnd = () => {
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    if (!enableDragDrop) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = async (e: React.DragEvent) => {
    if (!enableDragDrop) return;
    
    e.preventDefault();
    e.stopPropagation();

    try {
      const dragData = JSON.parse(e.dataTransfer.getData('application/json'));
      
      if (dragData.contextId === context.context_id) return; // Can't drop on self
      
      // Only allow delegation to higher levels
      if (level === 'global' || (level === 'project' && dragData.level === 'task')) {
        setIsProcessing(true);
        await onDelegate({
          pattern_name: `delegated_${dragData.contextId}`,
          pattern_type: 'context_delegation',
          implementation: dragData.contextData,
          usage_guide: `Delegated from ${dragData.level} to ${level}`
        });
      }
    } catch (error) {
      console.error('Failed to handle drop:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  // Action handlers with loading states
  const handleValidate = async () => {
    setIsProcessing(true);
    try {
      await onValidate();
    } finally {
      setIsProcessing(false);
    }
  };

  const handleResolve = async () => {
    setIsProcessing(true);
    try {
      await onResolve();
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDelegateClick = async () => {
    setIsProcessing(true);
    try {
      await onDelegate({
        pattern_name: `manual_delegation_${context.context_id}`,
        pattern_type: 'manual_delegation',
        implementation: context,
        usage_guide: 'Manually delegated pattern'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div
      ref={dragRef}
      className={getNodeStyling()}
      draggable={enableDragDrop}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={(e) => {
        e.stopPropagation();
        onSelect();
      }}
      onDoubleClick={() => setShowDetails(!showDetails)}
    >
      {/* Header Row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          {/* Expand/Collapse Button */}
          {children.length > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggleExpand();
              }}
              className="w-4 h-4 flex items-center justify-center text-gray-500 hover:text-gray-700 shrink-0"
            >
              {isExpanded ? '▼' : '▶'}
            </button>
          )}

          {/* Level Badge */}
          <LevelBadge level={level} />

          {/* Context Title */}
          <div className="min-w-0 flex-1">
            <h3 className="font-medium text-sm truncate" title={context.data.title || context.context_id}>
              {context.data.title || `Context ${context.context_id.slice(0, 8)}...`}
            </h3>
          </div>

          {/* Health Indicator */}
          {showHealth && (
            <HealthIndicator 
              status={healthStatus.status}
              score={healthStatus.score}
              issues={healthStatus.issues}
            />
          )}
        </div>

        {/* Action Buttons */}
        <ActionButtons
          onValidate={handleValidate}
          onResolve={handleResolve}
          onDelegate={handleDelegateClick}
          disabled={isProcessing}
        />
      </div>

      {/* Context Details (Expanded) */}
      {showDetails && (
        <ContextDetails context={context} />
      )}

      {/* Health Issues (If Any) */}
      {showHealth && healthStatus.issues.length > 0 && (
        <div className="mt-2 space-y-1">
          {healthStatus.issues.slice(0, 2).map((issue, index) => (
            <div key={index} className={`text-xs p-1 rounded ${
              issue.type === 'error' ? 'bg-red-100 text-red-700' : 
              issue.type === 'warning' ? 'bg-yellow-100 text-yellow-700' : 
              'bg-blue-100 text-blue-700'
            }`}>
              {issue.message}
            </div>
          ))}
          {healthStatus.issues.length > 2 && (
            <div className="text-xs text-gray-500">
              +{healthStatus.issues.length - 2} more issues
            </div>
          )}
        </div>
      )}

      {/* Processing Indicator */}
      {isProcessing && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center rounded-lg">
          <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
        </div>
      )}

      {/* Children Count Indicator */}
      {children.length > 0 && !isExpanded && (
        <div className="absolute -top-1 -right-1 bg-blue-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
          {children.length}
        </div>
      )}

      {/* Inheritance Lines (CSS-based) */}
      {level !== 'global' && (
        <div className="absolute -left-3 top-1/2 w-3 h-0.5 bg-blue-300 opacity-50"></div>
      )}
    </div>
  );
}