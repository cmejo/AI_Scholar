import React from 'react';
import { Brain, ChevronDown, ChevronRight, CheckCircle, AlertCircle, FileText, Lightbulb, Target } from 'lucide-react';

interface ReasoningStep {
  step: number;
  description: string;
  confidence: number;
  evidence: string[];
}

interface ReasoningData {
  steps: ReasoningStep[];
  conclusion: string;
  overallConfidence: number;
}

interface ReasoningStepsDisplayProps {
  reasoning: ReasoningData;
  isExpanded: boolean;
  onToggle: () => void;
}

export const ReasoningStepsDisplay: React.FC<ReasoningStepsDisplayProps> = ({
  reasoning,
  isExpanded,
  onToggle
}) => {
  const getStepIcon = (stepNumber: number, confidence: number) => {
    const baseClasses = "w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold";
    
    if (confidence >= 0.8) {
      return (
        <div className={`${baseClasses} bg-green-400/20 text-green-400 border border-green-400`}>
          {stepNumber}
        </div>
      );
    } else if (confidence >= 0.6) {
      return (
        <div className={`${baseClasses} bg-yellow-400/20 text-yellow-400 border border-yellow-400`}>
          {stepNumber}
        </div>
      );
    } else {
      return (
        <div className={`${baseClasses} bg-red-400/20 text-red-400 border border-red-400`}>
          {stepNumber}
        </div>
      );
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-400';
    if (confidence >= 0.6) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getEvidenceIcon = (evidence: string) => {
    if (evidence.toLowerCase().includes('document') || evidence.toLowerCase().includes('source')) {
      return <FileText size={12} className="text-blue-400" />;
    }
    if (evidence.toLowerCase().includes('analysis') || evidence.toLowerCase().includes('reasoning')) {
      return <Brain size={12} className="text-purple-400" />;
    }
    if (evidence.toLowerCase().includes('extraction') || evidence.toLowerCase().includes('parsing')) {
      return <Target size={12} className="text-emerald-400" />;
    }
    return <Lightbulb size={12} className="text-yellow-400" />;
  };

  return (
    <div className="mt-3 pt-3 border-t border-gray-600">
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full text-left hover:bg-gray-700/50 rounded p-2 transition-colors"
      >
        <div className="flex items-center space-x-2">
          <Brain size={14} className="text-purple-400" />
          <span className="text-sm font-medium">
            Chain of Thought ({reasoning.steps.length} steps)
          </span>
          <div className={`px-2 py-1 rounded text-xs bg-purple-400/20 ${getConfidenceColor(reasoning.overallConfidence)}`}>
            {(reasoning.overallConfidence * 100).toFixed(0)}% confidence
          </div>
        </div>
        {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
      </button>

      {/* Overall Confidence Bar */}
      <div className="mt-2 mb-3">
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${
              reasoning.overallConfidence >= 0.8 
                ? 'bg-green-400' 
                : reasoning.overallConfidence >= 0.6 
                ? 'bg-yellow-400' 
                : 'bg-red-400'
            }`}
            style={{ width: `${reasoning.overallConfidence * 100}%` }}
          />
        </div>
      </div>

      {isExpanded && (
        <div className="space-y-4 mt-3">
          <div className="text-xs text-gray-400 mb-3">
            Reasoning Process Breakdown:
          </div>
          
          {/* Reasoning Steps */}
          <div className="space-y-4">
            {reasoning.steps.map((step, index) => (
              <div key={index} className="relative">
                {/* Connection Line */}
                {index < reasoning.steps.length - 1 && (
                  <div className="absolute left-3 top-8 w-0.5 h-8 bg-gray-600" />
                )}
                
                <div className="flex items-start space-x-3">
                  {getStepIcon(step.step, step.confidence)}
                  
                  <div className="flex-1 bg-gray-800/50 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-200">
                        Step {step.step}
                      </span>
                      <div className="flex items-center space-x-2">
                        <span className={`text-xs ${getConfidenceColor(step.confidence)}`}>
                          {(step.confidence * 100).toFixed(0)}%
                        </span>
                        {step.confidence >= 0.8 ? (
                          <CheckCircle size={12} className="text-green-400" />
                        ) : (
                          <AlertCircle size={12} className="text-yellow-400" />
                        )}
                      </div>
                    </div>
                    
                    <p className="text-sm text-gray-300 mb-3">
                      {step.description}
                    </p>
                    
                    {/* Step Confidence Bar */}
                    <div className="w-full bg-gray-700 rounded-full h-1.5 mb-3">
                      <div
                        className={`h-1.5 rounded-full transition-all duration-300 ${
                          step.confidence >= 0.8 
                            ? 'bg-green-400' 
                            : step.confidence >= 0.6 
                            ? 'bg-yellow-400' 
                            : 'bg-red-400'
                        }`}
                        style={{ width: `${step.confidence * 100}%` }}
                      />
                    </div>
                    
                    {/* Evidence */}
                    {step.evidence.length > 0 && (
                      <div>
                        <div className="text-xs text-gray-400 mb-2">Evidence:</div>
                        <div className="space-y-1">
                          {step.evidence.map((evidence, evidenceIndex) => (
                            <div key={evidenceIndex} className="flex items-center space-x-2 text-xs text-gray-300">
                              {getEvidenceIcon(evidence)}
                              <span>{evidence}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Conclusion */}
          <div className="bg-gradient-to-r from-purple-900/30 to-blue-900/30 rounded-lg p-4 border border-purple-400/30">
            <div className="flex items-center space-x-2 mb-2">
              <Target size={16} className="text-purple-400" />
              <span className="text-sm font-medium text-purple-300">
                Conclusion
              </span>
            </div>
            <p className="text-sm text-gray-200 mb-3">
              {reasoning.conclusion}
            </p>
            
            {/* Final Confidence Assessment */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">
                Overall Reasoning Confidence:
              </span>
              <div className="flex items-center space-x-2">
                <span className={`text-sm font-medium ${getConfidenceColor(reasoning.overallConfidence)}`}>
                  {(reasoning.overallConfidence * 100).toFixed(0)}%
                </span>
                {reasoning.overallConfidence >= 0.8 ? (
                  <CheckCircle size={14} className="text-green-400" />
                ) : reasoning.overallConfidence >= 0.6 ? (
                  <AlertCircle size={14} className="text-yellow-400" />
                ) : (
                  <AlertCircle size={14} className="text-red-400" />
                )}
              </div>
            </div>
          </div>

          {/* Reasoning Quality Indicators */}
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div className="bg-gray-800/30 rounded p-2 text-center">
              <div className="text-gray-400">Steps</div>
              <div className="text-white font-medium">{reasoning.steps.length}</div>
            </div>
            <div className="bg-gray-800/30 rounded p-2 text-center">
              <div className="text-gray-400">Avg Step Confidence</div>
              <div className={`font-medium ${getConfidenceColor(
                reasoning.steps.reduce((sum, step) => sum + step.confidence, 0) / reasoning.steps.length
              )}`}>
                {((reasoning.steps.reduce((sum, step) => sum + step.confidence, 0) / reasoning.steps.length) * 100).toFixed(0)}%
              </div>
            </div>
            <div className="bg-gray-800/30 rounded p-2 text-center">
              <div className="text-gray-400">Evidence Items</div>
              <div className="text-white font-medium">
                {reasoning.steps.reduce((sum, step) => sum + step.evidence.length, 0)}
              </div>
            </div>
          </div>

          {/* Reasoning Tips */}
          <div className="bg-blue-900/20 rounded p-3 border-l-4 border-blue-400">
            <div className="text-xs font-medium text-blue-300 mb-1">
              Understanding This Reasoning
            </div>
            <ul className="text-xs text-gray-300 space-y-1">
              <li>• Each step shows how I processed your question</li>
              <li>• Confidence scores indicate certainty at each stage</li>
              <li>• Evidence shows what information I used</li>
              <li>• Higher overall confidence means more reliable reasoning</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};