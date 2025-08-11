import { AlertTriangle, Bug, Home, RefreshCw } from 'lucide-react';
import type { ReactNode } from 'react';
import React, { Component } from 'react';
import { errorTrackingService } from '../services/errorTrackingService';
import type { ErrorBoundaryProps, ErrorBoundaryState, StandardError } from '../types/ui';
import { createError } from '../utils/errorFactory';

interface ErrorDetails {
  message: string;
  stack?: string;
  componentStack?: string;
  timestamp: Date;
  userAgent: string;
  url: string;
  errorId: string;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private standardError: StandardError | null = null;
  private resetTimeoutId: number | null = null;

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  override componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    this.setState({
      error,
      errorInfo,
    });

    // Create standardized error
    this.standardError = createError.component(
      error.message,
      {
        component: this.props.children?.toString() || 'Unknown',
        operation: 'render',
        metadata: {
          componentStack: errorInfo.componentStack,
          retryCount: this.state.retryCount,
        },
      },
      {
        originalError: error.name,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
      }
    );

    // Collect error details
    const errorDetails: ErrorDetails = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      errorId: this.standardError.id,
    };

    // Report to error tracking service
    errorTrackingService.reportError({
      error_type: 'ComponentError',
      error_message: error.message,
      stack_trace: error.stack || '',
      severity: 'high',
      category: 'application',
      feature_name: 'react_component',
      operation: 'component_render',
      context_data: {
        errorId: this.standardError.id,
        componentStack: errorInfo.componentStack ?? undefined,
        url: window.location.href,
        timestamp: errorDetails.timestamp.toISOString(),
        retryCount: this.state.retryCount,
        standardError: {
          type: this.standardError.type,
          code: this.standardError.code,
          severity: this.standardError.severity,
          recoverable: this.standardError.recoverable,
          retryable: this.standardError.retryable,
        },
      },
    });

    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log to console in development
    if (import.meta.env?.DEV) {
      console.group('🚨 Error Boundary');
      console.error('Error:', error);
      console.error('Component Stack:', errorInfo.componentStack);
      console.error('Standard Error:', this.standardError);
      console.groupEnd();
    }
  }

  private handleRetry = (): void => {
    const maxRetries = this.props.maxRetries || 3;
    
    if (this.state.retryCount >= maxRetries) {
      console.warn('Maximum retry attempts reached');
      return;
    }

    this.setState(prevState => ({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: prevState.retryCount + 1,
    }));
    
    this.standardError = null;

    // Clear any existing reset timeout
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
      this.resetTimeoutId = null;
    }
  };

  private handleReportBug = (): void => {
    if (this.standardError && this.state.error) {
      const bugReportUrl = `mailto:support@example.com?subject=Bug Report - ${this.standardError.id}&body=${encodeURIComponent(
        `Error ID: ${this.standardError.id}\n` +
        `Error Type: ${this.standardError.type}\n` +
        `Error Code: ${this.standardError.code}\n` +
        `Error: ${this.state.error.message}\n` +
        `Severity: ${this.standardError.severity}\n` +
        `Recoverable: ${this.standardError.recoverable}\n` +
        `Retryable: ${this.standardError.retryable}\n` +
        `URL: ${window.location.href}\n` +
        `Timestamp: ${this.standardError.timestamp.toISOString()}\n` +
        `User Agent: ${navigator.userAgent}\n` +
        `Retry Count: ${this.state.retryCount}\n\n` +
        `Please describe what you were doing when this error occurred:\n\n`
      )}`;
      window.open(bugReportUrl);
    }
  };

  private handleGoHome = (): void => {
    window.location.href = '/';
  };

  override componentDidUpdate(prevProps: ErrorBoundaryProps): void {
    const { resetKeys, resetOnPropsChange } = this.props;
    const { hasError } = this.state;

    // Reset error state if resetKeys have changed
    if (hasError && resetKeys && prevProps.resetKeys) {
      const hasResetKeyChanged = resetKeys.some(
        (key, index) => key !== prevProps.resetKeys?.[index]
      );
      
      if (hasResetKeyChanged) {
        this.setState({
          hasError: false,
          error: null,
          errorInfo: null,
          retryCount: 0,
        });
        this.standardError = null;
      }
    }

    // Reset on any prop change if enabled
    if (hasError && resetOnPropsChange && prevProps !== this.props) {
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null,
        retryCount: 0,
      });
      this.standardError = null;
    }
  }

  override componentWillUnmount(): void {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }
  }

  override render(): ReactNode {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        if (typeof this.props.fallback === 'function') {
          return this.props.fallback(
            this.state.error!,
            this.state.errorInfo!,
            this.handleRetry
          );
        }
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-gray-800 rounded-lg shadow-xl p-6 text-center">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-8 h-8 text-red-400" />
              </div>
            </div>
            
            <h1 className="text-xl font-semibold text-white mb-2">
              Something went wrong
            </h1>
            
            <p className="text-gray-400 mb-6">
              We're sorry, but something unexpected happened. The error has been reported automatically.
            </p>

            {this.standardError && (
              <div className="bg-gray-700 rounded p-3 mb-6">
                <p className="text-xs text-gray-300 mb-1">Error ID:</p>
                <code className="text-xs text-blue-400 font-mono">{this.standardError.id}</code>
                {import.meta.env?.DEV && (
                  <div className="mt-2 pt-2 border-t border-gray-600">
                    <p className="text-xs text-gray-400">Type: {this.standardError.type}</p>
                    <p className="text-xs text-gray-400">Code: {this.standardError.code}</p>
                    <p className="text-xs text-gray-400">Severity: {this.standardError.severity}</p>
                    <p className="text-xs text-gray-400">Retryable: {this.standardError.retryable ? 'Yes' : 'No'}</p>
                    <p className="text-xs text-gray-400">Retry Count: {this.state.retryCount}</p>
                  </div>
                )}
              </div>
            )}

            {import.meta.env?.DEV && this.state.error && (
              <details className="text-left mb-6 bg-gray-700 rounded p-3">
                <summary className="text-sm text-gray-300 cursor-pointer mb-2">
                  Error Details (Development)
                </summary>
                <div className="text-xs text-red-400 font-mono whitespace-pre-wrap">
                  {this.state.error.message}
                  {this.state.error.stack && (
                    <>
                      {'\n\nStack Trace:\n'}
                      {this.state.error.stack}
                    </>
                  )}
                  {this.state.errorInfo?.componentStack && (
                    <>
                      {'\n\nComponent Stack:\n'}
                      {this.state.errorInfo.componentStack}
                    </>
                  )}
                </div>
              </details>
            )}

            <div className="space-y-3">
              {this.standardError?.retryable && this.state.retryCount < (this.props.maxRetries || 3) && (
                <button
                  onClick={this.handleRetry}
                  className="w-full flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Try Again ({this.state.retryCount + 1}/{this.props.maxRetries || 3})</span>
                </button>
              )}

              <div className="flex space-x-3">
                <button
                  onClick={this.handleGoHome}
                  className="flex-1 flex items-center justify-center space-x-2 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  <Home className="w-4 h-4" />
                  <span>Go Home</span>
                </button>

                <button
                  onClick={this.handleReportBug}
                  className="flex-1 flex items-center justify-center space-x-2 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  <Bug className="w-4 h-4" />
                  <span>Report Bug</span>
                </button>
              </div>
            </div>

            <p className="text-xs text-gray-500 mt-4">
              If this problem persists, please contact support with the error ID above.
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Higher-order component for wrapping components with error boundary
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ErrorBoundaryProps, 'children'>
): React.ComponentType<P> {
  const WrappedComponent = (props: P): JSX.Element => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
}

// Hook for error reporting in functional components
export function useErrorHandler(): (error: Error, errorInfo?: Record<string, unknown>) => void {
  return (error: Error, errorInfo?: Record<string, unknown>): void => {
    const errorId = `error_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
    
    errorTrackingService.reportError({
      error_type: error.name || 'Error',
      error_message: error.message,
      stack_trace: error.stack || '',
      severity: 'medium',
      category: 'application',
      feature_name: 'react_hook',
      operation: 'error_handler',
      context_data: {
        errorId,
        ...errorInfo,
        url: window.location.href,
        timestamp: new Date().toISOString(),
      },
    });

    if (import.meta.env?.DEV) {
      console.error('Error reported via useErrorHandler:', error);
      console.error('Additional info:', errorInfo);
    }
  };
}