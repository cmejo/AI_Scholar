import React, { createContext, useContext, useState, useCallback } from 'react';

export interface Document {
  id: string;
  name: string;
  size: number;
  type: string;
  status: 'uploading' | 'processing' | 'processed' | 'error';
  uploadedAt: Date;
  chunks?: number;
  embeddings?: number;
  content?: string;
}

interface DocumentContextType {
  documents: Document[];
  uploadDocument: (file: File) => Promise<void>;
  deleteDocument: (id: string) => void;
  searchDocuments: (query: string) => Document[];
  getDocumentContent: (id: string) => string | null;
}

const DocumentContext = createContext<DocumentContextType | undefined>(undefined);

export const useDocument = () => {
  const context = useContext(DocumentContext);
  if (!context) {
    throw new Error('useDocument must be used within a DocumentProvider');
  }
  return context;
};

export const DocumentProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [documents, setDocuments] = useState<Document[]>([]);

  const uploadDocument = useCallback(async (file: File) => {
    const document: Document = {
      id: Date.now().toString(),
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'uploading',
      uploadedAt: new Date(),
    };

    setDocuments(prev => [...prev, document]);

    try {
      // Simulate file upload
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Update to processing
      setDocuments(prev => 
        prev.map(d => d.id === document.id ? { ...d, status: 'processing' } : d)
      );

      // Read file content
      const content = await readFileContent(file);
      
      // Simulate processing (chunking, embedding generation)
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Simulate chunk and embedding counts
      const chunks = Math.floor(content.length / 500) + 1;
      const embeddings = chunks;

      // Update to processed
      setDocuments(prev => 
        prev.map(d => d.id === document.id ? { 
          ...d, 
          status: 'processed',
          content,
          chunks,
          embeddings
        } : d)
      );
    } catch (error) {
      setDocuments(prev => 
        prev.map(d => d.id === document.id ? { ...d, status: 'error' } : d)
      );
    }
  }, []);

  const deleteDocument = useCallback((id: string) => {
    setDocuments(prev => prev.filter(d => d.id !== id));
  }, []);

  const searchDocuments = useCallback((query: string) => {
    return documents.filter(doc => 
      doc.name.toLowerCase().includes(query.toLowerCase()) ||
      doc.content?.toLowerCase().includes(query.toLowerCase())
    );
  }, [documents]);

  const getDocumentContent = useCallback((id: string) => {
    const document = documents.find(d => d.id === id);
    return document?.content || null;
  }, [documents]);

  return (
    <DocumentContext.Provider value={{
      documents,
      uploadDocument,
      deleteDocument,
      searchDocuments,
      getDocumentContent,
    }}>
      {children}
    </DocumentContext.Provider>
  );
};

// Helper function to read file content
const readFileContent = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target?.result as string);
    reader.onerror = reject;
    reader.readAsText(file);
  });
};