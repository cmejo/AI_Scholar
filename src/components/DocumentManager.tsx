import React, { useState } from 'react';
import { Upload, FileText, Trash2, Eye, Download, Search } from 'lucide-react';
import { useDocument } from '../contexts/DocumentContext';

export const DocumentManager: React.FC = () => {
  const { documents, uploadDocument, deleteDocument, searchDocuments } = useDocument();
  const [searchQuery, setSearchQuery] = useState('');
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const files = Array.from(e.dataTransfer.files);
    files.forEach(file => {
      if (file.type === 'application/pdf' || file.type === 'text/plain') {
        uploadDocument(file);
      }
    });
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    files.forEach(file => uploadDocument(file));
  };

  const filteredDocuments = searchQuery 
    ? searchDocuments(searchQuery)
    : documents;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-6 border-b border-gray-700">
        <h2 className="text-2xl font-bold mb-4">Document Manager</h2>
        
        {/* Search */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-gray-800 border border-gray-600 rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Upload Area */}
        <div
          className={`
            border-2 border-dashed rounded-lg p-6 text-center transition-colors
            ${dragActive 
              ? 'border-blue-500 bg-blue-500/10' 
              : 'border-gray-600 hover:border-gray-500'
            }
          `}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <Upload className="mx-auto mb-4 text-gray-400" size={48} />
          <p className="text-lg font-medium mb-2">Upload Documents</p>
          <p className="text-gray-400 mb-4">
            Drag and drop PDF or TXT files here, or click to browse
          </p>
          <label className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg cursor-pointer transition-colors">
            <span>Choose Files</span>
            <input
              type="file"
              multiple
              accept=".pdf,.txt"
              onChange={handleFileInput}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* Documents List */}
      <div className="flex-1 overflow-y-auto p-6">
        {filteredDocuments.length === 0 ? (
          <div className="text-center text-gray-500 py-12">
            <FileText size={48} className="mx-auto mb-4 text-gray-600" />
            <p className="text-lg">No documents uploaded yet</p>
            <p className="text-sm">Upload some documents to get started with RAG</p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredDocuments.map((doc) => (
              <div
                key={doc.id}
                className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-gray-600 transition-colors"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <FileText className="text-emerald-400 flex-shrink-0" size={20} />
                    <h3 className="font-medium text-sm truncate">{doc.name}</h3>
                  </div>
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() => {/* View document */}}
                      className="p-1 hover:bg-gray-700 rounded transition-colors"
                    >
                      <Eye size={16} />
                    </button>
                    <button
                      onClick={() => deleteDocument(doc.id)}
                      className="p-1 hover:bg-gray-700 rounded transition-colors text-red-400 hover:text-red-300"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
                
                <div className="space-y-2 text-xs text-gray-400">
                  <div className="flex justify-between">
                    <span>Size:</span>
                    <span>{(doc.size / 1024).toFixed(1)} KB</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Type:</span>
                    <span>{doc.type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Status:</span>
                    <span className={`
                      px-2 py-1 rounded text-xs
                      ${doc.status === 'processed' 
                        ? 'bg-emerald-600 text-white' 
                        : doc.status === 'processing'
                        ? 'bg-yellow-600 text-white'
                        : 'bg-red-600 text-white'
                      }
                    `}>
                      {doc.status}
                    </span>
                  </div>
                  {doc.chunks && (
                    <div className="flex justify-between">
                      <span>Chunks:</span>
                      <span>{doc.chunks}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};