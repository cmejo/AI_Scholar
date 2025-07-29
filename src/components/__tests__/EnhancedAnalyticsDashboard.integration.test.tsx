import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
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

Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
  value: vi.fn(() => mockCanvasContext)
});

describe('EnhancedAnalyticsDashboard Integration', () => {
  const mockData = {
    queries: [
      { id: '1', query: 'test', userId: 'user1', timestamp: new Date(), responseTime: 1000, satisfaction: 0.8, intent: 'search', documentsUsed: ['doc1'], success: true }
    ],
    documents: [{ id: 'doc1', name: 'Document 1' }],
    users: [{ id: 'user1', name: 'User 1' }]
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    (analyticsService.getDashboardData as any).mockReturnValue(mockData);
    (analyticsService.getQueryInsights as any).mockReturnValue({
      mostCommonQueries: [{ query: 'test', count: 5 }],
      averageResponseTime: 1000,
      successRate: 0.95,
      topIntents: [{ intent: 'search', count: 10 }],
      satisfactionScore: 0.85
    });
    (analyticsService.getDocumentInsights as any).mockReturnValue({
      mostReferencedDocuments: [{ documentId: 'doc1', references: 15 }],
      leastUsedDocuments: [],
      documentEffectiveness: []
    });
    (analyticsService.getUserInsights as any).mockReturnValue({
      activeUsers: 25,
      averageSessionLength: 15.5,
      userRetention: 0.75,
      topUsers: []
    });
    (analyticsService.identifyKnowledgeGaps as any).mockReturnValue({
      unansweredQueries: [{ query: 'unanswered', frequency: 5 }],
      lowSatisfactionTopics: [],
      missingDocumentTypes: []
    });
  });

  it('renders dashboard successfully', async () => {
    render(<EnhancedAnalyticsDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Enhanced Analytics Dashboard')).toBeInTheDocument();
    });
  });

  it('displays real-time metrics section', async () => {
    render(<EnhancedAnalyticsDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Real-time Metrics')).toBeInTheDocument();
    });
  });

  it('shows navigation tabs', async () => {
    render(<EnhancedAnalyticsDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Overview')).toBeInTheDocument();
    });
  });

  it('displays metric cards with data', async () => {
    render(<EnhancedAnalyticsDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Total Queries')).toBeInTheDocument();
      expect(screen.getByText('Success Rate')).toBeInTheDocument();
    });
  });

  it('handles export functionality', async () => {
    const mockOnExport = vi.fn();
    render(<EnhancedAnalyticsDashboard onExport={mockOnExport} />);
    
    await waitFor(() => {
      const exportButton = screen.getByText('Export');
      expect(exportButton).toBeInTheDocument();
    });
  });

  it('renders without crashing when data is null', async () => {
    (analyticsService.getQueryInsights as any).mockReturnValue(null);
    (analyticsService.getDocumentInsights as any).mockReturnValue(null);
    (analyticsService.getUserInsights as any).mockReturnValue(null);
    (analyticsService.identifyKnowledgeGaps as any).mockReturnValue(null);
    
    render(<EnhancedAnalyticsDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Enhanced Analytics Dashboard')).toBeInTheDocument();
    });
  });

  it('displays loading state initially', () => {
    // Mock a slow loading response
    (analyticsService.getDashboardData as any).mockImplementation(() => {
      return new Promise(resolve => setTimeout(() => resolve(mockData), 100));
    });
    
    render(<EnhancedAnalyticsDashboard />);
    
    // Should show loading spinner
    expect(document.querySelector('.animate-spin')).toBeInTheDocument();
  });
});