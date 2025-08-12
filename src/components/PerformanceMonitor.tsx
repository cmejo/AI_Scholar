import { Activity, AlertTriangle, CheckCircle, Cpu, Zap } from 'lucide-react';
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';

interface PerformanceMetrics {
  renderCount: number;
  averageRenderTime: number;
  lastRenderTime: number;
  memoryUsage: number;
  componentName: string;
  timestamp: Date;
}

interface PerformanceMonitorProps {
  componentName: string;
  enabled?: boolean;
  threshold?: number; // ms
  onPerformanceIssue?: (metrics: PerformanceMetrics) => void;
}

export const PerformanceMonitor: React.FC<PerformanceMonitorProps> = React.memo(({
  componentName,
  enabled = true,
  threshold = 16, // 60fps = 16.67ms per frame
  onPerformanceIssue
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    renderCount: 0,
    averageRenderTime: 0,
    lastRenderTime: 0,
    memoryUsage: 0,
    componentName,
    timestamp: new Date()
  });

  const renderStartTimeRef = useRef<number>(0);
  const renderTimesRef = useRef<number[]>([]);
  const performanceObserverRef = useRef<PerformanceObserver | null>(null);

  // Start performance monitoring
  useEffect(() => {
    if (!enabled) return;

    renderStartTimeRef.current = performance.now();

    return () => {
      const renderEndTime = performance.now();
      const renderTime = renderEndTime - renderStartTimeRef.current;
      
      renderTimesRef.current.push(renderTime);
      
      // Keep only last 100 render times for average calculation
      if (renderTimesRef.current.length > 100) {
        renderTimesRef.current = renderTimesRef.current.slice(-100);
      }

      const averageRenderTime = renderTimesRef.current.reduce((sum, time) => sum + time, 0) / renderTimesRef.current.length;
      
      const newMetrics: PerformanceMetrics = {
        renderCount: renderTimesRef.current.length,
        averageRenderTime,
        lastRenderTime: renderTime,
        memoryUsage: getMemoryUsage(),
        componentName,
        timestamp: new Date()
      };

      setMetrics(newMetrics);

      // Check for performance issues
      if (renderTime > threshold && onPerformanceIssue) {
        onPerformanceIssue(newMetrics);
      }

      // Log performance in development
      if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
        if (renderTime > threshold) {
          console.warn(`[Performance Warning] ${componentName} took ${renderTime.toFixed(2)}ms to render (threshold: ${threshold}ms)`);
        }
      }
    };
  });

  // Set up performance observer for more detailed metrics
  useEffect(() => {
    if (!enabled || typeof window === 'undefined' || !window.PerformanceObserver) return;

    try {
      performanceObserverRef.current = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (entry.name.includes(componentName)) {
            console.log(`[Performance Observer] ${entry.name}: ${entry.duration}ms`);
          }
        });
      });

      performanceObserverRef.current.observe({ entryTypes: ['measure', 'navigation', 'resource'] });
    } catch (error) {
      console.warn('Performance Observer not supported:', error);
    }

    return () => {
      if (performanceObserverRef.current) {
        performanceObserverRef.current.disconnect();
      }
    };
  }, [enabled, componentName]);

  const getMemoryUsage = useCallback((): number => {
    if (typeof window !== 'undefined' && 'memory' in performance) {
      const memory = (performance as any).memory;
      return memory.usedJSHeapSize / 1024 / 1024; // Convert to MB
    }
    return 0;
  }, []);

  const performanceStatus = useMemo(() => {
    if (metrics.lastRenderTime === 0) return 'initializing';
    if (metrics.lastRenderTime > threshold * 2) return 'poor';
    if (metrics.lastRenderTime > threshold) return 'warning';
    return 'good';
  }, [metrics.lastRenderTime, threshold]);

  const statusColor = useMemo(() => {
    switch (performanceStatus) {
      case 'good': return 'text-green-400';
      case 'warning': return 'text-yellow-400';
      case 'poor': return 'text-red-400';
      default: return 'text-gray-400';
    }
  }, [performanceStatus]);

  const statusIcon = useMemo(() => {
    switch (performanceStatus) {
      case 'good': return <CheckCircle size={16} className="text-green-400" />;
      case 'warning': return <AlertTriangle size={16} className="text-yellow-400" />;
      case 'poor': return <AlertTriangle size={16} className="text-red-400" />;
      default: return <Activity size={16} className="text-gray-400" />;
    }
  }, [performanceStatus]);

  if (!enabled || typeof window === 'undefined' || window.location.hostname !== 'localhost') {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 bg-gray-900 border border-gray-700 rounded-lg p-3 text-xs font-mono z-50 shadow-lg">
      <div className="flex items-center space-x-2 mb-2">
        <Zap size={14} className="text-purple-400" />
        <span className="font-semibold text-white">Performance Monitor</span>
      </div>
      
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Component:</span>
          <span className="text-white">{componentName}</span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Status:</span>
          <div className="flex items-center space-x-1">
            {statusIcon}
            <span className={statusColor}>{performanceStatus}</span>
          </div>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Renders:</span>
          <span className="text-white">{metrics.renderCount}</span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Last Render:</span>
          <span className={statusColor}>
            {metrics.lastRenderTime.toFixed(2)}ms
          </span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Avg Render:</span>
          <span className="text-white">
            {metrics.averageRenderTime.toFixed(2)}ms
          </span>
        </div>
        
        {metrics.memoryUsage > 0 && (
          <div className="flex items-center justify-between">
            <span className="text-gray-400">Memory:</span>
            <span className="text-white">
              {metrics.memoryUsage.toFixed(1)}MB
            </span>
          </div>
        )}
        
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Threshold:</span>
          <span className="text-gray-300">{threshold}ms</span>
        </div>
      </div>
      
      {/* Performance Tips */}
      {performanceStatus !== 'good' && (
        <div className="mt-2 pt-2 border-t border-gray-700">
          <div className="flex items-center space-x-1 mb-1">
            <Cpu size={12} className="text-blue-400" />
            <span className="text-blue-400 font-semibold">Tips:</span>
          </div>
          <ul className="text-gray-300 space-y-1">
            {performanceStatus === 'warning' && (
              <>
                <li>• Consider using React.memo</li>
                <li>• Check for unnecessary re-renders</li>
              </>
            )}
            {performanceStatus === 'poor' && (
              <>
                <li>• Use useCallback for functions</li>
                <li>• Implement virtualization</li>
                <li>• Split into smaller components</li>
              </>
            )}
          </ul>
        </div>
      )}
    </div>
  );
});

PerformanceMonitor.displayName = 'PerformanceMonitor';

// Hook to use performance monitoring in components
export function usePerformanceMonitor(componentName: string, enabled: boolean = true) {
  const renderCountRef = useRef(0);
  const renderStartTimeRef = useRef(0);
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    renderCount: 0,
    averageRenderTime: 0,
    lastRenderTime: 0,
    memoryUsage: 0,
    componentName,
    timestamp: new Date()
  });

  useEffect(() => {
    if (!enabled) return;
    
    renderCountRef.current += 1;
    renderStartTimeRef.current = performance.now();

    return () => {
      const renderTime = performance.now() - renderStartTimeRef.current;
      
      setMetrics(prev => ({
        ...prev,
        renderCount: renderCountRef.current,
        lastRenderTime: renderTime,
        averageRenderTime: (prev.averageRenderTime * (renderCountRef.current - 1) + renderTime) / renderCountRef.current,
        timestamp: new Date()
      }));
    };
  });

  return metrics;
}

export default PerformanceMonitor;