#!/usr/bin/env node

/**
 * Tree shaking analysis script - analyzes without modifying files
 */

const fs = require('fs');
const path = require('path');

class TreeShakingAnalyzer {
  constructor() {
    this.projectRoot = process.cwd();
    this.srcPath = path.join(this.projectRoot, 'src');
    this.reportPath = path.join(this.projectRoot, 'tree-shaking-analysis.json');
  }

  /**
   * Analyze tree shaking opportunities
   */
  async analyze() {
    console.log('🌳 Analyzing tree shaking opportunities...\n');

    try {
      const sourceFiles = this.getAllSourceFiles();
      const opportunities = [];

      for (const file of sourceFiles) {
        const fileOpportunities = await this.analyzeFile(file);
        opportunities.push(...fileOpportunities);
      }

      const report = this.generateReport(opportunities);
      await this.saveReport(report);
      this.displayResults(report);

    } catch (error) {
      console.error('❌ Tree shaking analysis failed:', error.message);
      process.exit(1);
    }
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
   * Analyze a single file
   */
  async analyzeFile(filePath) {
    const opportunities = [];
    
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const lines = content.split('\n');
      
      lines.forEach((line, index) => {
        // Analyze lucide-react imports
        const lucideMatch = line.match(/import\s*{([^}]+)}\s*from\s*['"]lucide-react['"]/);
        if (lucideMatch) {
          const icons = lucideMatch[1].split(',').map(icon => icon.trim());
          if (icons.length > 1) {
            opportunities.push({
              file: path.relative(this.projectRoot, filePath),
              line: index + 1,
              type: 'lucide-react-barrel',
              current: line.trim(),
              iconCount: icons.length,
              icons: icons,
              estimatedSavings: this.estimateLucideSavings(icons.length),
              recommendation: 'Consider using individual icon imports when available',
            });
          }
        }

        // Analyze other potential barrel imports
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
              library: library,
              exportCount: exports.length,
              exports: exports,
              estimatedSavings: this.estimateLibrarySavings(library, exports.length),
              recommendation: `Consider individual imports for ${library}`,
            });
          }
        }

        // Analyze large imports
        if (line.includes('import') && line.length > 100) {
          opportunities.push({
            file: path.relative(this.projectRoot, filePath),
            line: index + 1,
            type: 'large-import',
            current: line.trim(),
            length: line.length,
            recommendation: 'Consider breaking into multiple import statements',
          });
        }
      });
    } catch (error) {
      console.warn(`Could not analyze ${filePath}:`, error.message);
    }
    
    return opportunities;
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
      'react-router-dom',
    ];
    
    return optimizableLibs.some(lib => library.includes(lib));
  }

  /**
   * Estimate lucide savings
   */
  estimateLucideSavings(iconCount) {
    // Conservative estimate: each unused icon saves ~2KB
    const totalIcons = 1000; // Approximate total icons in lucide-react
    const usedIcons = iconCount;
    const unusedIcons = totalIcons - usedIcons;
    
    return unusedIcons * 2000; // 2KB per unused icon
  }

  /**
   * Estimate library savings
   */
  estimateLibrarySavings(library, exportCount) {
    const librarySizes = {
      'lodash': 500000, // 500KB
      'date-fns': 300000, // 300KB
      '@mui/material': 2000000, // 2MB
      'react-router-dom': 250000, // 250KB
    };
    
    const librarySize = librarySizes[library] || 100000;
    const estimatedUsage = Math.min(exportCount * 0.1, 0.8); // Max 80% usage
    
    return Math.round(librarySize * (1 - estimatedUsage));
  }

  /**
   * Generate analysis report
   */
  generateReport(opportunities) {
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalFiles: this.getAllSourceFiles().length,
        opportunitiesFound: opportunities.length,
        totalPotentialSavings: opportunities.reduce((total, opp) => total + (opp.estimatedSavings || 0), 0),
      },
      byType: {},
      opportunities: opportunities,
      recommendations: [],
    };

    // Group by type
    opportunities.forEach(opp => {
      if (!report.byType[opp.type]) {
        report.byType[opp.type] = {
          count: 0,
          totalSavings: 0,
          files: new Set(),
        };
      }
      report.byType[opp.type].count++;
      report.byType[opp.type].totalSavings += opp.estimatedSavings || 0;
      report.byType[opp.type].files.add(opp.file);
    });

    // Convert sets to arrays for JSON serialization
    Object.keys(report.byType).forEach(type => {
      report.byType[type].files = Array.from(report.byType[type].files);
    });

    // Generate recommendations
    if (report.byType['lucide-react-barrel']) {
      const lucideData = report.byType['lucide-react-barrel'];
      report.recommendations.push({
        priority: 'high',
        type: 'lucide-optimization',
        message: `Found ${lucideData.count} lucide-react barrel imports across ${lucideData.files.length} files`,
        action: 'Consider using a custom icon component or wait for lucide-react to support individual imports',
        estimatedSavings: lucideData.totalSavings,
      });
    }

    if (report.byType['barrel-import']) {
      const barrelData = report.byType['barrel-import'];
      report.recommendations.push({
        priority: 'medium',
        type: 'barrel-optimization',
        message: `Found ${barrelData.count} barrel imports that could be optimized`,
        action: 'Replace barrel imports with specific imports where supported',
        estimatedSavings: barrelData.totalSavings,
      });
    }

    if (report.summary.totalPotentialSavings > 500000) { // > 500KB
      report.recommendations.push({
        priority: 'high',
        type: 'code-splitting',
        message: 'Large potential savings detected - consider code splitting',
        action: 'Implement dynamic imports and route-based code splitting',
        estimatedSavings: Math.round(report.summary.totalPotentialSavings * 0.3),
      });
    }

    return report;
  }

  /**
   * Save report to file
   */
  async saveReport(report) {
    fs.writeFileSync(this.reportPath, JSON.stringify(report, null, 2));
    console.log(`📊 Tree shaking analysis saved to: ${this.reportPath}`);
  }

  /**
   * Display results
   */
  displayResults(report) {
    console.log('\n🌳 Tree Shaking Analysis Results\n');
    console.log('=' .repeat(50));

    // Summary
    console.log(`📁 Files Analyzed: ${report.summary.totalFiles}`);
    console.log(`🎯 Opportunities Found: ${report.summary.opportunitiesFound}`);
    console.log(`💾 Potential Savings: ${this.formatSize(report.summary.totalPotentialSavings)}`);

    // By type breakdown
    if (Object.keys(report.byType).length > 0) {
      console.log('\n📊 Opportunities by Type:');
      Object.entries(report.byType).forEach(([type, data]) => {
        console.log(`  ${type}: ${data.count} opportunities, ${this.formatSize(data.totalSavings)} potential savings`);
        console.log(`    Files affected: ${data.files.length}`);
      });
    }

    // Top opportunities
    const topOpportunities = report.opportunities
      .filter(opp => opp.estimatedSavings)
      .sort((a, b) => b.estimatedSavings - a.estimatedSavings)
      .slice(0, 10);

    if (topOpportunities.length > 0) {
      console.log('\n🔝 Top Optimization Opportunities:');
      topOpportunities.forEach((opp, index) => {
        console.log(`  ${index + 1}. ${opp.file}:${opp.line} - ${this.formatSize(opp.estimatedSavings)}`);
        console.log(`     Type: ${opp.type}`);
        console.log(`     ${opp.recommendation}`);
      });
    }

    // Recommendations
    if (report.recommendations.length > 0) {
      console.log('\n💡 Recommendations:');
      report.recommendations.forEach((rec, index) => {
        const icon = rec.priority === 'high' ? '🔥' : 
                    rec.priority === 'medium' ? '⚠️' : 'ℹ️';
        console.log(`  ${index + 1}. ${icon} [${rec.priority.toUpperCase()}] ${rec.message}`);
        console.log(`     Action: ${rec.action}`);
        if (rec.estimatedSavings) {
          console.log(`     Potential Savings: ${this.formatSize(rec.estimatedSavings)}`);
        }
      });
    }

    console.log('\n' + '='.repeat(50));
    console.log('✨ Tree shaking analysis complete!');
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

// Run analysis if called directly
if (require.main === module) {
  const analyzer = new TreeShakingAnalyzer();
  analyzer.analyze().catch(console.error);
}

module.exports = TreeShakingAnalyzer;