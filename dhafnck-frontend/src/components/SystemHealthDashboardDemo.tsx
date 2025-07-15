/**
 * System Health Dashboard Demo Component
 * Demonstrates the SystemHealthDashboard with mock data and real MCP API integration
 */

import { useHealthDashboard } from '../hooks/useHealthDashboard';
import { SystemHealthDashboard } from './SystemHealthDashboard';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card } from './ui/card';

export function SystemHealthDashboardDemo() {
  const {
    connectionStatus,
    complianceStatus,
    performanceMetrics,
    alerts,
    overallHealthScore,
    lastUpdate,
    loading,
    error,
    autoRefresh,
    refreshHealth,
    runDiagnostics,
    resolveAlert,
    toggleAutoRefresh,
    isHealthy,
    hasWarnings,
    hasCriticalIssues,
    activeAlerts,
    criticalAlerts
  } = useHealthDashboard();

  // Handle cases where data is still loading
  if (loading && !connectionStatus) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading system health data...</p>
        </div>
      </div>
    );
  }

  // Handle error states
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <Card className="max-w-md mx-auto p-6 border-red-200 bg-red-50">
          <div className="text-center">
            <div className="text-red-600 text-xl mb-2">⚠️</div>
            <h2 className="text-lg font-semibold text-red-800 mb-2">Health Check Failed</h2>
            <p className="text-red-700 mb-4">{error}</p>
            <Button 
              onClick={refreshHealth}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              Retry Health Check
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // Prepare props for SystemHealthDashboard
  const dashboardProps = {
    connectionStatus: connectionStatus || {
      status: 'down' as const,
      response_time: 0,
      last_check: new Date().toISOString()
    },
    complianceStatus: complianceStatus || {
      compliance_score: 0,
      violations: []
    },
    performanceMetrics: performanceMetrics || {
      requestCount: 0,
      successCount: 0,
      errorCount: 0,
      averageResponseTime: 0,
      queueLength: 0,
      frontend: {
        page_load_time: 0,
        first_contentful_paint: 0,
        largest_contentful_paint: 0,
        cumulative_layout_shift: 0
      },
      api: {
        avg_response_time: 0,
        p95_response_time: 0,
        error_rate: 0,
        success_rate: 100
      },
      system: {
        memory_usage: 0,
        cache_hit_ratio: 100,
        active_connections: 0
      }
    },
    alerts: alerts || [],
    onRefreshHealth: refreshHealth,
    onRunDiagnostics: runDiagnostics,
    onResolveAlert: resolveAlert,
    refreshInterval: 30000
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Demo Controls Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">
              System Health Dashboard Demo
            </h1>
            <p className="text-sm text-gray-600">
              Real-time monitoring with MCP API integration
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Health Status Summary */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Overall Health:</span>
              <Badge className={
                isHealthy ? 'bg-green-100 text-green-800' :
                hasWarnings ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }>
                {overallHealthScore}%
              </Badge>
            </div>

            {/* Active Alerts Count */}
            {activeAlerts.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Active Alerts:</span>
                <Badge className={
                  criticalAlerts.length > 0 ? 'bg-red-100 text-red-800' :
                  'bg-yellow-100 text-yellow-800'
                }>
                  {activeAlerts.length}
                </Badge>
              </div>
            )}

            {/* Auto-refresh Toggle */}
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={toggleAutoRefresh}
                className="rounded"
              />
              Auto-refresh
            </label>

            {/* Manual Refresh */}
            <Button 
              onClick={refreshHealth}
              disabled={loading}
              variant="outline"
              size="sm"
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </Button>
          </div>
        </div>

        {/* Last Update Time */}
        {lastUpdate && (
          <div className="mt-2 text-xs text-gray-500">
            Last updated: {new Date(lastUpdate).toLocaleString()}
          </div>
        )}
      </div>

      {/* System Status Quick Overview */}
      <div className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              connectionStatus?.status === 'healthy' ? 'bg-green-500' :
              connectionStatus?.status === 'degraded' ? 'bg-yellow-500' :
              'bg-red-500'
            }`}></div>
            <span>Connection: {connectionStatus?.status || 'unknown'}</span>
          </div>

          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              (complianceStatus?.compliance_score || 0) >= 0.85 ? 'bg-green-500' :
              (complianceStatus?.compliance_score || 0) >= 0.7 ? 'bg-yellow-500' :
              'bg-red-500'
            }`}></div>
            <span>
              Compliance: {Math.round((complianceStatus?.compliance_score || 0) * 100)}%
            </span>
          </div>

          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              (performanceMetrics?.api.success_rate || 0) >= 95 ? 'bg-green-500' :
              (performanceMetrics?.api.success_rate || 0) >= 90 ? 'bg-yellow-500' :
              'bg-red-500'
            }`}></div>
            <span>
              Performance: {Math.round(performanceMetrics?.api.success_rate || 0)}%
            </span>
          </div>

          {activeAlerts.length > 0 && (
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                criticalAlerts.length > 0 ? 'bg-red-500 animate-pulse' : 'bg-yellow-500'
              }`}></div>
              <span>
                {activeAlerts.length} active alert{activeAlerts.length !== 1 ? 's' : ''}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Main Dashboard */}
      <SystemHealthDashboard {...dashboardProps} />

      {/* Demo Information Footer */}
      <div className="bg-white border-t border-gray-200 px-6 py-4 mt-8">
        <div className="max-w-4xl mx-auto">
          <h3 className="text-sm font-semibold text-gray-900 mb-2">
            Demo Information
          </h3>
          <div className="text-xs text-gray-600 space-y-1">
            <p>
              • This dashboard integrates with the DhafnckMCP system to provide real-time health monitoring
            </p>
            <p>
              • Connection health is fetched from the MCP server using the manage_connection tool
            </p>
            <p>
              • Compliance status uses the manage_compliance tool for security validation
            </p>
            <p>
              • Performance metrics combine frontend Web Vitals with API response analytics
            </p>
            <p>
              • Auto-refresh can be toggled and customized for different monitoring intervals
            </p>
            <p>
              • Alerts are generated based on threshold violations and system anomalies
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SystemHealthDashboardDemo;