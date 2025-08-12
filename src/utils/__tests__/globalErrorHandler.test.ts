import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { errorTrackingService } from '../../services/errorTrackingService';
import { createError } from '../errorFactory';
import { GlobalErrorHandler, globalErrorHandler, initializeGlobalErrorHandling } from '../globalErrorHandler';

// Mock the error tracking service
vi.mock('../../services/errorTrackingService', () => ({
  errorTrackingService: {
    reportError: vi.fn(),
  },
}));

// Mock the error factory
vi.mock('../errorFactory', () => ({
  createError: {
    component: vi.fn(() => ({
      id: 'error_123',
      type: 'COMPONENT_ERROR',
      severity: 'medium',
      recoverable: true,
      retryable: false,
      userMessage: 'Component error occurred',
    })),
    network: vi.fn(() => ({
      id: 'error_456',
      type: 'NETWORK_ERROR',
      severity: 'high',
      recoverable: false,
      retryable: true,
      userMessage: 'Network error occurred',
    })),
    unknown: vi.fn(() => ({
      id: 'error_789',
      type: 'UNKNOWN_ERROR',
      severity: 'medium',
      recoverable: true,
      retryable: false,
      userMessage: 'Unknown error occurred',
    })),
  },
}));

// Mock console methods
const consoleSpy = {
  error: vi.spyOn(console, 'error').mockImplementation(() => {}),
  group: vi.spyOn(console, 'group').mockImplementation(() => {}),
  groupEnd: vi.spyOn(console, 'groupEnd').mockImplementation(() => {}),
};

// Mock sessionStorage
const mockSessionStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'sessionStorage', { value: mockSessionStorage });

// Mock DOM methods
const mockAppendChild = vi.fn();
const mockRemove = vi.fn();
const mockCreateElement = vi.fn(() => ({
  className: '',
  innerHTML: '',
  remove: mockRemove,
}));
Object.defineProperty(document, 'createElement', { value: mockCreateElement });
Object.defineProperty(document.body, 'appendChild', { value: mockAppendChild });

describe('GlobalErrorHandler', () => {
  let handler: GlobalErrorHandler;
  let originalAddEventListener: typeof window.addEventListener;
  let eventListeners: Map<string, EventListener[]>;

  beforeEach(() => {
    vi.clearAllMocks();
    consoleSpy.error.mockClear();
    consoleSpy.group.mockClear();
    consoleSpy.groupEnd.mockClear();
    mockSessionStorage.getItem.mockClear();
    mockSessionStorage.setItem.mockClear();
    mockAppendChild.mockClear();
    mockRemove.mockClear();
    mockCreateElement.mockClear();

    // Mock addEventListener to track event listeners
    eventListeners = new Map();
    originalAddEventListener = window.addEventListener;
    window.addEventListener = vi.fn((event: string, listener: EventListener, options?: any) => {
      if (!eventListeners.has(event)) {
        eventListeners.set(event, []);
      }
      eventListeners.get(event)!.push(listener);
    });

    handler = new GlobalErrorHandler({
      enableConsoleLogging: true,
      enableErrorReporting: true,
      enableUserNotification: true,
      maxErrorsPerSession: 10,
      errorCooldownMs: 100,
    });
  });

  afterEach(() => {
    window.addEventListener = originalAddEventListener;
    vi.restoreAllMocks();
  });

  describe('Initialization', () => {
    it('should initialize with default configuration', () => {
      const defaultHandler = new GlobalErrorHandler();
      expect(defaultHandler).toBeInstanceOf(GlobalErrorHandler);
    });

    it('should initialize with custom configuration', () => {
      const customHandler = new GlobalErrorHandler({
        enableConsoleLogging: false,
        maxErrorsPerSession: 5,
      });
      expect(customHandler).toBeInstanceOf(GlobalErrorHandler);
    });

    it('should set up event listeners during initialization', () => {
      expect(window.addEventListener).toHaveBeenCalledWith('unhandledrejection', expect.any(Function));
      expect(window.addEventListener).toHaveBeenCalledWith('error', expect.any(Function));
      expect(window.addEventListener).toHaveBeenCalledWith('error', expect.any(Function), true);
    });

    it('should intercept console.error when logging is enabled', () => {
      const originalConsoleError = console.error;
      
      new GlobalErrorHandler({ enableConsoleLogging: true });
      
      expect(console.error).not.toBe(originalConsoleError);
    });
  });

  describe('Unhandled Promise Rejection Handling', () => {
    it('should handle unhandled promise rejections', () => {
      const error = new Error('Promise rejection test');
      const event = new PromiseRejectionEvent('unhandledrejection', {
        promise: Promise.reject(error),
        reason: error,
      });

      const listeners = eventListeners.get('unhandledrejection') || [];
      listeners.forEach(listener => listener(event));

      expect(errorTrackingService.reportError).toHaveBeenCalledWith(
        expect.objectContaining({
          error_type: 'COMPONENT_ERROR',
          error_message: 'Promise rejection test',
          category: 'application',
          feature_name: 'global_error_handler',
          operation: 'unhandled_promise_rejection',
        })
      );
    });

    it('should handle non-Error promise rejections', () => {
      const rejectionReason = 'String rejection reason';
      const event = new PromiseRejectionEvent('unhandledrejection', {
        promise: Promise.reject(rejectionReason),
        reason: rejectionReason,
      });

      const listeners = eventListeners.get('unhandledrejection') || [];
      listeners.forEach(listener => listener(event));

      expect(errorTrackingService.reportError).toHaveBeenCalled();
    });

    it('should prevent default browser behavior for unhandled rejections', () => {
      const error = new Error('Test error');
      const event = new PromiseRejectionEvent('unhandledrejection', {
        promise: Promise.reject(error),
        reason: error,
      });
      const preventDefaultSpy = vi.spyOn(event, 'preventDefault');

      const listeners = eventListeners.get('unhandledrejection') || [];
      listeners.forEach(listener => listener(event));

      expect(preventDefaultSpy).toHaveBeenCalled();
    });
  });

  describe('Uncaught JavaScript Error Handling', () => {
    it('should handle uncaught JavaScript errors', () => {
      const event = new ErrorEvent('error', {
        message: 'Uncaught error test',
        filename: 'test.js',
        lineno: 10,
        colno: 5,
        error: new Error('Uncaught error test'),
      });

      const listeners = eventListeners.get('error') || [];
      listeners.forEach(listener => listener(event));

      expect(errorTrackingService.reportError).toHaveBeenCalledWith(
        expect.objectContaining({
          error_type: 'COMPONENT_ERROR',
          error_message: 'Uncaught error test',
          operation: 'uncaught_javascript_error',
        })
      );
    });

    it('should handle errors without error object', () => {
      const event = new ErrorEvent('error', {
        message: 'Error without object',
        filename: 'test.js',
        lineno: 10,
        colno: 5,
      });

      const listeners = eventListeners.get('error') || [];
      listeners.forEach(listener => listener(event));

      expect(errorTrackingService.reportError).toHaveBeenCalled();
    });
  });

  describe('Resource Loading Error Handling', () => {
    it('should handle image loading errors', () => {
      const img = document.createElement('img');
      img.src = 'https://example.com/image.jpg';
      
      const event = new Event('error');
      Object.defineProperty(event, 'target', { value: img });

      const listeners = eventListeners.get('error') || [];
      // Find the capture listener (third parameter is true)
      const captureListener = listeners[listeners.length - 1];
      captureListener(event);

      expect(errorTrackingService.reportError).toHaveBeenCalledWith(
        expect.objectContaining({
          error_type: 'NETWORK_ERROR',
          error_message: expect.stringContaining('Failed to load resource'),
          operation: 'resource_loading_error',
        })
      );
    });

    it('should handle script loading errors', () => {
      const script = document.createElement('script');
      script.src = 'https://example.com/script.js';
      
      const event = new Event('error');
      Object.defineProperty(event, 'target', { value: script });

      const listeners = eventListeners.get('error') || [];
      const captureListener = listeners[listeners.length - 1];
      captureListener(event);

      expect(errorTrackingService.reportError).toHaveBeenCalled();
    });

    it('should handle link loading errors', () => {
      const link = document.createElement('link');
      link.href = 'https://example.com/style.css';
      
      const event = new Event('error');
      Object.defineProperty(event, 'target', { value: link });

      const listeners = eventListeners.get('error') || [];
      const captureListener = listeners[listeners.length - 1];
      captureListener(event);

      expect(errorTrackingService.reportError).toHaveBeenCalled();
    });
  });

  describe('Console Error Interception', () => {
    it('should intercept and report console.error calls', () => {
      console.error('Test console error', { data: 'test' });

      expect(errorTrackingService.reportError).toHaveBeenCalledWith(
        expect.objectContaining({
          error_type: 'COMPONENT_ERROR',
          error_message: expect.stringContaining('Console Error: Test console error'),
          operation: 'console_error',
        })
      );
    });

    it('should call original console.error', () => {
      const originalError = vi.fn();
      console.error = originalError;
      
      new GlobalErrorHandler({ enableConsoleLogging: true });
      
      console.error('Test message');
      expect(originalError).toHaveBeenCalledWith('Test message');
    });
  });

  describe('Manual Error Reporting', () => {
    it('should allow manual error reporting', () => {
      const error = new Error('Manual error test');
      const context = { customData: 'test' };

      handler.reportManualError(error, context);

      expect(errorTrackingService.reportError).toHaveBeenCalledWith(
        expect.objectContaining({
          error_message: 'Manual error test',
          operation: 'manual_report',
          context_data: expect.objectContaining({
            customData: 'test',
          }),
        })
      );
    });

    it('should report manual errors without context', () => {
      const error = new Error('Manual error without context');

      handler.reportManualError(error);

      expect(errorTrackingService.reportError).toHaveBeenCalledWith(
        expect.objectContaining({
          error_message: 'Manual error without context',
          operation: 'manual_report',
        })
      );
    });
  });

  describe('Rate Limiting', () => {
    it('should respect error cooldown period', async () => {
      const error1 = new Error('First error');
      const error2 = new Error('Second error');

      handler.reportManualError(error1);
      handler.reportManualError(error2); // Should be rate limited

      expect(errorTrackingService.reportError).toHaveBeenCalledTimes(1);
    });

    it('should allow errors after cooldown period', async () => {
      const error1 = new Error('First error');
      const error2 = new Error('Second error');

      handler.reportManualError(error1);
      
      // Wait for cooldown period
      await new Promise(resolve => setTimeout(resolve, 150));
      
      handler.reportManualError(error2);

      expect(errorTrackingService.reportError).toHaveBeenCalledTimes(2);
    });

    it('should respect maximum errors per session', () => {
      // Report more errors than the limit
      for (let i = 0; i < 15; i++) {
        handler.reportManualError(new Error(`Error ${i}`));
        // Add small delay to avoid cooldown
        vi.advanceTimersByTime(200);
      }

      // Should only report up to the limit
      expect(errorTrackingService.reportError).toHaveBeenCalledTimes(10);
    });

    it('should deduplicate similar errors', () => {
      const error1 = new Error('Duplicate error');
      const error2 = new Error('Duplicate error');

      handler.reportManualError(error1);
      vi.advanceTimersByTime(200);
      handler.reportManualError(error2);

      expect(errorTrackingService.reportError).toHaveBeenCalledTimes(1);
    });
  });

  describe('User Notifications', () => {
    it('should show user notification for high severity errors', () => {
      // Mock createError to return high severity error
      (createError.component as any).mockReturnValue({
        id: 'error_123',
        type: 'COMPONENT_ERROR',
        severity: 'high',
        recoverable: true,
        retryable: false,
        userMessage: 'High severity error',
      });

      const error = new Error('High severity test');
      handler.reportManualError(error);

      expect(mockCreateElement).toHaveBeenCalledWith('div');
      expect(mockAppendChild).toHaveBeenCalled();
    });

    it('should not show notification for low severity errors', () => {
      // Mock createError to return low severity error
      (createError.component as any).mockReturnValue({
        id: 'error_123',
        type: 'COMPONENT_ERROR',
        severity: 'low',
        recoverable: true,
        retryable: false,
        userMessage: 'Low severity error',
      });

      const error = new Error('Low severity test');
      handler.reportManualError(error);

      expect(mockCreateElement).not.toHaveBeenCalled();
      expect(mockAppendChild).not.toHaveBeenCalled();
    });

    it('should not show notification for resource loading errors', () => {
      const img = document.createElement('img');
      img.src = 'https://example.com/image.jpg';
      
      const event = new Event('error');
      Object.defineProperty(event, 'target', { value: img });

      const listeners = eventListeners.get('error') || [];
      const captureListener = listeners[listeners.length - 1];
      captureListener(event);

      expect(mockCreateElement).not.toHaveBeenCalled();
      expect(mockAppendChild).not.toHaveBeenCalled();
    });

    it('should auto-remove notifications after timeout', () => {
      vi.useFakeTimers();

      // Mock createError to return high severity error
      (createError.component as any).mockReturnValue({
        id: 'error_123',
        type: 'COMPONENT_ERROR',
        severity: 'high',
        recoverable: true,
        retryable: false,
        userMessage: 'High severity error',
      });

      const error = new Error('Auto-remove test');
      handler.reportManualError(error);

      // Fast-forward time
      vi.advanceTimersByTime(5000);

      expect(mockRemove).toHaveBeenCalled();

      vi.useRealTimers();
    });
  });

  describe('Session Management', () => {
    it('should generate session ID if not exists', () => {
      mockSessionStorage.getItem.mockReturnValue(null);

      handler.reportManualError(new Error('Session test'));

      expect(mockSessionStorage.setItem).toHaveBeenCalledWith(
        'error_session_id',
        expect.stringMatching(/^session_\d+_[a-z0-9]+$/)
      );
    });

    it('should use existing session ID', () => {
      const existingSessionId = 'existing_session_123';
      mockSessionStorage.getItem.mockReturnValue(existingSessionId);

      handler.reportManualError(new Error('Session test'));

      expect(errorTrackingService.reportError).toHaveBeenCalledWith(
        expect.objectContaining({
          context_data: expect.objectContaining({
            sessionId: existingSessionId,
          }),
        })
      );
    });
  });

  describe('Configuration Management', () => {
    it('should update configuration', () => {
      const newConfig = {
        enableConsoleLogging: false,
        maxErrorsPerSession: 20,
      };

      handler.updateConfig(newConfig);

      // Test that the new config is applied
      const stats = handler.getErrorStats();
      expect(stats).toHaveProperty('errorCount');
      expect(stats).toHaveProperty('lastErrorTime');
    });

    it('should get error statistics', () => {
      const stats = handler.getErrorStats();

      expect(stats).toHaveProperty('errorCount');
      expect(stats).toHaveProperty('lastErrorTime');
      expect(typeof stats.errorCount).toBe('number');
      expect(typeof stats.lastErrorTime).toBe('number');
    });

    it('should clear error cache', () => {
      // Generate some errors first
      handler.reportManualError(new Error('Test 1'));
      vi.advanceTimersByTime(200);
      handler.reportManualError(new Error('Test 2'));

      const statsBefore = handler.getErrorStats();
      expect(statsBefore.errorCount).toBeGreaterThan(0);

      handler.clearErrorCache();

      const statsAfter = handler.getErrorStats();
      expect(statsAfter.errorCount).toBe(0);
      expect(statsAfter.lastErrorTime).toBe(0);
    });
  });

  describe('Error Type Conversion', () => {
    it('should handle StandardError objects', () => {
      const standardError = {
        id: 'standard_error_123',
        type: 'VALIDATION_ERROR',
        code: 'VALIDATION_ERROR',
        message: 'Standard error test',
        severity: 'medium' as const,
        timestamp: new Date(),
        recoverable: true,
        retryable: false,
        userMessage: 'Standard error message',
        details: {},
      };

      handler.reportManualError(standardError as any);

      expect(errorTrackingService.reportError).toHaveBeenCalledWith(
        expect.objectContaining({
          error_type: 'VALIDATION_ERROR',
          error_message: 'Standard error test',
          severity: 'medium',
        })
      );
    });

    it('should handle APIErrorClass objects', () => {
      const apiError = {
        type: 'NETWORK_ERROR',
        statusCode: 500,
        message: 'API error test',
        id: 'api_error_123',
      };

      handler.reportManualError(apiError as any);

      expect(createError.component).toHaveBeenCalledWith(
        'API error test',
        expect.objectContaining({
          component: 'global_error_handler',
          operation: 'manual_report',
        }),
        expect.objectContaining({
          originalError: 'NETWORK_ERROR',
          statusCode: 500,
          apiErrorId: 'api_error_123',
        })
      );
    });
  });

  describe('Development Mode Features', () => {
    it('should log errors to console in development mode', () => {
      const error = new Error('Development test');
      handler.reportManualError(error);

      expect(consoleSpy.group).toHaveBeenCalledWith('🚨 Global Error Handler');
      expect(consoleSpy.error).toHaveBeenCalledWith('Error:', error);
      expect(consoleSpy.groupEnd).toHaveBeenCalled();
    });

    it('should not log errors when console logging is disabled', () => {
      const quietHandler = new GlobalErrorHandler({ enableConsoleLogging: false });
      const error = new Error('Quiet test');
      
      quietHandler.reportManualError(error);

      expect(consoleSpy.group).not.toHaveBeenCalled();
      expect(consoleSpy.error).not.toHaveBeenCalled();
    });
  });

  describe('Error Reporting Failures', () => {
    it('should handle error tracking service failures gracefully', () => {
      (errorTrackingService.reportError as any).mockImplementation(() => {
        throw new Error('Reporting service failed');
      });

      const error = new Error('Test error');
      
      expect(() => {
        handler.reportManualError(error);
      }).not.toThrow();

      expect(consoleSpy.error).toHaveBeenCalledWith(
        'Failed to report error:',
        expect.any(Error)
      );
    });
  });

  describe('Global Instance', () => {
    it('should export a global instance', () => {
      expect(globalErrorHandler).toBeInstanceOf(GlobalErrorHandler);
    });

    it('should provide initialization function', () => {
      const customHandler = initializeGlobalErrorHandling({
        enableConsoleLogging: false,
      });

      expect(customHandler).toBeInstanceOf(GlobalErrorHandler);
    });
  });
});