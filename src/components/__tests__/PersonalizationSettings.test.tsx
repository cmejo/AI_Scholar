import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import PersonalizationSettings from '../PersonalizationSettings';

// Mock the personalization service
const mockPersonalizationService = {
  getUserPreferences: vi.fn(),
  updateUserPreferences: vi.fn(),
  getDomainExpertise: vi.fn(),
  getPersonalizationStats: vi.fn(),
  getFeedbackHistory: vi.fn(),
  getLearningInsights: vi.fn(),
};

vi.mock('../../services/personalizationService', () => ({
  personalizationService: mockPersonalizationService,
  default: mockPersonalizationService,
}));

// Mock fetch for API calls
global.fetch = vi.fn();

const mockUserPreferences = {
  theme: 'dark' as const,
  language: 'en',
  defaultModel: 'mistral',
  responseLength: 'detailed' as const,
  enableVoice: false,
  enableNotifications: true,
  responseStyle: 'balanced' as const,
  citationPreference: 'inline' as const,
  reasoningDisplay: true,
  uncertaintyTolerance: 0.5,
  domainAdaptation: true,
  enableAdaptiveRetrieval: true,
};

const mockDomainExpertise = {
  technology: 0.8,
  science: 0.6,
  business: 0.4,
};

const mockPersonalizationStats = {
  totalSearches: 150,
  personalizedSearches: 120,
  personalizationRate: 0.8,
  topDomains: {
    technology: 45,
    science: 30,
    business: 25,
  },
  avgResultsPerSearch: 8.5,
  avgSatisfaction: 0.85,
  satisfactionTrend: 'improving' as const,
  periodDays: 30,
};

const mockFeedbackHistory = [
  {
    id: '1',
    timestamp: '2024-01-15T10:00:00Z',
    feedbackType: 'rating',
    rating: 4,
    comment: 'Very helpful response',
    processed: true,
    messageId: 'msg-1',
  },
  {
    id: '2',
    timestamp: '2024-01-14T15:30:00Z',
    feedbackType: 'correction',
    comment: 'Minor factual error in the response',
    processed: false,
    messageId: 'msg-2',
  },
];

const mockLearningInsights = {
  totalQueries: 200,
  favoriteTopics: ['machine learning', 'web development', 'data science'],
  averageSessionLength: 25.5,
  preferredResponseStyle: 'detailed',
  learningProgress: [
    {
      month: '2024-01',
      queries: 50,
      uniqueTopics: 8,
      engagement: 85,
    },
    {
      month: '2023-12',
      queries: 45,
      uniqueTopics: 6,
      engagement: 78,
    },
  ],
};

describe('PersonalizationSettings', () => {
  const mockUserId = 'test-user-123';
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default fetch responses
    (fetch as any).mockImplementation((url: string, options?: any) => {
      if (url.includes('/preferences')) {
        if (options?.method === 'PUT') {
          return Promise.resolve({ ok: true });
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockUserPreferences),
        });
      }
      if (url.includes('/domain-expertise')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockDomainExpertise),
        });
      }
      if (url.includes('/personalization-stats')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockPersonalizationStats),
        });
      }
      if (url.includes('/feedback-history')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockFeedbackHistory),
        });
      }
      if (url.includes('/learning-insights')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockLearningInsights),
        });
      }
      return Promise.resolve({
        ok: false,
        statusText: 'Not Found',
      });
    });
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('renders the personalization settings modal', async () => {
    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    await waitFor(() => {
      expect(screen.getByText('Personalization Settings')).toBeInTheDocument();
    });
    
    // Check that all tabs are present
    expect(screen.getByText('Preferences')).toBeInTheDocument();
    expect(screen.getByText('Domain Adaptation')).toBeInTheDocument();
    expect(screen.getByText('Feedback History')).toBeInTheDocument();
    expect(screen.getByText('Learning Insights')).toBeInTheDocument();
  });

  it('loads and displays user preferences', async () => {
    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('dark')).toBeInTheDocument();
      expect(screen.getByDisplayValue('en')).toBeInTheDocument();
      expect(screen.getByDisplayValue('mistral')).toBeInTheDocument();
      expect(screen.getByDisplayValue('detailed')).toBeInTheDocument();
    });
  });

  it('allows updating basic preferences', async () => {
    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('dark')).toBeInTheDocument();
    });

    // Change theme
    const themeSelect = screen.getByDisplayValue('dark');
    fireEvent.change(themeSelect, { target: { value: 'light' } });
    
    expect(themeSelect).toHaveValue('light');
  });

  it('allows updating response preferences', async () => {
    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('balanced')).toBeInTheDocument();
    });

    // Change response style
    const responseStyleSelect = screen.getByDisplayValue('balanced');
    fireEvent.change(responseStyleSelect, { target: { value: 'technical' } });
    
    expect(responseStyleSelect).toHaveValue('technical');
  });

  it('allows adjusting uncertainty tolerance slider', async () => {
    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    await waitFor(() => {
      const slider = screen.getByRole('slider');
      expect(slider).toBeInTheDocument();
      expect(slider).toHaveValue('0.5');
    });

    const slider = screen.getByRole('slider');
    fireEvent.change(slider, { target: { value: '0.8' } });
    
    expect(slider).toHaveValue('0.8');
  });

  it('allows toggling personalization features', async () => {
    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    await waitFor(() => {
      expect(screen.getByText('Personalization Settings')).toBeInTheDocument();
    });

    // Wait for data to load and expand personalization section
    await waitFor(() => {
      const personalizationHeader = screen.getByText('Personalization Features');
      fireEvent.click(personalizationHeader);
    });

    await waitFor(() => {
      const domainAdaptationToggle = screen.getByLabelText(/domain adaptation/i);
      expect(domainAdaptationToggle).toBeInTheDocument();
    });
  });

  it('saves preferences when save button is clicked', async () => {
    (fetch as any).mockImplementation((url: string, options: any) => {
      if (options?.method === 'PUT' && url.includes('/preferences')) {
        return Promise.resolve({ ok: true });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockUserPreferences),
      });
    });

    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    await waitFor(() => {
      expect(screen.getByText('Save Preferences')).toBeInTheDocument();
    });

    const saveButton = screen.getByText('Save Preferences');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        `/api/users/${mockUserId}/preferences`,
        expect.objectContaining({
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: expect.any(String),
        })
      );
    });
  });

  it('displays domain expertise in domains tab', async () => {
    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    // Switch to domains tab
    const domainsTab = screen.getByText('Domain Adaptation');
    fireEvent.click(domainsTab);

    await waitFor(() => {
      expect(screen.getByText('Domain Expertise')).toBeInTheDocument();
      expect(screen.getByText('technology', { selector: '.capitalize' })).toBeInTheDocument();
      expect(screen.getByText('80%')).toBeInTheDocument();
      expect(screen.getByText('science', { selector: '.capitalize' })).toBeInTheDocument();
      expect(screen.getByText('60%')).toBeInTheDocument();
    });
  });

  it('displays personalization effectiveness metrics', async () => {
    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    // Switch to domains tab
    const domainsTab = screen.getByText('Domain Adaptation');
    fireEvent.click(domainsTab);

    await waitFor(() => {
      expect(screen.getByText('Personalization Effectiveness')).toBeInTheDocument();
      expect(screen.getByText('80%')).toBeInTheDocument(); // Personalization rate
      expect(screen.getByText('150')).toBeInTheDocument(); // Total searches
      expect(screen.getByText('8.5')).toBeInTheDocument(); // Avg results
      expect(screen.getByText('85%')).toBeInTheDocument(); // Satisfaction
    });
  });

  it('displays feedback history in feedback tab', async () => {
    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    // Switch to feedback tab
    const feedbackTab = screen.getByText('Feedback History');
    fireEvent.click(feedbackTab);

    await waitFor(() => {
      expect(screen.getByText('Feedback History')).toBeInTheDocument();
      expect(screen.getByText('rating')).toBeInTheDocument();
      expect(screen.getByText('4/5')).toBeInTheDocument();
      expect(screen.getByText('Very helpful response')).toBeInTheDocument();
      expect(screen.getByText('Processed')).toBeInTheDocument();
      expect(screen.getByText('Pending')).toBeInTheDocument();
    });
  });

  it('displays learning insights in insights tab', async () => {
    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    // Switch to insights tab
    const insightsTab = screen.getByText('Learning Insights');
    fireEvent.click(insightsTab);

    await waitFor(() => {
      expect(screen.getByText('Learning Insights')).toBeInTheDocument();
      expect(screen.getByText('200')).toBeInTheDocument(); // Total queries
      expect(screen.getByText('3')).toBeInTheDocument(); // Favorite topics count
      expect(screen.getByText('26m')).toBeInTheDocument(); // Avg session length
      expect(screen.getByText('detailed')).toBeInTheDocument(); // Response style
    });
  });

  it('displays favorite topics', async () => {
    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    // Switch to insights tab
    const insightsTab = screen.getByText('Learning Insights');
    fireEvent.click(insightsTab);

    await waitFor(() => {
      expect(screen.getByText('machine learning')).toBeInTheDocument();
      expect(screen.getByText('web development')).toBeInTheDocument();
      expect(screen.getByText('data science')).toBeInTheDocument();
    });
  });

  it('displays learning progress', async () => {
    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    // Switch to insights tab
    const insightsTab = screen.getByText('Learning Insights');
    fireEvent.click(insightsTab);

    await waitFor(() => {
      expect(screen.getByText('Learning Progress')).toBeInTheDocument();
      expect(screen.getByText('2024-01')).toBeInTheDocument();
      expect(screen.getByText('50 queries, 8 topics')).toBeInTheDocument();
      expect(screen.getByText('2023-12')).toBeInTheDocument();
      expect(screen.getByText('45 queries, 6 topics')).toBeInTheDocument();
    });
  });

  it('handles expandable sections', async () => {
    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    await waitFor(() => {
      expect(screen.getByText('Basic Preferences')).toBeInTheDocument();
    });

    // Basic preferences should be expanded by default
    expect(screen.getByDisplayValue('dark')).toBeInTheDocument();

    // Click to collapse
    const basicPreferencesHeader = screen.getByText('Basic Preferences');
    fireEvent.click(basicPreferencesHeader);

    // Should still be visible (this is just UI behavior)
    expect(screen.getByDisplayValue('dark')).toBeInTheDocument();
  });

  it('handles loading state', () => {
    // Mock fetch to never resolve to simulate loading
    (fetch as any).mockImplementation(() => new Promise(() => {}));

    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    expect(screen.getByText('Loading personalization settings...')).toBeInTheDocument();
  });

  it('handles empty domain expertise', async () => {
    (fetch as any).mockImplementation((url: string) => {
      if (url.includes('/domain-expertise')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({}),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockUserPreferences),
      });
    });

    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    // Switch to domains tab
    const domainsTab = screen.getByText('Domain Adaptation');
    fireEvent.click(domainsTab);

    await waitFor(() => {
      expect(screen.getByText('No domain expertise detected yet.')).toBeInTheDocument();
      expect(screen.getByText('Continue using the system to build your domain profile.')).toBeInTheDocument();
    });
  });

  it('handles empty feedback history', async () => {
    (fetch as any).mockImplementation((url: string) => {
      if (url.includes('/feedback-history')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([]),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockUserPreferences),
      });
    });

    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    // Switch to feedback tab
    const feedbackTab = screen.getByText('Feedback History');
    fireEvent.click(feedbackTab);

    await waitFor(() => {
      expect(screen.getByText('No feedback history available.')).toBeInTheDocument();
      expect(screen.getByText('Start providing feedback to help improve your experience.')).toBeInTheDocument();
    });
  });

  it('handles empty learning progress', async () => {
    const emptyInsights = {
      ...mockLearningInsights,
      learningProgress: [],
    };

    (fetch as any).mockImplementation((url: string) => {
      if (url.includes('/learning-insights')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(emptyInsights),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockUserPreferences),
      });
    });

    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    // Switch to insights tab
    const insightsTab = screen.getByText('Learning Insights');
    fireEvent.click(insightsTab);

    await waitFor(() => {
      expect(screen.getByText('Not enough data for progress tracking.')).toBeInTheDocument();
      expect(screen.getByText('Continue using the system to see your learning progress.')).toBeInTheDocument();
    });
  });

  it('calls onClose when close button is clicked', async () => {
    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    await waitFor(() => {
      expect(screen.getByText('×')).toBeInTheDocument();
    });

    const closeButton = screen.getByText('×');
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('handles API errors gracefully', async () => {
    (fetch as any).mockImplementation(() => {
      return Promise.resolve({
        ok: false,
        statusText: 'Internal Server Error',
      });
    });

    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    // Should still render with default values
    await waitFor(() => {
      expect(screen.getByText('Personalization Settings')).toBeInTheDocument();
    });
  });

  it('shows saving state when saving preferences', async () => {
    let resolveSave: (value: any) => void;
    const savePromise = new Promise((resolve) => {
      resolveSave = resolve;
    });

    (fetch as any).mockImplementation((url: string, options: any) => {
      if (options?.method === 'PUT' && url.includes('/preferences')) {
        return savePromise;
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockUserPreferences),
      });
    });

    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    await waitFor(() => {
      expect(screen.getByText('Save Preferences')).toBeInTheDocument();
    });

    const saveButton = screen.getByText('Save Preferences');
    fireEvent.click(saveButton);

    // Should show saving state
    expect(screen.getByText('Saving...')).toBeInTheDocument();

    // Resolve the save
    resolveSave!({ ok: true });

    await waitFor(() => {
      expect(screen.getByText('Save Preferences')).toBeInTheDocument();
    });
  });

  it('handles reset functionality', async () => {
    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    await waitFor(() => {
      expect(screen.getByText('Reset')).toBeInTheDocument();
    });

    const resetButton = screen.getByText('Reset');
    fireEvent.click(resetButton);

    // Should reload data
    expect(fetch).toHaveBeenCalledWith(`/api/users/${mockUserId}/preferences`);
  });
});