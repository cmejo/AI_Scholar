import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  Send, Mic, MicOff, Volume2, VolumeX, Brain, 
  CheckCircle, Clock, User, Bot, Copy, ThumbsUp, 
  ThumbsDown, RotateCcw, Settings, Zap, FileText,
  Quote, Link, Lightbulb, MessageSquare
} from 'lucide-react';

interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  type: 'text' | 'voice' | 'system';
  mode?: ChatMode;
  metadata?: MessageMetadata;
  citations?: Citation[];
  reasoning?: ReasoningStep[];
}

interface MessageMetadata {
  processingTime?: number;
  confidence?: number;
  sources?: string[];
  voiceTranscription?: string;
  factChecked?: boolean;
  memoryContext?: string[];
}

interface Citation {
  id: string;
  text: string;
  source: string;
  url?: string;
  confidence: number;
}

interface ReasoningStep {
  step: number;
  description: string;
  reasoning: string;
  confidence: number;
}

type ChatMode = 'standard' | 'streaming' | 'chain_of_thought' | 'fact_checked' | 'voice' | 'memory_aware';

interface PromptTemplate {
  id: string;
  name: string;
  description: string;
  template: string;
  category: string;
  variables: string[];
}

interface AdvancedChatInterfaceProps {
  onMessageSend?: (message: string, mode: ChatMode) => void;
  onVoiceToggle?: (enabled: boolean) => void;
}

const promptTemplates: PromptTemplate[] = [
  {
    id: 'research_summary',
    name: 'Research Summary',
    description: 'Summarize research findings',
    template: 'Please provide a comprehensive summary of the research on {topic}, including key findings, methodologies, and implications.',
    category: 'Research',
    variables: ['topic']
  },
  {
    id: 'citation_analysis',
    name: 'Citation Analysis',
    description: 'Analyze citations and sources',
    template: 'Analyze the following citation: "{citation}" and provide context about its relevance to {research_area}.',
    category: 'Analysis',
    variables: ['citation', 'research_area']
  },
  {
    id: 'hypothesis_generation',
    name: 'Hypothesis Generation',
    description: 'Generate research hypotheses',
    template: 'Based on the current literature in {field}, generate 3-5 testable hypotheses related to {research_question}.',
    category: 'Research',
    variables: ['field', 'research_question']
  }
];

export const AdvancedChatInterface: React.FC<AdvancedChatInterfaceProps> = ({
  onMessageSend,
  onVoiceToggle
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      content: 'Hello! I\'m your advanced AI research assistant with memory-aware capabilities, voice interface, and multiple reasoning modes. How can I help you today?',
      sender: 'assistant',
      timestamp: new Date(),
      type: 'text',
      mode: 'standard'
    }
  ]);
  
  const [input, setInput] = useState('');
  const [currentMode, setCurrentMode] = useState<ChatMode>('standard');
  const [isLoading, setIsLoading] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<PromptTemplate | null>(null);
  const [templateVariables, setTemplateVariables] = useState<Record<string, string>>({});
  const [conversationMemory, setConversationMemory] = useState<string[]>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Voice recognition setup
  const startVoiceRecognition = useCallback(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Speech recognition not supported in this browser');
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
      setIsListening(false);
    };

    recognition.onerror = () => {
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  }, []);

  const sendMessage = async (messageContent: string, mode: ChatMode = currentMode) => {
    if (!messageContent.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: messageContent,
      sender: 'user',
      timestamp: new Date(),
      type: voiceEnabled ? 'voice' : 'text',
      mode
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setInput('');

    // Update conversation memory
    setConversationMemory(prev => [...prev.slice(-10), messageContent]);

    // Simulate AI response based on mode
    setTimeout(() => {
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: generateMockResponse(messageContent, mode),
        sender: 'assistant',
        timestamp: new Date(),
        type: 'text',
        mode,
        metadata: {
          processingTime: Math.floor(Math.random() * 2000) + 500,
          confidence: 0.85 + Math.random() * 0.15,
          memoryContext: mode === 'memory_aware' ? conversationMemory.slice(-3) : undefined
        },
        citations: mode === 'fact_checked' ? generateMockCitations() : undefined,
        reasoning: mode === 'chain_of_thought' ? generateMockReasoning() : undefined
      };

      setMessages(prev => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1500);

    onMessageSend?.(messageContent, mode);
  };

  const generateMockResponse = (input: string, mode: ChatMode): string => {
    const responses = {
      standard: `I understand you're asking about "${input}". Let me provide you with a comprehensive response based on current research and best practices.`,
      streaming: `[Streaming Response] Processing your query about "${input}"... This would normally stream token by token for a more dynamic experience.`,
      chain_of_thought: `Let me think through this step by step. Your question about "${input}" requires careful analysis of multiple factors and considerations.`,
      fact_checked: `Based on verified sources and fact-checking, here's what I can tell you about "${input}". All information has been cross-referenced with reliable sources.`,
      voice: `I heard you say "${input}". Here's my response, optimized for voice interaction and clear pronunciation.`,
      memory_aware: `Considering our previous conversation context, your question about "${input}" builds on what we've discussed. Let me provide a contextual response.`
    };

    return responses[mode] || responses.standard;
  };

  const generateMockCitations = (): Citation[] => [
    {
      id: 'cite_1',
      text: 'According to recent research findings...',
      source: 'Journal of AI Research, 2024',
      url: 'https://example.com/research',
      confidence: 0.92
    },
    {
      id: 'cite_2',
      text: 'Studies have shown that...',
      source: 'Nature AI, Vol. 15',
      confidence: 0.88
    }
  ];

  const generateMockReasoning = (): ReasoningStep[] => [
    {
      step: 1,
      description: 'Analyzing the question',
      reasoning: 'First, I need to understand the core components of your question and identify the key concepts.',
      confidence: 0.95
    },
    {
      step: 2,
      description: 'Gathering relevant information',
      reasoning: 'Next, I\'ll draw from my knowledge base to find relevant information and research.',
      confidence: 0.90
    },
    {
      step: 3,
      description: 'Synthesizing response',
      reasoning: 'Finally, I\'ll combine this information into a coherent and helpful response.',
      confidence: 0.93
    }
  ];

  const applyTemplate = (template: PromptTemplate) => {
    let processedTemplate = template.template;
    
    Object.entries(templateVariables).forEach(([key, value]) => {
      processedTemplate = processedTemplate.replace(`{${key}}`, value);
    });

    setInput(processedTemplate);
    setShowTemplates(false);
    setSelectedTemplate(null);
    setTemplateVariables({});
  };

  const renderMessage = (message: ChatMessage) => (
    <div
      key={message.id}
      style={{
        display: 'flex',
        justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
        marginBottom: '16px'
      }}
    >
      <div style={{
        maxWidth: '70%',
        background: message.sender === 'user' 
          ? 'linear-gradient(45deg, #10b981, #059669)'
          : 'rgba(255,255,255,0.1)',
        color: 'white',
        padding: '12px 16px',
        borderRadius: message.sender === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
        position: 'relative'
      }}>
        {/* Message Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '8px',
          fontSize: '12px',
          opacity: 0.8
        }}>
          {message.sender === 'user' ? (
            <User style={{ width: '14px', height: '14px' }} />
          ) : (
            <Bot style={{ width: '14px', height: '14px' }} />
          )}
          <span>{message.sender === 'user' ? 'You' : 'AI Scholar'}</span>
          {message.mode && message.mode !== 'standard' && (
            <span style={{
              background: 'rgba(255,255,255,0.2)',
              padding: '2px 6px',
              borderRadius: '10px',
              fontSize: '10px'
            }}>
              {message.mode.replace('_', ' ')}
            </span>
          )}
          <span>{message.timestamp.toLocaleTimeString()}</span>
        </div>

        {/* Message Content */}
        <div style={{ marginBottom: message.citations || message.reasoning ? '12px' : '0' }}>
          {message.content}
        </div>

        {/* Reasoning Steps */}
        {message.reasoning && (
          <div style={{
            background: 'rgba(59, 130, 246, 0.2)',
            borderRadius: '8px',
            padding: '12px',
            marginBottom: '8px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
              <Brain style={{ width: '14px', height: '14px', color: '#60a5fa' }} />
              <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#60a5fa' }}>
                Chain of Thought
              </span>
            </div>
            {message.reasoning.map((step) => (
              <div key={step.step} style={{ marginBottom: '6px', fontSize: '12px' }}>
                <div style={{ fontWeight: 'bold', marginBottom: '2px' }}>
                  Step {step.step}: {step.description}
                </div>
                <div style={{ opacity: 0.8, marginLeft: '12px' }}>
                  {step.reasoning}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Citations */}
        {message.citations && (
          <div style={{
            background: 'rgba(16, 185, 129, 0.2)',
            borderRadius: '8px',
            padding: '12px',
            marginBottom: '8px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
              <Quote style={{ width: '14px', height: '14px', color: '#10b981' }} />
              <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#10b981' }}>
                Sources & Citations
              </span>
            </div>
            {message.citations.map((citation) => (
              <div key={citation.id} style={{ marginBottom: '6px', fontSize: '12px' }}>
                <div style={{ marginBottom: '2px' }}>"{citation.text}"</div>
                <div style={{ opacity: 0.8, display: 'flex', gap: '8px' }}>
                  <span>— {citation.source}</span>
                  <span>({(citation.confidence * 100).toFixed(0)}% confidence)</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Metadata */}
        {message.metadata && (
          <div style={{
            fontSize: '11px',
            opacity: 0.6,
            display: 'flex',
            gap: '8px',
            marginTop: '8px'
          }}>
            {message.metadata.processingTime && (
              <span>⏱️ {message.metadata.processingTime}ms</span>
            )}
            {message.metadata.confidence && (
              <span>🎯 {(message.metadata.confidence * 100).toFixed(0)}%</span>
            )}
            {message.metadata.memoryContext && (
              <span>🧠 Context: {message.metadata.memoryContext.length} items</span>
            )}
          </div>
        )}

        {/* Message Actions */}
        {message.sender === 'assistant' && (
          <div style={{
            display: 'flex',
            gap: '4px',
            marginTop: '8px',
            opacity: 0.6
          }}>
            <button style={{
              background: 'none',
              border: 'none',
              color: 'white',
              cursor: 'pointer',
              padding: '2px'
            }}>
              <Copy style={{ width: '12px', height: '12px' }} />
            </button>
            <button style={{
              background: 'none',
              border: 'none',
              color: 'white',
              cursor: 'pointer',
              padding: '2px'
            }}>
              <ThumbsUp style={{ width: '12px', height: '12px' }} />
            </button>
            <button style={{
              background: 'none',
              border: 'none',
              color: 'white',
              cursor: 'pointer',
              padding: '2px'
            }}>
              <ThumbsDown style={{ width: '12px', height: '12px' }} />
            </button>
            <button style={{
              background: 'none',
              border: 'none',
              color: 'white',
              cursor: 'pointer',
              padding: '2px'
            }}>
              <Volume2 style={{ width: '12px', height: '12px' }} />
            </button>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      background: 'linear-gradient(135deg, #1a1a1a 0%, #2d1b69 100%)',
      color: 'white',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      {/* Chat Mode Selector */}
      <div style={{
        padding: '16px',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        background: 'rgba(255,255,255,0.05)'
      }}>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', color: '#9ca3af', marginRight: '8px' }}>Mode:</span>
          {(['standard', 'chain_of_thought', 'fact_checked', 'memory_aware'] as ChatMode[]).map((mode) => (
            <button
              key={mode}
              onClick={() => setCurrentMode(mode)}
              style={{
                background: currentMode === mode 
                  ? 'linear-gradient(45deg, #10b981, #059669)'
                  : 'rgba(255,255,255,0.1)',
                border: 'none',
                color: 'white',
                padding: '6px 12px',
                borderRadius: '16px',
                fontSize: '12px',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              {mode.replace('_', ' ')}
            </button>
          ))}
          
          <button
            onClick={() => setShowTemplates(!showTemplates)}
            style={{
              background: 'rgba(168, 85, 247, 0.2)',
              border: '1px solid rgba(168, 85, 247, 0.3)',
              color: '#c084fc',
              padding: '6px 12px',
              borderRadius: '16px',
              fontSize: '12px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            <FileText style={{ width: '12px', height: '12px' }} />
            Templates
          </button>
        </div>
      </div>

      {/* Template Selector */}
      {showTemplates && (
        <div style={{
          padding: '16px',
          background: 'rgba(168, 85, 247, 0.1)',
          borderBottom: '1px solid rgba(255,255,255,0.1)'
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '12px' }}>
            {promptTemplates.map((template) => (
              <div
                key={template.id}
                onClick={() => setSelectedTemplate(template)}
                style={{
                  background: 'rgba(255,255,255,0.1)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px',
                  padding: '12px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                <div style={{ fontWeight: 'bold', marginBottom: '4px', fontSize: '14px' }}>
                  {template.name}
                </div>
                <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '8px' }}>
                  {template.description}
                </div>
                <div style={{ fontSize: '11px', color: '#c084fc' }}>
                  {template.category} • {template.variables.length} variables
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Messages */}
      <div style={{
        flex: 1,
        overflow: 'auto',
        padding: '20px'
      }}>
        {messages.map(renderMessage)}
        
        {isLoading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '16px' }}>
            <div style={{
              background: 'rgba(255,255,255,0.1)',
              padding: '12px 16px',
              borderRadius: '16px 16px 16px 4px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <div style={{
                width: '16px',
                height: '16px',
                border: '2px solid rgba(16, 185, 129, 0.3)',
                borderTop: '2px solid #10b981',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }} />
              <span>AI Scholar is thinking...</span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div style={{
        padding: '16px',
        borderTop: '1px solid rgba(255,255,255,0.1)',
        background: 'rgba(255,255,255,0.05)'
      }}>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage(input);
                }
              }}
              placeholder={`Ask me anything... (${currentMode.replace('_', ' ')} mode)`}
              style={{
                width: '100%',
                background: 'rgba(255,255,255,0.1)',
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: '12px',
                padding: '12px 16px',
                color: 'white',
                fontSize: '14px',
                outline: 'none',
                resize: 'none'
              }}
            />
          </div>
          
          <button
            onClick={() => {
              setVoiceEnabled(!voiceEnabled);
              onVoiceToggle?.(!voiceEnabled);
            }}
            style={{
              background: voiceEnabled ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255,255,255,0.1)',
              border: voiceEnabled ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(255,255,255,0.2)',
              color: voiceEnabled ? '#10b981' : '#9ca3af',
              padding: '12px',
              borderRadius: '12px',
              cursor: 'pointer'
            }}
          >
            {voiceEnabled ? <Volume2 style={{ width: '16px', height: '16px' }} /> : <VolumeX style={{ width: '16px', height: '16px' }} />}
          </button>
          
          <button
            onClick={startVoiceRecognition}
            disabled={isListening}
            style={{
              background: isListening ? 'rgba(239, 68, 68, 0.2)' : 'rgba(59, 130, 246, 0.2)',
              border: isListening ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid rgba(59, 130, 246, 0.3)',
              color: isListening ? '#ef4444' : '#60a5fa',
              padding: '12px',
              borderRadius: '12px',
              cursor: isListening ? 'not-allowed' : 'pointer'
            }}
          >
            {isListening ? <MicOff style={{ width: '16px', height: '16px' }} /> : <Mic style={{ width: '16px', height: '16px' }} />}
          </button>
          
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || isLoading}
            style={{
              background: input.trim() && !isLoading 
                ? 'linear-gradient(45deg, #10b981, #059669)'
                : 'rgba(255,255,255,0.1)',
              border: 'none',
              color: 'white',
              padding: '12px',
              borderRadius: '12px',
              cursor: input.trim() && !isLoading ? 'pointer' : 'not-allowed'
            }}
          >
            <Send style={{ width: '16px', height: '16px' }} />
          </button>
        </div>
        
        <div style={{
          fontSize: '11px',
          color: '#9ca3af',
          marginTop: '8px',
          textAlign: 'center'
        }}>
          Press Enter to send • {currentMode.replace('_', ' ')} mode active
          {conversationMemory.length > 0 && ` • ${conversationMemory.length} items in memory`}
        </div>
      </div>
    </div>
  );
};