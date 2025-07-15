import React from 'react';
import { useAppDispatch, useAppSelector } from '../../store/store';
import { uiActions } from '../../store/store';

export function HeaderBar() {
  const dispatch = useAppDispatch();
  const { sidebarOpen, theme } = useAppSelector(state => state.ui);
  const { currentUser } = useAppSelector(state => state.session);
  const { connection, notifications } = useAppSelector(state => state.system);

  const unreadNotifications = notifications.filter(n => !n.read).length;

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : theme === 'dark' ? 'auto' : 'light';
    dispatch(uiActions.setTheme(newTheme));
  };

  const getThemeIcon = () => {
    switch (theme) {
      case 'light': return '☀️';
      case 'dark': return '🌙';
      case 'auto': return '🌓';
      default: return '🌓';
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-40 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
      <div className="flex justify-between items-center">
        {/* Left Section */}
        <div className="flex items-center gap-4">
          {/* Menu Toggle */}
          <button
            onClick={() => dispatch(uiActions.toggleSidebar())}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            <span className="text-xl">{sidebarOpen ? '☰' : '☰'}</span>
          </button>

          {/* Logo and Title */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">D</span>
            </div>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
              DhafnckMCP Dashboard
            </h1>
          </div>
          
          {/* Connection Status Indicator */}
          <div className={`flex items-center gap-2 px-2 py-1 rounded text-xs font-medium ${
            connection.status === 'healthy' 
              ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200' :
            connection.status === 'degraded' 
              ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200' :
              'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
          }`}>
            <div className={`w-1.5 h-1.5 rounded-full ${
              connection.status === 'healthy' ? 'bg-green-500' :
              connection.status === 'degraded' ? 'bg-yellow-500' :
              'bg-red-500'
            }`} />
            <span className="capitalize">{connection.status}</span>
          </div>
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-3">
          {/* Quick Actions */}
          <div className="flex items-center gap-2">
            {/* Command Palette Trigger */}
            <button
              onClick={() => dispatch(uiActions.toggleCommandPalette())}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              title="Command Palette (Ctrl+K)"
            >
              <span>⌘</span>
              <span className="hidden sm:inline">Quick Actions</span>
            </button>

            {/* Notifications */}
            <button
              className="relative p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title={`${unreadNotifications} unread notifications`}
            >
              <span className="text-xl">🔔</span>
              {unreadNotifications > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full min-w-[1.25rem] h-5 flex items-center justify-center">
                  {unreadNotifications > 99 ? '99+' : unreadNotifications}
                </span>
              )}
            </button>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title={`Current theme: ${theme}. Click to cycle themes.`}
            >
              <span className="text-xl">{getThemeIcon()}</span>
            </button>
          </div>

          {/* User Profile */}
          <div className="flex items-center gap-3 pl-3 border-l border-gray-200 dark:border-gray-700">
            {currentUser ? (
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gray-300 dark:bg-gray-600 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {currentUser.name.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div className="hidden md:block">
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {currentUser.name}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                    {currentUser.role}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gray-300 dark:bg-gray-600 rounded-full flex items-center justify-center">
                  <span className="text-sm text-gray-600 dark:text-gray-400">?</span>
                </div>
                <div className="hidden md:block">
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    Not signed in
                  </div>
                </div>
              </div>
            )}

            {/* Settings Menu */}
            <button
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title="Settings"
            >
              <span className="text-xl">⚙️</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}