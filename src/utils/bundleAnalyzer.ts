// Bundle analysis and optimization utilities

export interface BundleMetrics {
  totalSize: number;
  gzippedSize: number;
  chunkCount: number;
  largestChunk: string;
  largestChunkSize: number;
  duplicateModules: string[];
  unusedExports: string[];
  loadTime: number;
}

export interface ChunkInfo {
  name: string;
  size: number;
  gzippedSize?: number;
  modules: string[];
  isVendor: boolean;
  isAsync: boolean;
}

export class BundleAnalyzer {
  private static instance: BundleAnalyzer;
  private metrics: BundleMetrics | null = null;
  private chunks: ChunkInfo[] = [];
  private loadStartTime: number = 0;

  static getInstance(): BundleAnalyzer {
    if (!BundleAnalyzer.instance) {
      BundleAnalyzer.instance = new BundleAnalyzer();
    }
    return BundleAnalyzer.instance;
  }

  // Initialize bundle analysis
  initialize(): void {
    this.loadStartTime = performance.now();
    this.analyzeCurrentBundle();
    this.setupPerformanceObserver();
  }

  // Analyze the current bundle
  private analyzeCurrentBundle(): void {
    try {
      // Get all script tags (representing chunks)
      const scriptTags = Array.from(document.querySelectorAll('script[src]'));
      const chunks: ChunkInfo[] = [];

      scriptTags.forEach((script) => {
        const src = (script as HTMLScriptElement).src;
        if (src && src.includes('/assets/')) {
          const chunkName = this.extractChunkName(src);
          chunks.push({
            name: chunkName,
            size: 0, // Will be estimated
            modules: [],
            isVendor: chunkName.includes('vendor'),
            isAsync: script.hasAttribute('async') || script.hasAttribute('defer')
          });
        }
      });

      this.chunks = chunks;
      this.estimateBundleMetrics();
    } catch (error) {
      console.warn('Bundle analysis failed:', error);
    }
  }

  // Extract chunk name from URL
  private extractChunkName(url: string): string {
    const match = url.match(/\/([^\/]+)\.js$/);
    return match ? match[1] : 'unknown';
  }

  // Estimate bundle metrics
  private estimateBundleMetrics(): void {
    const totalChunks = this.chunks.length;
    const vendorChunks = this.chunks.filter(c => c.isVendor).length;
    const asyncChunks = this.chunks.filter(c => c.isAsync).length;

    // Estimate sizes based on typical patterns
    const estimatedTotalSize = totalChunks * 50000; // 50KB average per chunk
    const estimatedGzippedSize = estimatedTotalSize * 0.3; // ~30% compression

    this.metrics = {
      totalSize: estimatedTotalSize,
      gzippedSize: estimatedGzippedSize,
      chunkCount: totalChunks,
      largestChunk: this.chunks[0]?.name || 'unknown',
      largestChunkSize: 100000, // Estimated
      duplicateModules: [],
      unusedExports: [],
      loadTime: performance.now() - this.loadStartTime
    };
  }

  // Setup performance observer for resource timing
  private setupPerformanceObserver(): void {
    if ('PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (entry.name.includes('/assets/') && entry.name.endsWith('.js')) {
            this.updateChunkMetrics(entry as PerformanceResourceTiming);
          }
        });
      });

      observer.observe({ entryTypes: ['resource'] });
    }
  }

  // Update chunk metrics with actual performance data
  private updateChunkMetrics(entry: PerformanceResourceTiming): void {
    const chunkName = this.extractChunkName(entry.name);
    const chunk = this.chunks.find(c => c.name === chunkName);
    
    if (chunk) {
      chunk.size = entry.transferSize || entry.encodedBodySize || 0;
      chunk.gzippedSize = entry.encodedBodySize || 0;
    }
  }

  // Get current bundle metrics
  getMetrics(): BundleMetrics | null {
    return this.metrics;
  }

  // Get chunk information
  getChunks(): ChunkInfo[] {
    return this.chunks;
  }

  // Analyze bundle health
  analyzeBundleHealth(): {
    score: number;
    issues: string[];
    recommendations: string[];
  } {
    const issues: string[] = [];
    const recommendations: string[] = [];
    let score = 100;

    if (!this.metrics) {
      return { score: 0, issues: ['Bundle analysis not available'], recommendations: [] };
    }

    // Check total bundle size
    if (this.metrics.totalSize > 1000000) { // 1MB
      issues.push('Bundle size is very large (>1MB)');
      recommendations.push('Consider code splitting and lazy loading');
      score -= 20;
    } else if (this.metrics.totalSize > 500000) { // 500KB
      issues.push('Bundle size is large (>500KB)');
      recommendations.push('Review dependencies and remove unused code');
      score -= 10;
    }

    // Check chunk count
    if (this.metrics.chunkCount < 3) {
      issues.push('Too few chunks - missing code splitting opportunities');
      recommendations.push('Implement code splitting for better caching');
      score -= 15;
    } else if (this.metrics.chunkCount > 20) {
      issues.push('Too many chunks - may hurt performance');
      recommendations.push('Consolidate smaller chunks');
      score -= 10;
    }

    // Check load time
    if (this.metrics.loadTime > 3000) { // 3 seconds
      issues.push('Slow bundle load time');
      recommendations.push('Optimize bundle size and use CDN');
      score -= 25;
    } else if (this.metrics.loadTime > 1000) { // 1 second
      issues.push('Moderate bundle load time');
      recommendations.push('Consider preloading critical chunks');
      score -= 10;
    }

    // Check for vendor chunk
    const hasVendorChunk = this.chunks.some(c => c.isVendor);
    if (!hasVendorChunk) {
      issues.push('No vendor chunk detected');
      recommendations.push('Separate vendor dependencies for better caching');
      score -= 15;
    }

    return {
      score: Math.max(0, score),
      issues,
      recommendations
    };
  }

  // Generate optimization report
  generateOptimizationReport(): string {
    const health = this.analyzeBundleHealth();
    const metrics = this.getMetrics();
    
    if (!metrics) {
      return 'Bundle analysis not available';
    }

    return `
Bundle Optimization Report
=========================

Overall Health Score: ${health.score}/100

Bundle Metrics:
- Total Size: ${(metrics.totalSize / 1024).toFixed(2)} KB
- Gzipped Size: ${(metrics.gzippedSize / 1024).toFixed(2)} KB
- Chunk Count: ${metrics.chunkCount}
- Load Time: ${metrics.loadTime.toFixed(2)}ms

Issues Found:
${health.issues.map(issue => `- ${issue}`).join('\n')}

Recommendations:
${health.recommendations.map(rec => `- ${rec}`).join('\n')}

Chunk Breakdown:
${this.chunks.map(chunk => 
  `- ${chunk.name}: ${(chunk.size / 1024).toFixed(2)} KB ${chunk.isVendor ? '(vendor)' : ''} ${chunk.isAsync ? '(async)' : ''}`
).join('\n')}
    `.trim();
  }
}

// Performance budget checker
export class PerformanceBudget {
  private static budgets = {
    totalSize: 500000, // 500KB
    gzippedSize: 150000, // 150KB
    chunkCount: 10,
    loadTime: 2000, // 2 seconds
    largestChunkSize: 200000 // 200KB
  };

  static checkBudget(metrics: BundleMetrics): {
    passed: boolean;
    violations: string[];
    warnings: string[];
  } {
    const violations: string[] = [];
    const warnings: string[] = [];

    // Check hard limits
    if (metrics.totalSize > this.budgets.totalSize * 1.5) {
      violations.push(`Total size (${(metrics.totalSize / 1024).toFixed(2)}KB) exceeds budget by 50%`);
    } else if (metrics.totalSize > this.budgets.totalSize) {
      warnings.push(`Total size (${(metrics.totalSize / 1024).toFixed(2)}KB) exceeds budget`);
    }

    if (metrics.gzippedSize > this.budgets.gzippedSize * 1.5) {
      violations.push(`Gzipped size (${(metrics.gzippedSize / 1024).toFixed(2)}KB) exceeds budget by 50%`);
    } else if (metrics.gzippedSize > this.budgets.gzippedSize) {
      warnings.push(`Gzipped size (${(metrics.gzippedSize / 1024).toFixed(2)}KB) exceeds budget`);
    }

    if (metrics.loadTime > this.budgets.loadTime * 2) {
      violations.push(`Load time (${metrics.loadTime.toFixed(2)}ms) exceeds budget by 100%`);
    } else if (metrics.loadTime > this.budgets.loadTime) {
      warnings.push(`Load time (${metrics.loadTime.toFixed(2)}ms) exceeds budget`);
    }

    return {
      passed: violations.length === 0,
      violations,
      warnings
    };
  }

  static updateBudgets(newBudgets: Partial<typeof PerformanceBudget.budgets>): void {
    Object.assign(this.budgets, newBudgets);
  }

  static getBudgets() {
    return { ...this.budgets };
  }
}

// Initialize bundle analyzer
if (typeof window !== 'undefined') {
  const analyzer = BundleAnalyzer.getInstance();
  
  // Initialize after DOM is loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => analyzer.initialize());
  } else {
    analyzer.initialize();
  }

  // Expose to window for debugging
  (window as any).__bundleAnalyzer = analyzer;
  (window as any).__performanceBudget = PerformanceBudget;
}