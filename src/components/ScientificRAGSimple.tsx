import React, { useState, useEffect } from 'react';
import { Loader2, Search, Upload, Database, Brain } from 'lucide-react';

interface QueryResponse {
  query: string;
  query_type: string;
  response: string;
  sources: Array<{
    source_id: number;
    relevance_score: number;
    section: string;
    document_id: string;
    text_preview: string;
    cited_in_response: boolean;
  }>;
  context_chunks_used: number;
  total_results_found: number;
  confidence_score: number;
  processing_time: number;
  model_used: string;
  timestamp: string;
}

interface CorpusStats {
  total_documents: number;
  total_chunks: number;
  total_embeddings: number;
  average_document_length: number;
  most_common_sections: string[];
  processing_quality_distribution: Record<string, number>;
  last_updated: string;
}

const ScientificRAGSimple: React.FC = () => {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [corpusStats, setCorpusStats] = useState<CorpusStats | null>(null);
  const [selectedModel, setSelectedModel] = useState('llama2');
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [processingDataset, setProcessingDataset] = useState(false);

  // Load corpus statistics and available models on component mount
  useEffect(() => {
    loadCorpusStats();
    loadAvailableModels();
  }, []);

  const loadCorpusStats = async () => {
    try {
      const response = await fetch('/api/rag/corpus/stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const stats = await response.json();
        setCorpusStats(stats);
      }
    } catch (error) {
      console.error('Failed to load corpus stats:', error);
    }
  };

  const loadAvailableModels = async () => {
    try {
      const response = await fetch('/api/rag/models', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAvailableModels(data.available_models || []);
      }
    } catch (error) {
      console.error('Failed to load available models:', error);
    }
  };

  const handleQuery = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setResponse(null);

    try {
      const response = await fetch('/api/rag/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          query: query.trim(),
          model: selectedModel,
          max_sources: 10
        })
      });

      if (response.ok) {
        const data = await response.json();
        setResponse(data);
      } else {
        const error = await response.json();
        console.error('Query failed:', error);
      }
    } catch (error) {
      console.error('Query request failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const processArxivDataset = async () => {
    setProcessingDataset(true);
    
    try {
      const response = await fetch('/api/rag/process-arxiv-dataset', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Dataset processing started:', data);
        alert(`Started processing ${data.total_files} files. Check the backend logs for progress.`);
        
        // Refresh stats after a delay
        setTimeout(loadCorpusStats, 5000);
      } else {
        const error = await response.json();
        console.error('Dataset processing failed:', error);
        alert('Failed to start dataset processing. Check the backend logs.');
      }
    } catch (error) {
      console.error('Dataset processing request failed:', error);
      alert('Failed to start dataset processing.');
    } finally {
      setProcessingDataset(false);
    }
  };

  const formatConfidenceScore = (score: number) => {
    if (score >= 0.8) return { text: 'High', color: 'bg-green-500' };
    if (score >= 0.6) return { text: 'Medium', color: 'bg-yellow-500' };
    return { text: 'Low', color: 'bg-red-500' };
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6 bg-gray-900 text-white min-h-screen">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-2">AI Scholar Scientific RAG</h1>
        <p className="text-gray-400">Query your scientific literature using AI-powered retrieval and generation</p>
      </div>

      {/* Corpus Statistics */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Database className="w-5 h-5" />
          Document Corpus Statistics
        </h2>
        {corpusStats ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">{corpusStats.total_documents}</div>
              <div className="text-sm text-gray-400">Documents</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">{corpusStats.total_chunks}</div>
              <div className="text-sm text-gray-400">Text Chunks</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-400">{corpusStats.total_embeddings}</div>
              <div className="text-sm text-gray-400">Embeddings</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-400">{Math.round(corpusStats.average_document_length)}</div>
              <div className="text-sm text-gray-400">Avg Length</div>
            </div>
          </div>
        ) : (
          <div className="text-center text-gray-500">Loading corpus statistics...</div>
        )}
        
        <div className="mt-4 flex gap-2">
          <button 
            onClick={processArxivDataset} 
            disabled={processingDataset}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg transition-colors flex items-center gap-2"
          >
            {processingDataset ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Process arXiv Dataset
              </>
            )}
          </button>
          <button 
            onClick={loadCorpusStats} 
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
          >
            Refresh Stats
          </button>
        </div>
      </div>

      {/* Query Interface */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Brain className="w-5 h-5" />
          Scientific Query
        </h2>
        <div className="space-y-4">
          <div className="flex gap-2">
            <select 
              value={selectedModel} 
              onChange={(e) => setSelectedModel(e.target.value)}
              className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white"
            >
              {availableModels.map(model => (
                <option key={model} value={model}>{model}</option>
              ))}
            </select>
          </div>
          
          <div className="flex gap-2">
            <input
              placeholder="Enter your scientific research question..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleQuery()}
              className="flex-1 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button 
              onClick={handleQuery} 
              disabled={loading || !query.trim()}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg transition-colors flex items-center gap-2"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Search className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Query Response */}
      {response && (
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">Response</h2>
            <div className="flex items-center gap-2">
              <span className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-sm">{response.query_type}</span>
              <span className={`px-2 py-1 text-white rounded text-sm ${formatConfidenceScore(response.confidence_score).color}`}>
                {formatConfidenceScore(response.confidence_score).text} Confidence
              </span>
            </div>
          </div>
          
          <div className="bg-gray-700 p-4 rounded-lg mb-4">
            <p className="whitespace-pre-wrap">{response.response}</p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
            <div>
              <span className="font-medium">Sources Used:</span> {response.context_chunks_used}
            </div>
            <div>
              <span className="font-medium">Total Found:</span> {response.total_results_found}
            </div>
            <div>
              <span className="font-medium">Processing Time:</span> {response.processing_time.toFixed(2)}s
            </div>
            <div>
              <span className="font-medium">Model:</span> {response.model_used}
            </div>
          </div>

          {/* Sources */}
          {response.sources && response.sources.length > 0 && (
            <div>
              <h4 className="font-medium mb-2">Sources:</h4>
              <div className="space-y-2">
                {response.sources.slice(0, 5).map((source, index) => (
                  <div key={index} className="border border-gray-600 rounded p-3 text-sm">
                    <div className="flex justify-between items-start mb-2">
                      <span className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs">{source.section}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-400">
                          Relevance: {(source.relevance_score * 100).toFixed(1)}%
                        </span>
                        {source.cited_in_response && (
                          <span className="px-2 py-1 bg-blue-600 text-white rounded text-xs">Cited</span>
                        )}
                      </div>
                    </div>
                    <p className="text-gray-300">{source.text_preview}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Example Queries */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">Example Queries</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {[
            "What are the latest developments in transformer architectures?",
            "How do neural networks learn representations?",
            "What are the applications of reinforcement learning?",
            "Compare different optimization algorithms for deep learning",
            "What are the challenges in natural language processing?",
            "How does attention mechanism work in neural networks?"
          ].map((exampleQuery, index) => (
            <button
              key={index}
              onClick={() => setQuery(exampleQuery)}
              className="text-left p-2 bg-gray-700 hover:bg-gray-600 text-gray-300 hover:text-white rounded-lg transition-colors text-sm"
            >
              {exampleQuery}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ScientificRAGSimple;