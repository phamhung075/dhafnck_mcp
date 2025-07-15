import React, { useState, useEffect, useRef } from 'react';
import { useAppDispatch, useAppSelector } from '../../store/store';
import { uiActions, sessionActions, dataActions, systemActions } from '../../store/store';
import { store } from '../../store/store';
import { mcpApi as api } from '../../api/enhanced';
import type { ViewType } from '../../types/application';

interface Command {
  id: string;
  label: string;
  description: string;
  keywords: string[];
  icon: string;
  action: () => void | Promise<void>;
  category: 'navigation' | 'agent' | 'project' | 'task' | 'system';
  shortcut?: string;
}

export function CommandPalette() {
  const dispatch = useAppDispatch();
  const { commandPaletteOpen } = useAppSelector(state => state.ui);
  const { projects } = useAppSelector(state => state.data);
  const { selectedProject, currentAgent } = useAppSelector(state => state.session);
  
  const [search, setSearch] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isExecuting, setIsExecuting] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Available agents for switching
  const availableAgents = [
    { id: '@uber_orchestrator_agent', name: 'Uber Orchestrator', icon: '🎯', description: 'Complex multi-step workflows' },
    { id: '@coding_agent', name: 'Coding Agent', icon: '👨‍💻', description: 'Code implementation and development' },
    { id: '@debugger_agent', name: 'Debugger Agent', icon: '🐛', description: 'Bug fixing and troubleshooting' },
    { id: '@test_orchestrator_agent', name: 'Test Orchestrator', icon: '🧪', description: 'Testing and validation' },
    { id: '@task_planning_agent', name: 'Task Planning Agent', icon: '📋', description: 'Task breakdown and planning' },
    { id: '@ui_designer_agent', name: 'UI Designer Agent', icon: '🎨', description: 'UI/UX design and frontend' },
    { id: '@security_auditor_agent', name: 'Security Auditor', icon: '🔒', description: 'Security auditing and analysis' },
    { id: '@devops_agent', name: 'DevOps Agent', icon: '⚙️', description: 'Deployment and infrastructure' },
    { id: '@documentation_agent', name: 'Documentation Agent', icon: '📝', description: 'Documentation and guides' },
    { id: '@deep_research_agent', name: 'Research Agent', icon: '🔬', description: 'Research and investigation' }
  ];

  const commands: Command[] = [
    // Navigation Commands
    {
      id: 'nav_dashboard',
      label: 'Go to Dashboard',
      description: 'Navigate to main dashboard',
      keywords: ['dashboard', 'home', 'main', 'overview'],
      icon: '📊',
      category: 'navigation',
      shortcut: 'Ctrl+1',
      action: () => { dispatch(uiActions.setCurrentView('dashboard')); }
    },
    {
      id: 'nav_projects',
      label: 'Go to Projects',
      description: 'Navigate to project management',
      keywords: ['projects', 'project', 'manage'],
      icon: '📁',
      category: 'navigation',
      shortcut: 'Ctrl+2',
      action: () => { dispatch(uiActions.setCurrentView('projects')); }
    },
    {
      id: 'nav_agents',
      label: 'Go to Agent Management',
      description: 'Navigate to agent management',
      keywords: ['agents', 'agent', 'manage', 'orchestration'],
      icon: '🤖',
      category: 'navigation',
      shortcut: 'Ctrl+3',
      action: () => { dispatch(uiActions.setCurrentView('agents')); }
    },
    {
      id: 'nav_contexts',
      label: 'Go to Context Tree',
      description: 'Navigate to hierarchical context management',
      keywords: ['context', 'tree', 'hierarchy', 'inheritance'],
      icon: '🌳',
      category: 'navigation',
      action: () => { dispatch(uiActions.setCurrentView('contexts')); }
    },
    {
      id: 'nav_health',
      label: 'Go to System Health',
      description: 'Navigate to system health dashboard',
      keywords: ['health', 'system', 'monitoring', 'status'],
      icon: '🏥',
      category: 'navigation',
      action: () => { dispatch(uiActions.setCurrentView('health')); }
    },
    {
      id: 'nav_compliance',
      label: 'Go to Compliance',
      description: 'Navigate to compliance dashboard',
      keywords: ['compliance', 'security', 'audit', 'policy'],
      icon: '🛡️',
      category: 'navigation',
      action: () => { dispatch(uiActions.setCurrentView('compliance')); }
    },

    // Agent Commands
    ...availableAgents.map(agent => ({
      id: `agent_switch_${agent.id}`,
      label: `Switch to ${agent.name}`,
      description: agent.description,
      keywords: ['agent', 'switch', agent.name.toLowerCase(), agent.id.replace('@', '').replace('_', ' ')],
      icon: agent.icon,
      category: 'agent' as const,
      action: async () => {
        setIsExecuting(true);
        try {
          await api.callAgent(agent.id);
          dispatch(sessionActions.setCurrentAgent({
            id: agent.id,
            name: agent.name,
            status: 'active',
            project_id: selectedProject?.id || ''
          }));
          
          dispatch(uiActions.addUINotification({
            id: `agent_switch_${Date.now()}`,
            type: 'success',
            title: 'Agent Switched',
            message: `Successfully switched to ${agent.name}`,
            timestamp: new Date().toISOString(),
            read: false,
            autoClose: true,
            duration: 3000
          }));
        } catch (error) {
          dispatch(uiActions.addUINotification({
            id: `agent_error_${Date.now()}`,
            type: 'error',
            title: 'Agent Switch Failed',
            message: `Failed to switch to ${agent.name}: ${error}`,
            timestamp: new Date().toISOString(),
            read: false,
            autoClose: false
          }));
        } finally {
          setIsExecuting(false);
        }
      }
    })),

    // Project Commands
    ...projects.map(project => ({
      id: `project_select_${project.id}`,
      label: `Select Project: ${project.name}`,
      description: project.description || 'Switch to this project',
      keywords: ['project', 'select', 'switch', project.name.toLowerCase()],
      icon: '📁',
      category: 'project' as const,
      action: () => {
        dispatch(sessionActions.setSelectedProject(project));
        dispatch(uiActions.addUINotification({
          id: `project_select_${Date.now()}`,
          type: 'success',
          title: 'Project Selected',
          message: `Selected project: ${project.name}`,
          timestamp: new Date().toISOString(),
          read: false,
          autoClose: true,
          duration: 2000
        }));
      }
    })),

    // System Commands
    {
      id: 'system_health_check',
      label: 'Run System Health Check',
      description: 'Check overall system health and status',
      keywords: ['health', 'check', 'system', 'status', 'diagnostic'],
      icon: '🏥',
      category: 'system',
      action: async () => {
        setIsExecuting(true);
        try {
          const healthResponse = await api.manageConnection('health_check', { include_details: true });
          if (healthResponse.data) {
            dispatch(systemActions.setSystemHealth(healthResponse.data));
          }
          
          dispatch(uiActions.addUINotification({
            id: `health_check_${Date.now()}`,
            type: 'success',
            title: 'Health Check Complete',
            message: `System health: ${healthResponse.data?.overall_score || 'Unknown'}%`,
            timestamp: new Date().toISOString(),
            read: false,
            autoClose: true,
            duration: 3000
          }));
        } catch (error) {
          dispatch(uiActions.addUINotification({
            id: `health_error_${Date.now()}`,
            type: 'error',
            title: 'Health Check Failed',
            message: `Failed to check system health: ${error}`,
            timestamp: new Date().toISOString(),
            read: false,
            autoClose: false
          }));
        } finally {
          setIsExecuting(false);
        }
      }
    },
    {
      id: 'toggle_theme',
      label: 'Toggle Theme',
      description: 'Switch between light, dark, and auto mode',
      keywords: ['theme', 'dark', 'light', 'mode', 'appearance'],
      icon: '🌓',
      category: 'system',
      shortcut: 'Ctrl+Shift+T',
      action: () => {
        const currentTheme = store.getState().ui.theme;
        const newTheme = currentTheme === 'light' ? 'dark' : currentTheme === 'dark' ? 'auto' : 'light';
        dispatch(uiActions.setTheme(newTheme));
      }
    },
    {
      id: 'toggle_sidebar',
      label: 'Toggle Sidebar',
      description: 'Show or hide the navigation sidebar',
      keywords: ['sidebar', 'navigation', 'menu', 'toggle'],
      icon: '☰',
      category: 'system',
      shortcut: 'Ctrl+B',
      action: () => { dispatch(uiActions.toggleSidebar()); }
    },
    {
      id: 'clear_notifications',
      label: 'Clear All Notifications',
      description: 'Clear all system and UI notifications',
      keywords: ['clear', 'notifications', 'alerts', 'clean'],
      icon: '🗑️',
      category: 'system',
      action: () => {
        dispatch(systemActions.clearNotifications());
        dispatch(uiActions.clearUINotifications());
        dispatch(uiActions.addUINotification({
          id: `clear_notifications_${Date.now()}`,
          type: 'success',
          title: 'Notifications Cleared',
          message: 'All notifications have been cleared',
          timestamp: new Date().toISOString(),
          read: false,
          autoClose: true,
          duration: 2000
        }));
      }
    },
    {
      id: 'refresh_data',
      label: 'Refresh All Data',
      description: 'Reload projects, agents, and system status',
      keywords: ['refresh', 'reload', 'update', 'sync', 'data'],
      icon: '🔄',
      category: 'system',
      shortcut: 'F5',
      action: async () => {
        setIsExecuting(true);
        try {
          // Refresh projects
          const projectsResponse = await api.manageProject('list');
          if (projectsResponse.data) {
            dispatch(dataActions.setProjects(projectsResponse.data));
          }
          
          // Refresh system health
          const healthResponse = await api.manageConnection('health_check', { include_details: true });
          if (healthResponse.data) {
            dispatch(systemActions.setSystemHealth(healthResponse.data));
          }
          
          dispatch(uiActions.addUINotification({
            id: `refresh_${Date.now()}`,
            type: 'success',
            title: 'Data Refreshed',
            message: 'All data has been refreshed successfully',
            timestamp: new Date().toISOString(),
            read: false,
            autoClose: true,
            duration: 3000
          }));
        } catch (error) {
          dispatch(uiActions.addUINotification({
            id: `refresh_error_${Date.now()}`,
            type: 'error',
            title: 'Refresh Failed',
            message: `Failed to refresh data: ${error}`,
            timestamp: new Date().toISOString(),
            read: false,
            autoClose: false
          }));
        } finally {
          setIsExecuting(false);
        }
      }
    }
  ];

  const filteredCommands = commands.filter(command => {
    if (!search) return true;
    const searchLower = search.toLowerCase();
    return (
      command.label.toLowerCase().includes(searchLower) ||
      command.description.toLowerCase().includes(searchLower) ||
      command.keywords.some(keyword => keyword.includes(searchLower))
    );
  });

  // Keyboard navigation
  useEffect(() => {
    if (!commandPaletteOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(prev => Math.min(prev + 1, filteredCommands.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => Math.max(prev - 1, 0));
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredCommands[selectedIndex] && !isExecuting) {
            executeCommand(filteredCommands[selectedIndex]);
          }
          break;
        case 'Escape':
          closeCommandPalette();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [commandPaletteOpen, selectedIndex, filteredCommands, isExecuting]);

  // Focus input when opened
  useEffect(() => {
    if (commandPaletteOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [commandPaletteOpen]);

  // Reset state when opened
  useEffect(() => {
    if (commandPaletteOpen) {
      setSearch('');
      setSelectedIndex(0);
      setIsExecuting(false);
    }
  }, [commandPaletteOpen]);

  const executeCommand = async (command: Command) => {
    try {
      await command.action();
      closeCommandPalette();
    } catch (error) {
      console.error('Failed to execute command:', error);
    }
  };

  const closeCommandPalette = () => {
    dispatch(uiActions.setCommandPaletteOpen(false));
  };

  if (!commandPaletteOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-start justify-center pt-20 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl border border-gray-200 dark:border-gray-700">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="relative">
            <input
              ref={inputRef}
              type="text"
              placeholder="Type a command or search..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setSelectedIndex(0);
              }}
              className="w-full px-4 py-3 text-lg border-none outline-none bg-transparent text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
              disabled={isExecuting}
            />
            {isExecuting && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
              </div>
            )}
          </div>
        </div>

        {/* Commands List */}
        <div className="max-h-96 overflow-y-auto">
          {filteredCommands.length > 0 ? (
            filteredCommands.map((command, index) => (
              <CommandItem
                key={command.id}
                command={command}
                isSelected={index === selectedIndex}
                isExecuting={isExecuting}
                onClick={() => !isExecuting && executeCommand(command)}
              />
            ))
          ) : (
            <div className="p-8 text-center text-gray-500 dark:text-gray-400">
              <div className="text-4xl mb-2">🔍</div>
              <p>No commands found for "{search}"</p>
              <p className="text-sm mt-1">Try different keywords or clear the search</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700 rounded-b-lg">
          <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            <div className="flex items-center gap-4">
              <span>↑↓ Navigate</span>
              <span>↵ Execute</span>
              <span>⎋ Close</span>
            </div>
            <div>
              {filteredCommands.length} command{filteredCommands.length !== 1 ? 's' : ''}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface CommandItemProps {
  command: Command;
  isSelected: boolean;
  isExecuting: boolean;
  onClick: () => void;
}

function CommandItem({ command, isSelected, isExecuting, onClick }: CommandItemProps) {
  const getCategoryColor = (category: Command['category']) => {
    switch (category) {
      case 'navigation': return 'text-blue-600 dark:text-blue-400';
      case 'agent': return 'text-purple-600 dark:text-purple-400';
      case 'project': return 'text-green-600 dark:text-green-400';
      case 'system': return 'text-orange-600 dark:text-orange-400';
      case 'task': return 'text-indigo-600 dark:text-indigo-400';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  };

  return (
    <button
      onClick={onClick}
      disabled={isExecuting}
      className={`w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-3 transition-colors ${
        isSelected ? 'bg-blue-50 dark:bg-blue-900 border-r-2 border-blue-500' : ''
      } ${isExecuting ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <span className="text-xl flex-shrink-0">{command.icon}</span>
      <div className="flex-1 min-w-0">
        <div className="font-medium text-gray-900 dark:text-white truncate">
          {command.label}
        </div>
        <div className="text-sm text-gray-500 dark:text-gray-400 truncate">
          {command.description}
        </div>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        {command.shortcut && (
          <span className="text-xs px-2 py-1 bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300 rounded">
            {command.shortcut}
          </span>
        )}
        <span className={`text-xs uppercase font-medium ${getCategoryColor(command.category)}`}>
          {command.category}
        </span>
      </div>
    </button>
  );
}

