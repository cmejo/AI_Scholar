/**
 * Integration test environment setup and configuration
 */

import { cleanup } from '@testing-library/react';
import { afterAll, afterEach, beforeAll, beforeEach, vi } from 'vitest';
import type { APIMockConfig } from '../utils/apiMocks';
import { APIMockManager } from '../utils/apiMocks';

/**
 * Interface for integration test environment configuration
 */
interface IntegrationTestConfig {
  apiMocking?: APIMockConfig;
  enableRealAPI?: boolean;
  testTimeout?: number;
  setupDatabase?: boolean;
  mockServices?: string[];
  enablePerformanceMonitoring?: boolean;
  enableAccessibilityTesting?: boolean;
  enableErrorTracking?: boolean;
  customMocks?: Record<string, any>;
  testDataSeed?: Record<string, any>;
}

/**
 * Integration test environment manager
 */
export class IntegrationTestEnvironment {
  private apiMockManager?: APIMockManager;
  private config: IntegrationTestConfig;
  private originalEnv: Record<string, string | undefined> = {};

  constructor(config: IntegrationTestConfig = {}) {
    this.config = {
      testTimeout: 30000,
      enableRealAPI: false,
      setupDatabase: false,
      mockServices: [],
      enablePerformanceMonitoring: true,
      enableAccessibilityTesting: true,
      enableErrorTracking: true,
      customMocks: {},
      testDataSeed: {},
      ...config,
    };
  }

  /**
   * Set up the integration test environment
   */
  async setup(): Promise<void> {
    // Store original environment variables
    this.storeOriginalEnv();

    // Set test environment variables
    this.setTestEnv();

    // Set up API mocking if not using real API
    if (!this.config.enableRealAPI) {
      this.setupAPIMocking();
    }

    // Mock external services
    this.mockExternalServices();

    // Set up test database if needed
    if (this.config.setupDatabase) {
      await this.setupTestDatabase();
    }
  }

  /**
   * Clean up the integration test environment
   */
  async cleanup(): Promise<void> {
    // Restore original environment
    this.restoreOriginalEnv();

    // Clean up API mocks
    if (this.apiMockManager) {
      this.apiMockManager.restore();
    }

    // Clean up React Testing Library
    cleanup();

    // Clean up test database if needed
    if (this.config.setupDatabase) {
      await this.cleanupTestDatabase();
    }
  }

  /**
   * Store original environment variables
   */
  private storeOriginalEnv(): void {
    const envVars = [
      'NODE_ENV',
      'API_BASE_URL',
      'VITE_API_BASE_URL',
      'DATABASE_URL',
      'REDIS_URL',
    ];

    envVars.forEach(key => {
      this.originalEnv[key] = process.env[key];
    });
  }

  /**
   * Set test environment variables
   */
  private setTestEnv(): void {
    process.env.NODE_ENV = 'test';
    process.env.API_BASE_URL = 'http://localhost:3000/api';
    process.env.VITE_API_BASE_URL = 'http://localhost:3000/api';
    
    if (this.config.setupDatabase) {
      process.env.DATABASE_URL = 'sqlite://test.db';
    }
  }

  /**
   * Restore original environment variables
   */
  private restoreOriginalEnv(): void {
    Object.entries(this.originalEnv).forEach(([key, value]) => {
      if (value === undefined) {
        delete process.env[key];
      } else {
        process.env[key] = value;
      }
    });
  }

  /**
   * Set up API mocking
   */
  private setupAPIMocking(): void {
    this.apiMockManager = new APIMockManager(this.config.apiMocking);
    this.apiMockManager
      .mockChatEndpoints()
      .mockDocumentEndpoints()
      .mockSearchEndpoints()
      .mockVoiceEndpoints();
  }

  /**
   * Mock external services
   */
  private mockExternalServices(): void {
    // Mock localStorage
    const localStorageMock = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
      length: 0,
      key: vi.fn(),
    };
    Object.defineProperty(window, 'localStorage', { value: localStorageMock });

    // Mock sessionStorage
    const sessionStorageMock = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
      length: 0,
      key: vi.fn(),
    };
    Object.defineProperty(window, 'sessionStorage', { value: sessionStorageMock });

    // Mock IndexedDB
    const mockIndexedDB = {
      open: vi.fn(() => ({
        onsuccess: null,
        onerror: null,
        result: {
          createObjectStore: vi.fn(),
          transaction: vi.fn(() => ({
            objectStore: vi.fn(() => ({
              add: vi.fn(),
              get: vi.fn(),
              put: vi.fn(),
              delete: vi.fn(),
              getAll: vi.fn(),
            })),
          })),
        },
      })),
      deleteDatabase: vi.fn(),
    };
    Object.defineProperty(window, 'indexedDB', { value: mockIndexedDB });

    // Mock Notification API
    const mockNotification = vi.fn();
    mockNotification.permission = 'granted';
    mockNotification.requestPermission = vi.fn(() => Promise.resolve('granted'));
    Object.defineProperty(window, 'Notification', { value: mockNotification });

    // Mock geolocation
    const mockGeolocation = {
      getCurrentPosition: vi.fn(),
      watchPosition: vi.fn(),
      clearWatch: vi.fn(),
    };
    Object.defineProperty(navigator, 'geolocation', { value: mockGeolocation });

    // Mock service worker
    const mockServiceWorker = {
      register: vi.fn(() => Promise.resolve({
        installing: null,
        waiting: null,
        active: null,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })),
      getRegistration: vi.fn(() => Promise.resolve(null)),
      getRegistrations: vi.fn(() => Promise.resolve([])),
    };
    Object.defineProperty(navigator, 'serviceWorker', { value: mockServiceWorker });
  }

  /**
   * Set up test database
   */
  private async setupTestDatabase(): Promise<void> {
    // This would typically set up a test database
    // For now, we'll just mock it
    console.log('Setting up test database...');
  }

  /**
   * Clean up test database
   */
  private async cleanupTestDatabase(): Promise<void> {
    // This would typically clean up the test database
    // For now, we'll just mock it
    console.log('Cleaning up test database...');
  }

  /**
   * Get the API mock manager
   */
  getAPIMockManager(): APIMockManager | undefined {
    return this.apiMockManager;
  }

  /**
   * Wait for all async operations to complete
   */
  async waitForAsyncOperations(): Promise<void> {
    await new Promise(resolve => setTimeout(resolve, 0));
    await vi.runAllTimersAsync();
  }

  /**
   * Set up performance monitoring for tests
   */
  private setupPerformanceMonitoring(): void {
    if (!this.config.enablePerformanceMonitoring) return;

    // Mock performance.mark and performance.measure
    const originalMark = performance.mark;
    const originalMeasure = performance.measure;
    const originalGetEntriesByType = performance.getEntriesByType;

    const marks = new Map<string, number>();
    const measures = new Map<string, { duration: number; startTime: number }>();

    performance.mark = vi.fn().mockImplementation((name: string) => {
      marks.set(name, performance.now());
      return originalMark.call(performance, name);
    });

    performance.measure = vi.fn().mockImplementation((name: string, startMark?: string, endMark?: string) => {
      const startTime = startMark ? marks.get(startMark) || 0 : 0;
      const endTime = endMark ? marks.get(endMark) || performance.now() : performance.now();
      const duration = endTime - startTime;
      measures.set(name, { duration, startTime });
      return originalMeasure.call(performance, name, startMark, endMark);
    });

    performance.getEntriesByType = vi.fn().mockImplementation((type: string) => {
      if (type === 'mark') {
        return Array.from(marks.entries()).map(([name, startTime]) => ({
          name,
          entryType: 'mark',
          startTime,
          duration: 0,
        }));
      } else if (type === 'measure') {
        return Array.from(measures.entries()).map(([name, { duration, startTime }]) => ({
          name,
          entryType: 'measure',
          startTime,
          duration,
        }));
      }
      return originalGetEntriesByType.call(performance, type);
    });
  }

  /**
   * Set up accessibility testing utilities
   */
  private setupAccessibilityTesting(): void {
    if (!this.config.enableAccessibilityTesting) return;

    // Mock axe-core for accessibility testing
    const mockAxe = {
      run: vi.fn().mockResolvedValue({
        violations: [],
        passes: [],
        incomplete: [],
        inapplicable: [],
      }),
      configure: vi.fn(),
      reset: vi.fn(),
    };

    vi.doMock('axe-core', () => ({ default: mockAxe }));
  }

  /**
   * Set up error tracking for tests
   */
  private setupErrorTracking(): void {
    if (!this.config.enableErrorTracking) return;

    const errors: Array<{ error: Error; context: any; timestamp: number }> = [];
    const originalConsoleError = console.error;
    const originalWindowError = window.onerror;
    const originalUnhandledRejection = window.onunhandledrejection;

    // Track console errors
    console.error = vi.fn().mockImplementation((...args) => {
      errors.push({
        error: new Error(args.join(' ')),
        context: { type: 'console.error', args },
        timestamp: Date.now(),
      });
      originalConsoleError.apply(console, args);
    });

    // Track window errors
    window.onerror = vi.fn().mockImplementation((message, source, lineno, colno, error) => {
      errors.push({
        error: error || new Error(message as string),
        context: { type: 'window.error', source, lineno, colno },
        timestamp: Date.now(),
      });
      if (originalWindowError) {
        return originalWindowError.call(window, message, source, lineno, colno, error);
      }
      return false;
    });

    // Track unhandled promise rejections
    window.onunhandledrejection = vi.fn().mockImplementation((event) => {
      errors.push({
        error: event.reason instanceof Error ? event.reason : new Error(event.reason),
        context: { type: 'unhandledrejection', reason: event.reason },
        timestamp: Date.now(),
      });
      if (originalUnhandledRejection) {
        return originalUnhandledRejection.call(window, event);
      }
    });

    // Expose error tracking utilities
    (globalThis as any).__testErrorTracker = {
      getErrors: () => [...errors],
      clearErrors: () => errors.length = 0,
      getErrorCount: () => errors.length,
      getErrorsByType: (type: string) => errors.filter(e => e.context.type === type),
    };
  }

  /**
   * Seed test data
   */
  private async seedTestData(): Promise<void> {
    if (!this.config.testDataSeed || Object.keys(this.config.testDataSeed).length === 0) {
      return;
    }

    // Mock data seeding - in a real implementation, this would populate test databases
    Object.entries(this.config.testDataSeed).forEach(([key, data]) => {
      (globalThis as any)[`__testData_${key}`] = data;
    });
  }

  /**
   * Apply custom mocks
   */
  private applyCustomMocks(): void {
    if (!this.config.customMocks || Object.keys(this.config.customMocks).length === 0) {
      return;
    }

    Object.entries(this.config.customMocks).forEach(([modulePath, mockImplementation]) => {
      vi.doMock(modulePath, () => mockImplementation);
    });
  }

  /**
   * Get performance metrics collected during tests
   */
  getPerformanceMetrics(): {
    marks: Array<{ name: string; startTime: number }>;
    measures: Array<{ name: string; duration: number; startTime: number }>;
  } {
    if (!this.config.enablePerformanceMonitoring) {
      return { marks: [], measures: [] };
    }

    const marks = performance.getEntriesByType('mark').map(entry => ({
      name: entry.name,
      startTime: entry.startTime,
    }));

    const measures = performance.getEntriesByType('measure').map(entry => ({
      name: entry.name,
      duration: entry.duration,
      startTime: entry.startTime,
    }));

    return { marks, measures };
  }

  /**
   * Get accessibility test results
   */
  async getAccessibilityResults(element?: HTMLElement): Promise<{
    violations: any[];
    passes: any[];
    incomplete: any[];
  }> {
    if (!this.config.enableAccessibilityTesting) {
      return { violations: [], passes: [], incomplete: [] };
    }

    try {
      const axe = await import('axe-core');
      const results = await axe.default.run(element || document);
      return {
        violations: results.violations,
        passes: results.passes,
        incomplete: results.incomplete,
      };
    } catch (error) {
      console.warn('Accessibility testing not available:', error);
      return { violations: [], passes: [], incomplete: [] };
    }
  }

  /**
   * Get error tracking results
   */
  getErrorTrackingResults(): {
    errors: Array<{ error: Error; context: any; timestamp: number }>;
    errorCount: number;
    errorsByType: Record<string, number>;
  } {
    if (!this.config.enableErrorTracking) {
      return { errors: [], errorCount: 0, errorsByType: {} };
    }

    const tracker = (globalThis as any).__testErrorTracker;
    if (!tracker) {
      return { errors: [], errorCount: 0, errorsByType: {} };
    }

    const errors = tracker.getErrors();
    const errorsByType = errors.reduce((acc: Record<string, number>, error: any) => {
      const type = error.context.type;
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {});

    return {
      errors,
      errorCount: errors.length,
      errorsByType,
    };
  }
}

/**
 * Global integration test environment instance
 */
let globalTestEnvironment: IntegrationTestEnvironment | null = null;

/**
 * Set up integration test environment globally
 */
export const setupIntegrationTestEnvironment = (config?: IntegrationTestConfig): void => {
  beforeAll(async () => {
    globalTestEnvironment = new IntegrationTestEnvironment(config);
    await globalTestEnvironment.setup();
  });

  afterAll(async () => {
    if (globalTestEnvironment) {
      await globalTestEnvironment.cleanup();
      globalTestEnvironment = null;
    }
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });
};

/**
 * Get the global test environment
 */
export const getIntegrationTestEnvironment = (): IntegrationTestEnvironment => {
  if (!globalTestEnvironment) {
    throw new Error('Integration test environment not set up. Call setupIntegrationTestEnvironment first.');
  }
  return globalTestEnvironment;
};

/**
 * Utility to run integration tests with proper setup/cleanup
 */
export const withIntegrationTestEnvironment = <T>(
  testFn: () => Promise<T> | T,
  config?: IntegrationTestConfig
): Promise<T> => {
  return new Promise(async (resolve, reject) => {
    const env = new IntegrationTestEnvironment(config);
    
    try {
      await env.setup();
      const result = await testFn();
      resolve(result);
    } catch (error) {
      reject(error);
    } finally {
      await env.cleanup();
    }
  });
};