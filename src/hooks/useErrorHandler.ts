import { useCallback, useRef, useState } from 'react';
import { errorTrackingService } from '../services/errorTrackingService';
import type {
    AsyncErrorHandlerReturn,
    ErrorHandlerOptions,
    ErrorHandlerReturn,
    ErrorNotification,
    FormError,
    RetryHandlerOptions,
    RetryHandlerReturn,
    StandardError
} from '../types/ui';
import { convertAPIErrorToStandard, createError } from '../utils/errorFactory';
import { globalErrorHandler } from '../utils/globalErrorHandler';

/**
 * Hook for handling errors in React components
 * Provides standardized error handling, reporting, and user feedback
 */
export function useErrorHandler(options: ErrorHandlerOptions = {}): ErrorHandlerReturn {
  const {
    enableNotifications = true,
    enableReporting = true,
    context = 'component',
    onError,
  } = options;

  const errorCountRef = useRef(0);

  const handleError = useCallback((error: unknown, errorContext?: string): StandardError => {
    let standardError: StandardError;

    // Convert different error types to StandardError
    if (error instanceof Error) {
      standardError = createError.component(
        error.message,
        {
          component: errorContext || context,
          operation: 'error_handling',
        },
        {
          originalError: error.name,
          stack: error.stack,
        }
      );
    } else if (typeof error === 'object' && error !== null && 'type' in error) {
      // Handle API errors or other structured errors
      standardError = convertAPIErrorToStandard(error);
    } else {
      // Handle unknown error types
      standardError = createError.unknown(
        String(error),
        {
          component: errorContext || context,
          operation: 'error_handling',
        }
      );
    }

    errorCountRef.current++;

    // Call custom error handler if provided
    if (onError) {
      try {
        onError(standardError);
      } catch (handlerError) {
        console.error('Error in custom error handler:', handlerError);
      }
    }

    // Show notification if enabled
    if (enableNotifications) {
      const notification = createErrorNotification(standardError);
      // Here you would integrate with your notification system
      // For now, we'll just log it
      console.warn('Error notification:', notification);
    }

    // Report to error tracking service
    if (enableReporting) {
      errorTrackingService.reportError({
        error_type: standardError.type,
        error_message: standardError.message,
        stack_trace: standardError.stack || '',
        severity: standardError.severity,
        category: 'application',
        feature_name: standardError.context?.feature || context,
        operation: standardError.context?.operation || 'error_handling',
        context_data: {
          errorId: standardError.id,
          errorCode: standardError.code,
          recoverable: standardError.recoverable,
          retryable: standardError.retryable,
          context: standardError.context,
          details: standardError.details,
        },
      });
    }

    return standardError;
  }, [context, onError, enableNotifications, enableReporting]);

  const reportError = useCallback((error: Error, errorContext?: Record<string, unknown>): void => {
    if (enableReporting) {
      globalErrorHandler.reportManualError(error, {
        component: context,
        ...errorContext,
      });
    }
  }, [context, enableReporting]);

  const clearErrors = useCallback((): void => {
    errorCountRef.current = 0;
  }, []);

  return {
    handleError,
    reportError,
    clearErrors,
    errorCount: errorCountRef.current,
  };
}

// Helper function to create error notifications
function createErrorNotification(error: StandardError): ErrorNotification {
  const notification: ErrorNotification = {
    id: `notification_${error.id}`,
    title: 'Error',
    message: error.userMessage,
    type: error.severity === 'critical' || error.severity === 'high' ? 'error' : 'warning',
    duration: error.severity === 'critical' ? 0 : 5000, // Critical errors don't auto-dismiss
    dismissible: true,
  };

  if (error.retryable) {
    notification.actions = [
      {
        label: 'Retry',
        action: () => {
          // This would trigger a retry mechanism
          console.log('Retry action triggered for error:', error.id);
        },
        style: 'primary',
      }
    ];
  }

  return notification;
}

/**
 * Hook for handling errors in async operations
 * Automatically catches and handles promise rejections
 */
export function useAsyncErrorHandler<T>(
  options: ErrorHandlerOptions = {}
): AsyncErrorHandlerReturn<T> {
  const { handleError } = useErrorHandler(options);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<StandardError | null>(null);

  const execute = useCallback(async (asyncFn: () => Promise<T>): Promise<T | null> => {
    setLoading(true);
    setError(null);

    try {
      const result = await asyncFn();
      setLoading(false);
      return result;
    } catch (err) {
      setLoading(false);
      const standardError = handleError(err, 'async_operation');
      setError(standardError);
      return null;
    }
  }, [handleError]);

  const clearError = useCallback((): void => {
    setError(null);
  }, []);

  return {
    execute,
    loading,
    error,
    clearError,
  };
}

/**
 * Hook for handling form validation errors
 * Provides field-level error management
 */
export function useFormErrorHandler() {
  const [fieldErrors, setFieldErrors] = useState<Record<string, FormError>>({});

  const setFieldError = useCallback((field: string, message: string, code = 'VALIDATION_ERROR', value?: unknown): void => {
    setFieldErrors((prev: Record<string, FormError>) => ({
      ...prev,
      [field]: {
        field,
        message,
        code,
        value,
      },
    }));
  }, []);

  const clearFieldError = useCallback((field: string): void => {
    setFieldErrors((prev: Record<string, FormError>) => {
      const { [field]: _removed, ...rest } = prev;
      return rest;
    });
  }, []);

  const clearAllErrors = useCallback((): void => {
    setFieldErrors({});
  }, []);

  const handleValidationError = useCallback((error: StandardError): void => {
    if (error.details && typeof error.details === 'object') {
      // Handle validation errors with field details
      if (Array.isArray(error.details)) {
        // Handle array of validation errors
        error.details.forEach((validationError: any) => {
          if (validationError.field && validationError.message) {
            setFieldError(
              validationError.field,
              validationError.message,
              validationError.code || 'VALIDATION_ERROR',
              validationError.value
            );
          }
        });
      } else {
        // Handle object with field keys
        Object.entries(error.details).forEach(([field, details]) => {
          if (typeof details === 'string') {
            setFieldError(field, details);
          } else if (typeof details === 'object' && details !== null && 'message' in details) {
            setFieldError(
              field,
              (details as any).message,
              (details as any).code || 'VALIDATION_ERROR',
              (details as any).value
            );
          }
        });
      }
    }
  }, [setFieldError]);

  const hasErrors = Object.keys(fieldErrors).length > 0;
  const isValid = !hasErrors;

  return {
    fieldErrors,
    setFieldError,
    clearFieldError,
    clearAllErrors,
    hasErrors,
    isValid,
    handleValidationError,
  };
}

/**
 * Hook for handling retries with exponential backoff
 * Automatically retries failed operations based on error type
 */
export function useRetryHandler<T>(
  options: RetryHandlerOptions = {}
): RetryHandlerReturn<T> {
  const {
    maxRetries = 3,
    retryDelay = 1000,
    backoffMultiplier = 2,
    retryCondition = (error: StandardError) => error.retryable,
  } = options;

  const { handleError } = useErrorHandler();
  const [retryCount, setRetryCount] = useState(0);
  const [isRetrying, setIsRetrying] = useState(false);

  const executeWithRetry = useCallback(async (asyncFn: () => Promise<T>): Promise<T> => {
    setRetryCount(0);
    setIsRetrying(false);

    const attempt = async (attemptCount: number): Promise<T> => {
      try {
        const result = await asyncFn();
        setIsRetrying(false);
        return result;
      } catch (error) {
        const standardError = handleError(error, 'retry_operation');
        
        if (attemptCount < maxRetries && retryCondition(standardError)) {
          setRetryCount(attemptCount + 1);
          setIsRetrying(true);
          
          const delay = retryDelay * Math.pow(backoffMultiplier, attemptCount);
          await new Promise(resolve => setTimeout(resolve, delay));
          
          return attempt(attemptCount + 1);
        }
        
        setIsRetrying(false);
        throw standardError;
      }
    };

    return attempt(0);
  }, [handleError, maxRetries, retryDelay, backoffMultiplier, retryCondition]);

  return {
    executeWithRetry,
    retryCount,
    isRetrying,
  };
}