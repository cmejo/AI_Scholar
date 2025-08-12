/**
 * Type definitions for chat functionality
 */

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  sources?: ChatSource[];
  metadata?: Record<string, any>;
}

export interface ChatSource {
  document: string;
  page: number;
  relevance: number;
  excerpt?: string;
}

export interface ChatConversation {
  id: string;
  messages: ChatMessage[];
  title?: string;
  createdAt: Date;
  updatedAt: Date;
  metadata?: Record<string, any>;
}

export interface ChatContext {
  currentConversation?: ChatConversation;
  conversations: ChatConversation[];
  sendMessage: (content: string) => Promise<void>;
  createConversation: () => Promise<ChatConversation>;
  deleteConversation: (id: string) => Promise<void>;
  loadConversation: (id: string) => Promise<void>;
  isLoading: boolean;
  error?: string;
}

export interface DocumentContext {
  documents: Document[];
  uploadDocument: (file: File) => Promise<Document>;
  deleteDocument: (id: string) => Promise<void>;
  isUploading: boolean;
  error?: string;
}

export interface Document {
  id: string;
  name: string;
  type: string;
  size: number;
  uploadedAt?: Date;
  processedAt?: Date;
  status?: 'uploading' | 'processing' | 'ready' | 'error';
  metadata?: Record<string, any>;
}