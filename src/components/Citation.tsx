import React, { useState } from 'react';
import { ExternalLink, FileText, Globe, CheckCircle, AlertTriangle, Info } from 'lucide-react';

interface Citation {
  id: string;
  title: string;
  url?: string;
  snippet: string;
  confidence: number;
  source: string;
}

interface CitationProps {
  citations: Citation[];
  className?: string;
}

interface CitationItemProps {
  citation: Citation;
  index: number;
}

const CitationItem: React.FC<CitationItemProps> = ({ citation, index }) => {
  const [showDetails, setShowDetails] = useState(false);

  const getConfidenceIcon = (confidence: number) => {
    if (confidence >= 0.8) return CheckCircle;
    if (confidence >= 0.6) return Info;
    return AlertTriangle;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-400';
    if (confidence >= 0.6) return 'text-blue-400';
    return 'text-yellow-400';
  };

  const getSourceIcon = (source: string) => {
    if (source.includes('wikipedia') || source.includes('wiki')) return Globe;
    if (source.includes('pdf') || source.includes('doc')) return FileText;
    return Globe;
  };

  const ConfidenceIcon = getConfidenceIcon(citation.confidence);
  const SourceIcon = getSourceIcon(citation.source);

  const handleCitationClick = () => {
    if (citation.url) {
      window.open(citation.url, '_blank', 'noopener,noreferrer');
    } else {
      setShowDetails(!showDetails);
    }
  };

  return (
    <div className="border border-gray-600 rounded-lg bg-gray-800/30 hover:bg-gray-800/50 transition-colors">
      {/* Citation Header */}
      <button
        onClick={handleCitationClick}
        className="w-full flex items-start space-x-3 p-3 text-left"
      >
        <div className="flex-shrink-0 mt-0.5">
          <span className="inline-flex items-center justify-center w-6 h-6 bg-purple-600 text-white text-xs font-medium rounded-full">
            {index + 1}
          </span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <h4 className="text-sm font-medium text-gray-200 line-clamp-2">
              {citation.title}
            </h4>
            {citation.url && (
              <ExternalLink className="w-4 h-4 text-gray-400 ml-2 flex-shrink-0" />
            )}
          </div>

          <div className="flex items-center space-x-2 mt-1">
            <SourceIcon className="w-3 h-3 text-gray-500" />
            <span className="text-xs text-gray-500 truncate">
              {citation.source}
            </span>
          </div>

          <div className="flex items-center space-x-2 mt-2">
            <ConfidenceIcon className={`w-3 h-3 ${getConfidenceColor(citation.confidence)}`} />
            <span className={`text-xs ${getConfidenceColor(citation.confidence)}`}>
              {Math.round(citation.confidence * 100)}% confidence
            </span>
          </div>
        </div>
      </button>

      {/* Citation Details (for non-URL citations) */}
      {showDetails && !citation.url && (
        <div className="border-t border-gray-600 p-3">
          <div className="bg-gray-900/50 rounded-md p-3">
            <h5 className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">
              Excerpt
            </h5>
            <p className="text-sm text-gray-300 leading-relaxed">
              {citation.snippet}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export const Citation: React.FC<CitationProps> = ({ citations, className = '' }) => {
  if (!citations || citations.length === 0) {
    return null;
  }

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex items-center space-x-2 mb-3">
        <CheckCircle className="w-4 h-4 text-blue-400" />
        <h3 className="text-sm font-medium text-gray-300">
          Sources ({citations.length})
        </h3>
      </div>

      <div className="space-y-2">
        {citations.map((citation, index) => (
          <CitationItem
            key={citation.id}
            citation={citation}
            index={index}
          />
        ))}
      </div>

      {/* Citation Info */}
      <div className="mt-3 p-2 bg-blue-900/20 border border-blue-800/30 rounded-md">
        <p className="text-xs text-blue-300">
          <Info className="w-3 h-3 inline mr-1" />
          Citations are provided to support the information above. Click to view sources.
        </p>
      </div>
    </div>
  );
};

export default Citation;