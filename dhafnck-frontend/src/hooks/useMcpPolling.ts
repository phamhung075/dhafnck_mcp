/**
 * MCP Polling Hook
 * Replaces WebSocket with MCP-based polling for real-time updates
 */

import { useEffect, useRef, useCallback } from 'react';
import { useAppDispatch } from '../store/store';
import { systemActions, uiActions } from '../store/store';
import { mcpApi as api } from '../api/enhanced';
import { config } from '../config';
import type { 
  SystemHealthStatus, 
  ConnectionStatus,
  Notification 
} from '../types/application';

interface McpPollingOptions {
  enabled?: boolean;
  healthCheckInterval?: number;
  statusUpdateInterval?: number;
  onError?: (error: Error) => void;
}

export function useMcpPolling(options: McpPollingOptions = {}) {
  const {
    enabled = true,
    healthCheckInterval = config.polling.healthCheck,
    statusUpdateInterval = config.polling.statusUpdate,
    onError
  } = options;

  const dispatch = useAppDispatch();
  const healthIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const statusIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isPollingRef = useRef(false);

  // Check system health
  const checkSystemHealth = useCallback(async () => {
    try {
      const response = await api.manageConnection('health_check', { include_details: true });
      if (response.data) {
        // Map the health check response to SystemHealthStatus
        const healthData = response.data as any;
        const systemHealth: SystemHealthStatus = {
          overall_score: healthData.overall_score || healthData.health_score || 100,
          components: {
            database: { 
              status: healthData.components?.database?.status || healthData.database_status || 'healthy', 
              score: healthData.components?.database?.score || healthData.database_score || 100 
            },
            mcp_server: { 
              status: healthData.components?.mcp_server?.status || healthData.mcp_server_status || 'healthy', 
              score: healthData.components?.mcp_server?.score || healthData.mcp_server_score || 100 
            },
            authentication: { 
              status: healthData.components?.authentication?.status || healthData.auth_status || 'healthy', 
              score: healthData.components?.authentication?.score || healthData.auth_score || 100 
            },
            context_system: { 
              status: healthData.components?.context_system?.status || healthData.context_system_status || 'healthy', 
              score: healthData.components?.context_system?.score || healthData.context_system_score || 100 
            }
          },
          last_check: healthData.last_check || new Date().toISOString(),
          uptime: healthData.uptime || '0 hours'
        };
        
        dispatch(systemActions.setSystemHealth(systemHealth));
        
        // Update connection status based on health
        const connectionStatus: ConnectionStatus = {
          status: 'healthy',
          latency: 0,
          uptime_percentage: 100,
          active_connections: 1,
          last_check: new Date().toISOString(),
          error_rate: 0
        };
        dispatch(systemActions.setConnectionStatus(connectionStatus));
      }
    } catch (error) {
      console.error('Health check failed:', error);
      onError?.(error as Error);
      
      // Set degraded connection status on error
      const connectionStatus: ConnectionStatus = {
        status: 'degraded',
        latency: 0,
        uptime_percentage: 50,
        active_connections: 0,
        last_check: new Date().toISOString(),
        error_rate: 100
      };
      dispatch(systemActions.setConnectionStatus(connectionStatus));
    }
  }, [dispatch, onError]);

  // Check compliance status
  const checkComplianceStatus = useCallback(async () => {
    try {
      const response = await api.manageCompliance('get_compliance_dashboard');
      if (response.data) {
        dispatch(systemActions.setComplianceStatus(response.data));
      }
    } catch (error) {
      console.error('Compliance check failed:', error);
      onError?.(error as Error);
    }
  }, [dispatch, onError]);

  // Get server status and updates
  const checkServerStatus = useCallback(async () => {
    try {
      const response = await api.manageConnection('status', { include_details: true });
      if (response.data) {
        // Process any pending notifications or updates
        const serverStatus = response.data as any;
        
        // Add notifications if any
        if (serverStatus.notifications) {
          serverStatus.notifications.forEach((notification: Notification) => {
            dispatch(systemActions.addNotification(notification));
            dispatch(uiActions.addUINotification({
              id: notification.id || Date.now().toString(),
              type: notification.type || 'info',
              title: notification.title,
              message: notification.message,
              timestamp: notification.timestamp,
              read: notification.read || false,
              autoClose: notification.type !== 'error',
              duration: notification.type === 'error' ? undefined : 5000
            }));
          });
        }
      }
    } catch (error) {
      console.error('Status check failed:', error);
      onError?.(error as Error);
    }
  }, [dispatch, onError]);

  // Start polling
  const startPolling = useCallback(() => {
    if (isPollingRef.current) return;
    
    isPollingRef.current = true;
    
    // Initial checks
    checkSystemHealth();
    checkComplianceStatus();
    checkServerStatus();
    
    // Set up intervals
    healthIntervalRef.current = setInterval(() => {
      checkSystemHealth();
      checkComplianceStatus();
    }, healthCheckInterval);
    
    statusIntervalRef.current = setInterval(() => {
      checkServerStatus();
    }, statusUpdateInterval);
  }, [checkSystemHealth, checkComplianceStatus, checkServerStatus, healthCheckInterval, statusUpdateInterval]);

  // Stop polling
  const stopPolling = useCallback(() => {
    isPollingRef.current = false;
    
    if (healthIntervalRef.current) {
      clearInterval(healthIntervalRef.current);
      healthIntervalRef.current = null;
    }
    
    if (statusIntervalRef.current) {
      clearInterval(statusIntervalRef.current);
      statusIntervalRef.current = null;
    }
  }, []);

  // Effect to manage polling lifecycle
  useEffect(() => {
    if (enabled) {
      startPolling();
    } else {
      stopPolling();
    }
    
    return () => {
      stopPolling();
    };
  }, [enabled, startPolling, stopPolling]);

  return {
    isPolling: isPollingRef.current,
    checkSystemHealth,
    checkComplianceStatus,
    checkServerStatus,
    startPolling,
    stopPolling
  };
}