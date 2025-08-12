/**
 * Unit tests for performance monitoring utilities
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
    analyzePerformanceMetrics,
    createPerformanceBudget,
    createPerformanceMonitor,
    detectPerformanceRegressions,
    generatePerformanceReport,
    measureRenderTime,
    monitorNetworkRequests,
    trackMemoryUsage
} from '../performanceMonitor';

// Mock Performance API
const mockPerformance = {
  now: vi.fn(),
  mark: vi.fn(),
  measure: vi.fn(),
  getEntriesByType: vi.fn(),
  getEntriesByName: vi.fn(),
  clearMarks: vi.fn(),
  clearMeasures: vi.fn(),
  memory: {
    usedJSHeapSize: 10000000,
    totalJSHeapSize: 20000000,
    jsHeapSizeLimit: 100000000
  }
};

global.performance = mockPerformance as any;

describe('Performance Monitor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPerformance.now.mockReturnValue(1000);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('createPerformanceMonitor', () => {
    it('should create performance monitor with default config', () => {
      const monitor = createPerformanceMonitor();

      expect(monitor).toHaveProperty('start');
      expect(monitor).toHaveProperty('end');
      expect(monitor).toHaveProperty('getMetrics');
      expect(monitor).toHaveProperty('reset');
    });

    it('should track performance metrics', () => {
      const monitor = createPerformanceMonitor();

      monitor.start('test-operation');
      mockPerformance.now.mockReturnValue(1100);
      monitor.end('test-operation');

      const metrics = monitor.getMetrics();
      expect(metrics['test-operation']).toEqual({
        duration: 100,
        startTime: 1000,
        endTime: 1100
      });
    });

    it('should handle nested operations', () => {
      const monitor = createPerformanceMonitor();

      monitor.start('outer-operation');
      monitor.start('inner-operation');
      
      mockPerformance.now.mockReturnValue(1050);
      monitor.end('inner-operation');
      
      mockPerformance.now.mockReturnValue(1200);
      monitor.end('outer-operation');

      const metrics = monitor.getMetrics();
      expect(metrics['inner-operation'].duration).toBe(50);
      expect(metrics['outer-operation'].duration).toBe(200);
    });

    it('should support custom thresholds', () => {
      const onThresholdExceeded = vi.fn();
      const monitor = createPerformanceMonitor({
        thresholds: { 'slow-operation': 50 },
        onThresholdExceeded
      });

      monitor.start('slow-operation');
      mockPerformance.now.mockReturnValue(1100);
      monitor.end('slow-operation');

      expect(onThresholdExceeded).toHaveBeenCalledWith('slow-operation', 100, 50);
    });

    it('should reset metrics', () => {
      const monitor = createPerformanceMonitor();

      monitor.start('test');
      monitor.end('test');
      monitor.reset();

      const metrics = monitor.getMetrics();
      expect(Object.keys(metrics)).toHaveLength(0);
    });
  });

  describe('measureRenderTime', () => {
    it('should measure React component render time', async () => {
      const mockComponent = vi.fn().mockReturnValue('rendered');
      const mockProps = { prop1: 'value1' };

      mockPerformance.now
        .mockReturnValueOnce(1000)
        .mockReturnValueOnce(1050);

      const result = await measureRenderTime('TestComponent', mockComponent, mockProps);

      expect(result).toEqual({
        component: 'TestComponent',
        renderTime: 50,
        props: mockProps,
        result: 'rendered'
      });
      expect(mockComponent).toHaveBeenCalledWith(mockProps);
    });

    it('should handle render errors', async () => {
      const mockComponent = vi.fn().mockImplementation(() => {
        throw new Error('Render error');
      });

      await expect(measureRenderTime('ErrorComponent', mockComponent))
        .rejects.toThrow('Render error');
    });

    it('should measure async component rendering', async () => {
      const mockAsyncComponent = vi.fn().mockResolvedValue('async rendered');

      mockPerformance.now
        .mockReturnValueOnce(1000)
        .mockReturnValueOnce(1100);

      const result = await measureRenderTime('AsyncComponent', mockAsyncComponent);

      expect(result.renderTime).toBe(100);
      expect(result.result).toBe('async rendered');
    });
  });

  describe('trackMemoryUsage', () => {
    it('should track memory usage over time', () => {
      const tracker = trackMemoryUsage();

      const snapshot1 = tracker.takeSnapshot();
      expect(snapshot1).toEqual({
        timestamp: expect.any(Number),
        usedJSHeapSize: 10000000,
        totalJSHeapSize: 20000000,
        jsHeapSizeLimit: 100000000,
        usagePercentage: 50
      });
    });

    it('should detect memory leaks', () => {
      const onMemoryLeak = vi.fn();
      const tracker = trackMemoryUsage({ 
        leakThreshold: 5000000,
        onMemoryLeak 
      });

      // Simulate memory increase
      mockPerformance.memory.usedJSHeapSize = 16000000;
      tracker.takeSnapshot();

      expect(onMemoryLeak).toHaveBeenCalledWith({
        increase: 6000000,
        threshold: 5000000,
        current: 16000000
      });
    });

    it('should generate memory usage report', () => {
      const tracker = trackMemoryUsage();

      tracker.takeSnapshot();
      mockPerformance.memory.usedJSHeapSize = 12000000;
      tracker.takeSnapshot();

      const report = tracker.getReport();

      expect(report.snapshots).toHaveLength(2);
      expect(report.trend).toBe('increasing');
      expect(report.maxUsage).toBe(12000000);
    });

    it('should handle missing memory API', () => {
      const originalMemory = mockPerformance.memory;
      delete (mockPerformance as any).memory;

      const tracker = trackMemoryUsage();
      const snapshot = tracker.takeSnapshot();

      expect(snapshot).toEqual({
        timestamp: expect.any(Number),
        usedJSHeapSize: 0,
        totalJSHeapSize: 0,
        jsHeapSizeLimit: 0,
        usagePercentage: 0
      });

      mockPerformance.memory = originalMemory;
    });
  });

  describe('monitorNetworkRequests', () => {
    it('should monitor fetch requests', async () => {
      const originalFetch = global.fetch;
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ data: 'test' })
      });
      global.fetch = mockFetch;

      const monitor = monitorNetworkRequests();
      
      mockPerformance.now
        .mockReturnValueOnce(1000)
        .mockReturnValueOnce(1200);

      await fetch('/api/test');

      const metrics = monitor.getMetrics();
      expect(metrics).toHaveLength(1);
      expect(metrics[0]).toEqual({
        url: '/api/test',
        method: 'GET',
        status: 200,
        duration: 200,
        timestamp: expect.any(Number)
      });

      global.fetch = originalFetch;
    });

    it('should track failed requests', async () => {
      const originalFetch = global.fetch;
      const mockFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404
      });
      global.fetch = mockFetch;

      const monitor = monitorNetworkRequests();
      
      await fetch('/api/notfound');

      const metrics = monitor.getMetrics();
      expect(metrics[0].status).toBe(404);
      expect(metrics[0].success).toBe(false);

      global.fetch = originalFetch;
    });

    it('should detect slow requests', async () => {
      const onSlowRequest = vi.fn();
      const originalFetch = global.fetch;
      const mockFetch = vi.fn().mockResolvedValue({ ok: true, status: 200 });
      global.fetch = mockFetch;

      const monitor = monitorNetworkRequests({
        slowRequestThreshold: 100,
        onSlowRequest
      });

      mockPerformance.now
        .mockReturnValueOnce(1000)
        .mockReturnValueOnce(1200); // 200ms duration

      await fetch('/api/slow');

      expect(onSlowRequest).toHaveBeenCalledWith({
        url: '/api/slow',
        duration: 200,
        threshold: 100
      });

      global.fetch = originalFetch;
    });
  });

  describe('analyzePerformanceMetrics', () => {
    it('should analyze performance metrics', () => {
      const metrics = {
        'component-render': { duration: 50, count: 10 },
        'api-call': { duration: 200, count: 5 },
        'slow-operation': { duration: 1000, count: 2 }
      };

      const analysis = analyzePerformanceMetrics(metrics);

      expect(analysis.slowestOperations).toContain('slow-operation');
      expect(analysis.averageDuration).toBe(250); // (50*10 + 200*5 + 1000*2) / 17
      expect(analysis.recommendations).toContain(
        expect.stringContaining('slow-operation is taking too long')
      );
    });

    it('should identify performance bottlenecks', () => {
      const metrics = {
        'frequent-operation': { duration: 10, count: 1000 },
        'rare-operation': { duration: 100, count: 1 }
      };

      const analysis = analyzePerformanceMetrics(metrics);

      expect(analysis.bottlenecks).toContain('frequent-operation');
      expect(analysis.recommendations).toContain(
        expect.stringContaining('frequent-operation is called very frequently')
      );
    });

    it('should calculate performance score', () => {
      const goodMetrics = {
        'fast-operation': { duration: 10, count: 5 }
      };

      const badMetrics = {
        'slow-operation': { duration: 2000, count: 10 }
      };

      const goodAnalysis = analyzePerformanceMetrics(goodMetrics);
      const badAnalysis = analyzePerformanceMetrics(badMetrics);

      expect(goodAnalysis.score).toBeGreaterThan(badAnalysis.score);
    });
  });

  describe('createPerformanceBudget', () => {
    it('should create performance budget with thresholds', () => {
      const budget = createPerformanceBudget({
        'component-render': 50,
        'api-request': 200,
        'page-load': 1000
      });

      expect(budget.check('component-render', 30)).toBe(true);
      expect(budget.check('component-render', 70)).toBe(false);
    });

    it('should track budget violations', () => {
      const onViolation = vi.fn();
      const budget = createPerformanceBudget({
        'slow-operation': 100
      }, { onViolation });

      budget.check('slow-operation', 150);

      expect(onViolation).toHaveBeenCalledWith({
        operation: 'slow-operation',
        actual: 150,
        budget: 100,
        violation: 50
      });
    });

    it('should generate budget report', () => {
      const budget = createPerformanceBudget({
        'operation-a': 100,
        'operation-b': 200
      });

      budget.check('operation-a', 80);
      budget.check('operation-a', 120);
      budget.check('operation-b', 150);

      const report = budget.getReport();

      expect(report.totalChecks).toBe(3);
      expect(report.violations).toBe(1);
      expect(report.compliance).toBe(2/3);
    });
  });

  describe('detectPerformanceRegressions', () => {
    it('should detect performance regressions', () => {
      const baseline = {
        'operation-a': { duration: 100, count: 10 },
        'operation-b': { duration: 200, count: 5 }
      };

      const current = {
        'operation-a': { duration: 150, count: 10 }, // 50% slower
        'operation-b': { duration: 190, count: 5 }   // 5% faster
      };

      const regressions = detectPerformanceRegressions(baseline, current);

      expect(regressions.regressions).toHaveLength(1);
      expect(regressions.regressions[0]).toEqual({
        operation: 'operation-a',
        baseline: 100,
        current: 150,
        regression: 50,
        percentage: 50
      });

      expect(regressions.improvements).toHaveLength(1);
      expect(regressions.improvements[0].operation).toBe('operation-b');
    });

    it('should handle missing baseline data', () => {
      const baseline = {};
      const current = {
        'new-operation': { duration: 100, count: 5 }
      };

      const regressions = detectPerformanceRegressions(baseline, current);

      expect(regressions.newOperations).toContain('new-operation');
      expect(regressions.regressions).toHaveLength(0);
    });

    it('should apply regression threshold', () => {
      const baseline = {
        'operation': { duration: 100, count: 10 }
      };

      const current = {
        'operation': { duration: 105, count: 10 } // 5% slower
      };

      const regressions = detectPerformanceRegressions(baseline, current, {
        threshold: 10 // 10% threshold
      });

      expect(regressions.regressions).toHaveLength(0); // Below threshold
    });
  });

  describe('generatePerformanceReport', () => {
    it('should generate comprehensive performance report', () => {
      const metrics = {
        'render': { duration: 50, count: 100 },
        'api': { duration: 200, count: 20 }
      };

      const memorySnapshots = [
        { timestamp: 1000, usedJSHeapSize: 10000000 },
        { timestamp: 2000, usedJSHeapSize: 12000000 }
      ];

      const networkMetrics = [
        { url: '/api/data', duration: 150, status: 200 }
      ];

      const report = generatePerformanceReport({
        metrics,
        memorySnapshots,
        networkMetrics
      });

      expect(report).toEqual({
        timestamp: expect.any(String),
        summary: {
          totalOperations: 120,
          averageDuration: expect.any(Number),
          slowestOperation: 'api',
          memoryUsage: 12000000,
          networkRequests: 1
        },
        details: {
          operations: metrics,
          memory: memorySnapshots,
          network: networkMetrics
        },
        analysis: expect.any(Object),
        recommendations: expect.any(Array),
        score: expect.any(Number)
      });
    });

    it('should include performance trends', () => {
      const previousReport = {
        summary: { averageDuration: 100 }
      };

      const currentMetrics = {
        'operation': { duration: 120, count: 10 }
      };

      const report = generatePerformanceReport({
        metrics: currentMetrics,
        previousReport
      });

      expect(report.trends).toEqual({
        averageDuration: {
          previous: 100,
          current: 120,
          change: 20,
          percentage: 20
        }
      });
    });

    it('should generate actionable recommendations', () => {
      const metrics = {
        'slow-render': { duration: 500, count: 50 },
        'frequent-api': { duration: 100, count: 1000 }
      };

      const report = generatePerformanceReport({ metrics });

      expect(report.recommendations).toContain(
        expect.stringContaining('slow-render')
      );
      expect(report.recommendations).toContain(
        expect.stringContaining('frequent-api')
      );
    });
  });
});