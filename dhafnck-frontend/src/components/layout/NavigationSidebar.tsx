import React, { useState } from 'react';
import { useAppSelector } from '../../store/store';
import type { ViewType } from '../../types/application';

interface NavigationItem {
  id: string;
  label: string;
  icon: string;
  view: ViewType;
  badge?: number;
  disabled?: boolean;
  children?: NavigationItem[];
}

interface NavigationSidebarProps {
  isOpen: boolean;
  currentView: ViewType;
  onNavigate: (view: ViewType) => void;
  onToggle: () => void;
}

export function NavigationSidebar({ 
  isOpen, 
  currentView, 
  onNavigate, 
  onToggle 
}: NavigationSidebarProps) {
  const { notifications } = useAppSelector(state => state.system);
  const { projects } = useAppSelector(state => state.data);
  
  // Count unread notifications
  const unreadCount = notifications.filter(n => !n.read).length;
  
  // Count projects by status
  const activeProjects = projects.filter(p => p.status === 'active').length;

  const navigationItems: NavigationItem[] = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: '📊',
      view: 'dashboard'
    },
    {
      id: 'projects',
      label: 'Projects',
      icon: '📁',
      view: 'projects',
      badge: activeProjects
    },
    {
      id: 'agents',
      label: 'Agent Management',
      icon: '🤖',
      view: 'agents'
    },
    {
      id: 'contexts',
      label: 'Context Tree',
      icon: '🌳',
      view: 'contexts'
    },
    {
      id: 'monitoring',
      label: 'System Monitoring',
      icon: '📈',
      view: 'monitoring',
      badge: unreadCount > 0 ? unreadCount : undefined,
      children: [
        { 
          id: 'health', 
          label: 'Health Dashboard', 
          icon: '🏥', 
          view: 'health' 
        },
        { 
          id: 'compliance', 
          label: 'Compliance', 
          icon: '🛡️', 
          view: 'compliance' 
        },
        { 
          id: 'connections', 
          label: 'Connections', 
          icon: '🔗', 
          view: 'connections' 
        }
      ]
    },
    {
      id: 'tasks',
      label: 'Task Management',
      icon: '✅',
      view: 'tasks'
    },
    {
      id: 'rules',
      label: 'Rules & Policies',
      icon: '📋',
      view: 'rules'
    }
  ];

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={onToggle}
        />
      )}
      
      {/* Sidebar */}
      <aside className={`
        fixed top-16 left-0 h-[calc(100vh-4rem)] w-64 bg-white dark:bg-gray-800 
        border-r border-gray-200 dark:border-gray-700 z-50 transition-transform duration-300
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Navigation
            </h2>
            <button
              onClick={onToggle}
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <span className="text-gray-500">✕</span>
            </button>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="p-4 overflow-y-auto h-full">
          <ul className="space-y-2">
            {navigationItems.map(item => (
              <NavigationItem
                key={item.id}
                item={item}
                currentView={currentView}
                onNavigate={onNavigate}
              />
            ))}
          </ul>
        </nav>

        {/* Sidebar Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <div className="text-xs text-gray-500 dark:text-gray-400">
            <div>DhafnckMCP Dashboard v1.0</div>
            <div className="mt-1">
              {activeProjects} active project{activeProjects !== 1 ? 's' : ''}
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}

function NavigationItem({
  item,
  currentView,
  onNavigate,
  level = 0
}: {
  item: NavigationItem;
  currentView: ViewType;
  onNavigate: (view: ViewType) => void;
  level?: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const isActive = currentView === item.view;
  const hasChildren = item.children && item.children.length > 0;
  const isChildActive = hasChildren && item.children?.some(child => child.view === currentView);

  // Auto-expand if child is active
  React.useEffect(() => {
    if (isChildActive) {
      setExpanded(true);
    }
  }, [isChildActive]);

  return (
    <li>
      <button
        onClick={() => {
          if (hasChildren) {
            setExpanded(!expanded);
          } else {
            onNavigate(item.view);
          }
        }}
        className={`
          w-full flex items-center justify-between px-3 py-2 text-left rounded-lg 
          transition-colors duration-200 group
          ${level > 0 ? 'ml-4' : ''}
          ${isActive 
            ? 'bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100' 
            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
          }
          ${item.disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        disabled={item.disabled}
      >
        <div className="flex items-center gap-3">
          <span className="text-lg">{item.icon}</span>
          <span className="font-medium">{item.label}</span>
          {item.badge && item.badge > 0 && (
            <span className="px-2 py-1 text-xs bg-red-500 text-white rounded-full min-w-[1.25rem] text-center">
              {item.badge > 99 ? '99+' : item.badge}
            </span>
          )}
        </div>
        
        {hasChildren && (
          <span className={`
            transform transition-transform duration-200 text-gray-400
            ${expanded ? 'rotate-90' : ''}
          `}>
            ➤
          </span>
        )}
      </button>

      {/* Submenu */}
      {hasChildren && expanded && (
        <ul className="mt-1 space-y-1">
          {item.children!.map(child => (
            <NavigationItem
              key={child.id}
              item={child}
              currentView={currentView}
              onNavigate={onNavigate}
              level={level + 1}
            />
          ))}
        </ul>
      )}
    </li>
  );
}