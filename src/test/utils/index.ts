/**
 * Enhanced test utilities index
 * Exports all test utilities with proper TypeScript support
 */

// Core test utilities
export * from './apiMocks';
export * from './customMatchers';
export * from './fixtures';
export * from './mockFactories';
export * from './renderUtils';
export * from './testHelpers';

// Enhanced test utilities
export * from './testConfig';
export * from './testRunner';

// Integration test utilities
export * from '../integration/apiIntegration';
export * from '../integration/componentIntegration';
export * from '../integration/e2eHelpers';
export * from '../integration/testEnvironment';

// Re-export commonly used testing library functions with type safety
export {
    act,
    cleanup, findByLabelText, findByRole, findByTestId, findByText, fireEvent, getByLabelText, getByRole, getByTestId, getByText, queryByLabelText, queryByRole, queryByTestId, queryByText, render,
    screen, waitFor, within
} from '@testing-library/react';

export { default as userEvent } from '@testing-library/user-event';

// Re-export Vitest functions with enhanced types
export {
    afterAll,
    afterEach, beforeAll,
    beforeEach, describe, expect, it, suite, test, vi
} from 'vitest';

// Type exports for better TypeScript support
export type {
    AllByBoundAttribute, BoundFunction, FindByBoundAttribute, GetByBoundAttribute, Queries, QueryByBoundAttribute, RenderOptions, RenderResult, queries
} from '@testing-library/react';

export type {
    Mock, MockInstance, Mocked,
    MockedClass, MockedFunction, MockedObject
} from 'vitest';

// Enhanced type exports
export type { IntegrationTestConfig } from '../integration/testEnvironment';
export type { TestConfig } from './testConfig';

/**
 * Convenience object with all test utilities organized by category
 */
export const TestUtilities = {
  // Core utilities
  helpers: require('./testHelpers'),
  mocks: require('./mockFactories'),
  render: require('./renderUtils'),
  api: require('./apiMocks'),
  fixtures: require('./fixtures'),
  matchers: require('./customMatchers'),
  
  // Enhanced utilities
  config: require('./testConfig'),
  runner: require('./testRunner'),
  
  // Integration utilities
  environment: require('../integration/testEnvironment'),
  apiIntegration: require('../integration/apiIntegration'),
  componentIntegration: require('../integration/componentIntegration'),
  e2e: require('../integration/e2eHelpers'),
};

/**
 * Quick setup function for common test scenarios
 */
export const setupTest = (type: 'unit' | 'integration' | 'e2e' = 'unit') => {
  const config = getTestConfig(type);
  const runner = createTestRunner(config);
  
  return {
    config,
    runner,
    utils: testUtils,
    factories: testDataFactories,
    assertions: testAssertions,
  };
};

/**
 * Default export with most commonly used utilities
 */
export default {
  // Most commonly used functions
  render: renderWithAllProviders,
  createTestRunner,
  setupTest,
  testUtils,
  testDataFactories,
  testAssertions,
  
  // Quick access to utilities
  TestUtilities,
};