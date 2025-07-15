/**
 * Integrated Navigation System
 * Provides unified navigation with agent switcher, project selector,
 * system health indicators, and notifications
 */

import React, { useState, useCallback, useMemo } from 'react';
import { 
  Search, 
  Bell, 
  Settings, 
  User, 
  ChevronDown, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Menu, 
  X,
  Command,
  Zap,
  BarChart3,
  GitBranch,
  Users
} from 'lucide-react';
import { useSystemIntegration } from '../integration/SystemIntegration';
import { useAppDispatch, useAppSelector, uiActions, sessionActions } from '../store/store';
import { useAriaLive, AccessibleButton, useFocusManagement } from '../utils/AccessibilityUtils';
import type { 
  User as UserType, 
  Agent, 
  Project, 
  SystemHealthStatus, 
  Notification,
  ViewType 
} from '../types/application';

interface IntegratedNavigationProps {
  currentUser: UserType;
  projects: Project[];
  currentAgent: Agent | null;
  systemHealth: SystemHealthStatus | null;
  notifications: Notification[];
  onNavigate: (route: string) => void;
  onAgentSwitch: (agent: Agent) => Promise<void>;
  onProjectSwitch: (project: Project) => void;
}

// Navigation Views Configuration
const NAVIGATION_VIEWS: Array<{
  id: ViewType;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  description: string;
}> = [
  { id: 'dashboard', label: 'Dashboard', icon: BarChart3, description: 'System overview and metrics' },
  { id: 'projects', label: 'Projects', icon: GitBranch, description: 'Project management' },
  { id: 'agents', label: 'Agents', icon: Users, description: 'Agent orchestration' },
  { id: 'contexts', label: 'Contexts', icon: Activity, description: 'Context management' },
  { id: 'monitoring', label: 'Monitoring', icon: Activity, description: 'System monitoring' },
  { id: 'compliance', label: 'Compliance', icon: CheckCircle, description: 'Security and compliance' }
];

// Available Agents List
const AVAILABLE_AGENTS: Agent[] = [
  { id: '@uber_orchestrator_agent', name: '@uber_orchestrator_agent', status: 'inactive', project_id: '' },
  { id: '@coding_agent', name: '@coding_agent', status: 'inactive', project_id: '' },
  { id: '@debugger_agent', name: '@debugger_agent', status: 'inactive', project_id: '' },
  { id: '@test_orchestrator_agent', name: '@test_orchestrator_agent', status: 'inactive', project_id: '' },
  { id: '@ui_designer_agent', name: '@ui_designer_agent', status: 'inactive', project_id: '' },
  { id: '@security_auditor_agent', name: '@security_auditor_agent', status: 'inactive', project_id: '' },
  { id: '@devops_agent', name: '@devops_agent', status: 'inactive', project_id: '' },
  { id: '@documentation_agent', name: '@documentation_agent', status: 'inactive', project_id: '' },
  { id: '@deep_research_agent', name: '@deep_research_agent', status: 'inactive', project_id: '' },
  { id: '@task_planning_agent', name: '@task_planning_agent', status: 'inactive', project_id: '' }
];

// Health Status Indicator
function HealthIndicator({ health }: { health: SystemHealthStatus | null }) {
  if (!health) {
    return (
      <div className="flex items-center space-x-2 text-gray-500">
        <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
        <span className="text-sm">Unknown</span>
      </div>
    );
  }

  const getHealthColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'degraded': return 'text-yellow-600 bg-yellow-100';
      case 'critical': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getHealthIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy': return CheckCircle;
      case 'degraded': return AlertTriangle;
      case 'critical': return AlertTriangle;
      default: return Activity;
    }
  };

  // Derive status from overall_score
  const getHealthStatus = (score: number): 'healthy' | 'degraded' | 'critical' => {
    if (score >= 80) return 'healthy';
    if (score >= 50) return 'degraded';
    return 'critical';
  };

  const healthStatus = getHealthStatus(health.overall_score);
  const HealthIcon = getHealthIcon(healthStatus);

  return (
    <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${getHealthColor(healthStatus)}`}>
      <HealthIcon size={14} />
      <span className="text-sm font-medium">{healthStatus}</span>
    </div>
  );
}

// Agent Switcher Component
function AgentSwitcher({ 
  currentAgent, 
  onAgentSwitch 
}: { 
  currentAgent: Agent | null; 
  onAgentSwitch: (agent: Agent) => Promise<void>; 
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleAgentSwitch = useCallback(async (agent: Agent) => {
    if (agent.id === currentAgent?.id) return;
    
    setIsLoading(true);
    try {
      await onAgentSwitch(agent);
      setIsOpen(false);
    } catch (error) {
      console.error('Failed to switch agent:', error);
    } finally {
      setIsLoading(false);
    }
  }, [currentAgent, onAgentSwitch]);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors"
        disabled={isLoading}
      >
        <Zap size={16} />
        <span className="font-medium">
          {currentAgent?.name || 'No Agent'}
        </span>
        <ChevronDown size={14} className={`transform transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          <div className="p-3 border-b border-gray-200">
            <h3 className="font-semibold text-gray-900">Switch Agent</h3>
            <p className="text-sm text-gray-600">Select an agent for the current context</p>
          </div>
          
          <div className="max-h-64 overflow-y-auto">
            {AVAILABLE_AGENTS.map((agent) => (
              <button
                key={agent.id}
                onClick={() => handleAgentSwitch(agent)}
                disabled={isLoading}
                className={`w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors ${
                  currentAgent?.id === agent.id ? 'bg-blue-50 border-r-2 border-blue-500' : ''
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className={`w-2 h-2 rounded-full ${
                    agent.status === 'active' ? 'bg-green-400' : 'bg-gray-400'
                  }`}></div>
                  <div className="text-left">
                    <p className="font-medium text-gray-900">{agent.name}</p>
                    <p className="text-sm text-gray-500 capitalize">{agent.status}</p>
                  </div>
                </div>
                {currentAgent?.id === agent.id && (
                  <CheckCircle size={16} className="text-blue-600" />
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Project Selector Component
function ProjectSelector({ 
  projects, 
  selectedProject, 
  onProjectSwitch 
}: { 
  projects: Project[]; 
  selectedProject: Project | null; 
  onProjectSwitch: (project: Project) => void; 
}) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 py-2 bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
      >
        <GitBranch size={16} />
        <span className="font-medium">
          {selectedProject?.name || 'Select Project'}
        </span>
        <ChevronDown size={14} className={`transform transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          <div className="p-3 border-b border-gray-200">
            <h3 className="font-semibold text-gray-900">Projects</h3>
          </div>
          
          <div className="max-h-48 overflow-y-auto">
            {projects.length === 0 ? (
              <p className="p-3 text-gray-500 text-sm">No projects available</p>
            ) : (
              projects.map((project) => (
                <button
                  key={project.id}
                  onClick={() => {
                    onProjectSwitch(project);
                    setIsOpen(false);
                  }}
                  className={`w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors ${
                    selectedProject?.id === project.id ? 'bg-blue-50 border-r-2 border-blue-500' : ''
                  }`}
                >
                  <div className="text-left">
                    <p className="font-medium text-gray-900">{project.name}</p>
                    {project.description && (
                      <p className="text-sm text-gray-500 truncate">{project.description}</p>
                    )}
                  </div>
                  {selectedProject?.id === project.id && (
                    <CheckCircle size={16} className="text-blue-600" />
                  )}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Notification Center Component
function NotificationCenter({ notifications }: { notifications: Notification[] }) {
  const [isOpen, setIsOpen] = useState(false);
  const unreadCount = useMemo(() => 
    notifications.filter(n => !n.read).length, 
    [notifications]
  );

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute top-full right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          <div className="p-3 border-b border-gray-200">
            <h3 className="font-semibold text-gray-900">Notifications</h3>
          </div>
          
          <div className="max-h-64 overflow-y-auto">
            {notifications.length === 0 ? (
              <p className="p-3 text-gray-500 text-sm">No notifications</p>
            ) : (
              notifications.slice(0, 10).map((notification) => (
                <div
                  key={notification.id}
                  className={`p-3 border-b border-gray-100 last:border-b-0 ${
                    !notification.read ? 'bg-blue-50' : ''
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <div className={`mt-1 w-2 h-2 rounded-full ${
                      notification.type === 'error' ? 'bg-red-400' :
                      notification.type === 'warning' ? 'bg-yellow-400' :
                      'bg-blue-400'
                    }`}></div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 text-sm">{notification.title}</p>
                      <p className="text-gray-600 text-sm">{notification.message}</p>
                      <p className="text-gray-400 text-xs mt-1">
                        {new Date(notification.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Main Navigation Component
export function IntegratedNavigation({
  currentUser,
  projects,
  currentAgent,
  systemHealth,
  notifications,
  onNavigate,
  onAgentSwitch,
  onProjectSwitch
}: IntegratedNavigationProps) {
  const dispatch = useAppDispatch();
  const { currentView, sidebarOpen, commandPaletteOpen } = useAppSelector(state => state.ui);
  const { selectedProject } = useAppSelector(state => state.session);
  const [searchQuery, setSearchQuery] = useState('');

  const handleViewChange = useCallback((view: ViewType) => {
    dispatch(uiActions.setCurrentView(view));
    onNavigate(`/${view}`);
  }, [dispatch, onNavigate]);

  const handleProjectSwitch = useCallback((project: Project) => {
    onProjectSwitch(project);
    dispatch(sessionActions.setSelectedProject(project));
  }, [onProjectSwitch, dispatch]);

  const openCommandPalette = useCallback(() => {
    dispatch(uiActions.setCommandPaletteOpen(true));
  }, [dispatch]);

  return (
    <nav 
      className="bg-white border-b border-gray-200 sticky top-0 z-40"
      id="primary-navigation"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="max-w-full px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Left Section */}
          <div className="flex items-center space-x-4">
            {/* Mobile menu button */}
            <AccessibleButton
              onClick={() => dispatch(uiActions.toggleSidebar())}
              className="md:hidden p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
              ariaLabel={sidebarOpen ? "Close navigation menu" : "Open navigation menu"}
              ariaExpanded={sidebarOpen}
              ariaHaspopup="menu"
            >
              {sidebarOpen ? <X size={20} aria-hidden="true" /> : <Menu size={20} aria-hidden="true" />}
            </AccessibleButton>

            {/* Logo */}
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">D</span>
              </div>
              <span className="hidden sm:block font-bold text-gray-900">DhafnckMCP</span>
            </div>

            {/* Navigation Links */}
            <div className="hidden md:flex items-center space-x-1" role="menubar">
              {NAVIGATION_VIEWS.map((view) => {
                const Icon = view.icon;
                const isActive = currentView === view.id;
                return (
                  <AccessibleButton
                    key={view.id}
                    onClick={() => handleViewChange(view.id)}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                    ariaLabel={`Navigate to ${view.label}: ${view.description}`}
                    ariaPressed={isActive}
                    role="menuitem"
                  >
                    <Icon size={16} aria-hidden="true" />
                    <span>{view.label}</span>
                  </AccessibleButton>
                );
              })}
            </div>
          </div>

          {/* Center Section */}
          <div className="flex-1 flex items-center justify-center max-w-md mx-4">
            <AccessibleButton
              onClick={openCommandPalette}
              className="w-full flex items-center space-x-3 px-4 py-2 bg-gray-50 text-gray-500 rounded-lg hover:bg-gray-100 transition-colors"
              ariaLabel="Open command palette to search or run commands. Keyboard shortcut: Command K"
              ariaHaspopup="dialog"
            >
              <Search size={16} aria-hidden="true" />
              <span className="text-sm" id="search">Search or run command...</span>
              <div className="flex items-center space-x-1 ml-auto" aria-hidden="true">
                <kbd className="px-2 py-1 text-xs bg-white border border-gray-200 rounded">⌘</kbd>
                <kbd className="px-2 py-1 text-xs bg-white border border-gray-200 rounded">K</kbd>
              </div>
            </AccessibleButton>
          </div>

          {/* Right Section */}
          <div className="flex items-center space-x-4">
            {/* System Health */}
            <HealthIndicator health={systemHealth} />

            {/* Project Selector */}
            <ProjectSelector
              projects={projects}
              selectedProject={selectedProject}
              onProjectSwitch={handleProjectSwitch}
            />

            {/* Agent Switcher */}
            <AgentSwitcher
              currentAgent={currentAgent}
              onAgentSwitch={onAgentSwitch}
            />

            {/* Notifications */}
            <NotificationCenter notifications={notifications} />

            {/* Settings */}
            <AccessibleButton 
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              ariaLabel="Open settings menu"
              ariaHaspopup="menu"
            >
              <Settings size={20} aria-hidden="true" />
            </AccessibleButton>

            {/* User Menu */}
            <AccessibleButton 
              className="flex items-center space-x-2 p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              ariaLabel={`User menu for ${currentUser.name || 'User'}`}
              ariaHaspopup="menu"
            >
              <User size={20} aria-hidden="true" />
              <span className="hidden sm:block font-medium">{currentUser.name || 'User'}</span>
            </AccessibleButton>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Menu */}
      {sidebarOpen && (
        <div className="md:hidden border-t border-gray-200 bg-white">
          <div className="px-4 py-3 space-y-1">
            {NAVIGATION_VIEWS.map((view) => {
              const Icon = view.icon;
              return (
                <button
                  key={view.id}
                  onClick={() => {
                    handleViewChange(view.id);
                    dispatch(uiActions.setSidebarOpen(false));
                  }}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left ${
                    currentView === view.id
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <Icon size={20} />
                  <div>
                    <p className="font-medium">{view.label}</p>
                    <p className="text-sm opacity-70">{view.description}</p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </nav>
  );
}

export default IntegratedNavigation;