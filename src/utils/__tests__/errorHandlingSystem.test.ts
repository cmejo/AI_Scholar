/**
 * Comprehensive test suite for the type-safe error handling system
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { StandardError } from '../../types/ui';
import { ErrorType } from '../../types/ui';
import { APIErrorClass, createAPIError } from '../apiErrorHandler';
import { createError } from '../errorFactory';
import { globalErrorHandler } from '../globalErrorHandler';

describe('Type-Safe Error Handling System', () => {
  beforeEach(() => {
    // Clear any existing error state
    globalErrorHandler.clearErrorCache();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('StandardError Interface Compliance', () => {
    it('should create errors with all required StandardError properties', () => {
      const error = createError.component('Test error');
      
      // Check all required properties exist
      expect(error).toHaveProperty('id');
      expect(error).toHaveProperty('type');
      expect(error).toHaveProperty('code');
      expect(error).toHaveProperty('message');
      expect(error).toHaveProperty('severity');
      expect(error).toHaveProperty('timestamp');
      expect(error).toHaveProperty('userMessage');
      expect(error).toHaveProperty('recoverable');
      expect(error).toHaveProperty('retryable');
      
      // Check property types
      expect(typeof error.id).toBe('string');
      expect(typeof error.type).toBe('string');
      expect(typeof error.code).toBe('string');
      expect(typeof error.message).toBe('string');
      expect(typeof error.severity).toBe('string');
      expect(error.timestamp).toBeInstanceOf(Date);
      expect(typeof error.userMessage).toBe('string');
      expect(typeof error.recoverable).toBe('boolean');
      expect(typeof error.retryable).toBe('boolean');
    });

    it('should generate unique error IDs', () => {
      const error1 = createError.component('Test error 1');
      const error2 = createError.component('Test error 2');
      
      expect(error1.id).not.toBe(error2.id);
      expect(error1.id).toMatch(/^error_\d+_[a-z0-9]+$/);
      expect(error2.id).toMatch(/^error_\d+_[a-z0-9]+$/);
    });

    it('should set appropriate timestamps', () => {
      const beforeTime = new Date();
      const error = createError.component('Test error');
      const afterTime = new Date();
      
      expect(error.timestamp.getTime()).toBeGreaterThanOrEqual(beforeTime.getTime());
      expect(error.timestamp.getTime()).toBeLessThanOrEqual(afterTime.getTime());
    });
  });

  describe('Error Type Classification', () => {
    it('should create component errors with correct properties', () => {
      const error = createError.component('Component failed', {
        component: 'TestComponent',
        operation: 'render',
      });
      
      expect(error.type).toBe(ErrorType.COMPONENT_ERROR);
      expect(error.code).toBe('COMPONENT_ERROR');
      expect(error.severity).toBe('medium');
      expect(error.recoverable).toBe(true);
      expect(error.retryable).toBe(false);
      expect(error.context?.component).toBe('TestComponent');
      expect(error.context?.operation).toBe('render');
    });

    it('should create network errors with correct properties', () => {
      const error = createError.network('Network failed', {
        url: 'https://api.example.com',
        method: 'GET',
        timeout: true,
      });
      
      expect(error.type).toBe(ErrorType.NETWORK_ERROR);
      expect(error.code).toBe('NETWORK_ERROR');
      expect(error.severity).toBe('medium');
      expect(error.recoverable).toBe(false);
      expect(error.retryable).toBe(true);
      expect(error.details).toEqual({
        url: 'https://api.example.com',
        method: 'GET',
        timeout: true,
      });
    });

    it('should create validation errors with correct properties', () => {
      const validationDetails = [
        { field: 'email', message: 'Invalid email', code: 'INVALID_EMAIL' },
        { field: 'password', message: 'Too short', code: 'PASSWORD_TOO_SHORT' },
      ];
      
      const error = createError.validation('Validation failed', validationDetails);
      
      expect(error.type).toBe(ErrorType.VALIDATION_ERROR);
      expect(error.code).toBe('VALIDATION_ERROR');
      expect(error.severity).toBe('low');
      expect(error.recoverable).toBe(true);
      expect(error.retryable).toBe(false);
      expect(error.details).toEqual({ validationErrors: validationDetails });
    });

    it('should create authentication errors with correct properties', () => {
      const error = createError.authentication('Auth required', {
        reason: 'expired_token',
        redirectUrl: '/login',
      });
      
      expect(error.type).toBe(ErrorType.AUTHENTICATION_ERROR);
      expect(error.code).toBe('AUTH_REQUIRED');
      expect(error.severity).toBe('high');
      expect(error.recoverable).toBe(true);
      expect(error.retryable).toBe(false);
      expect(error.details).toEqual({
        reason: 'expired_token',
        redirectUrl: '/login',
      });
    });

    it('should create server errors with correct properties', () => {
      const error = createError.server('Server error', {
        errorId: 'srv_001',
        service: 'user_service',
        operation: 'get_user',
      });
      
      expect(error.type).toBe(ErrorType.SERVER_ERROR);
      expect(error.code).toBe('SERVER_ERROR');
      expect(error.severity).toBe('high');
      expect(error.recoverable).toBe(false);
      expect(error.retryable).toBe(true);
      expect(error.details).toEqual({
        errorId: 'srv_001',
        service: 'user_service',
        operation: 'get_user',
      });
    });
  });

  describe('API Error Integration', () => {
    it('should create API errors that implement StandardError', () => {
      const apiError = createAPIError.network('Network failed');
      
      // Should have all StandardError properties
      expect(apiError).toHaveProperty('id');
      expect(apiError).toHaveProperty('type');
      expect(apiError).toHaveProperty('code');
      expect(apiError).toHaveProperty('message');
      expect(apiError).toHaveProperty('severity');
      expect(apiError).toHaveProperty('timestamp');
      expect(apiError).toHaveProperty('userMessage');
      expect(apiError).toHaveProperty('recoverable');
      expect(apiError).toHaveProperty('retryable');
      
      // Should also have API-specific properties (may be undefined for some error types)
      expect(apiError.statusCode).toBeUndefined(); // Network errors don't have status codes
      expect(apiError.requestId).toBeUndefined(); // Network errors don't have request IDs
      
      // Test with an API error that has these properties
      const serverError = createAPIError.server('Server error', 500);
      expect(serverError.statusCode).toBe(500);
      expect(serverError.requestId).toBeUndefined(); // Still undefined unless explicitly set
    });

    it('should convert API errors to standard errors correctly', () => {
      const apiError = createAPIError.validation('Invalid data', [
        { field: 'name', message: 'Required', code: 'REQUIRED' },
      ]);
      
      expect(apiError.type).toBe(ErrorType.VALIDATION_ERROR);
      expect(apiError.userMessage).toBe('Please check your input and try again.');
      expect(apiError.recoverable).toBe(true);
      expect(apiError.retryable).toBe(false);
    });

    it('should handle different HTTP status codes correctly', () => {
      const authError = createAPIError.authentication('Unauthorized');
      const serverError = createAPIError.server('Internal error', 500);
      const notFoundError = createAPIError.notFound('User');
      
      expect(authError.type).toBe(ErrorType.AUTHENTICATION_ERROR);
      expect(authError.severity).toBe('high');
      
      expect(serverError.type).toBe(ErrorType.SERVER_ERROR);
      expect(serverError.severity).toBe('high');
      
      expect(notFoundError.type).toBe(ErrorType.NOT_FOUND_ERROR);
      expect(notFoundError.severity).toBe('medium');
    });
  });

  describe('User-Friendly Messages', () => {
    it('should provide appropriate user messages for different error types', () => {
      const networkError = createError.network('Connection failed');
      const authError = createError.authentication('Token expired');
      const validationError = createError.validation('Invalid input');
      const serverError = createError.server('Database error');
      
      expect(networkError.userMessage).toBe('Unable to connect to the server. Please check your internet connection and try again.');
      expect(authError.userMessage).toBe('Please sign in to continue.');
      expect(validationError.userMessage).toBe('Please check your input and try again.');
      expect(serverError.userMessage).toBe('A server error occurred. Our team has been notified.');
    });

    it('should provide fallback message for unknown errors', () => {
      const unknownError = createError.unknown('Something weird happened');
      
      expect(unknownError.userMessage).toBe('Something went wrong. Please try again or contact support if the problem persists.');
    });
  });

  describe('Error Context and Details', () => {
    it('should preserve error context information', () => {
      const error = createError.component('Test error', {
        component: 'TestComponent',
        feature: 'user_management',
        operation: 'create_user',
        userId: 'user_123',
        sessionId: 'session_456',
        metadata: { extra: 'data' },
      });
      
      expect(error.context).toEqual({
        component: 'TestComponent',
        feature: 'user_management',
        operation: 'create_user',
        userId: 'user_123',
        sessionId: 'session_456',
        metadata: { extra: 'data' },
      });
    });

    it('should preserve error details', () => {
      const details = {
        requestId: 'req_123',
        correlationId: 'corr_456',
        additionalInfo: 'Some extra information',
      };
      
      const error = createError.component('Test error', undefined, details);
      
      expect(error.details).toEqual(details);
    });

    it('should handle optional properties correctly', () => {
      const minimalError = createError.component('Minimal error');
      
      expect(minimalError.context).toBeUndefined();
      expect(minimalError.details).toBeUndefined();
      expect(minimalError.stack).toBeUndefined();
    });
  });

  describe('Error Serialization', () => {
    it('should serialize and deserialize errors correctly', () => {
      const originalError = createError.component('Test error', {
        component: 'TestComponent',
        operation: 'test',
      }, {
        extra: 'data',
      });
      
      const serialized = JSON.stringify(originalError);
      const parsed = JSON.parse(serialized);
      
      expect(parsed.id).toBe(originalError.id);
      expect(parsed.type).toBe(originalError.type);
      expect(parsed.code).toBe(originalError.code);
      expect(parsed.message).toBe(originalError.message);
      expect(parsed.severity).toBe(originalError.severity);
      expect(parsed.userMessage).toBe(originalError.userMessage);
      expect(parsed.recoverable).toBe(originalError.recoverable);
      expect(parsed.retryable).toBe(originalError.retryable);
      expect(parsed.context).toEqual(originalError.context);
      expect(parsed.details).toEqual(originalError.details);
    });
  });

  describe('Global Error Handler Integration', () => {
    it('should handle manual error reporting', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      const testError = new Error('Test manual error');
      globalErrorHandler.reportManualError(testError, {
        component: 'test_component',
        operation: 'manual_test',
      });
      
      const stats = globalErrorHandler.getErrorStats();
      expect(stats.errorCount).toBe(1);
      expect(stats.lastErrorTime).toBeGreaterThan(0);
      
      consoleSpy.mockRestore();
    });

    it('should provide error statistics', () => {
      const stats = globalErrorHandler.getErrorStats();
      
      expect(stats).toHaveProperty('errorCount');
      expect(stats).toHaveProperty('lastErrorTime');
      expect(typeof stats.errorCount).toBe('number');
      expect(typeof stats.lastErrorTime).toBe('number');
    });

    it('should allow clearing error cache', () => {
      const testError = new Error('Test error');
      globalErrorHandler.reportManualError(testError);
      
      let stats = globalErrorHandler.getErrorStats();
      expect(stats.errorCount).toBeGreaterThan(0);
      
      globalErrorHandler.clearErrorCache();
      
      stats = globalErrorHandler.getErrorStats();
      expect(stats.errorCount).toBe(0);
      expect(stats.lastErrorTime).toBe(0);
    });
  });

  describe('Type Safety', () => {
    it('should enforce proper TypeScript types', () => {
      // This test ensures TypeScript compilation succeeds with strict types
      const error: StandardError = createError.component('Test error');
      
      // These should all be properly typed
      const id: string = error.id;
      const type: ErrorType = error.type;
      const code: string = error.code;
      const message: string = error.message;
      const severity: 'low' | 'medium' | 'high' | 'critical' = error.severity;
      const timestamp: Date = error.timestamp;
      const userMessage: string = error.userMessage;
      const recoverable: boolean = error.recoverable;
      const retryable: boolean = error.retryable;
      
      // Optional properties should be properly typed
      const stack: string | undefined = error.stack;
      const context: any = error.context;
      const details: Record<string, unknown> | undefined = error.details;
      
      // Verify the values are what we expect
      expect(typeof id).toBe('string');
      expect(Object.values(ErrorType)).toContain(type);
      expect(typeof code).toBe('string');
      expect(typeof message).toBe('string');
      expect(['low', 'medium', 'high', 'critical']).toContain(severity);
      expect(timestamp).toBeInstanceOf(Date);
      expect(typeof userMessage).toBe('string');
      expect(typeof recoverable).toBe('boolean');
      expect(typeof retryable).toBe('boolean');
    });

    it('should work with API error classes', () => {
      const apiError: APIErrorClass = createAPIError.network('Network error');
      
      // Should implement StandardError interface
      const standardError: StandardError = apiError;
      
      expect(standardError.type).toBe(ErrorType.NETWORK_ERROR);
      expect(standardError.retryable).toBe(true);
      expect(standardError.recoverable).toBe(false);
    });
  });

  describe('Error Recovery and Retry Logic', () => {
    it('should correctly identify recoverable errors', () => {
      const componentError = createError.component('Component error');
      const validationError = createError.validation('Validation error');
      const authError = createError.authentication('Auth error');
      const networkError = createError.network('Network error');
      const serverError = createError.server('Server error');
      
      expect(componentError.recoverable).toBe(true);
      expect(validationError.recoverable).toBe(true);
      expect(authError.recoverable).toBe(true);
      expect(networkError.recoverable).toBe(false);
      expect(serverError.recoverable).toBe(false);
    });

    it('should correctly identify retryable errors', () => {
      const componentError = createError.component('Component error');
      const validationError = createError.validation('Validation error');
      const networkError = createError.network('Network error');
      const timeoutError = createError.timeout('Timeout error');
      const rateLimitError = createError.rateLimit('Rate limit error');
      const serverError = createError.server('Server error');
      
      expect(componentError.retryable).toBe(false);
      expect(validationError.retryable).toBe(false);
      expect(networkError.retryable).toBe(true);
      expect(timeoutError.retryable).toBe(true);
      expect(rateLimitError.retryable).toBe(true);
      expect(serverError.retryable).toBe(true);
    });
  });
});