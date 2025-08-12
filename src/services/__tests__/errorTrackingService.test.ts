/**
 * Comprehensive unit tests for ErrorTrackingService
 * Tests error reporting, tracking, and analytics functionality
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { errorTrackingService } from '../errorTrackingService';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock window and navigator
Object.defineProperty(window, 'location', {
  value: {
    href: 'https://example.com/test',
  },
  writable: true,
});

Object.defineProperty(navigator, 'userAgent', {
  value: 'Mozilla/5.0 (Test Browser)',
  writable: true,
});

describe('ErrorTrackingService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockClear();
    
    // Reset console methods
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Initialization', () => {
    it('should generate a unique session ID', () => {
      const service1 = new (errorTrackingService.constructor as any)();
      const service2 = new (errorTrackingService.constructor as any)();
      
      expect(service1.sessionId).toBeDefined();
      expect(service2.sessionId).toBeDefined();
      expect(service1.sessionId).not.toBe(service2.sessionId);
    });

    it('should set up global error handlers', () => {
      const addEventListenerSpy = vi.spyOn(window, 'addEventListener');
      
      new (errorTrackingService.constructor as any)();
      
      expect(addEventListenerSpy).toHaveBeenCalledWith('error', expect.any(Function));
      expect(addEventListenerSpy).toHaveBeenCalledWith('unhandledrejection', expect.any(Function));
    });
  });

  describe('User Management', () => {
    it('should set user ID correctly', () => {
      const testUserId = 'user-123';
      errorTrackingService.setUserId(testUserId);
      
      // Verify user ID is used in error reports
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ error_id: 'error-123' }),
      });

      errorTrackingService.reportError({
        error_type: 'TestError',
        error_message: 'Test message',
        severity: 'low',
        category: 'application',
      });

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/error-tracking/errors/report',
        expect.objectContaining({
          body: expect.stringContaining(testUserId),
        })
      );
    });
  });

  describe('Error Reporting', () => {
    it('should report basic errors successfully', async () => {
      const mockErrorId = 'error-123';
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ error_id: mockErrorId }),
      });

      const errorReport = {
        error_type: 'TestError',
        error_message: 'Test error message',
        severity: 'medium' as const,
        category: 'application' as const,
      };

      const result = await errorTrackingService.reportError(errorReport);

      expect(result).toBe(mockErrorId);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/error-tracking/errors/report',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining(errorReport.error_message),
        })
      );
    });

    it('should include context data in error reports', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ error_id: 'error-123' }),
      });

      const errorReport = {
        error_type: 'TestError',
        error_message: 'Test error',
        severity: 'low' as const,
        category: 'application' as const,
        context_data: { customField: 'customValue' },
      };

      await errorTrackingService.reportError(errorReport);

      const callBody = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(callBody.context_data).toEqual(
        expect.objectContaining({
          customField: 'customValue',
          url: 'https://example.com/test',
          userAgent: 'Mozilla/5.0 (Test Browser)',
          timestamp: expect.any(String),
        })
      );
    });

    it('should handle API errors gracefully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error',
      });

      const result = await errorTrackingService.reportError({
        error_type: 'TestError',
        error_message: 'Test error',
        severity: 'low',
        category: 'application',
      });

      expect(result).toBeNull();
      expect(console.error).toHaveBeenCalledWith('Failed to report error:', 'Internal Server Error');
    });

    it('should handle network errors gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await errorTrackingService.reportError({
        error_type: 'TestError',
        error_message: 'Test error',
        severity: 'low',
        category: 'application',
      });

      expect(result).toBeNull();
      expect(console.error).toHaveBeenCalledWith('Error reporting error:', expect.any(Error));
    });
  });

  describe('Specialized Error Reporting', () => {
    it('should report JavaScript errors with proper formatting', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ error_id: 'error-123' }),
      });

      const testError = new Error('Test JavaScript error');
      testError.stack = 'Error: Test JavaScript error\n    at test.js:1:1';

      const context = {
        feature_name: 'testFeature',
        operation: 'testOperation',
        context_data: { additional: 'data' },
      };

      await errorTrackingService.reportJavaScriptError(testError, context);

      const callBody = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(callBody).toEqual(
        expect.objectContaining({
          error_type: 'Error',
          error_message: 'Test JavaScript error',
          stack_trace: testError.stack,
          severity: 'high',
          category: 'application',
          feature_name: 'testFeature',
          operation: 'testOperation',
        })
      );
    });

    it('should report network errors with appropriate severity', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ error_id: 'error-123' }),
      });

      // Test 500 error (high severity)
      await errorTrackingService.reportNetworkError(
        '/api/test',
        500,
        'Internal Server Error'
      );

      let callBody = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(callBody.severity).toBe('high');

      mockFetch.mockClear();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ error_id: 'error-124' }),
      });

      // Test 404 error (medium severity)
      await errorTrackingService.reportNetworkError(
        '/api/test',
        404,
        'Not Found'
      );

      callBody = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(callBody.severity).toBe('medium');
    });

    it('should report performance issues with proper thresholds', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ error_id: 'error-123' }),
      });

      const metric = 'page_load_time';
      const value = 5000;
      const threshold = 2000;

      await errorTrackingService.reportPerformanceIssue(metric, value, threshold);

      const callBody = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(callBody).toEqual(
        expect.objectContaining({
          error_type: 'PerformanceIssue',
          error_message: `${metric} exceeded threshold: ${value} > ${threshold}`,
          severity: 'high', // value > threshold * 2
          category: 'performance',
        })
      );
    });
  });

  describe('User Feedback', () => {
    it('should submit user feedback successfully', async () => {
      const mockFeedbackId = 'feedback-123';
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ feedback_id: mockFeedbackId }),
      });

      const feedback = {
        feedback_type: 'bug_report' as const,
        title: 'Test Bug Report',
        description: 'This is a test bug report',
        user_email: 'test@example.com',
        severity: 'medium' as const,
        category: 'ui',
        metadata: { page: 'dashboard' },
      };

      const result = await errorTrackingService.submitUserFeedback(feedback);

      expect(result).toBe(mockFeedbackId);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/error-tracking/feedback',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
      );

      const callBody = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(callBody.metadata).toEqual(
        expect.objectContaining({
          page: 'dashboard',
          url: 'https://example.com/test',
          userAgent: 'Mozilla/5.0 (Test Browser)',
          timestamp: expect.any(String),
        })
      );
    });

    it('should handle feedback submission errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Bad Request',
      });

      const result = await errorTrackingService.submitUserFeedback({
        feedback_type: 'bug_report',
        title: 'Test',
        description: 'Test description',
        severity: 'low',
      });

      expect(result).toBeNull();
      expect(console.error).toHaveBeenCalledWith('Failed to submit feedback:', 'Bad Request');
    });
  });

  describe('Incident Management', () => {
    it('should create incidents successfully', async () => {
      const mockIncidentId = 'incident-123';
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ incident_id: mockIncidentId }),
      });

      const incident = {
        title: 'Test Incident',
        description: 'Test incident description',
        severity: 'high' as const,
        category: 'system' as const,
        affected_features: ['chat', 'documents'],
        assigned_to: 'admin@example.com',
      };

      const result = await errorTrackingService.createIncident(incident);

      expect(result).toBe(mockIncidentId);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/error-tracking/incidents',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(incident),
        })
      );
    });

    it('should update incidents successfully', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true });

      const incidentId = 'incident-123';
      const updates = {
        status: 'resolved',
        resolution_notes: 'Fixed the issue',
        update_description: 'Applied hotfix',
      };

      const result = await errorTrackingService.updateIncident(incidentId, updates);

      expect(result).toBe(true);
      expect(mockFetch).toHaveBeenCalledWith(
        `/api/error-tracking/incidents/${incidentId}`,
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updates),
        })
      );
    });
  });

  describe('Data Retrieval', () => {
    it('should get errors with filters', async () => {
      const mockErrors = [
        { id: 'error-1', message: 'Test error 1' },
        { id: 'error-2', message: 'Test error 2' },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockErrors),
      });

      const filters = {
        severity: 'high',
        category: 'application',
        days: 7,
        limit: 10,
      };

      const result = await errorTrackingService.getErrors(filters);

      expect(result).toEqual(mockErrors);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/error-tracking/errors?severity=high&category=application&days=7&limit=10'
      );
    });

    it('should get incidents with filters', async () => {
      const mockIncidents = [
        { id: 'incident-1', title: 'Test incident 1' },
        { id: 'incident-2', title: 'Test incident 2' },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ incidents: mockIncidents }),
      });

      const filters = {
        status: 'open',
        severity: 'critical',
        assigned_to: 'admin@example.com',
      };

      const result = await errorTrackingService.getIncidents(filters);

      expect(result).toEqual(mockIncidents);
    });

    it('should get system health status', async () => {
      const mockHealth = {
        overall_status: 'healthy',
        components: {
          database: 'healthy',
          api: 'degraded',
          cache: 'healthy',
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockHealth),
      });

      const result = await errorTrackingService.getSystemHealth();

      expect(result).toEqual(mockHealth);
      expect(mockFetch).toHaveBeenCalledWith('/api/error-tracking/health');
    });

    it('should get analytics data', async () => {
      const mockAnalytics = {
        total_errors: 150,
        error_rate: 0.02,
        top_errors: ['TypeError', 'NetworkError'],
        performance_metrics: { avg_response_time: 250 },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockAnalytics),
      });

      const result = await errorTrackingService.getAnalytics(30);

      expect(result).toEqual(mockAnalytics);
      expect(mockFetch).toHaveBeenCalledWith('/api/error-tracking/analytics?days=30');
    });

    it('should handle API errors in data retrieval', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Unauthorized',
      });

      const result = await errorTrackingService.getErrors();

      expect(result).toEqual([]);
      expect(console.error).toHaveBeenCalledWith('Failed to get errors:', 'Unauthorized');
    });
  });

  describe('Utility Methods', () => {
    it('should track feature usage failures', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ error_id: 'error-123' }),
      });

      errorTrackingService.trackFeatureUsage('chat', 'send_message', false, 1000);

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/error-tracking/errors/report',
        expect.objectContaining({
          body: expect.stringContaining('FeatureFailure'),
        })
      );
    });

    it('should track slow feature operations', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ error_id: 'error-123' }),
      });

      errorTrackingService.trackFeatureUsage('documents', 'upload', true, 6000);

      const callBody = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(callBody.error_type).toBe('PerformanceIssue');
      expect(callBody.error_message).toContain('operation_duration exceeded threshold');
    });

    it('should track API call failures', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ error_id: 'error-123' }),
      });

      errorTrackingService.trackApiCall('/api/chat', 'POST', 500, 2000);

      const callBody = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(callBody.error_type).toBe('NetworkError');
      expect(callBody.error_message).toContain('HTTP 500');
    });

    it('should track slow API calls', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ error_id: 'error-123' }),
      });

      errorTrackingService.trackApiCall('/api/search', 'GET', 200, 12000);

      const callBody = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(callBody.error_type).toBe('PerformanceIssue');
      expect(callBody.error_message).toContain('api_response_time exceeded threshold');
    });

    it('should track user action failures', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ error_id: 'error-123' }),
      });

      const context = { button: 'save', form: 'settings' };
      errorTrackingService.trackUserAction('save_settings', false, context);

      const callBody = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(callBody.error_type).toBe('UserActionFailure');
      expect(callBody.category).toBe('user_input');
      expect(callBody.context_data).toEqual(expect.objectContaining(context));
    });
  });

  describe('Global Error Handlers', () => {
    it('should handle window error events', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ error_id: 'error-123' }),
      });

      // Create a new service instance to test global handlers
      new (errorTrackingService.constructor as any)();

      // Simulate a window error event
      const errorEvent = new ErrorEvent('error', {
        message: 'Test error message',
        filename: 'test.js',
        lineno: 10,
        colno: 5,
        error: new Error('Test error'),
      });

      window.dispatchEvent(errorEvent);

      await new Promise(resolve => setTimeout(resolve, 0)); // Allow async operations

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/error-tracking/errors/report',
        expect.objectContaining({
          body: expect.stringContaining('JavaScriptError'),
        })
      );
    });

    it('should handle unhandled promise rejections', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ error_id: 'error-123' }),
      });

      // Create a new service instance to test global handlers
      new (errorTrackingService.constructor as any)();

      // Simulate an unhandled promise rejection
      const rejectionEvent = new PromiseRejectionEvent('unhandledrejection', {
        promise: Promise.reject(new Error('Unhandled promise rejection')),
        reason: new Error('Unhandled promise rejection'),
      });

      window.dispatchEvent(rejectionEvent);

      await new Promise(resolve => setTimeout(resolve, 0)); // Allow async operations

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/error-tracking/errors/report',
        expect.objectContaining({
          body: expect.stringContaining('UnhandledPromiseRejection'),
        })
      );
    });
  });

  describe('Error Resolution', () => {
    it('should resolve errors successfully', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true });

      const result = await errorTrackingService.resolveError('error-123');

      expect(result).toBe(true);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/error-tracking/errors/error-123/resolve',
        { method: 'PUT' }
      );
    });

    it('should handle error resolution failures', async () => {
      mockFetch.mockResolvedValueOnce({ ok: false });

      const result = await errorTrackingService.resolveError('error-123');

      expect(result).toBe(false);
    });
  });

  describe('Incident Timeline', () => {
    it('should get incident timeline successfully', async () => {
      const mockTimeline = [
        { timestamp: '2023-01-01T00:00:00Z', event: 'Incident created' },
        { timestamp: '2023-01-01T01:00:00Z', event: 'Investigation started' },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ timeline: mockTimeline }),
      });

      const result = await errorTrackingService.getIncidentTimeline('incident-123');

      expect(result).toEqual(mockTimeline);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/error-tracking/incidents/incident-123/timeline'
      );
    });

    it('should handle timeline retrieval errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Not Found',
      });

      const result = await errorTrackingService.getIncidentTimeline('incident-123');

      expect(result).toEqual([]);
      expect(console.error).toHaveBeenCalledWith('Failed to get incident timeline:', 'Not Found');
    });
  });
});