import { errorTrackingService } from '../services/errorTrackingService';
import type { StandardError } from '../types/ui';
import type { APIErrorClass } from './apiErrorHandler';
import { createError } from './errorFactory';

// Global error handler configuration
interface GlobalErrorHandlerConfig {
  enableConsoleLogging: boolean;
  enableErrorReporting: boolean;
  enableUserNotification: boolean;
  maxErrorsPerSession: number;
  errorCooldownMs: number;
}

class GlobalErrorHandler {
  private config: GlobalErrorHandlerConfig;
  private errorCount = 0;
  private lastErrorTime = 0;
  private errorCache = new Set<string>();

  constructor(config: Partial<GlobalErrorHandlerConfig> = {}) {
    this.config = {
      enableConsoleLogging: import.meta.env?.DEV || false,
      enableErrorReporting: true,
      enableUserNotification: true,
      maxErrorsPerSession: 50,
      errorCooldownMs: 1000,
      ...config,
    };

    this.initialize();
  }

  private initialize(): void {
    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.handleUnhandledRejection(event);
    });

    // Handle uncaught JavaScript errors
    window.addEventListener('error', (event) => {
      this.handleUncaughtError(event);
    });

    // Handle resource loading errors
    window.addEventListener('error', (event) => {
      if (event.target !== window) {
        this.handleResourceError(event);
      }
    }, true);

    // Handle console errors (optional)
    if (this.config.enableConsoleLogging) {
      this.interceptConsoleError();
    }
  }

  private handleUnhandledRejection(event: PromiseRejectionEvent): void {
    const error = event.reason;
    const errorInfo = {
      type: 'unhandled_promise_rejection',
      reason: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined,
      url: window.location.href,
      timestamp: new Date().toISOString(),
    };

    this.reportError(error, errorInfo);

    // Prevent the default browser behavior
    event.preventDefault();
  }

  private handleUncaughtError(event: ErrorEvent): void {
    const errorInfo = {
      type: 'uncaught_javascript_error',
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      url: window.location.href,
      timestamp: new Date().toISOString(),
    };

    this.reportError(event.error || new Error(event.message), errorInfo);
  }

  private handleResourceError(event: Event): void {
    const target = event.target as HTMLElement;
    const errorInfo = {
      type: 'resource_loading_error',
      tagName: target.tagName,
      src: (target as HTMLImageElement | HTMLScriptElement).src || 
           (target as HTMLLinkElement).href || 
           'unknown',
      url: window.location.href,
      timestamp: new Date().toISOString(),
    };

    const error = new Error(`Failed to load resource: ${errorInfo.src}`);
    this.reportError(error, errorInfo);
  }

  private interceptConsoleError(): void {
    const originalConsoleError = console.error;
    console.error = (...args: unknown[]) => {
      // Call original console.error
      originalConsoleError.apply(console, args);

      // Report console errors
      const errorMessage = args.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
      ).join(' ');

      const error = new Error(`Console Error: ${errorMessage}`);
      this.reportError(error, {
        type: 'console_error',
        arguments: args,
        url: window.location.href,
        timestamp: new Date().toISOString(),
      });
    };
  }

  private reportError(error: Error | APIErrorClass | StandardError, context: Record<string, unknown>): void {
    // Check rate limiting
    if (!this.shouldReportError(error)) {
      return;
    }

    // Log to console in development
    if (this.config.enableConsoleLogging) {
      console.group('🚨 Global Error Handler');
      console.error('Error:', error);
      console.error('Context:', context);
      console.groupEnd();
    }

    // Report to error tracking service
    if (this.config.enableErrorReporting) {
      try {
        const standardError = this.convertToStandardError(error, context);
        errorTrackingService.reportError({
          error_type: standardError.type,
          error_message: error.message,
          stack_trace: error.stack || '',
          severity: standardError.severity,
          category: 'application',
          feature_name: 'global_error_handler',
          operation: (context as any).type || 'unknown',
          context_data: {
            ...context,
            errorId: standardError.id,
            errorCount: this.errorCount,
            userAgent: navigator.userAgent,
            sessionId: this.getSessionId(),
            recoverable: standardError.recoverable,
            retryable: standardError.retryable,
          },
        });
      } catch (reportingError) {
        console.error('Failed to report error:', reportingError);
      }
    }

    // Show user notification for critical errors
    if (this.config.enableUserNotification && this.shouldNotifyUser(error, context)) {
      this.showUserNotification(error, context);
    }

    this.errorCount++;
  }

  private shouldReportError(error: Error | APIErrorClass | StandardError): boolean {
    // Rate limiting
    const now = Date.now();
    if (now - this.lastErrorTime < this.config.errorCooldownMs) {
      return false;
    }

    // Max errors per session
    if (this.errorCount >= this.config.maxErrorsPerSession) {
      return false;
    }

    // Deduplicate similar errors
    const errorKey = `${error.message}_${error.stack?.split('\n')[0] || ''}`;
    if (this.errorCache.has(errorKey)) {
      return false;
    }

    this.errorCache.add(errorKey);
    this.lastErrorTime = now;

    // Clean up cache periodically
    if (this.errorCache.size > 100) {
      this.errorCache.clear();
    }

    return true;
  }

  private convertToStandardError(error: Error | APIErrorClass | StandardError, context: Record<string, unknown>): StandardError {
    // If already a StandardError, return as-is
    if ('id' in error && 'type' in error && 'severity' in error) {
      return error as StandardError;
    }

    // If it's an APIErrorClass, convert it
    if ('type' in error && 'statusCode' in error) {
      const apiError = error as APIErrorClass;
      return createError.component(
        apiError.message,
        {
          component: 'global_error_handler',
          operation: (context as any).type || 'unknown',
        },
        {
          originalError: apiError.type.toString(),
          statusCode: apiError.statusCode,
          apiErrorId: apiError.id,
        }
      );
    }

    // Convert regular Error based on context
    const contextType = (context as any).type;
    switch (contextType) {
      case 'unhandled_promise_rejection':
        return createError.component(
          error.message,
          {
            component: 'global_error_handler',
            operation: 'unhandled_promise_rejection',
          },
          {
            originalError: error.name,
            stack: error.stack,
          }
        );
      case 'uncaught_javascript_error':
        return createError.component(
          error.message,
          {
            component: 'global_error_handler',
            operation: 'uncaught_javascript_error',
          },
          {
            originalError: error.name,
            stack: error.stack,
          }
        );
      case 'resource_loading_error':
        return createError.network(
          error.message,
          undefined,
          {
            component: 'global_error_handler',
            operation: 'resource_loading_error',
          }
        );
      case 'console_error':
        return createError.component(
          error.message,
          {
            component: 'global_error_handler',
            operation: 'console_error',
          },
          {
            originalError: error.name,
            stack: error.stack,
          }
        );
      default:
        return createError.unknown(
          error.message,
          {
            component: 'global_error_handler',
            operation: contextType || 'unknown',
          },
          error
        );
    }
  }

  private shouldNotifyUser(error: Error | APIErrorClass | StandardError, context: Record<string, unknown>): boolean {
    const contextType = (context as any).type;
    
    // Don't notify for resource loading errors
    if (contextType === 'resource_loading_error') {
      return false;
    }

    // Don't notify for console errors
    if (contextType === 'console_error') {
      return false;
    }

    const standardError = this.convertToStandardError(error, context);
    
    // Only notify for high or critical severity errors
    return standardError.severity === 'high' || standardError.severity === 'critical';
  }

  private showUserNotification(error: Error | APIErrorClass | StandardError, context: Record<string, unknown>): void {
    const standardError = this.convertToStandardError(error, context);
    // Create a simple notification
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-red-600 text-white p-4 rounded-lg shadow-lg z-50 max-w-sm';
    notification.innerHTML = `
      <div class="flex items-start space-x-3">
        <div class="flex-shrink-0">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
          </svg>
        </div>
        <div class="flex-1">
          <h4 class="font-medium">Something went wrong</h4>
          <p class="text-sm opacity-90 mt-1">
            ${standardError.userMessage}
          </p>
          ${standardError.recoverable ? '<p class="text-xs opacity-75 mt-1">You can try refreshing the page.</p>' : ''}
        </div>
        <button class="flex-shrink-0 text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
          </svg>
        </button>
      </div>
    `;

    document.body.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (notification.parentElement) {
        notification.remove();
      }
    }, 5000);
  }

  private getSessionId(): string {
    let sessionId = sessionStorage.getItem('error_session_id');
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
      sessionStorage.setItem('error_session_id', sessionId);
    }
    return sessionId;
  }

  // Public methods for manual error reporting
  public reportManualError(error: Error, context?: Record<string, unknown>): void {
    this.reportError(error, {
      type: 'manual_report',
      ...context,
      timestamp: new Date().toISOString(),
    });
  }

  public updateConfig(newConfig: Partial<GlobalErrorHandlerConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  public getErrorStats(): { errorCount: number; lastErrorTime: number } {
    return {
      errorCount: this.errorCount,
      lastErrorTime: this.lastErrorTime,
    };
  }

  public clearErrorCache(): void {
    this.errorCache.clear();
    this.errorCount = 0;
    this.lastErrorTime = 0;
  }
}

// Create and export global instance
export const globalErrorHandler = new GlobalErrorHandler();

// Export for manual initialization with custom config
export { GlobalErrorHandler };

// Initialize global error handling
export function initializeGlobalErrorHandling(config?: Partial<GlobalErrorHandlerConfig>): GlobalErrorHandler {
  return new GlobalErrorHandler(config);
}