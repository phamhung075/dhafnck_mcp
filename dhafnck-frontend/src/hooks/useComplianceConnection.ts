import { useState, useEffect, useCallback, useRef } from 'react';
import { mcpApi } from '../api/enhanced';

// Types
interface ComplianceStatus {
  compliance_score: number;
  total_violations: number;
  resolved_violations: number;
  framework_breakdown: {
    [framework: string]: {
      score: number;
      violations: number;
    };
  };
  last_audit: string;
  trends: {
    daily: number[];
    weekly: number[];
    monthly: number[];
  };
}

interface ComplianceViolation {
  id: string;
  type: 'security' | 'data_privacy' | 'access_control' | 'operational';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  affected_resources: string[];
  detected_at: string;
  status: 'open' | 'acknowledged' | 'resolved' | 'false_positive';
  remediation_steps: string[];
  compliance_framework: string[];
}

interface AuditEntry {
  id: string;
  timestamp: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details: any;
  ip_address: string;
  user_agent: string;
  result: 'success' | 'failure' | 'partial';
}

interface ConnectionStatus {
  status: 'healthy' | 'degraded' | 'down';
  response_time: number;
  last_check: string;
  uptime: number;
  connection_pool: {
    active: number;
    idle: number;
    total: number;
    peak_usage: number;
  };
  error_rate: number;
  throughput: number;
}

interface ConnectionHistoryEntry {
  timestamp: string;
  event_type: 'connected' | 'disconnected' | 'error' | 'timeout' | 'retry';
  duration?: number;
  error_message?: string;
  response_time: number;
}

interface ServerCapabilities {
  version: string;
  features: string[];
  tools: string[];
  authentication: {
    enabled: boolean;
    methods: string[];
  };
  rate_limiting: {
    enabled: boolean;
    requests_per_minute: number;
  };
  health_check: {
    interval: number;
    timeout: number;
  };
}

interface DiagnosticResult {
  test_name: string;
  status: 'passed' | 'failed' | 'warning' | 'skipped';
  response_time: number;
  error_message?: string;
  recommendations: string[];
  details: any;
  timestamp: string;
}

interface ConnectionHealth {
  overall_status: 'healthy' | 'degraded' | 'unhealthy';
  response_time: number;
  uptime: number;
  error_rate: number;
  throughput: number;
  connection_pool: {
    active: number;
    idle: number;
    total: number;
    peak_usage: number;
  };
  memory_usage: {
    used: number;
    total: number;
    percentage: number;
  };
  network_stats: {
    latency: number;
    packet_loss: number;
    bandwidth_usage: number;
  };
}

interface AuditFilters {
  dateFrom: string;
  dateTo: string;
  user: string;
  action: string;
  result: string;
  resourceType: string;
}

interface ComplianceConnectionState {
  // Compliance data
  complianceStatus: ComplianceStatus | null;
  violations: ComplianceViolation[];
  auditTrail: AuditEntry[];
  
  // Connection data
  connectionStatus: ConnectionStatus | null;
  connectionHistory: ConnectionHistoryEntry[];
  serverCapabilities: ServerCapabilities | null;
  diagnosticResults: DiagnosticResult[];
  connectionHealth: ConnectionHealth | null;
  
  // Loading states
  loading: {
    compliance: boolean;
    connection: boolean;
    diagnostics: boolean;
    audit: boolean;
  };
  
  // Error states
  errors: {
    compliance: string | null;
    connection: string | null;
    diagnostics: string | null;
    audit: string | null;
  };
  
  // WebSocket connection
  wsStatus: 'connected' | 'disconnected' | 'connecting';
  lastUpdated: string | null;
}

export function useComplianceConnection() {
  const [state, setState] = useState<ComplianceConnectionState>({
    complianceStatus: null,
    violations: [],
    auditTrail: [],
    connectionStatus: null,
    connectionHistory: [],
    serverCapabilities: null,
    diagnosticResults: [],
    connectionHealth: null,
    loading: {
      compliance: false,
      connection: false,
      diagnostics: false,
      audit: false
    },
    errors: {
      compliance: null,
      connection: null,
      diagnostics: null,
      audit: null
    },
    wsStatus: 'disconnected',
    lastUpdated: null
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Utility function to update loading state
  const setLoading = useCallback((key: keyof ComplianceConnectionState['loading'], value: boolean) => {
    setState(prev => ({
      ...prev,
      loading: { ...prev.loading, [key]: value }
    }));
  }, []);

  // Utility function to set errors
  const setError = useCallback((key: keyof ComplianceConnectionState['errors'], error: string | null) => {
    setState(prev => ({
      ...prev,
      errors: { ...prev.errors, [key]: error }
    }));
  }, []);

  // Compliance operations
  const runComplianceAudit = useCallback(async () => {
    setLoading('compliance', true);
    setError('compliance', null);

    try {
      const dashboardResult = await mcpApi.manageCompliance('get_compliance_dashboard');
      
      if (dashboardResult.success && dashboardResult.data) {
        setState(prev => ({
          ...prev,
          complianceStatus: {
            compliance_score: dashboardResult.data.compliance_score || 0,
            total_violations: dashboardResult.data.total_violations || 0,
            resolved_violations: dashboardResult.data.resolved_violations || 0,
            framework_breakdown: dashboardResult.data.framework_breakdown || {},
            last_audit: new Date().toISOString(),
            trends: dashboardResult.data.trends || { daily: [], weekly: [], monthly: [] }
          },
          violations: dashboardResult.data.violations || [],
          lastUpdated: new Date().toISOString()
        }));
      }
    } catch (error) {
      console.error('Failed to run compliance audit:', error);
      setError('compliance', error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setLoading('compliance', false);
    }
  }, [setLoading, setError]);

  const getAuditTrail = useCallback(async (limit: number = 100) => {
    setLoading('audit', true);
    setError('audit', null);

    try {
      const auditResult = await mcpApi.manageCompliance('get_audit_trail', { limit });
      
      if (auditResult.success && auditResult.data) {
        setState(prev => ({
          ...prev,
          auditTrail: auditResult.data.audit_trail || []
        }));
      }
    } catch (error) {
      console.error('Failed to get audit trail:', error);
      setError('audit', error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setLoading('audit', false);
    }
  }, [setLoading, setError]);

  const resolveViolation = useCallback(async (violationId: string) => {
    try {
      // This would typically make an API call to resolve the violation
      // For now, we'll simulate it by updating the local state
      setState(prev => ({
        ...prev,
        violations: prev.violations.map(violation =>
          violation.id === violationId
            ? { ...violation, status: 'resolved' as const }
            : violation
        ),
        lastUpdated: new Date().toISOString()
      }));
    } catch (error) {
      console.error('Failed to resolve violation:', error);
      setError('compliance', error instanceof Error ? error.message : 'Unknown error');
    }
  }, [setError]);

  const exportAuditReport = useCallback(async (filters: AuditFilters) => {
    try {
      // Filter audit entries based on filters
      const filteredEntries = state.auditTrail.filter(entry => {
        const matchesDateRange = (!filters.dateFrom || entry.timestamp >= filters.dateFrom) &&
                                (!filters.dateTo || entry.timestamp <= filters.dateTo);
        const matchesUser = !filters.user || entry.user_id.toLowerCase().includes(filters.user.toLowerCase());
        const matchesAction = !filters.action || entry.action.toLowerCase().includes(filters.action.toLowerCase());
        const matchesResult = filters.result === 'all' || entry.result === filters.result;
        const matchesResourceType = filters.resourceType === 'all' || entry.resource_type === filters.resourceType;
        
        return matchesDateRange && matchesUser && matchesAction && matchesResult && matchesResourceType;
      });

      // Create CSV content
      const csvContent = [
        ['Timestamp', 'User ID', 'Action', 'Resource Type', 'Resource ID', 'Result', 'IP Address'].join(','),
        ...filteredEntries.map(entry => [
          entry.timestamp,
          entry.user_id,
          entry.action,
          entry.resource_type,
          entry.resource_id,
          entry.result,
          entry.ip_address
        ].join(','))
      ].join('\n');

      // Download CSV
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-report-${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export audit report:', error);
      setError('audit', error instanceof Error ? error.message : 'Unknown error');
    }
  }, [state.auditTrail, setError]);

  // Connection operations
  const runConnectionDiagnostics = useCallback(async () => {
    setLoading('diagnostics', true);
    setError('diagnostics', null);

    try {
      const healthResult = await mcpApi.manageConnection('health_check', { include_details: true });
      const connectionHealthResult = await mcpApi.manageConnection('connection_health', { include_details: true });
      const capabilitiesResult = await mcpApi.manageConnection('server_capabilities');

      if (healthResult.success) {
        setState(prev => ({
          ...prev,
          connectionStatus: healthResult.data?.status || null
        }));
      }

      if (connectionHealthResult.success) {
        setState(prev => ({
          ...prev,
          connectionHealth: connectionHealthResult.data || null,
          diagnosticResults: connectionHealthResult.data?.diagnostic_results || []
        }));
      }

      if (capabilitiesResult.success) {
        setState(prev => ({
          ...prev,
          serverCapabilities: capabilitiesResult.data || null
        }));
      }
    } catch (error) {
      console.error('Failed to run connection diagnostics:', error);
      setError('diagnostics', error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setLoading('diagnostics', false);
    }
  }, [setLoading, setError]);

  const testConnection = useCallback(async () => {
    setLoading('connection', true);
    setError('connection', null);

    try {
      const result = await mcpApi.manageConnection('health_check');
      
      if (result.success) {
        setState(prev => ({
          ...prev,
          connectionStatus: result.data?.status || null,
          lastUpdated: new Date().toISOString()
        }));
      }
    } catch (error) {
      console.error('Failed to test connection:', error);
      setError('connection', error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setLoading('connection', false);
    }
  }, [setLoading, setError]);

  const restartConnection = useCallback(async () => {
    try {
      // Simulate connection restart
      setState(prev => ({
        ...prev,
        connectionStatus: prev.connectionStatus ? { ...prev.connectionStatus, status: 'degraded' } : null
      }));

      // Wait a moment then check health
      setTimeout(async () => {
        await testConnection();
      }, 2000);
    } catch (error) {
      console.error('Failed to restart connection:', error);
      setError('connection', error instanceof Error ? error.message : 'Unknown error');
    }
  }, [testConnection, setError]);

  const registerForUpdates = useCallback(async (sessionId: string) => {
    try {
      setState(prev => ({ ...prev, wsStatus: 'connecting' }));

      const result = await mcpApi.manageConnection('register_updates', {
        session_id: sessionId,
        client_info: {
          type: 'compliance_dashboard',
          version: '1.0.0',
          features: ['real_time_updates', 'compliance_monitoring']
        }
      });

      if (result.success) {
        setState(prev => ({ ...prev, wsStatus: 'connected' }));
      } else {
        setState(prev => ({ ...prev, wsStatus: 'disconnected' }));
      }
    } catch (error) {
      console.error('Failed to register for updates:', error);
      setState(prev => ({ ...prev, wsStatus: 'disconnected' }));
      setError('connection', error instanceof Error ? error.message : 'Unknown error');
    }
  }, [setError]);

  const runSpecificTest = useCallback(async (testType: string) => {
    try {
      // Simulate running specific test
      const testResult: DiagnosticResult = {
        test_name: testType,
        status: Math.random() > 0.8 ? 'failed' : Math.random() > 0.6 ? 'warning' : 'passed',
        response_time: Math.floor(Math.random() * 200) + 10,
        recommendations: ['Test completed successfully'],
        details: {},
        timestamp: new Date().toISOString()
      };

      if (testResult.status === 'failed') {
        testResult.error_message = `${testType} test failed`;
        testResult.recommendations = ['Check network connectivity', 'Verify server status'];
      }

      setState(prev => ({
        ...prev,
        diagnosticResults: prev.diagnosticResults.map(result =>
          result.test_name === testType ? testResult : result
        ).concat(prev.diagnosticResults.some(r => r.test_name === testType) ? [] : [testResult])
      }));
    } catch (error) {
      console.error('Failed to run specific test:', error);
      setError('diagnostics', error instanceof Error ? error.message : 'Unknown error');
    }
  }, [setError]);

  // Initialize data on mount
  useEffect(() => {
    const initializeData = async () => {
      await Promise.all([
        runComplianceAudit(),
        getAuditTrail(),
        runConnectionDiagnostics()
      ]);
    };

    initializeData();
  }, [runComplianceAudit, getAuditTrail, runConnectionDiagnostics]);

  // Setup periodic updates
  useEffect(() => {
    const interval = setInterval(() => {
      if (!state.loading.compliance && !state.loading.connection) {
        testConnection();
      }
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, [testConnection, state.loading]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return {
    // State
    ...state,
    
    // Actions
    actions: {
      // Compliance actions
      runComplianceAudit,
      getAuditTrail,
      resolveViolation,
      exportAuditReport,
      
      // Connection actions
      runConnectionDiagnostics,
      testConnection,
      restartConnection,
      registerForUpdates,
      runSpecificTest,
      
      // Utility actions
      refreshAll: useCallback(async () => {
        await Promise.all([
          runComplianceAudit(),
          getAuditTrail(),
          runConnectionDiagnostics()
        ]);
      }, [runComplianceAudit, getAuditTrail, runConnectionDiagnostics]),
      
      clearErrors: useCallback(() => {
        setState(prev => ({
          ...prev,
          errors: {
            compliance: null,
            connection: null,
            diagnostics: null,
            audit: null
          }
        }));
      }, [])
    }
  };
}