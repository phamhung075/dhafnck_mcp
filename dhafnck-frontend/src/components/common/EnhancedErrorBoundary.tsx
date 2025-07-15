/**
 * Enhanced Error Boundary with Error Recovery and Reporting
 * Provides comprehensive error handling, logging, and recovery options
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Bug, FileText, Home, Mail } from 'lucide-react';

// Error types and interfaces
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string;
  retryCount: number;
  isRecovering: boolean;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: React.ComponentType<ErrorFallbackProps>;
  onError?: (error: Error, errorInfo: ErrorInfo, errorId: string) => void;
  enableRetry?: boolean;
  maxRetries?: number;
  enableReporting?: boolean;
  isolate?: boolean;
}

interface ErrorFallbackProps {
  error: Error | null;
  errorId: string;
  retryCount: number;
  onRetry: () => void;
  onReportIssue: () => void;
  onGoHome: () => void;
  canRetry: boolean;
}

interface ErrorReport {
  errorId: string;
  message: string;
  stack?: string;
  componentStack?: string;
  timestamp: string;
  userAgent: string;
  url: string;
  userId?: string;
  sessionId?: string;
  buildVersion?: string;
  additionalContext?: Record<string, any>;
}

// Utility functions
const generateErrorId = (): string => {
  return `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

const getErrorCategory = (error: Error): string => {
  if (error.name === 'ChunkLoadError') return 'chunk_load';
  if (error.message.includes('Network Error')) return 'network';
  if (error.message.includes('Loading chunk')) return 'chunk_load';
  if (error.message.includes('script error')) return 'script';
  if (error.name === 'TypeError') return 'type_error';
  if (error.name === 'ReferenceError') return 'reference_error';
  return 'unknown';
};

const isRetryableError = (error: Error): boolean => {
  const retryableCategories = ['chunk_load', 'network', 'script'];
  return retryableCategories.includes(getErrorCategory(error));
};

// Error reporting service
class ErrorReportingService {
  private static instance: ErrorReportingService;
  private endpoint = '/api/errors';
  private queue: ErrorReport[] = [];
  private isOnline = navigator.onLine;

  static getInstance(): ErrorReportingService {
    if (!ErrorReportingService.instance) {
      ErrorReportingService.instance = new ErrorReportingService();
    }
    return ErrorReportingService.instance;
  }

  constructor() {
    // Monitor online status
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.flushQueue();
    });
    
    window.addEventListener('offline', () => {
      this.isOnline = false;
    });
  }

  async reportError(error: Error, errorInfo: ErrorInfo, errorId: string, additionalContext?: Record<string, any>): Promise<void> {
    const report: ErrorReport = {
      errorId,
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack || undefined,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      buildVersion: process.env.REACT_APP_VERSION || 'unknown',
      additionalContext
    };

    // Try to get user context if available
    try {
      const userContext = this.getUserContext();
      if (userContext) {
        report.userId = userContext.userId;
        report.sessionId = userContext.sessionId;
      }
    } catch (e) {
      // Ignore errors in getting user context
    }

    if (this.isOnline) {
      try {
        await this.sendReport(report);
      } catch (sendError) {
        console.error('Failed to send error report:', sendError);
        this.queueReport(report);
      }
    } else {
      this.queueReport(report);
    }
  }

  private async sendReport(report: ErrorReport): Promise<void> {
    const response = await fetch(this.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(report),
    });

    if (!response.ok) {
      throw new Error(`Error reporting failed: ${response.status}`);
    }
  }

  private queueReport(report: ErrorReport): void {
    this.queue.push(report);
    
    // Store in localStorage as backup
    try {
      const stored = localStorage.getItem('error_reports') || '[]';
      const reports = JSON.parse(stored);
      reports.push(report);
      
      // Keep only last 10 reports
      const trimmed = reports.slice(-10);
      localStorage.setItem('error_reports', JSON.stringify(trimmed));
    } catch (e) {
      // Ignore localStorage errors
    }
  }

  private async flushQueue(): Promise<void> {
    if (this.queue.length === 0) return;

    const reportsToSend = [...this.queue];
    this.queue = [];

    for (const report of reportsToSend) {
      try {
        await this.sendReport(report);
      } catch (e) {
        console.error('Failed to send queued error report:', e);
        this.queueReport(report); // Re-queue on failure
      }
    }
  }

  private getUserContext(): { userId?: string; sessionId?: string } | null {
    // Try to get user context from Redux store or other sources
    try {
      const state = (window as any).__REDUX_STORE__?.getState();
      if (state?.session) {
        return {
          userId: state.session.currentUser?.id,
          sessionId: state.session.sessionId
        };
      }
    } catch (e) {
      // Ignore errors
    }
    
    return null;
  }
}

// Default error fallback component
function DefaultErrorFallback({
  error,
  errorId,
  retryCount,
  onRetry,
  onReportIssue,
  onGoHome,
  canRetry
}: ErrorFallbackProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const [isReporting, setIsReporting] = React.useState(false);

  const handleReport = async () => {
    setIsReporting(true);
    try {
      await onReportIssue();
    } finally {
      setIsReporting(false);
    }
  };

  return (
    <div className="min-h-[400px] flex items-center justify-center p-6 bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center">
        <div className="mb-4">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-3" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Something went wrong
          </h2>
          <p className="text-gray-600 mb-4">
            We're sorry, but something unexpected happened. Our team has been notified.
          </p>
        </div>

        <div className="space-y-3">
          {/* Primary actions */}
          <div className="flex flex-col sm:flex-row gap-2">
            {canRetry && (
              <button
                onClick={onRetry}
                className="flex-1 flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again {retryCount > 0 && `(${retryCount + 1})`}
              </button>
            )}
            
            <button
              onClick={onGoHome}
              className="flex-1 flex items-center justify-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              <Home className="h-4 w-4 mr-2" />
              Go Home
            </button>
          </div>

          {/* Secondary actions */}
          <div className="flex flex-col sm:flex-row gap-2">
            <button
              onClick={handleReport}
              disabled={isReporting}
              className="flex-1 flex items-center justify-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              {isReporting ? (
                <>
                  <div className="animate-spin h-4 w-4 mr-2 border-2 border-gray-300 border-t-gray-600 rounded-full"></div>
                  Reporting...
                </>
              ) : (
                <>
                  <Bug className="h-4 w-4 mr-2" />
                  Report Issue
                </>
              )}
            </button>
            
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex-1 flex items-center justify-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <FileText className="h-4 w-4 mr-2" />
              {isExpanded ? 'Hide' : 'Show'} Details
            </button>
          </div>
        </div>

        {/* Error details */}
        {isExpanded && (
          <div className="mt-4 p-3 bg-gray-100 rounded text-left text-sm">
            <div className="font-semibold text-gray-700 mb-2">Error Details:</div>
            <div className="space-y-2 text-gray-600">
              <div>
                <span className="font-medium">ID:</span> {errorId}
              </div>
              <div>
                <span className="font-medium">Message:</span> {error?.message || 'Unknown error'}
              </div>
              {error?.stack && (
                <div>
                  <span className="font-medium">Stack:</span>
                  <pre className="mt-1 text-xs overflow-auto max-h-32 bg-white p-2 rounded border">
                    {error.stack}
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Main Error Boundary Component
export class EnhancedErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private errorReporter = ErrorReportingService.getInstance();

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: '',
      retryCount: 0,
      isRecovering: false
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
      errorId: generateErrorId()
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo });
    
    // Log error locally
    this.logError(error, errorInfo);
    
    // Report error if enabled
    if (this.props.enableReporting !== false) {
      this.reportError(error, errorInfo);
    }
    
    // Call custom error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo, this.state.errorId);
    }
  }

  private logError(error: Error, errorInfo: ErrorInfo): void {
    const category = getErrorCategory(error);
    
    console.group(`🚨 Error Boundary: ${category}`);
    console.error('Error:', error);
    console.error('Error Info:', errorInfo);
    console.error('Error ID:', this.state.errorId);
    console.error('Component Stack:', errorInfo.componentStack);
    console.groupEnd();
  }

  private async reportError(error: Error, errorInfo: ErrorInfo): Promise<void> {
    try {
      await this.errorReporter.reportError(error, errorInfo, this.state.errorId, {
        retryCount: this.state.retryCount,
        isRetryable: isRetryableError(error),
        errorCategory: getErrorCategory(error)
      });
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
    }
  }

  private handleRetry = (): void => {
    const { maxRetries = 3 } = this.props;
    
    if (this.state.retryCount >= maxRetries) {
      console.warn('Maximum retry attempts reached');
      return;
    }

    this.setState({
      isRecovering: true
    });

    // Clear error state after a brief delay to allow visual feedback
    setTimeout(() => {
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null,
        errorId: '',
        retryCount: this.state.retryCount + 1,
        isRecovering: false
      });
    }, 500);
  };

  private handleReportIssue = async (): Promise<void> => {
    if (!this.state.error || !this.state.errorInfo) return;

    // Re-send error report with user action context
    await this.errorReporter.reportError(
      this.state.error, 
      this.state.errorInfo, 
      this.state.errorId,
      {
        userAction: 'manual_report',
        retryCount: this.state.retryCount
      }
    );
  };

  private handleGoHome = (): void => {
    // Navigate to home page
    window.location.href = '/';
  };

  render(): ReactNode {
    if (this.state.hasError) {
      const { 
        fallback: FallbackComponent = DefaultErrorFallback,
        enableRetry = true,
        maxRetries = 3
      } = this.props;
      
      const canRetry = enableRetry && 
                      isRetryableError(this.state.error!) && 
                      this.state.retryCount < maxRetries;

      if (this.state.isRecovering) {
        return (
          <div className="min-h-[400px] flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Recovering...</p>
            </div>
          </div>
        );
      }

      return (
        <FallbackComponent
          error={this.state.error}
          errorId={this.state.errorId}
          retryCount={this.state.retryCount}
          onRetry={this.handleRetry}
          onReportIssue={this.handleReportIssue}
          onGoHome={this.handleGoHome}
          canRetry={canRetry}
        />
      );
    }

    return this.props.children;
  }
}

// Global error handler for unhandled promise rejections
export const setupGlobalErrorHandling = (): void => {
  const errorReporter = ErrorReportingService.getInstance();

  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    const error = event.reason instanceof Error ? event.reason : new Error(String(event.reason));
    const errorId = generateErrorId();
    
    console.error('Unhandled promise rejection:', error);
    
    errorReporter.reportError(error, { componentStack: 'Promise rejection' }, errorId, {
      type: 'unhandled_rejection',
      promise: event.promise
    });
  });

  // Handle global errors
  window.addEventListener('error', (event) => {
    const error = event.error || new Error(event.message);
    const errorId = generateErrorId();
    
    console.error('Global error:', error);
    
    errorReporter.reportError(error, { componentStack: 'Global error' }, errorId, {
      type: 'global_error',
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno
    });
  });
};

// HOC for wrapping components with error boundary
export function withErrorBoundary<T extends {}>(
  Component: React.ComponentType<T>,
  errorBoundaryProps?: Partial<ErrorBoundaryProps>
) {
  return function WithErrorBoundary(props: T) {
    return (
      <EnhancedErrorBoundary {...errorBoundaryProps}>
        <Component {...props} />
      </EnhancedErrorBoundary>
    );
  };
}

export default EnhancedErrorBoundary;