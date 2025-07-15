/**
 * MCP Integration Hook (formerly WebSocket)
 * Uses MCP polling instead of WebSocket for real-time updates
 */

import { useEffect } from 'react';
import { useAppDispatch } from '../store/store';
import { systemActions, sessionActions, dataActions, uiActions } from '../store/store';
import { useMcpPolling } from './useMcpPolling';
import type { 
  SystemHealthStatus, 
  ComplianceStatus, 
  TaskUpdate, 
  AgentStatusUpdate, 
  Notification 
} from '../types/application';

interface McpIntegrationProps {
  onSystemHealthUpdate?: (health: SystemHealthStatus) => void;
  onComplianceUpdate?: (compliance: ComplianceStatus) => void;
  onTaskUpdate?: (taskUpdate: TaskUpdate) => void;
  onAgentStatusUpdate?: (agentUpdate: AgentStatusUpdate) => void;
  onNotification?: (notification: Notification) => void;
  onConnectionStatusChange?: (status: 'connected' | 'disconnected' | 'reconnecting') => void;
}

// Deprecated: WebSocketManager replaced with MCP polling
// export class WebSocketManager { ... }

export function useMcpIntegration() {
  const dispatch = useAppDispatch();
  
  // Use MCP polling instead of WebSocket
  const { isPolling, checkSystemHealth, checkComplianceStatus } = useMcpPolling({
    enabled: true,
    healthCheckInterval: 300000, // 5 minutes (reduced from 30 seconds)
    statusUpdateInterval: 120000, // 2 minutes (reduced from 10 seconds)
    onError: (error) => {
      console.error('MCP polling error:', error);
      dispatch(uiActions.addUINotification({
        id: `mcp_error_${Date.now()}`,
        type: 'error',
        title: 'Connection Error',
        message: 'Failed to connect to MCP server. Some features may be unavailable.',
        timestamp: new Date().toISOString(),
        read: false,
        autoClose: false
      }));
    }
  });

  // Set connection status only once on mount
  useEffect(() => {
    if (isPolling) {
      dispatch(systemActions.setConnectionStatus({
        status: 'healthy' as const,
        latency: 0,
        uptime_percentage: 100,
        active_connections: 1,
        last_check: new Date().toISOString(),
        error_rate: 0
      }));
    } else {
      dispatch(systemActions.setConnectionStatus({
        status: 'critical' as const,
        latency: 0,
        uptime_percentage: 0,
        active_connections: 0,
        last_check: new Date().toISOString(),
        error_rate: 100
      }));
    }
  }, [dispatch]); // Remove isPolling from dependencies to prevent re-runs
  
  return {
    isConnected: isPolling,
    checkHealth: checkSystemHealth,
    checkCompliance: checkComplianceStatus
  };
}