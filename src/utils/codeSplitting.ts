import { ComponentType, lazy } from 'react';

/**
 * Enhanced lazy loading with error boundaries and loading states
 */

interface LazyComponentOptions {
  fallback?: ComponentType;
  retryCount?: number;
  retryDelay?: number;
  preload?: boolean;
}

/**
 * Create a lazy component with enhanced error handling and retry logic
 */
export function createLazyComponent<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  options: LazyComponentOptions = {}
): ComponentType<React.ComponentProps<T>> {
  const {
    retryCount = 3,
    retryDelay = 1000,
    preload = false
  } = options;

  let importPromise: Promise<{ default: T }> | null = null;
  let retryAttempts = 0;

  const loadComponent = async (): Promise<{ default: T }> => {
    try {
      if (!importPromise) {
        importPromise = importFn();
      }
      return await importPromise;
    } catch (error) {
      importPromise = null; // Reset promise to allow retry
      
      if (retryAttempts < retryCount) {
        retryAttempts++;
        console.warn(`Failed to load component, retrying (${retryAttempts}/${retryCount})...`, error);
        
        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, retryDelay));
        return loadComponent();
      }
      
      console.error('Failed to load component after all retries:', error);
      throw error;
    }
  };

  const LazyComponent = lazy(loadComponent);

  // Preload the component if requested
  if (preload) {
    loadComponent().catch(error => {
      console.warn('Failed to preload component:', error);
    });
  }

  return LazyComponent;
}

/**
 * Preload a lazy component
 */
export function preloadComponent<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>
): Promise<{ default: T }> {
  return importFn().catch(error => {
    console.warn('Failed to preload component:', error);
    throw error;
  });
}

/**
 * Create multiple lazy components with shared loading logic
 */
export function createLazyComponents<T extends Record<string, () => Promise<{ default: ComponentType<any> }>>>(
  imports: T,
  options: LazyComponentOptions = {}
): { [K in keyof T]: ComponentType<any> } {
  const result = {} as { [K in keyof T]: ComponentType<any> };
  
  for (const [key, importFn] of Object.entries(imports)) {
    result[key as keyof T] = createLazyComponent(importFn, options);
  }
  
  return result;
}

/**
 * Route-based code splitting helper
 */
export interface RouteComponent {
  path: string;
  component: ComponentType<any>;
  preload?: boolean;
}

export function createRouteComponents(
  routes: Array<{
    path: string;
    importFn: () => Promise<{ default: ComponentType<any> }>;
    preload?: boolean;
  }>,
  options: LazyComponentOptions = {}
): RouteComponent[] {
  return routes.map(({ path, importFn, preload = false }) => ({
    path,
    component: createLazyComponent(importFn, { ...options, preload }),
    preload
  }));
}

/**
 * Bundle splitting strategies
 */
export const bundleSplittingStrategies = {
  /**
   * Split by feature/page
   */
  byFeature: (featureName: string) => ({
    chunkName: `feature-${featureName}`,
    webpackChunkName: `feature-${featureName}`
  }),

  /**
   * Split by component type
   */
  byComponentType: (type: 'dashboard' | 'form' | 'chart' | 'modal') => ({
    chunkName: `${type}-components`,
    webpackChunkName: `${type}-components`
  }),

  /**
   * Split by vendor/library
   */
  byVendor: (vendorName: string) => ({
    chunkName: `vendor-${vendorName}`,
    webpackChunkName: `vendor-${vendorName}`
  })
};

/**
 * Performance monitoring for lazy components
 */
export class LazyComponentPerformanceMonitor {
  private static loadTimes = new Map<string, number>();
  private static loadErrors = new Map<string, number>();

  static recordLoadTime(componentName: string, loadTime: number): void {
    this.loadTimes.set(componentName, loadTime);
    
    if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
      console.log(`[Lazy Load] ${componentName} loaded in ${loadTime.toFixed(2)}ms`);
    }
  }

  static recordLoadError(componentName: string): void {
    const currentErrors = this.loadErrors.get(componentName) || 0;
    this.loadErrors.set(componentName, currentErrors + 1);
    
    console.warn(`[Lazy Load Error] ${componentName} failed to load (${currentErrors + 1} times)`);
  }

  static getMetrics(): {
    loadTimes: Map<string, number>;
    loadErrors: Map<string, number>;
    averageLoadTime: number;
    totalErrors: number;
  } {
    const loadTimesArray = Array.from(this.loadTimes.values());
    const averageLoadTime = loadTimesArray.length > 0 
      ? loadTimesArray.reduce((sum, time) => sum + time, 0) / loadTimesArray.length 
      : 0;
    
    const totalErrors = Array.from(this.loadErrors.values()).reduce((sum, errors) => sum + errors, 0);

    return {
      loadTimes: this.loadTimes,
      loadErrors: this.loadErrors,
      averageLoadTime,
      totalErrors
    };
  }

  static reset(): void {
    this.loadTimes.clear();
    this.loadErrors.clear();
  }
}

/**
 * Enhanced lazy component with performance monitoring
 */
export function createMonitoredLazyComponent<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  componentName: string,
  options: LazyComponentOptions = {}
): ComponentType<React.ComponentProps<T>> {
  const enhancedImportFn = async (): Promise<{ default: T }> => {
    const startTime = performance.now();
    
    try {
      const result = await importFn();
      const loadTime = performance.now() - startTime;
      
      LazyComponentPerformanceMonitor.recordLoadTime(componentName, loadTime);
      
      return result;
    } catch (error) {
      LazyComponentPerformanceMonitor.recordLoadError(componentName);
      throw error;
    }
  };

  return createLazyComponent(enhancedImportFn, options);
}

/**
 * Utility to check if a component should be lazy loaded based on viewport
 */
export function shouldLazyLoad(element: HTMLElement | null, threshold: number = 0.1): boolean {
  if (!element || typeof window === 'undefined' || !window.IntersectionObserver) {
    return true; // Fallback to immediate loading
  }

  return new Promise<boolean>((resolve) => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            resolve(true);
            observer.disconnect();
          }
        });
      },
      { threshold }
    );

    observer.observe(element);

    // Timeout fallback
    setTimeout(() => {
      resolve(true);
      observer.disconnect();
    }, 5000);
  });
}