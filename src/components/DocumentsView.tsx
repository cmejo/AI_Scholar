import React, { useState } from 'react';
import { 
  Upload, FileText, Search, Filter, Download, Trash2, 
  Eye, AlertCircle, CheckCircle, Clock, Plus 
} from 'lucide-react';

interface Document {
  id: string;
  name: string;
  size: string;
  uploadDate: Date;
  status: 'processing' | 'ready' | 'error';
  type: string;
  description?: string;
}

const DocumentsView: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([
    {
      id: '1',
      name: 'Research_Paper_AI_Ethics.pdf',
      size: '2.4 MB',
      uploadDate: new Date('2024-01-15'),
      status: 'ready',
      type: 'PDF',
      description: 'Comprehensive study on AI ethics and responsible AI development'
    },
    {
      id: '2',
      name: 'Financial_Analysis_Q4.xlsx',
      size: '1.8 MB',
      uploadDate: new Date('2024-01-10'),
      status: 'ready',
      type: 'Excel',
      description: 'Quarterly financial analysis and market trends'
    },
    {
      id: '3',
      name: 'Machine_Learning_Dataset.csv',
      size: '15.2 MB',
      uploadDate: new Date('2024-01-08'),
      status: 'processing',
      type: 'CSV',
      description: 'Large dataset for machine learning model training'
    }
  ]);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const handleFileUpload = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    
    setIsUploading(true);
    setUploadProgress(0);
    
    // Simulate upload progress
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsUploading(false);
          
          // Add new document to list
          const file = files[0];
          const newDoc: Document = {
            id: Date.now().toString(),
            name: file.name,
            size: `${(file.size / 1024 / 1024).toFixed(1)} MB`,
            uploadDate: new Date(),
            status: 'processing',
            type: file.name.split('.').pop()?.toUpperCase() || 'Unknown'
          };
          
          setDocuments(prev => [newDoc, ...prev]);
          return 100;
        }
        return prev + 10;
      });
    }, 200);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFileUpload(e.dataTransfer.files);
  };

  const getStatusIcon = (status: Document['status']) => {
    switch (status) {
      case 'ready':
        return <CheckCircle size={16} style={{ color: '#10b981' }} />;
      case 'processing':
        return <Clock size={16} style={{ color: '#f59e0b' }} />;
      case 'error':
        return <AlertCircle size={16} style={{ color: '#ef4444' }} />;
    }
  };

  const getStatusText = (status: Document['status']) => {
    switch (status) {
      case 'ready': return 'Ready';
      case 'processing': return 'Processing';
      case 'error': return 'Error';
    }
  };

  const filteredDocuments = documents.filter(doc =>
    doc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div style={{
      padding: '24px',
      height: '100%',
      overflow: 'auto'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px'
      }}>
        <div>
          <h2 style={{
            color: 'white',
            margin: 0,
            fontSize: '24px',
            fontWeight: '600'
          }}>
            Document Library
          </h2>
          <p style={{
            color: '#9ca3af',
            margin: '4px 0 0 0',
            fontSize: '14px'
          }}>
            Upload and manage your research documents
          </p>
        </div>
        
        <label style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '12px 20px',
          background: 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)',
          border: 'none',
          borderRadius: '8px',
          color: 'white',
          cursor: 'pointer',
          fontSize: '14px',
          fontWeight: '500'
        }}>
          <Plus size={16} />
          Upload Document
          <input
            type="file"
            multiple
            onChange={(e) => handleFileUpload(e.target.files)}
            style={{ display: 'none' }}
            accept=".pdf,.doc,.docx,.txt,.csv,.xlsx,.xls"
          />
        </label>
      </div>

      {/* Search and Filters */}
      <div style={{
        display: 'flex',
        gap: '12px',
        marginBottom: '24px'
      }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Search 
            size={16} 
            style={{
              position: 'absolute',
              left: '12px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: '#9ca3af'
            }}
          />
          <input
            type="text"
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '12px 12px 12px 40px',
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '8px',
              color: 'white',
              fontSize: '14px',
              outline: 'none'
            }}
          />
        </div>
        
        <button style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '12px 16px',
          background: 'rgba(255,255,255,0.1)',
          border: '1px solid rgba(255,255,255,0.2)',
          borderRadius: '8px',
          color: 'white',
          cursor: 'pointer',
          fontSize: '14px'
        }}>
          <Filter size={16} />
          Filter
        </button>
      </div>

      {/* Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${dragOver ? '#60a5fa' : 'rgba(255,255,255,0.2)'}`,
          borderRadius: '12px',
          padding: '40px',
          textAlign: 'center',
          marginBottom: '24px',
          background: dragOver ? 'rgba(96, 165, 250, 0.1)' : 'rgba(255,255,255,0.05)',
          transition: 'all 0.2s ease'
        }}
      >
        <Upload size={32} style={{ color: '#9ca3af', marginBottom: '12px' }} />
        <p style={{ color: 'white', margin: '0 0 8px 0', fontSize: '16px', fontWeight: '500' }}>
          Drag and drop files here
        </p>
        <p style={{ color: '#9ca3af', margin: 0, fontSize: '14px' }}>
          or click "Upload Document" to browse files
        </p>
        
        {isUploading && (
          <div style={{ marginTop: '16px' }}>
            <div style={{
              width: '100%',
              height: '4px',
              background: 'rgba(255,255,255,0.2)',
              borderRadius: '2px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${uploadProgress}%`,
                height: '100%',
                background: 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)',
                transition: 'width 0.2s ease'
              }} />
            </div>
            <p style={{ color: '#60a5fa', margin: '8px 0 0 0', fontSize: '14px' }}>
              Uploading... {uploadProgress}%
            </p>
          </div>
        )}
      </div>

      {/* Documents List */}
      <div style={{
        background: 'rgba(255,255,255,0.05)',
        borderRadius: '12px',
        overflow: 'hidden'
      }}>
        {filteredDocuments.length === 0 ? (
          <div style={{
            padding: '40px',
            textAlign: 'center',
            color: '#9ca3af'
          }}>
            <FileText size={32} style={{ marginBottom: '12px' }} />
            <p style={{ margin: 0, fontSize: '16px' }}>
              {searchQuery ? 'No documents match your search' : 'No documents uploaded yet'}
            </p>
          </div>
        ) : (
          filteredDocuments.map((doc, index) => (
            <div
              key={doc.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '16px 20px',
                borderBottom: index < filteredDocuments.length - 1 ? '1px solid rgba(255,255,255,0.1)' : 'none',
                transition: 'background-color 0.2s ease'
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
              onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
            >
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #34d399 0%, #10b981 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: '16px'
              }}>
                <FileText size={20} style={{ color: 'white' }} />
              </div>
              
              <div style={{ flex: 1 }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  marginBottom: '4px'
                }}>
                  <h3 style={{
                    color: 'white',
                    margin: 0,
                    fontSize: '14px',
                    fontWeight: '500'
                  }}>
                    {doc.name}
                  </h3>
                  {getStatusIcon(doc.status)}
                  <span style={{
                    fontSize: '12px',
                    color: '#9ca3af'
                  }}>
                    {getStatusText(doc.status)}
                  </span>
                </div>
                
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '16px',
                  fontSize: '12px',
                  color: '#9ca3af'
                }}>
                  <span>{doc.type}</span>
                  <span>{doc.size}</span>
                  <span>{doc.uploadDate.toLocaleDateString()}</span>
                </div>
                
                {doc.description && (
                  <p style={{
                    margin: '4px 0 0 0',
                    fontSize: '12px',
                    color: '#6b7280'
                  }}>
                    {doc.description}
                  </p>
                )}
              </div>
              
              <div style={{
                display: 'flex',
                gap: '8px'
              }}>
                <button style={{
                  padding: '8px',
                  background: 'rgba(255,255,255,0.1)',
                  border: 'none',
                  borderRadius: '6px',
                  color: '#9ca3af',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}>
                  <Eye size={16} />
                </button>
                
                <button style={{
                  padding: '8px',
                  background: 'rgba(255,255,255,0.1)',
                  border: 'none',
                  borderRadius: '6px',
                  color: '#9ca3af',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}>
                  <Download size={16} />
                </button>
                
                <button style={{
                  padding: '8px',
                  background: 'rgba(255,255,255,0.1)',
                  border: 'none',
                  borderRadius: '6px',
                  color: '#9ca3af',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}>
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default DocumentsView;