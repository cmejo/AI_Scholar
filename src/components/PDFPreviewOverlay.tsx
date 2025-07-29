import React, { useState, useRef, useEffect } from 'react';
import { Eye, ExternalLink, Search, Highlighter as Highlight, ZoomIn, ZoomOut } from 'lucide-react';

interface PDFPreviewOverlayProps {
  documentId: string;
  documentName: string;
  highlightedText: string;
  pageNumber: number;
  isVisible: boolean;
  onClose: () => void;
}

export const PDFPreviewOverlay: React.FC<PDFPreviewOverlayProps> = ({
  documentId,
  documentName,
  highlightedText,
  pageNumber,
  isVisible,
  onClose
}) => {
  const [zoomLevel, setZoomLevel] = useState(1.0);
  const [searchTerm, setSearchTerm] = useState('');
  const [highlights, setHighlights] = useState<string[]>([]);
  const previewRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (highlightedText) {
      setHighlights([highlightedText]);
      setSearchTerm(highlightedText);
    }
  }, [highlightedText]);

  const scrollToHighlight = () => {
    // In production, this would scroll to the actual highlighted text in the PDF
    if (previewRef.current) {
      const highlightElement = previewRef.current.querySelector('.highlight');
      if (highlightElement) {
        highlightElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  };

  const addHighlight = (text: string) => {
    if (text && !highlights.includes(text)) {
      setHighlights([...highlights, text]);
    }
  };

  const removeHighlight = (text: string) => {
    setHighlights(highlights.filter(h => h !== text));
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center">
      <div className="bg-gray-800 rounded-lg w-full max-w-6xl h-5/6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <div className="flex items-center space-x-3">
            <Eye className="text-blue-400" size={20} />
            <div>
              <h3 className="text-lg font-semibold text-white">{documentName}</h3>
              <p className="text-sm text-gray-400">Page {pageNumber}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search in document..."
                className="bg-gray-700 border border-gray-600 rounded-lg pl-10 pr-4 py-2 text-white text-sm"
              />
            </div>
            
            {/* Zoom Controls */}
            <button
              onClick={() => setZoomLevel(Math.max(0.5, zoomLevel - 0.1))}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <ZoomOut size={16} />
            </button>
            <span className="text-sm text-gray-400 min-w-[60px] text-center">
              {(zoomLevel * 100).toFixed(0)}%
            </span>
            <button
              onClick={() => setZoomLevel(Math.min(2.0, zoomLevel + 0.1))}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <ZoomIn size={16} />
            </button>
            
            {/* External Link */}
            <button
              onClick={() => window.open(`/documents/${documentId}`, '_blank')}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <ExternalLink size={16} />
            </button>
            
            {/* Close */}
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors text-red-400"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex flex-1 overflow-hidden">
          {/* PDF Viewer */}
          <div className="flex-1 overflow-auto bg-gray-900 p-4">
            <div
              ref={previewRef}
              className="bg-white rounded-lg shadow-lg mx-auto"
              style={{ 
                transform: `scale(${zoomLevel})`,
                transformOrigin: 'top center',
                width: '8.5in',
                minHeight: '11in',
                padding: '1in'
              }}
            >
              {/* Mock PDF Content */}
              <div className="space-y-4 text-black">
                <h1 className="text-2xl font-bold mb-4">Document Title</h1>
                
                <p className="text-sm text-gray-600 mb-6">
                  This is a mock PDF preview. In production, this would render the actual PDF content
                  using libraries like PDF.js or react-pdf.
                </p>
                
                <div className="space-y-4">
                  <p>
                    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor 
                    incididunt ut labore et dolore magna aliqua. 
                    <span 
                      className={`highlight ${highlights.includes(highlightedText) ? 'bg-yellow-300' : ''}`}
                      onClick={() => addHighlight(highlightedText)}
                    >
                      {highlightedText}
                    </span>
                    Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.
                  </p>
                  
                  <p>
                    Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore 
                    eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, 
                    sunt in culpa qui officia deserunt mollit anim id est laborum.
                  </p>
                  
                  <p>
                    Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium 
                    doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore 
                    veritatis et quasi architecto beatae vitae dicta sunt explicabo.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="w-80 border-l border-gray-700 bg-gray-800 p-4 overflow-y-auto">
            <h4 className="text-lg font-semibold text-white mb-4">Context & Highlights</h4>
            
            {/* Current Highlight */}
            <div className="mb-6">
              <h5 className="text-sm font-medium text-gray-300 mb-2">Current Selection:</h5>
              <div className="bg-yellow-500/20 border border-yellow-500/30 rounded-lg p-3">
                <p className="text-sm text-yellow-200">{highlightedText}</p>
                <button
                  onClick={scrollToHighlight}
                  className="mt-2 text-xs text-yellow-400 hover:text-yellow-300 flex items-center space-x-1"
                >
                  <Search size={12} />
                  <span>Scroll to highlight</span>
                </button>
              </div>
            </div>

            {/* All Highlights */}
            {highlights.length > 0 && (
              <div className="mb-6">
                <h5 className="text-sm font-medium text-gray-300 mb-2">All Highlights:</h5>
                <div className="space-y-2">
                  {highlights.map((highlight, index) => (
                    <div
                      key={index}
                      className="bg-gray-700 rounded-lg p-2 flex items-center justify-between"
                    >
                      <span className="text-sm text-gray-300 truncate flex-1">
                        {highlight}
                      </span>
                      <button
                        onClick={() => removeHighlight(highlight)}
                        className="text-red-400 hover:text-red-300 ml-2"
                      >
                        <Highlight size={12} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Document Info */}
            <div className="mb-6">
              <h5 className="text-sm font-medium text-gray-300 mb-2">Document Info:</h5>
              <div className="bg-gray-700 rounded-lg p-3 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Pages:</span>
                  <span className="text-white">24</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Size:</span>
                  <span className="text-white">2.4 MB</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Type:</span>
                  <span className="text-white">PDF</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Added:</span>
                  <span className="text-white">2 days ago</span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div>
              <h5 className="text-sm font-medium text-gray-300 mb-2">Quick Actions:</h5>
              <div className="space-y-2">
                <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-3 rounded-lg text-sm transition-colors">
                  Extract Text
                </button>
                <button className="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-2 px-3 rounded-lg text-sm transition-colors">
                  Generate Summary
                </button>
                <button className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 px-3 rounded-lg text-sm transition-colors">
                  Find Similar
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};