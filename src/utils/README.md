# Utils Directory

This directory contains utility functions, helpers, and common functionality used throughout the AI Scholar RAG chatbot application. Utilities are organized by domain and provide reusable, well-tested functions.

## Architecture Overview

Utilities follow a functional programming approach with:

- **Pure Functions**: No side effects, predictable outputs
- **Type Safety**: Full TypeScript support with proper type definitions
- **Modularity**: Small, focused functions that can be composed
- **Performance**: Optimized implementations with caching where appropriate
- **Testing**: Comprehensive test coverage for all utilities

## Utility Categories

### Performance & Monitoring
- **[performanceMonitor.ts](./performanceMonitor.ts)**: React component performance monitoring
- **[performanceOptimizations.ts](./performanceOptimizations.ts)**: Performance optimization utilities
- **[bundleOptimizer.ts](./bundleOptimizer.ts)**: Bundle size optimization tools
- **[codeSplitting.ts](./codeSplitting.ts)**: Code splitting and lazy loading utilities

### Error Handling
- **[globalErrorHandler.ts](./globalErrorHandler.ts)**: Global error handling and reporting
- **[errorFactory.ts](./errorFactory.ts)**: Error creation and classification utilities
- **[apiErrorHandler.ts](./apiErrorHandler.ts)**: API-specific error handling

### Data Processing
- **[treeShakingOptimizer.ts](./treeShakingOptimizer.ts)**: Tree shaking optimization utilities
- **[performanceRegression.ts](./performanceRegression.ts)**: Performance regression detection

## Usage Patterns

### Importing Utilities

Utilities can be imported individually or as a group:

```typescript
// Individual imports (recommended for tree shaking)
import { performanceMonitor } from './utils/performanceMonitor';
import { createAPIError } from './utils/errorFactory';

// Group imports
import * as PerformanceUtils from './utils/performanceOptimizations';
```

### Type-Safe Function Calls

All utilities are fully typed with TypeScript:

```typescript
import { measurePerformance, PerformanceMetrics } from './utils/performanceMonitor';

// Type-safe function call
const metrics: PerformanceMetrics = measurePerformance(() => {
  // Code to measure
  return expensiveOperation();
});

console.log(`Operation took ${metrics.duration}ms`);
```

### Error Handling Patterns

Utilities implement consistent error handling:

```typescript
import { handleAPIError, APIErrorType } from './utils/apiErrorHandler';

try {
  const result = await apiCall();
  return result;
} catch (error) {
  const handledError = handleAPIError(error, {
    context: 'user-profile-update',
    userId: currentUser.id
  });
  
  // Error is automatically logged and categorized
  throw handledError;
}
```

## Performance Utilities

### Performance Monitoring

Monitor React component performance:

```typescript
import { usePerformanceMonitor, withPerformanceMonitoring } from './utils/performanceMonitor';

// Hook-based monitoring
const MyComponent: React.FC = () => {
  usePerformanceMonitor('MyComponent');
  
  return <div>Component content</div>;
};

// HOC-based monitoring
const MonitoredComponent = withPerformanceMonitoring(MyComponent, 'MyComponent');
```

### Bundle Optimization

Analyze and optimize bundle size:

```typescript
import { analyzeBundleSize, optimizeImports } from './utils/bundleOptimizer';

// Analyze current bundle
const analysis = await analyzeBundleSize();
console.log(`Total bundle size: ${analysis.totalSize} bytes`);

// Get optimization suggestions
const suggestions = optimizeImports(analysis);
suggestions.forEach(suggestion => {
  console.log(`Suggestion: ${suggestion.description}`);
});
```

### Code Splitting

Implement dynamic imports and lazy loading:

```typescript
import { createLazyComponent, preloadComponent } from './utils/codeSplitting';

// Create lazy-loaded component
const LazyDashboard = createLazyComponent(() => import('./Dashboard'));

// Preload component on user interaction
const handleMouseEnter = () => {
  preloadComponent(() => import('./Dashboard'));
};
```

## Error Handling Utilities

### Global Error Handler

Set up global error handling:

```typescript
import { setupGlobalErrorHandler, ErrorContext } from './utils/globalErrorHandler';

// Initialize global error handling
setupGlobalErrorHandler({
  onError: (error, context) => {
    console.error('Global error:', error, context);
    // Send to error tracking service
  },
  enableConsoleLogging: process.env.NODE_ENV === 'development',
  enableRemoteLogging: process.env.NODE_ENV === 'production'
});
```

### Error Factory

Create standardized error objects:

```typescript
import { createAPIError, createValidationError, ErrorSeverity } from './utils/errorFactory';

// Create API error
const apiError = createAPIError({
  message: 'Failed to fetch user data',
  statusCode: 404,
  endpoint: '/api/users/123',
  severity: ErrorSeverity.MEDIUM
});

// Create validation error
const validationError = createValidationError({
  field: 'email',
  message: 'Invalid email format',
  value: 'invalid-email'
});
```

### API Error Handler

Handle API-specific errors:

```typescript
import { handleAPIError, isRetryableError } from './utils/apiErrorHandler';

const apiCall = async (url: string, options: RequestInit) => {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      throw await handleAPIError(response, { url, options });
    }
    
    return response.json();
  } catch (error) {
    if (isRetryableError(error)) {
      // Implement retry logic
      return retryApiCall(url, options);
    }
    throw error;
  }
};
```

## Data Processing Utilities

### Tree Shaking Optimizer

Optimize bundle size through tree shaking analysis:

```typescript
import { analyzeTreeShaking, getUnusedExports } from './utils/treeShakingOptimizer';

// Analyze tree shaking effectiveness
const analysis = await analyzeTreeShaking('./src');

// Get unused exports
const unusedExports = getUnusedExports(analysis);
console.log('Unused exports:', unusedExports);

// Generate optimization report
const report = generateOptimizationReport(analysis);
```

### Performance Regression Detection

Detect performance regressions:

```typescript
import { detectRegressions, PerformanceBaseline } from './utils/performanceRegression';

// Set performance baseline
const baseline: PerformanceBaseline = {
  renderTime: 16, // 16ms for 60fps
  bundleSize: 2048000, // 2MB
  loadTime: 3000 // 3 seconds
};

// Check for regressions
const currentMetrics = getCurrentPerformanceMetrics();
const regressions = detectRegressions(baseline, currentMetrics);

if (regressions.length > 0) {
  console.warn('Performance regressions detected:', regressions);
}
```

## Testing Utilities

### Test Helpers

Utilities include comprehensive test helpers:

```typescript
// Test file example
import { 
  measurePerformance, 
  createMockPerformanceEntry 
} from '../performanceMonitor';

describe('performanceMonitor', () => {
  it('measures function execution time', () => {
    const mockFn = jest.fn(() => 'result');
    const metrics = measurePerformance(mockFn);
    
    expect(metrics.duration).toBeGreaterThan(0);
    expect(metrics.result).toBe('result');
    expect(mockFn).toHaveBeenCalledTimes(1);
  });
  
  it('handles async functions', async () => {
    const asyncFn = jest.fn(async () => {
      await new Promise(resolve => setTimeout(resolve, 100));
      return 'async result';
    });
    
    const metrics = await measurePerformance(asyncFn);
    expect(metrics.duration).toBeGreaterThanOrEqual(100);
    expect(metrics.result).toBe('async result');
  });
});
```

### Mock Factories

Create mock data for testing:

```typescript
import { createMockError, createMockPerformanceMetrics } from '../testUtils';

// Create mock error for testing
const mockError = createMockError({
  type: 'NetworkError',
  message: 'Connection failed',
  statusCode: 500
});

// Create mock performance metrics
const mockMetrics = createMockPerformanceMetrics({
  duration: 150,
  memoryUsage: 1024000
});
```

## Configuration

Utilities can be configured through environment variables:

```typescript
// Performance monitoring configuration
const PERFORMANCE_CONFIG = {
  enableMonitoring: process.env.NODE_ENV !== 'test',
  sampleRate: parseFloat(process.env.PERFORMANCE_SAMPLE_RATE || '0.1'),
  maxMetricsHistory: parseInt(process.env.MAX_METRICS_HISTORY || '1000'),
  slowThreshold: parseInt(process.env.SLOW_THRESHOLD || '16')
};

// Error handling configuration
const ERROR_CONFIG = {
  enableRemoteLogging: process.env.NODE_ENV === 'production',
  logLevel: process.env.LOG_LEVEL || 'error',
  maxErrorHistory: parseInt(process.env.MAX_ERROR_HISTORY || '100')
};
```

## Best Practices

### Function Design

Write pure, composable functions:

```typescript
// Good: Pure function with clear inputs/outputs
export const formatFileSize = (bytes: number): string => {
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`;
};

// Good: Composable functions
export const pipe = <T>(...fns: Array<(arg: T) => T>) => (value: T): T =>
  fns.reduce((acc, fn) => fn(acc), value);

export const processData = pipe(
  validateData,
  transformData,
  formatData
);
```

### Error Handling

Implement consistent error handling:

```typescript
// Good: Consistent error handling with types
export const safeAsyncOperation = async <T>(
  operation: () => Promise<T>,
  fallback: T
): Promise<T> => {
  try {
    return await operation();
  } catch (error) {
    console.error('Operation failed:', error);
    return fallback;
  }
};

// Usage
const result = await safeAsyncOperation(
  () => fetchUserData(userId),
  { id: userId, name: 'Unknown' }
);
```

### Performance Optimization

Optimize for performance:

```typescript
// Good: Memoization for expensive operations
const memoize = <T extends (...args: any[]) => any>(fn: T): T => {
  const cache = new Map();
  
  return ((...args: any[]) => {
    const key = JSON.stringify(args);
    
    if (cache.has(key)) {
      return cache.get(key);
    }
    
    const result = fn(...args);
    cache.set(key, result);
    return result;
  }) as T;
};

// Good: Debouncing for frequent operations
export const debounce = <T extends (...args: any[]) => any>(
  fn: T,
  delay: number
): T => {
  let timeoutId: NodeJS.Timeout;
  
  return ((...args: any[]) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  }) as T;
};
```

## Adding New Utilities

When adding new utilities:

1. **Create focused, single-purpose functions**
2. **Add comprehensive TypeScript types**
3. **Include JSDoc documentation with examples**
4. **Write thorough unit tests**
5. **Consider performance implications**
6. **Update this README with usage examples**

### Utility Template

```typescript
/**
 * @fileoverview [Utility Name] Utilities
 * [Brief description of what the utilities do]
 * 
 * @author AI Scholar Team
 * @version 1.0.0
 * @since 2024-01-01
 */

/**
 * [Function description]
 * 
 * @param {Type} param - Parameter description
 * @returns {ReturnType} Description of return value
 * 
 * @example
 * ```typescript
 * const result = utilityFunction(input);
 * console.log(result);
 * ```
 */
export const utilityFunction = (param: Type): ReturnType => {
  // Implementation
  return result;
};

/**
 * [Async function description]
 * 
 * @param {Type} param - Parameter description
 * @returns {Promise<ReturnType>} Description of return value
 * 
 * @example
 * ```typescript
 * const result = await asyncUtilityFunction(input);
 * console.log(result);
 * ```
 */
export const asyncUtilityFunction = async (param: Type): Promise<ReturnType> => {
  // Implementation
  return result;
};

// Export types
export type { Type, ReturnType };
```

## Documentation

For detailed documentation of each utility:

1. Check the utility file for JSDoc comments
2. Review the test files for usage examples
3. Consult the generated API documentation
4. Check the main application documentation

## Contributing

When contributing to utilities:

1. Follow functional programming principles
2. Add comprehensive documentation and examples
3. Include unit tests with edge cases
4. Consider performance and memory usage
5. Ensure type safety with TypeScript
6. Update relevant documentation

## Support

For questions about utilities or to report issues:

1. Check the individual utility documentation
2. Review the test files for usage examples
3. Consult the generated API documentation
4. Create an issue in the project repository