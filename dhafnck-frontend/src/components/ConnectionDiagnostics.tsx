import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Alert } from './ui/alert';
import { mcpApi } from '../api/enhanced';

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

interface DiagnosticResult {
  test_name: string;
  status: 'passed' | 'failed' | 'warning' | 'skipped';
  response_time: number;
  error_message?: string;
  recommendations: string[];
  details: any;
  timestamp: string;
}

interface DiagnosticTest {
  id: string;
  name: string;
  description: string;
  category: 'connectivity' | 'performance' | 'security' | 'compatibility';
  severity: 'low' | 'medium' | 'high' | 'critical';
  automated: boolean;
}

interface ConnectionDiagnosticsProps {
  connectionHealth: ConnectionHealth;
  diagnosticResults: DiagnosticResult[];
  onRunDiagnostics: () => Promise<void>;
  onRunSpecificTest: (testType: string) => Promise<void>;
}

export function ConnectionDiagnostics({
  connectionHealth,
  diagnosticResults,
  onRunDiagnostics,
  onRunSpecificTest
}: ConnectionDiagnosticsProps) {
  const [loading, setLoading] = useState(false);
  const [selectedTest, setSelectedTest] = useState<string | null>(null);
  const [testProgress, setTestProgress] = useState(0);
  const [runningTests, setRunningTests] = useState<Set<string>>(new Set());

  const diagnosticTests: DiagnosticTest[] = [
    {
      id: 'ping',
      name: 'Server Ping',
      description: 'Basic connectivity test to verify server is reachable',
      category: 'connectivity',
      severity: 'critical',
      automated: true
    },
    {
      id: 'auth',
      name: 'Authentication',
      description: 'Verify authentication system functionality',
      category: 'security',
      severity: 'high',
      automated: true
    },
    {
      id: 'mcp_protocol',
      name: 'MCP Protocol',
      description: 'Test MCP protocol compatibility and communication',
      category: 'compatibility',
      severity: 'high',
      automated: true
    },
    {
      id: 'tools',
      name: 'Tool Availability',
      description: 'Verify all expected tools are available and functional',
      category: 'compatibility',
      severity: 'medium',
      automated: true
    },
    {
      id: 'performance',
      name: 'Performance Analysis',
      description: 'Analyze response times and throughput capabilities',
      category: 'performance',
      severity: 'medium',
      automated: true
    },
    {
      id: 'connection_pool',
      name: 'Connection Pool',
      description: 'Test connection pool management and scaling',
      category: 'performance',
      severity: 'medium',
      automated: true
    },
    {
      id: 'memory_usage',
      name: 'Memory Usage',
      description: 'Check server memory utilization and potential leaks',
      category: 'performance',
      severity: 'low',
      automated: true
    },
    {
      id: 'network_latency',
      name: 'Network Latency',
      description: 'Measure network latency and identify bottlenecks',
      category: 'performance',
      severity: 'low',
      automated: true
    }
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed': return '✅';
      case 'failed': return '❌';
      case 'warning': return '⚠️';
      case 'skipped': return '⏭️';
      default: return '❓';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed': return 'border-green-500 bg-green-50';
      case 'failed': return 'border-red-500 bg-red-50';
      case 'warning': return 'border-yellow-500 bg-yellow-50';
      case 'skipped': return 'border-gray-300 bg-gray-50';
      default: return 'border-gray-300 bg-gray-50';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'connectivity': return 'bg-blue-100 text-blue-800';
      case 'performance': return 'bg-green-100 text-green-800';
      case 'security': return 'bg-red-100 text-red-800';
      case 'compatibility': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-600 text-white';
      case 'high': return 'bg-orange-600 text-white';
      case 'medium': return 'bg-yellow-600 text-white';
      case 'low': return 'bg-blue-600 text-white';
      default: return 'bg-gray-600 text-white';
    }
  };

  const runAllDiagnostics = async () => {
    setLoading(true);
    setTestProgress(0);
    
    try {
      await onRunDiagnostics();
      
      // Simulate progress
      for (let i = 0; i <= 100; i += 10) {
        setTestProgress(i);
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    } finally {
      setLoading(false);
      setTestProgress(0);
    }
  };

  const runSpecificTest = async (testId: string) => {
    setRunningTests(prev => new Set(Array.from(prev).concat(testId)));
    
    try {
      await onRunSpecificTest(testId);
    } finally {
      setRunningTests(prev => {
        const newSet = new Set(prev);
        newSet.delete(testId);
        return newSet;
      });
    }
  };

  const getHealthScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-yellow-600';
    if (score >= 60) return 'text-orange-600';
    return 'text-red-600';
  };

  const calculateHealthScore = () => {
    const passedTests = diagnosticResults.filter(r => r.status === 'passed').length;
    const totalTests = diagnosticResults.length;
    if (totalTests === 0) return 0;
    return Math.round((passedTests / totalTests) * 100);
  };

  const getRecommendations = () => {
    const failedTests = diagnosticResults.filter(r => r.status === 'failed');
    const recommendations = new Set<string>();
    
    failedTests.forEach(test => {
      test.recommendations.forEach(rec => recommendations.add(rec));
    });
    
    return Array.from(recommendations);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Connection Diagnostics</h2>
        <Button onClick={runAllDiagnostics} disabled={loading}>
          {loading ? 'Running Tests...' : 'Run All Tests'}
        </Button>
      </div>

      {/* Health Score Overview */}
      <Card>
        <CardHeader>
          <CardTitle>System Health Score</CardTitle>
          <CardDescription>Overall connection and system health assessment</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="text-center">
              <div className={`text-4xl font-bold ${getHealthScoreColor(calculateHealthScore())}`}>
                {calculateHealthScore()}%
              </div>
              <div className="text-sm text-gray-500 mt-1">Health Score</div>
            </div>
            <div className="flex-1 ml-8">
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-xl font-semibold text-green-600">
                    {diagnosticResults.filter(r => r.status === 'passed').length}
                  </div>
                  <div className="text-sm text-gray-500">Passed</div>
                </div>
                <div className="text-center">
                  <div className="text-xl font-semibold text-red-600">
                    {diagnosticResults.filter(r => r.status === 'failed').length}
                  </div>
                  <div className="text-sm text-gray-500">Failed</div>
                </div>
                <div className="text-center">
                  <div className="text-xl font-semibold text-yellow-600">
                    {diagnosticResults.filter(r => r.status === 'warning').length}
                  </div>
                  <div className="text-sm text-gray-500">Warnings</div>
                </div>
              </div>
            </div>
          </div>
          
          {loading && (
            <div className="mt-4">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${testProgress}%` }}
                ></div>
              </div>
              <div className="text-sm text-gray-500 mt-1">
                Running diagnostics... {testProgress}%
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Critical Issues Alert */}
      {diagnosticResults.some(r => r.status === 'failed') && (
        <Alert>
          <div className="font-medium">
            {diagnosticResults.filter(r => r.status === 'failed').length} critical issue(s) detected
          </div>
          <div className="text-sm mt-1">
            Review failed tests and apply recommended fixes immediately.
          </div>
        </Alert>
      )}

      {/* Test Categories */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {['connectivity', 'performance', 'security', 'compatibility'].map(category => {
          const categoryTests = diagnosticTests.filter(t => t.category === category);
          const categoryResults = diagnosticResults.filter(r => 
            categoryTests.some(t => t.id === r.test_name)
          );
          const passedCount = categoryResults.filter(r => r.status === 'passed').length;
          
          return (
            <Card key={category} className="text-center">
              <CardContent className="p-4">
                <Badge className={getCategoryColor(category)} variant="secondary">
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </Badge>
                <div className="mt-2">
                  <div className="text-2xl font-bold">
                    {passedCount}/{categoryResults.length}
                  </div>
                  <div className="text-sm text-gray-500">Tests Passed</div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Diagnostic Tests */}
      <Card>
        <CardHeader>
          <CardTitle>Diagnostic Tests</CardTitle>
          <CardDescription>Individual test results and recommendations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {diagnosticTests.map(test => {
              const result = diagnosticResults.find(r => r.test_name === test.id);
              const isRunning = runningTests.has(test.id);
              
              return (
                <div 
                  key={test.id} 
                  className={`border-l-4 p-4 rounded-lg ${
                    result ? getStatusColor(result.status) : 'border-gray-300 bg-gray-50'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg">
                          {result ? getStatusIcon(result.status) : '⭕'}
                        </span>
                        <h4 className="font-medium">{test.name}</h4>
                        <Badge className={getCategoryColor(test.category)} variant="secondary">
                          {test.category}
                        </Badge>
                        <Badge className={getSeverityColor(test.severity)} variant="secondary">
                          {test.severity}
                        </Badge>
                      </div>
                      
                      <p className="text-sm text-gray-600 mb-2">{test.description}</p>
                      
                      {result && (
                        <div className="space-y-2">
                          <div className="flex items-center gap-4 text-sm">
                            <span className="font-medium">
                              Status: <span className={`capitalize ${
                                result.status === 'passed' ? 'text-green-600' :
                                result.status === 'failed' ? 'text-red-600' :
                                result.status === 'warning' ? 'text-yellow-600' :
                                'text-gray-600'
                              }`}>
                                {result.status}
                              </span>
                            </span>
                            <span className="text-gray-500">
                              Response: {result.response_time}ms
                            </span>
                            <span className="text-gray-500">
                              {new Date(result.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                          
                          {result.error_message && (
                            <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
                              <strong>Error:</strong> {result.error_message}
                            </div>
                          )}
                          
                          {result.recommendations.length > 0 && (
                            <div className="text-sm">
                              <div className="font-medium text-gray-700 mb-1">Recommendations:</div>
                              <ul className="list-disc list-inside text-gray-600 space-y-1">
                                {result.recommendations.map((rec, index) => (
                                  <li key={index}>{rec}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                    
                    <div className="ml-4">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => runSpecificTest(test.id)}
                        disabled={isRunning || loading}
                      >
                        {isRunning ? 'Running...' : 'Test'}
                      </Button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* System Recommendations */}
      {getRecommendations().length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>System Recommendations</CardTitle>
            <CardDescription>Actions to improve system health and performance</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {getRecommendations().map((recommendation, index) => (
                <div key={index} className="flex items-start gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                  <div className="text-sm text-gray-700">{recommendation}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* System Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Response Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {connectionHealth.response_time}ms
            </div>
            <div className="text-sm text-gray-500 mt-1">
              Average response time
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Error Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${
              connectionHealth.error_rate > 5 ? 'text-red-600' :
              connectionHealth.error_rate > 2 ? 'text-yellow-600' :
              'text-green-600'
            }`}>
              {connectionHealth.error_rate.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-500 mt-1">
              Error rate
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Uptime</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {Math.floor(connectionHealth.uptime / 3600)}h
            </div>
            <div className="text-sm text-gray-500 mt-1">
              System uptime
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}