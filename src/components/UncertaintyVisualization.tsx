import React from 'react';
import { AlertTriangle, ChevronDown, ChevronRight, Info, TrendingUp, TrendingDown } from 'lucide-react';

interface UncertaintyFactor {
  factor: string;
  impact: number;
  explanation: string;
}

interface UncertaintyData {
  confidence: number;
  factors: UncertaintyFactor[];
}

interface UncertaintyVisualizationProps {
  uncertainty: UncertaintyData;
  isExpanded: boolean;
  onToggle: () => void;
}

export const UncertaintyVisualization: React.FC<UncertaintyVisualizationProps> = ({
  uncertainty,
  isExpanded,
  onToggle
}) => {
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-400';
    if (confidence >= 0.6) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getConfidenceBackground = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-400/20';
    if (confidence >= 0.6) return 'bg-yellow-400/20';
    return 'bg-red-400/20';
  };

  const getImpactIcon = (impact: number) => {
    if (impact >= 0.7) return <TrendingUp size={12} className="text-green-400" />;
    if (impact >= 0.4) return <Info size={12} className="text-yellow-400" />;
    return <TrendingDown size={12} className="text-red-400" />;
  };

  return (
    <div className="mt-3 pt-3 border-t border-gray-600">
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full text-left hover:bg-gray-700/50 rounded p-2 transition-colors"
      >
        <div className="flex items-center space-x-2">
          <AlertTriangle size={14} className={getConfidenceColor(uncertainty.confidence)} />
          <span className="text-sm font-medium">
            Confidence: {(uncertainty.confidence * 100).toFixed(0)}%
          </span>
          <div className={`px-2 py-1 rounded text-xs ${getConfidenceBackground(uncertainty.confidence)} ${getConfidenceColor(uncertainty.confidence)}`}>
            {uncertainty.confidence >= 0.8 ? 'High' : uncertainty.confidence >= 0.6 ? 'Medium' : 'Low'}
          </div>
        </div>
        {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
      </button>

      {/* Confidence Bar */}
      <div className="mt-2 mb-3">
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${
              uncertainty.confidence >= 0.8 
                ? 'bg-green-400' 
                : uncertainty.confidence >= 0.6 
                ? 'bg-yellow-400' 
                : 'bg-red-400'
            }`}
            style={{ width: `${uncertainty.confidence * 100}%` }}
          />
        </div>
      </div>

      {isExpanded && (
        <div className="space-y-3 mt-3">
          <div className="text-xs text-gray-400 mb-2">
            Uncertainty Factors Analysis:
          </div>
          
          {uncertainty.factors.map((factor, index) => (
            <div key={index} className="bg-gray-800/50 rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  {getImpactIcon(factor.impact)}
                  <span className="text-sm font-medium text-gray-200">
                    {factor.factor}
                  </span>
                </div>
                <span className="text-xs text-gray-400">
                  Impact: {(factor.impact * 100).toFixed(0)}%
                </span>
              </div>
              
              {/* Impact Bar */}
              <div className="w-full bg-gray-700 rounded-full h-1.5 mb-2">
                <div
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    factor.impact >= 0.7 
                      ? 'bg-green-400' 
                      : factor.impact >= 0.4 
                      ? 'bg-yellow-400' 
                      : 'bg-red-400'
                  }`}
                  style={{ width: `${factor.impact * 100}%` }}
                />
              </div>
              
              <p className="text-xs text-gray-300">
                {factor.explanation}
              </p>
            </div>
          ))}

          {/* Overall Assessment */}
          <div className="bg-gray-800/30 rounded p-3 border-l-4 border-purple-400">
            <div className="text-xs font-medium text-purple-300 mb-1">
              Overall Assessment
            </div>
            <p className="text-xs text-gray-300">
              {uncertainty.confidence >= 0.8 
                ? 'High confidence response based on strong evidence and reliable sources.'
                : uncertainty.confidence >= 0.6
                ? 'Moderate confidence response. Some uncertainty factors may affect accuracy.'
                : 'Lower confidence response. Consider verifying information from additional sources.'
              }
            </p>
          </div>

          {/* Recommendations */}
          <div className="bg-blue-900/20 rounded p-3 border-l-4 border-blue-400">
            <div className="text-xs font-medium text-blue-300 mb-1">
              Recommendations
            </div>
            <ul className="text-xs text-gray-300 space-y-1">
              {uncertainty.confidence < 0.8 && (
                <li>• Consider asking for more specific information</li>
              )}
              {uncertainty.factors.some(f => f.factor.includes('Source')) && (
                <li>• Verify information with additional sources</li>
              )}
              {uncertainty.factors.some(f => f.factor.includes('Context')) && (
                <li>• Provide more context for better accuracy</li>
              )}
              <li>• Use the feedback system to help improve future responses</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};