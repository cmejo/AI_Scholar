import { useCallback, useMemo, useRef } from 'react';

/**
 * Performance optimization utilities for React components
 */

/**
 * Hook to debounce a function call
 */
export function useDebounce<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const timeoutRef = useRef<NodeJS.Timeout>();

  return useCallback(
    ((...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      
      timeoutRef.current = setTimeout(() => {
        callback(...args);
      }, delay);
    }) as T,
    [callback, delay]
  );
}

/**
 * Hook to throttle a function call
 */
export function useThrottle<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const lastCallRef = useRef<number>(0);
  const timeoutRef = useRef<NodeJS.Timeout>();

  return useCallback(
    ((...args: Parameters<T>) => {
      const now = Date.now();
      
      if (now - lastCallRef.current >= delay) {
        lastCallRef.current = now;
        callback(...args);
      } else {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
        
        timeoutRef.current = setTimeout(() => {
          lastCallRef.current = Date.now();
          callback(...args);
        }, delay - (now - lastCallRef.current));
      }
    }) as T,
    [callback, delay]
  );
}

/**
 * Hook to memoize expensive computations with deep comparison
 */
export function useDeepMemo<T>(
  factory: () => T,
  deps: React.DependencyList
): T {
  const depsRef = useRef<React.DependencyList>();
  const valueRef = useRef<T>();

  const hasChanged = useMemo(() => {
    if (!depsRef.current) return true;
    
    return deps.some((dep, index) => {
      const prevDep = depsRef.current![index];
      return !Object.is(dep, prevDep) || 
             (typeof dep === 'object' && dep !== null && JSON.stringify(dep) !== JSON.stringify(prevDep));
    });
  }, deps);

  if (hasChanged) {
    depsRef.current = deps;
    valueRef.current = factory();
  }

  return valueRef.current!;
}

/**
 * Hook to prevent unnecessary re-renders by stabilizing object references
 */
export function useStableCallback<T extends (...args: any[]) => any>(
  callback: T
): T {
  const callbackRef = useRef<T>(callback);
  callbackRef.current = callback;

  return useCallback(
    ((...args: Parameters<T>) => callbackRef.current(...args)) as T,
    []
  );
}

/**
 * Hook to create stable object references
 */
export function useStableObject<T extends Record<string, any>>(obj: T): T {
  return useMemo(() => obj, Object.values(obj));
}

/**
 * Hook for virtualization - only render visible items
 */
export function useVirtualization<T>(
  items: T[],
  containerHeight: number,
  itemHeight: number,
  overscan: number = 5
) {
  const [scrollTop, setScrollTop] = useState(0);

  const visibleRange = useMemo(() => {
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.min(
      items.length - 1,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
    );
    
    return { startIndex, endIndex };
  }, [scrollTop, containerHeight, itemHeight, overscan, items.length]);

  const visibleItems = useMemo(() => {
    return items.slice(visibleRange.startIndex, visibleRange.endIndex + 1).map((item, index) => ({
      item,
      index: visibleRange.startIndex + index,
      style: {
        position: 'absolute' as const,
        top: (visibleRange.startIndex + index) * itemHeight,
        height: itemHeight,
        width: '100%'
      }
    }));
  }, [items, visibleRange, itemHeight]);

  const totalHeight = items.length * itemHeight;

  return {
    visibleItems,
    totalHeight,
    setScrollTop,
    visibleRange
  };
}

/**
 * Performance monitoring hook
 */
export function usePerformanceMonitor(componentName: string) {
  const renderCountRef = useRef(0);
  const lastRenderTimeRef = useRef(Date.now());

  renderCountRef.current += 1;
  const currentTime = Date.now();
  const timeSinceLastRender = currentTime - lastRenderTimeRef.current;
  lastRenderTimeRef.current = currentTime;

  if (process.env.NODE_ENV === 'development') {
    console.log(`[Performance] ${componentName} - Render #${renderCountRef.current}, Time since last: ${timeSinceLastRender}ms`);
  }

  return {
    renderCount: renderCountRef.current,
    timeSinceLastRender
  };
}

/**
 * Hook to batch state updates
 */
export function useBatchedUpdates() {
  const pendingUpdatesRef = useRef<(() => void)[]>([]);
  const timeoutRef = useRef<NodeJS.Timeout>();

  const batchUpdate = useCallback((updateFn: () => void) => {
    pendingUpdatesRef.current.push(updateFn);

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      const updates = pendingUpdatesRef.current;
      pendingUpdatesRef.current = [];
      
      updates.forEach(update => update());
    }, 0);
  }, []);

  return batchUpdate;
}

/**
 * Hook for lazy loading components
 */
export function useLazyComponent<T>(
  importFn: () => Promise<{ default: T }>,
  fallback?: React.ComponentType
) {
  const [Component, setComponent] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const loadComponent = useCallback(async () => {
    if (Component || loading) return;

    setLoading(true);
    setError(null);

    try {
      const module = await importFn();
      setComponent(module.default);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to load component'));
    } finally {
      setLoading(false);
    }
  }, [Component, loading, importFn]);

  return {
    Component,
    loading,
    error,
    loadComponent
  };
}