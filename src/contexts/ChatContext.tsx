import React, { createContext, useCallback, useContext, useState } from 'react';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Array<{
    document: string;
    page: number;
    relevance: number;
  }>;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

interface ChatContextType {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  createNewConversation: () => void;
  switchConversation: (id: string) => void;
  sendMessage: (content: string) => Promise<void>;
  deleteConversation: (id: string) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);

  const createNewConversation = useCallback(() => {
    const newConversation: Conversation = {
      id: Date.now().toString(),
      title: 'New Conversation',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
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

  const sendMessage = useCallback(async (content: string) => {
    if (!currentConversation) {
      createNewConversation();
      return;
    }

    const userMessage: Message = {
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
    };

    setCurrentConversation(updatedConversation);
    setConversations(prev => 
      prev.map(c => c.id === currentConversation.id ? updatedConversation : c)
    );

    // Simulate AI response (in production, this would call your Ollama backend)
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));

    const aiResponse: Message = {
      role: 'assistant',
      content: generateMockResponse(content),
      timestamp: new Date(),
      sources: [
        { document: 'sample-document.pdf', page: 1, relevance: 0.95 },
        { document: 'research-paper.pdf', page: 3, relevance: 0.87 },
      ],
    };

    const finalConversation = {
      ...updatedConversation,
      messages: [...updatedConversation.messages, aiResponse],
      updatedAt: new Date(),
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
  useEffect(() => {
    if (conversations.length === 0) {
      createNewConversation();
    }
  }, [conversations.length, createNewConversation]);

  return (
    <ChatContext.Provider value={{
      conversations,
      currentConversation,
      createNewConversation,
      switchConversation,
      sendMessage,
      deleteConversation,
    }}>
      {children}
    </ChatContext.Provider>
  );
};

// Mock response generator (replace with actual Ollama integration)
const generateMockResponse = (userMessage: string): string => {
  const responses = [
    "Based on your uploaded documents, I can provide you with relevant information. The content you're asking about relates to several key concepts found in your research materials.",
    "I've analyzed your documents and found several relevant passages. According to the sources I've reviewed, this topic is covered in depth across multiple documents.",
    "Let me search through your document collection for relevant information. I found several matches that directly address your question with supporting evidence.",
    "Drawing from your uploaded materials, I can provide insights based on the following findings. The documents contain valuable information that answers your query.",
  ];
  
  return responses[Math.floor(Math.random() * responses.length)] + 
    "\n\nThis response is generated from the mock implementation. In production, this would be powered by your Ollama backend with actual RAG capabilities.";
};