/**
 * Enhanced test runner with comprehensive testing capabilities
 */

import { cleanup, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { APIMockManager } from './apiMocks';
import { renderWithAllProviders } from './renderUtils';
import type { TestConfig } from './testConfig';
import { getTestConfig, testAssertions, testDataFactories } from './testConfig';
import { createTestEnvironment } from './testHelpers';

/**
 * Interface for test suite configuration
 */
interface TestSuiteConfig {
  name: string;
  description?: string;
  config?: Partial<TestConfig>;
  setup?: () => Promise<void> | void;
  teardown?: () => Promise<void> | void;
  beforeEach?: () => Promise<void> | void;
  afterEach?: () => Promise<void> | void;
}

/**
 * Interface for test case configuration
 */
interface TestCaseConfig {
  name: string;
  description?: string;
  timeout?: number;
  retries?: number;
  skip?: boolean;
  only?: boolean;
  tags?: string[];
  setup?: () => Promise<void> | void;
  teardown?: () => Promise<void> | void;
}

/**
 * Interface for component test configuration
 */
interface ComponentTestConfig extends TestCaseConfig {
  component: React.ComponentType<any>;
  props?: Record<string, any>;
  providers?: any;
  mockServices?: Record<string, any>;
  testAccessibility?: boolean;
  testPerformance?: boolean;
  testResponsive?: boolean;
  testErrorBoundary?: boolean;
}

/**
 * Interface for API test configuration
 */
interface APITestConfig extends TestCaseConfig {
  endpoint: string;
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  payload?: any;
  expectedResponse?: any;
  expectedError?: any;
  testPerformance?: boolean;
  testErrorHandling?: boolean;
}

/**
 * Interface for integration test configuration
 */
interface IntegrationTestConfig extends TestCaseConfig {
  scenario: string;
  steps: Array<{
    action: string;
    target?: string;
    value?: any;
    timeout?: number;
    assertion?: (result: any) => void;
  }>;
  testData?: Record<string, any>;
  mockAPIs?: boolean;
}

/**
 * Enhanced test runner class
 */
export class EnhancedTestRunner {
  private config: TestConfig;
  private testEnvironment: any;
  private apiMockManager?: APIMockManager;
  private performanceMetrics: Array<{ name: string; duration: number; timestamp: number }> = [];
  private accessibilityResults: Array<{ component: string; violations: any[] }> = [];

  constructor(config?: Partial<TestConfig>) {
    this.config = config ? { ...getTestConfig(), ...config } : getTestConfig();
  }

  /**
   * Create a test suite with comprehensive setup
   */
  createTestSuite(suiteConfig: TestSuiteConfig, tests: () => void): void {
    describe(suiteConfig.name, () => {
      let environment: any;

      beforeEach(async () => {
        // Set up test environment
        environment = createTestEnvironment({
          mockAPIs: this.config.mockAPIs,
          mockStorage: this.config.mockStorage,
          mockWebAPIs: this.config.mockWebAPIs,
          mockMediaDevices: this.config.mockMediaDevices,
          mockNotifications: this.config.mockNotifications,
        });

        // Set up API mocking if enabled
        if (this.config.mockAPIs) {
          this.apiMockManager = new APIMockManager();
        }

        // Run custom setup
        if (suiteConfig.setup) {
          await suiteConfig.setup();
        }

        if (suiteConfig.beforeEach) {
          await suiteConfig.beforeEach();
        }
      });

      afterEach(async () => {
        // Run custom teardown
        if (suiteConfig.afterEach) {
          await suiteConfig.afterEach();
        }

        // Clean up environment
        if (environment?.cleanup) {
          environment.cleanup();
        }

        if (this.apiMockManager) {
          this.apiMockManager.restore();
        }

        cleanup();
      });

      // Run the tests
      tests();
    });
  }

  /**
   * Create a component test with comprehensive checks
   */
  createComponentTest(testConfig: ComponentTestConfig): void {
    const testFn = testConfig.skip ? it.skip : testConfig.only ? it.only : it;
    
    testFn(testConfig.name, async () => {
      const startTime = performance.now();

      try {
        // Setup
        if (testConfig.setup) {
          await testConfig.setup();
        }

        // Render component
        const renderResult = renderWithAllProviders(
          React.createElement(testConfig.component, testConfig.props),
          {
            providers: testConfig.providers,
            mockServices: testConfig.mockServices,
          }
        );

        const { container } = renderResult;

        // Basic render test
        expect(container).toBeInTheDocument();

        // Performance testing
        if (testConfig.testPerformance || this.config.enablePerformanceMonitoring) {
          const renderTime = performance.now() - startTime;
          testAssertions.assertRenderTime(renderTime, this.config.performanceThresholds.renderTime);
          
          this.performanceMetrics.push({
            name: `${testConfig.name} - Render Time`,
            duration: renderTime,
            timestamp: Date.now(),
          });
        }

        // Accessibility testing
        if (testConfig.testAccessibility || this.config.enableAccessibilityTesting) {
          await this.runAccessibilityTests(container, testConfig.name);
        }

        // Responsive testing
        if (testConfig.testResponsive) {
          await this.runResponsiveTests(testConfig.component, testConfig.props);
        }

        // Error boundary testing
        if (testConfig.testErrorBoundary) {
          await this.runErrorBoundaryTests(testConfig.component, testConfig.props);
        }

        // Teardown
        if (testConfig.teardown) {
          await testConfig.teardown();
        }

      } catch (error) {
        console.error(`Component test failed: ${testConfig.name}`, error);
        throw error;
      }
    }, testConfig.timeout || this.config.timeout);
  }

  /**
   * Create an API test with comprehensive checks
   */
  createAPITest(testConfig: APITestConfig): void {
    const testFn = testConfig.skip ? it.skip : testConfig.only ? it.only : it;
    
    testFn(testConfig.name, async () => {
      const startTime = performance.now();

      try {
        // Setup
        if (testConfig.setup) {
          await testConfig.setup();
        }

        // Mock API response
        if (this.apiMockManager) {
          if (testConfig.expectedError) {
            this.apiMockManager.mockEndpoint(testConfig.endpoint, {
              method: testConfig.method,
              shouldFail: true,
              error: testConfig.expectedError,
            });
          } else {
            this.apiMockManager.mockEndpoint(testConfig.endpoint, {
              method: testConfig.method,
              response: testConfig.expectedResponse,
            });
          }
        }

        // Make API call
        const response = await fetch(testConfig.endpoint, {
          method: testConfig.method || 'GET',
          headers: { 'Content-Type': 'application/json' },
          body: testConfig.payload ? JSON.stringify(testConfig.payload) : undefined,
        });

        // Performance testing
        if (testConfig.testPerformance || this.config.enablePerformanceMonitoring) {
          const responseTime = performance.now() - startTime;
          testAssertions.assertAPIResponseTime(responseTime, this.config.performanceThresholds.apiResponseTime);
          
          this.performanceMetrics.push({
            name: `${testConfig.name} - API Response Time`,
            duration: responseTime,
            timestamp: Date.now(),
          });
        }

        // Verify response
        if (testConfig.expectedError) {
          expect(response.ok).toBe(false);
        } else {
          expect(response.ok).toBe(true);
          if (testConfig.expectedResponse) {
            const data = await response.json();
            expect(data).toMatchObject(testConfig.expectedResponse);
          }
        }

        // Error handling testing
        if (testConfig.testErrorHandling) {
          await this.runAPIErrorHandlingTests(testConfig.endpoint, testConfig.method);
        }

        // Teardown
        if (testConfig.teardown) {
          await testConfig.teardown();
        }

      } catch (error) {
        if (testConfig.expectedError) {
          expect(error).toMatchObject(testConfig.expectedError);
        } else {
          console.error(`API test failed: ${testConfig.name}`, error);
          throw error;
        }
      }
    }, testConfig.timeout || this.config.timeout);
  }

  /**
   * Create an integration test with step-by-step execution
   */
  createIntegrationTest(testConfig: IntegrationTestConfig): void {
    const testFn = testConfig.skip ? it.skip : testConfig.only ? it.only : it;
    
    testFn(testConfig.name, async () => {
      const user = userEvent.setup();

      try {
        // Setup
        if (testConfig.setup) {
          await testConfig.setup();
        }

        // Seed test data
        if (testConfig.testData) {
          Object.entries(testConfig.testData).forEach(([key, data]) => {
            (globalThis as any)[`__testData_${key}`] = data;
          });
        }

        // Execute steps
        for (const [index, step] of testConfig.steps.entries()) {
          console.log(`Executing step ${index + 1}: ${step.action}`);

          switch (step.action) {
            case 'render':
              // Render component or navigate to page
              break;

            case 'click':
              if (step.target) {
                const element = screen.getByRole('button', { name: new RegExp(step.target, 'i') });
                await user.click(element);
              }
              break;

            case 'type':
              if (step.target && step.value) {
                const element = screen.getByRole('textbox');
                await user.type(element, step.value);
              }
              break;

            case 'wait':
              if (step.target) {
                await waitFor(() => {
                  expect(screen.getByText(new RegExp(step.target!, 'i'))).toBeInTheDocument();
                }, { timeout: step.timeout || 5000 });
              }
              break;

            case 'verify':
              if (step.assertion) {
                const result = step.target ? screen.getByText(new RegExp(step.target, 'i')) : null;
                step.assertion(result);
              }
              break;

            default:
              console.warn(`Unknown step action: ${step.action}`);
          }
        }

        // Teardown
        if (testConfig.teardown) {
          await testConfig.teardown();
        }

      } catch (error) {
        console.error(`Integration test failed: ${testConfig.name}`, error);
        throw error;
      }
    }, testConfig.timeout || this.config.timeout);
  }

  /**
   * Run accessibility tests on a component
   */
  private async runAccessibilityTests(container: HTMLElement, componentName: string): Promise<void> {
    try {
      // Basic accessibility checks
      testAssertions.assertKeyboardAccessible(container);

      // Check for ARIA violations (mock implementation)
      const violations: any[] = [];
      
      // Check for missing alt text on images
      const images = container.querySelectorAll('img');
      images.forEach((img, index) => {
        if (!img.getAttribute('alt') && img.getAttribute('role') !== 'presentation') {
          violations.push({
            id: 'image-alt',
            description: `Image at index ${index} missing alt text`,
            element: img,
          });
        }
      });

      // Check for missing form labels
      const inputs = container.querySelectorAll('input:not([type="hidden"]), textarea, select');
      inputs.forEach((input, index) => {
        const hasLabel = 
          input.getAttribute('aria-label') ||
          input.getAttribute('aria-labelledby') ||
          container.querySelector(`label[for="${input.id}"]`) ||
          input.closest('label');
        
        if (!hasLabel) {
          violations.push({
            id: 'form-field-label',
            description: `Form field at index ${index} missing label`,
            element: input,
          });
        }
      });

      // Store results
      this.accessibilityResults.push({
        component: componentName,
        violations,
      });

      // Assert no violations if threshold is 0
      if (this.config.accessibilityThresholds.violations === 0) {
        testAssertions.assertNoAccessibilityViolations(violations);
      }

    } catch (error) {
      console.error(`Accessibility test failed for ${componentName}:`, error);
      throw error;
    }
  }

  /**
   * Run responsive tests on a component
   */
  private async runResponsiveTests(Component: React.ComponentType<any>, props?: any): Promise<void> {
    const viewports = [
      { width: 320, height: 568, name: 'Mobile Portrait' },
      { width: 768, height: 1024, name: 'Tablet Portrait' },
      { width: 1920, height: 1080, name: 'Desktop' },
    ];

    for (const viewport of viewports) {
      // Mock window dimensions
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: viewport.width,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: viewport.height,
      });

      // Trigger resize event
      window.dispatchEvent(new Event('resize'));

      // Re-render component
      const { container } = renderWithAllProviders(
        React.createElement(Component, props)
      );

      // Wait for responsive changes
      await waitFor(() => {
        expect(container).toBeInTheDocument();
      });

      // Verify component is still functional
      expect(container.children.length).toBeGreaterThan(0);
    }
  }

  /**
   * Run error boundary tests on a component
   */
  private async runErrorBoundaryTests(Component: React.ComponentType<any>, props?: any): Promise<void> {
    const ErrorThrowingComponent = ({ shouldThrow }: { shouldThrow: boolean }) => {
      if (shouldThrow) {
        throw new Error('Test error for error boundary');
      }
      return React.createElement(Component, props);
    };

    const ErrorBoundary = ({ children }: { children: React.ReactNode }) => {
      const [hasError, setHasError] = React.useState(false);

      if (hasError) {
        return React.createElement('div', { 'data-testid': 'error-boundary' }, 'Something went wrong');
      }

      try {
        return children as React.ReactElement;
      } catch (error) {
        setHasError(true);
        return React.createElement('div', { 'data-testid': 'error-boundary' }, 'Something went wrong');
      }
    };

    const { container } = renderWithAllProviders(
      React.createElement(ErrorBoundary, {}, 
        React.createElement(ErrorThrowingComponent, { shouldThrow: true })
      )
    );

    await waitFor(() => {
      expect(screen.getByTestId('error-boundary')).toBeInTheDocument();
    });
  }

  /**
   * Run API error handling tests
   */
  private async runAPIErrorHandlingTests(endpoint: string, method: string = 'GET'): Promise<void> {
    const errorScenarios = [
      { status: 400, error: 'Bad Request' },
      { status: 401, error: 'Unauthorized' },
      { status: 403, error: 'Forbidden' },
      { status: 404, error: 'Not Found' },
      { status: 500, error: 'Internal Server Error' },
    ];

    for (const scenario of errorScenarios) {
      if (this.apiMockManager) {
        this.apiMockManager.mockEndpoint(endpoint, {
          method: method as any,
          status: scenario.status,
          shouldFail: true,
          error: testDataFactories.createAPIError({
            message: scenario.error,
            code: scenario.status.toString(),
          }),
        });

        try {
          await fetch(endpoint, { method });
          throw new Error(`Expected ${scenario.status} error was not thrown`);
        } catch (error: any) {
          expect(error.message).toContain(scenario.error);
        }
      }
    }
  }

  /**
   * Get performance metrics collected during tests
   */
  getPerformanceMetrics(): Array<{ name: string; duration: number; timestamp: number }> {
    return [...this.performanceMetrics];
  }

  /**
   * Get accessibility results from tests
   */
  getAccessibilityResults(): Array<{ component: string; violations: any[] }> {
    return [...this.accessibilityResults];
  }

  /**
   * Generate test report
   */
  generateTestReport(): {
    performance: Array<{ name: string; duration: number; timestamp: number }>;
    accessibility: Array<{ component: string; violations: any[] }>;
    summary: {
      totalPerformanceTests: number;
      averageRenderTime: number;
      totalAccessibilityTests: number;
      totalViolations: number;
    };
  } {
    const performanceTests = this.performanceMetrics.filter(m => m.name.includes('Render Time'));
    const averageRenderTime = performanceTests.length > 0 
      ? performanceTests.reduce((sum, test) => sum + test.duration, 0) / performanceTests.length 
      : 0;

    const totalViolations = this.accessibilityResults.reduce(
      (sum, result) => sum + result.violations.length, 
      0
    );

    return {
      performance: this.performanceMetrics,
      accessibility: this.accessibilityResults,
      summary: {
        totalPerformanceTests: this.performanceMetrics.length,
        averageRenderTime,
        totalAccessibilityTests: this.accessibilityResults.length,
        totalViolations,
      },
    };
  }

  /**
   * Reset all collected metrics and results
   */
  reset(): void {
    this.performanceMetrics = [];
    this.accessibilityResults = [];
  }
}

/**
 * Create a test runner instance with default configuration
 */
export const createTestRunner = (config?: Partial<TestConfig>): EnhancedTestRunner => {
  return new EnhancedTestRunner(config);
};

/**
 * Utility functions for common test patterns
 */
export const testUtils = {
  // Quick component test
  testComponent: (component: React.ComponentType<any>, props?: any, options?: Partial<ComponentTestConfig>) => {
    const runner = createTestRunner();
    runner.createComponentTest({
      name: `${component.displayName || component.name} - Basic Test`,
      component,
      props,
      testAccessibility: true,
      testPerformance: true,
      ...options,
    });
  },

  // Quick API test
  testAPI: (endpoint: string, options?: Partial<APITestConfig>) => {
    const runner = createTestRunner();
    runner.createAPITest({
      name: `API Test - ${endpoint}`,
      endpoint,
      testPerformance: true,
      testErrorHandling: true,
      ...options,
    });
  },

  // Quick integration test
  testIntegration: (scenario: string, steps: IntegrationTestConfig['steps'], options?: Partial<IntegrationTestConfig>) => {
    const runner = createTestRunner();
    runner.createIntegrationTest({
      name: `Integration Test - ${scenario}`,
      scenario,
      steps,
      ...options,
    });
  },
};