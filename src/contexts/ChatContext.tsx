/**
 * Chat context for managing conversation state
 */

import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';
import type { ChatContext, ChatConversation, ChatMessage } from '../types/chat';

const ChatContextImpl = createContext<ChatContext | undefined>(undefined);

export const ChatProvider: React.FC<{ children: React.ReactNode }> = React.memo(({ children }) => {
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<ChatConversation>();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>();

  const sendMessage = useCallback(async (content: string, context?: any) => {
    if (!currentConversation) return;

    setIsLoading(true);
    setError(undefined);

    try {
      const userMessage: ChatMessage = {
        role: 'user',
        content,
        timestamp: new Date(),
      };

      // Add user message
      const updatedConversation = {
        ...currentConversation,
        messages: [...currentConversation.messages, userMessage],
        updatedAt: new Date(),
      };

      setCurrentConversation(updatedConversation);

      // Import API service
      const { apiService } = await import('../services/apiService');
      
      // Call the actual API
      const response = await apiService.sendChatMessage(content, context);

      if (response.success && response.data) {
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: response.data.response,
          timestamp: new Date(),
          sources: response.data.sources || undefined,
        };

        const finalConversation = {
          ...updatedConversation,
          messages: [...updatedConversation.messages, assistantMessage],
          updatedAt: new Date(),
        };

        setCurrentConversation(finalConversation);
      } else {
        throw new Error(response.error || 'Failed to get AI response');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      
      // Add error message to conversation
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your message. Please make sure the backend server is running and try again.',
        timestamp: new Date(),
      };

      if (currentConversation) {
        const errorConversation = {
          ...currentConversation,
          messages: [...currentConversation.messages, errorMessage],
          updatedAt: new Date(),
        };
        setCurrentConversation(errorConversation);
      }
    } finally {
      setIsLoading(false);
    }
  }, [currentConversation]);

  const createConversation = useCallback(async () => {
    const newConversation: ChatConversation = {
      id: `conversation-${Date.now()}`,
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    setConversations(prev => [...prev, newConversation]);
    setCurrentConversation(newConversation);
    return newConversation;
  }, []);

  const deleteConversation = useCallback(async (id: string) => {
    setConversations(prev => prev.filter(conv => conv.id !== id));
    if (currentConversation?.id === id) {
      setCurrentConversation(undefined);
    }
  }, [currentConversation]);

  const loadConversation = useCallback(async (id: string) => {
    const conversation = conversations.find(conv => conv.id === id);
    if (conversation) {
      setCurrentConversation(conversation);
    }
  }, [conversations]);

  const value: ChatContext = useMemo(() => ({
    currentConversation,
    conversations,
    sendMessage,
    createConversation,
    deleteConversation,
    loadConversation,
    isLoading,
    error,
  }), [
    currentConversation,
    conversations,
    sendMessage,
    createConversation,
    deleteConversation,
    loadConversation,
    isLoading,
    error,
  ]);

  return (
    <ChatContextImpl.Provider value={value}>
      {children}
    </ChatContextImpl.Provider>
  );
});

export const useChat = (): ChatContext => {
  const context = useContext(ChatContextImpl);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};