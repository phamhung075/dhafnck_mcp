/**
 * Custom hook for managing System Health Dashboard state and operations
 * Provides comprehensive health monitoring, performance metrics collection, and alert management
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { ComplianceStatus, ConnectionStatus, mcpApi } from '../api/enhanced';
import { PerformanceMetrics, SystemAlert } from '../components/SystemHealthDashboard';

export interface HealthDashboardState {
  connectionStatus: ConnectionStatus | null;
  complianceStatus: ComplianceStatus | null;
  performanceMetrics: PerformanceMetrics | null;
  alerts: SystemAlert[];
  healthHistory: HealthHistoryEntry[];
  overallHealthScore: number;
  lastUpdate: string;
  autoRefresh: boolean;
  refreshInterval: number;
  loading: boolean;
  error: string | null;
}

export interface HealthHistoryEntry {
  timestamp: string;
  overall_score: number;
  connection_score: number;
  compliance_score: number;
  performance_score: number;
  alert_count: number;
}

interface WebVitals {
  fcp: number; // First Contentful Paint
  lcp: number; // Largest Contentful Paint
  cls: number; // Cumulative Layout Shift
  fid: number; // First Input Delay
  ttfb: number; // Time to First Byte
}

export function useHealthDashboard() {
  const [state, setState] = useState<HealthDashboardState>({
    connectionStatus: null,
    complianceStatus: null,
    performanceMetrics: null,
    alerts: [],
    healthHistory: [],
    overallHealthScore: 0,
    lastUpdate: '',
    autoRefresh: true,
    refreshInterval: 30000,
    loading: true,
    error: null
  });

  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isComponentMounted = useRef(true);

  /**
   * Collect frontend performance metrics (Web Vitals)
   */
  const collectWebVitals = useCallback((): WebVitals => {
    // Default values for Web Vitals
    let webVitals: WebVitals = {
      fcp: 0,
      lcp: 0,
      cls: 0,
      fid: 0,
      ttfb: 0
    };

    // Try to get performance data from browser
    if (typeof window !== 'undefined' && 'performance' in window) {
      const navigation = window.performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const paint = window.performance.getEntriesByType('paint');

      if (navigation) {
        webVitals.ttfb = navigation.responseStart - navigation.requestStart;
      }

      // First Contentful Paint
      const fcpEntry = paint.find(entry => entry.name === 'first-contentful-paint');
      if (fcpEntry) {
        webVitals.fcp = fcpEntry.startTime;
      }

      // Largest Contentful Paint (approximation)
      webVitals.lcp = webVitals.fcp * 1.2; // Rough estimation

      // Cumulative Layout Shift (mock value for demo)
      webVitals.cls = Math.random() * 0.1;

      // First Input Delay (mock value for demo)
      webVitals.fid = Math.random() * 100;
    }

    return webVitals;
  }, []);

  /**
   * Collect comprehensive performance metrics
   */
  const collectPerformanceMetrics = useCallback(async (): Promise<PerformanceMetrics> => {
    const webVitals = collectWebVitals();
    const apiMetrics = mcpApi.getPerformanceMetrics();

    // Calculate page load time
    const pageLoadTime = typeof window !== 'undefined' && window.performance.timing
      ? window.performance.timing.loadEventEnd - window.performance.timing.navigationStart
      : 0;

    return {
      // Base performance metrics from API wrapper
      requestCount: apiMetrics.requestCount,
      successCount: apiMetrics.successCount,
      errorCount: apiMetrics.errorCount,
      averageResponseTime: apiMetrics.averageResponseTime,
      queueLength: apiMetrics.queueLength,
      memoryUsage: apiMetrics.memoryUsage,

      // Frontend metrics
      frontend: {
        page_load_time: pageLoadTime,
        first_contentful_paint: webVitals.fcp,
        largest_contentful_paint: webVitals.lcp,
        cumulative_layout_shift: webVitals.cls
      },

      // API metrics (enhanced)
      api: {
        avg_response_time: apiMetrics.averageResponseTime,
        p95_response_time: apiMetrics.averageResponseTime * 1.5, // Approximation
        error_rate: apiMetrics.requestCount > 0 ? (apiMetrics.errorCount / apiMetrics.requestCount) * 100 : 0,
        success_rate: apiMetrics.requestCount > 0 ? (apiMetrics.successCount / apiMetrics.requestCount) * 100 : 100
      },

      // System metrics
      system: {
        memory_usage: apiMetrics.memoryUsage || 0,
        cache_hit_ratio: 85 + Math.random() * 10, // Mock data
        active_connections: apiMetrics.queueLength + Math.floor(Math.random() * 5)
      }
    };
  }, [collectWebVitals]);

  /**
   * Calculate overall health score from individual components
   */
  const calculateOverallHealth = useCallback((
    connectionStatus: ConnectionStatus | null,
    complianceStatus: ComplianceStatus | null,
    performanceMetrics: PerformanceMetrics | null
  ): number => {
    let connectionScore = 0;
    let complianceScore = 0;
    let performanceScore = 0;

    // Connection health score
    if (connectionStatus) {
      switch (connectionStatus.status) {
        case 'healthy':
          connectionScore = 100;
          break;
        case 'degraded':
          connectionScore = 70;
          break;
        case 'down':
          connectionScore = 0;
          break;
        default:
          connectionScore = 50;
      }
    }

    // Compliance score
    if (complianceStatus) {
      complianceScore = complianceStatus.compliance_score * 100;
    }

    // Performance score
    if (performanceMetrics) {
      performanceScore = performanceMetrics.api.success_rate;
    }

    // Weighted average
    const weights = { connection: 0.4, compliance: 0.3, performance: 0.3 };
    return Math.round(
      connectionScore * weights.connection +
      complianceScore * weights.compliance +
      performanceScore * weights.performance
    );
  }, []);

  /**
   * Generate mock alerts for demonstration
   */
  const generateMockAlerts = useCallback((): SystemAlert[] => {
    const now = new Date().toISOString();
    const alerts: SystemAlert[] = [];

    // Add some sample alerts based on current status
    if (state.connectionStatus?.status === 'degraded') {
      alerts.push({
        id: 'conn-001',
        type: 'connection',
        severity: 'warning',
        title: 'Connection Performance Degraded',
        description: 'API response times are higher than normal',
        timestamp: now,
        status: 'active',
        affected_components: ['API Gateway', 'MCP Server'],
        suggested_actions: ['Check network connectivity', 'Review server logs']
      });
    }

    if (state.complianceStatus && state.complianceStatus.compliance_score < 0.8) {
      alerts.push({
        id: 'comp-001',
        type: 'compliance',
        severity: 'error',
        title: 'Compliance Score Below Threshold',
        description: 'System compliance score has dropped below acceptable levels',
        timestamp: now,
        status: 'active',
        affected_components: ['Security Module', 'Audit System'],
        suggested_actions: ['Review security policies', 'Run compliance scan']
      });
    }

    if (state.performanceMetrics && state.performanceMetrics.api.error_rate > 5) {
      alerts.push({
        id: 'perf-001',
        type: 'performance',
        severity: 'warning',
        title: 'High Error Rate Detected',
        description: `API error rate is ${state.performanceMetrics.api.error_rate.toFixed(1)}%`,
        timestamp: now,
        status: 'active',
        affected_components: ['API Layer', 'Task Management'],
        suggested_actions: ['Check API logs', 'Review recent deployments']
      });
    }

    return alerts;
  }, [state.connectionStatus, state.complianceStatus, state.performanceMetrics]);

  /**
   * Add entry to health history for trending
   */
  const addHealthHistoryEntry = useCallback((
    overallScore: number,
    connectionStatus: ConnectionStatus | null,
    complianceStatus: ComplianceStatus | null,
    performanceMetrics: PerformanceMetrics | null,
    alertCount: number
  ) => {
    const entry: HealthHistoryEntry = {
      timestamp: new Date().toISOString(),
      overall_score: overallScore,
      connection_score: connectionStatus?.status === 'healthy' ? 100 : 
                      connectionStatus?.status === 'degraded' ? 70 : 0,
      compliance_score: (complianceStatus?.compliance_score || 0) * 100,
      performance_score: performanceMetrics?.api.success_rate || 0,
      alert_count: alertCount
    };

    setState(prevState => ({
      ...prevState,
      healthHistory: [...prevState.healthHistory.slice(-23), entry] // Keep last 24 hours
    }));
  }, []);

  /**
   * Main health refresh function
   */
  const refreshHealth = useCallback(async (): Promise<void> => {
    if (!isComponentMounted.current) return;

    setState(prevState => ({ ...prevState, loading: true, error: null }));

    try {
      // Fetch health data in parallel
      const [connectionResponse, complianceResponse, performanceMetrics] = await Promise.allSettled([
        mcpApi.getSystemHealth(true),
        mcpApi.manageCompliance('get_compliance_dashboard'),
        collectPerformanceMetrics()
      ]);

      // Process results
      const connectionStatus = connectionResponse.status === 'fulfilled' ? connectionResponse.value : null;
      
      const complianceStatus = complianceResponse.status === 'fulfilled' 
        ? complianceResponse.value?.data || null 
        : null;

      const metrics = performanceMetrics.status === 'fulfilled' ? performanceMetrics.value : null;

      // Calculate overall health score
      const overallScore = calculateOverallHealth(connectionStatus, complianceStatus, metrics);

      // Generate alerts
      const alerts = generateMockAlerts();

      // Add to history
      addHealthHistoryEntry(overallScore, connectionStatus, complianceStatus, metrics, alerts.length);

      // Update state
      if (isComponentMounted.current) {
        setState(prevState => ({
          ...prevState,
          connectionStatus,
          complianceStatus,
          performanceMetrics: metrics,
          alerts,
          overallHealthScore: overallScore,
          lastUpdate: new Date().toISOString(),
          loading: false,
          error: null
        }));
      }

    } catch (error: any) {
      console.error('Failed to refresh health:', error);
      
      if (isComponentMounted.current) {
        setState(prevState => ({
          ...prevState,
          loading: false,
          error: error.message || 'Failed to refresh health data'
        }));
      }
    }
  }, [calculateOverallHealth, collectPerformanceMetrics, generateMockAlerts, addHealthHistoryEntry]);

  /**
   * Start automatic refresh
   */
  const startAutoRefresh = useCallback((interval: number) => {
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
    }
    
    refreshIntervalRef.current = setInterval(() => {
      refreshHealth();
    }, interval);
    
    setState(prevState => ({ 
      ...prevState, 
      autoRefresh: true, 
      refreshInterval: interval 
    }));
  }, [refreshHealth]);

  /**
   * Stop automatic refresh
   */
  const stopAutoRefresh = useCallback(() => {
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
      refreshIntervalRef.current = null;
    }
    
    setState(prevState => ({ 
      ...prevState, 
      autoRefresh: false 
    }));
  }, []);

  /**
   * Run system diagnostics
   */
  const runDiagnostics = useCallback(async (): Promise<void> => {
    try {
      setState(prevState => ({ ...prevState, loading: true }));

      // Run comprehensive diagnostics
      const [connectionHealth, serverCapabilities] = await Promise.allSettled([
        mcpApi.manageConnection('connection_health'),
        mcpApi.manageConnection('server_capabilities')
      ]);

      console.log('Diagnostics completed:', {
        connectionHealth: connectionHealth.status === 'fulfilled' ? connectionHealth.value : null,
        serverCapabilities: serverCapabilities.status === 'fulfilled' ? serverCapabilities.value : null
      });

      // Refresh health after diagnostics
      await refreshHealth();

    } catch (error: any) {
      console.error('Diagnostics failed:', error);
      setState(prevState => ({
        ...prevState,
        loading: false,
        error: 'Diagnostics failed: ' + (error.message || 'Unknown error')
      }));
    }
  }, [refreshHealth]);

  /**
   * Resolve an alert
   */
  const resolveAlert = useCallback(async (alertId: string): Promise<void> => {
    setState(prevState => ({
      ...prevState,
      alerts: prevState.alerts.map(alert => 
        alert.id === alertId 
          ? { ...alert, status: 'resolved' as const }
          : alert
      )
    }));
  }, []);

  /**
   * Set refresh interval and restart auto-refresh if active
   */
  const setRefreshInterval = useCallback((interval: number) => {
    setState(prevState => ({ ...prevState, refreshInterval: interval }));
    
    if (state.autoRefresh) {
      startAutoRefresh(interval);
    }
  }, [state.autoRefresh, startAutoRefresh]);

  /**
   * Toggle auto-refresh
   */
  const toggleAutoRefresh = useCallback(() => {
    if (state.autoRefresh) {
      stopAutoRefresh();
    } else {
      startAutoRefresh(state.refreshInterval);
    }
  }, [state.autoRefresh, state.refreshInterval, startAutoRefresh, stopAutoRefresh]);

  // Initial health check and setup auto-refresh
  useEffect(() => {
    // Initial health check
    refreshHealth();

    // Start auto-refresh if enabled
    if (state.autoRefresh) {
      startAutoRefresh(state.refreshInterval);
    }

    // Cleanup on unmount
    return () => {
      isComponentMounted.current = false;
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, []); // Run only once on mount

  // Auto-refresh effect
  useEffect(() => {
    if (state.autoRefresh && !refreshIntervalRef.current) {
      startAutoRefresh(state.refreshInterval);
    } else if (!state.autoRefresh && refreshIntervalRef.current) {
      stopAutoRefresh();
    }
  }, [state.autoRefresh, state.refreshInterval, startAutoRefresh, stopAutoRefresh]);

  return {
    // State
    ...state,

    // Actions
    refreshHealth,
    runDiagnostics,
    resolveAlert,
    startAutoRefresh,
    stopAutoRefresh,
    toggleAutoRefresh,
    setRefreshInterval,

    // Computed properties
    isHealthy: state.overallHealthScore >= 85,
    hasWarnings: state.overallHealthScore >= 70 && state.overallHealthScore < 85,
    hasCriticalIssues: state.overallHealthScore < 70,
    activeAlerts: state.alerts.filter(alert => alert.status === 'active'),
    criticalAlerts: state.alerts.filter(alert => alert.severity === 'critical' && alert.status === 'active')
  };
}

export type HealthDashboardHook = ReturnType<typeof useHealthDashboard>;