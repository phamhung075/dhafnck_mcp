/**
 * System Health Dashboard Component
 * Real-time monitoring of system health, compliance, and performance metrics
 * Enhanced with compliance dashboard and connection monitoring integration
 */

import { useEffect, useRef, useState } from 'react';
import { PerformanceMetrics as BasePerformanceMetrics, ComplianceStatus, ConnectionStatus } from '../api/enhanced';
import { useComplianceConnection } from '../hooks/useComplianceConnection';
import { AuditTrailViewer } from './AuditTrailViewer';
import { ComplianceDashboard } from './ComplianceDashboard';
import { ConnectionDiagnostics } from './ConnectionDiagnostics';
import { ConnectionMonitor } from './ConnectionMonitor';
import { Alert } from './ui/alert';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Separator } from './ui/separator';

// Enhanced Types for System Health Dashboard
export interface PerformanceMetrics extends BasePerformanceMetrics {
  frontend: {
    page_load_time: number;
    first_contentful_paint: number;
    largest_contentful_paint: number;
    cumulative_layout_shift: number;
  };
  api: {
    avg_response_time: number;
    p95_response_time: number;
    error_rate: number;
    success_rate: number;
  };
  system: {
    memory_usage: number;
    cache_hit_ratio: number;
    active_connections: number;
  };
}

export interface SystemAlert {
  id: string;
  type: 'connection' | 'compliance' | 'performance' | 'security' | 'system';
  severity: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  description: string;
  timestamp: string;
  status: 'active' | 'acknowledged' | 'resolved';
  affected_components: string[];
  suggested_actions: string[];
}

export interface MetricDataPoint {
  timestamp: string;
  value: number;
  label?: string;
}

// Component Props
export interface SystemHealthDashboardProps {
  connectionStatus: ConnectionStatus;
  complianceStatus: ComplianceStatus;
  performanceMetrics: PerformanceMetrics;
  alerts: SystemAlert[];
  onRefreshHealth: () => Promise<void>;
  onRunDiagnostics: () => Promise<void>;
  onResolveAlert: (alertId: string) => Promise<void>;
  refreshInterval?: number;
}

export interface HealthStatusCardProps {
  title: string;
  status: 'healthy' | 'warning' | 'error' | 'unknown';
  score: number;
  metrics: Record<string, any>;
  lastUpdate: string;
  onViewDetails: () => void;
}

export interface MetricsChartProps {
  title: string;
  data: MetricDataPoint[];
  yAxisLabel: string;
  color: string;
  threshold?: number;
  timeRange: '1h' | '6h' | '24h' | '7d';
  onTimeRangeChange: (range: string) => void;
}

export interface AlertsPanelProps {
  alerts: SystemAlert[];
  onAcknowledgeAlert: (alertId: string) => Promise<void>;
  onResolveAlert: (alertId: string) => Promise<void>;
  onViewAlert: (alertId: string) => void;
}

// Health Status Card Component
function HealthStatusCard({
  title,
  status,
  score,
  metrics,
  lastUpdate,
  onViewDetails
}: HealthStatusCardProps) {
  const statusColors = {
    healthy: 'border-green-500 bg-green-50',
    warning: 'border-yellow-500 bg-yellow-50',
    error: 'border-red-500 bg-red-50',
    unknown: 'border-gray-500 bg-gray-50'
  };

  const statusBadgeColors = {
    healthy: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    error: 'bg-red-100 text-red-800',
    unknown: 'bg-gray-100 text-gray-800'
  };

  return (
    <Card className={`border-l-4 p-4 ${statusColors[status]}`}>
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-semibold text-lg">{title}</h3>
          <div className="text-2xl font-bold mt-1">{score}%</div>
        </div>
        <div className="text-right">
          <Badge className={statusBadgeColors[status]}>
            {status.toUpperCase()}
          </Badge>
          <div className="text-xs text-gray-500 mt-1">
            {new Date(lastUpdate).toLocaleTimeString()}
          </div>
        </div>
      </div>
      
      <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
        {Object.entries(metrics).slice(0, 4).map(([key, value]) => (
          <div key={key} className="flex justify-between">
            <span className="text-gray-600">{key}:</span>
            <span className="font-medium">{value}</span>
          </div>
        ))}
      </div>
      
      <Button 
        onClick={onViewDetails}
        variant="ghost"
        size="sm"
        className="mt-3 text-blue-600 hover:text-blue-800"
      >
        View Details →
      </Button>
    </Card>
  );
}

// Simple SVG-based Metrics Chart Component
function MetricsChart({
  title,
  data,
  yAxisLabel,
  color,
  threshold,
  timeRange,
  onTimeRangeChange
}: MetricsChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const width = 400;
  const height = 200;
  const margin = { top: 20, right: 20, bottom: 30, left: 40 };
  const chartWidth = width - margin.left - margin.right;
  const chartHeight = height - margin.top - margin.bottom;

  if (!data || data.length === 0) {
    return (
      <Card className="p-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-semibold">{title}</h3>
          <select 
            value={timeRange} 
            onChange={(e) => onTimeRangeChange(e.target.value)}
            className="px-2 py-1 border rounded text-sm"
          >
            <option value="1h">1 Hour</option>
            <option value="6h">6 Hours</option>
            <option value="24h">24 Hours</option>
            <option value="7d">7 Days</option>
          </select>
        </div>
        <div className="flex items-center justify-center h-32 text-gray-500">
          No data available
        </div>
      </Card>
    );
  }

  const maxValue = Math.max(...data.map(d => d.value));
  const minValue = Math.min(...data.map(d => d.value));
  const valueRange = maxValue - minValue || 1;

  const points = data.map((point, index) => {
    const x = (index / (data.length - 1)) * chartWidth;
    const y = chartHeight - ((point.value - minValue) / valueRange) * chartHeight;
    return `${x},${y}`;
  }).join(' ');

  return (
    <Card className="p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold">{title}</h3>
        <select 
          value={timeRange} 
          onChange={(e) => onTimeRangeChange(e.target.value)}
          className="px-2 py-1 border rounded text-sm"
        >
          <option value="1h">1 Hour</option>
          <option value="6h">6 Hours</option>
          <option value="24h">24 Hours</option>
          <option value="7d">7 Days</option>
        </select>
      </div>
      
      <div className="relative">
        <svg
          ref={svgRef}
          width={width}
          height={height}
          className="border rounded"
        >
          {/* Y-axis */}
          <line
            x1={margin.left}
            y1={margin.top}
            x2={margin.left}
            y2={height - margin.bottom}
            stroke="#666"
            strokeWidth={1}
          />
          
          {/* X-axis */}
          <line
            x1={margin.left}
            y1={height - margin.bottom}
            x2={width - margin.right}
            y2={height - margin.bottom}
            stroke="#666"
            strokeWidth={1}
          />
          
          {/* Threshold line */}
          {threshold && (
            <line
              x1={margin.left}
              y1={margin.top + chartHeight - ((threshold - minValue) / valueRange) * chartHeight}
              x2={width - margin.right}
              y2={margin.top + chartHeight - ((threshold - minValue) / valueRange) * chartHeight}
              stroke="#ff6b6b"
              strokeWidth={2}
              strokeDasharray="5,5"
            />
          )}
          
          {/* Data line */}
          <polyline
            points={points}
            fill="none"
            stroke={color}
            strokeWidth={2}
            transform={`translate(${margin.left}, ${margin.top})`}
          />
          
          {/* Data points */}
          {data.map((point, index) => {
            const x = margin.left + (index / (data.length - 1)) * chartWidth;
            const y = margin.top + chartHeight - ((point.value - minValue) / valueRange) * chartHeight;
            return (
              <circle
                key={index}
                cx={x}
                cy={y}
                r={3}
                fill={color}
              />
            );
          })}
          
          {/* Y-axis label */}
          <text
            x={15}
            y={height / 2}
            textAnchor="middle"
            fontSize="12"
            fill="#666"
            transform={`rotate(-90, 15, ${height / 2})`}
          >
            {yAxisLabel}
          </text>
          
          {/* Value labels */}
          <text x={margin.left} y={margin.top - 5} fontSize="10" fill="#666">
            {maxValue.toFixed(1)}
          </text>
          <text x={margin.left} y={height - margin.bottom + 15} fontSize="10" fill="#666">
            {minValue.toFixed(1)}
          </text>
        </svg>
      </div>
    </Card>
  );
}

// Alerts Panel Component
function AlertsPanel({
  alerts,
  onAcknowledgeAlert,
  onResolveAlert,
  onViewAlert
}: AlertsPanelProps) {
  const [filter, setFilter] = useState<'all' | 'critical' | 'error' | 'warning' | 'info'>('all');
  const [showResolved, setShowResolved] = useState(false);

  const filteredAlerts = alerts.filter(alert => {
    const severityMatch = filter === 'all' || alert.severity === filter;
    const statusMatch = showResolved || alert.status !== 'resolved';
    return severityMatch && statusMatch;
  });

  const severityColors = {
    info: 'border-blue-200 bg-blue-50',
    warning: 'border-yellow-200 bg-yellow-50',
    error: 'border-red-200 bg-red-50',
    critical: 'border-red-500 bg-red-100'
  };

  const severityBadgeColors = {
    critical: 'bg-red-600 text-white',
    error: 'bg-red-500 text-white',
    warning: 'bg-yellow-500 text-white',
    info: 'bg-blue-500 text-white'
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">System Alerts</h3>
        <div className="flex gap-2">
          <select 
            value={filter} 
            onChange={(e) => setFilter(e.target.value as any)}
            className="px-3 py-1 border rounded"
          >
            <option value="all">All Alerts</option>
            <option value="critical">Critical</option>
            <option value="error">Error</option>
            <option value="warning">Warning</option>
            <option value="info">Info</option>
          </select>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={showResolved}
              onChange={(e) => setShowResolved(e.target.checked)}
            />
            Show Resolved
          </label>
        </div>
      </div>

      <div className="space-y-2 max-h-64 overflow-y-auto">
        {filteredAlerts.map(alert => (
          <Alert key={alert.id} className={`border rounded-lg p-3 ${severityColors[alert.severity]}`}>
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <Badge className={severityBadgeColors[alert.severity]}>
                    {alert.severity.toUpperCase()}
                  </Badge>
                  <span className="text-sm text-gray-600">{alert.type}</span>
                  <span className="text-xs text-gray-500">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <h4 className="font-medium mt-1">{alert.title}</h4>
                <p className="text-sm text-gray-600 mt-1">{alert.description}</p>
                {alert.affected_components.length > 0 && (
                  <div className="text-xs text-gray-500 mt-1">
                    Affected: {alert.affected_components.join(', ')}
                  </div>
                )}
              </div>
              <div className="flex gap-1 ml-4">
                {alert.status === 'active' && (
                  <>
                    <Button
                      onClick={() => onAcknowledgeAlert(alert.id)}
                      variant="ghost"
                      size="sm"
                      className="text-xs"
                    >
                      Acknowledge
                    </Button>
                    <Button
                      onClick={() => onResolveAlert(alert.id)}
                      variant="ghost"
                      size="sm"
                      className="text-xs bg-green-100 hover:bg-green-200"
                    >
                      Resolve
                    </Button>
                  </>
                )}
                <Button
                  onClick={() => onViewAlert(alert.id)}
                  variant="ghost"
                  size="sm"
                  className="text-xs bg-blue-100 hover:bg-blue-200"
                >
                  Details
                </Button>
              </div>
            </div>
          </Alert>
        ))}
      </div>

      {filteredAlerts.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No alerts matching current filters
        </div>
      )}
    </div>
  );
}

// Enhanced System Health Dashboard with Compliance and Connection Integration
export function SystemHealthDashboard({
  connectionStatus,
  complianceStatus,
  performanceMetrics,
  alerts,
  onRefreshHealth,
  onRunDiagnostics,
  onResolveAlert,
  refreshInterval = 30000
}: SystemHealthDashboardProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date().toISOString());
  const [metricsTimeRange, setMetricsTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('1h');
  const [activeView, setActiveView] = useState<'overview' | 'compliance' | 'connection' | 'audit' | 'diagnostics'>('overview');
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Use the compliance connection hook for enhanced functionality
  const {
    complianceStatus: enhancedComplianceStatus,
    violations,
    auditTrail,
    connectionStatus: enhancedConnectionStatus,
    connectionHistory,
    serverCapabilities,
    diagnosticResults,
    connectionHealth,
    loading,
    errors,
    wsStatus,
    lastUpdated,
    actions
  } = useComplianceConnection();

  // Calculate overall health score with enhanced data
  const calculateOverallHealth = () => {
    const connectionScore = (enhancedConnectionStatus || connectionStatus)?.status === 'healthy' ? 100 : 
                          (enhancedConnectionStatus || connectionStatus)?.status === 'degraded' ? 70 : 20;
    const complianceScore = (enhancedComplianceStatus || complianceStatus)?.compliance_score * 100 || 0;
    const performanceScore = performanceMetrics?.api?.success_rate || 75;
    const criticalViolations = violations.filter(v => v.severity === 'critical' && v.status === 'open').length;
    
    // Adjust score based on critical violations
    const violationPenalty = criticalViolations * 10;
    const baseScore = Math.round((connectionScore + complianceScore + performanceScore) / 3);
    
    return Math.max(0, baseScore - violationPenalty);
  };

  const overallHealthScore = calculateOverallHealth();
  const overallStatus = overallHealthScore >= 85 ? 'healthy' :
                       overallHealthScore >= 70 ? 'warning' : 'error';

  // Auto-refresh logic
  useEffect(() => {
    if (autoRefresh) {
      refreshIntervalRef.current = setInterval(async () => {
        await handleRefresh();
      }, refreshInterval);
    } else {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    }

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [autoRefresh, refreshInterval]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await onRefreshHealth();
      setLastUpdate(new Date().toISOString());
    } catch (error) {
      console.error('Failed to refresh health:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      // Implementation would acknowledge the alert
      console.log('Acknowledging alert:', alertId);
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  const handleViewAlert = (alertId: string) => {
    console.log('Viewing alert details:', alertId);
    // Implementation would show alert details
  };

  // Mock data for charts (in real implementation, this would come from props)
  const mockChartData: MetricDataPoint[] = Array.from({ length: 24 }, (_, i) => ({
    timestamp: new Date(Date.now() - (23 - i) * 60 * 60 * 1000).toISOString(),
    value: 85 + Math.random() * 30
  }));

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Overall Health Score */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">Overall System Health</h2>
            <div className="flex items-center gap-3 mt-2">
              <div className="text-3xl font-bold">{overallHealthScore}%</div>
              <Badge className={
                overallStatus === 'healthy' ? 'bg-green-100 text-green-800' :
                overallStatus === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }>
                {overallStatus.toUpperCase()}
              </Badge>
            </div>
          </div>
          <div className="text-right text-sm text-gray-500">
            Last updated: {new Date(lastUpdated || lastUpdate).toLocaleTimeString()}
          </div>
        </div>
      </Card>

      {/* Critical Alerts */}
      {(violations.filter(v => v.severity === 'critical' && v.status === 'open').length > 0 || 
        (enhancedConnectionStatus || connectionStatus)?.status === 'down' ||
        Object.values(errors).some(error => error !== null)) && (
        <Card className="border-red-200 bg-red-50">
          <div className="p-4">
            <h3 className="font-medium text-red-800 mb-3">Critical Issues Detected</h3>
            <div className="space-y-2">
              {violations.filter(v => v.severity === 'critical' && v.status === 'open').map(violation => (
                <Alert key={violation.id} className="border-red-300">
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="font-medium">{violation.title}</div>
                      <div className="text-sm text-gray-600">{violation.description}</div>
                    </div>
                    <Button size="sm" onClick={() => actions.resolveViolation(violation.id)}>
                      Resolve
                    </Button>
                  </div>
                </Alert>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <HealthStatusCard
          title="Connection Health"
          status={(enhancedConnectionStatus || connectionStatus)?.status === 'healthy' ? 'healthy' : 
                 (enhancedConnectionStatus || connectionStatus)?.status === 'degraded' ? 'warning' : 'error'}
          score={(enhancedConnectionStatus || connectionStatus)?.status === 'healthy' ? 100 : 
                (enhancedConnectionStatus || connectionStatus)?.status === 'degraded' ? 70 : 20}
          metrics={{
            'Response Time': `${(enhancedConnectionStatus || connectionStatus)?.response_time || 0}ms`,
            'Status': (enhancedConnectionStatus || connectionStatus)?.status || 'unknown',
            'WebSocket': wsStatus || 'disconnected'
          }}
          lastUpdate={lastUpdated || lastUpdate}
          onViewDetails={() => setActiveView('connection')}
        />

        <HealthStatusCard
          title="Compliance Status"
          status={(enhancedComplianceStatus || complianceStatus)?.compliance_score >= 0.85 ? 'healthy' :
                 (enhancedComplianceStatus || complianceStatus)?.compliance_score >= 0.7 ? 'warning' : 'error'}
          score={Math.round(((enhancedComplianceStatus || complianceStatus)?.compliance_score || 0) * 100)}
          metrics={{
            'Open Violations': violations.filter(v => v.status === 'open').length,
            'Critical': violations.filter(v => v.severity === 'critical' && v.status === 'open').length,
            'High': violations.filter(v => v.severity === 'high' && v.status === 'open').length
          }}
          lastUpdate={lastUpdated || lastUpdate}
          onViewDetails={() => setActiveView('compliance')}
        />

        <HealthStatusCard
          title="Performance"
          status={performanceMetrics?.api?.success_rate >= 95 ? 'healthy' :
                 performanceMetrics?.api?.success_rate >= 90 ? 'warning' : 'error'}
          score={Math.round(performanceMetrics?.api?.success_rate || 0)}
          metrics={{
            'Success Rate': `${Math.round(performanceMetrics?.api?.success_rate || 0)}%`,
            'Avg Response': `${Math.round(performanceMetrics?.api?.avg_response_time || 0)}ms`,
            'Requests': performanceMetrics?.requestCount || 0
          }}
          lastUpdate={lastUpdated || lastUpdate}
          onViewDetails={() => setActiveView('diagnostics')}
        />
      </div>

      {/* Metrics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MetricsChart
          title="Response Time"
          data={mockChartData}
          yAxisLabel="Milliseconds"
          color="#3b82f6"
          threshold={500}
          timeRange={metricsTimeRange}
          onTimeRangeChange={(range) => setMetricsTimeRange(range as any)}
        />
        
        <MetricsChart
          title="Success Rate"
          data={mockChartData.map(d => ({ ...d, value: Math.min(100, d.value + 10) }))}
          yAxisLabel="Percentage"
          color="#10b981"
          threshold={95}
          timeRange={metricsTimeRange}
          onTimeRangeChange={(range) => setMetricsTimeRange(range as any)}
        />
      </div>

      {/* Alerts Panel */}
      <AlertsPanel
        alerts={alerts}
        onAcknowledgeAlert={handleAcknowledgeAlert}
        onResolveAlert={onResolveAlert}
        onViewAlert={handleViewAlert}
      />
    </div>
  );

  return (
    <div className="space-y-6 p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">System Health Dashboard</h1>
          <p className="text-gray-600">Complete system monitoring, compliance, and performance management</p>
        </div>
        <div className="flex gap-3">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-refresh
          </label>
          <Button 
            onClick={() => Promise.all([handleRefresh(), actions.refreshAll()])}
            disabled={isRefreshing || Object.values(loading).some(Boolean)}
            variant="outline"
          >
            {isRefreshing || Object.values(loading).some(Boolean) ? 'Refreshing...' : 'Refresh All'}
          </Button>
          <Button 
            onClick={onRunDiagnostics}
            variant="outline"
          >
            Run Diagnostics
          </Button>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        <Button
          variant={activeView === 'overview' ? 'default' : 'outline'}
          onClick={() => setActiveView('overview')}
        >
          Overview
        </Button>
        <Button
          variant={activeView === 'compliance' ? 'default' : 'outline'}
          onClick={() => setActiveView('compliance')}
        >
          Compliance ({violations.filter(v => v.status === 'open').length})
        </Button>
        <Button
          variant={activeView === 'connection' ? 'default' : 'outline'}
          onClick={() => setActiveView('connection')}
        >
          Connection
        </Button>
        <Button
          variant={activeView === 'diagnostics' ? 'default' : 'outline'}
          onClick={() => setActiveView('diagnostics')}
        >
          Diagnostics
        </Button>
        <Button
          variant={activeView === 'audit' ? 'default' : 'outline'}
          onClick={() => setActiveView('audit')}
        >
          Audit Trail
        </Button>
      </div>

      <Separator />

      {/* Content Views */}
      {activeView === 'overview' && renderOverview()}
      
      {activeView === 'compliance' && enhancedComplianceStatus && (
        <ComplianceDashboard
          complianceStatus={enhancedComplianceStatus}
          violations={violations}
          auditTrail={auditTrail}
          onRunAudit={actions.runComplianceAudit}
          onResolveViolation={actions.resolveViolation}
          onExportAuditReport={() => actions.exportAuditReport({} as any)}
          onUpdateCompliancePolicy={async (policy) => {
            console.log('Update compliance policy:', policy);
          }}
        />
      )}
      
      {activeView === 'connection' && (enhancedConnectionStatus || connectionStatus) && serverCapabilities && (
        <ConnectionMonitor
          connectionStatus={enhancedConnectionStatus || connectionStatus as any}
          connectionHistory={connectionHistory}
          serverCapabilities={serverCapabilities}
          onTestConnection={actions.testConnection}
          onRestartConnection={actions.restartConnection}
          onUpdateConnectionSettings={async (settings) => {
            console.log('Update connection settings:', settings);
          }}
          onRegisterForUpdates={actions.registerForUpdates}
        />
      )}
      
      {activeView === 'diagnostics' && connectionHealth && (
        <ConnectionDiagnostics
          connectionHealth={connectionHealth}
          diagnosticResults={diagnosticResults}
          onRunDiagnostics={actions.runConnectionDiagnostics}
          onRunSpecificTest={actions.runSpecificTest}
        />
      )}
      
      {activeView === 'audit' && (
        <AuditTrailViewer
          auditEntries={auditTrail}
          onExportAudit={actions.exportAuditReport}
          onViewEntryDetails={(entryId) => {
            console.log('View entry details:', entryId);
          }}
        />
      )}
    </div>
  );
}

export default SystemHealthDashboard;