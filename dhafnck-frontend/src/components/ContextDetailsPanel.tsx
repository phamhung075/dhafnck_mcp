/**
 * ContextDetailsPanel Component
 * Provides tabbed interface for context management with Overview, Data, Inheritance, Insights, Progress, and Next Steps
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Alert } from './ui/alert';
import {
  ContextDetailsPanelProps,
  ContextDetailTab,
  HierarchicalContext,
  ResolvedContext,
  InheritanceChainItem,
  ContextInsight,
  ContextProgress
} from '../types/context-delegation';

// Import sub-components
import { ContextDataEditor } from './ContextDataEditor';
import { ContextInheritanceView } from './ContextInheritanceView';
import { ContextInsightsManager } from './ContextInsightsManager';
import { ContextProgressView } from './ContextProgressView';
import { ContextNextStepsEditor } from './ContextNextStepsEditor';

export function ContextDetailsPanel({
  context,
  resolvedContext,
  inheritanceChain,
  onUpdateContext,
  onAddInsight,
  onAddProgress,
  onUpdateNextSteps,
  onForceRefresh,
  className = ''
}: ContextDetailsPanelProps) {
  const [activeTab, setActiveTab] = useState<ContextDetailTab>('overview');
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Handle tab switching
  const handleTabChange = useCallback((tab: ContextDetailTab) => {
    setActiveTab(tab);
    setErrors(prev => ({ ...prev, [tab]: '' }));
  }, []);

  // Handle refresh with loading state
  const handleRefresh = useCallback(async () => {
    setLoading(prev => ({ ...prev, refresh: true }));
    try {
      await onForceRefresh();
    } catch (error) {
      setErrors(prev => ({ 
        ...prev, 
        refresh: error instanceof Error ? error.message : 'Failed to refresh context' 
      }));
    } finally {
      setLoading(prev => ({ ...prev, refresh: false }));
    }
  }, [onForceRefresh]);

  // Tab configuration
  const tabs: Array<{
    id: ContextDetailTab;
    label: string;
    icon: string;
    description: string;
    disabled?: boolean;
  }> = [
    {
      id: 'overview',
      label: 'Overview',
      icon: '📊',
      description: 'Context summary and key metrics'
    },
    {
      id: 'data',
      label: 'Data',
      icon: '📝',
      description: 'JSON editor for context data'
    },
    {
      id: 'inheritance',
      label: 'Inheritance',
      icon: '🔗',
      description: 'Visual inheritance chain',
      disabled: !inheritanceChain?.length
    },
    {
      id: 'insights',
      label: 'Insights',
      icon: '💡',
      description: 'Insight management'
    },
    {
      id: 'progress',
      label: 'Progress',
      icon: '📈',
      description: 'Progress tracking'
    },
    {
      id: 'next-steps',
      label: 'Next Steps',
      icon: '🎯',
      description: 'Action planning'
    }
  ];

  // Render tab content
  const renderTabContent = () => {
    if (!context) {
      return (
        <div className="flex items-center justify-center h-48 text-gray-500">
          No context selected
        </div>
      );
    }

    switch (activeTab) {
      case 'overview':
        return <ContextOverview context={context} resolvedContext={resolvedContext} />;
      
      case 'data':
        return (
          <ContextDataEditor
            contextData={context.data}
            onChange={(updates) => {
              setLoading(prev => ({ ...prev, data: true }));
              onUpdateContext(context.context_id, updates)
                .catch(error => setErrors(prev => ({ 
                  ...prev, 
                  data: error.message 
                })))
                .finally(() => setLoading(prev => ({ ...prev, data: false })));
            }}
            onSave={async () => {
              // Data is auto-saved on change
            }}
            readOnly={false}
          />
        );
      
      case 'inheritance':
        return (
          <ContextInheritanceView
            context={context}
            inheritanceChain={inheritanceChain}
            resolvedContext={resolvedContext}
          />
        );
      
      case 'insights':
        return (
          <ContextInsightsManager
            insights={[]} // Will be loaded from props/state
            contextId={context.context_id}
            onAddInsight={(insight) => onAddInsight(context.context_id, insight as ContextInsight)}
            onUpdateInsight={async () => {}}
            onDeleteInsight={async () => {}}
            onFilterInsights={() => {}}
          />
        );
      
      case 'progress':
        return (
          <ContextProgressView
            contextId={context.context_id}
            progress={[]} // Will be loaded from props/state
            onAddProgress={(progress) => onAddProgress(context.context_id, progress)}
          />
        );
      
      case 'next-steps':
        return (
          <ContextNextStepsEditor
            contextId={context.context_id}
            nextSteps={context.data.next_steps || []}
            onUpdateNextSteps={(steps) => onUpdateNextSteps(context.context_id, steps)}
          />
        );
      
      default:
        return <div>Unknown tab: {activeTab}</div>;
    }
  };

  return (
    <div className={`context-details-panel ${className}`}>
      <Card className="h-full flex flex-col">
        {/* Header */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">
                {context?.data.title || 'Context Details'}
              </h2>
              <p className="text-sm text-gray-500">
                {context ? `${context.level.toUpperCase()} • ${context.context_id}` : 'No context selected'}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {context && (
                <Badge variant={
                  context.level === 'global' ? 'default' :
                  context.level === 'project' ? 'secondary' : 'outline'
                }>
                  {context.level}
                </Badge>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={loading.refresh}
              >
                {loading.refresh ? '🔄' : '↻'} Refresh
              </Button>
            </div>
          </div>

          {/* Global error display */}
          {errors.refresh && (
            <Alert className="mt-2 bg-red-50 border-red-200">
              <span className="text-red-600 text-sm">{errors.refresh}</span>
            </Alert>
          )}
        </div>

        {/* Tab Navigation */}
        <div className="px-4 py-2 border-b bg-gray-50">
          <div className="flex space-x-1 overflow-x-auto">
            {tabs.map(tab => (
              <button
                key={tab.id}
                className={`
                  px-3 py-2 text-sm font-medium rounded-md whitespace-nowrap transition-colors
                  ${activeTab === tab.id 
                    ? 'bg-white text-blue-600 shadow-sm border border-gray-200' 
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }
                  ${tab.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                `}
                onClick={() => !tab.disabled && handleTabChange(tab.id)}
                disabled={tab.disabled}
                title={tab.description}
              >
                <span className="mr-1">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1 p-4 overflow-auto">
          {errors[activeTab] && (
            <Alert className="mb-4 bg-red-50 border-red-200">
              <span className="text-red-600 text-sm">{errors[activeTab]}</span>
            </Alert>
          )}
          
          {loading[activeTab] && (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          )}
          
          {!loading[activeTab] && renderTabContent()}
        </div>
      </Card>
    </div>
  );
}

// Overview Tab Component
function ContextOverview({ 
  context, 
  resolvedContext 
}: { 
  context: HierarchicalContext; 
  resolvedContext: ResolvedContext | null; 
}) {
  const metrics = [
    {
      label: 'Level',
      value: context.level.toUpperCase(),
      icon: '📊'
    },
    {
      label: 'Status',
      value: context.data.status || 'Unknown',
      icon: '🔄'
    },
    {
      label: 'Priority',
      value: context.data.priority || 'Medium',
      icon: '⭐'
    },
    {
      label: 'Last Updated',
      value: context.metadata.updated_at ? new Date(context.metadata.updated_at).toLocaleDateString() : 'Unknown',
      icon: '📅'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {metrics.map((metric, index) => (
          <Card key={index} className="p-3">
            <div className="flex items-center space-x-2">
              <span className="text-lg">{metric.icon}</span>
              <div>
                <p className="text-xs text-gray-500">{metric.label}</p>
                <p className="font-medium">{metric.value}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Description */}
      {context.data.description && (
        <Card className="p-4">
          <h3 className="font-medium mb-2">Description</h3>
          <p className="text-gray-700">{context.data.description}</p>
        </Card>
      )}

      {/* Assignees */}
      {context.data.assignees && context.data.assignees.length > 0 && (
        <Card className="p-4">
          <h3 className="font-medium mb-2">Assignees</h3>
          <div className="flex flex-wrap gap-2">
            {context.data.assignees.map((assignee: string, index: number) => (
              <Badge key={index} variant="outline">
                {assignee}
              </Badge>
            ))}
          </div>
        </Card>
      )}

      {/* Labels */}
      {context.data.labels && context.data.labels.length > 0 && (
        <Card className="p-4">
          <h3 className="font-medium mb-2">Labels</h3>
          <div className="flex flex-wrap gap-2">
            {context.data.labels.map((label: string, index: number) => (
              <Badge key={index} variant="secondary">
                {label}
              </Badge>
            ))}
          </div>
        </Card>
      )}

      {/* Resolution Info */}
      {resolvedContext && (
        <Card className="p-4">
          <h3 className="font-medium mb-2">Resolution Information</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Resolved At:</span>
              <span>{new Date(resolvedContext.resolution_metadata.resolved_at).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Cache Status:</span>
              <Badge variant={resolvedContext.resolution_metadata.cache_status === 'hit' ? 'default' : 'outline'}>
                {resolvedContext.resolution_metadata.cache_status}
              </Badge>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Resolution Time:</span>
              <span>{resolvedContext.resolution_metadata.resolution_timing.total_ms}ms</span>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}