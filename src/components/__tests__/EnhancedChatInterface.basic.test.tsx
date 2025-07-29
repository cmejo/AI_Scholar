import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { EnhancedChatInterface } from '../EnhancedChatInterface';

// Mock the contexts
vi.mock('../../contexts/EnhancedChatContext', () => ({
  useEnhancedChat: () => ({
    conversations: [],
    currentConversation: null,
    createNewConversation: vi.fn(),
    switchConversation: vi.fn(),
    sendMessage: vi.fn(),
    deleteConversation: vi.fn(),
  })
}));

vi.mock('../../contexts/DocumentContext', () => ({
  useDocument: () => ({
    documents: [
      { id: '1', name: 'test-doc.pdf', type: 'pdf', content: 'Test content' }
    ],
    uploadDocument: vi.fn(),
    deleteDocument: vi.fn(),
    isUploading: false
  })
}));

// Mock the child components
vi.mock('../UncertaintyVisualization', () => ({
  UncertaintyVisualization: ({ uncertainty, isExpanded, onToggle }: any) => (
    <div data-testid="uncertainty-visualization">
      <button onClick={onToggle}>
        Confidence: {(uncertainty.confidence * 100).toFixed(0)}%
      </button>
    </div>
  )
}));

vi.mock('../ReasoningStepsDisplay', () => ({
  ReasoningStepsDisplay: ({ reasoning, isExpanded, onToggle }: any) => (
    <div data-testid="reasoning-steps">
      <button onClick={onToggle}>
        Chain of Thought ({reasoning.steps.length} steps)
      </button>
    </div>
  )
}));

vi.mock('../FeedbackCollector', () => ({
  FeedbackCollector: ({ messageId, onFeedback }: any) => (
    <div data-testid="feedback-collector">
      <button onClick={() => onFeedback(messageId, { rating: 5, helpful: true })}>
        Was this helpful?
      </button>
    </div>
  )
}));

describe('EnhancedChatInterface - Basic Functionality', () => {
  it('renders the enhanced chat interface', () => {
    render(<EnhancedChatInterface />);
    
    expect(screen.getByText('Enhanced Memory-Aware Chat')).toBeInTheDocument();
    expect(screen.getByText('Context-aware conversations with reasoning transparency and feedback learning')).toBeInTheDocument();
  });

  it('displays feature toggle buttons', () => {
    render(<EnhancedChatInterface />);
    
    expect(screen.getByText('Memory ON')).toBeInTheDocument();
    expect(screen.getByText('Uncertainty ON')).toBeInTheDocument();
    expect(screen.getByText('Reasoning ON')).toBeInTheDocument();
    expect(screen.getByText('Feedback ON')).toBeInTheDocument();
  });

  it('shows welcome message when no messages exist', () => {
    render(<EnhancedChatInterface />);
    
    expect(screen.getByText('Enhanced Memory-Aware Assistant')).toBeInTheDocument();
    expect(screen.getByText(/I remember our conversations/)).toBeInTheDocument();
  });

  it('displays input field and send button', () => {
    render(<EnhancedChatInterface />);
    
    expect(screen.getByPlaceholderText(/Ask me anything - I'll remember our conversation/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send message/i })).toBeInTheDocument();
  });

  it('shows document count when documents are available', () => {
    render(<EnhancedChatInterface />);
    
    expect(screen.getByText('✓ 1 documents loaded and ready')).toBeInTheDocument();
  });

  it('displays memory counter in header', () => {
    render(<EnhancedChatInterface />);
    
    expect(screen.getByText(/Memory: 0\/10 short-term, 0 long-term/)).toBeInTheDocument();
  });
});