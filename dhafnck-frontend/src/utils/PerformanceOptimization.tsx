/**
 * Performance Optimization Utilities
 * Provides code splitting, lazy loading, state optimization, and API optimization
 */

import { debounce } from 'lodash-es';
import React, { ComponentType, lazy, memo, ReactNode, Suspense, useCallback, useMemo } from 'react';

// Type definitions for optimization
export interface LazyComponentConfig {
  loader: () => Promise<{ default: ComponentType<any> }>;
  fallback?: ReactNode;
  preload?: boolean;
}

export interface VirtualizationConfig {
  itemHeight: number;
  overscan: number;
  threshold?: number;
}

export interface ApiOptimizationConfig {
  batchTimeout: number;
  cacheTimeout: number;
  maxCacheSize: number;
  retryAttempts: number;
}

// =================
// 1. CODE SPLITTING
// =================

// Route-based lazy loading
export const LazyComponents = {
  // Main Application Components
  ProjectDashboard: lazy(() => import('../components/ProjectDashboard').then(m => ({ default: m.ProjectDashboard }))),
  AgentOrchestration: lazy(() => import('../components/AgentSwitcher')),
  ContextManagement: lazy(() => import('../components/ContextManagementDemo').then(m => ({ default: m.ContextManagementDemo }))),
  SystemMonitoring: lazy(() => import('../components/SystemHealthDashboard')),
  ComplianceDashboard: lazy(() => import('../components/ComplianceDashboard').then(m => ({ default: m.ComplianceDashboard }))),
  
  // Feature-specific Components
  GitBranchManager: lazy(() => import('../components/GitBranchManager')),
  TaskManagement: lazy(() => import('../components/SimpleTaskManager')),
  ProjectCreationWizard: lazy(() => import('../components/ProjectCreationWizard').then(m => ({ default: m.ProjectCreationWizard }))),
  AuditTrailViewer: lazy(() => import('../components/AuditTrailViewer').then(m => ({ default: m.AuditTrailViewer }))),
  ConnectionDiagnostics: lazy(() => import('../components/ConnectionDiagnostics').then(m => ({ default: m.ConnectionDiagnostics }))),
  
  // Context Management
  ContextTree: lazy(() => import('../components/ContextTree').then(m => ({ default: m.ContextTree }))),
  ContextDelegationWorkflow: lazy(() => import('../components/ContextDelegationWorkflow').then(m => ({ default: m.ContextDelegationWorkflow }))),
  ContextInheritanceDebugger: lazy(() => import('../components/ContextInheritanceDebugger')),
  DelegationQueueViewer: lazy(() => import('../components/DelegationQueueViewer')),
  
  // Analytics and Reporting
  CrossProjectAnalytics: lazy(() => import('../components/CrossProjectAnalytics')),
  BranchStatisticsDashboard: lazy(() => import('../components/BranchStatisticsDashboard'))
};

// Dynamic component loader with preloading
export const loadComponentAsync = (componentName: string, preload = false) => {
  const loader = () => import(`../components/${componentName}`).then(module => ({
    default: module.default || module[componentName]
  }));
  
  if (preload) {
    // Preload in the next tick
    setTimeout(() => loader(), 0);
  }
  
  return lazy(loader);
};

// Feature-based module loading
export const FeatureModules = {
  AgentSystem: () => import('../components/AgentManagement'),
  ContextSystem: () => import('../components/ContextManagementDemo'),
  MonitoringSystem: () => import('../components/SystemHealthDashboard'),
  ProjectSystem: () => import('../components/ProjectDashboard'),
  ComplianceSystem: () => import('../components/ComplianceDashboard')
};

// Lazy wrapper with error boundary
export function LazyWrapper({ 
  component: Component, 
  fallback, 
  errorFallback,
  ...props 
}: {
  component: ComponentType<any>;
  fallback?: ReactNode;
  errorFallback?: ReactNode;
  [key: string]: any;
}) {
  const FallbackComponent = fallback || (
    <div className="flex items-center justify-center p-8">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
  );

  const ErrorFallback = errorFallback || (
    <div className="flex items-center justify-center p-8 text-red-600">
      <p>Failed to load component. Please try again.</p>
    </div>
  );

  return (
    <Suspense fallback={FallbackComponent}>
      <ErrorBoundaryWrapper fallback={ErrorFallback}>
        <Component {...props} />
      </ErrorBoundaryWrapper>
    </Suspense>
  );
}

// Error boundary for lazy components
class ErrorBoundaryWrapper extends React.Component<
  { children: ReactNode; fallback: ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: ReactNode; fallback: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Lazy component error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }

    return this.props.children;
  }
}

// =========================
// 2. STATE OPTIMIZATION
// =========================

export class StateOptimizer {
  // Memoization utilities
  static createMemoizedSelector<TState, TResult>(
    selector: (state: TState) => TResult,
    equalityFn?: (a: TResult, b: TResult) => boolean
  ) {
    let lastArgs: TState | undefined;
    let lastResult: TResult;

    return (state: TState): TResult => {
      if (lastArgs === undefined || !Object.is(lastArgs, state)) {
        lastResult = selector(state);
        lastArgs = state;
      } else if (equalityFn && !equalityFn(lastResult, selector(state))) {
        lastResult = selector(state);
        lastArgs = state;
      }
      
      return lastResult;
    };
  }

  // Virtualization configurations
  static virtualizationConfig: Record<string, VirtualizationConfig> = {
    agentList: { itemHeight: 60, overscan: 5, threshold: 50 },
    taskList: { itemHeight: 80, overscan: 3, threshold: 30 },
    contextTree: { itemHeight: 40, overscan: 10, threshold: 100 },
    projectList: { itemHeight: 120, overscan: 2, threshold: 20 },
    notificationList: { itemHeight: 70, overscan: 5, threshold: 25 }
  };

  // Debounced action creators
  static createDebouncedActions = () => ({
    updateContext: debounce((callback: Function, ...args: any[]) => callback(...args), 500),
    savePreferences: debounce((callback: Function, ...args: any[]) => callback(...args), 1000),
    refreshMetrics: debounce((callback: Function, ...args: any[]) => callback(...args), 2000),
    searchFilter: debounce((callback: Function, ...args: any[]) => callback(...args), 300),
    autoSave: debounce((callback: Function, ...args: any[]) => callback(...args), 5000)
  });

  // Batch state updates
  static batchUpdates = (updates: Array<() => void>) => {
    // React 18+ automatically batches updates
    updates.forEach(update => update());
  };

  // State cleanup utilities
  static cleanupState = (state: any, maxAge: number = 3600000) => { // 1 hour default
    const now = Date.now();
    const cleaned = { ...state };

    // Remove old notifications
    if (cleaned.notifications) {
      cleaned.notifications = cleaned.notifications.filter((notification: any) => 
        now - new Date(notification.timestamp).getTime() < maxAge
      );
    }

    // Remove old activity logs
    if (cleaned.recentActivity) {
      cleaned.recentActivity = cleaned.recentActivity.slice(0, 50);
    }

    // Clear empty error states
    if (cleaned.errors) {
      Object.keys(cleaned.errors).forEach(key => {
        if (!cleaned.errors[key]) {
          delete cleaned.errors[key];
        }
      });
    }

    return cleaned;
  };
}

// =======================
// 3. API OPTIMIZATION
// =======================

export class ApiOptimizer {
  private requestBatch: Array<{
    request: any;
    resolve: (value: any) => void;
    reject: (error: any) => void;
    timestamp: number;
  }> = [];
  
  private batchTimeout: NodeJS.Timeout | null = null;
  private cache = new Map<string, { 
    data: any; 
    timestamp: number; 
    ttl: number; 
    hits: number;
  }>();
  
  private config: ApiOptimizationConfig;

  constructor(config: Partial<ApiOptimizationConfig> = {}) {
    this.config = {
      batchTimeout: 50,
      cacheTimeout: 300000, // 5 minutes
      maxCacheSize: 100,
      retryAttempts: 3,
      ...config
    };
  }

  // Request batching
  batchRequest<T>(request: any): Promise<T> {
    return new Promise((resolve, reject) => {
      this.requestBatch.push({ 
        request, 
        resolve, 
        reject, 
        timestamp: Date.now() 
      });
      
      if (!this.batchTimeout) {
        this.batchTimeout = setTimeout(() => {
          this.executeBatch();
        }, this.config.batchTimeout);
      }
    });
  }

  private async executeBatch(): Promise<void> {
    const batch = [...this.requestBatch];
    this.requestBatch = [];
    this.batchTimeout = null;

    if (batch.length === 0) return;

    try {
      // Group similar requests
      const groupedRequests = this.groupRequests(batch);
      
      // Execute each group
      for (const [endpoint, requests] of Object.entries(groupedRequests)) {
        try {
          const responses = await this.sendBatchRequest(endpoint, requests);
          requests.forEach((request, index) => {
            request.resolve(responses[index]);
          });
        } catch (error) {
          requests.forEach(request => {
            request.reject(error);
          });
        }
      }
    } catch (error) {
      batch.forEach(request => {
        request.reject(error);
      });
    }
  }

  private groupRequests(batch: any[]): Record<string, any[]> {
    return batch.reduce((groups, request) => {
      const endpoint = this.getEndpoint(request.request);
      if (!groups[endpoint]) {
        groups[endpoint] = [];
      }
      groups[endpoint].push(request);
      return groups;
    }, {} as Record<string, any[]>);
  }

  private getEndpoint(request: any): string {
    // Extract endpoint from request
    return request.toolName || request.endpoint || 'default';
  }

  private async sendBatchRequest(endpoint: string, requests: any[]): Promise<any[]> {
    // Implementation depends on the actual API structure
    // This is a placeholder for batched API calls
    const responses = await Promise.all(
      requests.map(({ request }) => 
        fetch(`/api/${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(request.request)
        }).then(res => res.json())
      )
    );
    
    return responses;
  }

  // Caching with TTL and hit tracking
  getCachedData(key: string): any | null {
    const cached = this.cache.get(key);
    if (!cached) return null;
    
    if (Date.now() - cached.timestamp > cached.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    // Update hit count
    cached.hits++;
    return cached.data;
  }

  setCachedData(key: string, data: any, ttl: number = this.config.cacheTimeout): void {
    // Implement LRU eviction if cache is full
    if (this.cache.size >= this.config.maxCacheSize) {
      this.evictLeastUsed();
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
      hits: 0
    });
  }

  private evictLeastUsed(): void {
    let leastUsedKey = '';
    let minHits = Infinity;
    let oldestTimestamp = Infinity;

    for (const [key, value] of Array.from(this.cache.entries())) {
      if (value.hits < minHits || (value.hits === minHits && value.timestamp < oldestTimestamp)) {
        minHits = value.hits;
        oldestTimestamp = value.timestamp;
        leastUsedKey = key;
      }
    }

    if (leastUsedKey) {
      this.cache.delete(leastUsedKey);
    }
  }

  // Cache statistics
  getCacheStats() {
    const stats = {
      size: this.cache.size,
      maxSize: this.config.maxCacheSize,
      utilization: (this.cache.size / this.config.maxCacheSize) * 100,
      totalHits: 0,
      entries: [] as any[]
    };

    for (const [key, value] of Array.from(this.cache.entries())) {
      stats.totalHits += value.hits;
      stats.entries.push({
        key,
        hits: value.hits,
        age: Date.now() - value.timestamp,
        ttl: value.ttl
      });
    }

    return stats;
  }

  // Request retry with exponential backoff
  async retryRequest<T>(
    requestFn: () => Promise<T>,
    maxAttempts: number = this.config.retryAttempts
  ): Promise<T> {
    let lastError: Error;
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        return await requestFn();
      } catch (error) {
        lastError = error as Error;
        
        if (attempt === maxAttempts) {
          throw lastError;
        }
        
        // Exponential backoff
        const delay = Math.min(1000 * Math.pow(2, attempt - 1), 10000);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
    
    throw lastError!;
  }

  // Clear cache
  clearCache(): void {
    this.cache.clear();
  }

  // Get cache size in bytes (approximate)
  getCacheSize(): number {
    let size = 0;
    for (const [key, value] of Array.from(this.cache.entries())) {
      size += JSON.stringify({ key, ...value }).length * 2; // Rough estimate
    }
    return size;
  }
}

// =========================
// 4. COMPONENT OPTIMIZATION
// =========================

// HOC for performance monitoring
export function withPerformanceMonitoring<T extends {}>(
  Component: ComponentType<T>,
  componentName: string
) {
  return memo(function WithPerformanceMonitoring(props: T) {
    const startTime = useMemo(() => performance.now(), []);
    
    React.useEffect(() => {
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      if (renderTime > 100) {
        console.warn(`Slow render detected in ${componentName}: ${renderTime.toFixed(2)}ms`);
      }
      
      // Store performance metrics
      if ('performance' in window && 'mark' in performance) {
        performance.mark(`${componentName}-render-end`);
        performance.measure(
          `${componentName}-render-time`,
          `${componentName}-render-start`,
          `${componentName}-render-end`
        );
      }
    });

    React.useEffect(() => {
      if ('performance' in window && 'mark' in performance) {
        performance.mark(`${componentName}-render-start`);
      }
    }, []);
    
    return <Component {...props} />;
  });
}

// Virtualized list component
export function VirtualizedList<T>({
  items,
  renderItem,
  itemHeight,
  containerHeight,
  overscan = 5
}: {
  items: T[];
  renderItem: (item: T, index: number) => ReactNode;
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
}) {
  const [scrollTop, setScrollTop] = React.useState(0);
  
  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const endIndex = Math.min(
    items.length - 1,
    Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
  );
  
  const visibleItems = items.slice(startIndex, endIndex + 1);
  const totalHeight = items.length * itemHeight;
  const offsetY = startIndex * itemHeight;

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  return (
    <div
      style={{ height: containerHeight, overflow: 'auto' }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div style={{ transform: `translateY(${offsetY}px)` }}>
          {visibleItems.map((item, index) => (
            <div key={startIndex + index} style={{ height: itemHeight }}>
              {renderItem(item, startIndex + index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Global performance optimization instance
export const globalApiOptimizer = new ApiOptimizer();

// Preload critical components
export const preloadCriticalComponents = () => {
  // Preload components likely to be used soon
  LazyComponents.ProjectDashboard;
  LazyComponents.SystemMonitoring;
  LazyComponents.AgentOrchestration;
};

// Bundle analysis helper
export const analyzeBundleSize = () => {
  if (process.env.NODE_ENV === 'development') {
    console.log('Bundle analysis: Use "npm run build && npx webpack-bundle-analyzer build/static/js/*.js" to analyze bundle size');
  }
};

export default {
  LazyComponents,
  StateOptimizer,
  ApiOptimizer,
  withPerformanceMonitoring,
  VirtualizedList,
  globalApiOptimizer,
  preloadCriticalComponents
};