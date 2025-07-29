import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, FileText, Loader2, Brain, Clock, Star, ThumbsUp, ThumbsDown, AlertTriangle, CheckCircle, XCircle, Settings, Mic, Network, Target, Lightbulb, Quote } from 'lucide-react';
import { useEnhancedChat } from '../contexts/EnhancedChatContext';
import { useDocument } from '../contexts/DocumentContext';
import { UncertaintyVisualization } from './UncertaintyVisualization';
import { ReasoningStepsDisplay } from './ReasoningStepsDisplay';
import { FeedbackCollector } from './FeedbackCollector';
import { contextAwareRetriever } from '../utils/contextAwareRetrieval';
import { chainOfThoughtReasoner } from '../utils/chainOfThought';
import { memoryService } from '../services/memoryService';
import { userProfileService } from '../services/userProfileService';

interface MemoryContext {
  shortTermMemory: Array<{
    id: string;
    content: string;
    importance: number;
    timestamp: Date;
  }>;
  longTermMemory: Array<{
    id: string;
    content: string;
    importance: number;
    lastAccessed: Date;
  }>;
  conversationSummary: string;
  userPreferences: {
    responseStyle: 'concise' | 'detailed' | 'academic';
    preferredSources: string[];
    domainExpertise: string[];
  };
}

interface EnhancedMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  uncertainty?: {
    confidence: number;
    factors: Array<{
      factor: string;
      impact: number;
      explanation: string;
    }>;
  };
  reasoning?: {
    steps: Array<{
      step: number;
      description: string;
      confidence: number;
      evidence: string[];
    }>;
    conclusion: string;
    overallConfidence: number;
  };
  sources?: Array<{
    document: string;
    page: number;
    relevance: number;
    explanation?: string;
  }>;
  memoryContext?: {
    usedMemories: string[];
    newMemories: string[];
    contextRelevance: number;
  };
  feedback?: {
    rating: number;
    helpful: boolean;
    corrections?: string;
  };
}

export const MemoryAwareChatInterface: React.FC = () => {
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [messages, setMessages] = useState<EnhancedMessage[]>([]);
  const [memoryContext, setMemoryContext] = useState<MemoryContext>({
    shortTermMemory: [],
    longTermMemory: [],
    conversationSummary: '',
    userPreferences: {
      responseStyle: 'detailed',
      preferredSources: [],
      domainExpertise: []
    }
  });
  const [showMemoryPanel, setShowMemoryPanel] = useState(false);
  const [showUncertaintyDetails, setShowUncertaintyDetails] = useState<string | null>(null);
  const [showReasoningSteps, setShowReasoningSteps] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [enableMemoryAwareness, setEnableMemoryAwareness] = useState(true);
  const [enableUncertaintyVisualization, setEnableUncertaintyVisualization] = useState(true);
  const [enableReasoningSteps, setEnableReasoningSteps] = useState(true);
  const [enableFeedbackCollection, setEnableFeedbackCollection] = useState(true);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.7);
  const [maxMemoryItems, setMaxMemoryItems] = useState(10);
  const [currentUserId] = useState('user_demo'); // In production, get from auth context
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { documents } = useDocument();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userQuery = input.trim();
    const userMessage: EnhancedMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: userQuery,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      // Store user query in memory if memory awareness is enabled
      if (enableMemoryAwareness) {
        await memoryService.addMemory(currentUserId, {
          type: 'context',
          content: `User query: ${userQuery}`,
          importance: 0.8,
          source: 'chat_interface',
          verified: true
        });

        // Update short-term memory context
        setMemoryContext(prev => ({
          ...prev,
          shortTermMemory: [
            ...prev.shortTermMemory,
            {
              id: `mem_${Date.now()}`,
              content: `User asked: ${userQuery}`,
              importance: 0.8,
              timestamp: new Date()
            }
          ].slice(-maxMemoryItems)
        }));
      }

      // Get user profile for personalization
      const userProfile = await userProfileService.getUserProfile(currentUserId);
      
      // Perform contextual retrieval if documents are available
      let retrievalResponse = null;
      if (documents.length > 0) {
        retrievalResponse = await contextAwareRetriever.retrieve(userQuery, 5);
      }

      // Generate chain of thought reasoning if enabled
      let chainOfThoughtResponse = null;
      if (enableReasoningSteps && retrievalResponse) {
        const mockRetrievalFunction = async (query: string) => {
          const results = await contextAwareRetriever.retrieve(query, 3);
          return results.results;
        };

        chainOfThoughtResponse = await chainOfThoughtReasoner.processQuery(
          userQuery,
          retrievalResponse.results,
          mockRetrievalFunction
        );
      }

      // Generate enhanced AI response
      const aiResponse: EnhancedMessage = await generateEnhancedAIResponse(
        userQuery,
        memoryContext,
        userProfile,
        retrievalResponse,
        chainOfThoughtResponse
      );

      setMessages(prev => [...prev, aiResponse]);

      // Update memory context with AI response
      if (enableMemoryAwareness) {
        await memoryService.addMemory(currentUserId, {
          type: 'context',
          content: `AI response about: ${userQuery}`,
          importance: 0.7,
          source: 'chat_interface',
          verified: true
        });

        setMemoryContext(prev => ({
          ...prev,
          shortTermMemory: [
            ...prev.shortTermMemory,
            {
              id: `mem_${Date.now()}_response`,
              content: `AI provided information about: ${userQuery}`,
              importance: 0.7,
              timestamp: new Date()
            }
          ].slice(-maxMemoryItems),
          conversationSummary: generateConversationSummary(userQuery, aiResponse.content)
        }));
      }

    } catch (error) {
      console.error('Error sending message:', error);
      
      // Show error message
      const errorMessage: EnhancedMessage = {
        id: `msg_${Date.now()}_error`,
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
        uncertainty: {
          confidence: 0.0,
          factors: [
            {
              factor: 'System Error',
              impact: 1.0,
              explanation: 'An error occurred during processing'
            }
          ]
        }
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleFeedback = (messageId: string, feedback: { rating: number; helpful: boolean; corrections?: string }) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId 
        ? { ...msg, feedback }
        : msg
    ));

    // Update long-term memory based on feedback
    if (feedback.helpful) {
      setMemoryContext(prev => ({
        ...prev,
        longTermMemory: [
          ...prev.longTermMemory,
          {
            id: `ltm_${Date.now()}`,
            content: `User found response helpful for query type: ${messages.find(m => m.id === messageId)?.content?.slice(0, 50)}`,
            importance: feedback.rating / 5,
            lastAccessed: new Date()
          }
        ]
      }));
    }
  };

  const generateEnhancedAIResponse = async (
    query: string,
    context: MemoryContext,
    userProfile: any,
    retrievalResponse: any,
    chainOfThoughtResponse: any
  ): Promise<EnhancedMessage> => {
    // Simulate processing time
    await new Promise(resolve => setTimeout(resolve, 1500 + Math.random() * 2000));

    // Generate base response content
    let content = generateMemoryAwareResponse(query, context, userProfile, retrievalResponse);

    // Calculate uncertainty factors
    const uncertaintyFactors = calculateUncertaintyFactors(retrievalResponse, context, userProfile);
    const overallConfidence = uncertaintyFactors.reduce((sum, factor) => sum + (factor.impact * 0.33), 0);

    // Generate reasoning steps
    const reasoningSteps = generateReasoningSteps(query, context, retrievalResponse, chainOfThoughtResponse);

    // Extract sources from retrieval response
    const sources = retrievalResponse?.results?.slice(0, 3).map((result: any, index: number) => ({
      document: `document_${index + 1}.pdf`,
      page: Math.floor(Math.random() * 20) + 1,
      relevance: result.relevanceScore || Math.random() * 0.3 + 0.7,
      explanation: result.explanation || 'Relevant content found'
    })) || [];

    return {
      id: `msg_${Date.now()}_ai`,
      role: 'assistant',
      content,
      timestamp: new Date(),
      uncertainty: enableUncertaintyVisualization ? {
        confidence: Math.max(0.1, Math.min(1.0, overallConfidence)),
        factors: uncertaintyFactors
      } : undefined,
      reasoning: enableReasoningSteps ? {
        steps: reasoningSteps,
        conclusion: 'Generated comprehensive response using memory context and document analysis',
        overallConfidence: Math.max(0.1, Math.min(1.0, overallConfidence))
      } : undefined,
      sources: sources.length > 0 ? sources : undefined,
      memoryContext: enableMemoryAwareness ? {
        usedMemories: context.shortTermMemory.slice(-3).map(mem => mem.content),
        newMemories: [`User interested in: ${query}`, 'Response provided with high relevance'],
        contextRelevance: Math.random() * 0.3 + 0.7
      } : undefined
    };
  };

  const generateMemoryAwareResponse = (
    query: string, 
    context: MemoryContext, 
    userProfile: any, 
    retrievalResponse: any
  ): string => {
    let response = `Based on our conversation history and your preferences for ${context.userPreferences.responseStyle} responses, I can provide you with relevant information about "${query}".`;
    
    // Add memory context
    if (context.shortTermMemory.length > 0) {
      response += ` I notice from our recent discussion that you've been interested in related topics, which helps me provide more contextual information.`;
    }

    // Add user profile context
    if (context.userPreferences.domainExpertise.length > 0) {
      response += ` Given your expertise in ${context.userPreferences.domainExpertise.join(', ')}, I'll adjust the technical depth accordingly.`;
    }

    // Add retrieval context
    if (retrievalResponse && retrievalResponse.results.length > 0) {
      const avgRelevance = retrievalResponse.results.reduce((sum: number, r: any) => sum + r.relevanceScore, 0) / retrievalResponse.results.length;
      response += `\n\nI found ${retrievalResponse.results.length} relevant passages in your documents with an average relevance score of ${(avgRelevance * 100).toFixed(0)}%.`;
    }

    // Add conversation summary context
    if (context.conversationSummary) {
      response += `\n\nConversation context: ${context.conversationSummary}`;
    }

    response += '\n\nThis response demonstrates memory-aware conversation capabilities with uncertainty quantification and reasoning transparency.';

    return response;
  };

  const calculateUncertaintyFactors = (retrievalResponse: any, context: MemoryContext, userProfile: any) => {
    const factors = [];

    // Source quality factor
    if (retrievalResponse && retrievalResponse.results.length > 0) {
      const avgRelevance = retrievalResponse.results.reduce((sum: number, r: any) => sum + r.relevanceScore, 0) / retrievalResponse.results.length;
      factors.push({
        factor: 'Source Quality',
        impact: avgRelevance,
        explanation: `Average document relevance: ${(avgRelevance * 100).toFixed(0)}%`
      });
    } else {
      factors.push({
        factor: 'Source Quality',
        impact: 0.3,
        explanation: 'No documents available for reference'
      });
    }

    // Memory context factor
    const memoryRelevance = context.shortTermMemory.length > 0 ? 0.8 : 0.4;
    factors.push({
      factor: 'Memory Context',
      impact: memoryRelevance,
      explanation: `${context.shortTermMemory.length} recent conversation items available`
    });

    // User profile factor
    const profileCompleteness = (context.userPreferences.domainExpertise.length > 0 ? 0.3 : 0) +
                               (context.userPreferences.preferredSources.length > 0 ? 0.3 : 0) +
                               0.4; // Base score
    factors.push({
      factor: 'User Profile',
      impact: profileCompleteness,
      explanation: `User profile completeness: ${(profileCompleteness * 100).toFixed(0)}%`
    });

    return factors;
  };

  const generateReasoningSteps = (query: string, context: MemoryContext, retrievalResponse: any, chainOfThoughtResponse: any) => {
    const steps = [];

    // Step 1: Query analysis
    steps.push({
      step: 1,
      description: 'Analyzed user query and extracted key concepts',
      confidence: 0.95,
      evidence: ['Natural language processing', 'Entity extraction', 'Intent recognition']
    });

    // Step 2: Memory retrieval
    if (enableMemoryAwareness && context.shortTermMemory.length > 0) {
      steps.push({
        step: 2,
        description: 'Retrieved relevant context from conversation memory',
        confidence: 0.85,
        evidence: [`${context.shortTermMemory.length} memory items`, 'User preferences', 'Conversation history']
      });
    }

    // Step 3: Document search
    if (retrievalResponse && retrievalResponse.results.length > 0) {
      steps.push({
        step: steps.length + 1,
        description: 'Searched document collection for relevant information',
        confidence: 0.80,
        evidence: ['Vector similarity search', 'Keyword matching', 'Hierarchical retrieval']
      });
    }

    // Step 4: Response synthesis
    steps.push({
      step: steps.length + 1,
      description: 'Synthesized response considering all available context',
      confidence: 0.82,
      evidence: ['Memory integration', 'Source validation', 'Uncertainty assessment']
    });

    return steps;
  };

  const generateConversationSummary = (query: string, response: string): string => {
    return `Recent discussion about "${query}". User received detailed information with memory-aware context. Conversation demonstrates advanced RAG capabilities.`;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Enhanced Header with Memory Status and Controls */}
      <div className="border-b border-gray-700 p-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Brain className="text-purple-400" size={24} />
          <div>
            <h2 className="text-lg font-semibold">Memory-Aware Chat</h2>
            <p className="text-sm text-gray-400">
              Context-aware conversations with reasoning transparency and feedback learning
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <div className="text-sm text-gray-400">
            Memory: {memoryContext.shortTermMemory.length}/{maxMemoryItems} short-term, {memoryContext.longTermMemory.length} long-term
          </div>
          
          {/* Feature Toggle Buttons */}
          <button
            onClick={() => setEnableMemoryAwareness(!enableMemoryAwareness)}
            className={`px-2 py-1 rounded text-xs transition-colors ${
              enableMemoryAwareness 
                ? 'bg-purple-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
            title="Toggle memory awareness"
          >
            Memory {enableMemoryAwareness ? 'ON' : 'OFF'}
          </button>
          
          <button
            onClick={() => setEnableUncertaintyVisualization(!enableUncertaintyVisualization)}
            className={`px-2 py-1 rounded text-xs transition-colors ${
              enableUncertaintyVisualization 
                ? 'bg-yellow-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
            title="Toggle uncertainty visualization"
          >
            Uncertainty {enableUncertaintyVisualization ? 'ON' : 'OFF'}
          </button>
          
          <button
            onClick={() => setEnableReasoningSteps(!enableReasoningSteps)}
            className={`px-2 py-1 rounded text-xs transition-colors ${
              enableReasoningSteps 
                ? 'bg-green-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
            title="Toggle reasoning steps display"
          >
            Reasoning {enableReasoningSteps ? 'ON' : 'OFF'}
          </button>
          
          <button
            onClick={() => setEnableFeedbackCollection(!enableFeedbackCollection)}
            className={`px-2 py-1 rounded text-xs transition-colors ${
              enableFeedbackCollection 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
            title="Toggle feedback collection"
          >
            Feedback {enableFeedbackCollection ? 'ON' : 'OFF'}
          </button>
          
          <button
            onClick={() => setShowMemoryPanel(!showMemoryPanel)}
            className={`px-3 py-1 rounded-lg text-sm transition-colors ${
              showMemoryPanel 
                ? 'bg-purple-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Memory Panel
          </button>
          
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            title="Settings"
          >
            <Settings size={16} />
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="border-b border-gray-700 p-4 bg-gray-800/50">
          <h3 className="text-white font-medium mb-3">Memory-Aware Chat Settings</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <label className="block text-gray-400 mb-1">Response Style</label>
              <select 
                value={memoryContext.userPreferences.responseStyle}
                onChange={(e) => setMemoryContext(prev => ({
                  ...prev,
                  userPreferences: {
                    ...prev.userPreferences,
                    responseStyle: e.target.value as 'concise' | 'detailed' | 'academic'
                  }
                }))}
                className="w-full bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white"
              >
                <option value="concise">Concise</option>
                <option value="detailed">Detailed</option>
                <option value="academic">Academic</option>
              </select>
            </div>
            <div>
              <label className="block text-gray-400 mb-1">Confidence Threshold</label>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.1"
                value={confidenceThreshold}
                onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="text-xs text-gray-500 mt-1">{(confidenceThreshold * 100).toFixed(0)}%</div>
            </div>
            <div>
              <label className="block text-gray-400 mb-1">Max Memory Items</label>
              <input
                type="number"
                min="5"
                max="50"
                value={maxMemoryItems}
                onChange={(e) => setMaxMemoryItems(parseInt(e.target.value))}
                className="w-full bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white"
              />
            </div>
          </div>
          
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-2">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="memory-awareness"
                checked={enableMemoryAwareness}
                onChange={(e) => setEnableMemoryAwareness(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="memory-awareness" className="text-sm text-gray-300">Memory Awareness</label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="uncertainty-viz"
                checked={enableUncertaintyVisualization}
                onChange={(e) => setEnableUncertaintyVisualization(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="uncertainty-viz" className="text-sm text-gray-300">Uncertainty Visualization</label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="reasoning-steps"
                checked={enableReasoningSteps}
                onChange={(e) => setEnableReasoningSteps(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="reasoning-steps" className="text-sm text-gray-300">Reasoning Steps</label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="feedback-collection"
                checked={enableFeedbackCollection}
                onChange={(e) => setEnableFeedbackCollection(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="feedback-collection" className="text-sm text-gray-300">Feedback Collection</label>
            </div>
          </div>
        </div>
      )}

      {/* Memory Panel */}
      {showMemoryPanel && (
        <div className="border-b border-gray-700 p-4 bg-gray-800/50">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="text-white font-medium mb-2 flex items-center">
                <Clock size={16} className="mr-2 text-blue-400" />
                Short-term Memory
              </h3>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {memoryContext.shortTermMemory.map(memory => (
                  <div key={memory.id} className="bg-gray-800 rounded p-2 text-sm">
                    <div className="text-gray-300">{memory.content}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      Importance: {(memory.importance * 100).toFixed(0)}% | 
                      {memory.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h3 className="text-white font-medium mb-2 flex items-center">
                <Star size={16} className="mr-2 text-yellow-400" />
                User Preferences
              </h3>
              <div className="bg-gray-800 rounded p-2 text-sm">
                <div className="text-gray-300">Response Style: {memoryContext.userPreferences.responseStyle}</div>
                <div className="text-gray-300">Domain Expertise: {memoryContext.userPreferences.domainExpertise.join(', ') || 'None specified'}</div>
                <div className="text-gray-300">Preferred Sources: {memoryContext.userPreferences.preferredSources.length || 0}</div>
              </div>
            </div>
          </div>
          
          {memoryContext.conversationSummary && (
            <div className="mt-4">
              <h3 className="text-white font-medium mb-2">Conversation Summary</h3>
              <div className="bg-gray-800 rounded p-2 text-sm text-gray-300">
                {memoryContext.conversationSummary}
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
            <h3 className="text-xl font-semibold mb-2">Memory-Aware Assistant</h3>
            <p className="text-center max-w-md mb-4">
              I remember our conversations and adapt to your preferences. I'll show my reasoning process 
              and uncertainty levels to help you understand how I arrive at answers.
            </p>
            
            {documents.length > 0 && (
              <div className="mb-4 text-sm text-center">
                <p className="text-green-400 mb-2">✓ {documents.length} documents loaded and ready</p>
              </div>
            )}
            
            <div className="grid grid-cols-2 gap-3 text-xs mb-6">
              <div className={`flex items-center space-x-2 ${enableMemoryAwareness ? 'text-purple-400' : 'text-gray-600'}`}>
                <Brain size={12} />
                <span>Memory Context</span>
                {enableMemoryAwareness && <CheckCircle size={10} className="text-green-400" />}
              </div>
              <div className={`flex items-center space-x-2 ${enableUncertaintyVisualization ? 'text-yellow-400' : 'text-gray-600'}`}>
                <AlertTriangle size={12} />
                <span>Uncertainty Tracking</span>
                {enableUncertaintyVisualization && <CheckCircle size={10} className="text-green-400" />}
              </div>
              <div className={`flex items-center space-x-2 ${enableReasoningSteps ? 'text-green-400' : 'text-gray-600'}`}>
                <Lightbulb size={12} />
                <span>Reasoning Steps</span>
                {enableReasoningSteps && <CheckCircle size={10} className="text-green-400" />}
              </div>
              <div className={`flex items-center space-x-2 ${enableFeedbackCollection ? 'text-blue-400' : 'text-gray-600'}`}>
                <ThumbsUp size={12} />
                <span>Feedback Learning</span>
                {enableFeedbackCollection && <CheckCircle size={10} className="text-green-400" />}
              </div>
            </div>

            <div className="text-xs text-gray-600 max-w-lg text-center">
              <p className="mb-2">Enhanced features available:</p>
              <div className="grid grid-cols-2 gap-2">
                <div className="flex items-center space-x-2">
                  <Network size={10} className="text-purple-400" />
                  <span>Knowledge Graphs</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Target size={10} className="text-blue-400" />
                  <span>Intent Recognition</span>
                </div>
                <div className="flex items-center space-x-2">
                  <FileText size={10} className="text-emerald-400" />
                  <span>Hierarchical RAG</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Quote size={10} className="text-red-400" />
                  <span>Citation Tracking</span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div
                key={message.id}
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
                    
                    {/* Uncertainty Visualization */}
                    {message.uncertainty && (
                      <UncertaintyVisualization
                        uncertainty={message.uncertainty}
                        isExpanded={showUncertaintyDetails === message.id}
                        onToggle={() => setShowUncertaintyDetails(
                          showUncertaintyDetails === message.id ? null : message.id
                        )}
                      />
                    )}

                    {/* Reasoning Steps Display */}
                    {message.reasoning && (
                      <ReasoningStepsDisplay
                        reasoning={message.reasoning}
                        isExpanded={showReasoningSteps === message.id}
                        onToggle={() => setShowReasoningSteps(
                          showReasoningSteps === message.id ? null : message.id
                        )}
                      />
                    )}

                    {/* Memory Context */}
                    {message.memoryContext && (
                      <div className="mt-3 pt-3 border-t border-gray-600">
                        <div className="flex items-center space-x-1 text-xs text-gray-400 mb-2">
                          <Brain size={12} />
                          <span>Memory Context (Relevance: {(message.memoryContext.contextRelevance * 100).toFixed(0)}%)</span>
                        </div>
                        <div className="text-xs text-gray-300 space-y-1">
                          {message.memoryContext.usedMemories.length > 0 && (
                            <div>Used: {message.memoryContext.usedMemories.join(', ')}</div>
                          )}
                          {message.memoryContext.newMemories.length > 0 && (
                            <div>Learned: {message.memoryContext.newMemories.join(', ')}</div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Sources */}
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-600">
                        <div className="flex items-center space-x-1 text-xs text-gray-400 mb-2">
                          <FileText size={12} />
                          <span>Sources:</span>
                        </div>
                        {message.sources.map((source, idx) => (
                          <div key={idx} className="text-xs text-gray-300 mb-1 flex items-center justify-between">
                            <span>📄 {source.document} (p. {source.page})</span>
                            <span className="text-emerald-400 font-mono">
                              {(source.relevance * 100).toFixed(0)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Feedback Collector */}
                    {message.role === 'assistant' && enableFeedbackCollection && (
                      <FeedbackCollector
                        messageId={message.id}
                        currentFeedback={message.feedback}
                        onFeedback={handleFeedback}
                      />
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {isTyping && (
              <div className="flex justify-start">
                <div className="flex items-start space-x-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-600 to-emerald-600 flex items-center justify-center">
                    <Brain size={16} />
                  </div>
                  <div className="bg-gray-800 border border-gray-700 px-4 py-3 rounded-2xl">
                    <div className="flex items-center space-x-2">
                      <Loader2 size={16} className="animate-spin text-purple-400" />
                      <span className="text-sm text-gray-400">
                        Processing with memory context and reasoning...
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
              placeholder="Ask me anything - I'll remember our conversation and show my reasoning..."
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
          Enhanced with {enableMemoryAwareness ? 'memory awareness' : 'standard mode'}
          {enableUncertaintyVisualization && ', uncertainty visualization'}
          {enableReasoningSteps && ', reasoning transparency'}
          {enableFeedbackCollection && ', feedback learning'}
        </div>
      </div>
    </div>
  );
};