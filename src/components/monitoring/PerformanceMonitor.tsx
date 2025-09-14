import React, { useState, useEffect, useRef } from 'react';
import { Activity, Cpu, HardDrive, Wifi, Zap, X, Minimize2, Maximize2 } from 'lucide-react';

interface PerformanceMetrics {
  fps: number;
  memoryUsage: number;
  loadTime: number;
  networkLatency: number;
  bundleSize: number;
  renderTime: number;
  componentCount: number;
  errorCount: number;
}

interface PerformanceMonitorProps {
  isVisible: boolean;
  onToggle: () => void;
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
}

export const PerformanceMonitor: React.FC<PerformanceMonitorProps> = ({
  isVisible,
  onToggle,
  position = 'top-right'
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    fps: 60,
    memoryUsage: 0,
    loadTime: 0,
    networkLatency: 0,
    bundleSize: 0,
    renderTime: 0,
    componentCount: 0,
    errorCount: 0
  });
  
  const [isMinimized, setIsMinimized] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [customPosition, setCustomPosition] = useState({ x: 0, y: 0 });
  
  const monitorRef = useRef<HTMLDivElement>(null);
  const frameCountRef = useRef(0);
  const lastTimeRef = useRef(performance.now());
  const fpsHistoryRef = useRef<number[]>([]);

  // FPS monitoring
  useEffect(() => {
    if (!isVisible) return;

    const measureFPS = () => {
      const now = performance.now();
      const delta = now - lastTimeRef.current;
      
      if (delta >= 1000) {
        const fps = Math.round((frameCountRef.current * 1000) / delta);
        fpsHistoryRef.current.push(fps);
        
        if (fpsHistoryRef.current.length > 10) {
          fpsHistoryRef.current.shift();
        }
        
        const avgFps = fpsHistoryRef.current.reduce((a, b) => a + b, 0) / fpsHistoryRef.current.length;
        
        setMetrics(prev => ({ ...prev, fps: Math.round(avgFps) }));
        
        frameCountRef.current = 0;
        lastTimeRef.current = now;
      }
      
      frameCountRef.current++;
      requestAnimationFrame(measureFPS);
    };

    const animationId = requestAnimationFrame(measureFPS);
    return () => cancelAnimationFrame(animationId);
  }, [isVisible]);

  // Memory usage monitoring
  useEffect(() => {
    if (!isVisible) return;

    const measureMemory = () => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        const usedMB = Math.round(memory.usedJSHeapSize / 1024 / 1024);
        setMetrics(prev => ({ ...prev, memoryUsage: usedMB }));
      }
    };

    measureMemory();
    const interval = setInterval(measureMemory, 2000);
    return () => clearInterval(interval);
  }, [isVisible]);

  // Network latency monitoring
  useEffect(() => {
    if (!isVisible) return;

    const measureLatency = async () => {
      try {
        const start = performance.now();
        await fetch('/api/ping', { method: 'HEAD' }).catch(() => {});
        const latency = performance.now() - start;
        setMetrics(prev => ({ ...prev, networkLatency: Math.round(latency) }));
      } catch (error) {
        setMetrics(prev => ({ ...prev, networkLatency: -1 }));
      }
    };

    measureLatency();
    const interval = setInterval(measureLatency, 5000);
    return () => clearInterval(interval);
  }, [isVisible]);

  // Load time and bundle size
  useEffect(() => {
    if (!isVisible) return;

    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    if (navigation) {
      const loadTime = Math.round(navigation.loadEventEnd - navigation.navigationStart);
      setMetrics(prev => ({ ...prev, loadTime }));
    }

    // Estimate bundle size from resource entries
    const resources = performance.getEntriesByType('resource');
    const jsResources = resources.filter(r => r.name.includes('.js'));
    const totalSize = jsResources.reduce((sum, resource) => {
      return sum + ((resource as any).transferSize || 0);
    }, 0);
    
    setMetrics(prev => ({ 
      ...prev, 
      bundleSize: Math.round(totalSize / 1024),
      componentCount: document.querySelectorAll('[data-reactroot], [data-react-component]').length
    }));
  }, [isVisible]);

  // Drag functionality
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget || (e.target as HTMLElement).classList.contains('drag-handle')) {
      setIsDragging(true);
      const rect = monitorRef.current?.getBoundingClientRect();
      if (rect) {
        setDragOffset({
          x: e.clientX - rect.left,
          y: e.clientY - rect.top
        });
      }
    }
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging && monitorRef.current) {
        const newX = e.clientX - dragOffset.x;
        const newY = e.clientY - dragOffset.y;
        
        // Keep within viewport bounds
        const maxX = window.innerWidth - monitorRef.current.offsetWidth;
        const maxY = window.innerHeight - monitorRef.current.offsetHeight;
        
        setCustomPosition({
          x: Math.max(0, Math.min(newX, maxX)),
          y: Math.max(0, Math.min(newY, maxY))
        });
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, dragOffset]);

  if (!isVisible) return null;

  const getPositionStyles = () => {
    if (isDragging || customPosition.x !== 0 || customPosition.y !== 0) {
      return {
        position: 'fixed' as const,
        left: `${customPosition.x}px`,
        top: `${customPosition.y}px`,
        right: 'auto',
        bottom: 'auto'
      };
    }

    const baseStyles = {
      position: 'fixed' as const,
      zIndex: 1000
    };

    switch (position) {
      case 'top-left':
        return { ...baseStyles, top: '20px', left: '20px' };
      case 'top-right':
        return { ...baseStyles, top: '20px', right: '20px' };
      case 'bottom-left':
        return { ...baseStyles, bottom: '20px', left: '20px' };
      case 'bottom-right':
        return { ...baseStyles, bottom: '20px', right: '20px' };
      default:
        return { ...baseStyles, top: '20px', right: '20px' };
    }
  };

  const getStatusColor = (value: number, thresholds: { good: number; warning: number }) => {
    if (value <= thresholds.good) return '#10b981';
    if (value <= thresholds.warning) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div
      ref={monitorRef}
      style={{
        ...getPositionStyles(),
        background: 'rgba(0, 0, 0, 0.9)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        borderRadius: '12px',
        padding: isMinimized ? '8px' : '16px',
        minWidth: isMinimized ? 'auto' : '280px',
        color: 'white',
        fontSize: '12px',
        fontFamily: 'monospace',
        cursor: isDragging ? 'grabbing' : 'grab',
        userSelect: 'none',
        transition: isDragging ? 'none' : 'all 0.2s ease',
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.3)'
      }}
      onMouseDown={handleMouseDown}
    >
      {/* Header */}
      <div 
        className="drag-handle"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: isMinimized ? 0 : '12px',
          paddingBottom: isMinimized ? 0 : '8px',
          borderBottom: isMinimized ? 'none' : '1px solid rgba(255, 255, 255, 0.1)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Activity style={{ width: '14px', height: '14px', color: '#10b981' }} />
          {!isMinimized && <span style={{ fontWeight: 'bold' }}>Performance Monitor</span>}
        </div>
        
        <div style={{ display: 'flex', gap: '4px' }}>
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            style={{
              background: 'none',
              border: 'none',
              color: '#9ca3af',
              cursor: 'pointer',
              padding: '2px',
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            onMouseOver={(e) => e.currentTarget.style.color = 'white'}
            onMouseOut={(e) => e.currentTarget.style.color = '#9ca3af'}
          >
            {isMinimized ? <Maximize2 style={{ width: '12px', height: '12px' }} /> : <Minimize2 style={{ width: '12px', height: '12px' }} />}
          </button>
          
          <button
            onClick={onToggle}
            style={{
              background: 'none',
              border: 'none',
              color: '#9ca3af',
              cursor: 'pointer',
              padding: '2px',
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            onMouseOver={(e) => e.currentTarget.style.color = '#ef4444'}
            onMouseOut={(e) => e.currentTarget.style.color = '#9ca3af'}
          >
            <X style={{ width: '12px', height: '12px' }} />
          </button>
        </div>
      </div>

      {/* Metrics */}
      {!isMinimized && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {/* FPS */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Zap style={{ width: '12px', height: '12px', color: getStatusColor(60 - metrics.fps, { good: 5, warning: 15 }) }} />
              <span>FPS</span>
            </div>
            <span style={{ color: getStatusColor(60 - metrics.fps, { good: 5, warning: 15 }), fontWeight: 'bold' }}>
              {metrics.fps}
            </span>
          </div>

          {/* Memory */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Cpu style={{ width: '12px', height: '12px', color: getStatusColor(metrics.memoryUsage, { good: 50, warning: 100 }) }} />
              <span>Memory</span>
            </div>
            <span style={{ color: getStatusColor(metrics.memoryUsage, { good: 50, warning: 100 }), fontWeight: 'bold' }}>
              {metrics.memoryUsage}MB
            </span>
          </div>

          {/* Network */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Wifi style={{ width: '12px', height: '12px', color: getStatusColor(metrics.networkLatency, { good: 100, warning: 500 }) }} />
              <span>Latency</span>
            </div>
            <span style={{ color: getStatusColor(metrics.networkLatency, { good: 100, warning: 500 }), fontWeight: 'bold' }}>
              {metrics.networkLatency === -1 ? 'N/A' : `${metrics.networkLatency}ms`}
            </span>
          </div>

          {/* Bundle Size */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <HardDrive style={{ width: '12px', height: '12px', color: getStatusColor(metrics.bundleSize, { good: 500, warning: 1000 }) }} />
              <span>Bundle</span>
            </div>
            <span style={{ color: getStatusColor(metrics.bundleSize, { good: 500, warning: 1000 }), fontWeight: 'bold' }}>
              {metrics.bundleSize}KB
            </span>
          </div>

          {/* Load Time */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Activity style={{ width: '12px', height: '12px', color: getStatusColor(metrics.loadTime, { good: 2000, warning: 5000 }) }} />
              <span>Load Time</span>
            </div>
            <span style={{ color: getStatusColor(metrics.loadTime, { good: 2000, warning: 5000 }), fontWeight: 'bold' }}>
              {metrics.loadTime}ms
            </span>
          </div>

          {/* Component Count */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span>Components</span>
            <span style={{ color: '#9ca3af', fontWeight: 'bold' }}>
              {metrics.componentCount}
            </span>
          </div>
        </div>
      )}

      {/* Minimized indicator */}
      {isMinimized && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: getStatusColor(60 - metrics.fps, { good: 5, warning: 15 }),
            animation: 'pulse 2s infinite'
          }} />
          <span style={{ fontSize: '10px', color: '#9ca3af' }}>
            {metrics.fps}fps | {metrics.memoryUsage}MB
          </span>
        </div>
      )}
    </div>
  );
};