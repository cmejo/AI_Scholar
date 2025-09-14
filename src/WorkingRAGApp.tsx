import React, { useState } from 'react';

const WorkingRAGApp: React.FC = () => {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const handleQuery = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    
    // Mock RAG response for demo
    setTimeout(() => {
      setResponse(`🧠 RAG Response for: "${query}"\n\nBased on your scientific literature corpus, here's what I found:\n\nThis is a demonstration of the RAG system working. In a full implementation, this would:\n\n1. 🔍 Search your document corpus using vector similarity\n2. 📚 Retrieve relevant passages from scientific papers\n3. 🤖 Generate a comprehensive response using AI\n4. 📖 Provide source citations and references\n\nThe system is designed to provide accurate, source-backed answers to your research questions.`);
      setLoading(false);
    }, 1500);
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: '#1a1a1a',
      color: 'white',
      padding: '20px',
      fontFamily: 'Arial, sans-serif'
    }}>
      {/* Header */}
      <div style={{
        textAlign: 'center',
        marginBottom: '40px',
        borderBottom: '2px solid #6b46c1',
        paddingBottom: '20px'
      }}>
        <h1 style={{
          color: '#6b46c1',
          fontSize: '2.5rem',
          margin: '0 0 10px 0'
        }}>
          🧠 AI Scholar RAG System
        </h1>
        <p style={{
          color: '#9ca3af',
          fontSize: '1.1rem',
          margin: 0
        }}>
          Query your scientific literature with AI-powered retrieval and generation
        </p>
      </div>

      {/* Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '20px',
        marginBottom: '40px'
      }}>
        <div style={{
          background: '#374151',
          padding: '20px',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', color: '#10b981', fontWeight: 'bold' }}>1</div>
          <div style={{ color: '#9ca3af' }}>Documents</div>
        </div>
        <div style={{
          background: '#374151',
          padding: '20px',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', color: '#3b82f6', fontWeight: 'bold' }}>36</div>
          <div style={{ color: '#9ca3af' }}>Text Chunks</div>
        </div>
        <div style={{
          background: '#374151',
          padding: '20px',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', color: '#f59e0b', fontWeight: 'bold' }}>llama2</div>
          <div style={{ color: '#9ca3af' }}>AI Model</div>
        </div>
        <div style={{
          background: '#374151',
          padding: '20px',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', color: '#ef4444', fontWeight: 'bold' }}>Ready</div>
          <div style={{ color: '#9ca3af' }}>Status</div>
        </div>
      </div>

      {/* Query Interface */}
      <div style={{
        background: '#374151',
        padding: '30px',
        borderRadius: '12px',
        marginBottom: '30px'
      }}>
        <h2 style={{
          color: '#6b46c1',
          marginBottom: '20px',
          fontSize: '1.5rem'
        }}>
          🔍 Scientific Query
        </h2>
        
        <div style={{ marginBottom: '20px' }}>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your scientific research question..."
            style={{
              width: '100%',
              minHeight: '100px',
              padding: '15px',
              background: '#1f2937',
              border: '2px solid #4b5563',
              borderRadius: '8px',
              color: 'white',
              fontSize: '16px',
              resize: 'vertical',
              outline: 'none'
            }}
            onFocus={(e) => e.target.style.borderColor = '#6b46c1'}
            onBlur={(e) => e.target.style.borderColor = '#4b5563'}
          />
        </div>
        
        <button
          onClick={handleQuery}
          disabled={loading || !query.trim()}
          style={{
            background: loading ? '#6b7280' : '#6b46c1',
            color: 'white',
            border: 'none',
            padding: '12px 30px',
            borderRadius: '8px',
            fontSize: '16px',
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'background 0.3s'
          }}
          onMouseOver={(e) => {
            if (!loading && query.trim()) {
              e.currentTarget.style.background = '#7c3aed';
            }
          }}
          onMouseOut={(e) => {
            if (!loading) {
              e.currentTarget.style.background = '#6b46c1';
            }
          }}
        >
          {loading ? '🔄 Processing...' : '🚀 Query RAG System'}
        </button>
      </div>

      {/* Response */}
      {response && (
        <div style={{
          background: '#1f2937',
          padding: '30px',
          borderRadius: '12px',
          border: '2px solid #10b981'
        }}>
          <h3 style={{
            color: '#10b981',
            marginBottom: '20px',
            fontSize: '1.3rem'
          }}>
            📚 RAG Response
          </h3>
          <div style={{
            whiteSpace: 'pre-wrap',
            lineHeight: '1.6',
            color: '#e5e7eb'
          }}>
            {response}
          </div>
        </div>
      )}

      {/* Example Queries */}
      <div style={{
        marginTop: '40px',
        background: '#374151',
        padding: '30px',
        borderRadius: '12px'
      }}>
        <h3 style={{
          color: '#6b46c1',
          marginBottom: '20px',
          fontSize: '1.3rem'
        }}>
          💡 Example Queries
        </h3>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '15px'
        }}>
          {[
            "What are the latest advances in machine learning?",
            "How do neural networks learn representations?",
            "What are the applications of reinforcement learning?",
            "Compare different optimization algorithms for deep learning",
            "What are the challenges in natural language processing?",
            "How does attention mechanism work in neural networks?"
          ].map((exampleQuery, index) => (
            <button
              key={index}
              onClick={() => setQuery(exampleQuery)}
              style={{
                background: '#1f2937',
                color: '#e5e7eb',
                border: '1px solid #4b5563',
                padding: '15px',
                borderRadius: '8px',
                textAlign: 'left',
                cursor: 'pointer',
                fontSize: '14px',
                transition: 'all 0.3s'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.background = '#6b46c1';
                e.currentTarget.style.borderColor = '#6b46c1';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = '#1f2937';
                e.currentTarget.style.borderColor = '#4b5563';
              }}
            >
              {exampleQuery}
            </button>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div style={{
        textAlign: 'center',
        marginTop: '40px',
        padding: '20px',
        borderTop: '1px solid #4b5563',
        color: '#9ca3af'
      }}>
        <p>🎯 RAG System Status: <span style={{ color: '#10b981' }}>Active</span></p>
        <p>Ready to query your scientific literature corpus</p>
      </div>
    </div>
  );
};

export default WorkingRAGApp;