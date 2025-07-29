import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import PersonalizationSettings from '../PersonalizationSettings';

// Mock fetch
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

describe('PersonalizationSettings Integration', () => {
  const mockUserId = 'test-user-123';
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup successful fetch responses
    (fetch as any).mockImplementation((url: string, options?: any) => {
      if (options?.method === 'PUT') {
        return Promise.resolve({ ok: true });
      }
      
      return Promise.resolve({
        ok: true,
        json: () => {
          if (url.includes('/preferences')) {
            return Promise.resolve(mockUserPreferences);
          }
          if (url.includes('/domain-expertise')) {
            return Promise.resolve({ technology: 0.8, science: 0.6 });
          }
          if (url.includes('/personalization-stats')) {
            return Promise.resolve({
              totalSearches: 150,
              personalizedSearches: 120,
              personalizationRate: 0.8,
              topDomains: { technology: 45, science: 30 },
              avgResultsPerSearch: 8.5,
              avgSatisfaction: 0.85,
              periodDays: 30,
            });
          }
          if (url.includes('/feedback-history')) {
            return Promise.resolve([
              {
                id: '1',
                timestamp: '2024-01-15T10:00:00Z',
                feedbackType: 'rating',
                rating: 4,
                processed: true,
              }
            ]);
          }
          if (url.includes('/learning-insights')) {
            return Promise.resolve({
              totalQueries: 200,
              favoriteTopics: ['machine learning', 'web development'],
              averageSessionLength: 25.5,
              preferredResponseStyle: 'detailed',
              learningProgress: [
                { month: '2024-01', queries: 50, uniqueTopics: 8, engagement: 85 }
              ],
            });
          }
          return Promise.resolve({});
        },
      });
    });
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('renders and loads personalization settings', async () => {
    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    // Should show loading initially
    expect(screen.getByText('Loading personalization settings...')).toBeInTheDocument();
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Personalization Settings')).toBeInTheDocument();
      expect(screen.queryByText('Loading personalization settings...')).not.toBeInTheDocument();
    });
    
    // Check that tabs are present
    expect(screen.getByText('Preferences')).toBeInTheDocument();
    expect(screen.getByText('Domain Adaptation')).toBeInTheDocument();
    expect(screen.getByText('Feedback History')).toBeInTheDocument();
    expect(screen.getByText('Learning Insights')).toBeInTheDocument();
  });

  it('displays user preferences correctly', async () => {
    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('dark')).toBeInTheDocument();
      expect(screen.getByDisplayValue('en')).toBeInTheDocument();
      expect(screen.getByDisplayValue('mistral')).toBeInTheDocument();
      expect(screen.getByDisplayValue('detailed')).toBeInTheDocument();
    });
  });

  it('allows changing preferences and saving', async () => {
    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('dark')).toBeInTheDocument();
    });

    // Change theme
    const themeSelect = screen.getByDisplayValue('dark');
    fireEvent.change(themeSelect, { target: { value: 'light' } });
    expect(themeSelect).toHaveValue('light');

    // Save preferences
    const saveButton = screen.getByText('Save Preferences');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        `/api/users/${mockUserId}/preferences`,
        expect.objectContaining({
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
        })
      );
    });
  });

  it('switches between tabs correctly', async () => {
    render(<PersonalizationSettings userId={mockUserId} onClose={mockOnClose} />);
    
    await waitFor(() => {
      expect(screen.getByText('Personalization Settings')).toBeInTheDocument();
    });

    // Switch to domains tab
    const domainsTab = screen.getByText('Domain Adaptation');
    fireEvent.click(domainsTab);

    await waitFor(() => {
      expect(screen.getByText('Domain Expertise')).toBeInTheDocument();
    });

    // Switch to feedback tab
    const feedbackTab = screen.getByText('Feedback History');
    fireEvent.click(feedbackTab);

    await waitFor(() => {
      expect(screen.getByText('Feedback History')).toBeInTheDocument();
    });

    // Switch to insights tab
    const insightsTab = screen.getByText('Learning Insights');
    fireEvent.click(insightsTab);

    await waitFor(() => {
      expect(screen.getByText('Learning Insights')).toBeInTheDocument();
    });
  });

  it('handles close button click', async () => {
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
    
    // Should still render with default values after error
    await waitFor(() => {
      expect(screen.getByText('Personalization Settings')).toBeInTheDocument();
    });
  });

  it('shows saving state when saving preferences', async () => {
    let resolveSave: (value: any) => void;
    const savePromise = new Promise((resolve) => {
      resolveSave = resolve;
    });

    (fetch as any).mockImplementation((url: string, options?: any) => {
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
});