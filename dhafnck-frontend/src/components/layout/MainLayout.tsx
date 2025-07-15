import React, { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../store/store';
import { uiActions, sessionActions } from '../../store/store';
import { store } from '../../store/store';
import { NavigationSidebar } from './NavigationSidebar';
import { HeaderBar } from './HeaderBar';
import { NotificationSystem } from '../common/NotificationSystem';
import { ModalStack } from '../common/ModalStack';
import { CommandPalette } from '../common/CommandPalette';
import { useMcpIntegration } from '../../hooks/useWebSocketIntegration';

interface MainLayoutProps {
  children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const dispatch = useAppDispatch();
  const { currentView, sidebarOpen, theme } = useAppSelector(state => state.ui);
  const { currentAgent, selectedProject, preferences } = useAppSelector(state => state.session);
  const { connection } = useAppSelector(state => state.system);

  // Initialize MCP integration (replaced WebSocket)
  // Temporarily disabled to fix infinite render loop
  // useMcpIntegration();

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement;
    const effectiveTheme = theme === 'auto' 
      ? window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
      : theme;
    
    root.classList.toggle('dark', effectiveTheme === 'dark');
  }, [theme]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Command palette (Ctrl/Cmd + K)
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        dispatch(uiActions.toggleCommandPalette());
      }
      
      // Toggle sidebar (Ctrl/Cmd + B)
      if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        e.preventDefault();
        dispatch(uiActions.toggleSidebar());
      }
      
      // Escape key handling
      if (e.key === 'Escape') {
        // Close command palette if open
        const { commandPaletteOpen, modalStack } = store.getState().ui;
        if (commandPaletteOpen) {
          dispatch(uiActions.setCommandPaletteOpen(false));
        } else if (modalStack.length > 0) {
          dispatch(uiActions.popModal());
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [dispatch]);

  // Auto-refresh based on preferences
  useEffect(() => {
    if (!preferences.autoRefresh) return;

    const interval = setInterval(() => {
      // Trigger data refresh based on current view
      // This could dispatch actions to refresh current view data
    }, preferences.refreshInterval);

    return () => clearInterval(interval);
  }, [preferences.autoRefresh, preferences.refreshInterval]);

  const themeClass = theme === 'dark' ? 'dark' : '';

  return (
    <div className={`min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors ${themeClass}`}>
      {/* Header */}
      <HeaderBar />
      
      <div className="flex">
        {/* Sidebar */}
        <NavigationSidebar 
          isOpen={sidebarOpen}
          currentView={currentView}
          onNavigate={(view) => dispatch(uiActions.setCurrentView(view))}
          onToggle={() => dispatch(uiActions.toggleSidebar())}
        />

        {/* Main Content Area */}
        <main className={`flex-1 transition-all duration-300 ${
          sidebarOpen ? 'ml-64' : 'ml-0'
        }`}>
          <div className="p-6">
            {/* Status Bar */}
            <div className="mb-6 flex items-center justify-between">
              <div className="flex items-center gap-4">
                {/* Current Agent Indicator */}
                {currentAgent && (
                  <div className="flex items-center gap-2 px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-lg">
                    <span className="text-sm">🤖</span>
                    <span className="text-sm font-medium">{currentAgent.name}</span>
                    <div className={`w-2 h-2 rounded-full ${
                      currentAgent.status === 'active' ? 'bg-green-500' :
                      currentAgent.status === 'inactive' ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`} />
                  </div>
                )}

                {/* Selected Project Indicator */}
                {selectedProject && (
                  <div className="flex items-center gap-2 px-3 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded-lg">
                    <span className="text-sm">📁</span>
                    <span className="text-sm font-medium">{selectedProject.name}</span>
                  </div>
                )}
              </div>

              {/* Connection Status */}
              <div className={`flex items-center gap-2 px-3 py-1 rounded-lg text-sm font-medium ${
                connection.status === 'healthy' 
                  ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200' :
                connection.status === 'degraded' 
                  ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200' :
                  'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
              }`}>
                <div className={`w-2 h-2 rounded-full ${
                  connection.status === 'healthy' ? 'bg-green-500' :
                  connection.status === 'degraded' ? 'bg-yellow-500' :
                  'bg-red-500'
                }`} />
                <span>{connection.status}</span>
              </div>
            </div>

            {/* Page Content */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 min-h-[calc(100vh-10rem)]">
              {children}
            </div>
          </div>
        </main>
      </div>

      {/* Global Components */}
      <NotificationSystem />
      <CommandPalette />
      <ModalStack />
    </div>
  );
}

