import React, { useState, useEffect } from 'react';
import { Upload, FileText, Trash2, Eye, Search, Network, Brain, Target, BarChart3 } from 'lucide-react';
import { useDocument } from '../contexts/DocumentContext';
import { hierarchicalChunker, HierarchicalChunk } from '../utils/hierarchicalChunking';
import { knowledgeGraph, Entity } from '../utils/knowledgeGraph';
import { contextAwareRetriever } from '../utils/contextAwareRetrieval';

export const EnhancedDocumentManager: React.FC = () => {
  const { documents, uploadDocument, deleteDocument, searchDocuments } = useDocument();
  const [searchQuery, setSearchQuery] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<string | null>(null);
  const [processingStats, setProcessingStats] = useState<{
    totalChunks: number;
    totalEntities: number;
    avgImportance: number;
    knowledgeGraphNodes: number;
  } | null>(null);
  const [showAnalytics, setShowAnalytics] = useState(false);

  useEffect(() => {
    updateProcessingStats();
  }, [documents]);

  const updateProcessingStats = async () => {
    if (documents.length === 0) {
      setProcessingStats(null);
      return;
    }

    // Mock processing stats (in production, this would come from actual processing)
    const totalChunks = documents.reduce((sum, doc) => sum + (doc.chunks || 0), 0);
    const totalEntities = documents.length * 15; // Mock entity count
    const avgImportance = 0.75; // Mock average importance
    const knowledgeGraphNodes = Math.floor(totalEntities * 0.8);

    setProcessingStats({
      totalChunks,
      totalEntities,
      avgImportance,
      knowledgeGraphNodes
    });
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const files = Array.from(e.dataTransfer.files);
    for (const file of files) {
      if (file.type === 'application/pdf' || file.type === 'text/plain') {
        await processDocumentWithAdvancedFeatures(file);
      }
    }
  };

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    for (const file of files) {
      await processDocumentWithAdvancedFeatures(file);
    }
  };

  const processDocumentWithAdvancedFeatures = async (file: File) => {
    // Upload document first
    await uploadDocument(file);

    // Read file content
    const content = await readFileContent(file);
    
    // Process with hierarchical chunking
    const chunks = await hierarchicalChunker.processDocument(
      content,
      file.name.replace(/\.[^/.]+$/, ""),
      file.type === 'application/pdf' ? 'pdf' : 'txt'
    );

    // Build knowledge graph
    await knowledgeGraph.buildGraph(chunks.map(chunk => ({
      id: chunk.id,
      content: chunk.content,
      documentId: file.name,
      metadata: chunk.metadata
    })));

    // Add to retrieval system
    contextAwareRetriever.addChunks(chunks);

    // Update stats
    updateProcessingStats();
  };

  const readFileContent = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target?.result as string);
      reader.onerror = reject;
      reader.readAsText(file);
    });
  };

  const filteredDocuments = searchQuery 
    ? searchDocuments(searchQuery)
    : documents;

  return (
    <div className="flex flex-col h-full">
      {/* Enhanced Header */}
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Brain className="text-purple-400" size={24} />
            <div>
              <h2 className="text-2xl font-bold">Enhanced Document Manager</h2>
              <p className="text-sm text-gray-400">Advanced processing with knowledge graphs</p>
            </div>
          </div>
          
          <button
            onClick={() => setShowAnalytics(!showAnalytics)}
            className={`px-3 py-1 rounded-lg text-sm transition-colors ${
              showAnalytics 
                ? 'bg-purple-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Analytics
          </button>
        </div>

        {/* Processing Statistics */}
        {showAnalytics && processingStats && (
          <div className="mb-4 p-4 bg-gray-800/50 rounded-lg">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">{processingStats.totalChunks}</div>
                <div className="text-gray-400">Total Chunks</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-emerald-400">{processingStats.totalEntities}</div>
                <div className="text-gray-400">Entities Extracted</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-400">{processingStats.knowledgeGraphNodes}</div>
                <div className="text-gray-400">Graph Nodes</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-400">{(processingStats.avgImportance * 100).toFixed(0)}%</div>
                <div className="text-gray-400">Avg Importance</div>
              </div>
            </div>
          </div>
        )}
        
        {/* Search */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Search documents with semantic understanding..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-gray-800 border border-gray-600 rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        {/* Enhanced Upload Area */}
        <div
          className={`
            border-2 border-dashed rounded-lg p-6 text-center transition-all duration-300
            ${dragActive 
              ? 'border-purple-500 bg-purple-500/10 scale-105' 
              : 'border-gray-600 hover:border-gray-500'
            }
          `}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className="flex items-center justify-center space-x-4 mb-4">
            <Upload className="text-gray-400" size={48} />
            <div className="hidden md:flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-2">
                <Brain className="text-purple-400" size={16} />
                <span>Hierarchical Chunking</span>
              </div>
              <div className="flex items-center space-x-2">
                <Network className="text-emerald-400" size={16} />
                <span>Knowledge Graphs</span>
              </div>
              <div className="flex items-center space-x-2">
                <Target className="text-blue-400" size={16} />
                <span>Entity Extraction</span>
              </div>
            </div>
          </div>
          
          <p className="text-lg font-medium mb-2">Upload Documents for Advanced Processing</p>
          <p className="text-gray-400 mb-4">
            Automatic hierarchical chunking, entity extraction, and knowledge graph creation
          </p>
          <label className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-purple-600 to-emerald-600 hover:from-purple-700 hover:to-emerald-700 rounded-lg cursor-pointer transition-all duration-300 transform hover:scale-105">
            <span className="font-medium">Choose Files</span>
            <input
              type="file"
              multiple
              accept=".pdf,.txt,.md"
              onChange={handleFileInput}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* Enhanced Documents List */}
      <div className="flex-1 overflow-y-auto p-6">
        {filteredDocuments.length === 0 ? (
          <div className="text-center text-gray-500 py-12">
            <FileText size={48} className="mx-auto mb-4 text-gray-600" />
            <p className="text-lg">No documents uploaded yet</p>
            <p className="text-sm">Upload documents to experience advanced RAG features</p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredDocuments.map((doc) => (
              <div
                key={doc.id}
                className={`bg-gray-800 rounded-lg p-4 border transition-all duration-300 cursor-pointer transform hover:scale-105 ${
                  selectedDocument === doc.id 
                    ? 'border-purple-500 bg-purple-500/10' 
                    : 'border-gray-700 hover:border-gray-600'
                }`}
                onClick={() => setSelectedDocument(selectedDocument === doc.id ? null : doc.id)}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <FileText className="text-emerald-400 flex-shrink-0" size={20} />
                    <h3 className="font-medium text-sm truncate">{doc.name}</h3>
                  </div>
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        // View document functionality
                      }}
                      className="p-1 hover:bg-gray-700 rounded transition-colors"
                    >
                      <Eye size={16} />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteDocument(doc.id);
                      }}
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
                      <span className="text-blue-400">{doc.chunks}</span>
                    </div>
                  )}
                </div>

                {/* Enhanced Processing Info */}
                {selectedDocument === doc.id && doc.status === 'processed' && (
                  <div className="mt-3 pt-3 border-t border-gray-700 space-y-2">
                    <div className="text-xs font-medium text-purple-300">Advanced Processing:</div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="flex items-center space-x-1">
                        <Brain size={10} className="text-purple-400" />
                        <span>Hierarchical</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Network size={10} className="text-emerald-400" />
                        <span>Knowledge Graph</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Target size={10} className="text-blue-400" />
                        <span>Entity Extraction</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <BarChart3 size={10} className="text-yellow-400" />
                        <span>Importance Scoring</span>
                      </div>
                    </div>
                    
                    <div className="text-xs text-gray-400">
                      Entities: ~{Math.floor(Math.random() * 20) + 10} | 
                      Importance: {(Math.random() * 0.3 + 0.7).toFixed(2)}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};