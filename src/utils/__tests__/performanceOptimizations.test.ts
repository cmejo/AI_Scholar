/**
 * Unit tests for performance optimization utilities
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
    batchUpdates,
    createLazyLoader,
    createPerformanceObserver,
    debounce,
    measurePerformance,
    memoize,
    optimizeImageLoading,
    optimizeRenderLoop,
    preloadCriticalResources,
    throttle
} from '../performanceOptimizations';

describe('Performance Optimizations', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  describe('debounce', () => {
    it('should delay function execution', () => {
      const mockFn = vi.fn();
      const debouncedFn = debounce(mockFn, 100);

      debouncedFn();
      expect(mockFn).not.toHaveBeenCalled();

      vi.advanceTimersByTime(50);
      expect(mockFn).not.toHaveBeenCalled();

      vi.advanceTimersByTime(50);
      expect(mockFn).toHaveBeenCalledOnce();
    });

    it('should reset delay on multiple calls', () => {
      const mockFn = vi.fn();
      const debouncedFn = debounce(mockFn, 100);

      debouncedFn();
      vi.advanceTimersByTime(50);
      debouncedFn(); // Reset timer
      vi.advanceTimersByTime(50);
      expect(mockFn).not.toHaveBeenCalled();

      vi.advanceTimersByTime(50);
      expect(mockFn).toHaveBeenCalledOnce();
    });

    it('should pass arguments correctly', () => {
      const mockFn = vi.fn();
      const debouncedFn = debounce(mockFn, 100);

      debouncedFn('arg1', 'arg2');
      vi.advanceTimersByTime(100);

      expect(mockFn).toHaveBeenCalledWith('arg1', 'arg2');
    });

    it('should handle immediate execution option', () => {
      const mockFn = vi.fn();
      const debouncedFn = debounce(mockFn, 100, true);

      debouncedFn();
      expect(mockFn).toHaveBeenCalledOnce();

      debouncedFn();
      expect(mockFn).toHaveBeenCalledOnce(); // Should not call again immediately
    });
  });

  describe('throttle', () => {
    it('should limit function execution rate', () => {
      const mockFn = vi.fn();
      const throttledFn = throttle(mockFn, 100);

      throttledFn();
      expect(mockFn).toHaveBeenCalledOnce();

      throttledFn();
      expect(mockFn).toHaveBeenCalledOnce(); // Should not call again immediately

      vi.advanceTimersByTime(100);
      throttledFn();
      expect(mockFn).toHaveBeenCalledTimes(2);
    });

    it('should execute with latest arguments', () => {
      const mockFn = vi.fn();
      const throttledFn = throttle(mockFn, 100);

      throttledFn('first');
      throttledFn('second');
      throttledFn('third');

      expect(mockFn).toHaveBeenCalledWith('first');

      vi.advanceTimersByTime(100);
      expect(mockFn).toHaveBeenCalledWith('third');
    });
  });

  describe('memoize', () => {
    it('should cache function results', () => {
      const expensiveFn = vi.fn((x: number) => x * 2);
      const memoizedFn = memoize(expensiveFn);

      const result1 = memoizedFn(5);
      const result2 = memoizedFn(5);

      expect(result1).toBe(10);
      expect(result2).toBe(10);
      expect(expensiveFn).toHaveBeenCalledOnce();
    });

    it('should handle different arguments', () => {
      const expensiveFn = vi.fn((x: number) => x * 2);
      const memoizedFn = memoize(expensiveFn);

      memoizedFn(5);
      memoizedFn(10);
      memoizedFn(5); // Should use cache

      expect(expensiveFn).toHaveBeenCalledTimes(2);
    });

    it('should respect cache size limit', () => {
      const expensiveFn = vi.fn((x: number) => x * 2);
      const memoizedFn = memoize(expensiveFn, { maxSize: 2 });

      memoizedFn(1);
      memoizedFn(2);
      memoizedFn(3); // Should evict first entry
      memoizedFn(1); // Should call function again

      expect(expensiveFn).toHaveBeenCalledTimes(4);
    });

    it('should handle custom key generator', () => {
      const expensiveFn = vi.fn((obj: { id: number }) => obj.id * 2);
      const memoizedFn = memoize(expensiveFn, {
        keyGenerator: (obj) => obj.id.toString()
      });

      const obj1 = { id: 1 };
      const obj2 = { id: 1 }; // Different object, same id

      memoizedFn(obj1);
      memoizedFn(obj2); // Should use cache

      expect(expensiveFn).toHaveBeenCalledOnce();
    });
  });

  describe('createLazyLoader', () => {
    it('should load resource only when needed', async () => {
      const mockLoader = vi.fn().mockResolvedValue('loaded resource');
      const lazyLoader = createLazyLoader(mockLoader);

      expect(mockLoader).not.toHaveBeenCalled();

      const result = await lazyLoader();
      expect(result).toBe('loaded resource');
      expect(mockLoader).toHaveBeenCalledOnce();
    });

    it('should cache loaded resource', async () => {
      const mockLoader = vi.fn().mockResolvedValue('loaded resource');
      const lazyLoader = createLazyLoader(mockLoader);

      const result1 = await lazyLoader();
      const result2 = await lazyLoader();

      expect(result1).toBe('loaded resource');
      expect(result2).toBe('loaded resource');
      expect(mockLoader).toHaveBeenCalledOnce();
    });

    it('should handle loading errors', async () => {
      const mockLoader = vi.fn().mockRejectedValue(new Error('Load failed'));
      const lazyLoader = createLazyLoader(mockLoader);

      await expect(lazyLoader()).rejects.toThrow('Load failed');
      
      // Should retry on next call
      await expect(lazyLoader()).rejects.toThrow('Load failed');
      expect(mockLoader).toHaveBeenCalledTimes(2);
    });
  });

  describe('optimizeImageLoading', () => {
    it('should set up intersection observer for lazy loading', () => {
      const mockObserver = {
        observe: vi.fn(),
        unobserve: vi.fn(),
        disconnect: vi.fn()
      };
      
      // Mock IntersectionObserver
      global.IntersectionObserver = vi.fn().mockImplementation(() => mockObserver);

      const container = document.createElement('div');
      const img1 = document.createElement('img');
      const img2 = document.createElement('img');
      
      img1.dataset.src = 'image1.jpg';
      img2.dataset.src = 'image2.jpg';
      
      container.appendChild(img1);
      container.appendChild(img2);

      const cleanup = optimizeImageLoading(container);

      expect(global.IntersectionObserver).toHaveBeenCalled();
      expect(mockObserver.observe).toHaveBeenCalledWith(img1);
      expect(mockObserver.observe).toHaveBeenCalledWith(img2);

      cleanup();
      expect(mockObserver.disconnect).toHaveBeenCalled();
    });

    it('should handle containers without images', () => {
      const mockObserver = {
        observe: vi.fn(),
        disconnect: vi.fn()
      };
      
      global.IntersectionObserver = vi.fn().mockImplementation(() => mockObserver);

      const container = document.createElement('div');
      const cleanup = optimizeImageLoading(container);

      expect(mockObserver.observe).not.toHaveBeenCalled();
      
      cleanup();
      expect(mockObserver.disconnect).toHaveBeenCalled();
    });
  });

  describe('preloadCriticalResources', () => {
    it('should create preload links for resources', () => {
      const resources = [
        { href: 'critical.css', as: 'style' },
        { href: 'important.js', as: 'script' },
        { href: 'hero.jpg', as: 'image' }
      ];

      const originalCreateElement = document.createElement;
      const mockLinks: HTMLLinkElement[] = [];
      
      document.createElement = vi.fn().mockImplementation((tagName) => {
        if (tagName === 'link') {
          const link = originalCreateElement.call(document, 'link') as HTMLLinkElement;
          mockLinks.push(link);
          return link;
        }
        return originalCreateElement.call(document, tagName);
      });

      const mockHead = {
        appendChild: vi.fn()
      };
      
      Object.defineProperty(document, 'head', {
        value: mockHead,
        writable: true
      });

      preloadCriticalResources(resources);

      expect(mockLinks).toHaveLength(3);
      expect(mockLinks[0].rel).toBe('preload');
      expect(mockLinks[0].href).toContain('critical.css');
      expect(mockLinks[0].as).toBe('style');
      
      expect(mockHead.appendChild).toHaveBeenCalledTimes(3);

      // Restore
      document.createElement = originalCreateElement;
    });

    it('should handle empty resource list', () => {
      const mockHead = {
        appendChild: vi.fn()
      };
      
      Object.defineProperty(document, 'head', {
        value: mockHead,
        writable: true
      });

      preloadCriticalResources([]);

      expect(mockHead.appendChild).not.toHaveBeenCalled();
    });
  });

  describe('measurePerformance', () => {
    it('should measure function execution time', async () => {
      const mockPerformance = {
        now: vi.fn()
          .mockReturnValueOnce(100)
          .mockReturnValueOnce(150)
      };
      
      global.performance = mockPerformance as any;

      const testFn = vi.fn().mockResolvedValue('result');
      const result = await measurePerformance('test-operation', testFn);

      expect(result).toEqual({
        result: 'result',
        duration: 50,
        operation: 'test-operation'
      });
      expect(testFn).toHaveBeenCalled();
    });

    it('should handle synchronous functions', async () => {
      const mockPerformance = {
        now: vi.fn()
          .mockReturnValueOnce(100)
          .mockReturnValueOnce(120)
      };
      
      global.performance = mockPerformance as any;

      const testFn = vi.fn().mockReturnValue('sync result');
      const result = await measurePerformance('sync-operation', testFn);

      expect(result).toEqual({
        result: 'sync result',
        duration: 20,
        operation: 'sync-operation'
      });
    });

    it('should handle function errors', async () => {
      const mockPerformance = {
        now: vi.fn()
          .mockReturnValueOnce(100)
          .mockReturnValueOnce(110)
      };
      
      global.performance = mockPerformance as any;

      const testFn = vi.fn().mockRejectedValue(new Error('Test error'));
      
      await expect(measurePerformance('error-operation', testFn)).rejects.toThrow('Test error');
    });
  });

  describe('createPerformanceObserver', () => {
    it('should create performance observer with callback', () => {
      const mockObserver = {
        observe: vi.fn(),
        disconnect: vi.fn()
      };
      
      global.PerformanceObserver = vi.fn().mockImplementation(() => mockObserver);

      const callback = vi.fn();
      const observer = createPerformanceObserver(callback, ['measure']);

      expect(global.PerformanceObserver).toHaveBeenCalledWith(callback);
      expect(mockObserver.observe).toHaveBeenCalledWith({ entryTypes: ['measure'] });

      observer.disconnect();
      expect(mockObserver.disconnect).toHaveBeenCalled();
    });

    it('should handle unsupported performance observer', () => {
      global.PerformanceObserver = undefined as any;

      const callback = vi.fn();
      const observer = createPerformanceObserver(callback, ['measure']);

      expect(observer).toEqual({
        disconnect: expect.any(Function)
      });

      // Should not throw
      observer.disconnect();
    });
  });

  describe('optimizeRenderLoop', () => {
    it('should use requestAnimationFrame for render optimization', () => {
      const mockRAF = vi.fn().mockImplementation((callback) => {
        callback();
        return 1;
      });
      
      global.requestAnimationFrame = mockRAF;

      const renderFn = vi.fn();
      const optimizedRender = optimizeRenderLoop(renderFn);

      optimizedRender();
      optimizedRender(); // Should batch multiple calls

      expect(mockRAF).toHaveBeenCalledOnce();
      expect(renderFn).toHaveBeenCalledOnce();
    });

    it('should handle multiple render requests', () => {
      let rafCallback: (() => void) | null = null;
      const mockRAF = vi.fn().mockImplementation((callback) => {
        rafCallback = callback;
        return 1;
      });
      
      global.requestAnimationFrame = mockRAF;

      const renderFn = vi.fn();
      const optimizedRender = optimizeRenderLoop(renderFn);

      optimizedRender();
      optimizedRender();
      optimizedRender();

      expect(mockRAF).toHaveBeenCalledOnce();
      expect(renderFn).not.toHaveBeenCalled();

      // Execute the RAF callback
      rafCallback?.();
      expect(renderFn).toHaveBeenCalledOnce();
    });
  });

  describe('batchUpdates', () => {
    it('should batch multiple updates into single execution', () => {
      const updates: Array<() => void> = [];
      const batcher = batchUpdates((updateFns) => {
        updateFns.forEach(fn => fn());
      });

      const update1 = vi.fn();
      const update2 = vi.fn();
      const update3 = vi.fn();

      batcher(update1);
      batcher(update2);
      batcher(update3);

      expect(update1).not.toHaveBeenCalled();
      expect(update2).not.toHaveBeenCalled();
      expect(update3).not.toHaveBeenCalled();

      vi.advanceTimersByTime(0); // Trigger microtask

      expect(update1).toHaveBeenCalledOnce();
      expect(update2).toHaveBeenCalledOnce();
      expect(update3).toHaveBeenCalledOnce();
    });

    it('should handle empty batch', () => {
      const executeFn = vi.fn();
      const batcher = batchUpdates(executeFn);

      vi.advanceTimersByTime(0);
      expect(executeFn).not.toHaveBeenCalled();
    });

    it('should handle errors in batch execution', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      const batcher = batchUpdates((updateFns) => {
        updateFns.forEach(fn => fn());
      });

      const errorUpdate = vi.fn().mockImplementation(() => {
        throw new Error('Update failed');
      });

      batcher(errorUpdate);
      vi.advanceTimersByTime(0);

      expect(consoleSpy).toHaveBeenCalledWith(
        'Error in batch update:',
        expect.any(Error)
      );

      consoleSpy.mockRestore();
    });
  });
});