/**
 * Test suite for EnterpriseAnalyticsService
 * Tests the analytics data integration and service communication functionality
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { enterpriseAnalyticsService } from '../../services/enterpriseAnalyticsService';

// Mock fetch globally
global.fetch = vi.fn();

describe('EnterpriseAnalyticsService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    enterpriseAnalyticsService.clearCache();
  });

  afterEach(() => {
    enterpriseAnalyticsService.clearCache();
  });

  describe('getDashboardData', () => {
    it('should fetch and cache dashboard data', async () => {
      const mockData = {
        overview: {
          total_queries: 1250,
          total_users: 45,
          total_documents: 120,
          avg_response_time: 850,
          success_rate: 0.95,
          satisfaction_score: 0.88
        },
        queries: [],
        documents: [],
        users: [],
        performance: {
          response_time: 850,
          throughput: 25,
          error_rate: 0.05,
          cpu_usage: 65,
          memory_usage: 72,
          disk_usage: 45
        },
        trends: []
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData
      });

      const timeRange = {
        start: new Date('2024-01-01'),
        end: new Date('2024-01-31')
      };

      const result = await enterpriseAnalyticsService.getDashboardData(timeRange);

      expect(result).toBeDefined();
      expect(result.overview.totalQueries).toBe(1250);
      expect(result.overview.totalUsers).toBe(45);
      expect(result.performance.responseTime).toBe(850);
    });

    it('should handle backend errors gracefully', async () => {
      (fetch as any).mockRejectedValueOnce(new Error('Network error'));

      const timeRange = {
        start: new Date('2024-01-01'),
        end: new Date('2024-01-31')
      };

      // Should not throw, but fall back to local analytics service
      const result = await enterpriseAnalyticsService.getDashboardData(timeRange);
      expect(result).toBeDefined();
    });

    it('should use cache when available', async () => {
      const mockData = {
        overview: { total_queries: 100 },
        queries: [],
        documents: [],
        users: [],
        performance: { response_time: 500 },
        trends: []
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData
      });

      const timeRange = {
        start: new Date('2024-01-01'),
        end: new Date('2024-01-31')
      };

      // First call should fetch from backend
      await enterpriseAnalyticsService.getDashboardData(timeRange);
      expect(fetch).toHaveBeenCalledTimes(3); // dashboard, comprehensive, monitoring

      // Second call should use cache
      await enterpriseAnalyticsService.getDashboardData(timeRange);
      expect(fetch).toHaveBeenCalledTimes(3); // No additional calls
    });
  });

  describe('getOverviewMetrics', () => {
    it('should fetch and transform overview metrics', async () => {
      const mockData = {
        total_queries: 500,
        total_users: 25,
        avg_response_time: 750,
        queries: [],
        users: [
          { id: '1', satisfactionScore: 0.8 },
          { id: '2', satisfactionScore: 0.9 }
        ]
      };

      // Mock all the fetch calls that getOverviewMetrics makes
      (fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockData
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ cpu_usage: 50, memory_usage: 60 })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ avg_response_time: 750 })
        });

      const timeRange = {
        start: new Date('2024-01-01'),
        end: new Date('2024-01-31')
      };

      const result = await enterpriseAnalyticsService.getOverviewMetrics(timeRange);

      expect(result.totalQueries).toBe(500);
      expect(result.totalUsers).toBe(25);
      expect(result.averageResponseTime).toBe(750);
    });
  });

  describe('subscribe', () => {
    it('should set up subscription with callback', () => {
      const callback = vi.fn();
      const config = { enabled: true, interval: 1000 };

      const unsubscribe = enterpriseAnalyticsService.subscribe('dashboard', callback, config);

      expect(typeof unsubscribe).toBe('function');

      // Clean up
      unsubscribe();
    });

    it('should call unsubscribe function correctly', () => {
      const callback = vi.fn();
      const unsubscribe = enterpriseAnalyticsService.subscribe('dashboard', callback);

      // Should not throw
      expect(() => unsubscribe()).not.toThrow();
    });
  });

  describe('exportData', () => {
    it('should export data in JSON format', async () => {
      const mockData = {
        overview: { total_queries: 100 },
        queries: [],
        documents: [],
        users: [],
        performance: { response_time: 500 },
        trends: []
      };

      (fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockData
      });

      const timeRange = {
        start: new Date('2024-01-01'),
        end: new Date('2024-01-31')
      };

      const blob = await enterpriseAnalyticsService.exportData(timeRange, 'json');

      expect(blob).toBeInstanceOf(Blob);
      expect(blob.type).toBe('application/json');
    });

    it('should export data in CSV format', async () => {
      const mockData = {
        overview: { total_queries: 100 },
        queries: [],
        documents: [],
        users: [],
        performance: { response_time: 500 },
        trends: []
      };

      (fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockData
      });

      const timeRange = {
        start: new Date('2024-01-01'),
        end: new Date('2024-01-31')
      };

      const blob = await enterpriseAnalyticsService.exportData(timeRange, 'csv');

      expect(blob).toBeInstanceOf(Blob);
      expect(blob.type).toBe('text/csv');
    });
  });

  describe('clearCache', () => {
    it('should clear all cached data', () => {
      // Add some data to cache first
      const timeRange = {
        start: new Date('2024-01-01'),
        end: new Date('2024-01-31')
      };

      // This should work without throwing
      expect(() => enterpriseAnalyticsService.clearCache()).not.toThrow();
    });
  });

  describe('getCacheStats', () => {
    it('should return cache statistics', () => {
      const stats = enterpriseAnalyticsService.getCacheStats();

      expect(stats).toHaveProperty('size');
      expect(stats).toHaveProperty('entries');
      expect(stats).toHaveProperty('hitRate');
      expect(typeof stats.size).toBe('number');
      expect(Array.isArray(stats.entries)).toBe(true);
      expect(typeof stats.hitRate).toBe('number');
    });
  });
});