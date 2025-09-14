import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/apiService';

interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export const useApiIntegration = () => {
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const [lastHealthCheck, setLastHealthCheck] = useState<Date | null>(null);

  // Health check
  const checkConnection = useCallback(async () => {
    setConnectionStatus('checking');
    try {
      const response = await apiService.healthCheck();
      if (response.success) {
        setConnectionStatus('connected');
        setLastHealthCheck(new Date());
      } else {
        setConnectionStatus('disconnected');
      }
    } catch (error) {
      setConnectionStatus('disconnected');
    }
  }, []);

  // Periodic health checks
  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, [checkConnection]);

  return {
    connectionStatus,
    lastHealthCheck,
    checkConnection,
  };
};

// Hook for API calls with loading states
export const useApiCall = <T>(
  apiCall: () => Promise<{ success: boolean; data?: T; error?: string }>,
  dependencies: any[] = []
) => {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const response = await apiCall();
      if (response.success) {
        setState({
          data: response.data || null,
          loading: false,
          error: null,
        });
      } else {
        setState({
          data: null,
          loading: false,
          error: response.error || 'Unknown error',
        });
      }
    } catch (error) {
      setState({
        data: null,
        loading: false,
        error: error instanceof Error ? error.message : 'Network error',
      });
    }
  }, dependencies);

  useEffect(() => {
    execute();
  }, [execute]);

  return {
    ...state,
    refetch: execute,
  };
};

// Hook for chat integration
export const useChatApi = () => {
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = useCallback(async (message: string, context?: any) => {
    setLoading(true);
    try {
      const response = await apiService.sendChatMessage(message, context);
      if (response.success && response.data) {
        const newMessage = {
          id: Date.now().toString(),
          message,
          response: response.data.response,
          sources: response.data.sources,
          reasoning: response.data.reasoning,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, newMessage]);
        return newMessage;
      } else {
        throw new Error(response.error || 'Failed to send message');
      }
    } catch (error) {
      console.error('Chat error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const loadHistory = useCallback(async () => {
    try {
      const response = await apiService.getChatHistory();
      if (response.success && response.data) {
        setMessages(response.data);
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  return {
    messages,
    loading,
    sendMessage,
    loadHistory,
  };
};

// Hook for document management
export const useDocumentApi = () => {
  const [documents, setDocuments] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);

  const uploadDocument = useCallback(async (file: File) => {
    setUploading(true);
    try {
      const response = await apiService.uploadDocument(file);
      if (response.success && response.data) {
        await loadDocuments(); // Refresh list
        return response.data;
      } else {
        throw new Error(response.error || 'Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      throw error;
    } finally {
      setUploading(false);
    }
  }, []);

  const loadDocuments = useCallback(async () => {
    try {
      const response = await apiService.getDocuments();
      if (response.success && response.data) {
        setDocuments(response.data);
      }
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  }, []);

  const deleteDocument = useCallback(async (documentId: string) => {
    try {
      const response = await apiService.deleteDocument(documentId);
      if (response.success) {
        await loadDocuments(); // Refresh list
      } else {
        throw new Error(response.error || 'Delete failed');
      }
    } catch (error) {
      console.error('Delete error:', error);
      throw error;
    }
  }, [loadDocuments]);

  const searchDocuments = useCallback(async (query: string) => {
    try {
      const response = await apiService.searchDocuments(query);
      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Search failed');
      }
    } catch (error) {
      console.error('Search error:', error);
      throw error;
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  return {
    documents,
    uploading,
    uploadDocument,
    deleteDocument,
    searchDocuments,
    loadDocuments,
  };
};

// Hook for analytics
export const useAnalyticsApi = () => {
  const logAction = useCallback(async (action: string, metadata?: any) => {
    try {
      await apiService.logUserAction(action, metadata);
    } catch (error) {
      console.error('Failed to log action:', error);
    }
  }, []);

  const getAnalytics = useCallback(async (timeRange: string = '7d') => {
    try {
      const response = await apiService.getAnalytics(timeRange);
      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to get analytics');
      }
    } catch (error) {
      console.error('Analytics error:', error);
      throw error;
    }
  }, []);

  return {
    logAction,
    getAnalytics,
  };
};