import { describe, expect, it } from 'vitest';
import { ErrorSeverity, ErrorType } from '../../types/ui';
import { convertAPIErrorToStandard, createError, createFormError } from '../errorFactory';

describe('errorFactory', () => {
  describe('createError', () => {
    it('should create a component error with correct properties', () => {
      const error = createError.component('Test error message');
      
      expect(error.type).toBe(ErrorType.COMPONENT_ERROR);
      expect(error.code).toBe('COMPONENT_ERROR');
      expect(error.message).toBe('Test error message');
      expect(error.severity).toBe('medium');
      expect(error.recoverable).toBe(true);
      expect(error.retryable).toBe(false);
      expect(error.id).toMatch(/^error_\d+_[a-z0-9]+$/);
      expect(error.timestamp).toBeInstanceOf(Date);
      expect(error.userMessage).toBe('Something went wrong with this component. Please try refreshing the page.');
    });

    it('should create a network error with correct properties', () => {
      const error = createError.network('Network failed');
      
      expect(error.type).toBe(ErrorType.NETWORK_ERROR);
      expect(error.code).toBe('NETWORK_ERROR');
      expect(error.message).toBe('Network failed');
      expect(error.severity).toBe('medium');
      expect(error.recoverable).toBe(false);
      expect(error.retryable).toBe(true);
      expect(error.userMessage).toBe('Unable to connect to the server. Please check your internet connection and try again.');
    });

    it('should create a validation error with correct properties', () => {
      const validationDetails = [
        { field: 'email', message: 'Invalid email', code: 'INVALID_EMAIL' }
      ];
      const error = createError.validation('Validation failed', validationDetails);
      
      expect(error.type).toBe(ErrorType.VALIDATION_ERROR);
      expect(error.code).toBe('VALIDATION_ERROR');
      expect(error.message).toBe('Validation failed');
      expect(error.severity).toBe('low');
      expect(error.recoverable).toBe(true);
      expect(error.retryable).toBe(false);
      expect(error.details).toEqual({ validationErrors: validationDetails });
    });

    it('should create an authentication error with correct properties', () => {
      const error = createError.authentication('Auth required');
      
      expect(error.type).toBe(ErrorType.AUTHENTICATION_ERROR);
      expect(error.code).toBe('AUTH_REQUIRED');
      expect(error.message).toBe('Auth required');
      expect(error.severity).toBe('high');
      expect(error.recoverable).toBe(true);
      expect(error.retryable).toBe(false);
      expect(error.userMessage).toBe('Please sign in to continue.');
    });

    it('should create a server error with correct properties', () => {
      const error = createError.server('Server error');
      
      expect(error.type).toBe(ErrorType.SERVER_ERROR);
      expect(error.code).toBe('SERVER_ERROR');
      expect(error.message).toBe('Server error');
      expect(error.severity).toBe('high');
      expect(error.recoverable).toBe(false);
      expect(error.retryable).toBe(true);
      expect(error.userMessage).toBe('A server error occurred. Our team has been notified.');
    });
  });

  describe('convertAPIErrorToStandard', () => {
    it('should convert API error to standard error', () => {
      const apiError = {
        type: 'NETWORK_ERROR' as const,
        code: 'NETWORK_ERROR',
        message: 'Network failed',
        severity: 'medium' as ErrorSeverity,
        details: { url: 'https://api.example.com' }
      };

      const standardError = convertAPIErrorToStandard(apiError);
      
      expect(standardError.type).toBe(ErrorType.NETWORK_ERROR);
      expect(standardError.message).toBe('Network failed');
      expect(standardError.severity).toBe('medium');
      expect(standardError.retryable).toBe(true);
    });

    it('should convert regular Error to standard error', () => {
      const error = new Error('Regular error');
      const standardError = convertAPIErrorToStandard(error);
      
      expect(standardError.type).toBe(ErrorType.UNKNOWN_ERROR);
      expect(standardError.message).toBe('Regular error');
      expect(standardError.details?.['originalMessage']).toBe('Regular error');
    });

    it('should convert unknown error types to standard error', () => {
      const unknownError = 'String error';
      const standardError = convertAPIErrorToStandard(unknownError);
      
      expect(standardError.type).toBe(ErrorType.UNKNOWN_ERROR);
      expect(standardError.message).toBe('String error');
    });
  });

  describe('createFormError', () => {
    it('should create form error with correct properties', () => {
      const formError = createFormError('email', 'Invalid email format', 'INVALID_EMAIL', 'test@');
      
      expect(formError.field).toBe('email');
      expect(formError.message).toBe('Invalid email format');
      expect(formError.code).toBe('INVALID_EMAIL');
      expect(formError.value).toBe('test@');
    });
  });
});