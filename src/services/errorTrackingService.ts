/**
 * Error Tracking Service for Frontend
 * Provides client-side error tracking and reporting capabilities
 */

interface ErrorContext {
  user_id?: string;
  session_id?: string;
  feature_name?: string;
  operation?: string;
  context_data?: Record<string, any>;
}

interface ErrorReport {
  error_type: string;
  error_message: string;
  stack_trace?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: 'application' | 'system' | 'integration' | 'user_input' | 'performance' | 'security';
  feature_name?: string;
  operation?: string;
  user_id?: string;
  session_id?: string;
  context_data?: Record<string, any>;
}

interface UserFeedback {
  feedback_type: 'bug_report' | 'feature_request' | 'general';
  title: string;
  description: string;
  user_email?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category?: string;
  metadata?: Record<string, any>;
}

interface IncidentCreate {
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: 'application' | 'system' | 'integration' | 'user_input' | 'performance' | 'security';
  affected_features?: string[];
  assigned_to?: string;
}

class ErrorTrackingService {
  private baseUrl = '/api/error-tracking';
  private sessionId: string;
  private userId?: string;

  constructor() {
    this.sessionId = this.generateSessionId();
    this.setupGlobalErrorHandlers();
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private setupGlobalErrorHandlers(): void {
    // Handle unhandled JavaScript errors
    window.addEventListener('error', (event) => {
      this.reportError({
        error_type: 'JavaScriptError',
        error_message: event.message,
        stack_trace: event.error?.stack,
        severity: 'high',
        category: 'application',
        context_data: {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
          url: window.location.href
        }
      });
    });

    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.reportError({
        error_type: 'UnhandledPromiseRejection',
        error_message: event.reason?.message || 'Unhandled promise rejection',
        stack_trace: event.reason?.stack,
        severity: 'high',
        category: 'application',
        context_data: {
          reason: event.reason,
          url: window.location.href
        }
      });
    });

    // Handle React error boundaries (if using React)
    if (typeof window !== 'undefined' && (window as any).React) {
      const originalConsoleError = console.error;
      console.error = (...args) => {
        // Check if this is a React error
        if (args[0] && typeof args[0] === 'string' && args[0].includes('React')) {
          this.reportError({
            error_type: 'ReactError',
            error_message: args.join(' '),
            severity: 'high',
            category: 'application',
            context_data: {
              url: window.location.href,
              userAgent: navigator.userAgent
            }
          });
        }
        originalConsoleError.apply(console, args);
      };
    }
  }

  setUserId(userId: string): void {
    this.userId = userId;
  }

  async reportError(errorReport: ErrorReport): Promise<string | null> {
    try {
      const payload = {
        ...errorReport,
        user_id: this.userId,
        session_id: this.sessionId,
        context_data: {
          ...errorReport.context_data,
          url: window.location.href,
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString()
        }
      };

      const response = await fetch(`${this.baseUrl}/errors/report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        const result = await response.json();
        return result.error_id;
      } else {
        console.error('Failed to report error:', response.statusText);
        return null;
      }
    } catch (error) {
      console.error('Error reporting error:', error);
      return null;
    }
  }

  async reportJavaScriptError(error: Error, context?: ErrorContext): Promise<string | null> {
    return this.reportError({
      error_type: error.name || 'JavaScriptError',
      error_message: error.message,
      stack_trace: error.stack,
      severity: 'high',
      category: 'application',
      feature_name: context?.feature_name,
      operation: context?.operation,
      context_data: context?.context_data
    });
  }

  async reportNetworkError(url: string, status: number, statusText: string, context?: ErrorContext): Promise<string | null> {
    return this.reportError({
      error_type: 'NetworkError',
      error_message: `HTTP ${status}: ${statusText}`,
      severity: status >= 500 ? 'high' : 'medium',
      category: 'integration',
      feature_name: context?.feature_name,
      operation: context?.operation,
      context_data: {
        ...context?.context_data,
        url,
        status,
        statusText
      }
    });
  }

  async reportPerformanceIssue(metric: string, value: number, threshold: number, context?: ErrorContext): Promise<string | null> {
    return this.reportError({
      error_type: 'PerformanceIssue',
      error_message: `${metric} exceeded threshold: ${value} > ${threshold}`,
      severity: value > threshold * 2 ? 'high' : 'medium',
      category: 'performance',
      feature_name: context?.feature_name,
      operation: context?.operation,
      context_data: {
        ...context?.context_data,
        metric,
        value,
        threshold
      }
    });
  }

  async submitUserFeedback(feedback: UserFeedback): Promise<string | null> {
    try {
      const payload = {
        ...feedback,
        metadata: {
          ...feedback.metadata,
          url: window.location.href,
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString()
        }
      };

      const response = await fetch(`${this.baseUrl}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        const result = await response.json();
        return result.feedback_id;
      } else {
        console.error('Failed to submit feedback:', response.statusText);
        return null;
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
      return null;
    }
  }

  async createIncident(incident: IncidentCreate): Promise<string | null> {
    try {
      const response = await fetch(`${this.baseUrl}/incidents`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(incident)
      });

      if (response.ok) {
        const result = await response.json();
        return result.incident_id;
      } else {
        console.error('Failed to create incident:', response.statusText);
        return null;
      }
    } catch (error) {
      console.error('Error creating incident:', error);
      return null;
    }
  }

  async getErrors(filters?: {
    severity?: string;
    category?: string;
    feature_name?: string;
    resolved?: boolean;
    days?: number;
    limit?: number;
  }): Promise<any[]> {
    try {
      const params = new URLSearchParams();
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined) {
            params.append(key, value.toString());
          }
        });
      }

      const response = await fetch(`${this.baseUrl}/errors?${params}`);
      if (response.ok) {
        return await response.json();
      } else {
        console.error('Failed to get errors:', response.statusText);
        return [];
      }
    } catch (error) {
      console.error('Error getting errors:', error);
      return [];
    }
  }

  async getIncidents(filters?: {
    status?: string;
    severity?: string;
    assigned_to?: string;
    days?: number;
    limit?: number;
  }): Promise<any[]> {
    try {
      const params = new URLSearchParams();
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined) {
            params.append(key, value.toString());
          }
        });
      }

      const response = await fetch(`${this.baseUrl}/incidents?${params}`);
      if (response.ok) {
        const result = await response.json();
        return result.incidents || [];
      } else {
        console.error('Failed to get incidents:', response.statusText);
        return [];
      }
    } catch (error) {
      console.error('Error getting incidents:', error);
      return [];
    }
  }

  async getFeedback(filters?: {
    feedback_type?: string;
    status?: string;
    days?: number;
    limit?: number;
  }): Promise<any[]> {
    try {
      const params = new URLSearchParams();
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined) {
            params.append(key, value.toString());
          }
        });
      }

      const response = await fetch(`${this.baseUrl}/feedback?${params}`);
      if (response.ok) {
        const result = await response.json();
        return result.feedback || [];
      } else {
        console.error('Failed to get feedback:', response.statusText);
        return [];
      }
    } catch (error) {
      console.error('Error getting feedback:', error);
      return [];
    }
  }

  async getSystemHealth(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      if (response.ok) {
        return await response.json();
      } else {
        console.error('Failed to get system health:', response.statusText);
        return { overall_status: 'unknown', components: {} };
      }
    } catch (error) {
      console.error('Error getting system health:', error);
      return { overall_status: 'unknown', components: {} };
    }
  }

  async getAnalytics(days: number = 7): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/analytics?days=${days}`);
      if (response.ok) {
        return await response.json();
      } else {
        console.error('Failed to get analytics:', response.statusText);
        return {};
      }
    } catch (error) {
      console.error('Error getting analytics:', error);
      return {};
    }
  }

  async resolveError(errorId: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/errors/${errorId}/resolve`, {
        method: 'PUT'
      });
      return response.ok;
    } catch (error) {
      console.error('Error resolving error:', error);
      return false;
    }
  }

  async updateIncident(incidentId: string, updates: {
    status?: string;
    assigned_to?: string;
    resolution_notes?: string;
    update_description?: string;
  }): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/incidents/${incidentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates)
      });
      return response.ok;
    } catch (error) {
      console.error('Error updating incident:', error);
      return false;
    }
  }

  async getIncidentTimeline(incidentId: string): Promise<any[]> {
    try {
      const response = await fetch(`${this.baseUrl}/incidents/${incidentId}/timeline`);
      if (response.ok) {
        const result = await response.json();
        return result.timeline || [];
      } else {
        console.error('Failed to get incident timeline:', response.statusText);
        return [];
      }
    } catch (error) {
      console.error('Error getting incident timeline:', error);
      return [];
    }
  }

  // Utility methods for common error scenarios
  trackFeatureUsage(featureName: string, operation: string, success: boolean, duration?: number): void {
    if (!success) {
      this.reportError({
        error_type: 'FeatureFailure',
        error_message: `Feature ${featureName} operation ${operation} failed`,
        severity: 'medium',
        category: 'application',
        feature_name: featureName,
        operation: operation,
        context_data: { duration }
      });
    } else if (duration && duration > 5000) { // 5 seconds threshold
      this.reportPerformanceIssue('operation_duration', duration, 5000, {
        feature_name: featureName,
        operation: operation
      });
    }
  }

  trackApiCall(endpoint: string, method: string, status: number, duration: number): void {
    if (status >= 400) {
      this.reportNetworkError(endpoint, status, `${method} request failed`, {
        operation: `${method} ${endpoint}`,
        context_data: { duration }
      });
    } else if (duration > 10000) { // 10 seconds threshold
      this.reportPerformanceIssue('api_response_time', duration, 10000, {
        operation: `${method} ${endpoint}`
      });
    }
  }

  trackUserAction(action: string, success: boolean, context?: Record<string, any>): void {
    if (!success) {
      this.reportError({
        error_type: 'UserActionFailure',
        error_message: `User action ${action} failed`,
        severity: 'low',
        category: 'user_input',
        operation: action,
        context_data: context
      });
    }
  }
}

// Create and export singleton instance
export const errorTrackingService = new ErrorTrackingService();
export default errorTrackingService;