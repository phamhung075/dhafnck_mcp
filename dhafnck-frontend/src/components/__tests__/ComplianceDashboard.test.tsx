import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ComplianceDashboard } from '../ComplianceDashboard';

// Mock data
const mockComplianceStatus = {
  compliance_score: 85,
  total_violations: 10,
  resolved_violations: 7,
  framework_breakdown: {
    'SOC 2': { score: 90, violations: 2 },
    'ISO 27001': { score: 80, violations: 3 }
  },
  last_audit: '2024-01-15T10:00:00Z',
  trends: {
    daily: [85, 86, 84, 85],
    weekly: [83, 85, 87, 85],
    monthly: [80, 82, 85, 85]
  }
};

const mockViolations = [
  {
    id: 'v1',
    type: 'security' as const,
    severity: 'critical' as const,
    title: 'Unauthorized access detected',
    description: 'Multiple failed login attempts from suspicious IP',
    affected_resources: ['login-service', 'auth-db'],
    detected_at: '2024-01-15T09:00:00Z',
    status: 'open' as const,
    remediation_steps: ['Block suspicious IP', 'Review auth logs'],
    compliance_framework: ['SOC 2', 'ISO 27001']
  },
  {
    id: 'v2',
    type: 'data_privacy' as const,
    severity: 'medium' as const,
    title: 'Data retention policy violation',
    description: 'Old user data not properly archived',
    affected_resources: ['user-db'],
    detected_at: '2024-01-14T15:30:00Z',
    status: 'acknowledged' as const,
    remediation_steps: ['Update retention policy', 'Archive old data'],
    compliance_framework: ['GDPR']
  }
];

const mockAuditTrail = [
  {
    id: 'a1',
    timestamp: '2024-01-15T10:30:00Z',
    user_id: 'admin@example.com',
    action: 'resolve_violation',
    resource_type: 'compliance_violation',
    resource_id: 'v1',
    details: { resolution: 'blocked_ip' },
    ip_address: '192.168.1.1',
    user_agent: 'Mozilla/5.0',
    result: 'success' as const
  }
];

const mockProps = {
  complianceStatus: mockComplianceStatus,
  violations: mockViolations,
  auditTrail: mockAuditTrail,
  onRunAudit: jest.fn(),
  onResolveViolation: jest.fn(),
  onExportAuditReport: jest.fn(),
  onUpdateCompliancePolicy: jest.fn()
};

describe('ComplianceDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders compliance dashboard with correct score', () => {
    render(<ComplianceDashboard {...mockProps} />);
    
    expect(screen.getByText('Compliance Dashboard')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  test('displays violation counts by severity', () => {
    render(<ComplianceDashboard {...mockProps} />);
    
    // Check for critical violations count
    expect(screen.getByText('1')).toBeInTheDocument(); // Critical count
    // Check for medium violations count
    expect(screen.getByText('1')).toBeInTheDocument(); // Medium count
  });

  test('shows framework breakdown', () => {
    render(<ComplianceDashboard {...mockProps} />);
    
    expect(screen.getByText('SOC 2')).toBeInTheDocument();
    expect(screen.getByText('ISO 27001')).toBeInTheDocument();
    expect(screen.getByText('90%')).toBeInTheDocument();
    expect(screen.getByText('80%')).toBeInTheDocument();
  });

  test('can switch between tabs', () => {
    render(<ComplianceDashboard {...mockProps} />);
    
    // Click on violations tab
    fireEvent.click(screen.getByText(/Violations/));
    expect(screen.getByText('Compliance Violations')).toBeInTheDocument();
    
    // Click on audit tab
    fireEvent.click(screen.getByText('Audit Trail'));
    expect(screen.getByText('Audit Trail')).toBeInTheDocument();
  });

  test('displays violations with correct information', () => {
    render(<ComplianceDashboard {...mockProps} />);
    
    // Switch to violations tab
    fireEvent.click(screen.getByText(/Violations/));
    
    expect(screen.getByText('Unauthorized access detected')).toBeInTheDocument();
    expect(screen.getByText('Data retention policy violation')).toBeInTheDocument();
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
    expect(screen.getByText('MEDIUM')).toBeInTheDocument();
  });

  test('can filter violations', () => {
    render(<ComplianceDashboard {...mockProps} />);
    
    // Switch to violations tab
    fireEvent.click(screen.getByText(/Violations/));
    
    // Filter by critical severity
    const severityFilter = screen.getByDisplayValue('All Severities');
    fireEvent.change(severityFilter, { target: { value: 'critical' } });
    
    expect(screen.getByText('Unauthorized access detected')).toBeInTheDocument();
    expect(screen.queryByText('Data retention policy violation')).not.toBeInTheDocument();
  });

  test('can resolve violations', async () => {
    render(<ComplianceDashboard {...mockProps} />);
    
    // Switch to violations tab
    fireEvent.click(screen.getByText(/Violations/));
    
    // Click resolve button for open violation
    const resolveButtons = screen.getAllByText('Resolve');
    fireEvent.click(resolveButtons[0]);
    
    await waitFor(() => {
      expect(mockProps.onResolveViolation).toHaveBeenCalledWith('v1');
    });
  });

  test('runs compliance audit', async () => {
    render(<ComplianceDashboard {...mockProps} />);
    
    const runAuditButton = screen.getByText('Run Full Audit');
    fireEvent.click(runAuditButton);
    
    await waitFor(() => {
      expect(mockProps.onRunAudit).toHaveBeenCalled();
    });
  });

  test('exports audit report', async () => {
    render(<ComplianceDashboard {...mockProps} />);
    
    // Switch to audit tab
    fireEvent.click(screen.getByText('Audit Trail'));
    
    const exportButton = screen.getByText('Export Report');
    fireEvent.click(exportButton);
    
    await waitFor(() => {
      expect(mockProps.onExportAuditReport).toHaveBeenCalled();
    });
  });

  test('shows critical alert when critical violations exist', () => {
    render(<ComplianceDashboard {...mockProps} />);
    
    expect(screen.getByText('1 critical violation require immediate attention')).toBeInTheDocument();
  });

  test('displays audit trail information', () => {
    render(<ComplianceDashboard {...mockProps} />);
    
    // Switch to audit tab
    fireEvent.click(screen.getByText('Audit Trail'));
    
    expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    expect(screen.getByText('resolve_violation')).toBeInTheDocument();
    expect(screen.getByText('success')).toBeInTheDocument();
  });

  test('handles empty violations state', () => {
    const emptyProps = {
      ...mockProps,
      violations: []
    };
    
    render(<ComplianceDashboard {...emptyProps} />);
    
    // Switch to violations tab
    fireEvent.click(screen.getByText(/Violations/));
    
    expect(screen.getByText('No violations matching current filters')).toBeInTheDocument();
  });
});