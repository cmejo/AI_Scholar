/**
 * Comprehensive test configuration and utilities
 * Provides centralized configuration for all testing scenarios
 */

import type {
    APIError,
    FormError,
    StandardError
} from '../../types/api';
import type {
    ChatMessage,
    ChatResponse,
    DocumentMetadata,
    SearchResult
} from '../../types/ui';
import type {
    SpeechRecognitionResult,
    VoiceConfig
} from '../../types/voice';

/**
 * Global test configuration interface
 */
export interface TestConfig {
  // Environment settings
  environment: 'unit' | 'integration' | 'e2e';
  timeout: number;
  retries: number;
  
  // Mock settings
  mockAPIs: boolean;
  mockStorage: boolean;
  mockWebAPIs: boolean;
  mockMediaDevices: boolean;
  mockNotifications: boolean;
  
  // Feature flags
  enablePerformanceMonitoring: boolean;
  enableAccessibilityTesting: boolean;
  enableErrorTracking: boolean;
  enableCoverage: boolean;
  
  // Test data
  testDataSeed: Record<string, any>;
  customMocks: Record<string, any>;
  
  // Thresholds
  performanceThresholds: {
    renderTime: number;
    apiResponseTime: number;
    memoryUsage: number;
    bundleSize: number;
  };
  
  accessibilityThresholds: {
    violations: number;
    wcagLevel: 'A' | 'AA' | 'AAA';
  };
  
  coverageThresholds: {
    statements: number;
    branches: number;
    functions: number;
    lines: number;
  };
}

/**
 * Default test configurations for different environments
 */
export const defaultTestConfigs: Record<string, TestConfig> = {
  unit: {
    environment: 'unit',
    timeout: 5000,
    retries: 1,
    mockAPIs: true,
    mockStorage: true,
    mockWebAPIs: true,
    mockMediaDevices: true,
    mockNotifications: true,
    enablePerformanceMonitoring: false,
    enableAccessibilityTesting: false,
    enableErrorTracking: true,
    enableCoverage: true,
    testDataSeed: {},
    customMocks: {},
    performanceThresholds: {
      renderTime: 1000,
      apiResponseTime: 500,
      memoryUsage: 50 * 1024 * 1024, // 50MB
      bundleSize: 2 * 1024 * 1024, // 2MB
    },
    accessibilityThresholds: {
      violations: 0,
      wcagLevel: 'AA',
    },
    coverageThresholds: {
      statements: 85,
      branches: 80,
      functions: 85,
      lines: 85,
    },
  },
  
  integration: {
    environment: 'integration',
    timeout: 30000,
    retries: 2,
    mockAPIs: true,
    mockStorage: true,
    mockWebAPIs: true,
    mockMediaDevices: true,
    mockNotifications: true,
    enablePerformanceMonitoring: true,
    enableAccessibilityTesting: true,
    enableErrorTracking: true,
    enableCoverage: true,
    testDataSeed: {
      users: [
        { id: '1', name: 'Test User', email: 'test@example.com', role: 'user' },
        { id: '2', name: 'Admin User', email: 'admin@example.com', role: 'admin' },
      ],
      documents: [
        { id: '1', title: 'Test Document', type: 'pdf', size: 1024000 },
        { id: '2', title: 'Sample Paper', type: 'docx', size: 512000 },
      ],
    },
    customMocks: {},
    performanceThresholds: {
      renderTime: 2000,
      apiResponseTime: 1000,
      memoryUsage: 100 * 1024 * 1024, // 100MB
      bundleSize: 3 * 1024 * 1024, // 3MB
    },
    accessibilityThresholds: {
      violations: 0,
      wcagLevel: 'AA',
    },
    coverageThresholds: {
      statements: 80,
      branches: 75,
      functions: 80,
      lines: 80,
    },
  },
  
  e2e: {
    environment: 'e2e',
    timeout: 60000,
    retries: 3,
    mockAPIs: false,
    mockStorage: false,
    mockWebAPIs: false,
    mockMediaDevices: false,
    mockNotifications: false,
    enablePerformanceMonitoring: true,
    enableAccessibilityTesting: true,
    enableErrorTracking: true,
    enableCoverage: false,
    testDataSeed: {
      users: [
        { id: '1', name: 'E2E Test User', email: 'e2e@example.com', role: 'user' },
      ],
    },
    customMocks: {},
    performanceThresholds: {
      renderTime: 5000,
      apiResponseTime: 3000,
      memoryUsage: 200 * 1024 * 1024, // 200MB
      bundleSize: 5 * 1024 * 1024, // 5MB
    },
    accessibilityThresholds: {
      violations: 0,
      wcagLevel: 'AA',
    },
    coverageThresholds: {
      statements: 70,
      branches: 65,
      functions: 70,
      lines: 70,
    },
  },
};

/**
 * Test scenario templates for common testing patterns
 */
export const testScenarioTemplates = {
  // Component testing scenarios
  componentRender: {
    name: 'Component Render Test',
    description: 'Test that component renders without errors',
    steps: ['render', 'verify-no-errors', 'check-accessibility'],
    timeout: 5000,
  },
  
  componentInteraction: {
    name: 'Component Interaction Test',
    description: 'Test user interactions with component',
    steps: ['render', 'interact', 'verify-state-change', 'check-accessibility'],
    timeout: 10000,
  },
  
  componentError: {
    name: 'Component Error Handling Test',
    description: 'Test component error boundary behavior',
    steps: ['render', 'trigger-error', 'verify-error-boundary', 'verify-recovery'],
    timeout: 5000,
  },
  
  // API testing scenarios
  apiSuccess: {
    name: 'API Success Test',
    description: 'Test successful API request/response cycle',
    steps: ['setup-mock', 'make-request', 'verify-response', 'verify-side-effects'],
    timeout: 10000,
  },
  
  apiError: {
    name: 'API Error Test',
    description: 'Test API error handling',
    steps: ['setup-error-mock', 'make-request', 'verify-error-handling', 'verify-recovery'],
    timeout: 10000,
  },
  
  apiPerformance: {
    name: 'API Performance Test',
    description: 'Test API response time and resource usage',
    steps: ['setup-performance-monitoring', 'make-request', 'verify-performance-metrics'],
    timeout: 15000,
  },
  
  // Integration testing scenarios
  userWorkflow: {
    name: 'User Workflow Test',
    description: 'Test complete user workflow from start to finish',
    steps: ['setup-environment', 'simulate-user-actions', 'verify-outcomes', 'cleanup'],
    timeout: 30000,
  },
  
  dataFlow: {
    name: 'Data Flow Test',
    description: 'Test data flow between components and services',
    steps: ['setup-data', 'trigger-data-flow', 'verify-data-propagation', 'verify-persistence'],
    timeout: 20000,
  },
  
  // Accessibility testing scenarios
  keyboardNavigation: {
    name: 'Keyboard Navigation Test',
    description: 'Test keyboard accessibility',
    steps: ['render', 'test-tab-order', 'test-keyboard-shortcuts', 'verify-focus-management'],
    timeout: 10000,
  },
  
  screenReader: {
    name: 'Screen Reader Test',
    description: 'Test screen reader compatibility',
    steps: ['render', 'check-aria-labels', 'check-semantic-structure', 'verify-announcements'],
    timeout: 10000,
  },
  
  // Performance testing scenarios
  renderPerformance: {
    name: 'Render Performance Test',
    description: 'Test component rendering performance',
    steps: ['measure-initial-render', 'measure-re-render', 'measure-memory-usage', 'verify-thresholds'],
    timeout: 15000,
  },
  
  bundleSize: {
    name: 'Bundle Size Test',
    description: 'Test application bundle size',
    steps: ['analyze-bundle', 'check-tree-shaking', 'verify-size-limits', 'identify-optimizations'],
    timeout: 20000,
  },
};

/**
 * Common test data factories
 */
export const testDataFactories = {
  createUser: (overrides: Partial<any> = {}) => ({
    id: `user_${Date.now()}`,
    name: 'Test User',
    email: 'test@example.com',
    role: 'user',
    createdAt: new Date(),
    ...overrides,
  }),
  
  createDocument: (overrides: Partial<DocumentMetadata> = {}): DocumentMetadata => ({
    id: `doc_${Date.now()}`,
    title: 'Test Document',
    author: 'Test Author',
    type: 'pdf',
    size: 1024000,
    uploadDate: new Date(),
    lastModified: new Date(),
    tags: ['test'],
    summary: 'Test document summary',
    ...overrides,
  }),
  
  createChatMessage: (overrides: Partial<ChatMessage> = {}): ChatMessage => ({
    id: `msg_${Date.now()}`,
    content: 'Test message',
    role: 'user',
    timestamp: new Date(),
    metadata: {},
    ...overrides,
  }),
  
  createChatResponse: (overrides: Partial<ChatResponse> = {}): ChatResponse => ({
    id: `response_${Date.now()}`,
    content: 'Test response',
    role: 'assistant',
    timestamp: new Date(),
    sources: [],
    confidence: 0.9,
    processingTime: 1000,
    metadata: {},
    ...overrides,
  }),
  
  createSearchResult: (overrides: Partial<SearchResult> = {}): SearchResult => ({
    id: `result_${Date.now()}`,
    title: 'Test Result',
    content: 'Test content',
    score: 0.8,
    source: 'test-source.pdf',
    metadata: testDataFactories.createDocument(),
    highlights: ['test'],
    ...overrides,
  }),
  
  createAPIError: (overrides: Partial<APIError> = {}): APIError => ({
    type: 'NETWORK_ERROR',
    code: 'NETWORK_ERROR',
    message: 'Test API error',
    severity: 'medium',
    timestamp: new Date(),
    details: {},
    ...overrides,
  }),
  
  createStandardError: (overrides: Partial<StandardError> = {}): StandardError => ({
    id: `error_${Date.now()}`,
    type: 'COMPONENT_ERROR',
    code: 'COMPONENT_ERROR',
    message: 'Test error',
    severity: 'medium',
    timestamp: new Date(),
    recoverable: true,
    retryable: false,
    userMessage: 'A test error occurred',
    details: {},
    ...overrides,
  }),
  
  createFormError: (overrides: Partial<FormError> = {}): FormError => ({
    field: 'testField',
    message: 'Test form error',
    code: 'TEST_ERROR',
    value: 'testValue',
    ...overrides,
  }),
  
  createVoiceConfig: (overrides: Partial<VoiceConfig> = {}): VoiceConfig => ({
    language: 'en-US',
    voice: 'default',
    rate: 1.0,
    pitch: 1.0,
    volume: 1.0,
    continuous: true,
    interimResults: true,
    maxAlternatives: 1,
    ...overrides,
  }),
  
  createSpeechResult: (overrides: Partial<SpeechRecognitionResult> = {}): SpeechRecognitionResult => ({
    text: 'Test speech result',
    confidence: 0.95,
    language: 'en-US',
    timestamp: Date.now(),
    isFinal: true,
    alternatives: [],
    ...overrides,
  }),
};

/**
 * Test assertion helpers
 */
export const testAssertions = {
  // Performance assertions
  assertRenderTime: (actualTime: number, threshold: number = 1000) => {
    if (actualTime > threshold) {
      throw new Error(`Render time ${actualTime}ms exceeds threshold ${threshold}ms`);
    }
  },
  
  assertMemoryUsage: (actualUsage: number, threshold: number = 50 * 1024 * 1024) => {
    if (actualUsage > threshold) {
      throw new Error(`Memory usage ${actualUsage} bytes exceeds threshold ${threshold} bytes`);
    }
  },
  
  assertAPIResponseTime: (actualTime: number, threshold: number = 1000) => {
    if (actualTime > threshold) {
      throw new Error(`API response time ${actualTime}ms exceeds threshold ${threshold}ms`);
    }
  },
  
  // Accessibility assertions
  assertNoAccessibilityViolations: (violations: any[]) => {
    if (violations.length > 0) {
      const violationMessages = violations.map(v => `${v.id}: ${v.description}`).join('\n');
      throw new Error(`Accessibility violations found:\n${violationMessages}`);
    }
  },
  
  assertKeyboardAccessible: (element: HTMLElement) => {
    const focusableElements = element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    if (focusableElements.length === 0) {
      throw new Error('No focusable elements found - component may not be keyboard accessible');
    }
    
    focusableElements.forEach((el, index) => {
      const hasAccessibleName = 
        el.getAttribute('aria-label') ||
        el.getAttribute('aria-labelledby') ||
        el.textContent?.trim();
      
      if (!hasAccessibleName) {
        throw new Error(`Focusable element at index ${index} lacks accessible name`);
      }
    });
  },
  
  // Error handling assertions
  assertErrorHandled: (error: Error, expectedType: string) => {
    if (!error.name || !error.name.includes(expectedType)) {
      throw new Error(`Expected error type ${expectedType}, got ${error.name}`);
    }
  },
  
  assertErrorRecovery: (component: HTMLElement, recoveryIndicator: string) => {
    const recoveryElement = component.querySelector(`[data-testid="${recoveryIndicator}"]`);
    if (!recoveryElement) {
      throw new Error(`Error recovery indicator "${recoveryIndicator}" not found`);
    }
  },
  
  // Data integrity assertions
  assertDataPersistence: async (key: string, expectedValue: any, storage: 'localStorage' | 'sessionStorage' = 'localStorage') => {
    const actualValue = window[storage].getItem(key);
    const parsedValue = actualValue ? JSON.parse(actualValue) : null;
    
    if (JSON.stringify(parsedValue) !== JSON.stringify(expectedValue)) {
      throw new Error(`Data persistence failed for key "${key}". Expected: ${JSON.stringify(expectedValue)}, Got: ${JSON.stringify(parsedValue)}`);
    }
  },
  
  assertAPICallMade: (mockFetch: any, endpoint: string, method: string = 'GET') => {
    const calls = mockFetch.mock.calls;
    const matchingCall = calls.find((call: any[]) => {
      const [url, options] = call;
      return url.includes(endpoint) && (options?.method || 'GET') === method;
    });
    
    if (!matchingCall) {
      throw new Error(`Expected API call to ${method} ${endpoint} was not made`);
    }
  },
};

/**
 * Utility to get test configuration for current environment
 */
export const getTestConfig = (environment?: string): TestConfig => {
  const env = environment || process.env.NODE_ENV || 'unit';
  return defaultTestConfigs[env] || defaultTestConfigs.unit;
};

/**
 * Utility to merge custom test configuration
 */
export const mergeTestConfig = (base: TestConfig, overrides: Partial<TestConfig>): TestConfig => {
  return {
    ...base,
    ...overrides,
    performanceThresholds: {
      ...base.performanceThresholds,
      ...overrides.performanceThresholds,
    },
    accessibilityThresholds: {
      ...base.accessibilityThresholds,
      ...overrides.accessibilityThresholds,
    },
    coverageThresholds: {
      ...base.coverageThresholds,
      ...overrides.coverageThresholds,
    },
    testDataSeed: {
      ...base.testDataSeed,
      ...overrides.testDataSeed,
    },
    customMocks: {
      ...base.customMocks,
      ...overrides.customMocks,
    },
  };
};