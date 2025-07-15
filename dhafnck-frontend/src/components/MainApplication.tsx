import React, { useEffect, useState } from 'react';
import { Provider } from 'react-redux';
import { store } from '../store/store';
import { MainLayout } from './layout/MainLayout';
import { ViewRouter } from './navigation/ViewRouter';
import { useAppDispatch, useAppSelector } from '../store/store';
import { systemActions, sessionActions, dataActions } from '../store/store';
import { config } from '../config';
import type { SystemHealthStatus } from '../types/application';

interface MainApplicationProps {
  initialAgent?: string;
  initialProject?: string;
}

function MainApplicationContent({ 
  initialAgent, 
  initialProject 
}: MainApplicationProps) {
  const dispatch = useAppDispatch();
  const systemError = useAppSelector(state => state.system.errors.initialization);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isInitializing, setIsInitializing] = useState(false);

  // Initialize application on mount
  useEffect(() => {
    // Prevent multiple initialization attempts
    if (isInitialized || isInitializing) {
      return;
    }

    const initializeApplication = async () => {
      setIsInitializing(true);
      
      try {
        // Simplified initialization - skip MCP calls for now
        
        // Set default system health
        const defaultSystemHealth: SystemHealthStatus = {
          overall_score: 100,
          components: {
            database: { status: 'healthy', score: 100 },
            mcp_server: { status: 'degraded', score: 0 },
            authentication: { status: 'healthy', score: 100 },
            context_system: { status: 'healthy', score: 100 }
          },
          last_check: new Date().toISOString(),
          uptime: '0 hours'
        };
        
        dispatch(systemActions.setSystemHealth(defaultSystemHealth));
        // Set sample projects for demo
        dispatch(dataActions.setProjects([
          {
            id: 'proj-1',
            name: 'Sample Project',
            description: 'A sample project for demonstration',
            status: 'active',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }
        ]));
        
        // Set default compliance status
        dispatch(systemActions.setComplianceStatus({
          overall_score: 95,
          compliance_rate: 0.95,
          total_operations: 100,
          violations: 5,
          policies: {
            security: { score: 98, violations: 1 },
            data_protection: { score: 95, violations: 2 },
            access_control: { score: 92, violations: 2 }
          },
          last_audit: new Date().toISOString()
        }));
        
        // Set default connection status
        dispatch(systemActions.setConnectionStatus({
          status: 'degraded',
          latency: 0,
          uptime_percentage: 0,
          active_connections: 0,
          last_check: new Date().toISOString(),
          error_rate: 0
        }));
        
        if (initialAgent) {
          dispatch(sessionActions.setCurrentAgent({
            id: initialAgent,
            name: initialAgent,
            status: 'active',
            project_id: initialProject || ''
          }));
        }
        
        // Small delay to ensure state updates
        await new Promise(resolve => setTimeout(resolve, 100));
        
        setIsInitialized(true);
      } catch (error) {
        console.error('Error during initialization:', error);
        setIsInitialized(true); // Force initialization even on error
      } finally {
        setIsInitializing(false);
        dispatch(systemActions.setLoading({ key: 'initialization', loading: false }));
      }
    };
    
    initializeApplication();
  }, []); // Remove dependencies to ensure it only runs once

  // Show loading screen during initialization
  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Initializing DhafnckMCP Dashboard
          </h2>
          <p className="text-gray-600">Please wait while we load the system...</p>
          {systemError && (
            <div className="mt-8 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 text-sm">{systemError}</p>
              <p className="text-red-600 text-xs mt-2">
                Please ensure the MCP server is running on {config.mcp.baseUrl}
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <MainLayout>
      <ViewRouter />
    </MainLayout>
  );
}

export function MainApplication(props: MainApplicationProps) {
  return (
    <Provider store={store}>
      <MainApplicationContent {...props} />
    </Provider>
  );
}