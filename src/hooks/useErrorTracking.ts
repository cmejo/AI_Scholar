import { useCallback, useEffect } from 'react';
import { errorTrackingService } from '../services/errorTrackingService';

interface UseErrorTrackingOptions {
  featureName?: string;
  userId?: string;
  enableAutoTracking?: boolean;
}

interface ErrorTrackingHook {
  reportError: (error: Error, context?: Record<string, any>) => Promise<string | null>;
  reportNetworkError: (url: string, status: number, statusText: string, context?: Record<string, any>) => Promise<string | null>;
  reportPerformanceIssue: (metric: string, value: number, threshold: number, context?: Record<string, any>) => Promise<string | null>;
  submitFeedback: (feedback: {
    type: 'bug_report' | 'feature_request' | 'general';
    title: string;
    description: string;
    severity?: 'low' | 'medium' | 'high' | 'critical';
    email?: string;
  }) => Promise<string | null>;
  trackFeatureUsage: (operation: string, success: boolean, duration?: number) => void;
  trackApiCall: (endpoint: string, method: string, status: number, duration: number) => void;
  trackUserAction: (action: string, success: boolean, context?: Record<string, any>) => void;
}

export const useErrorTracking = (options: UseErrorTrackingOptions = {}): ErrorTrackingHook => {
  const { featureName, userId, enableAutoTracking = true } = options;

  useEffect(() => {
    if (userId) {
      errorTrackingService.setUserId(userId);
    }
  }, [userId]);

  const reportError = useCallback(async (error: Error, context?: Record<string, any>) => {
    return errorTrackingService.reportJavaScriptError(error, {
      feature_name: featureName,
      context_data: context
    });
  }, [featureName]);

  const reportNetworkError = useCallback(async (
    url: string, 
    status: number, 
    statusText: string, 
    context?: Record<string, any>
  ) => {
    return errorTrackingService.reportNetworkError(url, status, statusText, {
      feature_name: featureName,
      context_data: context
    });
  }, [featureName]);

  const reportPerformanceIssue = useCallback(async (
    metric: string, 
    value: number, 
    threshold: number, 
    context?: Record<string, any>
  ) => {
    return errorTrackingService.reportPerformanceIssue(metric, value, threshold, {
      feature_name: featureName,
      context_data: context
    });
  }, [featureName]);

  const submitFeedback = useCallback(async (feedback: {
    type: 'bug_report' | 'feature_request' | 'general';
    title: string;
    description: string;
    severity?: 'low' | 'medium' | 'high' | 'critical';
    email?: string;
  }) => {
    return errorTrackingService.submitUserFeedback({
      feedback_type: feedback.type,
      title: feedback.title,
      description: feedback.description,
      severity: feedback.severity || 'medium',
      user_email: feedback.email,
      category: featureName,
      metadata: {
        feature_name: featureName
      }
    });
  }, [featureName]);

  const trackFeatureUsage = useCallback((operation: string, success: boolean, duration?: number) => {
    if (enableAutoTracking) {
      errorTrackingService.trackFeatureUsage(featureName || 'unknown', operation, success, duration);
    }
  }, [featureName, enableAutoTracking]);

  const trackApiCall = useCallback((endpoint: string, method: string, status: number, duration: number) => {
    if (enableAutoTracking) {
      errorTrackingService.trackApiCall(endpoint, method, status, duration);
    }
  }, [enableAutoTracking]);

  const trackUserAction = useCallback((action: string, success: boolean, context?: Record<string, any>) => {
    if (enableAutoTracking) {
      errorTrackingService.trackUserAction(action, success, {
        ...context,
        feature_name: featureName
      });
    }
  }, [featureName, enableAutoTracking]);

  return {
    reportError,
    reportNetworkError,
    reportPerformanceIssue,
    submitFeedback,
    trackFeatureUsage,
    trackApiCall,
    trackUserAction
  };
};

export default useErrorTracking;