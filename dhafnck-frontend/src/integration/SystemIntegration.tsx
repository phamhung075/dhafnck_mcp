/**
 * System Integration Manager
 * Provides unified state management, real-time data synchronization,
 * and cross-component communication for the entire DhafnckMCP frontend
 */

import React, { ReactNode, useEffect, useState, createContext, useContext } from 'react';
import { Provider } from 'react-redux';
import { store, systemActions, sessionActions, dataActions, useAppDispatch, useAppSelector } from '../store/store';
import { ErrorBoundary } from '../components/common/ErrorBoundary';
import { NotificationSystem } from '../components/common/NotificationSystem';
import { mcpApi } from '../api/enhanced';
import type { 
  ConnectionStatus, 
  SystemHealthStatus, 
  Agent, 
  Project, 
  HierarchicalContext,
  ApiRequest,
  PerformanceMetrics
} from '../types/application';

// Global System State Interface
export interface GlobalSystemState {
  api: {
    connectionStatus: ConnectionStatus;
    requestQueue: ApiRequest[];
    errorLog: any[];
    performanceMetrics: PerformanceMetrics;
  };
  
  agents: {
    available: Agent[];
    current: Agent | null;
    assignments: Record<string, any>;
    performance: Record<string, any>;
  };
  
  contexts: {
    hierarchical: HierarchicalContext[];
    resolved: Record<string, any>;
    delegationQueue: any[];
    validationResults: Record<string, any>;
  };
  
  monitoring: {
    systemHealth: SystemHealthStatus | null;
    compliance: any;
    performance: PerformanceMetrics;
    alerts: any[];
  };
  
  projects: {
    list: Project[];
    selected: Project | null;
    branches: Record<string, any[]>;
    analytics: Record<string, any>;
    health: Record<string, any>;
  };
  
  ui: {
    theme: 'light' | 'dark' | 'system';
    layout: any;
    navigation: any;
    modals: any;
    notifications: any;
  };
}

// System Integration Context
interface SystemIntegrationContext {
  state: GlobalSystemState;
  actions: {
    refreshSystemHealth: () => Promise<void>;
    switchAgent: (agent: Agent) => Promise<void>;
    switchProject: (project: Project) => Promise<void>;
    resolveContext: (contextId: string, level: string) => Promise<void>;
    syncRealTimeData: () => Promise<void>;
  };
  performance: {
    measureRenderTime: (componentName: string) => void;
    optimizeState: () => Promise<void>;
    analyzeMemoryUsage: () => any;
  };
}

const SystemIntegrationContextProvider = createContext<SystemIntegrationContext | null>(null);

// MCP Polling Manager for Real-time Updates (Replaces WebSocket)
class McpPollingManager {
  private pollingInterval: NodeJS.Timeout | null = null;
  private healthCheckInterval = 300000; // 5 minutes (reduced from 30 seconds)
  private dispatch: any;
  private isPolling = false;
  private lastHealthCheck: number = 0;
  private healthCheckCache: any = null;

  constructor(dispatch: any) {
    this.dispatch = dispatch;
    // Disable polling for now to fix frozen page
    // this.startPolling();
  }

  private async startPolling() {
    if (this.isPolling) return;
    
    this.isPolling = true;
    
    // Initial health check
    await this.checkSystemHealth();
    
    // Set up polling interval
    this.pollingInterval = setInterval(async () => {
      await this.checkSystemHealth();
      await this.checkComplianceStatus();
    }, this.healthCheckInterval);
    
    // Set connection status
    this.dispatch(systemActions.setConnectionStatus({
      status: 'healthy',
      latency: 0,
      uptime_percentage: 100,
      active_connections: 1,
      last_check: new Date().toISOString(),
      error_rate: 0
    }));
  }

  private async checkSystemHealth() {
    // Check if we have a recent cached result (within 1 minute)
    const now = Date.now();
    if (this.healthCheckCache && (now - this.lastHealthCheck) < 60000) {
      console.log('Using cached health check result');
      return;
    }

    try {
      const response = await mcpApi.manageConnection('health_check', { include_details: true });
      if (response.data) {
        this.lastHealthCheck = now;
        this.healthCheckCache = response.data;
        this.dispatch(systemActions.setSystemHealth(response.data));
      }
    } catch (error) {
      console.error('Health check failed:', error);
      this.dispatch(systemActions.setConnectionStatus({
        status: 'degraded',
        latency: 0,
        uptime_percentage: 50,
        active_connections: 0,
        last_check: new Date().toISOString(),
        error_rate: 50
      }));
    }
  }

  private async checkComplianceStatus() {
    try {
      const response = await mcpApi.manageCompliance('get_compliance_dashboard');
      if (response.data) {
        this.dispatch(systemActions.setComplianceStatus(response.data));
      }
    } catch (error) {
      console.error('Compliance check failed:', error);
    }
  }

  public stopPolling() {
    this.isPolling = false;
    
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
    
    // Set disconnected status
    this.dispatch(systemActions.setConnectionStatus({
      status: 'critical',
      latency: 0,
      uptime_percentage: 0,
      active_connections: 0,
      last_check: new Date().toISOString(),
      error_rate: 0
    }));
  }

  public async refresh() {
    // Manual refresh
    await this.checkSystemHealth();
    await this.checkComplianceStatus();
  }

  public disconnect() {
    this.stopPolling();
  }
}

// Performance Monitor
class PerformanceMonitor {
  private renderTimes: Record<string, number[]> = {};
  private memoryUsage: Array<{
    used: number;
    total: number;
    limit: number;
    timestamp: number;
  }> = [];

  measureRenderTime(componentName: string) {
    const startTime = performance.now();
    
    return () => {
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      if (!this.renderTimes[componentName]) {
        this.renderTimes[componentName] = [];
      }
      
      this.renderTimes[componentName].push(renderTime);
      
      // Keep only last 50 measurements
      if (this.renderTimes[componentName].length > 50) {
        this.renderTimes[componentName] = this.renderTimes[componentName].slice(-50);
      }
      
      // Log slow renders
      if (renderTime > 100) {
        console.warn(`Slow render detected in ${componentName}: ${renderTime.toFixed(2)}ms`);
      }
    };
  }

  analyzeMemoryUsage() {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      const usage = {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize,
        limit: memory.jsHeapSizeLimit,
        timestamp: Date.now()
      };
      
      this.memoryUsage.push(usage);
      
      // Keep only last 100 measurements
      if (this.memoryUsage.length > 100) {
        this.memoryUsage = this.memoryUsage.slice(-100);
      }
      
      return usage;
    }
    
    return null;
  }

  getPerformanceReport() {
    const report: any = {
      renderTimes: {},
      memoryTrend: this.memoryUsage,
      timestamp: new Date().toISOString()
    };

    // Calculate average render times
    Object.keys(this.renderTimes).forEach(componentName => {
      const times = this.renderTimes[componentName];
      const average = times.reduce((sum, time) => sum + time, 0) / times.length;
      const max = Math.max(...times);
      const min = Math.min(...times);
      
      report.renderTimes[componentName] = {
        average: average.toFixed(2),
        max: max.toFixed(2),
        min: min.toFixed(2),
        count: times.length
      };
    });

    return report;
  }
}

// System Integration Provider Component
function SystemIntegrationProvider({ children }: { children: ReactNode }) {
  const dispatch = useAppDispatch();
  const systemState = useAppSelector(state => state.system);
  const sessionState = useAppSelector(state => state.session);
  const dataState = useAppSelector(state => state.data);
  const uiState = useAppSelector(state => state.ui);

  const [mcpPollingManager] = useState(() => new McpPollingManager(dispatch));
  const [performanceMonitor] = useState(() => new PerformanceMonitor());
  const [isInitialized, setIsInitialized] = useState(true); // Skip initialization for now

  // Initialize system on mount
  useEffect(() => {
    const initializeSystem = async () => {
      try {
        dispatch(systemActions.setLoading({ key: 'system_initialization', loading: true }));

        // 1. Health check
        const healthResponse = await mcpApi.manageConnection('health_check', { include_details: true });
        if (healthResponse.data) {
          dispatch(systemActions.setSystemHealth(healthResponse.data));
        }

        // 2. Load initial data
        const [projectsResponse, rulesResponse] = await Promise.all([
          mcpApi.manageProject('list'),
          mcpApi.manageRule('list')
        ]);

        if (projectsResponse.data) {
          dispatch(dataActions.setProjects(projectsResponse.data));
        }
        if (rulesResponse.data) {
          dispatch(dataActions.setRules(rulesResponse.data));
        }

        // 3. Set up real-time monitoring
        setInterval(() => {
          performanceMonitor.analyzeMemoryUsage();
        }, 30000); // Every 30 seconds

        setIsInitialized(true);
      } catch (error) {
        console.error('System initialization failed:', error);
        dispatch(systemActions.setError({
          key: 'system_initialization',
          error: 'Failed to initialize system. Please refresh and try again.'
        }));
      } finally {
        dispatch(systemActions.setLoading({ key: 'system_initialization', loading: false }));
      }
    };

    initializeSystem();

    // Cleanup on unmount
    return () => {
      mcpPollingManager.disconnect();
    };
  }, [dispatch, mcpPollingManager, performanceMonitor]);

  // Context value
  const contextValue: SystemIntegrationContext = {
    state: {
      api: {
        connectionStatus: systemState.connection,
        requestQueue: [],
        errorLog: [],
        performanceMetrics: {
          requestCount: 0,
          successCount: 0,
          errorCount: 0,
          averageResponseTime: 0,
          queueLength: 0
        }
      },
      agents: {
        available: Object.values(dataState.agents).flat(),
        current: sessionState.currentAgent,
        assignments: {},
        performance: {}
      },
      contexts: {
        hierarchical: dataState.contexts,
        resolved: {},
        delegationQueue: [],
        validationResults: {}
      },
      monitoring: {
        systemHealth: systemState.health,
        compliance: systemState.compliance,
        performance: {
          requestCount: 0,
          successCount: 0,
          errorCount: 0,
          averageResponseTime: 0,
          queueLength: 0
        },
        alerts: []
      },
      projects: {
        list: dataState.projects,
        selected: sessionState.selectedProject,
        branches: dataState.branches,
        analytics: {},
        health: {}
      },
      ui: {
        theme: uiState.theme === 'auto' ? 'system' : uiState.theme as 'light' | 'dark' | 'system',
        layout: {},
        navigation: { currentView: uiState.currentView },
        modals: uiState.modalStack,
        notifications: uiState.notifications
      }
    },
    actions: {
      refreshSystemHealth: async () => {
        try {
          const healthResponse = await mcpApi.manageConnection('health_check', { include_details: true });
          if (healthResponse.data) {
            dispatch(systemActions.setSystemHealth(healthResponse.data));
          }
        } catch (error) {
          console.error('Failed to refresh system health:', error);
        }
      },
      switchAgent: async (agent: Agent) => {
        try {
          await mcpApi.callAgent(agent.name);
          dispatch(sessionActions.setCurrentAgent(agent));
          // Agent switch is handled through MCP protocol, no need for WebSocket message
        } catch (error) {
          console.error('Failed to switch agent:', error);
          throw error;
        }
      },
      switchProject: async (project: Project) => {
        try {
          dispatch(sessionActions.setSelectedProject(project));
          
          // Load project-specific data
          const [branchesResponse, agentsResponse] = await Promise.all([
            mcpApi.manageGitBranch('list', { project_id: project.id }),
            mcpApi.manageAgent('list', { project_id: project.id })
          ]);
          
          if (branchesResponse.data) {
            dispatch(dataActions.setBranches({ projectId: project.id, branches: branchesResponse.data }));
          }
          if (agentsResponse.data) {
            dispatch(dataActions.setAgents({ projectId: project.id, agents: agentsResponse.data }));
          }
          
          // Project switch is handled through MCP protocol, no need for WebSocket message
        } catch (error) {
          console.error('Failed to switch project:', error);
          throw error;
        }
      },
      resolveContext: async (contextId: string, level: string) => {
        try {
          const contextResponse = await mcpApi.manageHierarchicalContext('resolve', {
            context_id: contextId,
            level: level
          });
          
          if (contextResponse.data) {
            dispatch(dataActions.addContext(contextResponse.data));
          }
        } catch (error) {
          console.error('Failed to resolve context:', error);
          throw error;
        }
      },
      syncRealTimeData: async () => {
        try {
          // Refresh all critical data
          const [healthResponse, projectsResponse] = await Promise.all([
            mcpApi.manageConnection('health_check', { include_details: true }),
            mcpApi.manageProject('list')
          ]);
          
          if (healthResponse.data) {
            dispatch(systemActions.setSystemHealth(healthResponse.data));
          }
          if (projectsResponse.data) {
            dispatch(dataActions.setProjects(projectsResponse.data));
          }
        } catch (error) {
          console.error('Failed to sync real-time data:', error);
        }
      }
    },
    performance: {
      measureRenderTime: (componentName: string) => {
        return performanceMonitor.measureRenderTime(componentName);
      },
      optimizeState: async () => {
        // State cleanup and optimization logic
        console.log('Optimizing state...');
        
        // Clear old notifications
        dispatch(systemActions.clearNotifications());
        
        // Clear old UI notifications
        dispatch({ type: 'ui/clearUINotifications' });
        
        // Generate performance report
        const report = performanceMonitor.getPerformanceReport();
        console.log('Performance Report:', report);
      },
      analyzeMemoryUsage: () => {
        return performanceMonitor.analyzeMemoryUsage();
      }
    }
  };

  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Initializing System Integration
          </h2>
          <p className="text-gray-600">
            Setting up unified state management and real-time connections...
          </p>
        </div>
      </div>
    );
  }

  return (
    <SystemIntegrationContextProvider.Provider value={contextValue}>
      <ErrorBoundary>
        <NotificationSystem />
        {children}
      </ErrorBoundary>
    </SystemIntegrationContextProvider.Provider>
  );
}

// Main System Integration Component
interface SystemIntegrationProps {
  children: ReactNode;
}

export function SystemIntegration({ children }: SystemIntegrationProps) {
  return (
    <Provider store={store}>
      <SystemIntegrationProvider>
        {children}
      </SystemIntegrationProvider>
    </Provider>
  );
}

// Hook to use System Integration Context
export function useSystemIntegration() {
  const context = useContext(SystemIntegrationContextProvider);
  if (!context) {
    throw new Error('useSystemIntegration must be used within SystemIntegration');
  }
  return context;
}

// Performance HOC
export function withPerformanceMonitoring<T extends {}>(
  Component: React.ComponentType<T>,
  componentName: string
) {
  return React.memo(function WithPerformanceMonitoring(props: T) {
    const { performance } = useSystemIntegration();
    
    useEffect(() => {
      const endMeasurement = performance.measureRenderTime(componentName);
      return endMeasurement;
    });
    
    return <Component {...props} />;
  });
}

export default SystemIntegration;