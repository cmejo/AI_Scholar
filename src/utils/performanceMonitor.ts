/**
 * Performance monitoring utilities for React components
 */

import React from 'react';

interface PerformanceMetrics {
  componentName: string;
  renderTime: number;
  timestamp: number;
  props?: Record<string, unknown>;
}

interface BundleMetrics {
  totalSize: number;
  chunkSizes: Record<string, number>;
  loadTimes: Record<string, number>;
}

class PerformanceMonitor {
  private metrics: PerformanceMetrics[] = [];
  private renderStartTimes = new Map<string, number>();
  private bundleMetrics: BundleMetrics | null = null;

  /**
   * Start measuring component render time
   */
  startRender(componentName: string): void {
    this.renderStartTimes.set(componentName, performance.now());
  }

  /**
   * End measuring component render time
   */
  endRender(componentName: string, props?: Record<string, unknown>): void {
    const startTime = this.renderStartTimes.get(componentName);
    if (startTime) {
      const renderTime = performance.now() - startTime;
      this.metrics.push({
        componentName,
        renderTime,
        timestamp: Date.now(),
        props,
      });
      this.renderStartTimes.delete(componentName);

      // Log slow renders in development
      if (process.env.NODE_ENV === 'development' && renderTime > 16) {
        console.warn(`Slow render detected: ${componentName} took ${renderTime.toFixed(2)}ms`);
      }
    }
  }

  /**
   * Get performance metrics for a specific component
   */
  getComponentMetrics(componentName: string): PerformanceMetrics[] {
    return this.metrics.filter(metric => metric.componentName === componentName);
  }

  /**
   * Get average render time for a component
   */
  getAverageRenderTime(componentName: string): number {
    const componentMetrics = this.getComponentMetrics(componentName);
    if (componentMetrics.length === 0) return 0;
    
    const totalTime = componentMetrics.reduce((sum, metric) => sum + metric.renderTime, 0);
    return totalTime / componentMetrics.length;
  }

  /**
   * Get all performance metrics
   */
  getAllMetrics(): PerformanceMetrics[] {
    return [...this.metrics];
  }

  /**
   * Clear all metrics
   */
  clearMetrics(): void {
    this.metrics = [];
    this.renderStartTimes.clear();
  }

  /**
   * Monitor bundle size and load times
   */
  setBundleMetrics(metrics: BundleMetrics): void {
    this.bundleMetrics = metrics;
  }

  /**
   * Get bundle metrics
   */
  getBundleMetrics(): BundleMetrics | null {
    return this.bundleMetrics;
  }

  /**
   * Generate performance report
   */
  generateReport(): {
    componentMetrics: Record<string, {
      averageRenderTime: number;
      totalRenders: number;
      slowRenders: number;
    }>;
    bundleMetrics: BundleMetrics | null;
    recommendations: string[];
  } {
    const componentMetrics: Record<string, {
      averageRenderTime: number;
      totalRenders: number;
      slowRenders: number;
    }> = {};

    const recommendations: string[] = [];

    // Analyze component metrics
    const componentNames = [...new Set(this.metrics.map(m => m.componentName))];
    
    componentNames.forEach(name => {
      const metrics = this.getComponentMetrics(name);
      const averageRenderTime = this.getAverageRenderTime(name);
      const slowRenders = metrics.filter(m => m.renderTime > 16).length;

      componentMetrics[name] = {
        averageRenderTime,
        totalRenders: metrics.length,
        slowRenders,
      };

      // Generate recommendations
      if (averageRenderTime > 16) {
        recommendations.push(`Consider optimizing ${name} - average render time: ${averageRenderTime.toFixed(2)}ms`);
      }

      if (slowRenders > metrics.length * 0.1) {
        recommendations.push(`${name} has frequent slow renders (${slowRenders}/${metrics.length})`);
      }
    });

    // Bundle size recommendations
    if (this.bundleMetrics) {
      if (this.bundleMetrics.totalSize > 2 * 1024 * 1024) { // 2MB
        recommendations.push('Bundle size is large (>2MB) - consider code splitting');
      }

      Object.entries(this.bundleMetrics.chunkSizes).forEach(([chunk, size]) => {
        if (size > 500 * 1024) { // 500KB
          recommendations.push(`Chunk ${chunk} is large (${(size / 1024).toFixed(0)}KB) - consider splitting`);
        }
      });
    }

    return {
      componentMetrics,
      bundleMetrics: this.bundleMetrics,
      recommendations,
    };
  }
}

// Create singleton instance
export const performanceMonitor = new PerformanceMonitor();

/**
 * React hook for monitoring component performance
 */
export function usePerformanceMonitor(componentName: string, props?: Record<string, unknown>) {
  React.useEffect(() => {
    performanceMonitor.startRender(componentName);
    return () => {
      performanceMonitor.endRender(componentName, props);
    };
  });
}

/**
 * Higher-order component for performance monitoring
 */
export function withPerformanceMonitoring<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  componentName?: string
) {
  const displayName = componentName || WrappedComponent.displayName || WrappedComponent.name || 'Component';
  
  const MonitoredComponent = React.forwardRef<any, P>((props, ref) => {
    usePerformanceMonitor(displayName, props as Record<string, unknown>);
    
    return React.createElement(WrappedComponent, { ...props, ref });
  });

  MonitoredComponent.displayName = `withPerformanceMonitoring(${displayName})`;
  
  return MonitoredComponent;
}

/**
 * Performance profiler component
 */
export const PerformanceProfiler: React.FC<{
  id: string;
  children: React.ReactNode;
  onRender?: (id: string, phase: 'mount' | 'update', actualDuration: number) => void;
}> = ({ id, children, onRender }) => {
  const handleRender = React.useCallback((
    id: string,
    phase: 'mount' | 'update',
    actualDuration: number,
    baseDuration: number,
    startTime: number,
    commitTime: number
  ) => {
    performanceMonitor.endRender(id);
    
    if (onRender) {
      onRender(id, phase, actualDuration);
    }

    // Log performance in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`${id} ${phase}:`, {
        actualDuration: actualDuration.toFixed(2),
        baseDuration: baseDuration.toFixed(2),
        startTime: startTime.toFixed(2),
        commitTime: commitTime.toFixed(2),
      });
    }
  }, [onRender]);

  React.useEffect(() => {
    performanceMonitor.startRender(id);
  });

  return React.createElement(
    React.Profiler,
    { id, onRender: handleRender },
    children
  );
};

// Export types
export type { BundleMetrics, PerformanceMetrics };
