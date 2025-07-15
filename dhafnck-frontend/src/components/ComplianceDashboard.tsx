import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Alert } from './ui/alert';
import { mcpApi } from '../api/enhanced';

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

interface CompliancePolicy {
  id: string;
  name: string;
  description: string;
  framework: string;
  rules: any[];
  enabled: boolean;
}

interface ComplianceDashboardProps {
  complianceStatus: ComplianceStatus;
  violations: ComplianceViolation[];
  auditTrail: AuditEntry[];
  onRunAudit: () => Promise<void>;
  onResolveViolation: (violationId: string) => Promise<void>;
  onExportAuditReport: () => Promise<void>;
  onUpdateCompliancePolicy: (policy: CompliancePolicy) => Promise<void>;
}

export function ComplianceDashboard({
  complianceStatus,
  violations,
  auditTrail,
  onRunAudit,
  onResolveViolation,
  onExportAuditReport,
  onUpdateCompliancePolicy
}: ComplianceDashboardProps) {
  const [selectedTab, setSelectedTab] = useState<'overview' | 'violations' | 'audit' | 'policies'>('overview');
  const [loading, setLoading] = useState(false);
  const [violationFilter, setViolationFilter] = useState({
    severity: 'all',
    type: 'all',
    status: 'open',
    framework: 'all'
  });

  const severityColors = {
    critical: 'bg-red-100 border-red-500 text-red-800',
    high: 'bg-orange-100 border-orange-500 text-orange-800',
    medium: 'bg-yellow-100 border-yellow-500 text-yellow-800',
    low: 'bg-blue-100 border-blue-500 text-blue-800'
  };

  const getComplianceScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-yellow-600';
    if (score >= 60) return 'text-orange-600';
    return 'text-red-600';
  };

  const filteredViolations = violations.filter(violation => {
    return (violationFilter.severity === 'all' || violation.severity === violationFilter.severity) &&
           (violationFilter.type === 'all' || violation.type === violationFilter.type) &&
           (violationFilter.status === 'all' || violation.status === violationFilter.status);
  });

  const violationCounts = {
    critical: violations.filter(v => v.severity === 'critical' && v.status === 'open').length,
    high: violations.filter(v => v.severity === 'high' && v.status === 'open').length,
    medium: violations.filter(v => v.severity === 'medium' && v.status === 'open').length,
    low: violations.filter(v => v.severity === 'low' && v.status === 'open').length,
  };

  const handleRunAudit = async () => {
    setLoading(true);
    try {
      await onRunAudit();
    } finally {
      setLoading(false);
    }
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Overall Compliance Score */}
      <Card>
        <CardHeader>
          <CardTitle>Overall Compliance Score</CardTitle>
          <CardDescription>Current organizational compliance status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="text-center">
              <div className={`text-4xl font-bold ${getComplianceScoreColor(complianceStatus.compliance_score)}`}>
                {complianceStatus.compliance_score}%
              </div>
              <div className="text-sm text-gray-500 mt-1">
                Last audit: {new Date(complianceStatus.last_audit).toLocaleDateString()}
              </div>
            </div>
            <div className="flex-1 ml-8">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-semibold text-green-600">
                    {complianceStatus.resolved_violations}
                  </div>
                  <div className="text-sm text-gray-500">Resolved</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-semibold text-red-600">
                    {complianceStatus.total_violations - complianceStatus.resolved_violations}
                  </div>
                  <div className="text-sm text-gray-500">Open</div>
                </div>
              </div>
            </div>
            <Button onClick={handleRunAudit} disabled={loading}>
              {loading ? 'Running...' : 'Run Full Audit'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Violation Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        {Object.entries(violationCounts).map(([severity, count]) => (
          <Card key={severity} className={`border-l-4 ${
            severity === 'critical' ? 'border-red-500' :
            severity === 'high' ? 'border-orange-500' :
            severity === 'medium' ? 'border-yellow-500' :
            'border-blue-500'
          }`}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold">{count}</div>
                  <div className="text-sm text-gray-500 capitalize">{severity}</div>
                </div>
                <Badge variant={severity === 'critical' || severity === 'high' ? 'destructive' : 'secondary'}>
                  {severity.toUpperCase()}
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Framework Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Framework Compliance</CardTitle>
          <CardDescription>Compliance scores by framework</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(complianceStatus.framework_breakdown || {}).map(([framework, data]) => (
              <div key={framework} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <div className="font-medium">{framework}</div>
                  <div className="text-sm text-gray-500">{data.violations} violations</div>
                </div>
                <div className="text-right">
                  <div className={`text-lg font-semibold ${getComplianceScoreColor(data.score)}`}>
                    {data.score}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Critical Violations */}
      <Card>
        <CardHeader>
          <CardTitle>Critical & High Priority Violations</CardTitle>
          <CardDescription>Violations requiring immediate attention</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {violations
              .filter(v => (v.severity === 'critical' || v.severity === 'high') && v.status === 'open')
              .slice(0, 5)
              .map(violation => (
                <div key={violation.id} className={`border-l-4 p-3 rounded-lg ${severityColors[violation.severity]}`}>
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="font-medium">{violation.title}</div>
                      <div className="text-sm text-gray-600 mt-1">{violation.description}</div>
                      <div className="text-xs text-gray-500 mt-2">
                        Detected: {new Date(violation.detected_at).toLocaleDateString()}
                      </div>
                    </div>
                    <Button 
                      size="sm" 
                      onClick={() => onResolveViolation(violation.id)}
                      className="ml-4"
                    >
                      Resolve
                    </Button>
                  </div>
                </div>
              ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderViolations = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Compliance Violations</h3>
        <div className="flex gap-2">
          <select 
            value={violationFilter.severity} 
            onChange={(e) => setViolationFilter(prev => ({ ...prev, severity: e.target.value }))}
            className="px-3 py-1 border rounded"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select 
            value={violationFilter.status} 
            onChange={(e) => setViolationFilter(prev => ({ ...prev, status: e.target.value }))}
            className="px-3 py-1 border rounded"
          >
            <option value="all">All Status</option>
            <option value="open">Open</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>
      </div>

      <div className="grid gap-3">
        {filteredViolations.map(violation => (
          <Card key={violation.id} className={`border-l-4 ${
            violation.severity === 'critical' ? 'border-red-500' :
            violation.severity === 'high' ? 'border-orange-500' :
            violation.severity === 'medium' ? 'border-yellow-500' :
            'border-blue-500'
          }`}>
            <CardContent className="p-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant={violation.severity === 'critical' || violation.severity === 'high' ? 'destructive' : 'secondary'}>
                      {violation.severity.toUpperCase()}
                    </Badge>
                    <span className="text-sm text-gray-600">{violation.type}</span>
                    <span className="text-xs text-gray-500">
                      {new Date(violation.detected_at).toLocaleDateString()}
                    </span>
                  </div>
                  <h4 className="font-medium text-lg">{violation.title}</h4>
                  <p className="text-sm text-gray-600 mt-1">{violation.description}</p>
                  {violation.affected_resources.length > 0 && (
                    <div className="text-xs text-gray-500 mt-2">
                      Affected: {violation.affected_resources.slice(0, 3).join(', ')}
                      {violation.affected_resources.length > 3 && ` +${violation.affected_resources.length - 3} more`}
                    </div>
                  )}
                  {violation.remediation_steps.length > 0 && (
                    <div className="mt-2">
                      <div className="text-sm font-medium text-gray-700">Remediation Steps:</div>
                      <ul className="text-xs text-gray-600 list-disc list-inside mt-1">
                        {violation.remediation_steps.slice(0, 2).map((step, index) => (
                          <li key={index}>{step}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
                <div className="flex gap-1 ml-4">
                  {violation.status === 'open' && (
                    <Button
                      size="sm"
                      onClick={() => onResolveViolation(violation.id)}
                      className="px-2 py-1 text-xs"
                    >
                      Resolve
                    </Button>
                  )}
                  <Badge variant="outline" className="text-xs">
                    {violation.status}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredViolations.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No violations matching current filters
        </div>
      )}
    </div>
  );

  const renderAuditTrail = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Audit Trail</h3>
        <Button onClick={onExportAuditReport}>
          Export Report
        </Button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border border-gray-200 rounded-lg">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Timestamp</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Resource</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Result</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {auditTrail.slice(0, 20).map(entry => (
              <tr key={entry.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm text-gray-900">
                  {new Date(entry.timestamp).toLocaleString()}
                </td>
                <td className="px-4 py-3 text-sm text-gray-900">{entry.user_id}</td>
                <td className="px-4 py-3 text-sm text-gray-900">{entry.action}</td>
                <td className="px-4 py-3 text-sm text-gray-900">
                  {entry.resource_type}/{entry.resource_id}
                </td>
                <td className="px-4 py-3 text-sm">
                  <Badge variant={
                    entry.result === 'success' ? 'default' :
                    entry.result === 'failure' ? 'destructive' :
                    'secondary'
                  }>
                    {entry.result}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Compliance Dashboard</h2>
        <div className="flex gap-2">
          <Button
            variant={selectedTab === 'overview' ? 'default' : 'outline'}
            onClick={() => setSelectedTab('overview')}
          >
            Overview
          </Button>
          <Button
            variant={selectedTab === 'violations' ? 'default' : 'outline'}
            onClick={() => setSelectedTab('violations')}
          >
            Violations ({violations.filter(v => v.status === 'open').length})
          </Button>
          <Button
            variant={selectedTab === 'audit' ? 'default' : 'outline'}
            onClick={() => setSelectedTab('audit')}
          >
            Audit Trail
          </Button>
        </div>
      </div>

      {violationCounts.critical > 0 && (
        <Alert>
          <div className="font-medium">
            {violationCounts.critical} critical violation{violationCounts.critical > 1 ? 's' : ''} require immediate attention
          </div>
        </Alert>
      )}

      {selectedTab === 'overview' && renderOverview()}
      {selectedTab === 'violations' && renderViolations()}
      {selectedTab === 'audit' && renderAuditTrail()}
    </div>
  );
}