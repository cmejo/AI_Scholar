#!/usr/bin/env node

/**
 * Bundle optimization script with tree shaking and performance monitoring
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class BundleOptimizer {
  constructor() {
    this.projectRoot = process.cwd();
    this.srcPath = path.join(this.projectRoot, 'src');
    this.reportPath = path.join(this.projectRoot, 'bundle-optimization-report.json');
  }

  /**
   * Run comprehensive bundle optimization
   */
  async optimize() {
    console.log('🚀 Starting bundle optimization...\n');

    try {
      // Step 1: Analyze current bundle
      console.log('📊 Analyzing current bundle...');
      const currentAnalysis = await this.analyzeCurrentBundle();

      // Step 2: Detect tree shaking opportunities
      console.log('🌳 Detecting tree shaking opportunities...');
      const treeShakingOpportunities = await this.detectTreeShakingOpportunities();

      // Step 3: Optimize imports
      console.log('📦 Optimizing imports...');
      const importOptimizations = await this.optimizeImports(treeShakingOpportunities);

      // Step 4: Apply code splitting recommendations
      console.log('✂️ Applying code splitting optimizations...');
      const codeSplittingResults = await this.applyCodeSplitting();

      // Step 5: Optimize dependencies
      console.log('🔧 Optimizing dependencies...');
      const dependencyOptimizations = await this.optimizeDependencies();

      // Step 6: Build and analyze optimized bundle
      console.log('🏗️ Building optimized bundle...');
      execSync('npm run build', { stdio: 'inherit' });

      const optimizedAnalysis = await this.analyzeCurrentBundle();

      // Step 7: Generate optimization report
      const report = await this.generateOptimizationReport({
        before: currentAnalysis,
        after: optimizedAnalysis,
        treeShaking: treeShakingOpportunities,
        imports: importOptimizations,
        codeSplitting: codeSplittingResults,
        dependencies: dependencyOptimizations,
      });

      this.displayResults(report);

    } catch (error) {
      console.error('❌ Bundle optimization failed:', error.message);
      process.exit(1);
    }
  }

  /**
   * Analyze current bundle
   */
  async analyzeCurrentBundle() {
    const BundleAnalyzer = require('./analyze-bundle.cjs');
    const analyzer = new BundleAnalyzer();
    
    // Build first if dist doesn't exist
    if (!fs.existsSync(path.join(this.projectRoot, 'dist'))) {
      execSync('npm run build', { stdio: 'pipe' });
    }

    return await analyzer.analyzeBundleSize();
  }

  /**
   * Detect tree shaking opportunities
   */
  async detectTreeShakingOpportunities() {
    const opportunities = [];
    const sourceFiles = this.getAllSourceFiles();

    for (const file of sourceFiles) {
      const fileOpportunities = await this.analyzeFileForTreeShaking(file);
      opportunities.push(...fileOpportunities);
    }

    return opportunities;
  }

  /**
   * Get all source files
   */
  getAllSourceFiles() {
    const files = [];
    
    const scanDirectory = (dir) => {
      if (!fs.existsSync(dir)) return;
      
      const items = fs.readdirSync(dir);
      
      for (const item of items) {
        const fullPath = path.join(dir, item);
        const stats = fs.statSync(fullPath);
        
        if (stats.isDirectory() && !item.startsWith('.')) {
          scanDirectory(fullPath);
        } else if (stats.isFile() && /\.(ts|tsx|js|jsx)$/.test(item)) {
          files.push(fullPath);
        }
      }
    };

    scanDirectory(this.srcPath);
    return files;
  }

  /**
   * Analyze file for tree shaking opportunities
   */
  async analyzeFileForTreeShaking(filePath) {
    const opportunities = [];
    
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const lines = content.split('\n');
      
      lines.forEach((line, index) => {
        // Check for lucide-react barrel imports
        const lucideMatch = line.match(/import\s*{([^}]+)}\s*from\s*['"]lucide-react['"]/);
        if (lucideMatch) {
          const icons = lucideMatch[1].split(',').map(icon => icon.trim());
          if (icons.length > 1) {
            opportunities.push({
              file: path.relative(this.projectRoot, filePath),
              line: index + 1,
              type: 'lucide-react-barrel',
              current: line.trim(),
              optimized: this.generateOptimizedLucideImport(icons),
              estimatedSavings: this.estimateLucideSavings(icons.length),
              icons: icons,
            });
          }
        }

        // Check for other barrel imports
        const barrelMatch = line.match(/import\s*{([^}]+)}\s*from\s*['"]([^'"@][^'"]*)['"]/);
        if (barrelMatch && this.isOptimizableLibrary(barrelMatch[2])) {
          const exports = barrelMatch[1].split(',').map(exp => exp.trim());
          const library = barrelMatch[2];
          
          if (exports.length > 2) {
            opportunities.push({
              file: path.relative(this.projectRoot, filePath),
              line: index + 1,
              type: 'barrel-import',
              current: line.trim(),
              optimized: this.generateOptimizedImport(exports, library),
              estimatedSavings: this.estimateLibrarySavings(library, exports.length),
              library: library,
              exports: exports,
            });
          }
        }
      });
    } catch (error) {
      console.warn(`Could not analyze ${filePath}:`, error.message);
    }
    
    return opportunities;
  }

  /**
   * Generate optimized lucide import
   */
  generateOptimizedLucideImport(icons) {
    // For now, keep the barrel import but add a comment about optimization
    const originalImport = `import { ${icons.join(', ')} } from 'lucide-react';`;
    const comment = `// TODO: Optimize to individual imports when lucide-react supports it`;
    return `${comment}\n${originalImport}`;
  }

  /**
   * Generate optimized import for other libraries
   */
  generateOptimizedImport(exports, library) {
    // For most libraries, try specific imports
    return exports
      .map(exp => `import { ${exp} } from '${library}/${exp.toLowerCase()}';`)
      .join('\n');
  }

  /**
   * Check if library is optimizable
   */
  isOptimizableLibrary(library) {
    const optimizableLibs = [
      'lodash',
      'date-fns',
      'ramda',
      '@mui/material',
      '@mui/icons-material',
    ];
    
    return optimizableLibs.some(lib => library.includes(lib));
  }

  /**
   * Estimate lucide savings
   */
  estimateLucideSavings(iconCount) {
    // Lucide-react is ~1.2MB, each icon is ~2KB
    const totalSize = 1200000; // 1.2MB
    const iconSize = 2000; // 2KB
    const usedSize = iconCount * iconSize;
    
    return Math.max(0, totalSize - usedSize);
  }

  /**
   * Estimate library savings
   */
  estimateLibrarySavings(library, exportCount) {
    const librarySizes = {
      'lodash': 500000, // 500KB
      'date-fns': 300000, // 300KB
      '@mui/material': 2000000, // 2MB
    };
    
    const librarySize = librarySizes[library] || 100000;
    const estimatedUsage = exportCount * 0.1; // 10% per export
    
    return Math.round(librarySize * (1 - estimatedUsage));
  }

  /**
   * Optimize imports
   */
  async optimizeImports(opportunities) {
    const results = {
      optimized: 0,
      failed: 0,
      totalSavings: 0,
      details: [],
    };

    for (const opportunity of opportunities) {
      try {
        // For now, skip automatic optimizations and just report opportunities
        results.details.push({
          file: opportunity.file,
          type: opportunity.type,
          savings: opportunity.estimatedSavings,
          status: 'identified',
          reason: 'Manual optimization recommended',
          current: opportunity.current,
          optimized: opportunity.optimized,
        });
      } catch (error) {
        results.failed++;
        results.details.push({
          file: opportunity.file,
          type: opportunity.type,
          status: 'failed',
          error: error.message,
        });
      }
    }

    return results;
  }

  /**
   * Optimize lucide import in file
   */
  async optimizeLucideImport(opportunity) {
    const filePath = path.join(this.projectRoot, opportunity.file);
    
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const lines = content.split('\n');
      
      // Replace the import line
      lines[opportunity.line - 1] = opportunity.optimized;
      
      const newContent = lines.join('\n');
      fs.writeFileSync(filePath, newContent, 'utf8');
      
      console.log(`✅ Optimized ${opportunity.file} (saved ~${Math.round(opportunity.estimatedSavings / 1000)}KB)`);
    } catch (error) {
      throw new Error(`Failed to optimize ${opportunity.file}: ${error.message}`);
    }
  }

  /**
   * Apply code splitting optimizations
   */
  async applyCodeSplitting() {
    const results = {
      applied: 0,
      recommendations: [],
    };

    // Check if App.tsx needs route-based code splitting
    const appPath = path.join(this.srcPath, 'App.tsx');
    if (fs.existsSync(appPath)) {
      const content = fs.readFileSync(appPath, 'utf8');
      
      // Check if already using React.lazy
      if (!content.includes('React.lazy') && !content.includes('lazy(')) {
        results.recommendations.push({
          type: 'route-splitting',
          message: 'Consider implementing route-based code splitting in App.tsx',
          implementation: 'Use React.lazy() and Suspense for route components',
          estimatedSavings: 300000, // 300KB
        });
      }
    }

    // Check for large components that could be split
    const componentFiles = this.getAllSourceFiles().filter(file => 
      file.includes('/components/') && file.endsWith('.tsx')
    );

    for (const file of componentFiles) {
      const stats = fs.statSync(file);
      if (stats.size > 10000) { // > 10KB
        const content = fs.readFileSync(file, 'utf8');
        const lines = content.split('\n').length;
        
        if (lines > 200) { // > 200 lines
          results.recommendations.push({
            type: 'component-splitting',
            file: path.relative(this.projectRoot, file),
            message: `Large component (${lines} lines) could be split`,
            implementation: 'Break into smaller, focused components',
            estimatedSavings: Math.round(stats.size * 0.3),
          });
        }
      }
    }

    return results;
  }

  /**
   * Optimize dependencies
   */
  async optimizeDependencies() {
    const results = {
      analyzed: 0,
      recommendations: [],
    };

    try {
      // Run dependency analysis
      const DependencyAnalyzer = require('./dependency-analyzer.cjs');
      const analyzer = new DependencyAnalyzer();
      const analysis = await analyzer.analyze();

      results.analyzed = analysis.unusedDependencies.length;
      
      // Add recommendations for unused dependencies
      if (analysis.unusedDependencies.length > 0) {
        results.recommendations.push({
          type: 'unused-dependencies',
          message: `Remove ${analysis.unusedDependencies.length} unused dependencies`,
          action: `npm uninstall ${analysis.unusedDependencies.map(d => d.name).join(' ')}`,
          estimatedSavings: analysis.unusedDependencies.length * 50000, // 50KB per dep
        });
      }

      // Add recommendations for heavy dependencies
      if (analysis.heavyDependencies.length > 0) {
        results.recommendations.push({
          type: 'heavy-dependencies',
          message: 'Consider optimizing heavy dependencies',
          dependencies: analysis.heavyDependencies.slice(0, 5).map(d => `${d.name}: ${d.size}`),
          estimatedSavings: 200000, // 200KB
        });
      }

    } catch (error) {
      console.warn('Could not analyze dependencies:', error.message);
    }

    return results;
  }

  /**
   * Generate optimization report
   */
  async generateOptimizationReport(data) {
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        beforeSize: this.formatSize(data.before.totalSize),
        afterSize: this.formatSize(data.after.totalSize),
        sizeDifference: this.formatSize(data.before.totalSize - data.after.totalSize),
        percentageImprovement: ((data.before.totalSize - data.after.totalSize) / data.before.totalSize * 100).toFixed(1),
        beforeGzipped: this.formatSize(data.before.gzippedSize),
        afterGzipped: this.formatSize(data.after.gzippedSize),
        gzippedImprovement: ((data.before.gzippedSize - data.after.gzippedSize) / data.before.gzippedSize * 100).toFixed(1),
      },
      optimizations: {
        treeShaking: {
          opportunities: data.treeShaking.length,
          applied: data.imports.optimized,
          failed: data.imports.failed,
          totalSavings: this.formatSize(data.imports.totalSavings),
        },
        codeSplitting: {
          recommendations: data.codeSplitting.recommendations.length,
          applied: data.codeSplitting.applied,
        },
        dependencies: {
          analyzed: data.dependencies.analyzed,
          recommendations: data.dependencies.recommendations.length,
        },
      },
      details: {
        treeShakingOpportunities: data.treeShaking,
        importOptimizations: data.imports.details,
        codeSplittingRecommendations: data.codeSplitting.recommendations,
        dependencyRecommendations: data.dependencies.recommendations,
      },
    };

    fs.writeFileSync(this.reportPath, JSON.stringify(report, null, 2));
    console.log(`📊 Optimization report saved to: ${this.reportPath}`);

    return report;
  }

  /**
   * Display optimization results
   */
  displayResults(report) {
    console.log('\n🎉 Bundle Optimization Complete!\n');
    console.log('=' .repeat(50));

    // Summary
    console.log('📊 Optimization Summary:');
    console.log(`  Bundle Size: ${report.summary.beforeSize} → ${report.summary.afterSize}`);
    console.log(`  Improvement: ${report.summary.sizeDifference} (${report.summary.percentageImprovement}%)`);
    console.log(`  Gzipped: ${report.summary.beforeGzipped} → ${report.summary.afterGzipped}`);
    console.log(`  Gzipped Improvement: ${report.summary.gzippedImprovement}%`);

    // Tree Shaking Results
    console.log('\n🌳 Tree Shaking Results:');
    console.log(`  Opportunities Found: ${report.optimizations.treeShaking.opportunities}`);
    console.log(`  Optimizations Applied: ${report.optimizations.treeShaking.applied}`);
    console.log(`  Failed: ${report.optimizations.treeShaking.failed}`);
    console.log(`  Estimated Savings: ${report.optimizations.treeShaking.totalSavings}`);

    // Code Splitting
    if (report.optimizations.codeSplitting.recommendations > 0) {
      console.log('\n✂️ Code Splitting Recommendations:');
      report.details.codeSplittingRecommendations.forEach((rec, index) => {
        console.log(`  ${index + 1}. ${rec.message}`);
        console.log(`     Implementation: ${rec.implementation}`);
        if (rec.file) {
          console.log(`     File: ${rec.file}`);
        }
      });
    }

    // Dependency Optimization
    if (report.optimizations.dependencies.recommendations > 0) {
      console.log('\n🔧 Dependency Recommendations:');
      report.details.dependencyRecommendations.forEach((rec, index) => {
        console.log(`  ${index + 1}. ${rec.message}`);
        if (rec.action) {
          console.log(`     Action: ${rec.action}`);
        }
      });
    }

    console.log('\n' + '='.repeat(50));
    console.log('✨ Optimization complete! Check the report for detailed information.');
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
}

// Run optimization if called directly
if (require.main === module) {
  const optimizer = new BundleOptimizer();
  optimizer.optimize().catch(console.error);
}

module.exports = BundleOptimizer;