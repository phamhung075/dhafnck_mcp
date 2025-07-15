import React, { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../store/store';
import { uiActions } from '../../store/store';
import type { UINotification } from '../../types/application';

export function NotificationSystem() {
  const dispatch = useAppDispatch();
  const { notifications } = useAppSelector(state => state.ui);

  return (
    <div className="fixed top-20 right-4 z-50 space-y-2 max-w-sm w-full">
      {notifications.map(notification => (
        <NotificationItem
          key={notification.id}
          notification={notification}
          onClose={() => dispatch(uiActions.removeUINotification(notification.id))}
        />
      ))}
    </div>
  );
}

interface NotificationItemProps {
  notification: UINotification;
  onClose: () => void;
}

function NotificationItem({ notification, onClose }: NotificationItemProps) {
  const dispatch = useAppDispatch();

  // Auto-close notification after duration
  useEffect(() => {
    if (notification.autoClose && notification.duration) {
      const timer = setTimeout(() => {
        onClose();
      }, notification.duration);

      return () => clearTimeout(timer);
    }
  }, [notification.autoClose, notification.duration, onClose]);

  const getNotificationStyles = () => {
    const baseStyles = "relative p-4 rounded-lg shadow-lg border-l-4 bg-white dark:bg-gray-800";
    
    switch (notification.type) {
      case 'success':
        return `${baseStyles} border-green-500 text-green-800 dark:text-green-200`;
      case 'warning':
        return `${baseStyles} border-yellow-500 text-yellow-800 dark:text-yellow-200`;
      case 'error':
        return `${baseStyles} border-red-500 text-red-800 dark:text-red-200`;
      case 'info':
      default:
        return `${baseStyles} border-blue-500 text-blue-800 dark:text-blue-200`;
    }
  };

  const getIcon = () => {
    switch (notification.type) {
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      case 'info':
      default: return 'ℹ️';
    }
  };

  return (
    <div className={`${getNotificationStyles()} transform transition-all duration-300 ease-in-out animate-slide-in-right`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1">
          <span className="text-lg flex-shrink-0 mt-0.5">{getIcon()}</span>
          <div className="flex-1">
            <h4 className="font-medium text-gray-900 dark:text-white">
              {notification.title}
            </h4>
            <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
              {notification.message}
            </p>
            
            {/* Action buttons */}
            {notification.actions && notification.actions.length > 0 && (
              <div className="flex gap-2 mt-3">
                {notification.actions.map((action, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      action.action();
                      onClose();
                    }}
                    className="text-xs px-3 py-1 rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
        
        {/* Close button */}
        <button
          onClick={onClose}
          className="flex-shrink-0 ml-2 p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <span className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">✕</span>
        </button>
      </div>

      {/* Progress bar for auto-closing notifications */}
      {notification.autoClose && notification.duration && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200 dark:bg-gray-600 rounded-b-lg overflow-hidden">
          <div 
            className="h-full bg-current opacity-50 animate-progress-bar"
            style={{ animationDuration: `${notification.duration}ms` }}
          />
        </div>
      )}
    </div>
  );
}