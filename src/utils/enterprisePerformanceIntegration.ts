/**
 * Enterprise Performance Integration - Connects performance monitoring with enterprise services
 */

interface EnterprisePerformanceConfig {
  enableRealTimeMonitoring: boolean;
  enableAlerts: boolean;
  enableAnalytics: boolean;
  alertThresholds: {
    loadTime: number;
    errorRate: number;
    successRate: number;
  };
  reportingInterval: number;
}

interface PerformanceAlert {
  id: string;
  type: 'performance' | 'error' | 'availability';
  severity: 'low' | 'medium' | 'high' | 'critical';
  componentName: string;
  message: string;
  timestamp: Date;
  metrics: Record<string, any>;
}

interface PerformanceReport {
  timestamp: Date;
  overallHealth: 'excellent' | 'good' | 'fair' | 'poor';
  componentMetrics: Record<string, any>;
  alerts: PerformanceAlert[];
  recommendations: string[];
}

export class EnterprisePerformanceIntegration {
  private static instance: EnterprisePerformanceIntegration;
  private config: EnterprisePerformanceConfig;
  private alertCallbacks: Array<(alert: PerformanceAlert) => void> = [];
  private reportCallbacks: Array<(report: PerformanceReport) => void> = [];
  private monitoringInterval?: NodeJS.Timeout;
  private reportingInterval?: NodeJS.Timeout;

  private constructor() {
    this.config = {
      enableRealTimeMonitoring: true,
      enableAlerts: true,
      enableAnalytics: true,
      alertThresholds: {
        loadTime: 3000, // 3 seconds
        errorRate: 0.1, // 10%
        successRate: 0.9 // 90%
      },
      reportingInterval: 300000 // 5 minutes
    };
  }

  static getInstance(): EnterprisePerformanceIntegration {
    if (!EnterprisePerformanceIntegration.instance) {
      EnterprisePerformanceIntegration.instance = new EnterprisePerformanceIntegration();
    }
    return EnterprisePerformanceIntegration.instance;
  }

  initialize(config?: Partial<EnterprisePerformanceConfig>) {
    if (config) {
      this.config = { ...this.config, ...config };
    }

    if (this.config.enableRealTimeMonitoring) {
      this.startRealTimeMonitoring();
    }

    if (this.config.enableAnalytics) {
      this.startPerformanceReporting();
    }

    // Set up global error handling for enterprise components
    this.setupGlobalErrorHandling();

    console.log('🏢 Enterprise Performance Integration initialized');
  }

  private startRealTimeMonitoring() {
    this.monitoringInterval = setInterval(() => {
      this.checkPerformanceThresholds();
    }, 10000); // Check every 10 seconds
  }

  private startPerformanceReporting() {
    this.reportingInterval = setInterval(() => {
      this.generatePerformanceReport();
    }, this.config.reportingInterval);
  }

  private setupGlobalErrorHandling() {
    // Capture unhandled errors in enterprise components
    window.addEventListener('error', (event) => {
      if (event.filename?.includes('enterprise') || event.message?.includes('enterprise')) {
        this.handleEnterpriseError(event.error, 'global_error');
      }
    });

    // Capture unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      if (event.reason?.message?.includes('enterprise') || 
          event.reason?.stack?.includes('enterprise')) {
        this.handleEnterpriseError(event.reason, 'unhandled_rejection');
      }
    });
  }

  private async checkPerformanceThresholds() {
    try {
      // This would integrate with your existing performance tracking
      const { EnterprisePerformanceTracker } = await import('./enterpriseCodeSplitting');
      const metrics = EnterprisePerformanceTracker.getAllMetrics();

      Object.entries(metrics).forEach(([componentName, metric]) => {
        // Check load time threshold
        if (metric.averageLoadTime > this.config.alertThresholds.loadTime) {
          this.createAlert({
            type: 'performance',
            severity: metric.averageLoadTime > this.config.alertThresholds.loadTime * 2 ? 'high' : 'medium',
            componentName,
            message: `High load time: ${metric.averageLoadTime.toFixed(0)}ms`,
            metrics: { loadTime: metric.averageLoadTime }
          });
        }

        // Check success rate threshold
        if (metric.successRate < this.config.alertThresholds.successRate) {
          this.createAlert({
            type: 'availability',
            severity: metric.successRate < 0.5 ? 'critical' : 'high',
            componentName,
            message: `Low success rate: ${(metric.successRate * 100).toFixed(1)}%`,
            metrics: { successRate: metric.successRate }
          });
        }

        // Check error rate
        const errorRate = metric.errorCount / (metric.errorCount + 1); // Avoid division by zero
        if (errorRate > this.config.alertThresholds.errorRate) {
          this.createAlert({
            type: 'error',
            severity: errorRate > 0.5 ? 'critical' : 'high',
            componentName,
            message: `High error rate: ${(errorRate * 100).toFixed(1)}%`,
            metrics: { errorRate, errorCount: metric.errorCount }
          });
        }
      });
    } catch (error) {
      console.warn('Failed to check performance thresholds:', error);
    }
  }

  private createAlert(alertData: Omit<PerformanceAlert, 'id' | 'timestamp'>) {
    const alert: PerformanceAlert = {
      id: `alert_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`,
      timestamp: new Date(),
      ...alertData
    };

    // Notify alert callbacks
    this.alertCallbacks.forEach(callback => {
      try {
        callback(alert);
      } catch (error) {
        console.error('Error in alert callback:', error);
      }
    });

    // Send to backend if alerts are enabled
    if (this.config.enableAlerts) {
      this.sendAlertToBackend(alert);
    }

    console.warn(`🚨 Enterprise Performance Alert [${alert.severity.toUpperCase()}]:`, alert.message);
  }

  private async sendAlertToBackend(alert: PerformanceAlert) {
    try {
      await fetch('/api/analytics/enterprise-alerts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(alert)
      });
    } catch (error) {
      console.error('Failed to send alert to backend:', error);
    }
  }

  private async generatePerformanceReport() {
    try {
      const { EnterprisePerformanceTracker } = await import('./enterpriseCodeSplitting');
      const allMetrics = EnterprisePerformanceTracker.getAllMetrics();
      const performanceReport = EnterprisePerformanceTracker.getPerformanceReport();

      // Calculate overall health
      const componentCount = Object.keys(allMetrics).length;
      let overallHealth: 'excellent' | 'good' | 'fair' | 'poor' = 'excellent';

      if (componentCount > 0) {
        const poorComponents = Object.values(performanceReport).filter(m => m.performance === 'poor').length;
        const fairComponents = Object.values(performanceReport).filter(m => m.performance === 'fair').length;

        if (poorComponents > 0) {
          overallHealth = 'poor';
        } else if (fairComponents > componentCount * 0.3) {
          overallHealth = 'fair';
        } else if (Object.values(performanceReport).filter(m => m.performance === 'good' || m.performance === 'excellent').length > componentCount * 0.8) {
          overallHealth = 'good';
        }
      }

      // Generate recommendations
      const recommendations: string[] = [];
      Object.entries(performanceReport).forEach(([componentName, metrics]) => {
        if (metrics.recommendations && metrics.recommendations.length > 0) {
          recommendations.push(`${componentName}: ${metrics.recommendations[0]}`);
        }
      });

      const report: PerformanceReport = {
        timestamp: new Date(),
        overallHealth,
        componentMetrics: performanceReport,
        alerts: [], // Would include recent alerts
        recommendations
      };

      // Notify report callbacks
      this.reportCallbacks.forEach(callback => {
        try {
          callback(report);
        } catch (error) {
          console.error('Error in report callback:', error);
        }
      });

      // Send to backend analytics
      if (this.config.enableAnalytics) {
        this.sendReportToBackend(report);
      }

      console.log('📊 Enterprise Performance Report generated:', {
        overallHealth,
        componentCount,
        recommendationCount: recommendations.length
      });
    } catch (error) {
      console.error('Failed to generate performance report:', error);
    }
  }

  private async sendReportToBackend(report: PerformanceReport) {
    try {
      await fetch('/api/analytics/enterprise-performance-reports', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(report)
      });
    } catch (error) {
      console.error('Failed to send performance report to backend:', error);
    }
  }

  private handleEnterpriseError(error: Error, context: string) {
    this.createAlert({
      type: 'error',
      severity: 'medium',
      componentName: 'global',
      message: `Unhandled error in enterprise context: ${error.message}`,
      metrics: {
        context,
        stack: error.stack,
        userAgent: navigator.userAgent,
        url: window.location.href
      }
    });
  }

  // Public API methods
  onAlert(callback: (alert: PerformanceAlert) => void) {
    this.alertCallbacks.push(callback);
    return () => {
      const index = this.alertCallbacks.indexOf(callback);
      if (index > -1) {
        this.alertCallbacks.splice(index, 1);
      }
    };
  }

  onReport(callback: (report: PerformanceReport) => void) {
    this.reportCallbacks.push(callback);
    return () => {
      const index = this.reportCallbacks.indexOf(callback);
      if (index > -1) {
        this.reportCallbacks.splice(index, 1);
      }
    };
  }

  updateConfig(newConfig: Partial<EnterprisePerformanceConfig>) {
    this.config = { ...this.config, ...newConfig };
    
    // Restart monitoring if configuration changed
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.startRealTimeMonitoring();
    }

    if (this.reportingInterval) {
      clearInterval(this.reportingInterval);
      this.startPerformanceReporting();
    }
  }

  getConfig(): EnterprisePerformanceConfig {
    return { ...this.config };
  }

  async getHealthStatus(): Promise<{
    status: 'healthy' | 'degraded' | 'unhealthy';
    details: Record<string, any>;
  }> {
    try {
      const { EnterprisePerformanceTracker } = await import('./enterpriseCodeSplitting');
      const metrics = EnterprisePerformanceTracker.getAllMetrics();
      
      const componentCount = Object.keys(metrics).length;
      if (componentCount === 0) {
        return { status: 'healthy', details: { message: 'No components loaded yet' } };
      }

      const unhealthyComponents = Object.entries(metrics).filter(([_, metric]) => 
        metric.successRate < 0.8 || metric.averageLoadTime > 5000
      );

      if (unhealthyComponents.length === 0) {
        return { status: 'healthy', details: { componentCount, message: 'All components performing well' } };
      } else if (unhealthyComponents.length < componentCount * 0.3) {
        return { 
          status: 'degraded', 
          details: { 
            componentCount, 
            unhealthyCount: unhealthyComponents.length,
            unhealthyComponents: unhealthyComponents.map(([name]) => name)
          } 
        };
      } else {
        return { 
          status: 'unhealthy', 
          details: { 
            componentCount, 
            unhealthyCount: unhealthyComponents.length,
            unhealthyComponents: unhealthyComponents.map(([name]) => name)
          } 
        };
      }
    } catch (error) {
      return { status: 'unhealthy', details: { error: error.message } };
    }
  }

  destroy() {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
    }
    if (this.reportingInterval) {
      clearInterval(this.reportingInterval);
    }
    this.alertCallbacks.length = 0;
    this.reportCallbacks.length = 0;
  }
}

// Export singleton instance
export const enterprisePerformanceIntegration = EnterprisePerformanceIntegration.getInstance();

// Helper hook for React components
import React from 'react';

export function useEnterprisePerformanceMonitoring() {
  const [healthStatus, setHealthStatus] = React.useState<{
    status: 'healthy' | 'degraded' | 'unhealthy';
    details: Record<string, any>;
  }>({ status: 'healthy', details: {} });

  const [alerts, setAlerts] = React.useState<PerformanceAlert[]>([]);

  React.useEffect(() => {
    // Subscribe to alerts
    const unsubscribeAlerts = enterprisePerformanceIntegration.onAlert((alert) => {
      setAlerts(prev => [...prev.slice(-9), alert]); // Keep last 10 alerts
    });

    // Update health status periodically
    const updateHealth = async () => {
      const status = await enterprisePerformanceIntegration.getHealthStatus();
      setHealthStatus(status);
    };

    updateHealth();
    const healthInterval = setInterval(updateHealth, 30000); // Every 30 seconds

    return () => {
      unsubscribeAlerts();
      clearInterval(healthInterval);
    };
  }, []);

  return {
    healthStatus,
    alerts,
    clearAlerts: () => setAlerts([]),
    getConfig: () => enterprisePerformanceIntegration.getConfig(),
    updateConfig: (config: Partial<EnterprisePerformanceConfig>) => 
      enterprisePerformanceIntegration.updateConfig(config)
  };
}

// Initialize on module load
if (typeof window !== 'undefined') {
  // Initialize with default config after a short delay
  setTimeout(() => {
    enterprisePerformanceIntegration.initialize();
  }, 1000);
}