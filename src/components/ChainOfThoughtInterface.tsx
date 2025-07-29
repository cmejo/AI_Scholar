import React, { useState } from 'react';
import { Brain, ChevronDown, ChevronRight, Clock, Target, Lightbulb, CheckCircle, AlertCircle } from 'lucide-react';
import { ChainOfThoughtResponse, ReasoningStep, ThoughtProcess } from '../utils/chainOfThought';

interface ChainOfThoughtInterfaceProps {
  response: ChainOfThoughtResponse | null;
  thoughtProcess: ThoughtProcess[];
  isVisible: boolean;
  onToggle: () => void;
}

export const ChainOfThoughtInterface: React.FC<ChainOfThoughtInterfaceProps> = ({
  response,
  thoughtProcess,
  isVisible,
  onToggle
}) => {
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<'reasoning' | 'thoughts'>('reasoning');

  const toggleStep = (stepId: string) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(stepId)) {
      newExpanded.delete(stepId);
    } else {
      newExpanded.add(stepId);
    }
    setExpandedSteps(newExpanded);
  };

  const getStepIcon = (type: ReasoningStep['type']) => {
    switch (type) {
      case 'analysis': return <Brain className="text-purple-400" size={16} />;
      case 'decomposition': return <Target className="text-blue-400" size={16} />;
      case 'retrieval': return <Lightbulb className="text-yellow-400" size={16} />;
      case 'synthesis': return <CheckCircle className="text-emerald-400" size={16} />;
      case 'validation': return <AlertCircle className="text-orange-400" size={16} />;
      default: return <Brain className="text-gray-400" size={16} />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-emerald-400';
    if (confidence >= 0.6) return 'text-yellow-400';
    return 'text-red-400';
  };

  if (!response && thoughtProcess.length === 0) return null;

  return (
    <div className="border-t border-gray-700">
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between bg-gray-800/50 hover:bg-gray-800 transition-colors"
      >
        <div className="flex items-center space-x-2">
          <Brain className="text-purple-400" size={20} />
          <span className="font-medium">Chain of Thought Reasoning</span>
          {response && (
            <span className="text-xs bg-purple-600/20 text-purple-300 px-2 py-1 rounded">
              {response.totalSteps} steps
            </span>
          )}
        </div>
        {isVisible ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
      </button>

      {isVisible && (
        <div className="p-4 bg-gray-800/30">
          {/* Tab Navigation */}
          <div className="flex space-x-4 mb-4 border-b border-gray-700">
            <button
              onClick={() => setActiveTab('reasoning')}
              className={`pb-2 px-1 text-sm transition-colors ${
                activeTab === 'reasoning'
                  ? 'text-purple-400 border-b-2 border-purple-400'
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              Reasoning Steps
            </button>
            <button
              onClick={() => setActiveTab('thoughts')}
              className={`pb-2 px-1 text-sm transition-colors ${
                activeTab === 'thoughts'
                  ? 'text-purple-400 border-b-2 border-purple-400'
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              Thought Process
            </button>
          </div>

          {/* Reasoning Steps Tab */}
          {activeTab === 'reasoning' && response && (
            <div className="space-y-3">
              {/* Summary */}
              <div className="bg-gray-800 rounded-lg p-3 mb-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div className="text-center">
                    <div className="text-lg font-bold text-purple-400">{response.totalSteps}</div>
                    <div className="text-gray-400">Total Steps</div>
                  </div>
                  <div className="text-center">
                    <div className={`text-lg font-bold ${getConfidenceColor(response.overallConfidence)}`}>
                      {(response.overallConfidence * 100).toFixed(0)}%
                    </div>
                    <div className="text-gray-400">Confidence</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-blue-400">{response.executionTime}ms</div>
                    <div className="text-gray-400">Execution Time</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-emerald-400 capitalize">
                      {response.metadata.queryComplexity}
                    </div>
                    <div className="text-gray-400">Complexity</div>
                  </div>
                </div>
              </div>

              {/* Reasoning Steps */}
              {response.reasoningChain.map((step, index) => (
                <div key={step.id} className="border border-gray-700 rounded-lg overflow-hidden">
                  <button
                    onClick={() => toggleStep(step.id)}
                    className="w-full px-4 py-3 flex items-center justify-between bg-gray-800/50 hover:bg-gray-800 transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded">
                        {index + 1}
                      </span>
                      {getStepIcon(step.type)}
                      <span className="font-medium capitalize">{step.type}</span>
                      <span className="text-sm text-gray-400">{step.description}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`text-xs ${getConfidenceColor(step.confidence)}`}>
                        {(step.confidence * 100).toFixed(0)}%
                      </span>
                      {expandedSteps.has(step.id) ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                    </div>
                  </button>

                  {expandedSteps.has(step.id) && (
                    <div className="px-4 py-3 bg-gray-900/50 border-t border-gray-700">
                      <div className="space-y-3 text-sm">
                        <div>
                          <span className="text-gray-400 font-medium">Input:</span>
                          <div className="mt-1 text-gray-300 bg-gray-800 rounded p-2">
                            {step.input}
                          </div>
                        </div>
                        
                        <div>
                          <span className="text-gray-400 font-medium">Reasoning:</span>
                          <div className="mt-1 text-gray-300">
                            {step.reasoning}
                          </div>
                        </div>
                        
                        <div>
                          <span className="text-gray-400 font-medium">Output:</span>
                          <div className="mt-1 text-gray-300 bg-gray-800 rounded p-2 max-h-32 overflow-y-auto">
                            {typeof step.output === 'string' && step.output.startsWith('{') 
                              ? JSON.stringify(JSON.parse(step.output), null, 2)
                              : step.output
                            }
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          <span>Confidence: {(step.confidence * 100).toFixed(1)}%</span>
                          <span>{step.timestamp.toLocaleTimeString()}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Thought Process Tab */}
          {activeTab === 'thoughts' && thoughtProcess.length > 0 && (
            <div className="space-y-4">
              {thoughtProcess.map((thought, index) => (
                <div key={index} className="bg-gray-800 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-3">
                    <span className="text-xs bg-purple-600 text-white px-2 py-1 rounded">
                      Step {thought.step}
                    </span>
                    <Brain className="text-purple-400" size={16} />
                  </div>
                  
                  <div className="space-y-3 text-sm">
                    <div>
                      <span className="text-purple-300 font-medium">💭 Thought:</span>
                      <div className="mt-1 text-gray-300 italic">"{thought.thought}"</div>
                    </div>
                    
                    <div>
                      <span className="text-blue-300 font-medium">🎯 Action:</span>
                      <div className="mt-1 text-gray-300">{thought.action}</div>
                    </div>
                    
                    <div>
                      <span className="text-emerald-300 font-medium">👁️ Observation:</span>
                      <div className="mt-1 text-gray-300">{thought.observation}</div>
                    </div>
                    
                    <div>
                      <span className="text-yellow-300 font-medium">🤔 Reflection:</span>
                      <div className="mt-1 text-gray-300">{thought.reflection}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Alternative Approaches */}
          {response && response.metadata.alternativeApproaches.length > 0 && (
            <div className="mt-4 p-3 bg-gray-800/50 rounded-lg">
              <div className="text-sm font-medium text-gray-300 mb-2">Alternative Approaches:</div>
              <div className="flex flex-wrap gap-2">
                {response.metadata.alternativeApproaches.map((approach, index) => (
                  <span
                    key={index}
                    className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded"
                  >
                    {approach}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};