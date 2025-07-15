/**
 * Loading States and Skeleton Components
 * Provides consistent loading states throughout the application
 */

import React from 'react';
import { Loader2, Zap, Activity, GitBranch, Users, BarChart3 } from 'lucide-react';

// ===================
// SKELETON COMPONENTS
// ===================

export const SkeletonComponents = {
  // Navigation skeleton
  Navigation: () => (
    <div className="animate-pulse bg-white border-b border-gray-200 h-16">
      <div className="max-w-full px-4 sm:px-6 lg:px-8 h-full">
        <div className="flex justify-between items-center h-full">
          {/* Left section */}
          <div className="flex items-center space-x-4">
            <div className="w-8 h-8 bg-gray-200 rounded-lg"></div>
            <div className="hidden sm:block w-24 h-6 bg-gray-200 rounded"></div>
            <div className="hidden md:flex items-center space-x-1">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="w-16 h-8 bg-gray-200 rounded-lg"></div>
              ))}
            </div>
          </div>
          
          {/* Center section */}
          <div className="flex-1 flex justify-center max-w-md mx-4">
            <div className="w-full h-10 bg-gray-200 rounded-lg"></div>
          </div>
          
          {/* Right section */}
          <div className="flex items-center space-x-4">
            <div className="w-20 h-8 bg-gray-200 rounded-full"></div>
            <div className="w-32 h-8 bg-gray-200 rounded-lg"></div>
            <div className="w-24 h-8 bg-gray-200 rounded-lg"></div>
            <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
          </div>
        </div>
      </div>
    </div>
  ),

  // Agent switcher skeleton
  AgentSwitcher: () => (
    <div className="animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-32 mb-2"></div>
      <div className="h-8 bg-gray-200 rounded w-24"></div>
    </div>
  ),

  // Project dashboard skeleton
  ProjectDashboard: () => (
    <div className="animate-pulse space-y-6 p-6">
      <div className="flex justify-between items-center">
        <div className="h-8 bg-gray-200 rounded w-48"></div>
        <div className="h-10 bg-gray-200 rounded w-32"></div>
      </div>
      
      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white p-6 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <div className="h-4 bg-gray-200 rounded w-20 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-16"></div>
              </div>
              <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="h-6 bg-gray-200 rounded w-32 mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gray-200 rounded"></div>
                <div className="flex-1">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-1"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
                <div className="h-6 bg-gray-200 rounded w-16"></div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="h-6 bg-gray-200 rounded w-32 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    </div>
  ),

  // Task list skeleton
  TaskList: () => (
    <div className="animate-pulse space-y-4">
      <div className="flex justify-between items-center">
        <div className="h-6 bg-gray-200 rounded w-24"></div>
        <div className="h-8 bg-gray-200 rounded w-20"></div>
      </div>
      
      {[...Array(6)].map((_, i) => (
        <div key={i} className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="h-5 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-3"></div>
              <div className="flex items-center space-x-4">
                <div className="h-6 bg-gray-200 rounded w-16"></div>
                <div className="h-6 bg-gray-200 rounded w-20"></div>
                <div className="h-6 bg-gray-200 rounded w-24"></div>
              </div>
            </div>
            <div className="h-8 bg-gray-200 rounded w-8"></div>
          </div>
        </div>
      ))}
    </div>
  ),

  // Context tree skeleton
  ContextTree: () => (
    <div className="animate-pulse space-y-2">
      {[...Array(8)].map((_, i) => (
        <div key={i} className="flex items-center space-x-2" style={{ paddingLeft: `${(i % 3) * 20}px` }}>
          <div className="h-4 w-4 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded flex-1"></div>
          <div className="h-6 bg-gray-200 rounded w-12"></div>
        </div>
      ))}
    </div>
  ),

  // System health skeleton
  SystemHealth: () => (
    <div className="animate-pulse space-y-6">
      <div className="h-8 bg-gray-200 rounded w-48"></div>
      
      {/* Health score */}
      <div className="text-center space-y-4">
        <div className="w-32 h-32 bg-gray-200 rounded-full mx-auto"></div>
        <div className="h-6 bg-gray-200 rounded w-24 mx-auto"></div>
      </div>
      
      {/* Components */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between">
              <div className="h-5 bg-gray-200 rounded w-24"></div>
              <div className="h-6 bg-gray-200 rounded w-16"></div>
            </div>
            <div className="mt-2 h-2 bg-gray-200 rounded w-full"></div>
          </div>
        ))}
      </div>
    </div>
  ),

  // Agent management skeleton
  AgentManagement: () => (
    <div className="animate-pulse space-y-6">
      <div className="flex justify-between items-center">
        <div className="h-8 bg-gray-200 rounded w-32"></div>
        <div className="h-10 bg-gray-200 rounded w-28"></div>
      </div>
      
      {/* Agent grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="bg-white p-6 rounded-lg border border-gray-200">
            <div className="flex items-center space-x-4 mb-4">
              <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
              <div>
                <div className="h-5 bg-gray-200 rounded w-24 mb-1"></div>
                <div className="h-4 bg-gray-200 rounded w-16"></div>
              </div>
            </div>
            <div className="space-y-2">
              <div className="h-3 bg-gray-200 rounded w-full"></div>
              <div className="h-3 bg-gray-200 rounded w-3/4"></div>
            </div>
            <div className="mt-4 flex justify-between">
              <div className="h-8 bg-gray-200 rounded w-20"></div>
              <div className="h-8 bg-gray-200 rounded w-16"></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  ),

  // Table skeleton
  Table: ({ rows = 5, columns = 4 }) => (
    <div className="animate-pulse">
      {/* Header */}
      <div className="bg-gray-50 p-4 rounded-t-lg border border-gray-200">
        <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
          {[...Array(columns)].map((_, i) => (
            <div key={i} className="h-4 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
      
      {/* Rows */}
      <div className="bg-white border-x border-b border-gray-200 rounded-b-lg">
        {[...Array(rows)].map((_, rowIndex) => (
          <div key={rowIndex} className="p-4 border-b border-gray-100 last:border-b-0">
            <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
              {[...Array(columns)].map((_, colIndex) => (
                <div key={colIndex} className="h-4 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  ),

  // Chart skeleton
  Chart: () => (
    <div className="animate-pulse space-y-4">
      <div className="h-6 bg-gray-200 rounded w-32"></div>
      <div className="h-64 bg-gray-200 rounded"></div>
    </div>
  )
};

// ==================
// LOADING INDICATORS
// ==================

export const LoadingIndicators = {
  // Spinner with text
  Spinner: ({ text = 'Loading...', size = 'md' }: { text?: string; size?: 'sm' | 'md' | 'lg' }) => {
    const sizeClasses = {
      sm: 'h-4 w-4',
      md: 'h-6 w-6',
      lg: 'h-8 w-8'
    };

    return (
      <div className="flex items-center justify-center space-x-2">
        <Loader2 className={`animate-spin ${sizeClasses[size]} text-blue-600`} />
        <span className="text-gray-600">{text}</span>
      </div>
    );
  },

  // Full page loading
  FullPage: ({ text = 'Loading Application...' }) => (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">{text}</h2>
        <p className="text-gray-600">Please wait while we load the system...</p>
      </div>
    </div>
  ),

  // Inline loading for buttons
  Button: ({ text = 'Loading...' }) => (
    <div className="flex items-center space-x-2">
      <Loader2 className="animate-spin h-4 w-4" />
      <span>{text}</span>
    </div>
  ),

  // Overlay loading
  Overlay: ({ text = 'Processing...', transparent = false }) => (
    <div className={`absolute inset-0 flex items-center justify-center z-50 ${
      transparent ? 'bg-white/70' : 'bg-white'
    } backdrop-blur-sm`}>
      <div className="text-center">
        <Loader2 className="animate-spin h-8 w-8 text-blue-600 mx-auto mb-2" />
        <p className="text-gray-600">{text}</p>
      </div>
    </div>
  ),

  // Progress bar
  Progress: ({ progress, text }: { progress: number; text?: string }) => (
    <div className="space-y-2">
      {text && <p className="text-sm text-gray-600">{text}</p>}
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
        ></div>
      </div>
      <p className="text-xs text-gray-500 text-right">{progress.toFixed(0)}%</p>
    </div>
  ),

  // Dots loading
  Dots: () => (
    <div className="flex space-x-1">
      {[...Array(3)].map((_, i) => (
        <div
          key={i}
          className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"
          style={{ animationDelay: `${i * 200}ms` }}
        ></div>
      ))}
    </div>
  ),

  // Pulse animation
  Pulse: ({ className = "w-full h-4 bg-gray-200 rounded" }) => (
    <div className={`animate-pulse ${className}`}></div>
  )
};

// ======================
// COMPONENT-SPECIFIC LOADING STATES
// ======================

export const ComponentLoadingStates = {
  // Agent switcher loading
  AgentSwitcher: () => (
    <div className="flex items-center space-x-2 px-3 py-2 bg-gray-50 rounded-lg">
      <Zap size={16} className="text-gray-400" />
      <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-20"></div>
      </div>
      <LoadingIndicators.Dots />
    </div>
  ),

  // System health loading
  SystemHealth: () => (
    <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-gray-100">
      <Activity size={14} className="text-gray-400" />
      <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-16"></div>
      </div>
    </div>
  ),

  // Project selector loading
  ProjectSelector: () => (
    <div className="flex items-center space-x-2 px-3 py-2 bg-gray-50 rounded-lg">
      <GitBranch size={16} className="text-gray-400" />
      <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-24"></div>
      </div>
    </div>
  ),

  // Dashboard stats loading
  DashboardStats: () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {[
        { icon: Users, label: 'Active Agents' },
        { icon: GitBranch, label: 'Branches' },
        { icon: Activity, label: 'Tasks' },
        { icon: BarChart3, label: 'Performance' }
      ].map((stat, i) => (
        <div key={i} className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-20 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-16"></div>
              </div>
            </div>
            <stat.icon size={24} className="text-gray-300" />
          </div>
        </div>
      ))}
    </div>
  ),

  // Card loading
  Card: ({ title, hasActions = false }: { title?: string; hasActions?: boolean }) => (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-32"></div>
        </div>
        {hasActions && (
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-20"></div>
          </div>
        )}
      </div>
      <div className="animate-pulse space-y-3">
        <div className="h-4 bg-gray-200 rounded w-full"></div>
        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    </div>
  )
};

// =======================
// HOC FOR LOADING STATES
// =======================

export function withLoadingState<T extends {}>(
  Component: React.ComponentType<T>,
  LoadingComponent: React.ComponentType<any>
) {
  return function WithLoadingStateComponent(props: T & { isLoading?: boolean; loadingProps?: any }) {
    const { isLoading, loadingProps, ...componentProps } = props;
    
    if (isLoading) {
      return <LoadingComponent {...loadingProps} />;
    }
    
    return <Component {...(componentProps as T)} />;
  };
}

// Conditional loading wrapper
export function LoadingWrapper({ 
  isLoading, 
  skeleton, 
  children,
  fallback 
}: {
  isLoading: boolean;
  skeleton?: React.ComponentType<any>;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  if (isLoading) {
    if (skeleton) {
      const SkeletonComponent = skeleton;
      return <SkeletonComponent />;
    }
    
    return fallback || <LoadingIndicators.Spinner />;
  }
  
  return <>{children}</>;
}

export default {
  SkeletonComponents,
  LoadingIndicators,
  ComponentLoadingStates,
  withLoadingState,
  LoadingWrapper
};