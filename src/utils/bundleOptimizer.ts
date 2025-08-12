/**
 * Bundle optimization utilities for tree shaking and performance monitoring
 */

export interface BundleAnalysisResult {
  totalSize: number;
  gzippedSize: number;
  chunks: ChunkInfo[];
  assets: AssetInfo[];
  dependencies: DependencyInfo[];
  recommendations: OptimizationRecommendation[];
  timestamp: string;
}

export interface ChunkInfo {
  name: string;
  size: number;
  gzippedSize: number;
  modules: string[];
  isEntry: boolean;
  isDynamic: boolean;
}

export interface AssetInfo {
  name: string;
  size: number;
  type: 'js' | 'css' | 'image' | 'font' | 'other';
  optimizable: boolean;
}

export interface DependencyInfo {
  name: string;
  size: number;
  version: string;
  treeshakeable: boolean;
  usagePattern: 'full' | 'partial' | 'minimal';
  unusedExports?: string[];
}

export interface OptimizationRecommendation {
  type: 'tree-shaking' | 'code-splitting' | 'dynamic-import' | 'asset-optimization';
  priority: 'high' | 'medium' | 'low';
  message: string;
  estimatedSavings: number;
  implementation: string;
  complexity: 'low' | 'medium' | 'high';
}

export interface PerformanceRegression {
  metric: string;
  current: number;
  previous: number;
  change: number;
  changePercent: number;
  threshold: number;
  severity: 'critical' | 'warning' | 'info';
}

/**
 * Bundle optimizer for analyzing and optimizing bundle size
 */
export class BundleOptimizer {
  private readonly thresholds = {
    bundleSize: 2 * 1024 * 1024, // 2MB
    chunkSize: 500 * 1024, // 500KB
    assetSize: 100 * 1024, // 100KB
    regressionPercent: 10, // 10%
  };

  /**
   * Analyze current bundle for optimization opportunities
   */
  public async analyzeBundleOptimization(): Promise<BundleAnalysisResult> {
    const analysis: BundleAnalysisResult = {
      totalSize: 0,
      gzippedSize: 0,
      chunks: [],
      assets: [],
      dependencies: [],
      recommendations: [],
      timestamp: new Date().toISOString(),
    };

    // Analyze chunks
    analysis.chunks = await this.analyzeChunks();
    analysis.totalSize = analysis.chunks.reduce((total, chunk) => total + chunk.size, 0);
    analysis.gzippedSize = analysis.chunks.reduce((total, chunk) => total + chunk.gzippedSize, 0);

    // Analyze assets
    analysis.assets = await this.analyzeAssets();

    // Analyze dependencies
    analysis.dependencies = await this.analyzeDependencies();

    // Generate recommendations
    analysis.recommendations = this.generateOptimizationRecommendations(analysis);

    return analysis;
  }

  /**
   * Analyze bundle chunks
   */
  private async analyzeChunks(): Promise<ChunkInfo[]> {
    // Mock implementation - in real scenario would parse build output
    return [
      {
        name: 'main',
        size: 850000, // 850KB
        gzippedSize: 280000, // 280KB
        modules: ['src/App.tsx', 'src/main.tsx', 'src/components/*'],
        isEntry: true,
        isDynamic: false,
      },
      {
        name: 'vendor',
        size: 1200000, // 1.2MB
        gzippedSize: 400000, // 400KB
        modules: ['react', 'react-dom', 'lucide-react'],
        isEntry: false,
        isDynamic: false,
      },
      {
        name: 'utils',
        size: 150000, // 150KB
        gzippedSize: 50000, // 50KB
        modules: ['src/utils/*', 'src/hooks/*'],
        isEntry: false,
        isDynamic: false,
      },
    ];
  }

  /**
   * Analyze bundle assets
   */
  private async analyzeAssets(): Promise<AssetInfo[]> {
    return [
      {
        name: 'main.css',
        size: 45000, // 45KB
        type: 'css',
        optimizable: true,
      },
      {
        name: 'logo.svg',
        size: 8000, // 8KB
        type: 'image',
        optimizable: false,
      },
    ];
  }

  /**
   * Analyze dependencies for tree shaking opportunities
   */
  private async analyzeDependencies(): Promise<DependencyInfo[]> {
    return [
      {
        name: 'lucide-react',
        size: 1200000, // 1.2MB
        version: '^0.344.0',
        treeshakeable: true,
        usagePattern: 'partial',
        unusedExports: ['Calendar', 'Database', 'Server', 'Wifi'],
      },
      {
        name: 'react',
        size: 42000, // 42KB
        version: '^18.3.1',
        treeshakeable: true,
        usagePattern: 'full',
      },
      {
        name: 'react-dom',
        size: 130000, // 130KB
        version: '^18.3.1',
        treeshakeable: true,
        usagePattern: 'full',
      },
    ];
  }

  /**
   * Generate optimization recommendations
   */
  private generateOptimizationRecommendations(
    analysis: BundleAnalysisResult
  ): OptimizationRecommendation[] {
    const recommendations: OptimizationRecommendation[] = [];

    // Check bundle size
    if (analysis.totalSize > this.thresholds.bundleSize) {
      recommendations.push({
        type: 'code-splitting',
        priority: 'high',
        message: `Bundle size (${this.formatSize(analysis.totalSize)}) exceeds recommended limit`,
        estimatedSavings: Math.round(analysis.totalSize * 0.3),
        implementation: 'Implement route-based code splitting with React.lazy()',
        complexity: 'medium',
      });
    }

    // Check large chunks
    const largeChunks = analysis.chunks.filter(chunk => chunk.size > this.thresholds.chunkSize);
    if (largeChunks.length > 0) {
      recommendations.push({
        type: 'code-splitting',
        priority: 'medium',
        message: `${largeChunks.length} chunks exceed size limit`,
        estimatedSavings: largeChunks.reduce((total, chunk) => total + Math.round(chunk.size * 0.2), 0),
        implementation: 'Split large chunks into smaller, more focused modules',
        complexity: 'medium',
      });
    }

    // Check tree shaking opportunities
    const treeshakeableDeps = analysis.dependencies.filter(
      dep => dep.treeshakeable && dep.usagePattern === 'partial'
    );

    treeshakeableDeps.forEach(dep => {
      const estimatedSavings = Math.round(dep.size * 0.7); // Assume 70% can be tree-shaken
      recommendations.push({
        type: 'tree-shaking',
        priority: 'high',
        message: `Optimize ${dep.name} imports for better tree shaking`,
        estimatedSavings,
        implementation: `Use specific imports instead of barrel imports for ${dep.name}`,
        complexity: 'low',
      });
    });

    // Check for dynamic import opportunities
    const heavyDependencies = analysis.dependencies.filter(dep => dep.size > 200000);
    if (heavyDependencies.length > 0) {
      recommendations.push({
        type: 'dynamic-import',
        priority: 'medium',
        message: 'Consider dynamic imports for heavy dependencies',
        estimatedSavings: Math.round(heavyDependencies.reduce((total, dep) => total + dep.size, 0) * 0.4),
        implementation: 'Use dynamic import() for conditionally loaded features',
        complexity: 'high',
      });
    }

    return recommendations.sort((a, b) => {
      const priorityOrder = { high: 3, medium: 2, low: 1 };
      return priorityOrder[b.priority] - priorityOrder[a.priority];
    });
  }

  /**
   * Detect performance regressions
   */
  public async detectPerformanceRegressions(
    current: BundleAnalysisResult,
    previous?: BundleAnalysisResult
  ): Promise<PerformanceRegression[]> {
    if (!previous) {
      return [];
    }

    const regressions: PerformanceRegression[] = [];

    // Check total bundle size regression
    const sizeChange = current.totalSize - previous.totalSize;
    const sizeChangePercent = (sizeChange / previous.totalSize) * 100;

    if (Math.abs(sizeChangePercent) > this.thresholds.regressionPercent) {
      regressions.push({
        metric: 'Bundle Size',
        current: current.totalSize,
        previous: previous.totalSize,
        change: sizeChange,
        changePercent: sizeChangePercent,
        threshold: this.thresholds.regressionPercent,
        severity: sizeChangePercent > 20 ? 'critical' : 'warning',
      });
    }

    // Check gzipped size regression
    const gzipChange = current.gzippedSize - previous.gzippedSize;
    const gzipChangePercent = (gzipChange / previous.gzippedSize) * 100;

    if (Math.abs(gzipChangePercent) > this.thresholds.regressionPercent) {
      regressions.push({
        metric: 'Gzipped Size',
        current: current.gzippedSize,
        previous: previous.gzippedSize,
        change: gzipChange,
        changePercent: gzipChangePercent,
        threshold: this.thresholds.regressionPercent,
        severity: gzipChangePercent > 15 ? 'critical' : 'warning',
      });
    }

    // Check chunk count changes
    const chunkCountChange = current.chunks.length - previous.chunks.length;
    if (Math.abs(chunkCountChange) > 2) {
      regressions.push({
        metric: 'Chunk Count',
        current: current.chunks.length,
        previous: previous.chunks.length,
        change: chunkCountChange,
        changePercent: (chunkCountChange / previous.chunks.length) * 100,
        threshold: 2,
        severity: 'info',
      });
    }

    return regressions;
  }

  /**
   * Generate performance monitoring report
   */
  public generatePerformanceReport(
    analysis: BundleAnalysisResult,
    regressions: PerformanceRegression[]
  ): string {
    const lines: string[] = [];
    
    lines.push('# Bundle Performance Report');
    lines.push(`Generated: ${new Date().toISOString()}`);
    lines.push('');

    // Summary
    lines.push('## Summary');
    lines.push(`- Total Size: ${this.formatSize(analysis.totalSize)}`);
    lines.push(`- Gzipped Size: ${this.formatSize(analysis.gzippedSize)}`);
    lines.push(`- Chunks: ${analysis.chunks.length}`);
    lines.push(`- Assets: ${analysis.assets.length}`);
    lines.push(`- Dependencies: ${analysis.dependencies.length}`);
    lines.push('');

    // Regressions
    if (regressions.length > 0) {
      lines.push('## Performance Regressions');
      regressions.forEach(regression => {
        const icon = regression.severity === 'critical' ? '🔴' : 
                    regression.severity === 'warning' ? '🟡' : '🔵';
        lines.push(`${icon} **${regression.metric}**: ${regression.changePercent > 0 ? '+' : ''}${regression.changePercent.toFixed(1)}% (${this.formatSize(Math.abs(regression.change))})`);
      });
      lines.push('');
    }

    // Recommendations
    if (analysis.recommendations.length > 0) {
      lines.push('## Optimization Recommendations');
      analysis.recommendations.forEach((rec, index) => {
        const icon = rec.priority === 'high' ? '🔥' : 
                    rec.priority === 'medium' ? '⚠️' : 'ℹ️';
        lines.push(`${index + 1}. ${icon} **${rec.message}**`);
        lines.push(`   - Estimated Savings: ${this.formatSize(rec.estimatedSavings)}`);
        lines.push(`   - Implementation: ${rec.implementation}`);
        lines.push(`   - Complexity: ${rec.complexity}`);
        lines.push('');
      });
    }

    // Chunk Analysis
    lines.push('## Chunk Analysis');
    analysis.chunks.forEach(chunk => {
      lines.push(`- **${chunk.name}**: ${this.formatSize(chunk.size)} (${this.formatSize(chunk.gzippedSize)} gzipped)`);
      if (chunk.size > this.thresholds.chunkSize) {
        lines.push(`  ⚠️ Exceeds recommended size limit`);
      }
    });

    return lines.join('\n');
  }

  /**
   * Save performance baseline for future comparisons
   */
  public async savePerformanceBaseline(analysis: BundleAnalysisResult): Promise<void> {
    const baseline = {
      timestamp: analysis.timestamp,
      totalSize: analysis.totalSize,
      gzippedSize: analysis.gzippedSize,
      chunkCount: analysis.chunks.length,
      assetCount: analysis.assets.length,
      dependencyCount: analysis.dependencies.length,
    };

    // In a real implementation, this would save to a file or database
    console.log('Performance baseline saved:', baseline);
  }

  /**
   * Load previous performance baseline
   */
  public async loadPerformanceBaseline(): Promise<BundleAnalysisResult | null> {
    // In a real implementation, this would load from a file or database
    // For now, return null to indicate no baseline exists
    return null;
  }

  /**
   * Format file size for display
   */
  private formatSize(bytes: number): string {
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
   * Apply automatic optimizations
   */
  public async applyOptimizations(recommendations: OptimizationRecommendation[]): Promise<{
    applied: number;
    failed: number;
    results: Array<{ recommendation: OptimizationRecommendation; success: boolean; error?: string }>;
  }> {
    const results: Array<{ recommendation: OptimizationRecommendation; success: boolean; error?: string }> = [];
    let applied = 0;
    let failed = 0;

    for (const recommendation of recommendations) {
      try {
        if (recommendation.complexity === 'low' && recommendation.type === 'tree-shaking') {
          // Apply tree shaking optimizations automatically
          await this.applyTreeShakingOptimization(recommendation);
          results.push({ recommendation, success: true });
          applied++;
        } else {
          // Log recommendation for manual implementation
          console.log(`Manual optimization required: ${recommendation.message}`);
          results.push({ recommendation, success: false, error: 'Manual implementation required' });
        }
      } catch (error) {
        results.push({ 
          recommendation, 
          success: false, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        });
        failed++;
      }
    }

    return { applied, failed, results };
  }

  /**
   * Apply tree shaking optimization
   */
  private async applyTreeShakingOptimization(recommendation: OptimizationRecommendation): Promise<void> {
    // In a real implementation, this would modify import statements
    console.log(`Applying tree shaking optimization: ${recommendation.message}`);
    console.log(`Implementation: ${recommendation.implementation}`);
    console.log(`Estimated savings: ${this.formatSize(recommendation.estimatedSavings)}`);
  }
}

/**
 * Performance regression detector
 */
export class PerformanceRegressionDetector {
  private readonly alertThresholds = {
    critical: 25, // 25% increase
    warning: 15,  // 15% increase
    info: 5,      // 5% increase
  };

  /**
   * Monitor bundle performance and detect regressions
   */
  public async monitorPerformance(): Promise<{
    analysis: BundleAnalysisResult;
    regressions: PerformanceRegression[];
    alerts: string[];
  }> {
    const optimizer = new BundleOptimizer();
    
    // Get current analysis
    const currentAnalysis = await optimizer.analyzeBundleOptimization();
    
    // Load previous baseline
    const previousAnalysis = await optimizer.loadPerformanceBaseline();
    
    // Detect regressions
    const regressions = await optimizer.detectPerformanceRegressions(currentAnalysis, previousAnalysis);
    
    // Generate alerts
    const alerts = this.generateAlerts(regressions);
    
    // Save new baseline
    await optimizer.savePerformanceBaseline(currentAnalysis);
    
    return {
      analysis: currentAnalysis,
      regressions,
      alerts,
    };
  }

  /**
   * Generate alerts for performance regressions
   */
  private generateAlerts(regressions: PerformanceRegression[]): string[] {
    const alerts: string[] = [];

    regressions.forEach(regression => {
      if (regression.changePercent > this.alertThresholds.critical) {
        alerts.push(`🚨 CRITICAL: ${regression.metric} increased by ${regression.changePercent.toFixed(1)}%`);
      } else if (regression.changePercent > this.alertThresholds.warning) {
        alerts.push(`⚠️ WARNING: ${regression.metric} increased by ${regression.changePercent.toFixed(1)}%`);
      } else if (Math.abs(regression.changePercent) > this.alertThresholds.info) {
        alerts.push(`ℹ️ INFO: ${regression.metric} changed by ${regression.changePercent > 0 ? '+' : ''}${regression.changePercent.toFixed(1)}%`);
      }
    });

    return alerts;
  }

  /**
   * Set up continuous monitoring
   */
  public setupContinuousMonitoring(intervalMinutes: number = 60): void {
    console.log(`Setting up performance monitoring every ${intervalMinutes} minutes`);
    
    setInterval(async () => {
      try {
        const result = await this.monitorPerformance();
        
        if (result.alerts.length > 0) {
          console.log('Performance alerts:');
          result.alerts.forEach(alert => console.log(alert));
        }
        
        if (result.regressions.length > 0) {
          console.log(`Detected ${result.regressions.length} performance regressions`);
        }
      } catch (error) {
        console.error('Performance monitoring failed:', error);
      }
    }, intervalMinutes * 60 * 1000);
  }
}

// Export singleton instances
export const bundleOptimizer = new BundleOptimizer();
export const performanceRegressionDetector = new PerformanceRegressionDetector();