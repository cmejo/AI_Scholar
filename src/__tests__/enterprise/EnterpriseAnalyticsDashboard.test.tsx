/**
 * EnterpriseAnalyticsDashboard Component Tests
 * Tests for task 2.1: Create EnterpriseAnalyticsDashboard component with layout and navigation
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { EnterpriseAnalyticsDashboard } from '../../components/enterprise/EnterpriseAnalyticsDashboard';
import { enterpriseAnalyticsService } from '../../services/enterpriseAnalyticsService';
import { AnalyticsDashboardData } from '../../types/ui';

// Mock the enterprise analytics service
vi.mock('../../services/enterpriseAnalyticsService', () => ({
  enterpriseAnalyticsService: {
    getDashboardData: vi.fn(),
    subscribe: vi.fn(),
    exportData: vi.fn(),
    clearCache: vi.fn(),
    getCacheStats: vi.fn(() => ({ size: 5, entries: [], hitRate: 0.85 }))
  }
}));

// Mock the analytics components
vi.mock('../../components/enterprise/analytics', () => ({
  AnalyticsOverview: ({ metrics, loading, timeRange }: any) => (
    <div data-testid="analytics-overview">
      Analytics Overview - {timeRange} - Loading: {loading ? 'true' : 'false'}
    </div>
  ),
  UsageMetrics: ({ timeRange }: any) => (
    <div data-testid="usage-metrics">Usage Metrics - {timeRange}</div>
  ),
  PerformanceCharts: ({ timeRange }: any) => (
    <div data-testid="performance-charts">Performance Charts - {timeRange}</div>
  ),
  UserBehaviorAnalytics: ({ timeRange }: any) => (
    <div data-testid="user-behavior-analytics">User Behavior Analytics - {timeRange}</div>
  )
}));

const mockDashboardData: AnalyticsDashboardData = {
  overview: {
    totalQueries: 1250,
    totalUsers: 45,
    totalDocuments: 320,
    averageResponseTime: 850,
    successRate: 0.96,
    satisfactionScore: 0.82
  },
  queries: [
    {
      id: 'q1',
      query: 'test query',
      count: 10,
      averageResponseTime: 500,
      successRate: 0.95,
      timestamp: new Date()
    }
  ],
  documents: [
    {
      id: 'd1',
      name: 'test document',
      accessCount: 5,
      lastAccessed: new Date(),
      relevanceScore: 0.9
    }
  ],
  users: [
    {
      id: 'u1',
      name: 'Test User',
      queryCount: 15,
      lastActive: new Date(),
      satisfactionScore: 0.85
    }
  ],
  performance: {
    responseTime: 850,
    throughput: 100,
    errorRate: 0.04,
    cpuUsage: 65,
    memoryUsage: 70,
    diskUsage: 45
  },
  trends: [
    {
      metric: 'queries',
      period: 'day',
      data: [
        { timestamp: new Date(), value: 100 },
        { timestamp: new Date(), value: 120 }
      ],
      change: 20,
      direction: 'up'
    }
  ]
};

describe('EnterpriseAnalyticsDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (enterpriseAnalyticsService.getDashboardData as any).mockResolvedValue(mockDashboardData);
    (enterpriseAnalyticsService.subscribe as any).mockReturnValue(() => {});
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should render the dashboard with header and controls', async () => {
    render(<EnterpriseAnalyticsDashboard />);

    // Check header
    expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Comprehensive analytics and insights for your enterprise system')).toBeInTheDocument();

    // Check time range selector
    expect(screen.getByDisplayValue('Last 24 Hours')).toBeInTheDocument();

    // Check refresh button
    expect(screen.getByText('Refresh')).toBeInTheDocument();

    // Check export button
    expect(screen.getByText('Export')).toBeInTheDocument();
  });

  it('should display overview metrics correctly', async () => {
    render(<EnterpriseAnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Total Queries')).toBeInTheDocument();
      expect(screen.getByText('1,250')).toBeInTheDocument();
      
      expect(screen.getByText('Active Users')).toBeInTheDocument();
      expect(screen.getByText('45')).toBeInTheDocument();
      
      expect(screen.getByText('Avg Response Time')).toBeInTheDocument();
      expect(screen.getByText('850ms')).toBeInTheDocument();
      
      expect(screen.getByText('Success Rate')).toBeInTheDocument();
      expect(screen.getByText('96.0%')).toBeInTheDocument();
    });
  });

  it('should handle time range changes', async () => {
    const onTimeRangeChange = vi.fn();
    render(<EnterpriseAnalyticsDashboard onTimeRangeChange={onTimeRangeChange} />);

    const timeRangeSelect = screen.getByDisplayValue('Last 24 Hours');
    fireEvent.change(timeRangeSelect, { target: { value: '7d' } });

    expect(onTimeRangeChange).toHaveBeenCalledWith('7d');
  });

  it('should handle manual refresh', async () => {
    render(<EnterpriseAnalyticsDashboard />);

    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(enterpriseAnalyticsService.getDashboardData).toHaveBeenCalledTimes(2); // Initial load + manual refresh
    });
  });

  it('should toggle auto-refresh', async () => {
    render(<EnterpriseAnalyticsDashboard />);

    const autoRefreshCheckbox = screen.getByLabelText('Auto-refresh');
    expect(autoRefreshCheckbox).toBeChecked();

    fireEvent.click(autoRefreshCheckbox);
    expect(autoRefreshCheckbox).not.toBeChecked();
  });

  it('should handle export functionality', async () => {
    const mockBlob = new Blob(['test data'], { type: 'application/json' });
    (enterpriseAnalyticsService.exportData as any).mockResolvedValue(mockBlob);

    // Mock URL.createObjectURL and related functions
    const mockCreateObjectURL = vi.fn(() => 'mock-url');
    const mockRevokeObjectURL = vi.fn();
    global.URL.createObjectURL = mockCreateObjectURL;
    global.URL.revokeObjectURL = mockRevokeObjectURL;

    // Mock document.createElement and appendChild
    const mockLink = {
      href: '',
      download: '',
      click: vi.fn()
    };
    const mockCreateElement = vi.fn(() => mockLink);
    const mockAppendChild = vi.fn();
    const mockRemoveChild = vi.fn();
    
    document.createElement = mockCreateElement;
    document.body.appendChild = mockAppendChild;
    document.body.removeChild = mockRemoveChild;

    render(<EnterpriseAnalyticsDashboard />);

    const exportButton = screen.getByText('Export');
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(enterpriseAnalyticsService.exportData).toHaveBeenCalled();
    });
  });

  it('should display loading states', () => {
    (enterpriseAnalyticsService.getDashboardData as any).mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve(mockDashboardData), 1000))
    );

    render(<EnterpriseAnalyticsDashboard />);

    // Should show loading spinners in metric cards
    expect(screen.getAllByText('Refresh').length).toBeGreaterThan(0);
  });

  it('should handle errors gracefully', async () => {
    const error = new Error('Analytics service unavailable');
    (enterpriseAnalyticsService.getDashboardData as any).mockRejectedValue(error);

    render(<EnterpriseAnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Analytics service unavailable/)).toBeInTheDocument();
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
  });

  it('should render analytics components when data is loaded', async () => {
    render(<EnterpriseAnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByTestId('analytics-overview')).toBeInTheDocument();
      expect(screen.getByTestId('usage-metrics')).toBeInTheDocument();
      expect(screen.getByTestId('performance-charts')).toBeInTheDocument();
      expect(screen.getByTestId('user-behavior-analytics')).toBeInTheDocument();
    });
  });

  it('should filter data by userId when provided', async () => {
    const userId = 'test-user-123';
    render(<EnterpriseAnalyticsDashboard userId={userId} />);

    await waitFor(() => {
      expect(enterpriseAnalyticsService.getDashboardData).toHaveBeenCalledWith(
        expect.any(Object),
        expect.objectContaining({
          filterByUserId: userId
        })
      );
    });
  });

  it('should display cache statistics', async () => {
    render(<EnterpriseAnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Cache: 5 entries/)).toBeInTheDocument();
      expect(screen.getByText(/Auto-refresh: On/)).toBeInTheDocument();
    });
  });

  it('should show empty state when no data is available', async () => {
    (enterpriseAnalyticsService.getDashboardData as any).mockResolvedValue(null);

    render(<EnterpriseAnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByText('No Analytics Data')).toBeInTheDocument();
      expect(screen.getByText('No analytics data available for the selected time range.')).toBeInTheDocument();
    });
  });

  it('should cleanup subscriptions on unmount', () => {
    const unsubscribe = vi.fn();
    (enterpriseAnalyticsService.subscribe as any).mockReturnValue(unsubscribe);

    const { unmount } = render(<EnterpriseAnalyticsDashboard />);
    
    unmount();

    expect(enterpriseAnalyticsService.clearCache).toHaveBeenCalled();
  });
});