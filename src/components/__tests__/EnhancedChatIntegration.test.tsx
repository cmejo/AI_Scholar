/**
 * Comprehensive integration tests for enhanced chat components.
 * Tests component interactions and complete user workflows.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryAwareChatInterface } from '../MemoryAwareChatInterface';
import { EnhancedAnalyticsDashboard } from '../EnhancedAnalyticsDashboard';
import { PersonalizationSettings } from '../PersonalizationSettings';
import { EnhancedChatContext } from '../../contexts/EnhancedChatContext';

// Mock API responses
const mockApiResponses = {
  chatQuery: {
    response: 'This is a test response about machine learning.',
    sources: [
      {
        content: 'Machine learning is a subset of AI',
        metadata: { source: 'test.pdf', page: 1 },
        score: 0.95
      }
    ],
    confidence_score: 0.85,
    reasoning_steps: [
      'Analyzed query for intent',
      'Retrieved relevant documents',
      'Generated response based on context'
    ],
    memory_context: {
      previous_queries: ['What is AI?'],
      user_preferences: { complexity: 'intermediate' }
    }
  },
  analytics: {
    query_count: 15,
    average_response_time: 2.3,
    user_satisfaction: 4.2,
    popular_topics: ['machine learning', 'AI', 'neural networks'],
    usage_trends: [
      { date: '2024-01-01', queries: 5 },
      { date: '2024-01-02', queries: 8 },
      { date: '2024-01-03', queries: 12 }
    ]
  },
  userProfile: {
    preferences: {
      complexity: 'intermediate',
      domain: 'machine_learning',
      explanation_style: 'detailed'
    },
    expertise_level: 0.7,
    interaction_history: [
      { query: 'What is AI?', timestamp: '2024-01-01T10:00:00Z' },
      { query: 'Explain neural networks', timestamp: '2024-01-01T10:05:00Z' }
    ]
  }
};

// Mock context provider
const MockEnhancedChatProvider = ({ children }: { children: React.ReactNode }) => {
  const mockContextValue = {
    messages: [
      {
        id: '1',
        content: 'What is machine learning?',
        role: 'user' as const,
        timestamp: new Date('2024-01-01T10:00:00Z')
      },
      {
        id: '2',
        content: 'Machine learning is a subset of artificial intelligence...',
        role: 'assistant' as const,
        timestamp: new Date('2024-01-01T10:00:30Z'),
        sources: mockApiResponses.chatQuery.sources,
        confidence_score: 0.85,
        reasoning_steps: mockApiResponses.chatQuery.reasoning_steps
      }
    ],
    isLoading: false,
    error: null,
    sendMessage: vi.fn().mockResolvedValue(mockApiResponses.chatQuery),
    clearMessages: vi.fn(),
    regenerateResponse: vi.fn(),
    provideFeedback: vi.fn(),
    conversationId: 'test-conversation-123',
    memoryContext: mockApiResponses.chatQuery.memory_context,
    userProfile: mockApiResponses.userProfile,
    updateUserProfile: vi.fn(),
    analytics: mockApiResponses.analytics
  };

  return (
    <EnhancedChatContext.Provider value={mockContextValue}>
      {children}
    </EnhancedChatContext.Provider>
  );
};

describe('Enhanced Chat Integration Tests', () => {
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    user = userEvent.setup();
    
    // Mock fetch globally
    global.fetch = vi.fn();
    
    // Setup default fetch responses
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/chat/query')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.chatQuery)
        });
      }
      if (url.includes('/api/analytics')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.analytics)
        });
      }
      if (url.includes('/api/user/profile')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.userProfile)
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({})
      });
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Memory-Aware Chat Interface Integration', () => {
    it('should display conversation with memory context', async () => {
      render(
        <MockEnhancedChatProvider>
          <MemoryAwareChatInterface />
        </MockEnhancedChatProvider>
      );

      // Check that messages are displayed
      expect(screen.getByText('What is machine learning?')).toBeInTheDocument();
      expect(screen.getByText(/Machine learning is a subset of artificial intelligence/)).toBeInTheDocument();

      // Check that memory context is shown
      expect(screen.getByText(/Previous context/i)).toBeInTheDocument();
      expect(screen.getByText(/What is AI\?/)).toBeInTheDocument();
    });

    it('should send message and update conversation', async () => {
      const mockSendMessage = vi.fn().mockResolvedValue(mockApiResponses.chatQuery);
      
      render(
        <MockEnhancedChatProvider>
          <MemoryAwareChatInterface />
        </MockEnhancedChatProvider>
      );

      // Find and interact with message input
      const messageInput = screen.getByPlaceholderText(/Type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      // Type and send message
      await user.type(messageInput, 'Explain neural networks');
      await user.click(sendButton);

      // Wait for response
      await waitFor(() => {
        expect(screen.getByText('Explain neural networks')).toBeInTheDocument();
      });
    });

    it('should display confidence scores and reasoning steps', async () => {
      render(
        <MockEnhancedChatProvider>
          <MemoryAwareChatInterface />
        </MockEnhancedChatProvider>
      );

      // Check confidence score display
      expect(screen.getByText(/Confidence: 85%/i)).toBeInTheDocument();

      // Check reasoning steps
      expect(screen.getByText(/Reasoning Steps/i)).toBeInTheDocument();
      expect(screen.getByText('Analyzed query for intent')).toBeInTheDocument();
      expect(screen.getByText('Retrieved relevant documents')).toBeInTheDocument();
    });

    it('should handle feedback submission', async () => {
      const mockProvideFeedback = vi.fn();
      
      render(
        <MockEnhancedChatProvider>
          <MemoryAwareChatInterface />
        </MockEnhancedChatProvider>
      );

      // Find feedback buttons
      const thumbsUpButton = screen.getByRole('button', { name: /thumbs up/i });
      
      await user.click(thumbsUpButton);

      // Verify feedback was submitted
      await waitFor(() => {
        expect(thumbsUpButton).toHaveClass('text-green-600');
      });
    });

    it('should display sources with proper formatting', async () => {
      render(
        <MockEnhancedChatProvider>
          <MemoryAwareChatInterface />
        </MockEnhancedChatProvider>
      );

      // Check sources section
      expect(screen.getByText(/Sources/i)).toBeInTheDocument();
      expect(screen.getByText('test.pdf')).toBeInTheDocument();
      expect(screen.getByText('Page 1')).toBeInTheDocument();
      expect(screen.getByText(/Score: 95%/i)).toBeInTheDocument();
    });
  });

  describe('Analytics Dashboard Integration', () => {
    it('should display analytics data correctly', async () => {
      render(
        <MockEnhancedChatProvider>
          <EnhancedAnalyticsDashboard />
        </MockEnhancedChatProvider>
      );

      // Wait for analytics to load
      await waitFor(() => {
        expect(screen.getByText('15')).toBeInTheDocument(); // Query count
        expect(screen.getByText('2.3s')).toBeInTheDocument(); // Average response time
        expect(screen.getByText('4.2')).toBeInTheDocument(); // User satisfaction
      });
    });

    it('should display usage trends chart', async () => {
      render(
        <MockEnhancedChatProvider>
          <EnhancedAnalyticsDashboard />
        </MockEnhancedChatProvider>
      );

      // Check for chart elements
      await waitFor(() => {
        expect(screen.getByText(/Usage Trends/i)).toBeInTheDocument();
      });

      // Check for trend data points
      expect(screen.getByText('Jan 1')).toBeInTheDocument();
      expect(screen.getByText('Jan 2')).toBeInTheDocument();
      expect(screen.getByText('Jan 3')).toBeInTheDocument();
    });

    it('should display popular topics', async () => {
      render(
        <MockEnhancedChatProvider>
          <EnhancedAnalyticsDashboard />
        </MockEnhancedChatProvider>
      );

      // Check popular topics
      await waitFor(() => {
        expect(screen.getByText('machine learning')).toBeInTheDocument();
        expect(screen.getByText('AI')).toBeInTheDocument();
        expect(screen.getByText('neural networks')).toBeInTheDocument();
      });
    });

    it('should handle time range selection', async () => {
      render(
        <MockEnhancedChatProvider>
          <EnhancedAnalyticsDashboard />
        </MockEnhancedChatProvider>
      );

      // Find time range selector
      const timeRangeSelect = screen.getByRole('combobox', { name: /time range/i });
      
      await user.selectOptions(timeRangeSelect, '7d');

      // Verify API call with new time range
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('time_range=7d'),
          expect.any(Object)
        );
      });
    });
  });

  describe('Personalization Settings Integration', () => {
    it('should display current user preferences', async () => {
      render(
        <MockEnhancedChatProvider>
          <PersonalizationSettings />
        </MockEnhancedChatProvider>
      );

      // Check current preferences
      await waitFor(() => {
        expect(screen.getByDisplayValue('intermediate')).toBeInTheDocument();
        expect(screen.getByDisplayValue('machine_learning')).toBeInTheDocument();
        expect(screen.getByDisplayValue('detailed')).toBeInTheDocument();
      });
    });

    it('should update preferences when changed', async () => {
      const mockUpdateProfile = vi.fn();
      
      render(
        <MockEnhancedChatProvider>
          <PersonalizationSettings />
        </MockEnhancedChatProvider>
      );

      // Find complexity selector
      const complexitySelect = screen.getByRole('combobox', { name: /complexity/i });
      
      await user.selectOptions(complexitySelect, 'advanced');

      // Find save button and click
      const saveButton = screen.getByRole('button', { name: /save preferences/i });
      await user.click(saveButton);

      // Verify preferences were updated
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/user/profile'),
          expect.objectContaining({
            method: 'PUT',
            body: expect.stringContaining('advanced')
          })
        );
      });
    });

    it('should display expertise level indicator', async () => {
      render(
        <MockEnhancedChatProvider>
          <PersonalizationSettings />
        </MockEnhancedChatProvider>
      );

      // Check expertise level display
      await waitFor(() => {
        expect(screen.getByText(/Expertise Level: 70%/i)).toBeInTheDocument();
      });
    });

    it('should show interaction history', async () => {
      render(
        <MockEnhancedChatProvider>
          <PersonalizationSettings />
        </MockEnhancedChatProvider>
      );

      // Check interaction history
      await waitFor(() => {
        expect(screen.getByText(/Recent Interactions/i)).toBeInTheDocument();
        expect(screen.getByText('What is AI?')).toBeInTheDocument();
        expect(screen.getByText('Explain neural networks')).toBeInTheDocument();
      });
    });
  });

  describe('Cross-Component Integration', () => {
    it('should update analytics when chat messages are sent', async () => {
      render(
        <MockEnhancedChatProvider>
          <div>
            <MemoryAwareChatInterface />
            <EnhancedAnalyticsDashboard />
          </div>
        </MockEnhancedChatProvider>
      );

      // Send a message
      const messageInput = screen.getByPlaceholderText(/Type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      await user.type(messageInput, 'Test integration message');
      await user.click(sendButton);

      // Wait for analytics to update
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/analytics'),
          expect.any(Object)
        );
      });
    });

    it('should apply personalization settings to chat responses', async () => {
      render(
        <MockEnhancedChatProvider>
          <div>
            <PersonalizationSettings />
            <MemoryAwareChatInterface />
          </div>
        </MockEnhancedChatProvider>
      );

      // Change complexity setting
      const complexitySelect = screen.getByRole('combobox', { name: /complexity/i });
      await user.selectOptions(complexitySelect, 'advanced');

      const saveButton = screen.getByRole('button', { name: /save preferences/i });
      await user.click(saveButton);

      // Send a message
      const messageInput = screen.getByPlaceholderText(/Type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      await user.type(messageInput, 'Explain quantum computing');
      await user.click(sendButton);

      // Verify personalization was applied in the request
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/chat/query'),
          expect.objectContaining({
            body: expect.stringContaining('advanced')
          })
        );
      });
    });

    it('should show memory context in chat based on previous interactions', async () => {
      render(
        <MockEnhancedChatProvider>
          <MemoryAwareChatInterface />
        </MockEnhancedChatProvider>
      );

      // Check that memory context is displayed
      expect(screen.getByText(/Previous context/i)).toBeInTheDocument();
      expect(screen.getByText(/User preferences/i)).toBeInTheDocument();
      expect(screen.getByText(/intermediate/i)).toBeInTheDocument();
    });
  });

  describe('Error Handling Integration', () => {
    it('should handle API errors gracefully', async () => {
      // Mock API error
      (global.fetch as any).mockImplementationOnce(() =>
        Promise.resolve({
          ok: false,
          status: 500,
          json: () => Promise.resolve({ error: 'Internal server error' })
        })
      );

      render(
        <MockEnhancedChatProvider>
          <MemoryAwareChatInterface />
        </MockEnhancedChatProvider>
      );

      const messageInput = screen.getByPlaceholderText(/Type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      await user.type(messageInput, 'This will cause an error');
      await user.click(sendButton);

      // Check error message is displayed
      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
      });
    });

    it('should handle network errors', async () => {
      // Mock network error
      (global.fetch as any).mockImplementationOnce(() =>
        Promise.reject(new Error('Network error'))
      );

      render(
        <MockEnhancedChatProvider>
          <MemoryAwareChatInterface />
        </MockEnhancedChatProvider>
      );

      const messageInput = screen.getByPlaceholderText(/Type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      await user.type(messageInput, 'This will cause a network error');
      await user.click(sendButton);

      // Check error handling
      await waitFor(() => {
        expect(screen.getByText(/network/i) || screen.getByText(/error/i)).toBeInTheDocument();
      });
    });

    it('should show loading states during API calls', async () => {
      // Mock slow API response
      (global.fetch as any).mockImplementationOnce(() =>
        new Promise(resolve => 
          setTimeout(() => resolve({
            ok: true,
            json: () => Promise.resolve(mockApiResponses.chatQuery)
          }), 1000)
        )
      );

      render(
        <MockEnhancedChatProvider>
          <MemoryAwareChatInterface />
        </MockEnhancedChatProvider>
      );

      const messageInput = screen.getByPlaceholderText(/Type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      await user.type(messageInput, 'Slow response test');
      await user.click(sendButton);

      // Check loading state
      expect(screen.getByText(/sending/i) || screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });

  describe('Accessibility Integration', () => {
    it('should be keyboard navigable', async () => {
      render(
        <MockEnhancedChatProvider>
          <MemoryAwareChatInterface />
        </MockEnhancedChatProvider>
      );

      const messageInput = screen.getByPlaceholderText(/Type your message/i);
      
      // Focus input with keyboard
      messageInput.focus();
      expect(messageInput).toHaveFocus();

      // Navigate to send button with Tab
      await user.keyboard('{Tab}');
      const sendButton = screen.getByRole('button', { name: /send/i });
      expect(sendButton).toHaveFocus();

      // Activate with Enter
      await user.keyboard('{Enter}');
      // Should trigger send action
    });

    it('should have proper ARIA labels', () => {
      render(
        <MockEnhancedChatProvider>
          <MemoryAwareChatInterface />
        </MockEnhancedChatProvider>
      );

      // Check ARIA labels
      expect(screen.getByRole('textbox', { name: /message input/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send message/i })).toBeInTheDocument();
      expect(screen.getByRole('region', { name: /chat messages/i })).toBeInTheDocument();
    });

    it('should announce new messages to screen readers', async () => {
      render(
        <MockEnhancedChatProvider>
          <MemoryAwareChatInterface />
        </MockEnhancedChatProvider>
      );

      // Check for live region
      expect(screen.getByRole('log')).toBeInTheDocument();
    });
  });
});