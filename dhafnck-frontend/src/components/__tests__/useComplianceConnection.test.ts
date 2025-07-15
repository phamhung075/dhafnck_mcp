import { renderHook, act, waitFor } from '@testing-library/react';
import { useComplianceConnection } from '../../hooks/useComplianceConnection';
import { mcpApi } from '../../api/enhanced';

// Mock the mcpApi
jest.mock('../../api/enhanced', () => ({
  mcpApi: {
    manageCompliance: jest.fn(),
    manageConnection: jest.fn()
  }
}));

const mockMcpApi = mcpApi as jest.Mocked<typeof mcpApi>;

describe('useComplianceConnection', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn()
      },
      writable: true
    });
  });

  test('initializes with default state', async () => {
    mockMcpApi.manageCompliance.mockResolvedValue({
      success: true,
      data: {
        compliance_score: 0.85,
        violations: [],
        audit_trail: []
      }
    });

    mockMcpApi.manageConnection.mockResolvedValue({
      success: true,
      data: {
        status: { status: 'healthy', response_time: 45 }
      }
    });

    const { result } = renderHook(() => useComplianceConnection());

    expect(result.current.complianceStatus).toBeNull();
    expect(result.current.violations).toEqual([]);
    expect(result.current.auditTrail).toEqual([]);
    expect(result.current.connectionStatus).toBeNull();
    expect(result.current.loading.compliance).toBe(false);
    expect(result.current.wsStatus).toBe('disconnected');
  });

  test('runs compliance audit successfully', async () => {
    const mockResponse = {
      success: true,
      data: {
        compliance_score: 0.85,
        total_violations: 5,
        resolved_violations: 3,
        violations: [
          {
            id: 'v1',
            type: 'security',
            severity: 'high',
            title: 'Test violation',
            description: 'Test description',
            status: 'open'
          }
        ]
      }
    };

    mockMcpApi.manageCompliance.mockResolvedValue(mockResponse);
    mockMcpApi.manageConnection.mockResolvedValue({
      success: true,
      data: { status: { status: 'healthy' } }
    });

    const { result } = renderHook(() => useComplianceConnection());

    await act(async () => {
      await result.current.actions.runComplianceAudit();
    });

    await waitFor(() => {
      expect(result.current.complianceStatus?.compliance_score).toBe(0.85);
      expect(result.current.violations).toHaveLength(1);
      expect(result.current.violations[0].title).toBe('Test violation');
    });

    expect(mockMcpApi.manageCompliance).toHaveBeenCalledWith('get_compliance_dashboard');
  });

  test('handles compliance audit error', async () => {
    const error = new Error('API Error');
    mockMcpApi.manageCompliance.mockRejectedValue(error);
    mockMcpApi.manageConnection.mockResolvedValue({
      success: true,
      data: { status: { status: 'healthy' } }
    });

    const { result } = renderHook(() => useComplianceConnection());

    await act(async () => {
      await result.current.actions.runComplianceAudit();
    });

    await waitFor(() => {
      expect(result.current.errors.compliance).toBe('API Error');
    });
  });

  test('gets audit trail successfully', async () => {
    const mockAuditResponse = {
      success: true,
      data: {
        audit_trail: [
          {
            id: 'a1',
            timestamp: '2024-01-15T10:00:00Z',
            user_id: 'admin',
            action: 'resolve_violation',
            result: 'success'
          }
        ]
      }
    };

    mockMcpApi.manageCompliance
      .mockResolvedValueOnce({ success: true, data: {} }) // Initial compliance audit
      .mockResolvedValueOnce(mockAuditResponse); // Audit trail

    mockMcpApi.manageConnection.mockResolvedValue({
      success: true,
      data: { status: { status: 'healthy' } }
    });

    const { result } = renderHook(() => useComplianceConnection());

    await act(async () => {
      await result.current.actions.getAuditTrail(50);
    });

    await waitFor(() => {
      expect(result.current.auditTrail).toHaveLength(1);
      expect(result.current.auditTrail[0].action).toBe('resolve_violation');
    });

    expect(mockMcpApi.manageCompliance).toHaveBeenCalledWith('get_audit_trail', { limit: 50 });
  });

  test('resolves violation successfully', async () => {
    // Setup initial state with violations
    const initialResponse = {
      success: true,
      data: {
        violations: [
          { id: 'v1', status: 'open', title: 'Test violation' },
          { id: 'v2', status: 'open', title: 'Another violation' }
        ]
      }
    };

    mockMcpApi.manageCompliance.mockResolvedValue(initialResponse);
    mockMcpApi.manageConnection.mockResolvedValue({
      success: true,
      data: { status: { status: 'healthy' } }
    });

    const { result } = renderHook(() => useComplianceConnection());

    // Wait for initial load
    await waitFor(() => {
      expect(result.current.violations).toHaveLength(2);
    });

    await act(async () => {
      await result.current.actions.resolveViolation('v1');
    });

    expect(result.current.violations[0].status).toBe('resolved');
    expect(result.current.violations[1].status).toBe('open');
  });

  test('exports audit report with CSV format', async () => {
    const mockAuditEntries = [
      {
        id: 'a1',
        timestamp: '2024-01-15T10:00:00Z',
        user_id: 'admin',
        action: 'test_action',
        resource_type: 'test_resource',
        resource_id: 'r1',
        result: 'success',
        ip_address: '192.168.1.1'
      }
    ];

    // Mock URL.createObjectURL and related functions
    global.URL.createObjectURL = jest.fn(() => 'blob:mock-url');
    global.URL.revokeObjectURL = jest.fn();
    
    // Mock document.createElement and click
    const mockAnchor = {
      href: '',
      download: '',
      click: jest.fn()
    };
    jest.spyOn(document, 'createElement').mockReturnValue(mockAnchor as any);

    mockMcpApi.manageCompliance.mockResolvedValue({
      success: true,
      data: { audit_trail: mockAuditEntries }
    });
    mockMcpApi.manageConnection.mockResolvedValue({
      success: true,
      data: { status: { status: 'healthy' } }
    });

    const { result } = renderHook(() => useComplianceConnection());

    // Wait for audit trail to load
    await waitFor(() => {
      expect(result.current.auditTrail).toHaveLength(1);
    });

    const filters = {
      dateFrom: '',
      dateTo: '',
      user: '',
      action: '',
      result: 'all',
      resourceType: 'all'
    };

    await act(async () => {
      await result.current.actions.exportAuditReport(filters);
    });

    expect(mockAnchor.click).toHaveBeenCalled();
    expect(mockAnchor.download).toContain('audit-report-');
  });

  test('runs connection diagnostics successfully', async () => {
    const mockHealthResponse = {
      success: true,
      data: { status: { status: 'healthy', response_time: 45 } }
    };

    const mockConnectionHealthResponse = {
      success: true,
      data: {
        overall_status: 'healthy',
        diagnostic_results: [
          { test_name: 'ping', status: 'passed', response_time: 10 }
        ]
      }
    };

    const mockCapabilitiesResponse = {
      success: true,
      data: {
        version: '2.1.0',
        features: ['real_time_updates'],
        tools: ['manage_task']
      }
    };

    mockMcpApi.manageConnection
      .mockResolvedValueOnce(mockHealthResponse)
      .mockResolvedValueOnce(mockConnectionHealthResponse)
      .mockResolvedValueOnce(mockCapabilitiesResponse);

    mockMcpApi.manageCompliance.mockResolvedValue({
      success: true,
      data: {}
    });

    const { result } = renderHook(() => useComplianceConnection());

    await act(async () => {
      await result.current.actions.runConnectionDiagnostics();
    });

    await waitFor(() => {
      expect(result.current.connectionStatus?.status).toBe('healthy');
      expect(result.current.diagnosticResults).toHaveLength(1);
      expect(result.current.serverCapabilities?.version).toBe('2.1.0');
    });
  });

  test('tests connection successfully', async () => {
    const mockResponse = {
      success: true,
      data: { status: { status: 'healthy', response_time: 35 } }
    };

    mockMcpApi.manageConnection.mockResolvedValue(mockResponse);
    mockMcpApi.manageCompliance.mockResolvedValue({
      success: true,
      data: {}
    });

    const { result } = renderHook(() => useComplianceConnection());

    await act(async () => {
      await result.current.actions.testConnection();
    });

    await waitFor(() => {
      expect(result.current.connectionStatus?.response_time).toBe(35);
    });

    expect(mockMcpApi.manageConnection).toHaveBeenCalledWith('health_check');
  });

  test('registers for updates successfully', async () => {
    const mockResponse = {
      success: true,
      data: {}
    };

    mockMcpApi.manageConnection.mockResolvedValue(mockResponse);
    mockMcpApi.manageCompliance.mockResolvedValue({
      success: true,
      data: {}
    });

    const { result } = renderHook(() => useComplianceConnection());

    await act(async () => {
      await result.current.actions.registerForUpdates('test-session');
    });

    await waitFor(() => {
      expect(result.current.wsStatus).toBe('connected');
    });

    expect(mockMcpApi.manageConnection).toHaveBeenCalledWith('register_updates', {
      session_id: 'test-session',
      client_info: {
        type: 'compliance_dashboard',
        version: '1.0.0',
        features: ['real_time_updates', 'compliance_monitoring']
      }
    });
  });

  test('runs specific test successfully', async () => {
    mockMcpApi.manageCompliance.mockResolvedValue({
      success: true,
      data: {}
    });
    mockMcpApi.manageConnection.mockResolvedValue({
      success: true,
      data: { status: { status: 'healthy' } }
    });

    const { result } = renderHook(() => useComplianceConnection());

    await act(async () => {
      await result.current.actions.runSpecificTest('ping');
    });

    await waitFor(() => {
      const pingResult = result.current.diagnosticResults.find(r => r.test_name === 'ping');
      expect(pingResult).toBeDefined();
      expect(pingResult?.test_name).toBe('ping');
    });
  });

  test('clears errors successfully', async () => {
    mockMcpApi.manageCompliance.mockRejectedValue(new Error('Test error'));
    mockMcpApi.manageConnection.mockResolvedValue({
      success: true,
      data: { status: { status: 'healthy' } }
    });

    const { result } = renderHook(() => useComplianceConnection());

    // Generate an error
    await act(async () => {
      await result.current.actions.runComplianceAudit();
    });

    await waitFor(() => {
      expect(result.current.errors.compliance).toBe('Test error');
    });

    // Clear errors
    await act(async () => {
      result.current.actions.clearErrors();
    });

    expect(result.current.errors.compliance).toBeNull();
    expect(result.current.errors.connection).toBeNull();
    expect(result.current.errors.diagnostics).toBeNull();
    expect(result.current.errors.audit).toBeNull();
  });
});