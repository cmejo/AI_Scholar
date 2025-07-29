import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import { MemoryAwareChatInterface } from '../MemoryAwareChatInterface';
import { EnhancedChatProvider } from '../../contexts/EnhancedChatContext';
import { DocumentProvider } from '../../contexts/DocumentContext';

// Mock the services with simpler implementations
vi.mock('../../services/memoryService', () => ({
  memoryService: {
    addMemory: vi.fn().mockResolvedValue(undefined),
    getMemories: vi.fn().mockResolvedValue([]),
  }
}));

vi.mock('../../services/userProfileService', () => ({
  userProfileService: {
    getUserProfile: vi.fn().mockResolvedValue({
      id: 'test-user',
      preferences: {
        responseStyle: 'detailed',
        domainExpertise: ['technology'],
        preferredSources: []
      }
    })
  }
}));

vi.mock('../../utils/contextAwareRetrieval', () => ({
  contextAwareRetriever: {
    retrieve: vi.fn().mockResolvedValue({
      results: [],
      queryAnalysis: {
        intent: { type: 'question', confidence: 0.9 },
        relatedEntities: []
      }
    })
  }
}));

vi.mock('../../utils/chainOfThought', () => ({
  chainOfThoughtReasoner: {
    processQuery: vi.fn().mockResolvedValue({
      totalSteps: 3,
      overallConfidence: 0.85,
      executionTime: 1200,
      metadata: {
        queryComplexity: 'medium',
        reasoningStrategy: 'analytical'
      }
    })
  }
}));

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <DocumentProvider>
    <EnhancedChatProvider>
      {children}
    </EnhancedChatProvider>
  </DocumentProvider>
);

describe('MemoryAwareChatInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders memory-aware chat interface', () => {
    render(
      <TestWrapper>
        <MemoryAwareChatInterface />
      </TestWrapper>
    );

    expect(screen.getByText('Memory-Aware Chat')).toBeInTheDocument();
  });

  test('displays feature toggle buttons', () => {
    render(
      <TestWrapper>
        <MemoryAwareChatInterface />
      </TestWrapper>
    );

    expect(screen.getByText('Memory ON')).toBeInTheDocument();
    expect(screen.getByText('Uncertainty ON')).toBeInTheDocument();
    expect(screen.getByText('Reasoning ON')).toBeInTheDocument();
    expect(screen.getByText('Feedback ON')).toBeInTheDocument();
  });

  test('toggles memory awareness feature', () => {
    render(
      <TestWrapper>
        <MemoryAwareChatInterface />
      </TestWrapper>
    );

    const memoryButton = screen.getByText('Memory ON');
    fireEvent.click(memoryButton);
    
    expect(screen.getByText('Memory OFF')).toBeInTheDocument();
  });

  test('displays empty state with feature indicators', () => {
    render(
      <TestWrapper>
        <MemoryAwareChatInterface />
      </TestWrapper>
    );

    expect(screen.getByText('Memory-Aware Assistant')).toBeInTheDocument();
    expect(screen.getByText('Memory Context')).toBeInTheDocument();
    expect(screen.getByText('Uncertainty Tracking')).toBeInTheDocument();
    expect(screen.getByText('Reasoning Steps')).toBeInTheDocument();
    expect(screen.getByText('Feedback Learning')).toBeInTheDocument();
  });
});