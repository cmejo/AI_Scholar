import React, { Component, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Mic, MicOff } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: string | null;
  retryCount: number;
}

export class VoiceErrorBoundary extends Component<Props, State> {
  private maxRetries = 3;

  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Voice feature error:', error, errorInfo);
    
    this.setState({
      errorInfo: errorInfo.componentStack,
    });

    // Report error to analytics or error tracking service
    this.reportError(error, errorInfo);
  }

  private reportError = (error: Error, errorInfo: React.ErrorInfo) => {
    // In a real app, you'd send this to your error tracking service
    const errorReport = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    };

    console.error('Voice Error Report:', errorReport);
    
    // You could send this to services like Sentry, LogRocket, etc.
    // Example: Sentry.captureException(error, { extra: errorReport });
  };

  private handleRetry = () => {
    if (this.state.retryCount < this.maxRetries) {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        retryCount: prevState.retryCount + 1,
      }));
    }
  };

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
    });
  };

  private getErrorMessage = (error: Error): string => {
    if (error.message.includes('microphone')) {
      return 'Microphone access failed. Please check your browser permissions and try again.';
    }
    
    if (error.message.includes('speech')) {
      return 'Speech recognition failed. This might be due to network issues or browser compatibility.';
    }
    
    if (error.message.includes('synthesis')) {
      return 'Text-to-speech failed. Please check your audio settings.';
    }

    return 'Voice features encountered an error. Please try again or disable voice features.';
  };

  private getRecoveryInstructions = (): string[] => {
    const instructions = [];
    
    if (this.state.error?.message.includes('microphone')) {
      instructions.push('Check that your microphone is connected and working');
      instructions.push('Allow microphone permissions in your browser');
      instructions.push('Try refreshing the page');
    } else if (this.state.error?.message.includes('speech')) {
      instructions.push('Check your internet connection');
      instructions.push('Try using a different browser (Chrome or Edge recommended)');
      instructions.push('Ensure your microphone is not being used by another application');
    } else {
      instructions.push('Try refreshing the page');
      instructions.push('Check your browser\'s audio settings');
      instructions.push('Use a supported browser (Chrome, Edge, or Safari)');
    }

    return instructions;
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const canRetry = this.state.retryCount < this.maxRetries;
      const errorMessage = this.getErrorMessage(this.state.error!);
      const recoveryInstructions = this.getRecoveryInstructions();

      return (
        <div className="bg-red-900/20 border border-red-700/50 rounded-lg p-4 m-2">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <MicOff className="w-6 h-6 text-red-400" />
            </div>
            
            <div className="flex-1">
              <h3 className="text-sm font-medium text-red-300 mb-2">
                Voice Feature Error
              </h3>
              
              <p className="text-sm text-red-200 mb-3">
                {errorMessage}
              </p>

              {/* Recovery Instructions */}
              <div className="mb-4">
                <h4 className="text-xs font-medium text-red-300 mb-2 uppercase tracking-wide">
                  Try these steps:
                </h4>
                <ul className="text-xs text-red-200 space-y-1">
                  {recoveryInstructions.map((instruction, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <span className="text-red-400 mt-0.5">•</span>
                      <span>{instruction}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-2">
                {canRetry && (
                  <button
                    onClick={this.handleRetry}
                    className="flex items-center space-x-1 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs rounded-md transition-colors"
                  >
                    <RefreshCw className="w-3 h-3" />
                    <span>Retry ({this.maxRetries - this.state.retryCount} left)</span>
                  </button>
                )}
                
                <button
                  onClick={this.handleReset}
                  className="flex items-center space-x-1 px-3 py-1.5 bg-gray-600 hover:bg-gray-700 text-white text-xs rounded-md transition-colors"
                >
                  <Mic className="w-3 h-3" />
                  <span>Reset Voice Features</span>
                </button>
              </div>

              {/* Error Details (Development) */}
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-4">
                  <summary className="text-xs text-red-300 cursor-pointer hover:text-red-200">
                    Error Details (Development)
                  </summary>
                  <div className="mt-2 p-2 bg-red-950/50 rounded text-xs font-mono text-red-200 overflow-auto">
                    <div className="mb-2">
                      <strong>Error:</strong> {this.state.error.message}
                    </div>
                    {this.state.error.stack && (
                      <div className="mb-2">
                        <strong>Stack:</strong>
                        <pre className="whitespace-pre-wrap text-xs">
                          {this.state.error.stack}
                        </pre>
                      </div>
                    )}
                    {this.state.errorInfo && (
                      <div>
                        <strong>Component Stack:</strong>
                        <pre className="whitespace-pre-wrap text-xs">
                          {this.state.errorInfo}
                        </pre>
                      </div>
                    )}
                  </div>
                </details>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default VoiceErrorBoundary;