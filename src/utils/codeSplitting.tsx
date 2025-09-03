/**
 * Enhanced code splitting utilities for AI Scholar
 * Provides monitored lazy loading with performance tracking and error handling
 */
import { ComponentType, lazy } from 'react';

interface LoadableComponent<T = Record<string, unknown>> {
  (): Promise<{ default: ComponentType<T> }>;
}

interface MonitoringOptions {
  componentName: string;
  timeout?: number;
  retries?: number;
  preload?: boolean;
}

export function createMonitoredLazyComponent<T = {}>(
  loader: LoadableComponent<T>,
  options: MonitoringOptions
): ComponentType<T> {
  const {
    componentName,
    timeout = 10000,
    retries = 3,
    preload = false,
  } = options;

  // Preload if requested
  if (preload) {
    ComponentPreloader.preload(componentName, loader);
  }

  return lazy(() => {
    const startTime = performance.now();

    return Promise.race([
      // Main loader with retry logic
      retryLoader(loader, retries),

      // Timeout fallback
      new Promise<never>((_, reject) => {
        setTimeout(() => {
          reject(
            new Error(
              `Component ${componentName} failed to load within ${timeout}ms`
            )
          );
        }, timeout);
      }),
    ]).then(
      module => {
        const loadTime = performance.now() - startTime;

        // Report performance metrics
        if ('performance' in window && 'measure' in window.performance) {
          performance.measure(`component-load-${componentName}`, {
            start: startTime,
            duration: loadTime,
          });
        }

        // Log performance data
        ComponentPerformanceTracker.recordLoad(componentName, loadTime);

        // Warn about slow loads
        if (loadTime > 2000) {
          console.warn(
            `Slow component load: ${componentName} took ${loadTime.toFixed(2)}ms`
          );
        }

        return module;
      },
      error => {
        console.error(`Failed to load component ${componentName}:`, error);
        ComponentPerformanceTracker.recordError(componentName, error);

        // Return fallback component
        return {
          default: () => (
            <div className='flex items-center justify-center p-8'>
              <div className='text-center'>
                <div className='text-red-500 mb-2'>
                  Failed to load {componentName}
                </div>
                <button
                  onClick={() => window.location.reload()}
                  className='px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600'
                >
                  Retry
                </button>
              </div>
            </div>
          ),
        };
      }
    );
  });
}

async function retryLoader<T>(
  loader: LoadableComponent<T>,
  retries: number
): Promise<{ default: ComponentType<T> }> {
  for (let i = 0; i <= retries; i++) {
    try {
      return await loader();
    } catch (error) {
      if (i === retries) {
        throw error;
      }

      // Exponential backoff
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
    }
  }

  throw new Error('Max retries exceeded');
}

// Component preloader utility
export class ComponentPreloader {
  private static preloadedComponents = new Set<string>();
  private static preloadPromises = new Map<string, Promise<any>>();

  static preload(componentName: string, loader: LoadableComponent) {
    if (this.preloadedComponents.has(componentName)) {
      return this.preloadPromises.get(componentName);
    }

    this.preloadedComponents.add(componentName);

    const preloadPromise = this.schedulePreload(componentName, loader);
    this.preloadPromises.set(componentName, preloadPromise);

    return preloadPromise;
  }

  private static schedulePreload(
    componentName: string,
    loader: LoadableComponent
  ) {
    return new Promise<void>(resolve => {
      // Preload on idle or after a short delay
      if ('requestIdleCallback' in window) {
        requestIdleCallback(() => {
          loader()
            .then(() => {
              console.log(`✅ Preloaded component: ${componentName}`);
              resolve();
            })
            .catch(error => {
              console.warn(`⚠️ Failed to preload ${componentName}:`, error);
              resolve(); // Don't reject, just log the warning
            });
        });
      } else {
        // Fallback for browsers without requestIdleCallback
        setTimeout(() => {
          loader()
            .then(() => {
              console.log(`✅ Preloaded component: ${componentName}`);
              resolve();
            })
            .catch(error => {
              console.warn(`⚠️ Failed to preload ${componentName}:`, error);
              resolve();
            });
        }, 100);
      }
    });
  }

  static preloadCriticalComponents() {
    // Define critical components that should be preloaded
    const criticalComponents = [
      {
        name: 'AdvancedChatInterface',
        loader: () =>
          import('../components/AdvancedChatInterface').then(m => ({
            default: m.AdvancedChatInterface,
          })),
      },
      {
        name: 'EnhancedDocumentManager',
        loader: () =>
          import('../components/EnhancedDocumentManager').then(m => ({
            default: m.EnhancedDocumentManager,
          })),
      },
      {
        name: 'MemoryAwareChatInterface',
        loader: () =>
          import('../components/MemoryAwareChatInterface').then(m => ({
            default: m.MemoryAwareChatInterface,
          })),
      },
    ];

    criticalComponents.forEach(({ name, loader }) => {
      this.preload(name, loader);
    });
  }

  static getPreloadStatus(): Record<string, boolean> {
    const status: Record<string, boolean> = {};

    this.preloadedComponents.forEach(componentName => {
      const promise = this.preloadPromises.get(componentName);
      status[componentName] = promise ? true : false;
    });

    return status;
  }
}

// Performance tracking for components
export class ComponentPerformanceTracker {
  private static loadTimes = new Map<string, number[]>();
  private static errors = new Map<string, Error[]>();

  static recordLoad(componentName: string, loadTime: number) {
    if (!this.loadTimes.has(componentName)) {
      this.loadTimes.set(componentName, []);
    }

    this.loadTimes.get(componentName)!.push(loadTime);

    // Keep only last 10 measurements
    const times = this.loadTimes.get(componentName)!;
    if (times.length > 10) {
      times.shift();
    }
  }

  static recordError(componentName: string, error: Error) {
    if (!this.errors.has(componentName)) {
      this.errors.set(componentName, []);
    }

    this.errors.get(componentName)!.push(error);

    // Keep only last 5 errors
    const errors = this.errors.get(componentName)!;
    if (errors.length > 5) {
      errors.shift();
    }
  }

  static getPerformanceReport(): Record<string, any> {
    const report: Record<string, any> = {};

    this.loadTimes.forEach((times, componentName) => {
      const avgTime = times.reduce((sum, time) => sum + time, 0) / times.length;
      const minTime = Math.min(...times);
      const maxTime = Math.max(...times);

      report[componentName] = {
        averageLoadTime: Math.round(avgTime),
        minLoadTime: Math.round(minTime),
        maxLoadTime: Math.round(maxTime),
        loadCount: times.length,
        errorCount: this.errors.get(componentName)?.length || 0,
        performance: avgTime < 1000 ? 'good' : avgTime < 2000 ? 'fair' : 'poor',
      };
    });

    return report;
  }

  static clearMetrics() {
    this.loadTimes.clear();
    this.errors.clear();
  }
}

// Route-based code splitting helper
export function createRouteComponent<T = {}>(
  routeName: string,
  loader: LoadableComponent<T>
): ComponentType<T> {
  return createMonitoredLazyComponent(loader, {
    componentName: `Route-${routeName}`,
    timeout: 15000, // Routes can take a bit longer
    retries: 2,
    preload: false, // Don't preload routes by default
  });
}

// Feature-based code splitting helper
export function createFeatureComponent<T = {}>(
  featureName: string,
  loader: LoadableComponent<T>,
  critical: boolean = false
): ComponentType<T> {
  return createMonitoredLazyComponent(loader, {
    componentName: `Feature-${featureName}`,
    timeout: 10000,
    retries: 3,
    preload: critical,
  });
}

// Initialize preloading on app start
export function initializeCodeSplitting() {
  // Preload critical components after a short delay
  setTimeout(() => {
    ComponentPreloader.preloadCriticalComponents();
  }, 1000);

  // Set up performance monitoring
  if (typeof window !== 'undefined') {
    // Report performance metrics periodically
    setInterval(() => {
      const report = ComponentPerformanceTracker.getPerformanceReport();
      if (Object.keys(report).length > 0) {
        console.log('📊 Component Performance Report:', report);
      }
    }, 60000); // Every minute
  }
}

// Export for use in main app
export { ComponentPerformanceTracker, ComponentPreloader };
