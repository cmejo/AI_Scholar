/**
 * Unit tests for code splitting utilities
 */

import React from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
    analyzeChunkDependencies,
    createAsyncChunk,
    createDynamicImport,
    createFeatureBasedSplit,
    createLazyComponent,
    createRouteBasedSplit,
    optimizeChunkLoading,
    preloadComponent
} from '../codeSplitting';

// Mock React.lazy and Suspense
vi.mock('react', async () => {
  const actual = await vi.importActual('react');
  return {
    ...actual,
    lazy: vi.fn(),
    Suspense: vi.fn(({ children }) => children)
  };
});

describe('Code Splitting Utilities', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('createLazyComponent', () => {
    it('should create lazy component with React.lazy', () => {
      const mockComponent = () => React.createElement('div', null, 'Test Component');
      const mockImport = vi.fn().mockResolvedValue({ default: mockComponent });
      
      React.lazy = vi.fn().mockReturnValue(mockComponent);

      const LazyComponent = createLazyComponent(mockImport);

      expect(React.lazy).toHaveBeenCalledWith(mockImport);
      expect(LazyComponent).toBe(mockComponent);
    });

    it('should handle import errors gracefully', async () => {
      const mockImport = vi.fn().mockRejectedValue(new Error('Import failed'));
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      React.lazy = vi.fn().mockImplementation((importFn) => {
        // Simulate React.lazy behavior
        return () => {
          importFn().catch(consoleSpy);
          return React.createElement('div', null, 'Error loading component');
        };
      });

      const LazyComponent = createLazyComponent(mockImport);
      const component = LazyComponent();

      await new Promise(resolve => setTimeout(resolve, 0));

      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to load component:',
        expect.any(Error)
      );

      consoleSpy.mockRestore();
    });

    it('should support custom loading fallback', () => {
      const mockComponent = () => React.createElement('div', null, 'Test Component');
      const mockImport = vi.fn().mockResolvedValue({ default: mockComponent });
      const fallback = React.createElement('div', null, 'Loading...');

      React.lazy = vi.fn().mockReturnValue(mockComponent);

      const LazyComponent = createLazyComponent(mockImport, { fallback });

      expect(React.lazy).toHaveBeenCalledWith(mockImport);
    });
  });

  describe('createAsyncChunk', () => {
    it('should create async chunk with dynamic import', async () => {
      const mockModule = { someFunction: vi.fn() };
      const mockImport = vi.fn().mockResolvedValue(mockModule);

      const chunk = createAsyncChunk('test-chunk', mockImport);
      const result = await chunk.load();

      expect(mockImport).toHaveBeenCalled();
      expect(result).toBe(mockModule);
      expect(chunk.isLoaded()).toBe(true);
    });

    it('should cache loaded chunks', async () => {
      const mockModule = { someFunction: vi.fn() };
      const mockImport = vi.fn().mockResolvedValue(mockModule);

      const chunk = createAsyncChunk('test-chunk', mockImport);
      
      const result1 = await chunk.load();
      const result2 = await chunk.load();

      expect(mockImport).toHaveBeenCalledOnce();
      expect(result1).toBe(result2);
    });

    it('should handle loading errors', async () => {
      const mockImport = vi.fn().mockRejectedValue(new Error('Chunk load failed'));

      const chunk = createAsyncChunk('test-chunk', mockImport);

      await expect(chunk.load()).rejects.toThrow('Chunk load failed');
      expect(chunk.isLoaded()).toBe(false);
    });

    it('should support preloading', () => {
      const mockModule = { someFunction: vi.fn() };
      const mockImport = vi.fn().mockResolvedValue(mockModule);

      const chunk = createAsyncChunk('test-chunk', mockImport);
      chunk.preload();

      expect(mockImport).toHaveBeenCalled();
    });
  });

  describe('preloadComponent', () => {
    it('should preload component using link prefetch', () => {
      const mockLink = {
        rel: '',
        as: '',
        href: '',
        crossOrigin: ''
      };

      const originalCreateElement = document.createElement;
      document.createElement = vi.fn().mockImplementation((tagName) => {
        if (tagName === 'link') return mockLink;
        return originalCreateElement.call(document, tagName);
      });

      const mockHead = {
        appendChild: vi.fn()
      };
      Object.defineProperty(document, 'head', { value: mockHead });

      preloadComponent('/chunks/component.js');

      expect(mockLink.rel).toBe('prefetch');
      expect(mockLink.as).toBe('script');
      expect(mockLink.href).toBe('/chunks/component.js');
      expect(mockHead.appendChild).toHaveBeenCalledWith(mockLink);

      document.createElement = originalCreateElement;
    });

    it('should handle preload with high priority', () => {
      const mockLink = {
        rel: '',
        as: '',
        href: '',
        crossOrigin: ''
      };

      document.createElement = vi.fn().mockReturnValue(mockLink);
      const mockHead = { appendChild: vi.fn() };
      Object.defineProperty(document, 'head', { value: mockHead });

      preloadComponent('/chunks/critical.js', { priority: 'high' });

      expect(mockLink.rel).toBe('preload');
    });

    it('should support crossorigin attribute', () => {
      const mockLink = {
        rel: '',
        as: '',
        href: '',
        crossOrigin: ''
      };

      document.createElement = vi.fn().mockReturnValue(mockLink);
      const mockHead = { appendChild: vi.fn() };
      Object.defineProperty(document, 'head', { value: mockHead });

      preloadComponent('/chunks/component.js', { crossOrigin: 'anonymous' });

      expect(mockLink.crossOrigin).toBe('anonymous');
    });
  });

  describe('createRouteBasedSplit', () => {
    it('should create route-based code splitting configuration', () => {
      const routes = [
        { path: '/home', component: 'HomePage' },
        { path: '/about', component: 'AboutPage' },
        { path: '/contact', component: 'ContactPage' }
      ];

      const result = createRouteBasedSplit(routes);

      expect(result.chunks).toHaveLength(3);
      expect(result.chunks[0]).toEqual({
        name: 'route-home',
        path: '/home',
        component: 'HomePage',
        preload: false
      });
    });

    it('should support preloading critical routes', () => {
      const routes = [
        { path: '/home', component: 'HomePage', critical: true },
        { path: '/admin', component: 'AdminPage' }
      ];

      const result = createRouteBasedSplit(routes);

      expect(result.chunks[0].preload).toBe(true);
      expect(result.chunks[1].preload).toBe(false);
    });

    it('should generate webpack chunk names', () => {
      const routes = [
        { path: '/user/:id', component: 'UserProfile' }
      ];

      const result = createRouteBasedSplit(routes);

      expect(result.webpackChunkNames).toContain('route-user-profile');
    });
  });

  describe('createFeatureBasedSplit', () => {
    it('should create feature-based code splitting', () => {
      const features = [
        { name: 'dashboard', components: ['DashboardView', 'DashboardStats'] },
        { name: 'settings', components: ['SettingsPanel', 'UserPreferences'] }
      ];

      const result = createFeatureBasedSplit(features);

      expect(result.chunks).toHaveLength(2);
      expect(result.chunks[0]).toEqual({
        name: 'feature-dashboard',
        components: ['DashboardView', 'DashboardStats'],
        lazy: true
      });
    });

    it('should handle feature dependencies', () => {
      const features = [
        { 
          name: 'advanced-features', 
          components: ['AdvancedChart'], 
          dependencies: ['chart-library'] 
        }
      ];

      const result = createFeatureBasedSplit(features);

      expect(result.chunks[0].dependencies).toEqual(['chart-library']);
    });

    it('should calculate bundle sizes', () => {
      const features = [
        { 
          name: 'large-feature', 
          components: ['HugeComponent'], 
          estimatedSize: 500000 
        }
      ];

      const result = createFeatureBasedSplit(features);

      expect(result.totalEstimatedSize).toBe(500000);
      expect(result.recommendations).toContain(
        expect.stringContaining('large-feature is quite large')
      );
    });
  });

  describe('optimizeChunkLoading', () => {
    it('should optimize chunk loading strategy', () => {
      const chunks = [
        { name: 'vendor', size: 500000, priority: 'high' },
        { name: 'feature-a', size: 100000, priority: 'medium' },
        { name: 'feature-b', size: 80000, priority: 'low' }
      ];

      const result = optimizeChunkLoading(chunks);

      expect(result.loadingOrder).toEqual(['vendor', 'feature-a', 'feature-b']);
      expect(result.preloadCandidates).toContain('vendor');
    });

    it('should suggest parallel loading for independent chunks', () => {
      const chunks = [
        { name: 'feature-a', size: 100000, dependencies: [] },
        { name: 'feature-b', size: 100000, dependencies: [] },
        { name: 'feature-c', size: 100000, dependencies: ['feature-a'] }
      ];

      const result = optimizeChunkLoading(chunks);

      expect(result.parallelGroups).toContain(['feature-a', 'feature-b']);
    });

    it('should calculate loading performance metrics', () => {
      const chunks = [
        { name: 'main', size: 200000, priority: 'high' },
        { name: 'secondary', size: 100000, priority: 'medium' }
      ];

      const result = optimizeChunkLoading(chunks);

      expect(result.metrics).toEqual({
        totalSize: 300000,
        estimatedLoadTime: expect.any(Number),
        parallelizationRatio: expect.any(Number)
      });
    });
  });

  describe('analyzeChunkDependencies', () => {
    it('should analyze chunk dependencies', () => {
      const chunks = [
        { name: 'main', imports: ['react', 'lodash'] },
        { name: 'feature-a', imports: ['react', 'feature-utils'] },
        { name: 'feature-b', imports: ['lodash', 'feature-utils'] }
      ];

      const result = analyzeChunkDependencies(chunks);

      expect(result.sharedDependencies).toEqual({
        'react': ['main', 'feature-a'],
        'lodash': ['main', 'feature-b'],
        'feature-utils': ['feature-a', 'feature-b']
      });
    });

    it('should detect circular dependencies', () => {
      const chunks = [
        { name: 'chunk-a', imports: ['chunk-b'] },
        { name: 'chunk-b', imports: ['chunk-c'] },
        { name: 'chunk-c', imports: ['chunk-a'] }
      ];

      const result = analyzeChunkDependencies(chunks);

      expect(result.circularDependencies).toHaveLength(1);
      expect(result.circularDependencies[0]).toEqual(['chunk-a', 'chunk-b', 'chunk-c']);
    });

    it('should suggest vendor chunk optimization', () => {
      const chunks = [
        { name: 'main', imports: ['react', 'react-dom', 'lodash'] },
        { name: 'feature-a', imports: ['react', 'lodash'] },
        { name: 'feature-b', imports: ['react', 'moment'] }
      ];

      const result = analyzeChunkDependencies(chunks);

      expect(result.recommendations).toContain(
        expect.stringContaining('Create vendor chunk for react')
      );
    });
  });

  describe('createDynamicImport', () => {
    it('should create dynamic import with error handling', async () => {
      const mockModule = { default: 'test-module' };
      const mockImport = vi.fn().mockResolvedValue(mockModule);

      const dynamicImport = createDynamicImport(mockImport);
      const result = await dynamicImport();

      expect(mockImport).toHaveBeenCalled();
      expect(result).toBe(mockModule);
    });

    it('should handle import failures with retry', async () => {
      const mockModule = { default: 'test-module' };
      const mockImport = vi.fn()
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValue(mockModule);

      const dynamicImport = createDynamicImport(mockImport, { retries: 1 });
      const result = await dynamicImport();

      expect(mockImport).toHaveBeenCalledTimes(2);
      expect(result).toBe(mockModule);
    });

    it('should timeout after specified duration', async () => {
      const mockImport = vi.fn().mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 2000))
      );

      const dynamicImport = createDynamicImport(mockImport, { timeout: 1000 });

      await expect(dynamicImport()).rejects.toThrow('Import timeout');
    });

    it('should support custom error handling', async () => {
      const mockImport = vi.fn().mockRejectedValue(new Error('Import failed'));
      const errorHandler = vi.fn().mockReturnValue('fallback-module');

      const dynamicImport = createDynamicImport(mockImport, { 
        onError: errorHandler 
      });
      
      const result = await dynamicImport();

      expect(errorHandler).toHaveBeenCalledWith(expect.any(Error));
      expect(result).toBe('fallback-module');
    });

    it('should track loading metrics', async () => {
      const mockModule = { default: 'test-module' };
      const mockImport = vi.fn().mockResolvedValue(mockModule);
      const metricsCallback = vi.fn();

      const dynamicImport = createDynamicImport(mockImport, {
        onMetrics: metricsCallback
      });

      await dynamicImport();

      expect(metricsCallback).toHaveBeenCalledWith({
        loadTime: expect.any(Number),
        success: true,
        retries: 0
      });
    });
  });
});