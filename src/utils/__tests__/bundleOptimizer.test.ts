/**
 * Unit tests for bundle optimization utilities
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
    analyzeBundleSize,
    analyzeTreeShaking,
    detectCircularDependencies,
    generateBundleReport,
    identifyUnusedDependencies,
    optimizeChunkSizes,
    optimizeImports,
    suggestCodeSplitting
} from '../bundleOptimizer';

// Mock file system operations
vi.mock('fs', () => ({
  readFileSync: vi.fn(),
  writeFileSync: vi.fn(),
  existsSync: vi.fn(),
  readdirSync: vi.fn(),
  statSync: vi.fn()
}));

describe('Bundle Optimizer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('analyzeBundleSize', () => {
    it('should analyze bundle size from stats file', () => {
      const mockStats = {
        assets: [
          { name: 'main.js', size: 100000 },
          { name: 'vendor.js', size: 200000 },
          { name: 'styles.css', size: 50000 }
        ],
        chunks: [
          { id: 0, names: ['main'], size: 100000, modules: [] },
          { id: 1, names: ['vendor'], size: 200000, modules: [] }
        ]
      };

      const fs = require('fs');
      fs.readFileSync.mockReturnValue(JSON.stringify(mockStats));
      fs.existsSync.mockReturnValue(true);

      const result = analyzeBundleSize('./dist/stats.json');

      expect(result).toEqual({
        totalSize: 350000,
        assets: mockStats.assets,
        chunks: mockStats.chunks,
        recommendations: expect.any(Array)
      });
    });

    it('should handle missing stats file', () => {
      const fs = require('fs');
      fs.existsSync.mockReturnValue(false);

      expect(() => analyzeBundleSize('./missing-stats.json'))
        .toThrow('Bundle stats file not found');
    });

    it('should identify large bundles', () => {
      const mockStats = {
        assets: [
          { name: 'huge-bundle.js', size: 2000000 } // 2MB
        ],
        chunks: []
      };

      const fs = require('fs');
      fs.readFileSync.mockReturnValue(JSON.stringify(mockStats));
      fs.existsSync.mockReturnValue(true);

      const result = analyzeBundleSize('./dist/stats.json');

      expect(result.recommendations).toContain(
        expect.stringContaining('Consider code splitting for huge-bundle.js')
      );
    });
  });

  describe('identifyUnusedDependencies', () => {
    it('should identify unused dependencies', () => {
      const mockPackageJson = {
        dependencies: {
          'used-lib': '^1.0.0',
          'unused-lib': '^2.0.0',
          'react': '^18.0.0'
        },
        devDependencies: {
          'used-dev-lib': '^1.0.0',
          'unused-dev-lib': '^2.0.0'
        }
      };

      const mockSourceFiles = [
        'import React from "react";',
        'import { something } from "used-lib";',
        'import devTool from "used-dev-lib";'
      ];

      const fs = require('fs');
      fs.readFileSync
        .mockReturnValueOnce(JSON.stringify(mockPackageJson))
        .mockReturnValue(mockSourceFiles[0]);
      
      fs.existsSync.mockReturnValue(true);
      fs.readdirSync.mockReturnValue(['file1.ts', 'file2.ts']);

      const result = identifyUnusedDependencies('./');

      expect(result.unused).toContain('unused-lib');
      expect(result.unused).toContain('unused-dev-lib');
      expect(result.used).toContain('react');
      expect(result.used).toContain('used-lib');
    });

    it('should handle missing package.json', () => {
      const fs = require('fs');
      fs.existsSync.mockReturnValue(false);

      expect(() => identifyUnusedDependencies('./'))
        .toThrow('package.json not found');
    });

    it('should detect dynamic imports', () => {
      const mockPackageJson = {
        dependencies: {
          'dynamic-lib': '^1.0.0'
        }
      };

      const mockSourceFile = `
        const loadLib = () => import('dynamic-lib');
      `;

      const fs = require('fs');
      fs.readFileSync
        .mockReturnValueOnce(JSON.stringify(mockPackageJson))
        .mockReturnValue(mockSourceFile);
      
      fs.existsSync.mockReturnValue(true);
      fs.readdirSync.mockReturnValue(['file1.ts']);

      const result = identifyUnusedDependencies('./');

      expect(result.used).toContain('dynamic-lib');
    });
  });

  describe('optimizeImports', () => {
    it('should optimize import statements', () => {
      const sourceCode = `
        import * as _ from 'lodash';
        import { Button, Input, Form } from 'antd';
        import React, { useState, useEffect } from 'react';
      `;

      const result = optimizeImports(sourceCode);

      expect(result.optimized).toContain("import { debounce } from 'lodash/debounce'");
      expect(result.savings).toBeGreaterThan(0);
      expect(result.suggestions).toContain(
        expect.stringContaining('Consider using specific lodash imports')
      );
    });

    it('should detect barrel imports', () => {
      const sourceCode = `
        import { utils } from '../utils';
        import { components } from '../components';
      `;

      const result = optimizeImports(sourceCode);

      expect(result.suggestions).toContain(
        expect.stringContaining('Avoid barrel imports')
      );
    });

    it('should handle empty source code', () => {
      const result = optimizeImports('');

      expect(result.optimized).toBe('');
      expect(result.savings).toBe(0);
      expect(result.suggestions).toHaveLength(0);
    });
  });

  describe('generateBundleReport', () => {
    it('should generate comprehensive bundle report', () => {
      const mockBundleData = {
        totalSize: 500000,
        assets: [
          { name: 'main.js', size: 300000 },
          { name: 'vendor.js', size: 200000 }
        ],
        chunks: [],
        recommendations: ['Consider code splitting']
      };

      const mockUnusedDeps = {
        unused: ['unused-lib'],
        used: ['react', 'lodash'],
        savings: 50000
      };

      const result = generateBundleReport(mockBundleData, mockUnusedDeps);

      expect(result).toEqual({
        timestamp: expect.any(String),
        bundleSize: mockBundleData,
        dependencies: mockUnusedDeps,
        performance: {
          loadTime: expect.any(Number),
          parseTime: expect.any(Number),
          gzipSize: expect.any(Number)
        },
        recommendations: expect.any(Array),
        score: expect.any(Number)
      });
    });

    it('should calculate performance score', () => {
      const smallBundle = {
        totalSize: 100000,
        assets: [],
        chunks: [],
        recommendations: []
      };

      const largeBundle = {
        totalSize: 2000000,
        assets: [],
        chunks: [],
        recommendations: []
      };

      const smallResult = generateBundleReport(smallBundle, { unused: [], used: [], savings: 0 });
      const largeResult = generateBundleReport(largeBundle, { unused: [], used: [], savings: 0 });

      expect(smallResult.score).toBeGreaterThan(largeResult.score);
    });
  });

  describe('detectCircularDependencies', () => {
    it('should detect circular dependencies', () => {
      const mockDependencyGraph = {
        'moduleA.js': ['moduleB.js'],
        'moduleB.js': ['moduleC.js'],
        'moduleC.js': ['moduleA.js'] // Circular dependency
      };

      const result = detectCircularDependencies(mockDependencyGraph);

      expect(result.circular).toHaveLength(1);
      expect(result.circular[0]).toEqual(['moduleA.js', 'moduleB.js', 'moduleC.js']);
    });

    it('should handle no circular dependencies', () => {
      const mockDependencyGraph = {
        'moduleA.js': ['moduleB.js'],
        'moduleB.js': ['moduleC.js'],
        'moduleC.js': []
      };

      const result = detectCircularDependencies(mockDependencyGraph);

      expect(result.circular).toHaveLength(0);
      expect(result.clean).toBe(true);
    });

    it('should detect self-referencing modules', () => {
      const mockDependencyGraph = {
        'moduleA.js': ['moduleA.js'] // Self-reference
      };

      const result = detectCircularDependencies(mockDependencyGraph);

      expect(result.circular).toHaveLength(1);
      expect(result.circular[0]).toEqual(['moduleA.js']);
    });
  });

  describe('suggestCodeSplitting', () => {
    it('should suggest code splitting for large modules', () => {
      const mockModules = [
        { name: 'huge-component.js', size: 500000, type: 'component' },
        { name: 'small-util.js', size: 5000, type: 'utility' },
        { name: 'large-service.js', size: 300000, type: 'service' }
      ];

      const result = suggestCodeSplitting(mockModules);

      expect(result.suggestions).toContain(
        expect.objectContaining({
          module: 'huge-component.js',
          strategy: 'lazy-loading',
          reason: expect.stringContaining('Large component')
        })
      );
    });

    it('should suggest route-based splitting', () => {
      const mockModules = [
        { name: 'HomePage.js', size: 100000, type: 'page' },
        { name: 'AboutPage.js', size: 80000, type: 'page' },
        { name: 'ContactPage.js', size: 60000, type: 'page' }
      ];

      const result = suggestCodeSplitting(mockModules);

      expect(result.suggestions).toContain(
        expect.objectContaining({
          strategy: 'route-based',
          reason: expect.stringContaining('Page component')
        })
      );
    });

    it('should calculate potential savings', () => {
      const mockModules = [
        { name: 'large-module.js', size: 400000, type: 'component' }
      ];

      const result = suggestCodeSplitting(mockModules);

      expect(result.potentialSavings).toBeGreaterThan(0);
    });
  });

  describe('analyzeTreeShaking', () => {
    it('should analyze tree shaking effectiveness', () => {
      const mockBundleStats = {
        modules: [
          { name: 'lodash', size: 100000, usedExports: ['debounce', 'throttle'], unusedExports: ['map', 'filter'] },
          { name: 'react', size: 50000, usedExports: ['useState', 'useEffect'], unusedExports: [] }
        ]
      };

      const result = analyzeTreeShaking(mockBundleStats);

      expect(result.effectiveness).toBeLessThan(100); // Some unused exports
      expect(result.unusedCode).toBeGreaterThan(0);
      expect(result.recommendations).toContain(
        expect.stringContaining('lodash has unused exports')
      );
    });

    it('should handle perfect tree shaking', () => {
      const mockBundleStats = {
        modules: [
          { name: 'react', size: 50000, usedExports: ['useState'], unusedExports: [] }
        ]
      };

      const result = analyzeTreeShaking(mockBundleStats);

      expect(result.effectiveness).toBe(100);
      expect(result.unusedCode).toBe(0);
    });
  });

  describe('optimizeChunkSizes', () => {
    it('should optimize chunk sizes', () => {
      const mockChunks = [
        { name: 'main', size: 800000, modules: ['app.js', 'utils.js'] },
        { name: 'vendor', size: 1200000, modules: ['react', 'lodash', 'antd'] },
        { name: 'small', size: 10000, modules: ['tiny-util.js'] }
      ];

      const result = optimizeChunkSizes(mockChunks);

      expect(result.recommendations).toContain(
        expect.stringContaining('vendor chunk is too large')
      );
      expect(result.recommendations).toContain(
        expect.stringContaining('small chunk could be merged')
      );
    });

    it('should suggest optimal chunk configuration', () => {
      const mockChunks = [
        { name: 'main', size: 300000, modules: ['app.js'] },
        { name: 'vendor', size: 400000, modules: ['react', 'lodash'] }
      ];

      const result = optimizeChunkSizes(mockChunks);

      expect(result.optimal).toBe(true);
      expect(result.recommendations).toHaveLength(0);
    });

    it('should calculate chunk efficiency', () => {
      const mockChunks = [
        { name: 'efficient', size: 250000, modules: ['module1', 'module2'] },
        { name: 'inefficient', size: 2000000, modules: ['huge-module'] }
      ];

      const result = optimizeChunkSizes(mockChunks);

      expect(result.efficiency).toBeLessThan(100);
      expect(result.wastedBytes).toBeGreaterThan(0);
    });
  });
});