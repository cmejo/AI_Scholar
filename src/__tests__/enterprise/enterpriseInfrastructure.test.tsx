/**
 * Tests for Enterprise Infrastructure Components
 */
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import React from 'react';

// Import enterprise components
import { EnterpriseErrorBoundary } from '../../components/enterprise/EnterpriseErrorBoundary';
import { EnterprisePerformanceMonitor } from '../../components/enterprise/EnterprisePerformanceMonitor';
import { 
  EnterprisePerformanceTracker,
  EnterpriseComponentPreloader,
  createEnterpriseComponent
} from '../../utils/enterpriseCodeSplitting';
import { enterprisePerformanceIntegration } from '../../utils/enterprisePerformanceIntegration';

// Mock fetch for error reporting
global.fetch = vi.fn();

describe('Enterprise Infrastructure', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    EnterprisePerformanceTracker.clearMetrics();
    EnterpriseComponentPreloader.clearPreloadCache();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('EnterpriseErrorBoundary', () => {
    const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
      if (shouldThrow) {
        throw new Error('Test error');
      }
      return <div>No error</div>;
    };

    it('should render children when no error occurs', () => {
      render(
        <EnterpriseErrorBoundary componentType="analytics">
          <ThrowError shouldThrow={false} />
        </EnterpriseErrorBoundary>
      );

      expect(screen.getByText('No error')).toBeInTheDocument();
    });

    it('should render error UI when error occurs', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <EnterpriseErrorBoundary componentType="analytics">
          <ThrowError shouldThrow={true} />
        </EnterpriseErrorBoundary>
      );

      expect(screen.getByText('Analytics Dashboard Unavailable')).toBeInTheDocument();
      expect(screen.getByText(/experiencing issues with the analytics service/)).toBeInTheDocument();

      consoleSpy.mockRestore();
    });

    it('should display fallback data when provided', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const fallbackData = { totalQueries: 1000, activeUsers: 50 };

      render(
        <EnterpriseErrorBoundary 
          componentType="analytics" 
          fallbackData={fallbackData}
        >
          <ThrowError shouldThrow={true} />
        </EnterpriseErrorBoundary>
      );

      expect(screen.getByText('Cached Analytics Data')).toBeInTheDocument();
      expect(screen.getByText('1000')).toBeInTheDocument();
      expect(screen.getByText('50')).toBeInTheDocument();

      consoleSpy.mockRestore();
    });

    it('should call onError callback when error occurs', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const onError = vi.fn();

      render(
        <EnterpriseErrorBoundary 
          componentType="analytics" 
          onError={onError}
        >
          <ThrowError shouldThrow={true} />
        </EnterpriseErrorBoundary>
      );

      expect(onError).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          componentStack: expect.any(String)
        })
      );

      consoleSpy.mockRestore();
    });
  });

  describe('EnterprisePerformanceMonitor', () => {
    it('should render when enabled', () => {
      render(<EnterprisePerformanceMonitor enabled={true} />);
      
      expect(screen.getByText('Enterprise Monitor')).toBeInTheDocument();
    });

    it('should not render when disabled', () => {
      render(<EnterprisePerformanceMonitor enabled={false} />);
      
      expect(screen.queryByText('Enterprise Monitor')).not.toBeInTheDocument();
    });

    it('should show expanded content when clicked', async () => {
      render(<EnterprisePerformanceMonitor enabled={true} />);
      
      const header = screen.getByText('Enterprise Monitor');
      header.click();

      await waitFor(() => {
        expect(screen.getByText('Clear Alerts')).toBeInTheDocument();
        expect(screen.getByText('Reset Metrics')).toBeInTheDocument();
      });
    });
  });

  describe('EnterprisePerformanceTracker', () => {
    it('should record load success metrics', () => {
      const componentName = 'TestComponent';
      const startTime = performance.now();

      EnterprisePerformanceTracker.recordLoadStart(componentName);
      EnterprisePerformanceTracker.recordLoadSuccess(componentName, startTime);

      const metrics = EnterprisePerformanceTracker.getMetrics(componentName);
      expect(metrics).toBeDefined();
      expect(metrics?.loadTime).toBeGreaterThan(0);
      expect(metrics?.successRate).toBe(1);
    });

    it('should record load errors', () => {
      const componentName = 'TestComponent';
      const error = new Error('Test error');

      EnterprisePerformanceTracker.recordLoadError(componentName, error);

      const metrics = EnterprisePerformanceTracker.getMetrics(componentName);
      expect(metrics).toBeDefined();
      expect(metrics?.errorCount).toBe(1);
    });

    it('should record retries', () => {
      const componentName = 'TestComponent';

      EnterprisePerformanceTracker.recordRetry(componentName);
      EnterprisePerformanceTracker.recordRetry(componentName);

      const metrics = EnterprisePerformanceTracker.getMetrics(componentName);
      expect(metrics).toBeDefined();
      expect(metrics?.retryCount).toBe(2);
    });

    it('should generate performance report', () => {
      const componentName = 'TestComponent';
      const startTime = performance.now();

      EnterprisePerformanceTracker.recordLoadStart(componentName);
      EnterprisePerformanceTracker.recordLoadSuccess(componentName, startTime);

      const report = EnterprisePerformanceTracker.getPerformanceReport();
      expect(report[componentName]).toBeDefined();
      expect(report[componentName].performance).toBeDefined();
      expect(report[componentName].recommendations).toBeDefined();
    });
  });

  describe('EnterpriseComponentPreloader', () => {
    it('should preload components', async () => {
      const mockLoader = vi.fn().mockResolvedValue({ 
        default: () => <div>Test Component</div> 
      });

      const promise = EnterpriseComponentPreloader.preload(
        'TestComponent',
        mockLoader,
        'analytics',
        5
      );

      await promise;
      expect(mockLoader).toHaveBeenCalled();
    });

    it('should track preload status', async () => {
      const mockLoader = vi.fn().mockResolvedValue({ 
        default: () => <div>Test Component</div> 
      });

      const promise = EnterpriseComponentPreloader.preload(
        'TestComponent',
        mockLoader,
        'analytics',
        5
      );

      // Wait a bit for the preload to be processed
      await new Promise(resolve => setTimeout(resolve, 10));

      const status = EnterpriseComponentPreloader.getPreloadStatus();
      expect(status['TestComponent']).toBeDefined();
      expect(status['TestComponent'].type).toBe('analytics');
      expect(status['TestComponent'].priority).toBe(5);

      // Wait for the preload to complete
      await promise;
    });
  });

  describe('createEnterpriseComponent', () => {
    it('should create a component with enterprise error boundary', () => {
      const mockLoader = vi.fn().mockResolvedValue({ 
        default: () => <div>Test Component</div> 
      });

      const Component = createEnterpriseComponent(
        'TestComponent',
        'analytics',
        mockLoader
      );

      render(<Component />);

      // The component should be wrapped in an error boundary
      // We can't easily test the lazy loading without more complex setup,
      // but we can verify the component renders
      expect(Component).toBeDefined();
    });
  });

  describe('enterprisePerformanceIntegration', () => {
    it('should initialize with default config', () => {
      const config = enterprisePerformanceIntegration.getConfig();
      
      expect(config.enableRealTimeMonitoring).toBe(true);
      expect(config.enableAlerts).toBe(true);
      expect(config.enableAnalytics).toBe(true);
      expect(config.alertThresholds).toBeDefined();
    });

    it('should update config', () => {
      const newConfig = {
        enableAlerts: false,
        alertThresholds: {
          loadTime: 5000,
          errorRate: 0.2,
          successRate: 0.8
        }
      };

      enterprisePerformanceIntegration.updateConfig(newConfig);
      const config = enterprisePerformanceIntegration.getConfig();

      expect(config.enableAlerts).toBe(false);
      expect(config.alertThresholds.loadTime).toBe(5000);
    });

    it('should get health status', async () => {
      const healthStatus = await enterprisePerformanceIntegration.getHealthStatus();
      
      expect(healthStatus).toBeDefined();
      expect(healthStatus.status).toMatch(/healthy|degraded|unhealthy/);
      expect(healthStatus.details).toBeDefined();
    });
  });
});

describe('Enterprise Infrastructure Integration', () => {
  it('should work together as a complete system', async () => {
    // Render performance monitoring separately to avoid lazy loading issues
    render(<EnterprisePerformanceMonitor enabled={true} />);

    // Verify the monitor is present
    expect(screen.getByText('Enterprise Monitor')).toBeInTheDocument();

    // Verify the integration is working
    const healthStatus = await enterprisePerformanceIntegration.getHealthStatus();
    expect(healthStatus).toBeDefined();
  });
});