/**
 * Enterprise-specific code splitting utilities with enhanced monitoring and performance tracking
 */
import type { ComponentType } from 'react';
import { lazy } from 'react';
import { EnterpriseErrorBoundary } from '../components/enterprise/EnterpriseErrorBoundary';

type EnterpriseComponentType = 'analytics' | 'security' | 'workflow' | 'integration' | 'performance';

type LoadableEnterpriseComponent<T = Record<string, unknown>> = () => Promise<{
  default: ComponentType<T>;
}>;

interface EnterpriseMonitoringOptions {
  componentName: string;
  componentType: EnterpriseComponentType;
  timeout?: number;
  retries?: number;
  preload?: boolean;
  fallbackData?: any;
  criticalComponent?: boolean;
}

interface EnterprisePerformanceMetrics {
  loadTime: number;
  retryCount: number;
  errorCount: number;
  lastAccessed: Date;
  averageLoadTime: number;
  successRate: number;
}

export class EnterprisePerformanceTracker {
  private static metrics = new Map<string, EnterprisePerformanceMetrics>();
  private static loadAttempts = new Map<string, number[]>();
  private static errors = new Map<string, Error[]>();

  static recordLoadStart(componentName: string) {
    const attempts = this.loadAttempts.get(componentName) || [];
    attempts.push(performance.now());
    this.loadAttempts.set(componentName, attempts);
  }

  static recordLoadSuccess(componentName: string, startTime: number) {
    const loadTime = performance.now() - startTime;
    const currentMetrics = this.metrics.get(componentName) || {
      loadTime: 0,
      retryCount: 0,
      errorCount: 0,
      lastAccessed: new Date(),
      averageLoadTime: 0,
      successRate: 1
    };

    const attempts = this.loadAttempts.get(componentName) || [];
    const totalAttempts = attempts.length;
    const errors = this.errors.get(componentName) || [];
    
    const newMetrics: EnterprisePerformanceMetrics = {
      loadTime,
      retryCount: currentMetrics.retryCount,
      errorCount: errors.length,
      lastAccessed: new Date(),
      averageLoadTime: totalAttempts > 0 ? 
        attempts.reduce((sum, time, index) => {
          if (index === attempts.length - 1) return sum + loadTime;
          return sum + (attempts[index + 1] - time);
        }, 0) / totalAttempts : loadTime,
      successRate: totalAttempts > 0 ? (totalAttempts - errors.length) / totalAttempts : 1
    };

    this.metrics.set(componentName, newMetrics);

    // Report to enterprise analytics
    this.reportToEnterpriseAnalytics(componentName, 'load_success', { loadTime });
  }

  static recordLoadError(componentName: string, error: Error) {
    const errors = this.errors.get(componentName) || [];
    errors.push(error);
    this.errors.set(componentName, errors);

    const currentMetrics = this.metrics.get(componentName) || {
      loadTime: 0,
      retryCount: 0,
      errorCount: 0,
      lastAccessed: new Date(),
      averageLoadTime: 0,
      successRate: 1
    };

    currentMetrics.errorCount = errors.length;
    currentMetrics.lastAccessed = new Date();
    
    const attempts = this.loadAttempts.get(componentName) || [];
    if (attempts.length > 0) {
      currentMetrics.successRate = (attempts.length - errors.length) / attempts.length;
    }

    this.metrics.set(componentName, currentMetrics);

    // Report to enterprise analytics
    this.reportToEnterpriseAnalytics(componentName, 'load_error', { 
      error: error.message,
      errorCount: errors.length 
    });
  }

  static recordRetry(componentName: string) {
    const currentMetrics = this.metrics.get(componentName) || {
      loadTime: 0,
      retryCount: 0,
      errorCount: 0,
      lastAccessed: new Date(),
      averageLoadTime: 0,
      successRate: 1
    };

    currentMetrics.retryCount++;
    this.metrics.set(componentName, currentMetrics);

    // Report to enterprise analytics
    this.reportToEnterpriseAnalytics(componentName, 'retry', { 
      retryCount: currentMetrics.retryCount 
    });
  }

  static getMetrics(componentName: string): EnterprisePerformanceMetrics | undefined {
    return this.metrics.get(componentName);
  }

  static getAllMetrics(): Record<string, EnterprisePerformanceMetrics> {
    const result: Record<string, EnterprisePerformanceMetrics> = {};
    this.metrics.forEach((metrics, componentName) => {
      result[componentName] = metrics;
    });
    return result;
  }

  static getPerformanceReport(): Record<string, any> {
    const report: Record<string, any> = {};
    
    this.metrics.forEach((metrics, componentName) => {
      report[componentName] = {
        ...metrics,
        performance: this.getPerformanceRating(metrics),
        recommendations: this.getRecommendations(metrics)
      };
    });

    return report;
  }

  private static getPerformanceRating(metrics: EnterprisePerformanceMetrics): string {
    if (metrics.successRate < 0.8) return 'poor';
    if (metrics.averageLoadTime > 3000) return 'poor';
    if (metrics.averageLoadTime > 1500) return 'fair';
    if (metrics.successRate > 0.95 && metrics.averageLoadTime < 1000) return 'excellent';
    return 'good';
  }

  private static getRecommendations(metrics: EnterprisePerformanceMetrics): string[] {
    const recommendations: string[] = [];
    
    if (metrics.averageLoadTime > 2000) {
      recommendations.push('Consider code splitting optimization');
    }
    if (metrics.errorCount > 5) {
      recommendations.push('Investigate recurring load errors');
    }
    if (metrics.successRate < 0.9) {
      recommendations.push('Improve error handling and retry logic');
    }
    if (metrics.retryCount > 10) {
      recommendations.push('Review network connectivity and service stability');
    }

    return recommendations;
  }

  private static async reportToEnterpriseAnalytics(
    componentName: string, 
    eventType: string, 
    data: any
  ) {
    try {
      await fetch('/api/analytics/enterprise-performance', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          componentName,
          eventType,
          data,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent,
          url: window.location.href
        })
      });
    } catch (error) {
      // Silently fail - don't let analytics reporting break the app
      console.warn('Failed to report enterprise performance metrics:', error);
    }
  }

  static clearMetrics() {
    this.metrics.clear();
    this.loadAttempts.clear();
    this.errors.clear();
  }
}

export function createMonitoredEnterpriseComponent<T = {}>(
  loader: LoadableEnterpriseComponent<T>,
  options: EnterpriseMonitoringOptions
): ComponentType<T> {
  const {
    componentName,
    componentType,
    timeout = 15000, // Enterprise components get more time
    retries = 5, // More retries for enterprise components
    preload = false,
    fallbackData,
    criticalComponent = false
  } = options;

  // Preload critical components immediately
  if (preload || criticalComponent) {
    EnterpriseComponentPreloader.preload(componentName, loader, componentType);
  }

  const LazyComponent = lazy(() => {
    const startTime = performance.now();
    EnterprisePerformanceTracker.recordLoadStart(componentName);

    return Promise.race([
      // Main loader with enhanced retry logic
      retryEnterpriseLoader(loader, retries, componentName),

      // Timeout with enterprise-specific handling
      new Promise<never>((_, reject) => {
        setTimeout(() => {
          reject(
            new Error(
              `Enterprise component ${componentName} (${componentType}) failed to load within ${timeout}ms`
            )
          );
        }, timeout);
      }),
    ]).then(
      module => {
        EnterprisePerformanceTracker.recordLoadSuccess(componentName, startTime);

        // Log successful load for enterprise monitoring
        console.log(`✅ Enterprise ${componentType} component loaded: ${componentName}`);

        return module;
      },
      error => {
        EnterprisePerformanceTracker.recordLoadError(componentName, error);
        
        console.error(`❌ Failed to load enterprise ${componentType} component ${componentName}:`, error);

        // Return enterprise-specific fallback component
        return {
          default: (props: T) => (
            <EnterpriseErrorBoundary 
              componentType={componentType}
              fallbackData={fallbackData}
            >
              <div className='flex items-center justify-center p-8 min-h-96'>
                <div className='text-center'>
                  <div className='text-red-500 mb-4 text-lg'>
                    {componentName} Unavailable
                  </div>
                  <div className='text-gray-400 mb-4'>
                    The {componentType} service is temporarily unavailable.
                  </div>
                  <button
                    onClick={() => window.location.reload()}
                    className='px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors'
                  >
                    Reload Application
                  </button>
                </div>
              </div>
            </EnterpriseErrorBoundary>
          ),
        };
      }
    );
  });

  // Wrap with enterprise error boundary
  return (props: T) => (
    <EnterpriseErrorBoundary 
      componentType={componentType}
      fallbackData={fallbackData}
    >
      <LazyComponent {...props} />
    </EnterpriseErrorBoundary>
  );
}

async function retryEnterpriseLoader<T>(
  loader: LoadableEnterpriseComponent<T>,
  retries: number,
  componentName: string
): Promise<{ default: ComponentType<T> }> {
  for (let i = 0; i <= retries; i++) {
    try {
      return await loader();
    } catch (error) {
      if (i < retries) {
        EnterprisePerformanceTracker.recordRetry(componentName);
        
        // Progressive backoff with jitter for enterprise components
        const baseDelay = Math.pow(2, i) * 1000;
        const jitter = Math.random() * 1000;
        const delay = baseDelay + jitter;
        
        console.warn(`Retrying enterprise component ${componentName} in ${delay}ms (attempt ${i + 1}/${retries + 1})`);
        
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        throw error;
      }
    }
  }

  throw new Error(`Max retries (${retries}) exceeded for enterprise component ${componentName}`);
}

// Enterprise component preloader
export class EnterpriseComponentPreloader {
  private static preloadedComponents = new Set<string>();
  private static preloadPromises = new Map<string, Promise<any>>();
  private static preloadQueue: Array<{
    name: string;
    loader: LoadableEnterpriseComponent;
    type: EnterpriseComponentType;
    priority: number;
  }> = [];

  static preload(
    componentName: string, 
    loader: LoadableEnterpriseComponent,
    componentType: EnterpriseComponentType,
    priority: number = 1
  ) {
    if (this.preloadedComponents.has(componentName)) {
      return this.preloadPromises.get(componentName);
    }

    // Store metadata
    this.componentMetadata.set(componentName, { type: componentType, priority });

    // Add to queue with priority
    this.preloadQueue.push({
      name: componentName,
      loader,
      type: componentType,
      priority
    });

    // Sort by priority (higher priority first)
    this.preloadQueue.sort((a, b) => b.priority - a.priority);

    // Process queue
    return this.processPreloadQueue();
  }

  private static async processPreloadQueue() {
    if (this.preloadQueue.length === 0) return;

    const item = this.preloadQueue.shift()!;
    
    if (this.preloadedComponents.has(item.name)) {
      return this.processPreloadQueue(); // Continue with next item
    }

    this.preloadedComponents.add(item.name);

    const preloadPromise = this.scheduleEnterprisePreload(item);
    this.preloadPromises.set(item.name, preloadPromise);

    // Continue processing queue after a short delay
    setTimeout(() => this.processPreloadQueue(), 100);

    return preloadPromise;
  }

  private static scheduleEnterprisePreload(item: {
    name: string;
    loader: LoadableEnterpriseComponent;
    type: EnterpriseComponentType;
    priority: number;
  }) {
    return new Promise<void>(resolve => {
      const preloadFn = () => {
        const startTime = performance.now();
        
        item.loader()
          .then(() => {
            const loadTime = performance.now() - startTime;
            console.log(`✅ Preloaded enterprise ${item.type} component: ${item.name} (${loadTime.toFixed(2)}ms)`);
            
            // Record preload success
            EnterprisePerformanceTracker.recordLoadSuccess(item.name, startTime);
            resolve();
          })
          .catch(error => {
            console.warn(`⚠️ Failed to preload enterprise ${item.type} component ${item.name}:`, error);
            
            // Record preload error
            EnterprisePerformanceTracker.recordLoadError(item.name, error);
            resolve(); // Don't reject, just log the warning
          });
      };

      // Use requestIdleCallback for non-critical components
      if (item.priority < 3 && 'requestIdleCallback' in window) {
        requestIdleCallback(preloadFn, { timeout: 5000 });
      } else {
        // Immediate preload for critical components
        setTimeout(preloadFn, item.priority >= 5 ? 0 : 500);
      }
    });
  }

  static preloadCriticalEnterpriseComponents() {
    // Define critical enterprise components with priorities
    const criticalComponents = [
      {
        name: 'EnterpriseAnalyticsDashboard',
        type: 'analytics' as EnterpriseComponentType,
        priority: 5,
        loader: () =>
          import('../components/enterprise/EnterpriseAnalyticsDashboard').then(m => ({
            default: m.EnterpriseAnalyticsDashboard,
          })),
      },
      {
        name: 'SecurityDashboard',
        type: 'security' as EnterpriseComponentType,
        priority: 4,
        loader: () =>
          import('../components/enterprise/SecurityDashboard').then(m => ({
            default: m.SecurityDashboard,
          })),
      },
      {
        name: 'WorkflowManager',
        type: 'workflow' as EnterpriseComponentType,
        priority: 3,
        loader: () =>
          import('../components/enterprise/WorkflowManager').then(m => ({
            default: m.WorkflowManager,
          })),
      },
      {
        name: 'IntegrationHub',
        type: 'integration' as EnterpriseComponentType,
        priority: 2,
        loader: () =>
          import('../components/enterprise/IntegrationHub').then(m => ({
            default: m.IntegrationHub,
          })),
      },
    ];

    criticalComponents.forEach(({ name, type, priority, loader }) => {
      this.preload(name, loader, type, priority);
    });
  }

  private static componentMetadata = new Map<string, { type: EnterpriseComponentType; priority: number }>();

  static getPreloadStatus(): Record<string, { loaded: boolean; type: string; priority: number }> {
    const status: Record<string, { loaded: boolean; type: string; priority: number }> = {};

    this.preloadedComponents.forEach(componentName => {
      const promise = this.preloadPromises.get(componentName);
      const metadata = this.componentMetadata.get(componentName);
      
      status[componentName] = {
        loaded: promise ? true : false,
        type: metadata?.type || 'unknown',
        priority: metadata?.priority || 0
      };
    });

    return status;
  }

  static clearPreloadCache() {
    this.preloadedComponents.clear();
    this.preloadPromises.clear();
    this.preloadQueue.length = 0;
    this.componentMetadata.clear();
  }
}

// Initialize enterprise code splitting
export function initializeEnterpriseCodeSplitting() {
  console.log('🏢 Initializing enterprise code splitting...');

  // Preload critical enterprise components after app initialization
  setTimeout(() => {
    EnterpriseComponentPreloader.preloadCriticalEnterpriseComponents();
  }, 2000);

  // Set up enterprise performance monitoring
  if (typeof window !== 'undefined') {
    // Report enterprise performance metrics every 2 minutes
    setInterval(() => {
      const report = EnterprisePerformanceTracker.getPerformanceReport();
      if (Object.keys(report).length > 0) {
        console.log('📊 Enterprise Component Performance Report:', report);
        
        // Send to enterprise analytics service
        fetch('/api/analytics/enterprise-performance-report', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            report,
            timestamp: new Date().toISOString()
          })
        }).catch(error => {
          console.warn('Failed to send enterprise performance report:', error);
        });
      }
    }, 120000); // Every 2 minutes

    // Monitor memory usage for enterprise components
    if ('memory' in performance) {
      setInterval(() => {
        const memoryInfo = (performance as any).memory;
        if (memoryInfo.usedJSHeapSize > memoryInfo.jsHeapSizeLimit * 0.9) {
          console.warn('⚠️ High memory usage detected in enterprise components');
        }
      }, 30000); // Every 30 seconds
    }
  }
}

// Helper function to create enterprise components with standard configuration
export function createEnterpriseComponent<T = {}>(
  componentName: string,
  componentType: EnterpriseComponentType,
  loader: LoadableEnterpriseComponent<T>,
  options: Partial<EnterpriseMonitoringOptions> = {}
): ComponentType<T> {
  return createMonitoredEnterpriseComponent(loader, {
    componentName,
    componentType,
    timeout: 15000,
    retries: 5,
    preload: false,
    criticalComponent: false,
    ...options
  });
}