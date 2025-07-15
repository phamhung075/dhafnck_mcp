/**
 * ContextInheritanceView Component
 * Visual display of context inheritance chain and resolution
 */

import React from 'react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Alert } from './ui/alert';
import {
  HierarchicalContext,
  ResolvedContext,
  InheritanceChainItem,
  ContextConflict
} from '../types/context-delegation';

interface ContextInheritanceViewProps {
  context: HierarchicalContext;
  inheritanceChain: InheritanceChainItem[];
  resolvedContext: ResolvedContext | null;
}

export function ContextInheritanceView({
  context,
  inheritanceChain,
  resolvedContext
}: ContextInheritanceViewProps) {
  const renderInheritanceChain = () => {
    return (
      <div className="space-y-4">
        {inheritanceChain.map((item, index) => (
          <div key={item.context_id} className="relative">
            <Card className={`p-4 ${item.level === context.level ? 'border-blue-500 bg-blue-50' : ''}`}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <Badge variant={
                    item.level === 'global' ? 'default' :
                    item.level === 'project' ? 'secondary' : 'outline'
                  }>
                    {item.level.toUpperCase()}
                  </Badge>
                  <span className="font-medium">{item.data.title || 'Untitled'}</span>
                  {item.level === context.level && (
                    <Badge variant="outline">Current</Badge>
                  )}
                </div>
                <span className="text-xs text-gray-500">{item.context_id.slice(0, 8)}...</span>
              </div>

              {/* Properties */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <h4 className="font-medium text-green-600 mb-1">Effective Properties</h4>
                  <div className="space-y-1">
                    {item.effective_properties.map(prop => (
                      <div key={prop} className="flex items-center">
                        <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                        <span>{prop}</span>
                      </div>
                    ))}
                  </div>
                  {item.effective_properties.length === 0 && (
                    <span className="text-gray-500">None</span>
                  )}
                </div>
                <div>
                  <h4 className="font-medium text-orange-600 mb-1">Overridden Properties</h4>
                  <div className="space-y-1">
                    {item.overridden_properties.map(prop => (
                      <div key={prop} className="flex items-center">
                        <span className="w-2 h-2 bg-orange-500 rounded-full mr-2"></span>
                        <span>{prop}</span>
                      </div>
                    ))}
                  </div>
                  {item.overridden_properties.length === 0 && (
                    <span className="text-gray-500">None</span>
                  )}
                </div>
              </div>
            </Card>

            {/* Inheritance Arrow */}
            {index < inheritanceChain.length - 1 && (
              <div className="flex justify-center my-2">
                <div className="flex items-center text-gray-400">
                  <div className="w-px h-6 bg-gray-300"></div>
                  <div className="w-0 h-0 border-l-4 border-r-4 border-t-6 border-transparent border-t-gray-400 mx-1"></div>
                  <div className="w-px h-6 bg-gray-300"></div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  const renderConflicts = () => {
    if (!resolvedContext?.conflicts || resolvedContext.conflicts.length === 0) {
      return (
        <Alert className="bg-green-50 border-green-200">
          <span className="text-green-600">✓ No inheritance conflicts detected</span>
        </Alert>
      );
    }

    return (
      <div className="space-y-3">
        <Alert className="bg-yellow-50 border-yellow-200">
          <span className="text-yellow-600">⚠️ {resolvedContext.conflicts.length} inheritance conflicts found</span>
        </Alert>

        {resolvedContext.conflicts.map((conflict, index) => (
          <Card key={index} className="p-4 border-yellow-200">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="font-medium text-yellow-800">Conflict in field: {conflict.field}</h4>
                <Badge variant="outline">{conflict.conflict_type}</Badge>
              </div>

              <div className="text-sm space-y-1">
                <div className="flex items-center">
                  <span className="text-gray-500 w-20">Task:</span>
                  <code className="bg-gray-100 px-2 py-1 rounded text-xs">
                    {JSON.stringify(conflict.task_value)}
                  </code>
                </div>
                {conflict.project_value !== undefined && (
                  <div className="flex items-center">
                    <span className="text-gray-500 w-20">Project:</span>
                    <code className="bg-gray-100 px-2 py-1 rounded text-xs">
                      {JSON.stringify(conflict.project_value)}
                    </code>
                  </div>
                )}
                {conflict.global_value !== undefined && (
                  <div className="flex items-center">
                    <span className="text-gray-500 w-20">Global:</span>
                    <code className="bg-gray-100 px-2 py-1 rounded text-xs">
                      {JSON.stringify(conflict.global_value)}
                    </code>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between pt-2 border-t">
                <span className="text-sm text-gray-600">Resolution Strategy:</span>
                <Badge variant={
                  conflict.resolution_strategy === 'task_wins' ? 'default' :
                  conflict.resolution_strategy === 'project_wins' ? 'secondary' :
                  conflict.resolution_strategy === 'global_wins' ? 'outline' : 'destructive'
                }>
                  {conflict.resolution_strategy.replace('_', ' ')}
                </Badge>
              </div>
            </div>
          </Card>
        ))}
      </div>
    );
  };

  const renderResolutionMetrics = () => {
    if (!resolvedContext?.resolution_metadata) return null;

    const metrics = resolvedContext.resolution_metadata;
    return (
      <Card className="p-4">
        <h3 className="font-medium mb-3">Resolution Metrics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Total Time</span>
            <p className="font-medium">{metrics.resolution_timing.total_ms}ms</p>
          </div>
          <div>
            <span className="text-gray-500">Cache Lookup</span>
            <p className="font-medium">{metrics.resolution_timing.cache_lookup_ms}ms</p>
          </div>
          <div>
            <span className="text-gray-500">Inheritance</span>
            <p className="font-medium">{metrics.resolution_timing.inheritance_resolution_ms}ms</p>
          </div>
          <div>
            <span className="text-gray-500">Cache Status</span>
            <Badge variant={metrics.cache_status === 'hit' ? 'default' : 'outline'}>
              {metrics.cache_status}
            </Badge>
          </div>
        </div>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-2">Inheritance Chain</h2>
        <p className="text-gray-600 mb-4">
          Shows how properties are inherited from higher-level contexts.
        </p>
      </div>

      {/* Inheritance Chain Visualization */}
      {inheritanceChain.length > 0 ? (
        renderInheritanceChain()
      ) : (
        <Alert>
          <span>No inheritance chain data available</span>
        </Alert>
      )}

      {/* Conflicts Section */}
      <div>
        <h3 className="font-medium mb-3">Inheritance Conflicts</h3>
        {renderConflicts()}
      </div>

      {/* Resolution Metrics */}
      {renderResolutionMetrics()}
    </div>
  );
}