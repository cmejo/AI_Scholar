import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { EnhancedAnalyticsDashboard } from '../EnhancedAnalyticsDashboard';
import { analyticsService } from '../../services/analyticsService';

// Mock the analytics service
vi.mock('../../services/analyticsService', () => ({
  analyticsService: {
    getDashboardData: vi.fn(),
    getQueryInsights: vi.fn(),
    getDocumentInsights: vi.fn(),
    getUserInsights: vi.fn(),
    identifyKnowledgeGaps: vi.fn()
  }
}));

// Mock canvas context
const mockCanvasContext = {
  clearRect: vi.fn(),
  fillRect: vi.fn(),
  strokeRect: vi.fn(),
  beginPath: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  arc: vi.fn(),
  closePath: vi.fn(),
  fill: vi.fn(),
  stroke: vi.fn(),
  fillText: vi.fn(),
  measureText: vi.fn(() => ({ width: 100 })),
  save: vi.fn(),
  restore: vi.fn(),
  scale: vi.fn(),
  translate: vi.fn(),
  rotate: vi.fn(),
  setTransform: vi.fn(),
  transform: vi.fn()
};

// Mock HTMLCanvasElement
Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
  value: vi.fn(() => mockCanvasContext)
});

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}));

describe('EnhancedAnalyticsDashboard', () => {
  const mockAnalyticsData = {
    queries: [
      { id: '1', query: 'test query', userId: 'user1', timestamp: new Date(), responseTime: 1000, satisfaction: 0.8, intent: 'search', documentsUsed: ['doc1'], success: true },
      { id: '2', query: 'another query', userId: 'user2', timestamp: new Date(), responseTime: 1500, satisfaction: 0.9, intent: 'question', documentsUsed: ['doc2'], success: true }
    ],
    documents: [
      { id: 'doc1', name: 'Document 1', type: 'pdf' },
      { id: 'doc2', name: 'Document 2', type: 'text' }
    ],
    users: [
      { id: 'user1', name: 'User 1' },
      { id: 'user2', name: 'User 2' }
    ]
  };

  const mockQueryInsights = {
    mostCommonQueries: [
      { query: 'test query', count: 5 },
      { query: 'another query', count: 3 }
    ],
    averageResponseTime: 1250,
    successRate: 0.95,
    topIntents: [
      { intent: 'search', count: 10 },
      { intent: 'question', count: 8 }
    ],
    satisfactionScore: 0.85
  };

  const mockDocumentInsights = {
    mostReferencedDocuments: [
      { documentId: 'doc1', references: 15 },
      { documentId: 'doc2', references: 10 }
    ],
    leastUsedDocuments: [
      { documentId: 'doc3', lastUsed: new Date() }
    ],
    documentEffectiveness: [
      { documentId: 'doc1', effectiveness: 0.9 }
    ]
  };

  const mockUserInsights = {
    activeUsers: 25,
    averageSessionLength: 15.5,
    userRetention: 0.75,
    topUsers: [
      { userId: 'user1', queryCount: 20 }
    ]
  };

  const mockKnowledgeGaps = {
    unansweredQueries: [
      { query: 'unanswered query', frequency: 5 }
    ],
    lowSatisfactionTopics: [
      { topic: 'complex topic', avgSatisfaction: 0.3 }
    ],
    missingDocumentTypes: ['api-docs']
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    (analyticsService.getDashboardData as any).mockReturnValue(mockAnalyticsData);
    (analyticsService.getQueryInsights as any).mockReturnValue(mockQueryInsights);
    (analyticsService.getDocumentInsights as any).mockReturnValue(mockDocumentInsights);
    (analyticsService.getUserInsights as any).mockReturnValue(mockUserInsights);
    (analyticsService.identifyKnowledgeGaps as any).mockReturnValue(mockKnowledgeGaps);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders dashboard header correctly', async () => {
    render(<EnhancedAnalyticsDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Enhanced Analytics Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Comprehensive insights and real-time monitoring')).toBeInTheDocument();
    });
  });

  it('displays real-time metrics', async () => {
    render(<EnhancedAnalyticsDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Real-time Metrics')).toBeInTheDocument();
      expect(screen.getByText('Active Users')).toBeInTheDocument();
      expect(screen.getByText('Queries/Min')).toBeInTheDocument();
      expect(screen.getByText('Avg Response')).toBeInTheDocument();
    });
  });

  it('shows navigation tabs', async () => {
    render(<EnhancedAnalyticsDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Overview')).toBeInTheDocument();
      expect(screen.getByText('Queries')).toBeInTheDocument();
      expect(screen.getByText('Documents')).toBeInTheDocument();
      expect(screen.getByText('Users')).toBeInTheDocument();
      expect(screen.getByText('Knowledge Graph')).toBeInTheDocument();
      expect(screen.getByText('Performance')).toBeInTheDocument();
    });
  });

  it('switches between different dashboard views', async () => {
    render(<EnhancedAnalyticsDashboard />);
    
    await waitFor(() => {
      // Default should be overview
      expect(screen.getByText('Total Queries')).toBeInTheDocument();
    });

    // Click on Queries tab
    fireEvent.click(screen.getByText('Queries'));
    
    await waitFor(() => {
      expect(screen.getByText('Most Common Queries')).toBeInTheDocument();
    });

    // Click on Documents tab
    fireEvent.click(screen.getByText('Documents'));
    
    await waitFor(() => {
      expect(screen.getByText('Document Usage Heatmap')).toBeInTheDocument();
    });
  });

  it('displays key metrics cards', async () => {
    render(<EnhancedAnalyticsDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Total Queries')).toBeInTheDocument();
      expect(screen.getByText('Success Rate')).toBeInTheDocument();
      expect(screen.getByText('Avg Response Time')).toBeInTheDocument();
      expect(screen.getByText('Active Users')).toBeInTheDocument();
    });
  });

  it('handles time range selection', async () => {
    render(<EnhancedAnalyticsDashboard />);
    
    const timeRangeSelect = screen.getByDisplayValue('Last 7 Days');
    fireEvent.change(timeRangeSelect, { target: { value: '24h' } });
    
    await waitFor(() => {
      expect(analyticsService.getDashboardData).toHaveBeenCalled();
    });
  });

  it('toggles auto refresh', async () => {
    render(<EnhancedAnalyticsDashboard />);
    
    const autoRefreshButton = screen.getByText('Auto Refresh');
    fireEvent.click(autoRefreshButton);
    
    // Should toggle the auto refresh state
    expect(autoRefreshButton).toBeInTheDocument();
  });

  it('exports analytics data', async () => {
    const mockOnExport = vi.fn();
    render(<EnhancedAnalyticsDashboard onExport={mockOnExport} />);
    
    await waitFor(() => {
      const exportButton = screen.getByText('Export');
      fireEvent.click(exportButton);
      
      expect(mockOnExport).toHaveBeenCalledWith(
        expect.objectContaining({
          analytics: mockAnalyticsData,
          timeRange: '7d'
        })
      );
    });
  });

  it('displays query insights correctly', async () => {
    render(<EnhancedAnalyticsDashboard />);
    
    // Switch to queries tab
    fireEvent.click(screen.getByText('Queries'));
    
    await waitFor(() => {
      expect(screen.getByText('95.0%')).toBeInTheDocument(); // Success rate
      expect(screen.getByText('1250ms')).toBeInTheDocument(); // Avg response time
    });
  });

  it('displays document insights correctly', async () => {
    render(<EnhancedAnalyticsDashboard />);
    
    // Switch to documents tab
    fireEvent.click(screen.getByText('Documents'));
    
    await waitFor(() => {
      expect(screen.getByText('Document Usage Heatmap')).toBeInTheDocument();
      expect(screen.getByText('Document Type Distribution')).toBeInTheDocument();
    });
  });

  it('displays user behavior metrics', async () => {
    render(<EnhancedAnalyticsDashboard />);
    
    // Switch to users tab
    fireEvent.click(screen.getByText('Users'));
    
    await waitFor(() => {
      expect(screen.getByText('25')).toBeInTheDocument(); // Active users
      expect(screen.getByText('15.5m')).toBeInTheDocument(); // Avg session length
      expect(screen.getByText('75.0%')).toBeInTheDocument(); // Retention rate
    });
  });

  it('displays knowledge graph visualization', async () => {
    render(<EnhancedAnalyticsDashboard />);
    
    // Switch to knowledge graph tab
    fireEvent.click(screen.getByText('Knowledge Graph'));
    
    await waitFor(() => {
      expect(screen.getByText('Knowledge Graph Overview')).toBeInTheDocument();
      expect(screen.getByText('Most Connected Entities')).toBeInTheDocument();
    });
  });

  it('displays performance metrics', async () => {
    render(<EnhancedAnalyticsDashboard />);
    
    // Switch to performance tab
    fireEvent.click(screen.getByText('Performance'));
    
    await waitFor(() => {
      expect(screen.getByText('Response Time Trend')).toBeInTheDocument();
      expect(screen.getByText('System Resources')).toBeInTheDocument();
      expect(screen.getByText('Performance Alerts')).toBeInTheDocument();
    });
  });

  it('handles loading state', () => {
    // Mock loading state
    (analyticsService.getDashboardData as any).mockImplementation(() => {
      return new Promise(resolve => setTimeout(resolve, 1000));
    });
    
    render(<EnhancedAnalyticsDashboard />);
    
    expect(screen.getByRole('status')).toBeInTheDocument(); // Loading spinner
  });

  it('handles error states gracefully', async () => {
    // Mock error
    (analyticsService.getDashboardData as any).mockImplementation(() => {
      throw new Error('Analytics service error');
    });
    
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    render(<EnhancedAnalyticsDashboard />);
    
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Failed to load analytics:', expect.any(Error));
    });
    
    consoleSpy.mockRestore();
  });

  it('updates metrics with user ID filter', async () => {
    const userId = 'test-user-123';
    render(<EnhancedAnalyticsDashboard userId={userId} />);
    
    await waitFor(() => {
      expect(analyticsService.getDashboardData).toHaveBeenCalled();
    });
  });

  it('respects custom time range', async () => {
    const customTimeRange = {
      start: new Date('2023-01-01'),
      end: new Date('2023-01-31')
    };
    
    render(<EnhancedAnalyticsDashboard timeRange={customTimeRange} />);
    
    await waitFor(() => {
      expect(analyticsService.getDashboardData).toHaveBeenCalledWith(customTimeRange);
    });
  });

  it('renders charts without errors', async () => {
    render(<EnhancedAnalyticsDashboard />);
    
    await waitFor(() => {
      // Check that canvas elements are rendered
      const canvases = document.querySelectorAll('canvas');
      expect(canvases.length).toBeGreaterThan(0);
    });
  });

  it('displays knowledge gaps correctly', async () => {
    render(<EnhancedAnalyticsDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Knowledge Gaps')).toBeInTheDocument();
      expect(screen.getByText('unanswered query')).toBeInTheDocument();
    });
  });

  it('shows most referenced documents', async () => {
    render(<EnhancedAnalyticsDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Most Referenced Documents')).toBeInTheDocument();
      expect(screen.getByText('doc1')).toBeInTheDocument();
      expect(screen.getByText('15')).toBeInTheDocument();
    });
  });
});