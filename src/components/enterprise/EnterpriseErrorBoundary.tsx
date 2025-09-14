/**
 * Enterprise-specific error boundary with enhanced fallback states and monitoring
 */
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Shield, TrendingUp, Workflow, Zap } from 'lucide-react';

interface Props {
  children: ReactNode;
  componentType: 'analytics' | 'security' | 'workflow' | 'integration' | 'performance';
  fallbackData?: any;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
  retryCount: number;
}

export class EnterpriseErrorBoundary extends Component<Props, State> {
  private retryTimeout?: NodeJS.Timeout;

  constructor(props: Props) {
    super(props);
    this.state = { 
      hasError: false,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo
    });

    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo);

    // Report error to enterprise monitoring
    this.reportEnterpriseError(error, errorInfo);
  }

  componentWillUnmount() {
    if (this.retryTimeout) {
      clearTimeout(this.retryTimeout);
    }
  }

  private async reportEnterpriseError(error: Error, errorInfo: ErrorInfo) {
    try {
      const errorReport = {
        error: error.message,
        context: `enterprise_${this.props.componentType}`,
        errorId: `enterprise_${this.props.componentType}_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        componentType: this.props.componentType,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
        retryCount: this.state.retryCount
      };

      await fetch('/api/error-tracking/enterprise-errors/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorReport)
      });

      // Also log to console in development
      if (process.env.NODE_ENV === 'development') {
        console.error(`Enterprise ${this.props.componentType} Error:`, errorReport);
      }
    } catch (reportingError) {
      console.error('Failed to report enterprise error:', reportingError);
    }
  }

  private handleRetry = () => {
    this.setState(prevState => ({
      hasError: false,
      error: undefined,
      errorInfo: undefined,
      retryCount: prevState.retryCount + 1
    }));
  };

  private handleAutoRetry = () => {
    // Auto-retry after 5 seconds for transient errors
    this.retryTimeout = setTimeout(() => {
      if (this.state.retryCount < 3) {
        this.handleRetry();
      }
    }, 5000);
  };

  private handleReload = () => {
    window.location.reload();
  };

  private getComponentIcon() {
    switch (this.props.componentType) {
      case 'analytics':
        return <TrendingUp className="w-12 h-12 text-blue-500" />;
      case 'security':
        return <Shield className="w-12 h-12 text-red-500" />;
      case 'workflow':
        return <Workflow className="w-12 h-12 text-green-500" />;
      case 'integration':
        return <Zap className="w-12 h-12 text-yellow-500" />;
      case 'performance':
        return <TrendingUp className="w-12 h-12 text-purple-500" />;
      default:
        return <AlertTriangle className="w-12 h-12 text-red-500" />;
    }
  }

  private getComponentTitle() {
    switch (this.props.componentType) {
      case 'analytics':
        return 'Analytics Dashboard';
      case 'security':
        return 'Security Dashboard';
      case 'workflow':
        return 'Workflow Manager';
      case 'integration':
        return 'Integration Hub';
      case 'performance':
        return 'Performance Monitor';
      default:
        return 'Enterprise Component';
    }
  }

  private getFallbackContent() {
    const { componentType, fallbackData } = this.props;

    if (fallbackData) {
      switch (componentType) {
        case 'analytics':
          return (
            <div className="bg-gray-800 rounded-lg p-4 mt-4">
              <h3 className="text-lg font-semibold mb-2">Cached Analytics Data</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Total Queries:</span>
                  <span className="ml-2 text-white">{fallbackData.totalQueries || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-gray-400">Active Users:</span>
                  <span className="ml-2 text-white">{fallbackData.activeUsers || 'N/A'}</span>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Last updated: {fallbackData.lastUpdated || 'Unknown'}
              </p>
            </div>
          );
        case 'security':
          return (
            <div className="bg-gray-800 rounded-lg p-4 mt-4">
              <h3 className="text-lg font-semibold mb-2">Security Status</h3>
              <div className="text-sm">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-400">System Status:</span>
                  <span className="text-green-400">Secure</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Active Sessions:</span>
                  <span className="text-white">{fallbackData?.activeSessions || 'Unknown'}</span>
                </div>
              </div>
            </div>
          );
        default:
          return (
            <div className="bg-gray-800 rounded-lg p-4 mt-4">
              <h3 className="text-lg font-semibold mb-2">Limited Functionality</h3>
              <p className="text-gray-400 text-sm">
                Some features may be unavailable while the service is being restored.
              </p>
            </div>
          );
      }
    }

    return null;
  }

  render() {
    if (this.state.hasError) {
      const isTransientError = this.state.error?.message.includes('timeout') || 
                              this.state.error?.message.includes('network') ||
                              this.state.error?.message.includes('fetch');

      // Auto-retry for transient errors
      if (isTransientError && this.state.retryCount < 3) {
        this.handleAutoRetry();
      }

      return (
        <div className="min-h-96 bg-gray-900 text-white flex items-center justify-center p-6">
          <div className="max-w-lg w-full bg-gray-800 rounded-lg p-6 text-center">
            {this.getComponentIcon()}
            
            <h2 className="text-xl font-bold mt-4 mb-2">
              {this.getComponentTitle()} Unavailable
            </h2>
            
            <p className="text-gray-400 mb-4">
              We're experiencing issues with the {this.props.componentType} service. 
              {isTransientError && this.state.retryCount < 3 && (
                <span className="block mt-2 text-blue-400">
                  Attempting to reconnect automatically...
                </span>
              )}
            </p>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="bg-gray-900 rounded p-3 mb-4 text-left">
                <p className="text-red-400 text-sm font-mono">
                  {this.state.error.message}
                </p>
                {this.state.error.stack && (
                  <pre className="text-xs text-gray-500 mt-2 overflow-auto max-h-32">
                    {this.state.error.stack}
                  </pre>
                )}
              </div>
            )}

            {this.getFallbackContent()}

            <div className="flex space-x-3 mt-6">
              <button
                onClick={this.handleRetry}
                className="flex-1 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center justify-center space-x-2"
                disabled={this.state.retryCount >= 5}
              >
                <RefreshCw className="w-4 h-4" />
                <span>
                  {this.state.retryCount >= 5 ? 'Max Retries Reached' : 'Try Again'}
                </span>
              </button>
              
              <button
                onClick={this.handleReload}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                Reload Page
              </button>
            </div>

            <div className="mt-4 text-xs text-gray-500">
              <p>Error ID: enterprise_{this.props.componentType}_{Date.now()}</p>
              {this.state.retryCount > 0 && (
                <p>Retry attempts: {this.state.retryCount}</p>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}