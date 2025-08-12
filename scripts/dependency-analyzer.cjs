#!/usr/bin/env node

/**
 * Dependency analyzer for identifying unused dependencies and optimization opportunities
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class DependencyAnalyzer {
  constructor() {
    this.projectRoot = process.cwd();
    this.packageJsonPath = path.join(this.projectRoot, 'package.json');
    this.srcPath = path.join(this.projectRoot, 'src');
    this.reportPath = path.join(this.projectRoot, 'dependency-analysis-report.json');
  }

  /**
   * Analyze project dependencies
   */
  async analyze() {
    console.log('🔍 Starting dependency analysis...\n');

    try {
      const packageJson = this.loadPackageJson();
      const sourceFiles = this.getAllSourceFiles();
      const imports = this.extractImports(sourceFiles);
      
      const analysis = {
        timestamp: new Date().toISOString(),
        dependencies: this.analyzeDependencies(packageJson, imports),
        devDependencies: this.analyzeDevDependencies(packageJson, imports),
        unusedDependencies: this.findUnusedDependencies(packageJson, imports),
        heavyDependencies: await this.findHeavyDependencies(packageJson),
        duplicateDependencies: this.findDuplicateDependencies(),
        recommendations: [],
      };

      analysis.recommendations = this.generateRecommendations(analysis);

      await this.generateReport(analysis);
      this.displayResults(analysis);

    } catch (error) {
      console.error('❌ Dependency analysis failed:', error.message);
      process.exit(1);
    }
  }

  /**
   * Load package.json
   */
  loadPackageJson() {
    if (!fs.existsSync(this.packageJsonPath)) {
      throw new Error('package.json not found');
    }

    return JSON.parse(fs.readFileSync(this.packageJsonPath, 'utf8'));
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
        
        if (stats.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
          scanDirectory(fullPath);
        } else if (stats.isFile() && /\.(ts|tsx|js|jsx)$/.test(item)) {
          files.push(fullPath);
        }
      }
    };

    scanDirectory(this.srcPath);
    
    // Also check config files
    const configFiles = [
      'vite.config.ts',
      'vitest.config.ts',
      'tailwind.config.js',
      'postcss.config.js',
      'eslint.config.js',
    ];

    configFiles.forEach(file => {
      const filePath = path.join(this.projectRoot, file);
      if (fs.existsSync(filePath)) {
        files.push(filePath);
      }
    });

    return files;
  }

  /**
   * Extract imports from source files
   */
  extractImports(files) {
    const imports = new Set();
    const importRegex = /(?:import|require)\s*\(?[^'"]*['"]([^'"]+)['"]/g;
    
    files.forEach(file => {
      try {
        const content = fs.readFileSync(file, 'utf8');
        let match;
        
        while ((match = importRegex.exec(content)) !== null) {
          const importPath = match[1];
          
          // Skip relative imports
          if (importPath.startsWith('.') || importPath.startsWith('/')) {
            continue;
          }
          
          // Extract package name (handle scoped packages)
          let packageName = importPath;
          if (importPath.startsWith('@')) {
            const parts = importPath.split('/');
            packageName = parts.slice(0, 2).join('/');
          } else {
            packageName = importPath.split('/')[0];
          }
          
          imports.add(packageName);
        }
      } catch (error) {
        console.warn(`Warning: Could not read file ${file}:`, error.message);
      }
    });

    return imports;
  }

  /**
   * Analyze dependencies
   */
  analyzeDependencies(packageJson, imports) {
    const dependencies = packageJson.dependencies || {};
    const analysis = {};

    Object.keys(dependencies).forEach(dep => {
      analysis[dep] = {
        version: dependencies[dep],
        used: imports.has(dep),
        type: 'dependency',
      };
    });

    return analysis;
  }

  /**
   * Analyze dev dependencies
   */
  analyzeDevDependencies(packageJson, imports) {
    const devDependencies = packageJson.devDependencies || {};
    const analysis = {};

    Object.keys(devDependencies).forEach(dep => {
      analysis[dep] = {
        version: devDependencies[dep],
        used: imports.has(dep) || this.isToolingDependency(dep),
        type: 'devDependency',
      };
    });

    return analysis;
  }

  /**
   * Check if dependency is a tooling dependency (always considered used)
   */
  isToolingDependency(dep) {
    const toolingDeps = [
      'vite',
      'vitest',
      'eslint',
      'prettier',
      'typescript',
      'tailwindcss',
      'postcss',
      'autoprefixer',
      'husky',
      'lint-staged',
      '@vitejs/plugin-react',
      '@testing-library/react',
      '@testing-library/jest-dom',
      '@testing-library/user-event',
      'jsdom',
      'rollup-plugin-visualizer',
    ];

    return toolingDeps.some(toolDep => dep.includes(toolDep));
  }

  /**
   * Find unused dependencies
   */
  findUnusedDependencies(packageJson, imports) {
    const unused = [];
    const allDeps = {
      ...packageJson.dependencies,
      ...packageJson.devDependencies,
    };

    Object.keys(allDeps).forEach(dep => {
      if (!imports.has(dep) && !this.isToolingDependency(dep)) {
        unused.push({
          name: dep,
          version: allDeps[dep],
          type: packageJson.dependencies?.[dep] ? 'dependency' : 'devDependency',
        });
      }
    });

    return unused;
  }

  /**
   * Find heavy dependencies (requires npm ls)
   */
  async findHeavyDependencies(packageJson) {
    const heavy = [];
    
    try {
      // Get package sizes (this is a simplified approach)
      const dependencies = { ...packageJson.dependencies, ...packageJson.devDependencies };
      
      // Known heavy packages (in practice, you'd use a service like bundlephobia)
      const knownHeavyPackages = {
        'react': { size: '42.2kB', gzipped: '13.2kB' },
        'react-dom': { size: '130kB', gzipped: '42.2kB' },
        'lucide-react': { size: '1.2MB', gzipped: '180kB' },
        '@testing-library/react': { size: '400kB', gzipped: '120kB' },
        'vitest': { size: '2.1MB', gzipped: '600kB' },
        'typescript': { size: '34MB', gzipped: '8.2MB' },
        'eslint': { size: '15MB', gzipped: '3.8MB' },
      };

      Object.keys(dependencies).forEach(dep => {
        if (knownHeavyPackages[dep]) {
          heavy.push({
            name: dep,
            version: dependencies[dep],
            ...knownHeavyPackages[dep],
          });
        }
      });

    } catch (error) {
      console.warn('Could not analyze package sizes:', error.message);
    }

    return heavy.sort((a, b) => {
      const aSize = parseFloat(a.size) || 0;
      const bSize = parseFloat(b.size) || 0;
      return bSize - aSize;
    });
  }

  /**
   * Find duplicate dependencies (simplified check)
   */
  findDuplicateDependencies() {
    const duplicates = [];
    
    try {
      // This would require analyzing node_modules or using npm ls
      // For now, return empty array
      return duplicates;
    } catch (error) {
      console.warn('Could not check for duplicate dependencies:', error.message);
      return duplicates;
    }
  }

  /**
   * Generate optimization recommendations
   */
  generateRecommendations(analysis) {
    const recommendations = [];

    // Unused dependencies
    if (analysis.unusedDependencies.length > 0) {
      recommendations.push({
        type: 'cleanup',
        priority: 'medium',
        message: `Remove ${analysis.unusedDependencies.length} unused dependencies to reduce bundle size`,
        action: `npm uninstall ${analysis.unusedDependencies.map(d => d.name).join(' ')}`,
      });
    }

    // Heavy dependencies
    const heavyProdDeps = analysis.heavyDependencies.filter(dep => 
      analysis.dependencies[dep.name]?.used
    );

    if (heavyProdDeps.length > 0) {
      recommendations.push({
        type: 'optimization',
        priority: 'high',
        message: 'Consider optimizing heavy production dependencies',
        details: heavyProdDeps.map(dep => `${dep.name}: ${dep.size}`),
      });
    }

    // Lucide React optimization
    if (analysis.dependencies['lucide-react']?.used) {
      recommendations.push({
        type: 'optimization',
        priority: 'high',
        message: 'Optimize lucide-react imports using tree shaking',
        action: 'Import specific icons instead of the entire library',
      });
    }

    // Bundle size recommendations
    const totalHeavySize = analysis.heavyDependencies.reduce((total, dep) => {
      const size = parseFloat(dep.size) || 0;
      return total + size;
    }, 0);

    if (totalHeavySize > 5) { // 5MB
      recommendations.push({
        type: 'performance',
        priority: 'high',
        message: 'Total dependency size is large - consider code splitting',
        details: `Total size: ~${totalHeavySize.toFixed(1)}MB`,
      });
    }

    return recommendations;
  }

  /**
   * Generate detailed report
   */
  async generateReport(analysis) {
    const report = {
      ...analysis,
      summary: {
        totalDependencies: Object.keys(analysis.dependencies).length,
        totalDevDependencies: Object.keys(analysis.devDependencies).length,
        unusedCount: analysis.unusedDependencies.length,
        heavyCount: analysis.heavyDependencies.length,
        recommendationsCount: analysis.recommendations.length,
      },
    };

    fs.writeFileSync(this.reportPath, JSON.stringify(report, null, 2));
    console.log(`📊 Detailed report saved to: ${this.reportPath}`);
  }

  /**
   * Display analysis results
   */
  displayResults(analysis) {
    console.log('\n📦 Dependency Analysis Results\n');
    console.log('=' .repeat(50));

    // Summary
    console.log(`📦 Production Dependencies: ${Object.keys(analysis.dependencies).length}`);
    console.log(`🛠️  Dev Dependencies: ${Object.keys(analysis.devDependencies).length}`);
    console.log(`❌ Unused Dependencies: ${analysis.unusedDependencies.length}`);
    console.log(`⚠️  Heavy Dependencies: ${analysis.heavyDependencies.length}`);

    // Unused dependencies
    if (analysis.unusedDependencies.length > 0) {
      console.log('\n❌ Unused Dependencies:');
      analysis.unusedDependencies.forEach((dep, index) => {
        console.log(`  ${index + 1}. ${dep.name} (${dep.type})`);
      });
      
      const unusedProd = analysis.unusedDependencies.filter(d => d.type === 'dependency');
      const unusedDev = analysis.unusedDependencies.filter(d => d.type === 'devDependency');
      
      if (unusedProd.length > 0) {
        console.log(`\n  Remove unused production dependencies:`);
        console.log(`  npm uninstall ${unusedProd.map(d => d.name).join(' ')}`);
      }
      
      if (unusedDev.length > 0) {
        console.log(`\n  Remove unused dev dependencies:`);
        console.log(`  npm uninstall --save-dev ${unusedDev.map(d => d.name).join(' ')}`);
      }
    }

    // Heavy dependencies
    if (analysis.heavyDependencies.length > 0) {
      console.log('\n⚠️  Heavy Dependencies:');
      analysis.heavyDependencies.slice(0, 10).forEach((dep, index) => {
        console.log(`  ${index + 1}. ${dep.name} - ${dep.size} (${dep.gzipped} gzipped)`);
      });
    }

    // Recommendations
    if (analysis.recommendations.length > 0) {
      console.log('\n💡 Optimization Recommendations:');
      analysis.recommendations.forEach((rec, index) => {
        const icon = rec.priority === 'high' ? '🔥' : rec.priority === 'medium' ? '⚠️' : 'ℹ️';
        console.log(`  ${index + 1}. ${icon} [${rec.priority.toUpperCase()}] ${rec.message}`);
        
        if (rec.action) {
          console.log(`     Action: ${rec.action}`);
        }
        
        if (rec.details) {
          if (Array.isArray(rec.details)) {
            rec.details.forEach(detail => console.log(`     - ${detail}`));
          } else {
            console.log(`     ${rec.details}`);
          }
        }
      });
    } else {
      console.log('\n✅ No optimization recommendations - dependencies look good!');
    }

    console.log('\n' + '='.repeat(50));
    console.log('🎉 Dependency analysis complete!');
  }
}

// Run analysis if called directly
if (require.main === module) {
  const analyzer = new DependencyAnalyzer();
  analyzer.analyze().catch(console.error);
}

module.exports = DependencyAnalyzer;