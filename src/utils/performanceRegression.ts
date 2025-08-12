/**
 * Performance regression detection system
 */

interface PerformanceBaseline {
  componentName: string;
  averageRenderTime: number;
  p95RenderTime: number;
  bundleSize: number;
  timestamp: number;
  version: string;
}

interface RegressionAlert {
  type: 'render_time' | 'bundle_size' | 'memory_usage';
  severity: 'low' | 'medium' | 'high' | 'critical';
  componentName?: string;
  currentValue: number;
  baselineValue: number;
  threshold: number;
  message: string;
  timestamp: number;
}

interface PerformanceBudget {
  maxBundleSize: number; // in bytes
  maxRenderTime: number; // in milliseconds
  maxMemoryUsage: number; // in MB
  regressionThreshold: number; // percentage increase that triggers alert
}

class PerformanceRegressionDetector {
  private baselines: Map<string, PerformanceBaseline> = new Map();
  private alerts: RegressionAlert[] = [];
  private budget: PerformanceBudget;

  constructor(budget: PerformanceBudget) {
    this.budget = budget;
    this.loadBaselines();
  }

  /**
   * Set performance baseline for a component
   */
  setBaseline(baseline: PerformanceBaseline): void {
    this.baselines.set(baseline.componentName, baseline);
    this.saveBaselines();
  }

  /**
   * Check for performance regressions
   */
  checkRegression(
    componentName: string,
    currentMetrics: {
      averageRenderTime: number;
      p95RenderTime: number;
      bundleSize?: number;
    }
  ): RegressionAlert[] {
    const baseline = this.baselines.get(componentName);
    if (!baseline) {
      console.warn(`No baseline found for component: ${componentName}`);
      return [];
    }

    const alerts: RegressionAlert[] = [];

    // Check render time regression
    const renderTimeIncrease = 
      (currentMetrics.averageRenderTime - baseline.averageRenderTime) / baseline.averageRenderTime;

    if (renderTimeIncrease > this.budget.regressionThreshold / 100) {
      const severity = this.calculateSeverity(renderTimeIncrease, 'render_time');
      alerts.push({
        type: 'render_time',
        severity,
        componentName,
        currentValue: currentMetrics.averageRenderTime,
        baselineValue: baseline.averageRenderTime,
        threshold: this.budget.regressionThreshold,
        message: `Render time increased by ${(renderTimeIncrease * 100).toFixed(1)}% for ${componentName}`,
        timestamp: Date.now(),
      });
    }

    // Check bundle size regression (if provided)
    if (currentMetrics.bundleSize && baseline.bundleSize) {
      const bundleSizeIncrease = 
        (currentMetrics.bundleSize - baseline.bundleSize) / baseline.bundleSize;

      if (bundleSizeIncrease > this.budget.regressionThreshold / 100) {
        const severity = this.calculateSeverity(bundleSizeIncrease, 'bundle_size');
        alerts.push({
          type: 'bundle_size',
          severity,
          componentName,
          currentValue: currentMetrics.bundleSize,
          baselineValue: baseline.bundleSize,
          threshold: this.budget.regressionThreshold,
          message: `Bundle size increased by ${(bundleSizeIncrease * 100).toFixed(1)}% for ${componentName}`,
          timestamp: Date.now(),
        });
      }
    }

    // Store alerts
    this.alerts.push(...alerts);
    
    return alerts;
  }

  /**
   * Check if current metrics exceed performance budget
   */
  checkBudget(metrics: {
    bundleSize: number;
    averageRenderTime: number;
    memoryUsage?: number;
  }): RegressionAlert[] {
    const alerts: RegressionAlert[] = [];

    // Check bundle size budget
    if (metrics.bundleSize > this.budget.maxBundleSize) {
      alerts.push({
        type: 'bundle_size',
        severity: 'high',
        currentValue: metrics.bundleSize,
        baselineValue: this.budget.maxBundleSize,
        threshold: 0,
        message: `Bundle size (${this.formatBytes(metrics.bundleSize)}) exceeds budget (${this.formatBytes(this.budget.maxBundleSize)})`,
        timestamp: Date.now(),
      });
    }

    // Check render time budget
    if (metrics.averageRenderTime > this.budget.maxRenderTime) {
      alerts.push({
        type: 'render_time',
        severity: 'high',
        currentValue: metrics.averageRenderTime,
        baselineValue: this.budget.maxRenderTime,
        threshold: 0,
        message: `Average render time (${metrics.averageRenderTime.toFixed(2)}ms) exceeds budget (${this.budget.maxRenderTime}ms)`,
        timestamp: Date.now(),
      });
    }

    // Check memory usage budget (if provided)
    if (metrics.memoryUsage && metrics.memoryUsage > this.budget.maxMemoryUsage) {
      alerts.push({
        type: 'memory_usage',
        severity: 'medium',
        currentValue: metrics.memoryUsage,
        baselineValue: this.budget.maxMemoryUsage,
        threshold: 0,
        message: `Memory usage (${metrics.memoryUsage.toFixed(1)}MB) exceeds budget (${this.budget.maxMemoryUsage}MB)`,
        timestamp: Date.now(),
      });
    }

    this.alerts.push(...alerts);
    return alerts;
  }

  /**
   * Get all alerts
   */
  getAlerts(severity?: RegressionAlert['severity']): RegressionAlert[] {
    if (severity) {
      return this.alerts.filter(alert => alert.severity === severity);
    }
    return [...this.alerts];
  }

  /**
   * Clear alerts
   */
  clearAlerts(): void {
    this.alerts = [];
  }

  /**
   * Get performance trend analysis
   */
  getTrendAnalysis(componentName: string, recentMetrics: Array<{
    timestamp: number;
    averageRenderTime: number;
    bundleSize?: number;
  }>): {
    trend: 'improving' | 'stable' | 'degrading';
    confidence: number;
    recommendation: string;
  } {
    if (recentMetrics.length < 3) {
      return {
        trend: 'stable',
        confidence: 0,
        recommendation: 'Need more data points for trend analysis',
      };
    }

    // Calculate trend using linear regression
    const renderTimes = recentMetrics.map(m => m.averageRenderTime);
    const trend = this.calculateTrend(renderTimes);
    
    let trendDirection: 'improving' | 'stable' | 'degrading';
    let recommendation: string;

    if (trend > 0.1) {
      trendDirection = 'degrading';
      recommendation = `Performance is degrading for ${componentName}. Consider optimization.`;
    } else if (trend < -0.1) {
      trendDirection = 'improving';
      recommendation = `Performance is improving for ${componentName}. Good work!`;
    } else {
      trendDirection = 'stable';
      recommendation = `Performance is stable for ${componentName}.`;
    }

    return {
      trend: trendDirection,
      confidence: Math.min(Math.abs(trend) * 10, 1),
      recommendation,
    };
  }

  /**
   * Generate performance report
   */
  generateReport(): {
    summary: {
      totalAlerts: number;
      criticalAlerts: number;
      componentsMonitored: number;
      budgetViolations: number;
    };
    alerts: RegressionAlert[];
    recommendations: string[];
  } {
    const criticalAlerts = this.alerts.filter(a => a.severity === 'critical').length;
    const budgetViolations = this.alerts.filter(a => a.threshold === 0).length;
    
    const recommendations: string[] = [];
    
    // Generate recommendations based on alerts
    const renderTimeAlerts = this.alerts.filter(a => a.type === 'render_time');
    const bundleSizeAlerts = this.alerts.filter(a => a.type === 'bundle_size');
    
    if (renderTimeAlerts.length > 0) {
      recommendations.push('Consider implementing React.memo, useMemo, or useCallback for slow components');
      recommendations.push('Review component re-render patterns and optimize dependencies');
    }
    
    if (bundleSizeAlerts.length > 0) {
      recommendations.push('Implement code splitting and lazy loading for large components');
      recommendations.push('Review and remove unused dependencies');
      recommendations.push('Consider using dynamic imports for non-critical features');
    }

    return {
      summary: {
        totalAlerts: this.alerts.length,
        criticalAlerts,
        componentsMonitored: this.baselines.size,
        budgetViolations,
      },
      alerts: this.alerts,
      recommendations,
    };
  }

  /**
   * Calculate severity based on regression percentage
   */
  private calculateSeverity(
    regressionPercentage: number, 
    type: RegressionAlert['type']
  ): RegressionAlert['severity'] {
    const percentage = regressionPercentage * 100;
    
    if (type === 'render_time') {
      if (percentage > 100) return 'critical';
      if (percentage > 50) return 'high';
      if (percentage > 25) return 'medium';
      return 'low';
    } else if (type === 'bundle_size') {
      if (percentage > 50) return 'critical';
      if (percentage > 25) return 'high';
      if (percentage > 10) return 'medium';
      return 'low';
    }
    
    return 'medium';
  }

  /**
   * Calculate trend using simple linear regression
   */
  private calculateTrend(values: number[]): number {
    const n = values.length;
    const x = Array.from({ length: n }, (_, i) => i);
    const y = values;
    
    const sumX = x.reduce((a, b) => a + b, 0);
    const sumY = y.reduce((a, b) => a + b, 0);
    const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
    const sumXX = x.reduce((sum, xi) => sum + xi * xi, 0);
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    return slope;
  }

  /**
   * Format bytes to human readable format
   */
  private formatBytes(bytes: number): string {
    const KB = 1024;
    const MB = KB * 1024;
    
    if (bytes >= MB) {
      return `${(bytes / MB).toFixed(2)} MB`;
    } else if (bytes >= KB) {
      return `${(bytes / KB).toFixed(2)} KB`;
    } else {
      return `${bytes} B`;
    }
  }

  /**
   * Load baselines from localStorage
   */
  private loadBaselines(): void {
    try {
      const stored = localStorage.getItem('performance-baselines');
      if (stored) {
        const baselines = JSON.parse(stored);
        this.baselines = new Map(Object.entries(baselines));
      }
    } catch (error) {
      console.warn('Failed to load performance baselines:', error);
    }
  }

  /**
   * Save baselines to localStorage
   */
  private saveBaselines(): void {
    try {
      const baselines = Object.fromEntries(this.baselines);
      localStorage.setItem('performance-baselines', JSON.stringify(baselines));
    } catch (error) {
      console.warn('Failed to save performance baselines:', error);
    }
  }
}

// Default performance budget
export const DEFAULT_PERFORMANCE_BUDGET: PerformanceBudget = {
  maxBundleSize: 2 * 1024 * 1024, // 2MB
  maxRenderTime: 16, // 16ms (60fps)
  maxMemoryUsage: 100, // 100MB
  regressionThreshold: 20, // 20% increase triggers alert
};

// Create singleton instance
export const performanceRegressionDetector = new PerformanceRegressionDetector(
  DEFAULT_PERFORMANCE_BUDGET
);

// Export types
export type { PerformanceBaseline, PerformanceBudget, RegressionAlert };
