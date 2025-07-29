import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, FileText, Loader2, Brain, Network, Target, Lightbulb, Settings, Mic, Quote } from 'lucide-react';
import { useEnhancedChat } from '../contexts/EnhancedChatContext';
import { useDocument } from '../contexts/DocumentContext';
import { contextAwareRetriever, ContextualResponse } from '../utils/contextAwareRetrieval';
import { chainOfThoughtReasoner, ChainOfThoughtResponse, ThoughtProcess } from '../utils/chainOfThought';
import { ChainOfThoughtInterface } from './ChainOfThoughtInterface';
import { CitationAwareChat } from './CitationAwareChat';
import { promptTemplateService } from '../services/promptTemplateService';
import { streamingService } from '../services/streamingService';
import { evaluationService } from '../services/evaluationService';
import { factCheckingService } from '../services/factCheckingService';
import { pluginService } from '../services/pluginService';

type ChatMode = 'standard' | 'citation_aware' | 'chain_of_thought' | 'streaming' | 'fact_checked';

export const AdvancedChatInterface: React.FC = () => {
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [lastResponse, setLastResponse] = useState<ContextualResponse | null>(null);
  const [chainOfThoughtResponse, setChainOfThoughtResponse] = useState<ChainOfThoughtResponse | null>(null);
  const [thoughtProcess, setThoughtProcess] = useState<ThoughtProcess[]>([]);
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [showChainOfThought, setShowChainOfThought] = useState(false);
  const [enableChainOfThought, setEnableChainOfThought] = useState(true);
  const [chatMode, setChatMode] = useState<ChatMode>('standard');
  const [selectedTemplate, setSelectedTemplate] = useState('direct_qa');
  const [showSettings, setShowSettings] = useState(false);
  const [streamingEnabled, setStreamingEnabled] = useState(false);
  const [factCheckEnabled, setFactCheckEnabled] = useState(true);
  const [currentStreamContent, setCurrentStreamContent] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { currentConversation, sendMessage } = useEnhancedChat();
  const { documents } = useDocument();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentConversation?.messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');
    setIsTyping(true);
    setCurrentStreamContent('');

    try {
      if (chatMode === 'citation_aware') {
        // Handle citation-aware mode separately
        return;
      }

      // Perform advanced retrieval
      const retrievalResponse = await contextAwareRetriever.retrieve(userMessage, 5);
      setLastResponse(retrievalResponse);

      // Apply prompt template
      const template = promptTemplateService.getTemplate(selectedTemplate);
      let processedQuery = userMessage;
      
      if (template) {
        processedQuery = promptTemplateService.applyTemplate(selectedTemplate, {
          question: userMessage,
          context: JSON.stringify(retrievalResponse.results),
          topic: userMessage.split(' ').slice(0, 3).join(' ')
        });
      }

      // Generate chain of thought reasoning if enabled
      if (enableChainOfThought) {
        const mockRetrievalFunction = async (query: string) => {
          const results = await contextAwareRetriever.retrieve(query, 3);
          return results.results;
        };

        const cotResponse = await chainOfThoughtReasoner.processQuery(
          userMessage,
          retrievalResponse.results,
          mockRetrievalFunction
        );
        setChainOfThoughtResponse(cotResponse);

        // Generate thought process
        const thoughts = await chainOfThoughtReasoner.generateThoughtProcess(
          userMessage,
          retrievalResponse.results
        );
        setThoughtProcess(thoughts);
      }

      // Handle streaming if enabled
      if (streamingEnabled) {
        await handleStreamingResponse(processedQuery, retrievalResponse);
      } else {
        await handleStandardResponse(userMessage, retrievalResponse);
      }

      // Evaluate the query
      await evaluateQuery(userMessage, retrievalResponse);

    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsTyping(false);
    }
  };

  const handleStreamingResponse = async (query: string, retrievalResponse: ContextualResponse) => {
    let accumulatedContent = '';
    
    try {
      for await (const chunk of streamingService.streamWithCitations(query, retrievalResponse.results)) {
        accumulatedContent += chunk.content;
        setCurrentStreamContent(accumulatedContent);
        
        if (chunk.isComplete) {
          // Send final message
          await sendMessage(query, retrievalResponse);
          setCurrentStreamContent('');
        }
      }
    } catch (error) {
      console.error('Streaming error:', error);
      await sendMessage(query, retrievalResponse);
    }
  };

  const handleStandardResponse = async (query: string, retrievalResponse: ContextualResponse) => {
    // Fact check if enabled
    if (factCheckEnabled) {
      const factCheckResults = await factCheckingService.factCheck(query);
      // Add fact check results to context
    }

    await sendMessage(query, retrievalResponse);
  };

  const evaluateQuery = async (query: string, retrievalResponse: ContextualResponse) => {
    try {
      const evaluation = await evaluationService.evaluateQuery(
        `query_${Date.now()}`,
        query,
        'Generated response', // Would be actual response
        retrievalResponse.results,
        [], // Would be ground truth if available
        undefined // Ground truth response
      );
      
      console.log('Query evaluation:', evaluation);
    } catch (error) {
      console.error('Evaluation error:', error);
    }
  };

  const handlePluginExecution = async (pluginId: string, input: any) => {
    try {
      const result = await pluginService.executePlugin(pluginId, input);
      console.log('Plugin execution result:', result);
      return result;
    } catch (error) {
      console.error('Plugin execution error:', error);
      return null;
    }
  };

  const messages = currentConversation?.messages || [];
  const templates = promptTemplateService.getTemplates();

  // If citation-aware mode is selected, render the specialized component
  if (chatMode === 'citation_aware') {
    return <CitationAwareChat />;
  }

  return (
    <div className="flex flex-col h-full">
      {/* Enhanced Header with Mode Selection */}
      <div className="border-b border-gray-700 p-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Brain className="text-purple-400" size={24} />
          <div>
            <h2 className="text-lg font-semibold">Advanced RAG Chat</h2>
            <p className="text-sm text-gray-400">
              {chatMode === 'standard' && 'Intelligent retrieval with advanced features'}
              {chatMode === 'citation_aware' && 'Precise source linking with expandable citations'}
              {chatMode === 'chain_of_thought' && 'Step-by-step reasoning and analysis'}
              {chatMode === 'streaming' && 'Real-time token-by-token generation'}
              {chatMode === 'fact_checked' && 'Fact-checked responses with validation'}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Chat Mode Selector */}
          <select
            value={chatMode}
            onChange={(e) => setChatMode(e.target.value as ChatMode)}
            className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-1 text-sm text-white"
          >
            <option value="standard">Standard</option>
            <option value="citation_aware">Citation-Aware</option>
            <option value="chain_of_thought">Chain of Thought</option>
            <option value="streaming">Streaming</option>
            <option value="fact_checked">Fact-Checked</option>
          </select>

          {/* Template Selector */}
          <select
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
            className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-1 text-sm text-white"
          >
            {templates.map(template => (
              <option key={template.id} value={template.id}>
                {template.name}
              </option>
            ))}
          </select>

          <button
            onClick={() => setEnableChainOfThought(!enableChainOfThought)}
            className={`px-3 py-1 rounded-lg text-sm transition-colors ${
              enableChainOfThought 
                ? 'bg-emerald-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            CoT {enableChainOfThought ? 'ON' : 'OFF'}
          </button>
          
          <button
            onClick={() => setStreamingEnabled(!streamingEnabled)}
            className={`px-3 py-1 rounded-lg text-sm transition-colors ${
              streamingEnabled 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Stream {streamingEnabled ? 'ON' : 'OFF'}
          </button>

          <button
            onClick={() => setFactCheckEnabled(!factCheckEnabled)}
            className={`px-3 py-1 rounded-lg text-sm transition-colors ${
              factCheckEnabled 
                ? 'bg-red-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Fact-Check {factCheckEnabled ? 'ON' : 'OFF'}
          </button>
          
          <button
            onClick={() => setShowAnalysis(!showAnalysis)}
            className={`px-3 py-1 rounded-lg text-sm transition-colors ${
              showAnalysis 
                ? 'bg-purple-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Analysis
          </button>

          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <Settings size={16} />
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="border-b border-gray-700 p-4 bg-gray-800/50">
          <h3 className="text-white font-medium mb-3">Advanced Settings</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <label className="block text-gray-400 mb-1">Response Style</label>
              <select className="w-full bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white">
                <option>Detailed</option>
                <option>Concise</option>
                <option>Academic</option>
                <option>Conversational</option>
              </select>
            </div>
            <div>
              <label className="block text-gray-400 mb-1">Confidence Threshold</label>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.1"
                defaultValue="0.7"
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-gray-400 mb-1">Max Sources</label>
              <input
                type="number"
                min="1"
                max="10"
                defaultValue="5"
                className="w-full bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white"
              />
            </div>
          </div>
        </div>
      )}

      {/* Analysis Panel */}
      {showAnalysis && lastResponse && (
        <div className="border-b border-gray-700 p-4 bg-gray-800/50">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            {/* Query Analysis */}
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Target className="text-blue-400" size={16} />
                <span className="font-medium">Query Intent</span>
              </div>
              <div className="bg-gray-800 rounded p-2">
                <div className="text-blue-300 capitalize">{lastResponse.queryAnalysis.intent.type}</div>
                <div className="text-xs text-gray-400">
                  Confidence: {(lastResponse.queryAnalysis.intent.confidence * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-gray-400">
                  Scope: {lastResponse.queryAnalysis.intent.scope}
                </div>
              </div>
            </div>

            {/* Strategy Used */}
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Network className="text-emerald-400" size={16} />
                <span className="font-medium">Retrieval Strategy</span>
              </div>
              <div className="bg-gray-800 rounded p-2">
                <div className="text-emerald-300 capitalize">{lastResponse.strategy.type}</div>
                <div className="text-xs text-gray-400 space-y-1">
                  <div>Semantic: {(lastResponse.strategy.weights.semantic * 100).toFixed(0)}%</div>
                  <div>Keyword: {(lastResponse.strategy.weights.keyword * 100).toFixed(0)}%</div>
                  <div>Hierarchical: {(lastResponse.strategy.weights.hierarchical * 100).toFixed(0)}%</div>
                </div>
              </div>
            </div>

            {/* Chain of Thought Summary */}
            {chainOfThoughtResponse && (
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Brain className="text-purple-400" size={16} />
                  <span className="font-medium">Chain of Thought</span>
                </div>
                <div className="bg-gray-800 rounded p-2">
                  <div className="text-purple-300">{chainOfThoughtResponse.totalSteps} Steps</div>
                  <div className="text-xs text-gray-400">
                    Confidence: {(chainOfThoughtResponse.overallConfidence * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-gray-400">
                    Time: {chainOfThoughtResponse.executionTime}ms
                  </div>
                  <div className="text-xs text-gray-400 capitalize">
                    Complexity: {chainOfThoughtResponse.metadata.queryComplexity}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Related Entities */}
          {lastResponse.queryAnalysis.relatedEntities.length > 0 && (
            <div className="mt-4">
              <div className="text-sm font-medium mb-2">Related Entities:</div>
              <div className="flex flex-wrap gap-2">
                {lastResponse.queryAnalysis.relatedEntities.slice(0, 5).map((entity, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-1 bg-purple-600/20 text-purple-300 rounded text-xs"
                  >
                    {entity.name} ({entity.type})
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Brain size={48} className="mb-4 text-purple-600" />
            <h3 className="text-xl font-semibold mb-2">Advanced RAG Assistant</h3>
            <p className="text-center max-w-md mb-4">
              I use knowledge graphs, hierarchical chunking, intent recognition, and chain of thought reasoning 
              to provide highly relevant and transparent responses from your documents.
            </p>
            
            {documents.length > 0 && (
              <div className="mt-4 text-sm">
                <p className="mb-2">Enhanced features active:</p>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex items-center space-x-2">
                    <Network size={12} className="text-purple-400" />
                    <span>Knowledge Graphs</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Target size={12} className="text-blue-400" />
                    <span>Intent Recognition</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Brain size={12} className="text-emerald-400" />
                    <span>Hierarchical RAG</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Lightbulb size={12} className="text-yellow-400" />
                    <span>Chain of Thought</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Quote size={12} className="text-red-400" />
                    <span>Citation Tracking</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Mic size={12} className="text-indigo-400" />
                    <span>Streaming Responses</span>
                  </div>
                </div>
              </div>
            )}
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
                      : 'bg-gradient-to-br from-purple-600 to-emerald-600 mr-2'
                    }
                  `}>
                    {message.role === 'user' ? (
                      <User size={16} />
                    ) : (
                      <Brain size={16} />
                    )}
                  </div>
                  
                  <div className={`
                    px-4 py-3 rounded-2xl
                    ${message.role === 'user' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-800 text-gray-100 border border-gray-700'
                    }
                  `}>
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-600">
                        <div className="flex items-center space-x-1 text-xs text-gray-400 mb-2">
                          <FileText size={12} />
                          <span>Sources with relevance scores:</span>
                        </div>
                        {message.sources.map((source, idx) => (
                          <div key={idx} className="text-xs text-gray-300 mb-1 flex items-center justify-between">
                            <span>📄 {source.document} (p. {source.page})</span>
                            <span className="text-emerald-400 font-mono">
                              {(source.relevance * 100).toFixed(0)}%
                            </span>
                          </div>
                        ))}
                        
                        {message.explanation && (
                          <div className="mt-2 text-xs text-purple-300 italic">
                            {message.explanation}
                          </div>
                        )}
                      </div>
                    )}

                    {message.insights && message.insights.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-600">
                        <div className="flex items-center space-x-1 text-xs text-gray-400 mb-2">
                          <Lightbulb size={12} />
                          <span>Contextual Insights:</span>
                        </div>
                        {message.insights.map((insight, idx) => (
                          <div key={idx} className="text-xs text-yellow-300 mb-1">
                            • {insight}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Chain of Thought Analysis for Assistant Messages */}
                    {message.role === 'assistant' && enableChainOfThought && (
                      <ChainOfThoughtInterface
                        response={chainOfThoughtResponse}
                        thoughtProcess={thoughtProcess}
                        isVisible={showChainOfThought}
                        onToggle={() => setShowChainOfThought(!showChainOfThought)}
                      />
                    )}
                  </div>
                </div>
              </div>
            ))}

            {/* Streaming Content */}
            {streamingEnabled && currentStreamContent && (
              <div className="flex justify-start">
                <div className="flex items-start space-x-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-600 to-emerald-600 flex items-center justify-center">
                    <Brain size={16} />
                  </div>
                  <div className="bg-gray-800 border border-gray-700 px-4 py-3 rounded-2xl max-w-[85%]">
                    <p className="whitespace-pre-wrap">{currentStreamContent}</p>
                    <div className="mt-2 flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                      <span className="text-xs text-gray-400">Streaming...</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {isTyping && !currentStreamContent && (
              <div className="flex justify-start">
                <div className="flex items-start space-x-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-600 to-emerald-600 flex items-center justify-center">
                    <Brain size={16} />
                  </div>
                  <div className="bg-gray-800 border border-gray-700 px-4 py-3 rounded-2xl">
                    <div className="flex items-center space-x-2">
                      <Loader2 size={16} className="animate-spin text-purple-400" />
                      <span className="text-sm text-gray-400">
                        {enableChainOfThought 
                          ? 'Analyzing query and reasoning step-by-step...' 
                          : 'Analyzing query and retrieving context...'
                        }
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

      {/* Enhanced Input Area */}
      <div className="border-t border-gray-700 p-4">
        <form onSubmit={handleSubmit} className="flex space-x-4">
          <div className="flex-1 relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                chatMode === 'citation_aware' 
                  ? "Ask me anything - I'll provide precise citations..."
                  : enableChainOfThought 
                  ? "Ask me anything - I'll reason through it step by step..." 
                  : "Ask me anything - I'll use advanced RAG to find the best answers..."
              }
              className="w-full bg-gray-800 border border-gray-600 rounded-xl px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
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
          Enhanced with knowledge graphs, intent recognition, hierarchical retrieval, streaming responses
          {enableChainOfThought && ', chain of thought reasoning'}
          {factCheckEnabled && ', and fact-checking'}
        </div>
      </div>
    </div>
  );
};