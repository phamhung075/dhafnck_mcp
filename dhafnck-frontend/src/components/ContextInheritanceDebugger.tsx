/**
 * ContextInheritanceDebugger Component
 * Debug and validate inheritance chains with performance monitoring
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Alert } from './ui/alert';
import { Separator } from './ui/separator';
import {
  ContextInheritanceDebuggerProps,
  ContextInheritanceValidation,
  ValidationError
} from '../types/context-delegation';

function ContextInheritanceDebugger({
  contextId,
  level,
  validationResult,
  onValidate,
  onRepairInheritance,
  onOptimizePerformance,
  onClearCache
}: ContextInheritanceDebuggerProps) {
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [lastValidated, setLastValidated] = useState<string | null>(null);
  const [autoValidate, setAutoValidate] = useState(false);

  // Handle validation
  const handleValidate = useCallback(async () => {
    setLoading(prev => ({ ...prev, validate: true }));
    try {
      await onValidate(contextId, level);
      setLastValidated(new Date().toISOString());
    } catch (error) {
      console.error('Validation failed:', error);
    } finally {
      setLoading(prev => ({ ...prev, validate: false }));
    }
  }, [contextId, level, onValidate]);

  // Handle repair
  const handleRepair = useCallback(async () => {
    setLoading(prev => ({ ...prev, repair: true }));
    try {
      await onRepairInheritance(contextId, level);
      // Re-validate after repair
      await handleValidate();
    } catch (error) {
      console.error('Repair failed:', error);
    } finally {
      setLoading(prev => ({ ...prev, repair: false }));
    }
  }, [contextId, level, onRepairInheritance, handleValidate]);

  // Handle performance optimization
  const handleOptimize = useCallback(async () => {
    setLoading(prev => ({ ...prev, optimize: true }));
    try {
      await onOptimizePerformance(contextId);
      // Re-validate after optimization
      await handleValidate();
    } catch (error) {
      console.error('Optimization failed:', error);
    } finally {
      setLoading(prev => ({ ...prev, optimize: false }));
    }
  }, [contextId, onOptimizePerformance, handleValidate]);

  // Handle cache clearing
  const handleClearCache = useCallback(async () => {
    setLoading(prev => ({ ...prev, clearCache: true }));
    try {
      await onClearCache(contextId);
      // Re-validate after cache clear
      await handleValidate();
    } catch (error) {
      console.error('Cache clear failed:', error);
    } finally {
      setLoading(prev => ({ ...prev, clearCache: false }));
    }
  }, [contextId, onClearCache, handleValidate]);

  // Auto-validate effect
  useEffect(() => {
    if (autoValidate) {
      const interval = setInterval(() => {
        handleValidate();
      }, 30000); // Validate every 30 seconds

      return () => clearInterval(interval);
    }
  }, [autoValidate, handleValidate]);

  // Initial validation
  useEffect(() => {
    if (!validationResult) {
      handleValidate();
    }
  }, []);

  const getPerformanceGradeColor = (grade: string) => {
    switch (grade) {
      case 'A': return 'text-green-600 bg-green-100';
      case 'B': return 'text-blue-600 bg-blue-100';
      case 'C': return 'text-yellow-600 bg-yellow-100';
      case 'D': return 'text-orange-600 bg-orange-100';
      case 'F': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const categorizeErrors = (errors: ValidationError[]) => {
    const categories = {
      critical: errors.filter(e => e.severity === 'error'),
      warnings: errors.filter(e => e.severity === 'warning'),
      info: errors.filter(e => e.severity === 'info')
    };
    return categories;
  };

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Inheritance Debugger</h2>
          <p className="text-sm text-gray-600">
            Context: {contextId.slice(0, 8)}... • Level: {level.toUpperCase()}
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <label className="flex items-center space-x-2 text-sm">
            <input
              type="checkbox"
              checked={autoValidate}
              onChange={(e) => setAutoValidate(e.target.checked)}
              className="rounded"
            />
            <span>Auto-validate</span>
          </label>
          
          <Button
            onClick={handleValidate}
            disabled={loading.validate}
            size="sm"
          >
            {loading.validate ? 'Validating...' : '🔍 Validate'}
          </Button>
        </div>
      </div>

      {/* Validation Status */}
      {validationResult && (
        <Card className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium">Validation Status</h3>
            <div className="flex items-center space-x-2">
              <Badge variant={validationResult.valid ? 'default' : 'destructive'}>
                {validationResult.valid ? '✓ Valid' : '✗ Invalid'}
              </Badge>
              <Badge className={getPerformanceGradeColor(validationResult.performance_grade)}>
                Grade: {validationResult.performance_grade}
              </Badge>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Resolution Time</span>
              <p className="font-medium">{validationResult.resolution_timing.total_ms}ms</p>
            </div>
            <div>
              <span className="text-gray-500">Cache Hit Ratio</span>
              <p className="font-medium">{Math.round(validationResult.cache_metrics.hit_ratio * 100)}%</p>
            </div>
            <div>
              <span className="text-gray-500">Chain Length</span>
              <p className="font-medium">{validationResult.inheritance_chain.length}</p>
            </div>
            <div>
              <span className="text-gray-500">Errors</span>
              <p className="font-medium text-red-600">{validationResult.errors.length}</p>
            </div>
          </div>

          {lastValidated && (
            <p className="text-xs text-gray-500 mt-2">
              Last validated: {new Date(lastValidated).toLocaleString()}
            </p>
          )}
        </Card>
      )}

      {/* Action Buttons */}
      <Card className="p-4">
        <h3 className="font-medium mb-3">Maintenance Actions</h3>
        <div className="flex flex-wrap gap-2">
          <Button
            onClick={handleRepair}
            disabled={loading.repair || !validationResult || validationResult.valid}
            variant="outline"
          >
            {loading.repair ? 'Repairing...' : '🔧 Repair Inheritance'}
          </Button>
          
          <Button
            onClick={handleOptimize}
            disabled={loading.optimize}
            variant="outline"
          >
            {loading.optimize ? 'Optimizing...' : '⚡ Optimize Performance'}
          </Button>
          
          <Button
            onClick={handleClearCache}
            disabled={loading.clearCache}
            variant="outline"
          >
            {loading.clearCache ? 'Clearing...' : '🗑️ Clear Cache'}
          </Button>
        </div>
      </Card>

      {/* Detailed Results */}
      {validationResult && (
        <>
          {/* Errors and Warnings */}
          {validationResult.errors.length > 0 && (
            <Card className="p-4">
              <h3 className="font-medium mb-3">Validation Issues</h3>
              <ErrorList errors={validationResult.errors} />
            </Card>
          )}

          {/* Warnings */}
          {validationResult.warnings.length > 0 && (
            <Card className="p-4">
              <h3 className="font-medium mb-3">Warnings</h3>
              <div className="space-y-2">
                {validationResult.warnings.map((warning, index) => (
                  <Alert key={index} className="bg-yellow-50 border-yellow-200">
                    <span className="text-yellow-800">{warning}</span>
                  </Alert>
                ))}
              </div>
            </Card>
          )}

          {/* Performance Metrics */}
          <Card className="p-4">
            <h3 className="font-medium mb-3">Performance Analysis</h3>
            <PerformanceMetrics 
              validation={validationResult}
              onOptimize={handleOptimize}
              optimizing={loading.optimize}
            />
          </Card>

          {/* Inheritance Chain */}
          <Card className="p-4">
            <h3 className="font-medium mb-3">Inheritance Chain</h3>
            <InheritanceChainView 
              chain={validationResult.inheritance_chain}
              resolutionPath={validationResult.resolution_path}
            />
          </Card>

          {/* Optimization Suggestions */}
          {validationResult.optimization_suggestions.length > 0 && (
            <Card className="p-4">
              <h3 className="font-medium mb-3">Optimization Suggestions</h3>
              <div className="space-y-2">
                {validationResult.optimization_suggestions.map((suggestion, index) => (
                  <div key={index} className="flex items-start space-x-2 p-3 bg-blue-50 rounded">
                    <span className="text-blue-500 mt-0.5">💡</span>
                    <span className="text-blue-800 text-sm">{suggestion}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

export { ContextInheritanceDebugger };
export default ContextInheritanceDebugger;

// Error List Component
function ErrorList({ errors }: { errors: ValidationError[] }) {
  const categorizedErrors = errors.reduce((acc, error) => {
    if (!acc[error.severity]) acc[error.severity] = [];
    acc[error.severity].push(error);
    return acc;
  }, {} as Record<string, ValidationError[]>);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error': return 'bg-red-50 border-red-200 text-red-800';
      case 'warning': return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'info': return 'bg-blue-50 border-blue-200 text-blue-800';
      default: return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  return (
    <div className="space-y-3">
      {Object.entries(categorizedErrors).map(([severity, severityErrors]) => (
        <div key={severity}>
          <h4 className="font-medium mb-2 capitalize">{severity}s ({severityErrors.length})</h4>
          <div className="space-y-2">
            {severityErrors.map((error, index) => (
              <Alert key={index} className={getSeverityColor(error.severity)}>
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{error.code}</span>
                    {error.field && (
                      <Badge variant="outline" className="text-xs">
                        {error.field}
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm">{error.message}</p>
                  {error.suggestion && (
                    <p className="text-xs italic">Suggestion: {error.suggestion}</p>
                  )}
                </div>
              </Alert>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// Performance Metrics Component
function PerformanceMetrics({ 
  validation, 
  onOptimize, 
  optimizing 
}: { 
  validation: ContextInheritanceValidation;
  onOptimize: () => void;
  optimizing: boolean;
}) {
  const timing = validation.resolution_timing;
  const cache = validation.cache_metrics;

  const getTimingStatus = (ms: number) => {
    if (ms < 10) return { status: 'excellent', color: 'text-green-600' };
    if (ms < 50) return { status: 'good', color: 'text-blue-600' };
    if (ms < 100) return { status: 'acceptable', color: 'text-yellow-600' };
    return { status: 'poor', color: 'text-red-600' };
  };

  const getCacheStatus = (ratio: number) => {
    if (ratio > 0.8) return { status: 'excellent', color: 'text-green-600' };
    if (ratio > 0.6) return { status: 'good', color: 'text-blue-600' };
    if (ratio > 0.4) return { status: 'fair', color: 'text-yellow-600' };
    return { status: 'poor', color: 'text-red-600' };
  };

  const timingStatus = getTimingStatus(timing.total_ms);
  const cacheStatus = getCacheStatus(cache.hit_ratio);

  return (
    <div className="space-y-4">
      {/* Timing Breakdown */}
      <div>
        <h4 className="font-medium mb-2">Resolution Timing</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className={`text-2xl font-bold ${timingStatus.color}`}>
              {timing.total_ms}ms
            </div>
            <div className="text-sm text-gray-500">Total Time</div>
            <div className="text-xs text-gray-400 capitalize">{timingStatus.status}</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-medium">
              {timing.cache_lookup_ms}ms
            </div>
            <div className="text-sm text-gray-500">Cache Lookup</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-medium">
              {timing.inheritance_resolution_ms}ms
            </div>
            <div className="text-sm text-gray-500">Inheritance Resolution</div>
          </div>
        </div>
      </div>

      <Separator />

      {/* Cache Metrics */}
      <div>
        <h4 className="font-medium mb-2">Cache Performance</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className={`text-2xl font-bold ${cacheStatus.color}`}>
              {Math.round(cache.hit_ratio * 100)}%
            </div>
            <div className="text-sm text-gray-500">Hit Ratio</div>
            <div className="text-xs text-gray-400 capitalize">{cacheStatus.status}</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-medium">
              {Math.round(cache.miss_ratio * 100)}%
            </div>
            <div className="text-sm text-gray-500">Miss Ratio</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-medium">
              {cache.entries}
            </div>
            <div className="text-sm text-gray-500">Cache Entries</div>
          </div>
        </div>

        {cache.total_size_mb && (
          <div className="mt-2 text-center">
            <span className="text-sm text-gray-500">
              Cache Size: {cache.total_size_mb.toFixed(2)} MB
            </span>
          </div>
        )}
      </div>

      {/* Optimization Actions */}
      {(timing.total_ms > 50 || cache.hit_ratio < 0.6) && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-yellow-800 font-medium">Performance Issues Detected</span>
              <p className="text-yellow-700 text-sm mt-1">
                Consider running optimization to improve performance.
              </p>
            </div>
            <Button
              size="sm"
              onClick={onOptimize}
              disabled={optimizing}
            >
              {optimizing ? 'Optimizing...' : 'Optimize'}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

// Inheritance Chain View Component
function InheritanceChainView({ 
  chain, 
  resolutionPath 
}: { 
  chain: string[];
  resolutionPath: any[];
}) {
  return (
    <div className="space-y-3">
      <div className="text-sm text-gray-600">
        Chain: {chain.join(' → ')}
      </div>
      
      {resolutionPath && resolutionPath.length > 0 && (
        <div className="space-y-2">
          {resolutionPath.map((context, index) => (
            <div 
              key={index}
              className="flex items-center space-x-3 p-3 bg-gray-50 rounded"
            >
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-sm font-medium">
                {index + 1}
              </div>
              <div className="flex-1">
                <div className="font-medium">{context.level?.toUpperCase()}</div>
                <div className="text-sm text-gray-600">{context.context_id}</div>
              </div>
              <Badge variant="outline">
                {Object.keys(context.data || {}).length} properties
              </Badge>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}