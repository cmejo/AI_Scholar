import { ExternalLink, Eye, FileText, Loader2, Quote, Send, User } from 'lucide-react';
import React, { useEffect, useRef, useState } from 'react';
import { DocumentSource } from '../types/ui';
import { citationAwareRetriever, ExpandableCitation } from '../utils/citationAwareRetrieval';
import { PDFPreviewOverlay } from './PDFPreviewOverlay';

export const CitationAwareChat: React.FC = () => {
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [selectedCitation, setSelectedCitation] = useState<ExpandableCitation | null>(null);
  const [showPDFPreview, setShowPDFPreview] = useState(false);
  const [previewDocument, setPreviewDocument] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');
    setIsTyping(true);

    // Add user message
    const newUserMessage = {
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newUserMessage]);

    try {
      // Get citation-aware response
      const citationResult = await citationAwareRetriever.retrieveWithCitations(userMessage);
      
      // Create assistant message with citations
      const assistantMessage = {
        role: 'assistant',
        content: citationResult.content,
        timestamp: new Date(),
        citations: citationResult.citations,
        sources: citationResult.sources,
        expandableCitations: citationResult.expandableCitations
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error getting citation-aware response:', error);
      
      const errorMessage = {
        role: 'assistant',
        content: 'I apologize, but I encountered an error while processing your request. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleCitationClick = (citation: ExpandableCitation) => {
    setSelectedCitation(citation);
  };

  const handleViewInPDF = (source: DocumentSource) => {
    setPreviewDocument({
      id: source.id,
      name: source.documentName,
      highlightedText: source.highlightedText,
      pageNumber: source.pageNumber
    });
    setShowPDFPreview(true);
  };

  const renderMessageWithCitations = (content: string, expandableCitations: ExpandableCitation[]) => {
    let renderedContent = content;
    
    // Replace citation markers with clickable elements
    expandableCitations.forEach((citation, index) => {
      const citationRegex = new RegExp(`\\[Source ${index + 1}[^\\]]*\\]`, 'g');
      renderedContent = renderedContent.replace(citationRegex, (match) => {
        return `<span class="citation-marker" data-citation-id="${citation.id}">${match}</span>`;
      });
    });

    return (
      <div 
        dangerouslySetInnerHTML={{ __html: renderedContent }}
        onClick={(e) => {
          const target = e.target as HTMLElement;
          if (target.classList.contains('citation-marker')) {
            const citationId = target.getAttribute('data-citation-id');
            const citation = expandableCitations.find(c => c.id === citationId);
            if (citation) handleCitationClick(citation);
          }
        }}
      />
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-gray-700 p-4">
        <div className="flex items-center space-x-3">
          <Quote className="text-blue-400" size={24} />
          <div>
            <h2 className="text-lg font-semibold">Citation-Aware Chat</h2>
            <p className="text-sm text-gray-400">Precise source linking with expandable citations</p>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Quote size={48} className="mb-4 text-blue-600" />
            <h3 className="text-xl font-semibold mb-2">Citation-Aware Assistant</h3>
            <p className="text-center max-w-md">
              Ask me anything and I'll provide answers with precise citations and source linking.
              Click on citations to see detailed source information.
            </p>
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`flex max-w-[85%] ${
                    message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                  } items-start space-x-2`}
                >
                  <div className={`
                    w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                    ${message.role === 'user' 
                      ? 'bg-blue-600 ml-2' 
                      : 'bg-gradient-to-br from-blue-600 to-purple-600 mr-2'
                    }
                  `}>
                    {message.role === 'user' ? (
                      <User size={16} />
                    ) : (
                      <Quote size={16} />
                    )}
                  </div>
                  
                  <div className={`
                    px-4 py-3 rounded-2xl
                    ${message.role === 'user' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-800 text-gray-100 border border-gray-700'
                    }
                  `}>
                    {message.role === 'user' ? (
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    ) : (
                      <>
                        {message.expandableCitations ? (
                          renderMessageWithCitations(message.content, message.expandableCitations)
                        ) : (
                          <p className="whitespace-pre-wrap">{message.content}</p>
                        )}
                        
                        {/* Expandable Citations */}
                        {message.expandableCitations && message.expandableCitations.length > 0 && (
                          <div className="mt-4 pt-3 border-t border-gray-600">
                            <div className="flex items-center space-x-1 text-xs text-gray-400 mb-2">
                              <FileText size={12} />
                              <span>Expandable Citations:</span>
                            </div>
                            <div className="space-y-2">
                              {message.expandableCitations.map((citation: ExpandableCitation, idx: number) => (
                                <div
                                  key={idx}
                                  className="bg-gray-700 rounded-lg p-3 cursor-pointer hover:bg-gray-600 transition-colors"
                                  onClick={() => handleCitationClick(citation)}
                                >
                                  <div className="flex items-center justify-between">
                                    <span className="text-blue-400 text-sm font-medium">
                                      {citation.inlineText}
                                    </span>
                                    <ExternalLink size={12} className="text-gray-400" />
                                  </div>
                                  <p className="text-xs text-gray-300 mt-1 truncate">
                                    {citation.sourceSnippet}
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Source References */}
                        {message.sources && message.sources.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-gray-600">
                            <div className="flex items-center space-x-1 text-xs text-gray-400 mb-2">
                              <FileText size={12} />
                              <span>Source References:</span>
                            </div>
                            {message.sources.map((source: DocumentSource, idx: number) => (
                              <div key={idx} className="text-xs text-gray-300 mb-2 flex items-center justify-between">
                                <div className="flex-1">
                                  <span className="font-medium">📄 {source.documentName}</span>
                                  <span className="text-gray-400 ml-2">(p. {source.pageNumber})</span>
                                  <div className="text-gray-400 mt-1 text-xs">
                                    Relevance: {(source.relevanceScore * 100).toFixed(0)}%
                                  </div>
                                </div>
                                <button
                                  onClick={() => handleViewInPDF(source)}
                                  className="ml-2 p-1 hover:bg-gray-600 rounded transition-colors"
                                >
                                  <Eye size={12} />
                                </button>
                              </div>
                            ))}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {isTyping && (
              <div className="flex justify-start">
                <div className="flex items-start space-x-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center">
                    <Quote size={16} />
                  </div>
                  <div className="bg-gray-800 border border-gray-700 px-4 py-3 rounded-2xl">
                    <div className="flex items-center space-x-2">
                      <Loader2 size={16} className="animate-spin text-blue-400" />
                      <span className="text-sm text-gray-400">
                        Analyzing sources and generating citations...
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-700 p-4">
        <form onSubmit={handleSubmit} className="flex space-x-4">
          <div className="flex-1 relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me anything - I'll provide precise citations..."
              className="w-full bg-gray-800 border border-gray-600 rounded-xl px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isTyping}
            />
            <button
              type="submit"
              disabled={!input.trim() || isTyping}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send size={18} />
            </button>
          </div>
        </form>
        
        <div className="mt-2 text-xs text-gray-500 text-center">
          Enhanced with precise phrase-level citations and expandable source references
        </div>
      </div>

      {/* Citation Detail Modal */}
      {selectedCitation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Citation Details</h3>
              <button
                onClick={() => setSelectedCitation(null)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-gray-300 mb-2">Full Citation:</h4>
                <p className="text-white bg-gray-700 p-3 rounded-lg">
                  {selectedCitation.fullCitation}
                </p>
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-300 mb-2">Source Snippet:</h4>
                <p className="text-gray-300 bg-gray-700 p-3 rounded-lg">
                  {selectedCitation.sourceSnippet}
                </p>
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-300 mb-2">Document Preview:</h4>
                <div className="bg-gray-700 p-3 rounded-lg">
                  <h5 className="text-white font-medium">{selectedCitation.documentPreview.title}</h5>
                  <p className="text-gray-400 text-sm">
                    Authors: {selectedCitation.documentPreview.authors.join(', ')}
                  </p>
                  <p className="text-gray-400 text-sm">Year: {selectedCitation.documentPreview.year}</p>
                  <p className="text-gray-300 text-sm mt-2">
                    {selectedCitation.documentPreview.abstract}
                  </p>
                </div>
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={() => {
                    setPreviewDocument({
                      id: selectedCitation.id,
                      name: selectedCitation.documentPreview.title,
                      highlightedText: selectedCitation.sourceSnippet,
                      pageNumber: 1
                    });
                    setShowPDFPreview(true);
                    setSelectedCitation(null);
                  }}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2"
                >
                  <Eye size={16} />
                  <span>View in PDF</span>
                </button>
                <button
                  onClick={() => setSelectedCitation(null)}
                  className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded-lg transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* PDF Preview Overlay */}
      {showPDFPreview && previewDocument && (
        <PDFPreviewOverlay
          documentId={previewDocument.id}
          documentName={previewDocument.name}
          highlightedText={previewDocument.highlightedText}
          pageNumber={previewDocument.pageNumber}
          isVisible={showPDFPreview}
          onClose={() => setShowPDFPreview(false)}
        />
      )}
    </div>
  );
};