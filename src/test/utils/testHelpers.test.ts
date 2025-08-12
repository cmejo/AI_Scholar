/**
 * Test file for enhanced test utilities
 */

import { describe, expect, it } from 'vitest';
import {
    createControllablePromise,
    createMockFile,
    createTestEnvironment,
    mockConsole,
    mockDateNow,
    mockTypedAPIResponse,
    waitForCondition
} from './testHelpers';

describe('Enhanced Test Helpers', () => {
  describe('waitForCondition', () => {
    it('should wait for condition to be true', async () => {
      let condition = false;
      setTimeout(() => { condition = true; }, 100);

      await waitForCondition(() => condition, 1000, 50);
      expect(condition).toBe(true);
    });

    it('should timeout if condition is never met', async () => {
      await expect(
        waitForCondition(() => false, 100, 10)
      ).rejects.toThrow('Condition not met within 100ms');
    });
  });

  describe('createMockFile', () => {
    it('should create a mock file with correct properties', () => {
      const file = createMockFile('test.txt', 'test content', 'text/plain');
      
      expect(file.name).toBe('test.txt');
      expect(file.type).toBe('text/plain');
      expect(file.size).toBeGreaterThan(0);
    });
  });

  describe('mockConsole', () => {
    it('should mock console methods and capture calls', () => {
      const { mocks, restore } = mockConsole();
      
      console.log('test message');
      console.error('test error');
      
      expect(mocks.log).toHaveBeenCalledWith('test message');
      expect(mocks.error).toHaveBeenCalledWith('test error');
      
      restore();
    });
  });

  describe('mockDateNow', () => {
    it('should mock Date.now() with fixed timestamp', () => {
      const fixedTime = 1234567890000;
      const { restore, advance } = mockDateNow(fixedTime);
      
      expect(Date.now()).toBe(fixedTime);
      
      advance(1000);
      expect(Date.now()).toBe(fixedTime + 1000);
      
      restore();
    });
  });

  describe('createControllablePromise', () => {
    it('should create a promise that can be resolved externally', async () => {
      const { promise, resolve } = createControllablePromise<string>();
      
      setTimeout(() => resolve('test result'), 10);
      
      const result = await promise;
      expect(result).toBe('test result');
    });

    it('should create a promise that can be rejected externally', async () => {
      const { promise, reject } = createControllablePromise<string>();
      
      setTimeout(() => reject(new Error('test error')), 10);
      
      await expect(promise).rejects.toThrow('test error');
    });
  });

  describe('mockTypedAPIResponse', () => {
    it('should create a typed API response mock', async () => {
      const mockData = { id: '1', message: 'test' };
      const mockFetch = mockTypedAPIResponse('/api/test', mockData, {
        status: 200,
        delay: 0,
      });

      global.fetch = mockFetch;

      const response = await fetch('/api/test');
      const data = await response.json();

      expect(response.ok).toBe(true);
      expect(response.status).toBe(200);
      expect(data).toEqual(mockData);
    });
  });

  describe('createTestEnvironment', () => {
    it('should create a comprehensive test environment', () => {
      const { mocks, cleanup } = createTestEnvironment({
        mockAPIs: true,
        mockStorage: true,
        mockWebAPIs: true,
        mockMediaDevices: true,
        mockNotifications: true,
      });

      expect(mocks.fetch).toBeDefined();
      expect(mocks.localStorage).toBeDefined();
      expect(mocks.sessionStorage).toBeDefined();
      expect(mocks.intersectionObserver).toBeDefined();
      expect(mocks.resizeObserver).toBeDefined();
      expect(mocks.mediaDevices).toBeDefined();
      expect(mocks.notification).toBeDefined();

      cleanup();
    });
  });
});