/**
 * Standardized Error Factory
 * Creates type-safe error objects with consistent structure
 */

import type { APIErrorType } from '../types/api';
import type {
    AuthenticationErrorDetails,
    AuthorizationErrorDetails,
    ErrorContext,
    ErrorSeverity,
    FormError,
    NetworkErrorDetails,
    ServerErrorDetails,
    StandardError,
    ValidationErrorDetails
} from '../types/ui';
import { ErrorType } from '../types/ui';

// Error ID generator
function generateErrorId(): string {
  return `error_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
}

// Base error factory
function createBaseError(
  type: ErrorType,
  code: string,
  message: string,
  severity: ErrorSeverity,
  options: {
    stack?: string;
    context?: ErrorContext;
    details?: Record<string, unknown>;
    recoverable?: boolean;
    retryable?: boolean;
  } = {}
): StandardError {
  const {
    stack,
    context,
    details,
    recoverable = false,
    retryable = false
  } = options;

  const error: StandardError = {
    id: generateErrorId(),
    type,
    code,
    message,
    severity,
    timestamp: new Date(),
    userMessage: getUserFriendlyMessage(type, code, message),
    recoverable,
    retryable,
  };

  // Only add optional properties if they have values
  if (stack) {
    error.stack = stack;
  }
  if (context) {
    error.context = context;
  }
  if (details) {
    error.details = details;
  }

  return error;
}

// User-friendly message generator
function getUserFriendlyMessage(type: ErrorType, code: string, message: string): string {
  switch (type) {
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
    case ErrorType.COMPONENT_ERROR:
      return 'Something went wrong with this component. Please try refreshing the page.';
    default:
      return 'Something went wrong. Please try again or contact support if the problem persists.';
  }
}

// Specific error factories
export const createError = {
  // Component errors
  component: (
    message: string,
    context?: ErrorContext,
    details?: Record<string, unknown>
  ): StandardError => {
    const options: Parameters<typeof createBaseError>[4] = { recoverable: true };
    if (context) options.context = context;
    if (details) options.details = details;
    return createBaseError(ErrorType.COMPONENT_ERROR, 'COMPONENT_ERROR', message, 'medium', options);
  },

  // Network errors
  network: (
    message: string,
    details?: NetworkErrorDetails,
    context?: ErrorContext
  ): StandardError => {
    const options: Parameters<typeof createBaseError>[4] = { retryable: true };
    if (context) options.context = context;
    if (details) options.details = details as Record<string, unknown>;
    return createBaseError(ErrorType.NETWORK_ERROR, 'NETWORK_ERROR', message, 'medium', options);
  },

  // Timeout errors
  timeout: (
    message: string = 'Request timed out',
    context?: ErrorContext
  ): StandardError => {
    const options: Parameters<typeof createBaseError>[4] = { retryable: true };
    if (context) options.context = context;
    return createBaseError(ErrorType.TIMEOUT_ERROR, 'TIMEOUT_ERROR', message, 'medium', options);
  },

  // Authentication errors
  authentication: (
    message: string,
    details?: AuthenticationErrorDetails,
    context?: ErrorContext
  ): StandardError => {
    const options: Parameters<typeof createBaseError>[4] = { recoverable: true };
    if (context) options.context = context;
    if (details) options.details = details as Record<string, unknown>;
    return createBaseError(ErrorType.AUTHENTICATION_ERROR, 'AUTH_REQUIRED', message, 'high', options);
  },

  // Authorization errors
  authorization: (
    message: string,
    details?: AuthorizationErrorDetails,
    context?: ErrorContext
  ): StandardError => {
    const options: Parameters<typeof createBaseError>[4] = {};
    if (context) options.context = context;
    if (details) options.details = details as Record<string, unknown>;
    return createBaseError(ErrorType.AUTHORIZATION_ERROR, 'ACCESS_DENIED', message, 'high', options);
  },

  // Validation errors
  validation: (
    message: string,
    details?: ValidationErrorDetails | ValidationErrorDetails[],
    context?: ErrorContext
  ): StandardError => {
    const options: Parameters<typeof createBaseError>[4] = { recoverable: true };
    if (context) options.context = context;
    if (details) options.details = Array.isArray(details) ? { validationErrors: details } : details as Record<string, unknown>;
    return createBaseError(ErrorType.VALIDATION_ERROR, 'VALIDATION_ERROR', message, 'low', options);
  },

  // Not found errors
  notFound: (
    resource: string = 'Resource',
    context?: ErrorContext
  ): StandardError => {
    const options: Parameters<typeof createBaseError>[4] = {};
    if (context) options.context = context;
    return createBaseError(ErrorType.NOT_FOUND_ERROR, 'NOT_FOUND', `${resource} not found`, 'medium', options);
  },

  // Rate limit errors
  rateLimit: (
    message: string = 'Too many requests',
    context?: ErrorContext
  ): StandardError => {
    const options: Parameters<typeof createBaseError>[4] = { retryable: true };
    if (context) options.context = context;
    return createBaseError(ErrorType.RATE_LIMIT_ERROR, 'RATE_LIMIT', message, 'medium', options);
  },

  // Server errors
  server: (
    message: string,
    details?: ServerErrorDetails,
    context?: ErrorContext
  ): StandardError => {
    const options: Parameters<typeof createBaseError>[4] = { retryable: true };
    if (context) options.context = context;
    if (details) options.details = details as Record<string, unknown>;
    return createBaseError(ErrorType.SERVER_ERROR, 'SERVER_ERROR', message, 'high', options);
  },

  // Unknown errors
  unknown: (
    message: string = 'An unexpected error occurred',
    context?: ErrorContext,
    originalError?: Error
  ): StandardError => {
    const options: Parameters<typeof createBaseError>[4] = {};
    if (context) options.context = context;
    if (originalError?.stack) options.stack = originalError.stack;
    if (originalError) options.details = { originalMessage: originalError.message };
    return createBaseError(ErrorType.UNKNOWN_ERROR, 'UNKNOWN_ERROR', message, 'high', options);
  },
};

// Error conversion utilities
export function convertAPIErrorToStandard(apiError: any): StandardError {
  // Handle APIErrorClass instances
  if (apiError && typeof apiError === 'object' && 'type' in apiError) {
    const errorType = mapAPIErrorTypeToStandardType(apiError.type);
    return createBaseError(
      errorType,
      apiError.code || 'API_ERROR',
      apiError.message || 'API request failed',
      apiError.severity || 'medium',
      {
        stack: apiError.stack,
        details: apiError.details,
        recoverable: isRecoverable(errorType),
        retryable: isRetryable(errorType),
      }
    );
  }

  // Handle standard Error objects
  if (apiError instanceof Error) {
    return createError.unknown(apiError.message, undefined, apiError);
  }

  // Handle unknown error types
  return createError.unknown(String(apiError));
}

function mapAPIErrorTypeToStandardType(apiErrorType: APIErrorType): ErrorType {
  switch (apiErrorType) {
    case 'NETWORK_ERROR':
      return ErrorType.NETWORK_ERROR;
    case 'TIMEOUT_ERROR':
      return ErrorType.TIMEOUT_ERROR;
    case 'AUTHENTICATION_ERROR':
      return ErrorType.AUTHENTICATION_ERROR;
    case 'AUTHORIZATION_ERROR':
      return ErrorType.AUTHORIZATION_ERROR;
    case 'VALIDATION_ERROR':
      return ErrorType.VALIDATION_ERROR;
    case 'NOT_FOUND_ERROR':
      return ErrorType.NOT_FOUND_ERROR;
    case 'RATE_LIMIT_ERROR':
      return ErrorType.RATE_LIMIT_ERROR;
    case 'SERVER_ERROR':
      return ErrorType.SERVER_ERROR;
    default:
      return ErrorType.UNKNOWN_ERROR;
  }
}

function isRecoverable(errorType: ErrorType): boolean {
  return [
    ErrorType.COMPONENT_ERROR,
    ErrorType.VALIDATION_ERROR,
    ErrorType.AUTHENTICATION_ERROR,
  ].includes(errorType);
}

function isRetryable(errorType: ErrorType): boolean {
  return [
    ErrorType.NETWORK_ERROR,
    ErrorType.TIMEOUT_ERROR,
    ErrorType.RATE_LIMIT_ERROR,
    ErrorType.SERVER_ERROR,
  ].includes(errorType);
}

// Form error utilities
export function createFormError(
  field: string,
  message: string,
  code: string,
  value?: unknown
): FormError {
  return {
    field,
    message,
    code,
    value,
  };
}

export function createFormErrors(
  validationErrors: ValidationErrorDetails[]
): Record<string, FormError> {
  return validationErrors.reduce((acc, error) => {
    acc[error.field] = createFormError(
      error.field,
      error.message,
      error.code,
      error.value
    );
    return acc;
  }, {} as Record<string, FormError>);
}

// Error comparison utilities
export function isSameError(error1: StandardError, error2: StandardError): boolean {
  return (
    error1.type === error2.type &&
    error1.code === error2.code &&
    error1.message === error2.message
  );
}

export function isErrorType(error: StandardError, type: ErrorType): boolean {
  return error.type === type;
}

export function isErrorSeverity(error: StandardError, severity: ErrorSeverity): boolean {
  return error.severity === severity;
}

// Error serialization
export function serializeError(error: StandardError): string {
  return JSON.stringify({
    id: error.id,
    type: error.type,
    code: error.code,
    message: error.message,
    severity: error.severity,
    timestamp: error.timestamp.toISOString(),
    context: error.context,
    details: error.details,
    userMessage: error.userMessage,
    recoverable: error.recoverable,
    retryable: error.retryable,
  });
}

export function deserializeError(serializedError: string): StandardError {
  const parsed = JSON.parse(serializedError);
  return {
    ...parsed,
    timestamp: new Date(parsed.timestamp),
  };
}