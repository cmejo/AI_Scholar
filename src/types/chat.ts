export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  type?: 'text' | 'voice' | 'system';
  metadata?: {
    voiceTranscription?: string;
    confidence?: number;
    processingTime?: number;
    sources?: string[];
    reasoning?: ThoughtStep[];
  };
}

export interface ThoughtStep {
  step: number;
  description: string;
  reasoning: string;
  confidence: number;
}

export interface ChatMode {
  id: 'standard' | 'streaming' | 'chain_of_thought' | 'fact_checked' | 'voice';
  name: string;
  description: string;
  icon: string;
  enabled: boolean;
}

export interface VoiceSettings {
  enabled: boolean;
  autoListen: boolean;
  language: string;
  voice: string;
  rate: number;
  pitch: number;
  volume: number;
}

export interface ChatSettings {
  mode: ChatMode['id'];
  temperature: number;
  maxTokens: number;
  enableMemory: boolean;
  enableFactChecking: boolean;
  enableChainOfThought: boolean;
  voiceSettings: VoiceSettings;
}

export interface StreamingResponse {
  content: string;
  isComplete: boolean;
  metadata?: {
    processingTime?: number;
    tokensGenerated?: number;
  };
}

export interface FactCheckResult {
  claim: string;
  verified: boolean;
  confidence: number;
  sources: string[];
  explanation: string;
}

// Additional types for chat context
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Array<{
    document: string;
    page: number;
  }> | undefined;
}

export interface ChatConversation {
  id: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
}

export interface ChatContext {
  currentConversation: ChatConversation | undefined;
  conversations: ChatConversation[];
  sendMessage: (content: string, context?: any) => Promise<void>;
  createConversation: () => Promise<ChatConversation>;
  deleteConversation: (id: string) => Promise<void>;
  loadConversation: (id: string) => Promise<void>;
  isLoading: boolean;
  error: string | undefined;
}

// Document types for context
export interface Document {
  id: string;
  title: string;
  content: string;
  type: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface DocumentContext {
  documents: Document[];
  currentDocument: Document | null;
  addDocument: (document: Document) => void;
  updateDocument: (id: string, updates: Partial<Document>) => void;
  deleteDocument: (id: string) => void;
  selectDocument: (id: string) => void;
}