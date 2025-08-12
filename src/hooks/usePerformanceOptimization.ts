import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

/**
 * Hook to debounce a value
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Hook for virtualized list rendering
 */
interface UseVirtualizedListProps<T> {
  items: T[];
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
}

interface VirtualizedListResult<T> {
  visibleItems: T[];
  totalHeight: number;
  offsetY: number;
  handleScroll: (event: React.UIEvent<HTMLDivElement>) => void;
  visibleRange: { startIndex: number; endIndex: number };
}

export function useVirtualizedList<T>({
  items,
  itemHeight,
  containerHeight,
  overscan = 5,
}: UseVirtualizedListProps<T>): VirtualizedListResult<T> {
  const [scrollTop, setScrollTop] = useState(0);

  const visibleRange = useMemo(() => {
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.min(
      items.length - 1,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
    );
    
    return { startIndex, endIndex };
  }, [scrollTop, itemHeight, containerHeight, overscan, items.length]);

  const visibleItems = useMemo(() => {
    return items.slice(visibleRange.startIndex, visibleRange.endIndex + 1);
  }, [items, visibleRange.startIndex, visibleRange.endIndex]);

  const totalHeight = items.length * itemHeight;
  const offsetY = visibleRange.startIndex * itemHeight;

  const handleScroll = useCallback((event: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(event.currentTarget.scrollTop);
  }, []);

  return {
    visibleItems,
    totalHeight,
    offsetY,
    handleScroll,
    visibleRange,
  };
}

/**
 * Hook to throttle a function
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
 * Hook for performance monitoring
 */
export function usePerformanceMonitor(componentName: string) {
  const renderCountRef = useRef(0);
  const lastRenderTimeRef = useRef(Date.now());

  renderCountRef.current += 1;
  const currentTime = Date.now();
  const timeSinceLastRender = currentTime - lastRenderTimeRef.current;
  lastRenderTimeRef.current = currentTime;

  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    console.log(`[Performance] ${componentName} - Render #${renderCountRef.current}, Time since last: ${timeSinceLastRender}ms`);
  }

  return {
    renderCount: renderCountRef.current,
    timeSinceLastRender
  };
}

/**
 * Hook to create stable callback references
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