import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Brain, Target, Lightbulb } from 'lucide-react';
import { ThoughtStep } from '../types/chat';

interface ThoughtProcessProps {
  steps: ThoughtStep[];
  isExpanded: boolean;
  onToggle: () => void;
  className?: string;
}

export const ThoughtProcess: React.FC<ThoughtProcessProps> = ({
  steps,
  isExpanded,
  onToggle,
  className = '',
}) => {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());

  if (!steps || steps.length === 0) {
    return null;
  }

  const toggleStepExpansion = (stepNumber: number) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(stepNumber)) {
      newExpanded.delete(stepNumber);
    } else {
      newExpanded.add(stepNumber);
    }
    setExpandedSteps(newExpanded);
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-400';
    if (confidence >= 0.6) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.6) return 'Medium';
    return 'Low';
  };

  const getStepIcon = (stepNumber: number) => {
    // Cycle through different icons for visual variety
    const icons = [Brain, Target, Lightbulb];
    return icons[(stepNumber - 1) % icons.length];
  };

  return (
    <div className={`border border-gray-600 rounded-lg bg-gray-800/50 ${className}`}>
      {/* Header */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-3 hover:bg-gray-700/50 transition-colors"
      >
        <div className="flex items-center space-x-2">
          <Brain className="w-4 h-4 text-purple-400" />
          <span className="text-sm font-medium text-gray-300">
            Chain of Thought ({steps.length} steps)
          </span>
        </div>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronRight className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-gray-600">
          {steps.map((step, index) => {
            const StepIcon = getStepIcon(step.step);
            const isStepExpanded = expandedSteps.has(step.step);
            
            return (
              <div key={step.step} className="border-b border-gray-700 last:border-b-0">
                {/* Step Header */}
                <button
                  onClick={() => toggleStepExpansion(step.step)}
                  className="w-full flex items-center justify-between p-3 hover:bg-gray-700/30 transition-colors text-left"
                >
                  <div className="flex items-center space-x-3 flex-1">
                    <div className="flex items-center space-x-2">
                      <StepIcon className="w-4 h-4 text-blue-400" />
                      <span className="text-sm font-medium text-gray-300">
                        Step {step.step}
                      </span>
                    </div>
                    
                    <div className="flex-1">
                      <p className="text-sm text-gray-400 truncate">
                        {step.description}
                      </p>
                    </div>

                    <div className="flex items-center space-x-2">
                      <span className={`text-xs font-medium ${getConfidenceColor(step.confidence)}`}>
                        {getConfidenceLabel(step.confidence)}
                      </span>
                      <span className="text-xs text-gray-500">
                        {Math.round(step.confidence * 100)}%
                      </span>
                    </div>
                  </div>
                  
                  {isStepExpanded ? (
                    <ChevronDown className="w-4 h-4 text-gray-400 ml-2" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-gray-400 ml-2" />
                  )}
                </button>

                {/* Step Details */}
                {isStepExpanded && (
                  <div className="px-6 pb-3 animate-fade-in">
                    <div className="bg-gray-900/50 rounded-md p-3 space-y-2 thought-expand">
                      <div>
                        <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">
                          Description
                        </h4>
                        <p className="text-sm text-gray-300">
                          {step.description}
                        </p>
                      </div>
                      
                      <div>
                        <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">
                          Reasoning
                        </h4>
                        <p className="text-sm text-gray-300">
                          {step.reasoning}
                        </p>
                      </div>

                      <div className="flex items-center justify-between pt-2 border-t border-gray-700">
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-gray-500">Confidence:</span>
                          <div className="flex items-center space-x-1">
                            <div className="w-20 h-2.5 bg-gray-700 rounded-full overflow-hidden">
                              <div 
                                className={`h-full confidence-fill ${
                                  step.confidence >= 0.8 ? 'bg-gradient-to-r from-green-500 to-green-400' :
                                  step.confidence >= 0.6 ? 'bg-gradient-to-r from-yellow-500 to-yellow-400' : 
                                  'bg-gradient-to-r from-red-500 to-red-400'
                                }`}
                                style={{ width: `${step.confidence * 100}%` }}
                              />
                            </div>
                            <span className={`text-xs font-medium ${getConfidenceColor(step.confidence)} animate-fade-in`}>
                              {Math.round(step.confidence * 100)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ThoughtProcess;