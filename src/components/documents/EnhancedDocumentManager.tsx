import React, { useState, useCallback, useRef } from 'react';
import { 
  Upload, FileText, Search, Filter, Download, Trash2, 
  Eye, Edit, Share, Tag, Clock, User, FileCheck,
  AlertCircle, CheckCircle, Loader, X, Plus
} from 'lucide-react';

interface Document {
  id: string;
  name: string;
  type: string;
  size: number;
  uploadDate: Date;
  lastModified: Date;
  status: 'processing' | 'ready' | 'error';
  tags: string[];
  summary?: string;
  citations?: Citation[];
  content?: string;
  metadata?: DocumentMetadata;
}

interface Citation {
  id: string;
  text: string;
  page?: number;
  confidence: number;
  type: 'direct' | 'paraphrase' | 'reference';
}

interface DocumentMetadata {
  author?: string;
  title?: string;
  publishDate?: Date;
  pageCount?: number;
  wordCount?: number;
  language?: string;
}

interface EnhancedDocumentManagerProps {
  onDocumentSelect?: (document: Document) => void;
  onDocumentUpload?: (files: FileList) => void;
}

export const EnhancedDocumentManager: React.FC<EnhancedDocumentManagerProps> = ({
  onDocumentSelect,
  onDocumentUpload
}) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);

  // Handle file upload
  const handleFileUpload = useCallback(async (files: FileList) => {
    setIsUploading(true);
    setUploadProgress(0);

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const newDocument: Document = {
        id: `doc_${Date.now()}_${i}`,
        name: file.name,
        type: file.type || 'application/octet-stream',
        size: file.size,
        uploadDate: new Date(),
        lastModified: new Date(file.lastModified),
        status: 'processing',
        tags: [],
        summary: 'Processing document...',
      };

      setDocuments(prev => [...prev, newDocument]);

      // Simulate processing
      setTimeout(() => {
        setDocuments(prev => prev.map(doc => 
          doc.id === newDocument.id 
            ? { 
                ...doc, 
                status: 'ready',
                summary: `Processed document: ${file.name}. Ready for analysis and citation.`,
                metadata: {
                  pageCount: Math.floor(Math.random() * 50) + 1,
                  wordCount: Math.floor(Math.random() * 10000) + 1000,
                  language: 'en'
                },
                citations: [
                  {
                    id: 'cite_1',
                    text: 'This is an example citation from the document.',
                    page: 1,
                    confidence: 0.95,
                    type: 'direct'
                  }
                ]
              }
            : doc
        ));
      }, 2000 + i * 1000);

      setUploadProgress(((i + 1) / files.length) * 100);
    }

    setTimeout(() => {
      setIsUploading(false);
      setUploadProgress(0);
    }, 3000);

    onDocumentUpload?.(files);
  }, [onDocumentUpload]);

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      background: 'linear-gradient(135deg, #1a1a1a 0%, #2d1b69 100%)',
      color: 'white',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      {/* Document List Panel */}
      <div style={{
        width: '400px',
        borderRight: '1px solid rgba(255,255,255,0.1)',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Header */}
        <div style={{
          padding: '20px',
          borderBottom: '1px solid rgba(255,255,255,0.1)'
        }}>
          <h2 style={{ margin: '0 0 16px 0', color: '#10b981' }}>
            📄 Document Manager
          </h2>
          
          {/* Upload Button */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            style={{
              width: '100%',
              background: 'linear-gradient(45deg, #10b981, #059669)',
              border: 'none',
              color: 'white',
              padding: '12px',
              borderRadius: '8px',
              cursor: isUploading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              fontSize: '14px',
              fontWeight: 'bold',
              marginBottom: '16px'
            }}
          >
            {isUploading ? (
              <>
                <Loader style={{ width: '16px', height: '16px', animation: 'spin 1s linear infinite' }} />
                Uploading... {uploadProgress.toFixed(0)}%
              </>
            ) : (
              <>
                <Upload style={{ width: '16px', height: '16px' }} />
                Upload Documents
              </>
            )}
          </button>

          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.txt,.md"
            onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
            style={{ display: 'none' }}
          />

          {/* Search */}
          <div style={{ position: 'relative', marginBottom: '12px' }}>
            <Search style={{
              position: 'absolute',
              left: '12px',
              top: '50%',
              transform: 'translateY(-50%)',
              width: '16px',
              height: '16px',
              color: '#9ca3af'
            }} />
            <input
              type="text"
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                background: 'rgba(255,255,255,0.1)',
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: '6px',
                padding: '8px 8px 8px 36px',
                color: 'white',
                fontSize: '14px',
                outline: 'none'
              }}
            />
          </div>

          {/* Filter */}
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            style={{
              width: '100%',
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '6px',
              padding: '8px',
              color: 'white',
              fontSize: '14px',
              outline: 'none'
            }}
          >
            <option value="all">All Documents</option>
            <option value="pdf">PDF Files</option>
            <option value="doc">Word Documents</option>
            <option value="processing">Processing</option>
            <option value="ready">Ready</option>
          </select>
        </div>

        {/* Document List */}
        <div style={{
          flex: 1,
          overflow: 'auto',
          padding: '16px'
        }}>
          {documents.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: '40px 20px',
              color: '#9ca3af'
            }}>
              <FileText style={{ width: '48px', height: '48px', margin: '0 auto 16px' }} />
              <p>No documents uploaded yet</p>
              <p style={{ fontSize: '12px' }}>
                Upload PDF, Word, or text files to get started
              </p>
            </div>
          ) : (
            documents.map((doc) => (
              <div
                key={doc.id}
                onClick={() => {
                  setSelectedDocument(doc);
                  onDocumentSelect?.(doc);
                }}
                style={{
                  background: selectedDocument?.id === doc.id 
                    ? 'rgba(16, 185, 129, 0.2)' 
                    : 'rgba(255,255,255,0.05)',
                  border: selectedDocument?.id === doc.id
                    ? '1px solid rgba(16, 185, 129, 0.5)'
                    : '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  padding: '12px',
                  marginBottom: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                  <FileText style={{ width: '16px', height: '16px', color: '#10b981', marginTop: '2px' }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                      fontSize: '14px',
                      fontWeight: '500',
                      marginBottom: '4px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {doc.name}
                    </div>
                    <div style={{
                      fontSize: '12px',
                      color: '#9ca3af',
                      marginBottom: '4px'
                    }}>
                      {(doc.size / 1024).toFixed(1)} KB • {doc.uploadDate.toLocaleDateString()}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      {doc.status === 'processing' && (
                        <>
                          <Loader style={{ width: '12px', height: '12px', animation: 'spin 1s linear infinite' }} />
                          <span style={{ fontSize: '11px', color: '#f59e0b' }}>Processing...</span>
                        </>
                      )}
                      {doc.status === 'ready' && (
                        <>
                          <CheckCircle style={{ width: '12px', height: '12px', color: '#10b981' }} />
                          <span style={{ fontSize: '11px', color: '#10b981' }}>Ready</span>
                        </>
                      )}
                      {doc.status === 'error' && (
                        <>
                          <AlertCircle style={{ width: '12px', height: '12px', color: '#ef4444' }} />
                          <span style={{ fontSize: '11px', color: '#ef4444' }}>Error</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Document Details Panel */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {selectedDocument ? (
          <>
            {/* Document Header */}
            <div style={{
              padding: '20px',
              borderBottom: '1px solid rgba(255,255,255,0.1)',
              background: 'rgba(255,255,255,0.05)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3 style={{ margin: '0 0 8px 0', fontSize: '18px' }}>
                    {selectedDocument.name}
                  </h3>
                  <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: '#9ca3af' }}>
                    <span>Size: {(selectedDocument.size / 1024).toFixed(1)} KB</span>
                    <span>Uploaded: {selectedDocument.uploadDate.toLocaleDateString()}</span>
                    {selectedDocument.metadata?.pageCount && (
                      <span>Pages: {selectedDocument.metadata.pageCount}</span>
                    )}
                    {selectedDocument.metadata?.wordCount && (
                      <span>Words: {selectedDocument.metadata.wordCount.toLocaleString()}</span>
                    )}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button style={{
                    background: 'rgba(59, 130, 246, 0.2)',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                    color: '#60a5fa',
                    padding: '6px',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}>
                    <Download style={{ width: '14px', height: '14px' }} />
                  </button>
                  <button style={{
                    background: 'rgba(16, 185, 129, 0.2)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    color: '#10b981',
                    padding: '6px',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}>
                    <Share style={{ width: '14px', height: '14px' }} />
                  </button>
                  <button style={{
                    background: 'rgba(239, 68, 68, 0.2)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    color: '#ef4444',
                    padding: '6px',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}>
                    <Trash2 style={{ width: '14px', height: '14px' }} />
                  </button>
                </div>
              </div>
            </div>

            {/* Document Content */}
            <div style={{ flex: 1, overflow: 'auto', padding: '20px' }}>
              {/* Summary */}
              <div style={{
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                borderRadius: '8px',
                padding: '16px',
                marginBottom: '20px'
              }}>
                <h4 style={{ margin: '0 0 8px 0', color: '#10b981' }}>📋 Summary</h4>
                <p style={{ margin: 0, fontSize: '14px', lineHeight: '1.5' }}>
                  {selectedDocument.summary}
                </p>
              </div>

              {/* Citations */}
              {selectedDocument.citations && selectedDocument.citations.length > 0 && (
                <div style={{
                  background: 'rgba(59, 130, 246, 0.1)',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                  borderRadius: '8px',
                  padding: '16px',
                  marginBottom: '20px'
                }}>
                  <h4 style={{ margin: '0 0 12px 0', color: '#60a5fa' }}>📖 Citations</h4>
                  {selectedDocument.citations.map((citation) => (
                    <div
                      key={citation.id}
                      style={{
                        background: 'rgba(255,255,255,0.05)',
                        borderRadius: '6px',
                        padding: '12px',
                        marginBottom: '8px'
                      }}
                    >
                      <div style={{ fontSize: '14px', marginBottom: '4px' }}>
                        "{citation.text}"
                      </div>
                      <div style={{ fontSize: '12px', color: '#9ca3af', display: 'flex', gap: '12px' }}>
                        {citation.page && <span>Page {citation.page}</span>}
                        <span>Confidence: {(citation.confidence * 100).toFixed(0)}%</span>
                        <span style={{ 
                          color: citation.type === 'direct' ? '#10b981' : 
                                citation.type === 'paraphrase' ? '#f59e0b' : '#60a5fa'
                        }}>
                          {citation.type}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Metadata */}
              {selectedDocument.metadata && (
                <div style={{
                  background: 'rgba(168, 85, 247, 0.1)',
                  border: '1px solid rgba(168, 85, 247, 0.3)',
                  borderRadius: '8px',
                  padding: '16px'
                }}>
                  <h4 style={{ margin: '0 0 12px 0', color: '#c084fc' }}>📊 Metadata</h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '8px' }}>
                    {selectedDocument.metadata.author && (
                      <div style={{ fontSize: '12px' }}>
                        <span style={{ color: '#9ca3af' }}>Author:</span> {selectedDocument.metadata.author}
                      </div>
                    )}
                    {selectedDocument.metadata.language && (
                      <div style={{ fontSize: '12px' }}>
                        <span style={{ color: '#9ca3af' }}>Language:</span> {selectedDocument.metadata.language}
                      </div>
                    )}
                    {selectedDocument.metadata.publishDate && (
                      <div style={{ fontSize: '12px' }}>
                        <span style={{ color: '#9ca3af' }}>Published:</span> {selectedDocument.metadata.publishDate.toLocaleDateString()}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <div style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#9ca3af',
            textAlign: 'center'
          }}>
            <div>
              <FileCheck style={{ width: '64px', height: '64px', margin: '0 auto 16px' }} />
              <h3 style={{ margin: '0 0 8px 0' }}>Select a Document</h3>
              <p style={{ margin: 0, fontSize: '14px' }}>
                Choose a document from the list to view details, citations, and metadata
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};