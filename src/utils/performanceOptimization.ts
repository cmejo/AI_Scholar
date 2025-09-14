// Performance Optimization Utilities for Phase 7

interface PerformanceMetrics {
  loadTime: number;
  renderTime: number;
  bundleSize: number;
  memoryUsage: number;
  networkRequests: number;
  cacheHitRate: number;
}

interface OptimizationConfig {
  enableLazyLoading: boolean;
  enableImageOptimization: boolean;
  enableCodeSplitting: boolean;
  enableCaching: boolean;
  enablePreloading: boolean;
  enableServiceWorker: boolean;
}

class PerformanceOptimizer {
  private static instance: PerformanceOptimizer;
  private metrics: PerformanceMetrics;
  private config: OptimizationConfig;
  private observers: Map<string, PerformanceObserver>;

  private constructor() {
    this.metrics = {
      loadTime: 0,
      renderTime: 0,
      bundleSize: 0,
      memoryUsage: 0,
      networkRequests: 0,
      cacheHitRate: 0
    };

    this.config = {
      enableLazyLoading: true,
      enableImageOptimization: true,
      enableCodeSplitting: true,
      enableCaching: true,
      enablePreloading: true,
      enableServiceWorker: true
    };

    this.observers = new Map();
    this.initializePerformanceMonitoring();
  }

  public static getInstance(): PerformanceOptimizer {
    if (!PerformanceOptimizer.instance) {
      PerformanceOptimizer.instance = new PerformanceOptimizer();
    }
    return PerformanceOptimizer.instance;
  }

  private initializePerformanceMonitoring(): void {
    // Monitor navigation timing
    if ('performance' in window && 'getEntriesByType' in performance) {
      this.monitorNavigationTiming();
      this.monitorResourceTiming();
      this.monitorLargestContentfulPaint();
      this.monitorFirstInputDelay();
      this.monitorCumulativeLayoutShift();
    }

    // Monitor memory usage
    this.monitorMemoryUsage();

    // Monitor network requests
    this.monitorNetworkRequests();
  }

  private monitorNavigationTiming(): void {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry) => {
        if (entry.entryType === 'navigation') {
          const navEntry = entry as PerformanceNavigationTiming;
          this.metrics.loadTime = navEntry.loadEventEnd - navEntry.navigationStart;
          this.metrics.renderTime = navEntry.domContentLoadedEventEnd - navEntry.navigationStart;
        }
      });
    });

    observer.observe({ entryTypes: ['navigation'] });
    this.observers.set('navigation', observer);
  }

  private monitorResourceTiming(): void {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry) => {
        if (entry.entryType === 'resource') {
          this.metrics.networkRequests++;
          
          // Calculate cache hit rate
          const resourceEntry = entry as PerformanceResourceTiming;
          if (resourceEntry.transferSize === 0 && resourceEntry.decodedBodySize > 0) {
            this.metrics.cacheHitRate++;
          }
        }
      });
    });

    observer.observe({ entryTypes: ['resource'] });
    this.observers.set('resource', observer);
  }

  private monitorLargestContentfulPaint(): void {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1];
      console.log('LCP:', lastEntry.startTime);
    });

    observer.observe({ entryTypes: ['largest-contentful-paint'] });
    this.observers.set('lcp', observer);
  }

  private monitorFirstInputDelay(): void {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry) => {
        console.log('FID:', entry.processingStart - entry.startTime);
      });
    });

    observer.observe({ entryTypes: ['first-input'] });
    this.observers.set('fid', observer);
  }

  private monitorCumulativeLayoutShift(): void {
    const observer = new PerformanceObserver((list) => {
      let clsValue = 0;
      const entries = list.getEntries();
      entries.forEach((entry) => {
        if (!(entry as any).hadRecentInput) {
          clsValue += (entry as any).value;
        }
      });
      console.log('CLS:', clsValue);
    });

    observer.observe({ entryTypes: ['layout-shift'] });
    this.observers.set('cls', observer);
  }

  private monitorMemoryUsage(): void {
    if ('memory' in performance) {
      setInterval(() => {
        const memory = (performance as any).memory;
        this.metrics.memoryUsage = memory.usedJSHeapSize / 1024 / 1024; // MB
      }, 5000);
    }
  }

  private monitorNetworkRequests(): void {
    // Override fetch to monitor network requests
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const startTime = performance.now();
      try {
        const response = await originalFetch(...args);
        const endTime = performance.now();
        
        console.log(`Network request: ${args[0]} - ${endTime - startTime}ms`);
        return response;
      } catch (error) {
        console.error('Network request failed:', error);
        throw error;
      }
    };
  }

  // Lazy loading implementation
  public enableLazyLoading(): void {
    if (!this.config.enableLazyLoading) return;

    const imageObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const img = entry.target as HTMLImageElement;
          if (img.dataset.src) {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
            imageObserver.unobserve(img);
          }
        }
      });
    });

    // Observe all images with data-src attribute
    document.querySelectorAll('img[data-src]').forEach((img) => {
      imageObserver.observe(img);
    });
  }

  // Preload critical resources
  public preloadCriticalResources(): void {
    if (!this.config.enablePreloading) return;

    const criticalResources = [
      '/fonts/inter-var.woff2',
      '/images/logo.svg',
      '/api/user/profile'
    ];

    criticalResources.forEach((resource) => {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.href = resource;
      
      if (resource.endsWith('.woff2')) {
        link.as = 'font';
        link.type = 'font/woff2';
        link.crossOrigin = 'anonymous';
      } else if (resource.endsWith('.svg')) {
        link.as = 'image';
      } else if (resource.startsWith('/api/')) {
        link.as = 'fetch';
        link.crossOrigin = 'anonymous';
      }
      
      document.head.appendChild(link);
    });
  }

  // Enable service worker for caching
  public enableServiceWorker(): void {
    if (!this.config.enableServiceWorker || !('serviceWorker' in navigator)) return;

    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('Service Worker registered:', registration);
      })
      .catch((error) => {
        console.error('Service Worker registration failed:', error);
      });
  }

  // Bundle size optimization
  public analyzeBundleSize(): Promise<any> {
    return new Promise((resolve) => {
      // Analyze loaded scripts
      const scripts = Array.from(document.querySelectorAll('script[src]'));
      const bundleInfo = scripts.map((script) => {
        const src = (script as HTMLScriptElement).src;
        return {
          url: src,
          size: 0 // Would need actual size from network tab
        };
      });

      this.metrics.bundleSize = bundleInfo.length;
      resolve(bundleInfo);
    });
  }

  // Memory optimization
  public optimizeMemoryUsage(): void {
    // Clean up unused event listeners
    this.cleanupEventListeners();

    // Force garbage collection if available
    if ('gc' in window) {
      (window as any).gc();
    }

    // Clear unused caches
    this.clearUnusedCaches();
  }

  private cleanupEventListeners(): void {
    // Remove unused observers
    this.observers.forEach((observer, key) => {
      if (key !== 'navigation' && key !== 'resource') {
        observer.disconnect();
        this.observers.delete(key);
      }
    });
  }

  private clearUnusedCaches(): void {
    if ('caches' in window) {
      caches.keys().then((cacheNames) => {
        cacheNames.forEach((cacheName) => {
          if (cacheName.includes('old') || cacheName.includes('temp')) {
            caches.delete(cacheName);
          }
        });
      });
    }
  }

  // Performance budget enforcement
  public checkPerformanceBudget(): {
    passed: boolean;
    violations: string[];
    recommendations: string[];
  } {
    const violations: string[] = [];
    const recommendations: string[] = [];

    // Check load time (budget: 3 seconds)
    if (this.metrics.loadTime > 3000) {
      violations.push(`Load time: ${this.metrics.loadTime}ms (budget: 3000ms)`);
      recommendations.push('Consider code splitting and lazy loading');
    }

    // Check bundle size (budget: 250KB)
    if (this.metrics.bundleSize > 250) {
      violations.push(`Bundle size: ${this.metrics.bundleSize}KB (budget: 250KB)`);
      recommendations.push('Implement tree shaking and remove unused dependencies');
    }

    // Check memory usage (budget: 50MB)
    if (this.metrics.memoryUsage > 50) {
      violations.push(`Memory usage: ${this.metrics.memoryUsage}MB (budget: 50MB)`);
      recommendations.push('Optimize component lifecycle and cleanup unused objects');
    }

    return {
      passed: violations.length === 0,
      violations,
      recommendations
    };
  }

  // Get current metrics
  public getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  // Update configuration
  public updateConfig(newConfig: Partial<OptimizationConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  // Generate performance report
  public generatePerformanceReport(): string {
    const budget = this.checkPerformanceBudget();
    const metrics = this.getMetrics();

    return `
Performance Report - ${new Date().toLocaleString()}
================================================

Core Web Vitals:
- Load Time: ${metrics.loadTime}ms
- Render Time: ${metrics.renderTime}ms
- Memory Usage: ${metrics.memoryUsage.toFixed(2)}MB
- Network Requests: ${metrics.networkRequests}
- Cache Hit Rate: ${((metrics.cacheHitRate / metrics.networkRequests) * 100).toFixed(1)}%

Performance Budget:
- Status: ${budget.passed ? 'PASSED' : 'FAILED'}
- Violations: ${budget.violations.length}
- Recommendations: ${budget.recommendations.length}

${budget.violations.length > 0 ? `
Violations:
${budget.violations.map(v => `- ${v}`).join('\n')}
` : ''}

${budget.recommendations.length > 0 ? `
Recommendations:
${budget.recommendations.map(r => `- ${r}`).join('\n')}
` : ''}

Optimization Status:
- Lazy Loading: ${this.config.enableLazyLoading ? 'Enabled' : 'Disabled'}
- Image Optimization: ${this.config.enableImageOptimization ? 'Enabled' : 'Disabled'}
- Code Splitting: ${this.config.enableCodeSplitting ? 'Enabled' : 'Disabled'}
- Caching: ${this.config.enableCaching ? 'Enabled' : 'Disabled'}
- Preloading: ${this.config.enablePreloading ? 'Enabled' : 'Disabled'}
- Service Worker: ${this.config.enableServiceWorker ? 'Enabled' : 'Disabled'}
    `.trim();
  }

  // Cleanup
  public cleanup(): void {
    this.observers.forEach((observer) => {
      observer.disconnect();
    });
    this.observers.clear();
  }
}

// Export singleton instance
export const performanceOptimizer = PerformanceOptimizer.getInstance();

// Utility functions
export const measurePerformance = (name: string, fn: () => void): number => {
  const start = performance.now();
  fn();
  const end = performance.now();
  const duration = end - start;
  console.log(`${name}: ${duration}ms`);
  return duration;
};

export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

export const memoize = <T extends (...args: any[]) => any>(fn: T): T => {
  const cache = new Map();
  return ((...args: Parameters<T>) => {
    const key = JSON.stringify(args);
    if (cache.has(key)) {
      return cache.get(key);
    }
    const result = fn(...args);
    cache.set(key, result);
    return result;
  }) as T;
};

// Initialize performance optimization
export const initializePerformanceOptimization = (): void => {
  const optimizer = performanceOptimizer;
  
  // Enable optimizations
  optimizer.enableLazyLoading();
  optimizer.preloadCriticalResources();
  optimizer.enableServiceWorker();
  
  // Set up periodic optimization
  setInterval(() => {
    optimizer.optimizeMemoryUsage();
  }, 60000); // Every minute
  
  // Log performance report every 5 minutes in development
  if (window.location.hostname === 'localhost') {
    setInterval(() => {
      console.log(optimizer.generatePerformanceReport());
    }, 300000);
  }
};