import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Alert } from './ui/alert';
import { mcpApi } from '../api/enhanced';

interface ConnectionStatus {
  status: 'healthy' | 'degraded' | 'down';
  response_time: number;
  last_check: string;
  uptime: number;
  connection_pool: {
    active: number;
    idle: number;
    total: number;
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
}

interface ConnectionSettings {
  timeout: number;
  retry_attempts: number;
  health_check_interval: number;
  auto_reconnect: boolean;
  session_persistence: boolean;
}

interface ConnectionMonitorProps {
  connectionStatus: ConnectionStatus;
  connectionHistory: ConnectionHistoryEntry[];
  serverCapabilities: ServerCapabilities;
  onTestConnection: () => Promise<void>;
  onRestartConnection: () => Promise<void>;
  onUpdateConnectionSettings: (settings: ConnectionSettings) => Promise<void>;
  onRegisterForUpdates: (sessionId: string) => Promise<void>;
}

export function ConnectionMonitor({
  connectionStatus,
  connectionHistory,
  serverCapabilities,
  onTestConnection,
  onRestartConnection,
  onUpdateConnectionSettings,
  onRegisterForUpdates
}: ConnectionMonitorProps) {
  const [selectedTab, setSelectedTab] = useState<'status' | 'history' | 'capabilities' | 'settings'>('status');
  const [loading, setLoading] = useState(false);
  const [diagnostics, setDiagnostics] = useState<DiagnosticResult[]>([]);
  const [wsStatus, setWsStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected');

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'degraded': return 'text-yellow-600 bg-yellow-100';
      case 'down': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getEventTypeColor = (eventType: string) => {
    switch (eventType) {
      case 'connected': return 'text-green-600';
      case 'disconnected': return 'text-red-600';
      case 'error': return 'text-red-600';
      case 'timeout': return 'text-orange-600';
      case 'retry': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  const handleTestConnection = async () => {
    setLoading(true);
    try {
      await onTestConnection();
    } finally {
      setLoading(false);
    }
  };

  const runDiagnostics = async () => {
    setLoading(true);
    try {
      // Simulate running diagnostics
      const diagnosticTests = [
        { name: 'ping', description: 'Basic connectivity test' },
        { name: 'auth', description: 'Authentication system test' },
        { name: 'mcp_protocol', description: 'Protocol compatibility test' },
        { name: 'tools', description: 'Available tools verification' },
        { name: 'performance', description: 'Response time analysis' }
      ];

      const results: DiagnosticResult[] = [];
      
      for (const test of diagnosticTests) {
        // Simulate test execution
        await new Promise(resolve => setTimeout(resolve, 500));
        
        const mockResult: DiagnosticResult = {
          test_name: test.name,
          status: Math.random() > 0.2 ? 'passed' : Math.random() > 0.5 ? 'warning' : 'failed',
          response_time: Math.floor(Math.random() * 200) + 10,
          recommendations: ['Maintain current configuration'],
          details: {}
        };

        if (mockResult.status === 'failed') {
          mockResult.error_message = `${test.name} test failed due to connectivity issues`;
          mockResult.recommendations = ['Check network connectivity', 'Verify server status'];
        }

        results.push(mockResult);
      }
      
      setDiagnostics(results);
    } finally {
      setLoading(false);
    }
  };

  const renderStatus = () => (
    <div className="space-y-6">
      {/* Current Status */}
      <Card>
        <CardHeader>
          <CardTitle>Connection Status</CardTitle>
          <CardDescription>Real-time server connection information</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(connectionStatus.status)}`}>
                {connectionStatus.status.toUpperCase()}
              </div>
              <div className="text-xs text-gray-500 mt-1">Overall Status</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {connectionStatus.response_time}ms
              </div>
              <div className="text-xs text-gray-500 mt-1">Response Time</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {Math.floor(connectionStatus.uptime / 3600)}h
              </div>
              <div className="text-xs text-gray-500 mt-1">Uptime</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {connectionStatus.error_rate.toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500 mt-1">Error Rate</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Connection Pool */}
      <Card>
        <CardHeader>
          <CardTitle>Connection Pool</CardTitle>
          <CardDescription>Active connection statistics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-xl font-semibold text-green-600">
                {connectionStatus.connection_pool.active}
              </div>
              <div className="text-sm text-gray-500">Active</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-semibold text-gray-600">
                {connectionStatus.connection_pool.idle}
              </div>
              <div className="text-sm text-gray-500">Idle</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-semibold text-blue-600">
                {connectionStatus.connection_pool.total}
              </div>
              <div className="text-sm text-gray-500">Total</div>
            </div>
          </div>
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-green-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(connectionStatus.connection_pool.active / connectionStatus.connection_pool.total) * 100}%` }}
              ></div>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Pool utilization: {Math.round((connectionStatus.connection_pool.active / connectionStatus.connection_pool.total) * 100)}%
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Metrics</CardTitle>
          <CardDescription>Connection performance indicators</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium">Throughput</span>
                <span className="text-sm text-gray-500">{connectionStatus.throughput} req/min</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(connectionStatus.throughput / 1000 * 100, 100)}%` }}
                ></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium">Error Rate</span>
                <span className="text-sm text-gray-500">{connectionStatus.error_rate.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-300 ${
                    connectionStatus.error_rate > 5 ? 'bg-red-600' :
                    connectionStatus.error_rate > 2 ? 'bg-yellow-600' :
                    'bg-green-600'
                  }`}
                  style={{ width: `${Math.min(connectionStatus.error_rate * 10, 100)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* WebSocket Status */}
      <Card>
        <CardHeader>
          <CardTitle>Real-time Updates</CardTitle>
          <CardDescription>WebSocket connection for live updates</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${
                wsStatus === 'connected' ? 'bg-green-500' :
                wsStatus === 'connecting' ? 'bg-yellow-500' :
                'bg-red-500'
              }`}></div>
              <span className="font-medium capitalize">{wsStatus}</span>
            </div>
            <Button 
              size="sm"
              onClick={() => onRegisterForUpdates(`session_${Date.now()}`)}
              disabled={wsStatus === 'connected'}
            >
              {wsStatus === 'connected' ? 'Connected' : 'Connect'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="flex gap-2">
        <Button onClick={handleTestConnection} disabled={loading}>
          {loading ? 'Testing...' : 'Test Connection'}
        </Button>
        <Button onClick={runDiagnostics} disabled={loading} variant="outline">
          Run Diagnostics
        </Button>
        <Button onClick={onRestartConnection} variant="outline">
          Restart Connection
        </Button>
      </div>

      {/* Diagnostics Results */}
      {diagnostics.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Diagnostic Results</CardTitle>
            <CardDescription>Latest connection diagnostic test results</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {diagnostics.map(result => (
                <div key={result.test_name} className={`border-l-4 p-3 rounded-lg ${
                  result.status === 'passed' ? 'border-green-500 bg-green-50' :
                  result.status === 'warning' ? 'border-yellow-500 bg-yellow-50' :
                  result.status === 'failed' ? 'border-red-500 bg-red-50' :
                  'border-gray-300 bg-gray-50'
                }`}>
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-medium capitalize">{result.test_name} Test</h4>
                      {result.error_message && (
                        <p className="text-sm text-red-600 mt-1">{result.error_message}</p>
                      )}
                      <div className="text-xs text-gray-500 mt-1">
                        Response time: {result.response_time}ms
                      </div>
                    </div>
                    <Badge variant={
                      result.status === 'passed' ? 'default' :
                      result.status === 'warning' ? 'secondary' :
                      'destructive'
                    }>
                      {result.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderHistory = () => (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Connection History</CardTitle>
          <CardDescription>Recent connection events and timeline</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {connectionHistory.map((entry, index) => (
              <div key={index} className="flex items-start gap-3 pb-3 border-b border-gray-100 last:border-b-0">
                <div className={`w-2 h-2 rounded-full mt-2 ${getEventTypeColor(entry.event_type).replace('text-', 'bg-')}`}></div>
                <div className="flex-1">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className={`font-medium ${getEventTypeColor(entry.event_type)}`}>
                        {entry.event_type.toUpperCase()}
                      </div>
                      <div className="text-sm text-gray-600">
                        Response time: {entry.response_time}ms
                        {entry.duration && ` | Duration: ${Math.floor(entry.duration / 1000)}s`}
                      </div>
                      {entry.error_message && (
                        <div className="text-sm text-red-600 mt-1">{entry.error_message}</div>
                      )}
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(entry.timestamp).toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderCapabilities = () => (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Server Information</CardTitle>
          <CardDescription>Server version and basic information</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm font-medium text-gray-500">Version</div>
              <div className="text-lg font-semibold">{serverCapabilities.version}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500">Protocol</div>
              <div className="text-lg font-semibold">MCP 2025-06-18</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Authentication</CardTitle>
          <CardDescription>Authentication system configuration</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">
                Status: {serverCapabilities.authentication.enabled ? 'Enabled' : 'Disabled'}
              </div>
              <div className="text-sm text-gray-500">
                Methods: {serverCapabilities.authentication.methods.join(', ')}
              </div>
            </div>
            <Badge variant={serverCapabilities.authentication.enabled ? 'default' : 'secondary'}>
              {serverCapabilities.authentication.enabled ? 'Active' : 'Inactive'}
            </Badge>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Rate Limiting</CardTitle>
          <CardDescription>Request rate limiting configuration</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">
                Status: {serverCapabilities.rate_limiting.enabled ? 'Enabled' : 'Disabled'}
              </div>
              <div className="text-sm text-gray-500">
                Limit: {serverCapabilities.rate_limiting.requests_per_minute} requests/minute
              </div>
            </div>
            <Badge variant={serverCapabilities.rate_limiting.enabled ? 'default' : 'secondary'}>
              {serverCapabilities.rate_limiting.enabled ? 'Active' : 'Inactive'}
            </Badge>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Available Tools</CardTitle>
          <CardDescription>MCP tools supported by this server</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {serverCapabilities.tools.map(tool => (
              <Badge key={tool} variant="outline" className="justify-center">
                {tool}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Features</CardTitle>
          <CardDescription>Supported server features</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {serverCapabilities.features.map(feature => (
              <div key={feature} className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm">{feature}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Connection Monitor</h2>
        <div className="flex gap-2">
          <Button
            variant={selectedTab === 'status' ? 'default' : 'outline'}
            onClick={() => setSelectedTab('status')}
          >
            Status
          </Button>
          <Button
            variant={selectedTab === 'history' ? 'default' : 'outline'}
            onClick={() => setSelectedTab('history')}
          >
            History
          </Button>
          <Button
            variant={selectedTab === 'capabilities' ? 'default' : 'outline'}
            onClick={() => setSelectedTab('capabilities')}
          >
            Capabilities
          </Button>
        </div>
      </div>

      {connectionStatus.status === 'down' && (
        <Alert>
          <div className="font-medium">
            Connection is down. Check server status and network connectivity.
          </div>
        </Alert>
      )}

      {selectedTab === 'status' && renderStatus()}
      {selectedTab === 'history' && renderHistory()}
      {selectedTab === 'capabilities' && renderCapabilities()}
    </div>
  );
}