import { errorTrackingService } from '../services/errorTrackingService';
import type {
    APIError,
    APIResponse,
    AuthenticationErrorDetails,
    AuthorizationErrorDetails,
    NetworkErrorDetails,
    ServerErrorDetails,
    ValidationErrorDetails
} from '../types/api';
import { APIErrorType } from '../types/api';
import type { ErrorSeverity, StandardError } from '../types/ui';
import { ErrorType } from '../types/ui';

// Enhanced API error class with proper typing
export class APIErrorClass extends Error implements StandardError {
  public readonly id: string;
  public readonly code: string;
  public readonly type: ErrorType;
  public readonly statusCode?: number;
  public readonly details?: Record<string, unknown>;
  public readonly timestamp: Date;
  public readonly requestId?: string;
  public readonly severity: ErrorSeverity;
  public readonly userMessage: string;
  public readonly recoverable: boolean;
  public readonly retryable: boolean;
  public readonly context?: {
    component?: string;
    feature?: string;
    operation?: string;
    userId?: string;
    sessionId?: string;
    metadata?: Record<string, unknown>;
  };

  constructor(
    message: string,
    apiErrorType: APIErrorType,
    code: string,
    severity: ErrorSeverity = 'medium',
    statusCode?: number,
    details?: Record<string, unknown>,
    requestId?: string
  ) {
    super(message);
    this.name = 'APIError';
    this.id = `api_error_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
    this.code = code;
    this.type = this.mapAPIErrorTypeToStandardType(apiErrorType);
    this.timestamp = new Date();
    this.severity = severity;
    this.userMessage = this.generateUserMessage();
    this.recoverable = this.isRecoverable();
    this.retryable = this.isRetryable();

    // Only set optional properties if they have values
    if (statusCode !== undefined) {
      this.statusCode = statusCode;
    }
    if (details !== undefined) {
      this.details = details;
    }
    if (requestId !== undefined) {
      this.requestId = requestId;
    }

    // Maintain proper stack trace
    if ((Error as any).captureStackTrace) {
      (Error as any).captureStackTrace(this, APIErrorClass);
    }
  }

  private mapAPIErrorTypeToStandardType(apiErrorType: APIErrorType): ErrorType {
    switch (apiErrorType) {
      case APIErrorType.NETWORK_ERROR:
        return ErrorType.NETWORK_ERROR;
      case APIErrorType.TIMEOUT_ERROR:
        return ErrorType.TIMEOUT_ERROR;
      case APIErrorType.AUTHENTICATION_ERROR:
        return ErrorType.AUTHENTICATION_ERROR;
      case APIErrorType.AUTHORIZATION_ERROR:
        return ErrorType.AUTHORIZATION_ERROR;
      case APIErrorType.VALIDATION_ERROR:
        return ErrorType.VALIDATION_ERROR;
      case APIErrorType.NOT_FOUND_ERROR:
        return ErrorType.NOT_FOUND_ERROR;
      case APIErrorType.RATE_LIMIT_ERROR:
        return ErrorType.RATE_LIMIT_ERROR;
      case APIErrorType.SERVER_ERROR:
        return ErrorType.SERVER_ERROR;
      default:
        return ErrorType.UNKNOWN_ERROR;
    }
  }

  private generateUserMessage(): string {
    switch (this.type) {
      case ErrorType.NETWORK_ERROR:
        return 'Unable to connect to the server. Please check your internet connection and try again.';
      case ErrorType.TIMEOUT_ERROR:
        return 'The request is taking longer than expected. Please try again.';
      case ErrorType.AUTHENTICATION_ERROR:
        return 'Please sign in to continue.';
      case ErrorType.AUTHORIZATION_ERROR:
        return 'You don\'t have permission to perform this action.';
      case ErrorType.VALIDATION_ERROR:
        return 'Please check your input and try again.';
      case ErrorType.NOT_FOUND_ERROR:
        return 'The requested resource could not be found.';
      case ErrorType.RATE_LIMIT_ERROR:
        return 'Too many requests. Please wait a moment and try again.';
      case ErrorType.SERVER_ERROR:
        return 'A server error occurred. Our team has been notified.';
      default:
        return 'Something went wrong. Please try again or contact support if the problem persists.';
    }
  }

  private isRecoverable(): boolean {
    return [
      ErrorType.VALIDATION_ERROR,
      ErrorType.AUTHENTICATION_ERROR,
    ].includes(this.type);
  }

  private isRetryable(): boolean {
    return [
      ErrorType.NETWORK_ERROR,
      ErrorType.TIMEOUT_ERROR,
      ErrorType.RATE_LIMIT_ERROR,
      ErrorType.SERVER_ERROR,
    ].includes(this.type);
  }

  toJSON(): Omit<APIError, 'type'> & { type: ErrorType } {
    const result: Omit<APIError, 'type'> & { type: ErrorType } = {
      code: this.code,
      message: this.message,
      timestamp: this.timestamp,
      type: this.type,
      severity: this.severity,
    };

    // Only add optional properties if they exist
    if (this.details !== undefined) {
      result.details = this.details;
    }
    if (this.stack !== undefined) {
      result.stack = this.stack;
    }
    if (this.requestId !== undefined) {
      result.requestId = this.requestId;
    }
    if (this.statusCode !== undefined) {
      result.statusCode = this.statusCode;
    }

    return result;
  }
}

// Enhanced error factory functions
export const createAPIError = {
  network: (message = 'Network connection failed', details?: NetworkErrorDetails): APIErrorClass =>
    new APIErrorClass(message, APIErrorType.NETWORK_ERROR, 'NETWORK_ERROR', 'medium', undefined, details),

  timeout: (message = 'Request timed out'): APIErrorClass =>
    new APIErrorClass(message, APIErrorType.TIMEOUT_ERROR, 'TIMEOUT_ERROR', 'medium'),

  authentication: (message = 'Authentication required', details?: AuthenticationErrorDetails): APIErrorClass =>
    new APIErrorClass(message, APIErrorType.AUTHENTICATION_ERROR, 'AUTH_REQUIRED', 'high', 401, details),

  authorization: (message = 'Access denied', details?: AuthorizationErrorDetails): APIErrorClass =>
    new APIErrorClass(message, APIErrorType.AUTHORIZATION_ERROR, 'ACCESS_DENIED', 'high', 403, details),

  validation: (message = 'Invalid request data', details?: ValidationErrorDetails[]): APIErrorClass =>
    new APIErrorClass(message, APIErrorType.VALIDATION_ERROR, 'VALIDATION_ERROR', 'low', 400, { validationErrors: details }),

  notFound: (resource = 'Resource', message?: string): APIErrorClass =>
    new APIErrorClass(
      message || `${resource} not found`,
      APIErrorType.NOT_FOUND_ERROR,
      'NOT_FOUND',
      'medium',
      404
    ),

  rateLimit: (message = 'Too many requests'): APIErrorClass =>
    new APIErrorClass(message, APIErrorType.RATE_LIMIT_ERROR, 'RATE_LIMIT', 'medium', 429),

  server: (message = 'Internal server error', statusCode = 500, details?: ServerErrorDetails): APIErrorClass =>
    new APIErrorClass(message, APIErrorType.SERVER_ERROR, 'SERVER_ERROR', statusCode >= 500 ? 'high' : 'medium', statusCode, details),

  unknown: (message = 'An unexpected error occurred'): APIErrorClass =>
    new APIErrorClass(message, APIErrorType.UNKNOWN_ERROR, 'UNKNOWN_ERROR', 'high'),
};

// Response parser with error handling
export async function parseAPIResponse<T>(response: Response): Promise<APIResponse<T>> {
  const requestId = response.headers.get('x-request-id') || undefined;

  try {
    // Check if response is ok
    if (!response.ok) {
      let errorData: { message?: string; code?: string; details?: Record<string, unknown> } = {};
      
      try {
        errorData = await response.json();
      } catch {
        // If JSON parsing fails, use status text
        errorData = { message: response.statusText };
      }

      const error = createErrorFromStatus(
        response.status,
        errorData.message || response.statusText,
        errorData.code,
        errorData.details,
        requestId
      );

      throw error;
    }

    // Parse successful response
    const data = await response.json();
    
    return {
      data,
      success: true,
      timestamp: new Date(),
    };
  } catch (error) {
    if (error instanceof APIErrorClass) {
      throw error;
    }

    // Handle JSON parsing errors or other unexpected errors
    throw createAPIError.unknown(`Failed to parse response: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

// Create error from HTTP status code
function createErrorFromStatus(
  status: number,
  message: string,
  code?: string,
  details?: Record<string, unknown>,
  requestId?: string
): APIErrorClass {
  const severity: ErrorSeverity = status >= 500 ? 'high' : status >= 400 ? 'medium' : 'low';
  
  switch (status) {
    case 400:
      return new APIErrorClass(message, APIErrorType.VALIDATION_ERROR, code || 'BAD_REQUEST', 'low', status, details, requestId);
    case 401:
      return new APIErrorClass(message, APIErrorType.AUTHENTICATION_ERROR, code || 'UNAUTHORIZED', 'high', status, details, requestId);
    case 403:
      return new APIErrorClass(message, APIErrorType.AUTHORIZATION_ERROR, code || 'FORBIDDEN', 'high', status, details, requestId);
    case 404:
      return new APIErrorClass(message, APIErrorType.NOT_FOUND_ERROR, code || 'NOT_FOUND', 'medium', status, details, requestId);
    case 429:
      return new APIErrorClass(message, APIErrorType.RATE_LIMIT_ERROR, code || 'RATE_LIMIT', 'medium', status, details, requestId);
    case 500:
    case 502:
    case 503:
    case 504:
      return new APIErrorClass(message, APIErrorType.SERVER_ERROR, code || 'SERVER_ERROR', 'high', status, details, requestId);
    default:
      return new APIErrorClass(message, APIErrorType.UNKNOWN_ERROR, code || 'UNKNOWN_ERROR', severity, status, details, requestId);
  }
}

// Enhanced fetch wrapper with error handling
export async function apiRequest<T>(
  url: string,
  options: RequestInit & { timeout?: number } = {}
): Promise<APIResponse<T>> {
  const { timeout = 30000, ...fetchOptions } = options;
  const requestId = `req_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;

  // Add request ID header
  const headers = new Headers(fetchOptions.headers);
  headers.set('x-request-id', requestId);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    return await parseAPIResponse<T>(response);
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof APIErrorClass) {
        // Report API error to tracking service
      errorTrackingService.reportError({
        error_type: error.type,
        error_message: error.message,
        stack_trace: error.stack || '',
        severity: error.severity,
        category: 'integration',
        feature_name: 'api_request',
        operation: 'fetch',
        context_data: {
          url,
          method: fetchOptions.method || 'GET',
          statusCode: error.statusCode,
          errorType: error.type,
          errorId: error.id,
          requestId,
          recoverable: error.recoverable,
          retryable: error.retryable,
        },
      });

      throw error;
    }

    // Handle network errors
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        const timeoutError = createAPIError.timeout(`Request to ${url} timed out after ${timeout}ms`);
        errorTrackingService.reportError({
          error_type: timeoutError.type,
          error_message: timeoutError.message,
          stack_trace: timeoutError.stack || '',
          severity: timeoutError.severity,
          category: 'integration',
          feature_name: 'api_request',
          operation: 'timeout',
          context_data: { 
            url, 
            timeout, 
            requestId,
            errorId: timeoutError.id,
          },
        });
        throw timeoutError;
      }

      const networkError = createAPIError.network(`Network error: ${error.message}`, {
        url,
        method: fetchOptions.method || 'GET',
        timeout: error.name === 'AbortError',
      });
      errorTrackingService.reportError({
        error_type: networkError.type,
        error_message: networkError.message,
        stack_trace: networkError.stack || '',
        severity: networkError.severity,
        category: 'integration',
        feature_name: 'api_request',
        operation: 'network',
        context_data: { 
          url, 
          originalError: error.message, 
          requestId,
          errorId: networkError.id,
        },
      });
      throw networkError;
    }

    // Fallback for unknown errors
    const unknownError = createAPIError.unknown('An unexpected error occurred during the request');
    errorTrackingService.reportError({
      error_type: unknownError.type,
      error_message: unknownError.message,
      stack_trace: unknownError.stack || '',
      severity: unknownError.severity,
      category: 'integration',
      feature_name: 'api_request',
      operation: 'unknown',
      context_data: { 
        url, 
        requestId,
        errorId: unknownError.id,
      },
    });
    throw unknownError;
  }
}

// Error handler for React components
export function handleAPIError(error: unknown, context?: string): APIErrorClass {
  if (error instanceof APIErrorClass) {
    return error;
  }

  if (error instanceof Error) {
    const apiError = createAPIError.unknown(error.message);
    
    errorTrackingService.reportError({
      error_type: apiError.type,
      error_message: apiError.message,
      stack_trace: apiError.stack || '',
      severity: apiError.severity,
      category: 'application',
      feature_name: context || 'component',
      operation: 'error_handling',
      context_data: {
        originalError: error.message,
        originalStack: error.stack,
        errorId: apiError.id,
      },
    });

    return apiError;
  }

  const unknownError = createAPIError.unknown('An unknown error occurred');
  errorTrackingService.reportError({
    error_type: unknownError.type,
    error_message: unknownError.message,
    stack_trace: unknownError.stack || '',
    severity: unknownError.severity,
    category: 'application',
    feature_name: context || 'component',
    operation: 'unknown_error',
    context_data: { 
      error: String(error),
      errorId: unknownError.id,
    },
  });

  return unknownError;
}

// User-friendly error messages (now using the userMessage property)
export function getErrorMessage(error: APIErrorClass): string {
  return error.userMessage;
}

// Error notification helper (now using standardized types)
export function createErrorNotification(
  error: APIErrorClass,
  options: Partial<{
    title: string;
    description: string;
    duration: number;
  }> = {}
): {
  id: string;
  title: string;
  message: string;
  type: 'error' | 'warning' | 'info';
  duration: number;
  dismissible: boolean;
} {
  return {
    id: `notification_${error.id}`,
    title: options.title || 'Error',
    message: options.description || error.userMessage,
    type: error.severity === 'critical' || error.severity === 'high' ? 'error' : 'warning',
    duration: options.duration || (error.severity === 'critical' ? 0 : 5000),
    dismissible: true,
  };
}