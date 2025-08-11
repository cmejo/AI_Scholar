import { AlertTriangle, Bug, CheckCircle, RefreshCw, Wifi, WifiOff } from 'lucide-react';
import React, { useState } from 'react';
import { useAsyncErrorHandler, useErrorHandler, useFormErrorHandler, useRetryHandler } from '../hooks/useErrorHandler';
import type { StandardError } from '../types/ui';
import { createAPIError } from '../utils/apiErrorHandler';
import { createError } from '../utils/errorFactory';
import { ErrorBoundary } from './ErrorBoundary';

// Component that demonstrates various error scenarios
const ErrorTriggerComponent: React.FC = () => {
  const { handleError } = useErrorHandler({ context: 'error_demo' });
  const { execute, loading, error, clearError } = useAsyncErrorHandler({ context: 'async_demo' });
  const { executeWithRetry, retryCount, isRetrying } = useRetryHandler({
    maxRetries: 3,
    retryDelay: 1000,
    backoffMultiplier: 2,
  });
  const { fieldErrors, setFieldError, clearFieldError, hasErrors, handleValidationError } = useFormErrorHandler();

  const [lastError, setLastError] = useState<StandardError | null>(null);
  const [successMessage, setSuccessMessage] = useState<string>('');

  // Simulate different types of errors
  const triggerComponentError = () => {
    try {
      const error = createError.component(
        'Simulated component error',
        {
          component: 'ErrorTriggerComponent',
          operation: 'button_click',
          userId: 'demo_user',
        },
        {
          buttonId: 'component_error_btn',
          timestamp: new Date().toISOString(),
        }
      );
      setLastError(error);
      handleError(error, 'component_error_trigger');
    } catch (err) {
      console.error('Error in triggerComponentError:', err);
    }
  };

  const triggerNetworkError = () => {
    const error = createAPIError.network('Failed to connect to server', {
      url: 'https://api.example.com/data',
      method: 'GET',
      timeout: true,
    });
    setLastError(error);
    handleError(error, 'network_error_trigger');
  };

  const triggerValidationError = () => {
    const error = createError.validation(
      'Form validation failed',
      [
        { field: 'email', message: 'Invalid email format', code: 'INVALID_EMAIL', value: 'invalid-email' },
        { field: 'password', message: 'Password too short', code: 'PASSWORD_TOO_SHORT', value: '123' },
      ],
      {
        component: 'ErrorTriggerComponent',
        operation: 'form_validation',
      }
    );
    setLastError(error);
    handleValidationError(error);
  };

  const triggerAuthenticationError = () => {
    const error = createAPIError.authentication('Session expired', {
      reason: 'expired_token',
      redirectUrl: '/login',
    });
    setLastError(error);
    handleError(error, 'auth_error_trigger');
  };

  const triggerServerError = () => {
    const error = createAPIError.server('Internal server error', 500, {
      errorId: 'srv_err_001',
      service: 'user_service',
      operation: 'get_user_profile',
    });
    setLastError(error);
    handleError(error, 'server_error_trigger');
  };

  const simulateAsyncOperation = async () => {
    const result = await execute(async () => {
      // Simulate async operation that might fail
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      if (Math.random() > 0.5) {
        throw createAPIError.timeout('Async operation timed out');
      }
      
      return 'Async operation completed successfully!';
    });

    if (result) {
      setSuccessMessage(result);
      setTimeout(() => setSuccessMessage(''), 3000);
    }
  };

  const simulateRetryOperation = async () => {
    try {
      const result = await executeWithRetry(async () => {
        // Simulate operation that fails a few times then succeeds
        if (retryCount < 2) {
          throw createAPIError.network('Network temporarily unavailable');
        }
        return 'Retry operation succeeded!';
      });
      
      setSuccessMessage(result);
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      const standardError = handleError(err, 'retry_operation_failed');
      setLastError(standardError);
    }
  };

  const clearAllErrors = () => {
    setLastError(null);
    clearError();
    clearFieldError('email');
    clearFieldError('password');
    setSuccessMessage('');
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
          <Bug className="w-5 h-5 mr-2" />
          Type-Safe Error Handling Demo
        </h2>
        
        <p className="text-gray-300 mb-6">
          This demo showcases the comprehensive type-safe error handling system with proper TypeScript interfaces,
          standardized error types, and user-friendly error reporting.
        </p>

        {/* Error Trigger Buttons */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
          <button
            onClick={triggerComponentError}
            className="flex items-center justify-center space-x-2 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <AlertTriangle className="w-4 h-4" />
            <span>Component Error</span>
          </button>

          <button
            onClick={triggerNetworkError}
            className="flex items-center justify-center space-x-2 bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <WifiOff className="w-4 h-4" />
            <span>Network Error</span>
          </button>

          <button
            onClick={triggerValidationError}
            className="flex items-center justify-center space-x-2 bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <AlertTriangle className="w-4 h-4" />
            <span>Validation Error</span>
          </button>

          <button
            onClick={triggerAuthenticationError}
            className="flex items-center justify-center space-x-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <AlertTriangle className="w-4 h-4" />
            <span>Auth Error</span>
          </button>

          <button
            onClick={triggerServerError}
            className="flex items-center justify-center space-x-2 bg-red-700 hover:bg-red-800 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <AlertTriangle className="w-4 h-4" />
            <span>Server Error</span>
          </button>

          <button
            onClick={simulateAsyncOperation}
            disabled={loading}
            className="flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-lg transition-colors"
          >
            {loading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Wifi className="w-4 h-4" />
            )}
            <span>Async Operation</span>
          </button>
        </div>

        {/* Retry Operation */}
        <div className="mb-6">
          <button
            onClick={simulateRetryOperation}
            disabled={isRetrying}
            className="flex items-center justify-center space-x-2 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-4 py-2 rounded-lg transition-colors"
          >
            {isRetrying ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            <span>
              Retry Operation {retryCount > 0 && `(Attempt ${retryCount + 1})`}
            </span>
          </button>
        </div>

        {/* Clear Errors Button */}
        <button
          onClick={clearAllErrors}
          className="flex items-center justify-center space-x-2 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors mb-6"
        >
          <CheckCircle className="w-4 h-4" />
          <span>Clear All Errors</span>
        </button>

        {/* Success Message */}
        {successMessage && (
          <div className="bg-green-600 text-white p-4 rounded-lg mb-4 flex items-center">
            <CheckCircle className="w-5 h-5 mr-2" />
            {successMessage}
          </div>
        )}

        {/* Error Display */}
        {(lastError || error) && (
          <div className="bg-red-600 text-white p-4 rounded-lg mb-4">
            <h3 className="font-semibold mb-2">Error Details:</h3>
            {lastError && (
              <div className="space-y-1 text-sm">
                <p><strong>ID:</strong> {lastError.id}</p>
                <p><strong>Type:</strong> {lastError.type}</p>
                <p><strong>Code:</strong> {lastError.code}</p>
                <p><strong>Message:</strong> {lastError.message}</p>
                <p><strong>User Message:</strong> {lastError.userMessage}</p>
                <p><strong>Severity:</strong> {lastError.severity}</p>
                <p><strong>Recoverable:</strong> {lastError.recoverable ? 'Yes' : 'No'}</p>
                <p><strong>Retryable:</strong> {lastError.retryable ? 'Yes' : 'No'}</p>
                <p><strong>Timestamp:</strong> {lastError.timestamp.toISOString()}</p>
              </div>
            )}
            {error && (
              <div className="space-y-1 text-sm">
                <p><strong>Async Error:</strong> {error.message}</p>
                <p><strong>Type:</strong> {error.type}</p>
                <p><strong>Severity:</strong> {error.severity}</p>
              </div>
            )}
          </div>
        )}

        {/* Form Errors Display */}
        {hasErrors && (
          <div className="bg-yellow-600 text-white p-4 rounded-lg mb-4">
            <h3 className="font-semibold mb-2">Form Validation Errors:</h3>
            <div className="space-y-2">
              {Object.entries(fieldErrors).map(([field, fieldError]) => (
                <div key={field} className="flex items-center justify-between">
                  <span className="text-sm">
                    <strong>{fieldError.field}:</strong> {fieldError.message}
                  </span>
                  <button
                    onClick={() => clearFieldError(field)}
                    className="text-xs bg-yellow-700 hover:bg-yellow-800 px-2 py-1 rounded"
                  >
                    Clear
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error Handling Features */}
        <div className="bg-gray-700 rounded-lg p-4">
          <h3 className="font-semibold text-white mb-3">Error Handling Features:</h3>
          <ul className="text-gray-300 text-sm space-y-1">
            <li>✅ Type-safe error interfaces with proper TypeScript support</li>
            <li>✅ Standardized error types and severity levels</li>
            <li>✅ User-friendly error messages</li>
            <li>✅ Automatic error reporting and tracking</li>
            <li>✅ React Error Boundaries with retry functionality</li>
            <li>✅ Form validation error handling</li>
            <li>✅ Async operation error handling</li>
            <li>✅ Retry mechanisms with exponential backoff</li>
            <li>✅ Context-aware error reporting</li>
            <li>✅ Error deduplication and rate limiting</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

// Component that will throw an error to test Error Boundary
const ErrorThrowingComponent: React.FC<{ shouldThrow: boolean }> = ({ shouldThrow }) => {
  if (shouldThrow) {
    throw new Error('This is a test error thrown by ErrorThrowingComponent');
  }
  
  return (
    <div className="bg-green-600 text-white p-4 rounded-lg">
      <CheckCircle className="w-5 h-5 inline mr-2" />
      Component is working correctly!
    </div>
  );
};

// Main demo component with Error Boundary
export const ErrorHandlingDemo: React.FC = () => {
  const [shouldThrowError, setShouldThrowError] = useState(false);

  return (
    <div className="min-h-screen bg-gray-900 py-8">
      <ErrorTriggerComponent />
      
      {/* Error Boundary Demo */}
      <div className="max-w-4xl mx-auto p-6 mt-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2" />
            Error Boundary Demo
          </h2>
          
          <div className="mb-4">
            <button
              onClick={() => setShouldThrowError(!shouldThrowError)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                shouldThrowError
                  ? 'bg-green-600 hover:bg-green-700 text-white'
                  : 'bg-red-600 hover:bg-red-700 text-white'
              }`}
            >
              {shouldThrowError ? 'Fix Component' : 'Break Component'}
            </button>
          </div>

          <ErrorBoundary
            maxRetries={3}
            onError={(error, errorInfo) => {
              console.log('Error caught by boundary:', error, errorInfo);
            }}
          >
            <ErrorThrowingComponent shouldThrow={shouldThrowError} />
          </ErrorBoundary>
        </div>
      </div>
    </div>
  );
};

export default ErrorHandlingDemo;