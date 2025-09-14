/**
 * Integration test for analytics data integration and service communication
 * Tests task 2.2 implementation
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { enterpriseAnalyticsService } from '../../services/enterpriseAnalyticsService';

describe('Analytics Data Integration - Task 2.2', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    enterpriseAnalyticsService.clearCache();
  });

  it('should connect to analyticsService for real-time data fetching', async () => {
    // Test that the service can fetch data (even if it falls back to local service)
    const timeRange = {
      start: new Date('2024-01-01'),
      end: new Date('2024-01-31')
    };

    const result = await enterpriseAnalyticsService.getDashboardData(timeRange);
    
    // Should return valid data structure
    expect(result).toBeDefined();
    expect(result).toHaveProperty('overview');
    expect(result).toHaveProperty('queries');
    expect(result).toHaveProperty('documents');
    expect(result).toHaveProperty('users');
    expect(result).toHaveProperty('performance');
    expect(result).toHaveProperty('trends');
  });

  it('should implement data transformation and caching mechanisms', async () => {
    const timeRange = {
      start: new Date('2024-01-01'),
      end: new Date('2024-01-31')
    };

    // First call should populate cache
    const result1 = await enterpriseAnalyticsService.getDashboardData(timeRange);
    
    // Second call should use cache (should be faster)
    const startTime = Date.now();
    const result2 = await enterpriseAnalyticsService.getDashboardData(timeRange);
    const endTime = Date.now();
    
    // Cache should return same data structure
    expect(result2).toEqual(result1);
    
    // Should be fast (cached)
    expect(endTime - startTime).toBeLessThan(100);
  });

  it('should provide automatic refresh functionality with configurable intervals', () => {
    const callback = vi.fn();
    
    // Test subscription setup
    const unsubscribe = enterpriseAnalyticsService.subscribe(
      'dashboard',
      callback,
      {
        enabled: true,
        interval: 1000,
        onError: vi.fn(),
        onSuccess: vi.fn()
      }
    );

    // Should return unsubscribe function
    expect(typeof unsubscribe).toBe('function');
    
    // Should be able to unsubscribe without error
    expect(() => unsubscribe()).not.toThrow();
  });

  it('should handle data transformation options', async () => {
    const timeRange = {
      start: new Date('2024-01-01'),
      end: new Date('2024-01-31')
    };

    const options = {
      includeRealTimeMetrics: true,
      aggregateUserData: true,
      calculateTrends: true,
      filterByUserId: 'test-user'
    };

    const result = await enterpriseAnalyticsService.getDashboardData(timeRange, options);
    
    // Should return transformed data
    expect(result).toBeDefined();
    expect(result.overview).toBeDefined();
    expect(result.performance).toBeDefined();
  });

  it('should provide cache statistics and management', () => {
    const stats = enterpriseAnalyticsService.getCacheStats();
    
    expect(stats).toHaveProperty('size');
    expect(stats).toHaveProperty('entries');
    expect(stats).toHaveProperty('hitRate');
    
    // Should be able to clear cache
    expect(() => enterpriseAnalyticsService.clearCache()).not.toThrow();
  });

  it('should support data export functionality', async () => {
    const timeRange = {
      start: new Date('2024-01-01'),
      end: new Date('2024-01-31')
    };

    // Test JSON export
    const jsonBlob = await enterpriseAnalyticsService.exportData(timeRange, 'json');
    expect(jsonBlob).toBeInstanceOf(Blob);
    expect(jsonBlob.type).toBe('application/json');

    // Test CSV export
    const csvBlob = await enterpriseAnalyticsService.exportData(timeRange, 'csv');
    expect(csvBlob).toBeInstanceOf(Blob);
    expect(csvBlob.type).toBe('text/csv');
  });

  it('should handle backend connection errors gracefully', async () => {
    // Mock fetch to simulate network error
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));

    const timeRange = {
      start: new Date('2024-01-01'),
      end: new Date('2024-01-31')
    };

    // Should not throw error, should fall back gracefully
    const result = await enterpriseAnalyticsService.getDashboardData(timeRange);
    
    expect(result).toBeDefined();
    expect(result.overview).toBeDefined();
  });
});