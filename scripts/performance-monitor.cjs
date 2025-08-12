#!/usr/bin/env node

/**
 * Comprehensive performance monitoring script
 * Combines bundle analysis, dependency analysis, and tree shaking analysis
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class PerformanceMonitor {
  constructor() {
    this.projectRoot = process.cwd();
    this.reportPath = path.join(this.projectRoot, 'performance-monitoring-report.json');
    this.startTime = Date.now();
  }

  /**
   * Run comprehensive performance monitoring
   */
  async monitor() {
    console.log('🚀 Starting comprehensive performance monitoring...\n');

    try {
      const report = {
        timestamp: new Date().toISOString(),
        monitoring: {
          startTime: this.startTime,
          endTime: null,
          duration: null,
        },
        bundle: null,
        dependencies: null,
        treeShaking: null,
        performance: null,
        alerts: [],
        recommendations: [],
        summary: {},
      };

      // Step 1: Bundle Analysis
      console.log('📦 Running bundle analysis...');
      report.bundle = await this.runBundleAnalysis();

      // Step 2: Dependency Analysis
      console.log('🔍 Running dependency analysis...');
      report.dependencies = await this.runDependencyAnalysis();

      // Step 3: Tree Shaking Analysis
      console.log('🌳 Running tree shaking analysis...');
      report.treeShaking = await this.runTreeShakingAnalysis();

      // Step 4: Performance Analysis
      console.log('⚡ Analyzing performance metrics...');
      report.performance = await this.analyzePerformance(report);

      // Step 5: Generate Alerts
      console.log('🚨 Checking for performance alerts...');
      report.alerts = this.generateAlerts(report);

      // Step 6: Generate Recommendations
      console.log('💡 Generating optimization recommendations...');
      report.recommendations = this.generateRecommendations(report);

      // Step 7: Create Summary
      report.summary = this.createSummary(report);

      // Finalize timing
      report.monitoring.endTime = Date.now();
      report.monitoring.duration = report.monitoring.endTime - report.monitoring.startTime;

      // Save and display report
      await this.saveReport(report);
      this.displayResults(report);

      // Return exit code based on alerts
      const criticalAlerts = report.alerts.filter(alert => alert.severity === 'critical');
      if (criticalAlerts.length > 0) {
        console.log(`\n❌ ${criticalAlerts.length} critical performance issues detected!`);
        process.exit(1);
      }

    } catch (error) {
      console.error('❌ Performance monitoring failed:', error.message);
      process.exit(1);
    }
  }

  /**
   * Run bundle analysis
   */
  async runBundleAnalysis() {
    try {
      // Build if needed
      if (!fs.existsSync(path.join(this.projectRoot, 'dist'))) {
        execSync('npm run build', { stdio: 'pipe' });
      }

      execSync('npm run bundle:analyze', { stdio: 'pipe' });
      
      const reportPath = path.join(this.projectRoot, 'bundle-analysis-report.json');
      if (fs.existsSync(reportPath)) {
        return JSON.parse(fs.readFileSync(reportPath, 'utf8'));
      }
    } catch (error) {
      console.warn('Bundle analysis failed:', error.message);
    }
    
    return null;
  }

  /**
   * Run dependency analysis
   */
  async runDependencyAnalysis() {
    try {
      execSync('npm run deps:analyze', { stdio: 'pipe' });
      
      const reportPath = path.join(this.projectRoot, 'dependency-analysis-report.json');
      if (fs.existsSync(reportPath)) {
        return JSON.parse(fs.readFileSync(reportPath, 'utf8'));
      }
    } catch (error) {
      console.warn('Dependency analysis failed:', error.message);
    }
    
    return null;
  }

  /**
   * Run tree shaking analysis
   */
  async runTreeShakingAnalysis() {
    try {
      execSync('npm run optimize:tree-shaking', { stdio: 'pipe' });
      
      const reportPath = path.join(this.projectRoot, 'tree-shaking-analysis.json');
      if (fs.existsSync(reportPath)) {
        return JSON.parse(fs.readFileSync(reportPath, 'utf8'));
      }
    } catch (error) {
      console.warn('Tree shaking analysis failed:', error.message);
    }
    
    return null;
  }

  /**
   * Analyze performance metrics
   */
  async analyzePerformance(report) {
    const performance = {
      bundleSize: {
        total: 0,
        gzipped: 0,
        chunks: 0,
        assets: 0,
      },
      dependencies: {
        total: 0,
        unused: 0,
        heavy: 0,
      },
      treeShaking: {
        opportunities: 0,
        potentialSavings: 0,
      },
      scores: {},
    };

    // Bundle metrics
    if (report.bundle) {
      performance.bundleSize.total = this.parseSizeString(report.bundle.summary?.totalSize || '0 B');
      performance.bundleSize.gzipped = this.parseSizeString(report.bundle.summary?.gzippedSize || '0 B');
      performance.bundleSize.chunks = report.bundle.summary?.jsChunks || 0;
      performance.bundleSize.assets = report.bundle.summary?.assets || 0;
    }

    // Dependency metrics
    if (report.dependencies) {
      performance.dependencies.total = (report.dependencies.summary?.totalDependencies || 0) + 
                                     (report.dependencies.summary?.totalDevDependencies || 0);
      performance.dependencies.unused = report.dependencies.summary?.unusedCount || 0;
      performance.dependencies.heavy = report.dependencies.summary?.heavyCount || 0;
    }

    // Tree shaking metrics
    if (report.treeShaking) {
      performance.treeShaking.opportunities = report.treeShaking.summary?.opportunitiesFound || 0;
      performance.treeShaking.potentialSavings = report.treeShaking.summary?.totalPotentialSavings || 0;
    }

    // Calculate performance scores (0-100)
    performance.scores = {
      bundleSize: this.calculateBundleSizeScore(performance.bundleSize.total),
      dependencies: this.calculateDependencyScore(performance.dependencies),
      treeShaking: this.calculateTreeShakingScore(performance.treeShaking),
      overall: 0,
    };

    // Calculate overall score
    performance.scores.overall = Math.round(
      (performance.scores.bundleSize + performance.scores.dependencies + performance.scores.treeShaking) / 3
    );

    return performance;
  }

  /**
   * Parse size string to bytes
   */
  parseSizeString(sizeStr) {
    const match = sizeStr.match(/^([\d.]+)\s*(B|KB|MB|GB)$/);
    if (!match) return 0;

    const value = parseFloat(match[1]);
    const unit = match[2];

    const multipliers = {
      'B': 1,
      'KB': 1024,
      'MB': 1024 * 1024,
      'GB': 1024 * 1024 * 1024,
    };

    return Math.round(value * multipliers[unit]);
  }

  /**
   * Calculate bundle size score
   */
  calculateBundleSizeScore(totalSize) {
    // Score based on bundle size thresholds
    if (totalSize <= 500 * 1024) return 100; // <= 500KB: Excellent
    if (totalSize <= 1024 * 1024) return 90;  // <= 1MB: Very Good
    if (totalSize <= 2 * 1024 * 1024) return 75; // <= 2MB: Good
    if (totalSize <= 5 * 1024 * 1024) return 50; // <= 5MB: Fair
    return 25; // > 5MB: Poor
  }

  /**
   * Calculate dependency score
   */
  calculateDependencyScore(deps) {
    let score = 100;
    
    // Penalize unused dependencies
    if (deps.unused > 0) {
      score -= Math.min(deps.unused * 10, 30); // Max 30 point penalty
    }
    
    // Penalize heavy dependencies
    if (deps.heavy > 5) {
      score -= Math.min((deps.heavy - 5) * 5, 20); // Max 20 point penalty
    }
    
    return Math.max(score, 0);
  }

  /**
   * Calculate tree shaking score
   */
  calculateTreeShakingScore(treeShaking) {
    if (treeShaking.opportunities === 0) return 100; // No opportunities = perfect
    
    // Score based on potential savings
    const savingsKB = treeShaking.potentialSavings / 1024;
    if (savingsKB <= 50) return 90;   // <= 50KB: Very Good
    if (savingsKB <= 200) return 75;  // <= 200KB: Good
    if (savingsKB <= 500) return 50;  // <= 500KB: Fair
    return 25; // > 500KB: Poor
  }

  /**
   * Generate performance alerts
   */
  generateAlerts(report) {
    const alerts = [];

    // Bundle size alerts
    if (report.performance?.bundleSize.total > 5 * 1024 * 1024) { // > 5MB
      alerts.push({
        type: 'bundle-size',
        severity: 'critical',
        message: `Bundle size (${this.formatSize(report.performance.bundleSize.total)}) exceeds 5MB limit`,
        recommendation: 'Implement code splitting and remove unused dependencies',
      });
    } else if (report.performance?.bundleSize.total > 2 * 1024 * 1024) { // > 2MB
      alerts.push({
        type: 'bundle-size',
        severity: 'warning',
        message: `Bundle size (${this.formatSize(report.performance.bundleSize.total)}) exceeds 2MB recommended limit`,
        recommendation: 'Consider code splitting and dependency optimization',
      });
    }

    // Performance regression alerts
    if (report.bundle?.regressions) {
      report.bundle.regressions.forEach(regression => {
        alerts.push({
          type: 'regression',
          severity: regression.severity,
          message: regression.message,
          recommendation: 'Review recent changes that may have increased bundle size',
        });
      });
    }

    // Dependency alerts
    if (report.dependencies?.summary?.unusedCount > 5) {
      alerts.push({
        type: 'dependencies',
        severity: 'warning',
        message: `${report.dependencies.summary.unusedCount} unused dependencies detected`,
        recommendation: 'Remove unused dependencies to reduce bundle size',
      });
    }

    // Tree shaking alerts
    if (report.treeShaking?.summary?.totalPotentialSavings > 500 * 1024) { // > 500KB
      alerts.push({
        type: 'tree-shaking',
        severity: 'warning',
        message: `${this.formatSize(report.treeShaking.summary.totalPotentialSavings)} potential savings from tree shaking`,
        recommendation: 'Optimize imports to enable better tree shaking',
      });
    }

    // Overall performance score alert
    if (report.performance?.scores.overall < 50) {
      alerts.push({
        type: 'performance',
        severity: 'critical',
        message: `Overall performance score is low (${report.performance.scores.overall}/100)`,
        recommendation: 'Address bundle size, dependencies, and tree shaking issues',
      });
    }

    return alerts;
  }

  /**
   * Generate optimization recommendations
   */
  generateRecommendations(report) {
    const recommendations = [];

    // Bundle recommendations
    if (report.bundle?.recommendations) {
      report.bundle.recommendations.forEach(rec => {
        recommendations.push({
          category: 'bundle',
          priority: rec.priority,
          message: rec.message,
          action: rec.action,
          estimatedSavings: rec.estimatedSavings,
        });
      });
    }

    // Dependency recommendations
    if (report.dependencies?.recommendations) {
      report.dependencies.recommendations.forEach(rec => {
        recommendations.push({
          category: 'dependencies',
          priority: rec.priority,
          message: rec.message,
          action: rec.action,
          estimatedSavings: rec.estimatedSavings,
        });
      });
    }

    // Tree shaking recommendations
    if (report.treeShaking?.recommendations) {
      report.treeShaking.recommendations.forEach(rec => {
        recommendations.push({
          category: 'tree-shaking',
          priority: rec.priority,
          message: rec.message,
          action: rec.action,
          estimatedSavings: rec.estimatedSavings,
        });
      });
    }

    // Sort by priority and estimated savings
    return recommendations.sort((a, b) => {
      const priorityOrder = { high: 3, medium: 2, low: 1 };
      const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
      if (priorityDiff !== 0) return priorityDiff;
      
      return (b.estimatedSavings || 0) - (a.estimatedSavings || 0);
    });
  }

  /**
   * Create performance summary
   */
  createSummary(report) {
    return {
      overallScore: report.performance?.scores.overall || 0,
      bundleSize: report.performance?.bundleSize.total || 0,
      gzippedSize: report.performance?.bundleSize.gzipped || 0,
      totalDependencies: report.performance?.dependencies.total || 0,
      unusedDependencies: report.performance?.dependencies.unused || 0,
      treeShakingOpportunities: report.performance?.treeShaking.opportunities || 0,
      potentialSavings: report.performance?.treeShaking.potentialSavings || 0,
      alertsCount: report.alerts?.length || 0,
      criticalAlerts: report.alerts?.filter(a => a.severity === 'critical').length || 0,
      recommendationsCount: report.recommendations?.length || 0,
      monitoringDuration: report.monitoring?.duration || 0,
    };
  }

  /**
   * Save performance report
   */
  async saveReport(report) {
    fs.writeFileSync(this.reportPath, JSON.stringify(report, null, 2));
    console.log(`📊 Performance monitoring report saved to: ${this.reportPath}`);
  }

  /**
   * Display monitoring results
   */
  displayResults(report) {
    console.log('\n🎯 Performance Monitoring Results\n');
    console.log('=' .repeat(60));

    // Overall Score
    const score = report.summary.overallScore;
    const scoreIcon = score >= 90 ? '🟢' : score >= 70 ? '🟡' : '🔴';
    console.log(`${scoreIcon} Overall Performance Score: ${score}/100`);

    // Key Metrics
    console.log('\n📊 Key Metrics:');
    console.log(`  Bundle Size: ${this.formatSize(report.summary.bundleSize)}`);
    console.log(`  Gzipped Size: ${this.formatSize(report.summary.gzippedSize)}`);
    console.log(`  Dependencies: ${report.summary.totalDependencies} (${report.summary.unusedDependencies} unused)`);
    console.log(`  Tree Shaking: ${report.summary.treeShakingOpportunities} opportunities`);
    console.log(`  Potential Savings: ${this.formatSize(report.summary.potentialSavings)}`);

    // Performance Scores
    if (report.performance?.scores) {
      console.log('\n🎯 Performance Scores:');
      console.log(`  Bundle Size: ${report.performance.scores.bundleSize}/100`);
      console.log(`  Dependencies: ${report.performance.scores.dependencies}/100`);
      console.log(`  Tree Shaking: ${report.performance.scores.treeShaking}/100`);
    }

    // Alerts
    if (report.alerts.length > 0) {
      console.log('\n🚨 Performance Alerts:');
      report.alerts.forEach((alert, index) => {
        const icon = alert.severity === 'critical' ? '🔴' : 
                    alert.severity === 'warning' ? '🟡' : '🔵';
        console.log(`  ${index + 1}. ${icon} [${alert.severity.toUpperCase()}] ${alert.message}`);
        console.log(`     Recommendation: ${alert.recommendation}`);
      });
    }

    // Top Recommendations
    const topRecs = report.recommendations.slice(0, 5);
    if (topRecs.length > 0) {
      console.log('\n💡 Top Optimization Recommendations:');
      topRecs.forEach((rec, index) => {
        const icon = rec.priority === 'high' ? '🔥' : 
                    rec.priority === 'medium' ? '⚠️' : 'ℹ️';
        console.log(`  ${index + 1}. ${icon} [${rec.priority.toUpperCase()}] ${rec.message}`);
        if (rec.action) {
          console.log(`     Action: ${rec.action}`);
        }
        if (rec.estimatedSavings) {
          console.log(`     Potential Savings: ${this.formatSize(rec.estimatedSavings)}`);
        }
      });
    }

    // Summary
    console.log('\n📈 Summary:');
    console.log(`  Monitoring Duration: ${(report.summary.monitoringDuration / 1000).toFixed(1)}s`);
    console.log(`  Alerts: ${report.summary.alertsCount} (${report.summary.criticalAlerts} critical)`);
    console.log(`  Recommendations: ${report.summary.recommendationsCount}`);

    console.log('\n' + '='.repeat(60));
    
    if (report.summary.criticalAlerts > 0) {
      console.log('❌ Critical performance issues detected! Please address them before deployment.');
    } else if (report.summary.alertsCount > 0) {
      console.log('⚠️ Performance warnings detected. Consider addressing them for optimal performance.');
    } else {
      console.log('✅ No critical performance issues detected. Great job!');
    }
  }

  /**
   * Format file size
   */
  formatSize(bytes) {
    const KB = 1024;
    const MB = KB * 1024;
    const GB = MB * 1024;

    if (bytes >= GB) {
      return `${(bytes / GB).toFixed(2)} GB`;
    } else if (bytes >= MB) {
      return `${(bytes / MB).toFixed(2)} MB`;
    } else if (bytes >= KB) {
      return `${(bytes / KB).toFixed(2)} KB`;
    } else {
      return `${bytes} B`;
    }
  }
}

// Run monitoring if called directly
if (require.main === module) {
  const monitor = new PerformanceMonitor();
  monitor.monitor().catch(console.error);
}

module.exports = PerformanceMonitor;