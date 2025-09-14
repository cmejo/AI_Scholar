import React, { Suspense, ComponentType, LazyExoticComponent } from 'react';
import { ErrorBoundary } from '../components/ErrorBoundary';

interface LazyLoadOptions {
  fallback?: React.ComponentType;
  errorFallback?: React.ComponentType<{ error: Error; retry: () => void }>;
  retryCount?: number;
  delay?: number;
}

interface LoadingFallbackProps {
  componentName?: string;
  isMinimal?: boolean;
}

// Default loading component
const DefaultLoadingFallback: React.FC<LoadingFallbackProps> = ({ 
  componentName = 'Component', 
  isMinimal = false 
}) => (
  <div style={{
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: isMinimal ? '200px' : '100%',
    background: 'linear-gradient(135deg, #1a1a1a 0%, #2d1b69 100%)',
    color: 'white',
    fontFamily: 'system-ui, -apple-system, sans-serif'
  }}>
    <div style={{ textAlign: 'center' }}>
      <div style={{
        width: '40px',
        height: '40px',
        border: '3px solid rgba(16, 185, 129, 0.3)',
        borderTop: '3px solid #10b981',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite',
        margin: '0 auto 16px'
      }} />
      <p style={{ fontSize: '16px', color: '#9ca3af', margin: 0 }}>
        Loading {componentName}...
      </p>
      {!isMinimal && (
        <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '8px' }}>
          Optimizing performance with lazy loading
        </p>
      )}
    </div>
  </div>
);

// Default error fallback component
const DefaultErrorFallback: React.FC<{ error: Error; retry: () => void }> = ({ error, retry }) => (
  <div style={{
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    background: 'linear-gradient(135deg, #1a1a1a 0%, #2d1b69 100%)',
    color: 'white',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    padding: '40px'
  }}>
    <div style={{ textAlign: 'center', maxWidth: '400px' }}>
      <div style={{
        width: '60px',
        height: '60px',
        background: 'rgba(239, 68, 68, 0.2)',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        margin: '0 auto 20px',
        border: '2px solid rgba(239, 68, 68, 0.3)'
      }}>
        <span style={{ fontSize: '24px' }}>⚠️</span>
      </div>
      
      <h3 style={{ margin: '0 0 12px 0', color: '#ef4444' }}>
        Failed to Load Component
      </h3>
      
      <p style={{ fontSize: '14px', color: '#9ca3af', marginBottom: '20px', lineHeight: '1.5' }}>
        There was an error loading this component. This might be due to a network issue or a temporary problem.
      </p>
      
      <button
        onClick={retry}
        style={{
          background: 'linear-gradient(45deg, #10b981, #059669)',
          color: 'white',
          border: 'none',
          padding: '12px 24px',
          borderRadius: '8px',
          fontSize: '14px',
          fontWeight: 'bold',
          cursor: 'pointer',
          transition: 'transform 0.2s ease'
        }}
        onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-1px)'}
        onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
      >
        Try Again
      </button>
      
      {process.env.NODE_ENV === 'development' && (
        <details style={{ marginTop: '20px', textAlign: 'left' }}>
          <summary style={{ cursor: 'pointer', color: '#9ca3af', fontSize: '12px' }}>
            Error Details (Development)
          </summary>
          <pre style={{
            background: 'rgba(0, 0, 0, 0.5)',
            padding: '12px',
            borderRadius: '6px',
            fontSize: '11px',
            color: '#ef4444',
            overflow: 'auto',
            marginTop: '8px'
          }}>
            {error.message}
            {error.stack && `\n\n${error.stack}`}
          </pre>
        </details>
      )}
    </div>
  </div>
);

// Retry wrapper for lazy components
class LazyComponentWrapper extends React.Component<
  { 
    children: React.ReactNode; 
    componentName: string;
    retryCount: number;
    errorFallback?: React.ComponentType<{ error: Error; retry: () => void }>;
  },
  { retryKey: number; hasError: boolean; error?: Error }
> {
  constructor(props: any) {
    super(props);
    this.state = { retryKey: 0, hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error(`Lazy loading error for ${this.props.componentName}:`, error, errorInfo);
  }

  retry = () => {
    if (this.state.retryKey < this.props.retryCount) {
      this.setState(prevState => ({ 
        retryKey: prevState.retryKey + 1, 
        hasError: false, 
        error: undefined 
      }));
    }
  };

  render() {
    if (this.state.hasError && this.state.error) {
      const ErrorFallback = this.props.errorFallback || DefaultErrorFallback;
      return <ErrorFallback error={this.state.error} retry={this.retry} />;
    }

    return (
      <div key={this.state.retryKey}>
        {this.props.children}
      </div>
    );
  }
}

// Main lazy loading function
export function createLazyComponent<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  componentName: string,
  options: LazyLoadOptions = {}
): LazyExoticComponent<T> {
  const {
    fallback: CustomFallback,
    errorFallback: CustomErrorFallback,
    retryCount = 3,
    delay = 0
  } = options;

  // Add artificial delay if specified (useful for testing)
  const delayedImportFn = delay > 0 
    ? () => new Promise<{ default: T }>(resolve => {
        setTimeout(() => {
          importFn().then(resolve);
        }, delay);
      })
    : importFn;

  const LazyComponent = React.lazy(delayedImportFn);

  // Return wrapped component with error handling and retry logic
  const WrappedComponent = React.forwardRef<any, any>((props, ref) => {
    const FallbackComponent = CustomFallback || (() => (
      <DefaultLoadingFallback componentName={componentName} />
    ));

    return (
      <LazyComponentWrapper
        componentName={componentName}
        retryCount={retryCount}
        errorFallback={CustomErrorFallback}
      >
        <Suspense fallback={<FallbackComponent />}>
          <LazyComponent {...props} ref={ref} />
        </Suspense>
      </LazyComponentWrapper>
    );
  });

  WrappedComponent.displayName = `Lazy(${componentName})`;
  
  return WrappedComponent as LazyExoticComponent<T>;
}

// Preload function for better UX
export function preloadComponent<T extends ComponentType<any>>(
  lazyComponent: LazyExoticComponent<T>
): Promise<void> {
  // Access the internal _payload to trigger loading
  const componentImporter = (lazyComponent as any)._payload;
  if (componentImporter && typeof componentImporter._result === 'undefined') {
    return componentImporter._result || Promise.resolve();
  }
  return Promise.resolve();
}

// Hook for preloading components on hover or focus
export function usePreloadOnHover<T extends ComponentType<any>>(
  lazyComponent: LazyExoticComponent<T>,
  enabled: boolean = true
) {
  const preload = React.useCallback(() => {
    if (enabled) {
      preloadComponent(lazyComponent).catch(console.error);
    }
  }, [lazyComponent, enabled]);

  return {
    onMouseEnter: preload,
    onFocus: preload,
  };
}

// Performance monitoring for lazy loading
export class LazyLoadingPerformanceMonitor {
  private static loadTimes: Map<string, number> = new Map();
  private static loadStartTimes: Map<string, number> = new Map();

  static startLoad(componentName: string) {
    this.loadStartTimes.set(componentName, performance.now());
  }

  static endLoad(componentName: string) {
    const startTime = this.loadStartTimes.get(componentName);
    if (startTime) {
      const loadTime = performance.now() - startTime;
      this.loadTimes.set(componentName, loadTime);
      this.loadStartTimes.delete(componentName);
      
      if (process.env.NODE_ENV === 'development') {
        console.log(`🚀 Lazy loaded ${componentName} in ${loadTime.toFixed(2)}ms`);
      }
    }
  }

  static getLoadTimes(): Record<string, number> {
    return Object.fromEntries(this.loadTimes);
  }

  static getAverageLoadTime(): number {
    const times = Array.from(this.loadTimes.values());
    return times.length > 0 ? times.reduce((a, b) => a + b, 0) / times.length : 0;
  }
}

// Global styles for loading animations
export const LazyLoadingStyles = `
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  .lazy-component-enter {
    animation: fadeIn 0.3s ease-out;
  }
`;

// Inject styles
if (typeof document !== 'undefined') {
  const styleElement = document.createElement('style');
  styleElement.textContent = LazyLoadingStyles;
  document.head.appendChild(styleElement);
}