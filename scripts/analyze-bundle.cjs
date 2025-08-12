#!/usr/bin/env node

/**
 * Bundle analysis script for performance monitoring
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class BundleAnalyzer {
  constructor() {
    this.distPath = path.join(process.cwd(), 'dist');
    this.reportPath = path.join(process.cwd(), 'bundle-analysis-report.json');
    this.startTime = Date.now();
  }

  /**
   * Build the project and generate bundle analysis
   */
  async analyze() {
    console.log('🔍 Starting bundle analysis...\n');

    try {
      // Build the project
      console.log('📦 Building project...');
      execSync('npm run build', { stdio: 'inherit' });

      // Analyze bundle
      const analysis = await this.analyzeBundleSize();
      
      // Generate report
      await this.generateReport(analysis);
      
      // Display results
      this.displayResults(analysis);

    } catch (error) {
      console.error('❌ Bundle analysis failed:', error.message);
      process.exit(1);
    }
  }

  /**
   * Analyze bundle size and composition
   */
  async analyzeBundleSize() {
    if (!fs.existsSync(this.distPath)) {
      throw new Error('Build directory not found. Run npm run build first.');
    }

    const analysis = {
      timestamp: new Date().toISOString(),
      totalSize: 0,
      gzippedSize: 0,
      files: [],
      chunks: {},
      assets: {},
      recommendations: [],
    };

    // Analyze all files in dist directory
    const files = this.getAllFiles(this.distPath);
    
    for (const file of files) {
      const stats = fs.statSync(file);
      const relativePath = path.relative(this.distPath, file);
      const ext = path.extname(file);
      
      const fileInfo = {
        path: relativePath,
        size: stats.size,
        type: this.getFileType(ext),
        gzippedSize: this.estimateGzippedSize(stats.size),
      };

      analysis.files.push(fileInfo);
      analysis.totalSize += stats.size;
      analysis.gzippedSize += fileInfo.gzippedSize;

      // Categorize files
      if (ext === '.js') {
        analysis.chunks[relativePath] = fileInfo;
      } else {
        analysis.assets[relativePath] = fileInfo;
      }
    }

    // Generate recommendations
    analysis.recommendations = this.generateRecommendations(analysis);

    return analysis;
  }

  /**
   * Get all files recursively
   */
  getAllFiles(dir) {
    const files = [];
    const items = fs.readdirSync(dir);

    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stats = fs.statSync(fullPath);

      if (stats.isDirectory()) {
        files.push(...this.getAllFiles(fullPath));
      } else {
        files.push(fullPath);
      }
    }

    return files;
  }

  /**
   * Determine file type
   */
  getFileType(ext) {
    const types = {
      '.js': 'JavaScript',
      '.css': 'Stylesheet',
      '.html': 'HTML',
      '.png': 'Image',
      '.jpg': 'Image',
      '.jpeg': 'Image',
      '.svg': 'Image',
      '.gif': 'Image',
      '.woff': 'Font',
      '.woff2': 'Font',
      '.ttf': 'Font',
      '.eot': 'Font',
    };

    return types[ext] || 'Other';
  }

  /**
   * Estimate gzipped size (rough approximation)
   */
  estimateGzippedSize(size) {
    // Rough estimation: gzipped size is typically 20-30% of original
    return Math.round(size * 0.25);
  }

  /**
   * Generate optimization recommendations
   */
  generateRecommendations(analysis) {
    const recommendations = [];
    const MB = 1024 * 1024;
    const KB = 1024;

    // Check total bundle size
    if (analysis.totalSize > 2 * MB) {
      recommendations.push({
        type: 'warning',
        category: 'Bundle Size',
        message: `Total bundle size is ${this.formatSize(analysis.totalSize)} (>${this.formatSize(2 * MB)}). Consider code splitting.`,
        priority: 'high',
        action: 'npm run optimize:code-splitting',
        estimatedSavings: Math.round(analysis.totalSize * 0.3),
      });
    }

    // Check individual chunk sizes
    Object.entries(analysis.chunks).forEach(([path, info]) => {
      if (info.size > 500 * KB) {
        recommendations.push({
          type: 'warning',
          category: 'Chunk Size',
          message: `Chunk ${path} is ${this.formatSize(info.size)} (>${this.formatSize(500 * KB)}). Consider splitting.`,
          priority: 'medium',
          action: 'Split large chunks into smaller modules',
          estimatedSavings: Math.round(info.size * 0.2),
        });
      }
    });

    // Check for large assets
    Object.entries(analysis.assets).forEach(([path, info]) => {
      if (info.type === 'Image' && info.size > 100 * KB) {
        recommendations.push({
          type: 'info',
          category: 'Asset Optimization',
          message: `Image ${path} is ${this.formatSize(info.size)}. Consider optimization.`,
          priority: 'low',
          action: 'Optimize images using tools like imagemin or squoosh',
          estimatedSavings: Math.round(info.size * 0.4),
        });
      }
    });

    // Check gzipped size
    if (analysis.gzippedSize > 1 * MB) {
      recommendations.push({
        type: 'info',
        category: 'Compression',
        message: `Gzipped size is ${this.formatSize(analysis.gzippedSize)}. Ensure server compression is enabled.`,
        priority: 'medium',
        action: 'Enable Brotli compression on server',
        estimatedSavings: Math.round(analysis.gzippedSize * 0.15),
      });
    }

    // Tree shaking recommendations
    const jsFiles = analysis.files.filter(f => f.type === 'JavaScript');
    const totalJsSize = jsFiles.reduce((total, file) => total + file.size, 0);
    
    if (totalJsSize > 1 * MB) {
      recommendations.push({
        type: 'optimization',
        category: 'Tree Shaking',
        message: `JavaScript bundle is ${this.formatSize(totalJsSize)}. Optimize imports for better tree shaking.`,
        priority: 'high',
        action: 'npm run optimize:tree-shaking',
        estimatedSavings: Math.round(totalJsSize * 0.25),
      });
    }

    // Dynamic import recommendations
    if (analysis.files.length > 20) {
      recommendations.push({
        type: 'optimization',
        category: 'Dynamic Imports',
        message: 'Large number of modules detected. Consider dynamic imports for better performance.',
        priority: 'medium',
        action: 'Implement dynamic imports for route-based code splitting',
        estimatedSavings: Math.round(analysis.totalSize * 0.2),
      });
    }

    // Dependency optimization
    const vendorFiles = analysis.files.filter(f => f.path.includes('vendor') || f.path.includes('node_modules'));
    if (vendorFiles.length > 0) {
      const vendorSize = vendorFiles.reduce((total, file) => total + file.size, 0);
      if (vendorSize > 800 * KB) {
        recommendations.push({
          type: 'optimization',
          category: 'Dependency Optimization',
          message: `Vendor bundle is ${this.formatSize(vendorSize)}. Analyze dependencies for unused code.`,
          priority: 'high',
          action: 'npm run deps:analyze && npm run optimize:deps',
          estimatedSavings: Math.round(vendorSize * 0.3),
        });
      }
    }

    return recommendations;
  }

  /**
   * Format file size
   */
  formatSize(bytes) {
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
   * Generate detailed report
   */
  async generateReport(analysis) {
    // Load previous analysis for regression detection
    const previousAnalysis = this.loadPreviousAnalysis();
    const regressions = this.detectRegressions(analysis, previousAnalysis);

    const report = {
      ...analysis,
      regressions,
      summary: {
        totalFiles: analysis.files.length,
        totalSize: this.formatSize(analysis.totalSize),
        gzippedSize: this.formatSize(analysis.gzippedSize),
        compressionRatio: `${((1 - analysis.gzippedSize / analysis.totalSize) * 100).toFixed(1)}%`,
        jsChunks: Object.keys(analysis.chunks).length,
        assets: Object.keys(analysis.assets).length,
        recommendations: analysis.recommendations.length,
        regressions: regressions.length,
      },
      performance: {
        buildTime: Date.now() - this.startTime,
        analysisTime: new Date().toISOString(),
        baseline: previousAnalysis ? {
          totalSize: this.formatSize(previousAnalysis.totalSize),
          gzippedSize: this.formatSize(previousAnalysis.gzippedSize),
          timestamp: previousAnalysis.timestamp,
        } : null,
      },
    };

    fs.writeFileSync(this.reportPath, JSON.stringify(report, null, 2));
    console.log(`📊 Detailed report saved to: ${this.reportPath}`);

    // Save current analysis as baseline for future comparisons
    this.saveAsBaseline(analysis);
  }

  /**
   * Load previous analysis for comparison
   */
  loadPreviousAnalysis() {
    const baselinePath = path.join(process.cwd(), 'bundle-baseline.json');
    
    try {
      if (fs.existsSync(baselinePath)) {
        return JSON.parse(fs.readFileSync(baselinePath, 'utf8'));
      }
    } catch (error) {
      console.warn('Could not load previous analysis:', error.message);
    }
    
    return null;
  }

  /**
   * Save current analysis as baseline
   */
  saveAsBaseline(analysis) {
    const baselinePath = path.join(process.cwd(), 'bundle-baseline.json');
    
    try {
      const baseline = {
        timestamp: analysis.timestamp,
        totalSize: analysis.totalSize,
        gzippedSize: analysis.gzippedSize,
        files: analysis.files.length,
        chunks: Object.keys(analysis.chunks).length,
        assets: Object.keys(analysis.assets).length,
      };
      
      fs.writeFileSync(baselinePath, JSON.stringify(baseline, null, 2));
    } catch (error) {
      console.warn('Could not save baseline:', error.message);
    }
  }

  /**
   * Detect performance regressions
   */
  detectRegressions(current, previous) {
    if (!previous) {
      return [];
    }

    const regressions = [];
    const thresholds = {
      size: 10, // 10% increase threshold
      files: 20, // 20% increase threshold
    };

    // Check total size regression
    const sizeChange = ((current.totalSize - previous.totalSize) / previous.totalSize) * 100;
    if (sizeChange > thresholds.size) {
      regressions.push({
        type: 'size_regression',
        metric: 'Total Size',
        current: this.formatSize(current.totalSize),
        previous: this.formatSize(previous.totalSize),
        change: `+${sizeChange.toFixed(1)}%`,
        severity: sizeChange > 25 ? 'critical' : sizeChange > 15 ? 'warning' : 'info',
        message: `Bundle size increased by ${sizeChange.toFixed(1)}%`,
      });
    }

    // Check gzipped size regression
    const gzipChange = ((current.gzippedSize - previous.gzippedSize) / previous.gzippedSize) * 100;
    if (gzipChange > thresholds.size) {
      regressions.push({
        type: 'gzip_regression',
        metric: 'Gzipped Size',
        current: this.formatSize(current.gzippedSize),
        previous: this.formatSize(previous.gzippedSize),
        change: `+${gzipChange.toFixed(1)}%`,
        severity: gzipChange > 20 ? 'critical' : gzipChange > 12 ? 'warning' : 'info',
        message: `Gzipped size increased by ${gzipChange.toFixed(1)}%`,
      });
    }

    // Check file count regression
    const fileChange = ((current.files.length - previous.files) / previous.files) * 100;
    if (fileChange > thresholds.files) {
      regressions.push({
        type: 'file_regression',
        metric: 'File Count',
        current: current.files.length,
        previous: previous.files,
        change: `+${fileChange.toFixed(1)}%`,
        severity: 'info',
        message: `Number of files increased by ${fileChange.toFixed(1)}%`,
      });
    }

    return regressions;
  }

  /**
   * Display analysis results
   */
  displayResults(analysis) {
    console.log('\n📊 Bundle Analysis Results\n');
    console.log('=' .repeat(50));

    // Summary
    console.log(`📦 Total Size: ${this.formatSize(analysis.totalSize)}`);
    console.log(`🗜️  Gzipped Size: ${this.formatSize(analysis.gzippedSize)}`);
    console.log(`📁 Total Files: ${analysis.files.length}`);
    console.log(`🧩 JS Chunks: ${Object.keys(analysis.chunks).length}`);
    console.log(`🎨 Assets: ${Object.keys(analysis.assets).length}`);

    // Largest files
    console.log('\n🔍 Largest Files:');
    const sortedFiles = analysis.files
      .sort((a, b) => b.size - a.size)
      .slice(0, 10);

    sortedFiles.forEach((file, index) => {
      console.log(`  ${index + 1}. ${file.path} - ${this.formatSize(file.size)}`);
    });

    // File type breakdown
    console.log('\n📊 File Type Breakdown:');
    const typeBreakdown = {};
    analysis.files.forEach(file => {
      if (!typeBreakdown[file.type]) {
        typeBreakdown[file.type] = { count: 0, size: 0 };
      }
      typeBreakdown[file.type].count++;
      typeBreakdown[file.type].size += file.size;
    });

    Object.entries(typeBreakdown).forEach(([type, info]) => {
      console.log(`  ${type}: ${info.count} files, ${this.formatSize(info.size)}`);
    });

    // Performance Regressions
    if (analysis.regressions && analysis.regressions.length > 0) {
      console.log('\n🚨 Performance Regressions Detected:');
      analysis.regressions.forEach((reg, index) => {
        const icon = reg.severity === 'critical' ? '🔴' : 
                    reg.severity === 'warning' ? '🟡' : '🔵';
        console.log(`  ${index + 1}. ${icon} ${reg.message}`);
        console.log(`     ${reg.previous} → ${reg.current} (${reg.change})`);
      });
    }

    // Recommendations
    if (analysis.recommendations.length > 0) {
      console.log('\n💡 Optimization Recommendations:');
      analysis.recommendations.forEach((rec, index) => {
        const icon = rec.type === 'warning' ? '⚠️' : 
                    rec.type === 'optimization' ? '🔧' : 'ℹ️';
        console.log(`  ${index + 1}. ${icon} [${rec.priority.toUpperCase()}] ${rec.message}`);
        if (rec.action) {
          console.log(`     Action: ${rec.action}`);
        }
        if (rec.estimatedSavings) {
          console.log(`     Potential Savings: ${this.formatSize(rec.estimatedSavings)}`);
        }
      });
    } else {
      console.log('\n✅ No optimization recommendations - bundle looks good!');
    }

    console.log('\n' + '='.repeat(50));
    console.log('🎉 Bundle analysis complete!');
    
    if (fs.existsSync(path.join(this.distPath, 'bundle-analysis.html'))) {
      console.log('📈 Visual analysis available at: dist/bundle-analysis.html');
    }
  }
}

// Run analysis if called directly
if (require.main === module) {
  const analyzer = new BundleAnalyzer();
  analyzer.analyze().catch(console.error);
}

module.exports = BundleAnalyzer;