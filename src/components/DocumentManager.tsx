import React, { useState, useEffect, useRef } from 'react';
import { 
  Upload, 
  Search, 
  FileText, 
  Trash2, 
  Download, 
  Eye,
  Plus,
  Filter,
  X,
  AlertCircle,
  CheckCircle,
  Loader2
} from 'lucide-react';
import { Document, SearchResponse, UploadProgress } from '../types/document';
import { documentService } from '../services/documentService';

export const DocumentManager: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [showUploadArea, setShowUploadArea] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      setIsLoading(true);
      const docs = await documentService.getDocuments();
      setDocuments(docs);
      setError(null);
    } catch (err) {
      setError('Failed to load documents');
      console.error('Load documents error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    try {
      setIsSearching(true);
      const results = await documentService.searchDocuments(searchQuery, 10);
      setSearchResults(results);
      setError(null);
    } catch (err) {
      setError('Search failed');
      console.error('Search error:', err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleFileUpload = async (files: FileList) => {
    const fileArray = Array.from(files);
    
    for (const file of fileArray) {
      const uploadItem: UploadProgress = {
        file,
        progress: 0,
        status: 'uploading'
      };
      
      setUploadProgress(prev => [...prev, uploadItem]);

      try {
        const document = await documentService.uploadDocument(file, (progress) => {
          setUploadProgress(prev => 
            prev.map(item => 
              item.file === file 
                ? { ...item, progress, status: progress === 100 ? 'processing' : 'uploading' }
                : item
            )
          );
        });

        // Mark as completed
        setUploadProgress(prev => 
          prev.map(item => 
            item.file === file 
              ? { ...item, progress: 100, status: 'completed' }
              : item
          )
        );

        // Add to documents list
        setDocuments(prev => [document, ...prev]);

        // Remove from upload progress after delay
        setTimeout(() => {
          setUploadProgress(prev => prev.filter(item => item.file !== file));
        }, 2000);

      } catch (err) {
        setUploadProgress(prev => 
          prev.map(item => 
            item.file === file 
              ? { ...item, status: 'error', error: 'Upload failed' }
              : item
          )
        );
        console.error('Upload error:', err);
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDeleteDocument = async (documentId: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
      await documentService.deleteDocument(documentId);
      setDocuments(prev => prev.filter(doc => doc.id !== documentId));
      if (selectedDocument?.id === documentId) {
        setSelectedDocument(null);
      }
    } catch (err) {
      setError('Failed to delete document');
      console.error('Delete error:', err);
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults(null);
  };

  return (
    <div className="flex h-full bg-gray-900 text-white">
      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold">Document Management</h1>
            <button
              onClick={() => setShowUploadArea(!showUploadArea)}
              className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Upload Documents</span>
            </button>
          </div>

          {/* Search */}
          <form onSubmit={handleSearch} className="flex space-x-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search documents and research papers..."
                className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={clearSearch}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
            <button
              type="submit"
              disabled={isSearching || !searchQuery.trim()}
              className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors flex items-center space-x-2"
            >
              {isSearching ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Search className="w-4 h-4" />
              )}
              <span>Search</span>
            </button>
          </form>
        </div>

        {/* Upload Area */}
        {showUploadArea && (
          <div className="p-6 border-b border-gray-700">
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center hover:border-purple-500 transition-colors cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-lg font-medium text-gray-300 mb-2">
                Drop files here or click to upload
              </p>
              <p className="text-sm text-gray-500">
                Supports PDF, TXT, and other document formats
              </p>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.txt,.md,.doc,.docx"
                onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
                className="hidden"
              />
            </div>

            {/* Upload Progress */}
            {uploadProgress.length > 0 && (
              <div className="mt-4 space-y-2">
                {uploadProgress.map((item, index) => (
                  <div key={index} className="bg-gray-800 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">{item.file.name}</span>
                      <div className="flex items-center space-x-2">
                        {item.status === 'completed' && <CheckCircle className="w-4 h-4 text-green-500" />}
                        {item.status === 'error' && <AlertCircle className="w-4 h-4 text-red-500" />}
                        {(item.status === 'uploading' || item.status === 'processing') && (
                          <Loader2 className="w-4 h-4 animate-spin text-purple-500" />
                        )}
                      </div>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-300 ${
                          item.status === 'error' ? 'bg-red-500' : 
                          item.status === 'completed' ? 'bg-green-500' : 'bg-purple-500'
                        }`}
                        style={{ width: `${item.progress}%` }}
                      />
                    </div>
                    {item.error && (
                      <p className="text-red-400 text-xs mt-1">{item.error}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="p-4 bg-red-600/20 border-l-4 border-red-500 text-red-300">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4" />
              <span>{error}</span>
              <button
                onClick={() => setError(null)}
                className="ml-auto text-red-400 hover:text-red-300"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {searchResults ? (
            /* Search Results */
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">
                  Search Results ({searchResults.total_results})
                </h2>
                <button
                  onClick={clearSearch}
                  className="text-gray-400 hover:text-white text-sm"
                >
                  Back to Documents
                </button>
              </div>
              <div className="space-y-4">
                {searchResults.results.map((result) => (
                  <div key={result.id} className="bg-gray-800 rounded-lg p-4">
                    <h3 className="font-medium text-white mb-2">{result.title}</h3>
                    <p className="text-gray-400 text-sm mb-2">{result.content}</p>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>Relevance: {(result.relevance_score * 100).toFixed(1)}%</span>
                      <span>{result.source}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            /* Document List */
            <div className="p-6">
              <h2 className="text-lg font-semibold mb-4">Your Documents ({documents.length})</h2>
              
              {isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
                </div>
              ) : documents.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-400">No documents uploaded yet</p>
                  <p className="text-gray-500 text-sm">Upload your first document to get started</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {documents.map((doc) => (
                    <div key={doc.id} className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition-colors">
                      <div className="flex items-start justify-between mb-3">
                        <FileText className="w-8 h-8 text-purple-500 flex-shrink-0" />
                        <button
                          onClick={() => handleDeleteDocument(doc.id)}
                          className="text-gray-400 hover:text-red-400 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                      
                      <h3 className="font-medium text-white mb-2 truncate" title={doc.title}>
                        {doc.title}
                      </h3>
                      
                      <p className="text-gray-400 text-sm mb-3 line-clamp-2">
                        {doc.content}
                      </p>
                      
                      <div className="text-xs text-gray-500 space-y-1">
                        <div>Size: {documentService.formatFileSize(doc.size)}</div>
                        <div>Uploaded: {documentService.formatDate(doc.uploadDate)}</div>
                        {doc.metadata.authors && (
                          <div>Authors: {doc.metadata.authors.join(', ')}</div>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-2 mt-3">
                        <button
                          onClick={() => setSelectedDocument(doc)}
                          className="flex-1 bg-purple-600 hover:bg-purple-700 text-white text-xs px-3 py-1 rounded transition-colors flex items-center justify-center space-x-1"
                        >
                          <Eye className="w-3 h-3" />
                          <span>View</span>
                        </button>
                        <button className="bg-gray-600 hover:bg-gray-700 text-white text-xs px-3 py-1 rounded transition-colors flex items-center justify-center space-x-1">
                          <Download className="w-3 h-3" />
                          <span>Download</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Document Viewer Sidebar */}
      {selectedDocument && (
        <div className="w-96 bg-gray-800 border-l border-gray-700 flex flex-col">
          <div className="p-4 border-b border-gray-700 flex items-center justify-between">
            <h3 className="font-semibold">Document Details</h3>
            <button
              onClick={() => setSelectedDocument(null)}
              className="text-gray-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4">
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-white mb-2">{selectedDocument.title}</h4>
                <p className="text-gray-400 text-sm">{selectedDocument.content}</p>
              </div>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Type:</span>
                  <span className="text-gray-300 capitalize">{selectedDocument.type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Size:</span>
                  <span className="text-gray-300">{documentService.formatFileSize(selectedDocument.size)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Uploaded:</span>
                  <span className="text-gray-300">{documentService.formatDate(selectedDocument.uploadDate)}</span>
                </div>
                {selectedDocument.metadata.authors && (
                  <div>
                    <span className="text-gray-500">Authors:</span>
                    <div className="text-gray-300 mt-1">
                      {selectedDocument.metadata.authors.join(', ')}
                    </div>
                  </div>
                )}
                {selectedDocument.metadata.year && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Year:</span>
                    <span className="text-gray-300">{selectedDocument.metadata.year}</span>
                  </div>
                )}
                {selectedDocument.metadata.journal && (
                  <div>
                    <span className="text-gray-500">Journal:</span>
                    <div className="text-gray-300 mt-1">{selectedDocument.metadata.journal}</div>
                  </div>
                )}
              </div>
              
              {selectedDocument.tags.length > 0 && (
                <div>
                  <span className="text-gray-500 text-sm">Tags:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedDocument.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="bg-purple-600/20 text-purple-300 text-xs px-2 py-1 rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};