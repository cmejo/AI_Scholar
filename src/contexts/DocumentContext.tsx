/**
 * Document context for managing document state
 */

import React, { createContext, useCallback, useContext, useState } from 'react';
import type { Document, DocumentContext } from '../types/chat';

const DocumentContextImpl = createContext<DocumentContext | undefined>(undefined);

export const DocumentProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string>();

  const uploadDocument = useCallback(async (file: File): Promise<Document> => {
    setIsUploading(true);
    setError(undefined);

    try {
      // Simulate upload process
      await new Promise(resolve => setTimeout(resolve, 1000));

      const newDocument: Document = {
        id: `doc-${Date.now()}`,
        name: file.name,
        type: file.type,
        size: file.size,
        uploadedAt: new Date(),
        status: 'ready',
      };

      setDocuments(prev => [...prev, newDocument]);
      return newDocument;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsUploading(false);
    }
  }, []);

  const deleteDocument = useCallback(async (id: string) => {
    setDocuments(prev => prev.filter(doc => doc.id !== id));
  }, []);

  const value: DocumentContext = {
    documents,
    uploadDocument,
    deleteDocument,
    isUploading,
    error,
  };

  return (
    <DocumentContextImpl.Provider value={value}>
      {children}
    </DocumentContextImpl.Provider>
  );
};

export const useDocument = (): DocumentContext => {
  const context = useContext(DocumentContextImpl);
  if (!context) {
    throw new Error('useDocument must be used within a DocumentProvider');
  }
  return context;
};