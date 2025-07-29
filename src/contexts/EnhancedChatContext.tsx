import React, { createContext, useContext, useState, useCallback } from 'react';
import { ContextualResponse } from '../utils/contextAwareRetrieval';
import { ChainOfThoughtResponse } from '../utils/chainOfThought';

export interface EnhancedMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Array<{
    document: string;
    page: number;
    relevance: number;
    explanation?: string;
  }>;
  insights?: string[];
  queryAnalysis?: {
    intent: string;
    confidence: number;
    entities: string[];
    strategy: string;
  };
  explanation?: string;
  chainOfThought?: ChainOfThoughtResponse;
}

export interface EnhancedConversation {
  id: string;
  title: string;
  messages: EnhancedMessage[];
  createdAt: Date;
  updatedAt: Date;
  totalQueries: number;
  avgRelevanceScore: number;
  avgReasoningSteps: number;
  avgConfidence: number;
}

interface EnhancedChatContextType {
  conversations: EnhancedConversation[];
  currentConversation: EnhancedConversation | null;
  createNewConversation: () => void;
  switchConversation: (id: string) => void;
  sendMessage: (content: string, retrievalResponse?: ContextualResponse, chainOfThought?: ChainOfThoughtResponse) => Promise<void>;
  deleteConversation: (id: string) => void;
}

const EnhancedChatContext = createContext<EnhancedChatContextType | undefined>(undefined);

export const useEnhancedChat = () => {
  const context = useContext(EnhancedChatContext);
  if (!context) {
    throw new Error('useEnhancedChat must be used within an EnhancedChatProvider');
  }
  return context;
};

export const EnhancedChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [conversations, setConversations] = useState<EnhancedConversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<EnhancedConversation | null>(null);

  const createNewConversation = useCallback(() => {
    const newConversation: EnhancedConversation = {
      id: Date.now().toString(),
      title: 'New Enhanced Conversation',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
      totalQueries: 0,
      avgRelevanceScore: 0,
      avgReasoningSteps: 0,
      avgConfidence: 0,
    };
    
    setConversations(prev => [newConversation, ...prev]);
    setCurrentConversation(newConversation);
  }, []);

  const switchConversation = useCallback((id: string) => {
    const conversation = conversations.find(c => c.id === id);
    if (conversation) {
      setCurrentConversation(conversation);
    }
  }, [conversations]);

  const sendMessage = useCallback(async (
    content: string, 
    retrievalResponse?: ContextualResponse,
    chainOfThought?: ChainOfThoughtResponse
  ) => {
    if (!currentConversation) {
      createNewConversation();
      return;
    }

    const userMessage: EnhancedMessage = {
      role: 'user',
      content,
      timestamp: new Date(),
    };

    // Update conversation with user message
    const updatedConversation = {
      ...currentConversation,
      messages: [...currentConversation.messages, userMessage],
      title: currentConversation.messages.length === 0 ? content.slice(0, 50) : currentConversation.title,
      updatedAt: new Date(),
      totalQueries: currentConversation.totalQueries + 1,
    };

    setCurrentConversation(updatedConversation);
    setConversations(prev => 
      prev.map(c => c.id === currentConversation.id ? updatedConversation : c)
    );

    // Simulate AI response with enhanced features
    await new Promise(resolve => setTimeout(resolve, 1500 + Math.random() * 2000));

    const aiResponse: EnhancedMessage = {
      role: 'assistant',
      content: generateEnhancedResponse(content, retrievalResponse, chainOfThought),
      timestamp: new Date(),
      sources: retrievalResponse?.results.slice(0, 3).map(result => ({
        document: result.chunk.id.split('_')[0] + '.pdf',
        page: Math.floor(Math.random() * 10) + 1,
        relevance: result.relevanceScore,
        explanation: result.explanation
      })) || [],
      insights: retrievalResponse?.contextualInsights || [],
      queryAnalysis: retrievalResponse ? {
        intent: retrievalResponse.queryAnalysis.intent.type,
        confidence: retrievalResponse.queryAnalysis.intent.confidence,
        entities: retrievalResponse.queryAnalysis.relatedEntities.slice(0, 3).map(e => e.name),
        strategy: retrievalResponse.strategy.type
      } : undefined,
      explanation: retrievalResponse?.results[0]?.explanation,
      chainOfThought
    };

    // Calculate enhanced metrics
    const allSources = [...updatedConversation.messages, aiResponse]
      .flatMap(m => m.sources || []);
    const avgRelevance = allSources.length > 0 
      ? allSources.reduce((sum, s) => sum + s.relevance, 0) / allSources.length 
      : 0;

    const allChainOfThoughts = [...updatedConversation.messages, aiResponse]
      .map(m => m.chainOfThought)
      .filter(Boolean) as ChainOfThoughtResponse[];
    const avgReasoningSteps = allChainOfThoughts.length > 0
      ? allChainOfThoughts.reduce((sum, cot) => sum + cot.totalSteps, 0) / allChainOfThoughts.length
      : 0;
    const avgConfidence = allChainOfThoughts.length > 0
      ? allChainOfThoughts.reduce((sum, cot) => sum + cot.overallConfidence, 0) / allChainOfThoughts.length
      : 0;

    const finalConversation = {
      ...updatedConversation,
      messages: [...updatedConversation.messages, aiResponse],
      updatedAt: new Date(),
      avgRelevanceScore: avgRelevance,
      avgReasoningSteps,
      avgConfidence,
    };

    setCurrentConversation(finalConversation);
    setConversations(prev => 
      prev.map(c => c.id === currentConversation.id ? finalConversation : c)
    );
  }, [currentConversation, createNewConversation]);

  const deleteConversation = useCallback((id: string) => {
    setConversations(prev => prev.filter(c => c.id !== id));
    if (currentConversation?.id === id) {
      setCurrentConversation(null);
    }
  }, [currentConversation]);

  // Initialize with a default conversation
  React.useEffect(() => {
    if (conversations.length === 0) {
      createNewConversation();
    }
  }, [conversations.length, createNewConversation]);

  return (
    <EnhancedChatContext.Provider value={{
      conversations,
      currentConversation,
      createNewConversation,
      switchConversation,
      sendMessage,
      deleteConversation,
    }}>
      {children}
    </EnhancedChatContext.Provider>
  );
};

// Enhanced response generator
const generateEnhancedResponse = (
  userMessage: string, 
  retrievalResponse?: ContextualResponse,
  chainOfThought?: ChainOfThoughtResponse
): string => {
  const baseResponses = [
    "Based on my advanced analysis of your documents using knowledge graphs and hierarchical retrieval, I can provide you with highly relevant information.",
    "Through sophisticated intent recognition and contextual understanding, I've identified the most pertinent information from your document collection.",
    "Using hierarchical chunking and entity relationship mapping, I've found several key insights that directly address your query.",
    "My enhanced retrieval system has analyzed the semantic relationships and contextual dependencies to provide you with comprehensive information.",
  ];

  let response = baseResponses[Math.floor(Math.random() * baseResponses.length)];

  if (retrievalResponse) {
    const { intent, expandedQuery } = retrievalResponse.queryAnalysis;
    
    response += `\n\nQuery Analysis: I detected this as a ${intent.type} query with ${(intent.confidence * 100).toFixed(0)}% confidence. `;
    
    if (expandedQuery.synonyms.length > 0) {
      response += `I expanded your query to include related terms: ${expandedQuery.synonyms.slice(0, 3).join(', ')}.`;
    }

    if (retrievalResponse.results.length > 0) {
      const avgRelevance = retrievalResponse.results.reduce((sum, r) => sum + r.relevanceScore, 0) / retrievalResponse.results.length;
      response += `\n\nI found ${retrievalResponse.results.length} highly relevant passages with an average relevance score of ${(avgRelevance * 100).toFixed(0)}%.`;
    }
  }

  if (chainOfThought) {
    response += `\n\nChain of Thought: I processed your query through ${chainOfThought.totalSteps} reasoning steps with ${(chainOfThought.overallConfidence * 100).toFixed(0)}% overall confidence. The query was classified as ${chainOfThought.metadata.queryComplexity} complexity, requiring ${chainOfThought.metadata.reasoningStrategy} strategy.`;
    
    if (chainOfThought.executionTime) {
      response += ` This analysis completed in ${chainOfThought.executionTime}ms.`;
    }
  }

  response += "\n\nThis response demonstrates the power of advanced RAG with knowledge graphs, intent recognition, hierarchical document understanding, and transparent chain of thought reasoning.";

  return response;
};