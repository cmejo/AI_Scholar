import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, Menu, MessageSquare, FileText, BarChart3, Settings, User, Shield, 
  Zap, Puzzle, Brain, ChevronDown, Database, Activity, RefreshCw
} from 'lucide-react';
import { ToastContainer, useToast } from './components/ToastNotification';
import DocumentsView from './components/DocumentsView';
import AnalyticsView from './components/AnalyticsView';
import WorkflowsView from './components/WorkflowsView';
import IntegrationsView from './components/IntegrationsView';
import SecurityView from './components/SecurityView';
import SettingsView from './components/SettingsView';

type ViewType = 'chat' | 'documents' | 'analytics' | 'workflows' | 'integrations' | 'security' | 'settings';
type DatasetType = 'ai_scholar' | 'quant_finance';

interface User {
  name: string;
  email: string;
  role: string;
}

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  sources?: any[];
  confidence?: number;
}

interface Model {
  name: string;
  description: string;
  size: string;
  status: 'available' | 'loading' | 'error';
}



const mockUser: User = {
  name: 'Administrator',
  email: 'admin@aischolar.com',
  role: 'Administrator'
};

const availableModels: Model[] = [
  // 🚀 Flagship Large Models (70B+ parameters) - Dual RTX 3090 Optimized
  { name: 'qwen2.5:72b', description: '🧠 Alibaba Qwen 2.5 72B - Most powerful reasoning model', size: '47GB', status: 'available' },
  { name: 'qwen2.5:72b-instruct', description: '🎯 Qwen 2.5 72B Instruct - Optimized for following instructions', size: '47GB', status: 'available' },
  { name: 'llama3.1:70b', description: '🚀 Meta Llama 3.1 70B - Most capable general model', size: '42GB', status: 'available' },
  { name: 'mixtral:8x22b', description: '🔥 Mixtral 8x22B - Mixture of Experts, exceptional performance', size: '79GB', status: 'available' },
  
  // ⚡ High-Performance Medium Models (15-35GB VRAM)
  { name: 'qwen2.5:32b', description: '⚡ Qwen 2.5 32B - Excellent balance of power and speed', size: '19GB', status: 'available' },
  { name: 'deepseek-coder:33b', description: '💻 DeepSeek Coder 33B - Advanced code analysis and generation', size: '18GB', status: 'available' },
  { name: 'codellama:34b', description: '💻 CodeLlama 34B - Meta\'s specialized coding model', size: '19GB', status: 'available' },
  { name: 'mixtral:8x7b', description: '🔀 Mixtral 8x7B - Mixture of Experts, versatile performance', size: '26GB', status: 'available' },
  { name: 'gemma2:27b', description: '🔬 Google Gemma 2 27B - Research-optimized model', size: '15GB', status: 'available' },
  
  // 🚀 Efficient High-Quality Models (5-15GB VRAM)
  { name: 'qwen2.5:14b', description: '🚀 Qwen 2.5 14B - Strong performance, good efficiency', size: '9.0GB', status: 'available' },
  { name: 'phi3:14b', description: '🎯 Microsoft Phi-3 14B - Efficient reasoning model', size: '7.9GB', status: 'available' },
  { name: 'mistral-nemo:12b', description: '✨ Mistral Nemo 12B - Latest Mistral technology', size: '7.1GB', status: 'available' },
  { name: 'llama3.1:8b', description: '🏃 Llama 3.1 8B - Fast and highly capable', size: '4.9GB', status: 'available' },
  { name: 'neural-chat:7b', description: '💬 Neural Chat 7B - Optimized conversations', size: '4.1GB', status: 'available' },
  { name: 'deepseek-coder-v2:16b', description: '💻 DeepSeek Coder v2 16B - Enhanced code understanding', size: '8.9GB', status: 'available' },
  
  // 👁️ Multimodal/Vision Models
  { name: 'llama3.2-vision:11b', description: '👁️ Llama 3.2 Vision - Multimodal (text + images)', size: '7.8GB', status: 'available' },
  
  // 📚 Legacy Models (Still Supported)
  { name: 'qwen2:7b', description: '📚 Qwen2 7B - Reliable general purpose model', size: '4.4GB', status: 'available' },
  { name: 'mistral:latest', description: '📚 Mistral 7B - Fast and efficient baseline', size: '4.4GB', status: 'available' },
  { name: 'codellama:latest', description: '📚 CodeLlama 7B - Basic code assistance', size: '3.8GB', status: 'available' },
  { name: 'llama2:latest', description: '📚 Llama2 7B - Classic general model', size: '3.8GB', status: 'available' }
];

// Dataset Selector Component
const DatasetSelector: React.FC<{
  currentDataset: DatasetType;
  onDatasetChange: (dataset: DatasetType) => void;
}> = ({ currentDataset, onDatasetChange }) => {
  const [isOpen, setIsOpen] = useState(false);

  const datasets = [
    { 
      id: 'ai_scholar' as DatasetType, 
      name: 'AI Scholar', 
      description: 'Scientific research papers and academic literature',
      icon: '🔬',
      color: '#60a5fa'
    },
    { 
      id: 'quant_finance' as DatasetType, 
      name: 'Quant Scholar', 
      description: 'Quantitative finance and trading research',
      icon: '📈',
      color: '#10b981'
    }
  ];

  const currentDatasetInfo = datasets.find(d => d.id === currentDataset);

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 12px',
          background: 'rgba(255,255,255,0.1)',
          border: '1px solid rgba(255,255,255,0.2)',
          borderRadius: '8px',
          color: 'white',
          cursor: 'pointer',
          fontSize: '14px',
          minWidth: '180px',
          justifyContent: 'space-between'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>{currentDatasetInfo?.icon}</span>
          <span>{currentDatasetInfo?.name}</span>
        </div>
        <ChevronDown size={16} style={{ 
          transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
          transition: 'transform 0.2s ease'
        }} />
      </button>

      {isOpen && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          marginTop: '4px',
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
          border: '1px solid rgba(255,255,255,0.2)',
          borderRadius: '8px',
          boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
          zIndex: 1000,
          overflow: 'hidden'
        }}>
          {datasets.map((dataset) => (
            <button
              key={dataset.id}
              onClick={() => {
                onDatasetChange(dataset.id);
                setIsOpen(false);
              }}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '12px',
                background: currentDataset === dataset.id ? 'rgba(96, 165, 250, 0.2)' : 'transparent',
                border: 'none',
                color: 'white',
                cursor: 'pointer',
                fontSize: '14px',
                textAlign: 'left',
                transition: 'background-color 0.2s ease'
              }}
              onMouseEnter={(e) => {
                if (currentDataset !== dataset.id) {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
                }
              }}
              onMouseLeave={(e) => {
                if (currentDataset !== dataset.id) {
                  e.currentTarget.style.background = 'transparent';
                }
              }}
            >
              <span style={{ fontSize: '18px' }}>{dataset.icon}</span>
              <div>
                <div style={{ fontWeight: '500' }}>{dataset.name}</div>
                <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '2px' }}>
                  {dataset.description}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

// Model Selector Component
const ModelSelector: React.FC<{
  currentModel: string;
  onModelChange: (model: string) => void;
}> = ({ currentModel, onModelChange }) => {
  const [isOpen, setIsOpen] = useState(false);

  const currentModelInfo = availableModels.find(m => m.name === currentModel);

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 12px',
          background: 'rgba(255,255,255,0.1)',
          border: '1px solid rgba(255,255,255,0.2)',
          borderRadius: '8px',
          color: 'white',
          cursor: 'pointer',
          fontSize: '14px',
          minWidth: '200px',
          justifyContent: 'space-between'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Brain size={16} />
          <span>{currentModelInfo?.name || 'Select Model'}</span>
        </div>
        <ChevronDown size={16} style={{ 
          transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
          transition: 'transform 0.2s ease'
        }} />
      </button>

      {isOpen && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          marginTop: '4px',
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
          border: '1px solid rgba(255,255,255,0.2)',
          borderRadius: '8px',
          boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
          zIndex: 1000,
          overflow: 'hidden',
          maxHeight: '300px',
          overflowY: 'auto'
        }}>
          {availableModels.map((model) => (
            <button
              key={model.name}
              onClick={() => {
                onModelChange(model.name);
                setIsOpen(false);
              }}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
                padding: '12px',
                background: currentModel === model.name ? 'rgba(96, 165, 250, 0.2)' : 'transparent',
                border: 'none',
                color: 'white',
                cursor: 'pointer',
                fontSize: '14px',
                textAlign: 'left',
                transition: 'background-color 0.2s ease'
              }}
              onMouseEnter={(e) => {
                if (currentModel !== model.name) {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
                }
              }}
              onMouseLeave={(e) => {
                if (currentModel !== model.name) {
                  e.currentTarget.style.background = 'transparent';
                }
              }}
            >
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: model.status === 'available' ? '#10b981' : '#ef4444',
                marginTop: '6px',
                flexShrink: 0
              }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: '500', marginBottom: '2px' }}>{model.name}</div>
                <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>
                  {model.description}
                </div>
                <div style={{ fontSize: '11px', color: '#6b7280' }}>
                  Size: {model.size} • Status: {model.status}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

// Enhanced Chat Component with dataset and model selection
const ChatView: React.FC<{
  messages: Message[];
  input: string;
  setInput: (value: string) => void;
  sendMessage: () => void;
  messagesEndRef: React.RefObject<HTMLDivElement>;
  currentDataset: DatasetType;
  onDatasetChange: (dataset: DatasetType) => void;
  currentModel: string;
  onModelChange: (model: string) => void;
  isLoading: boolean;
}> = ({ 
  messages, 
  input, 
  setInput, 
  sendMessage, 
  messagesEndRef, 
  currentDataset, 
  onDatasetChange, 
  currentModel, 
  onModelChange,
  isLoading 
}) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%'
    }}>
      {/* Chat Header with Controls */}
      <div style={{
        padding: '20px',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        background: 'rgba(255,255,255,0.02)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '16px'
        }}>
          <h2 style={{
            color: 'white',
            margin: 0,
            fontSize: '18px',
            fontWeight: '600'
          }}>
            AI Research Assistant
          </h2>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            color: '#9ca3af'
          }}>
            <Activity size={14} />
            <span>{isLoading ? 'Processing...' : 'Ready'}</span>
          </div>
        </div>
        
        <div style={{
          display: 'flex',
          gap: '12px',
          alignItems: 'center',
          flexWrap: 'wrap'
        }}>
          <DatasetSelector 
            currentDataset={currentDataset} 
            onDatasetChange={onDatasetChange} 
          />
          <ModelSelector 
            currentModel={currentModel} 
            onModelChange={onModelChange} 
          />
        </div>
      </div>

      {/* Messages */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '20px'
      }}>
        {messages.map((message) => (
          <div
            key={message.id}
            style={{
              marginBottom: '24px',
              display: 'flex',
              justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start'
            }}
          >
            <div style={{
              maxWidth: '75%',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px'
            }}>
              <div style={{
                padding: '16px 20px',
                borderRadius: message.sender === 'user' ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
                background: message.sender === 'user' 
                  ? 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)'
                  : 'rgba(255,255,255,0.1)',
                color: 'white',
                fontSize: '14px',
                lineHeight: '1.6',
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
              }}>
                {message.content}
              </div>
              
              {/* Message metadata */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '11px',
                color: '#6b7280',
                justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start'
              }}>
                <span>{message.timestamp.toLocaleTimeString()}</span>
                {message.confidence && (
                  <>
                    <span>•</span>
                    <span>Confidence: {(message.confidence * 100).toFixed(1)}%</span>
                  </>
                )}
                {message.sources && message.sources.length > 0 && (
                  <>
                    <span>•</span>
                    <span>{message.sources.length} sources</span>
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div style={{
            display: 'flex',
            justifyContent: 'flex-start',
            marginBottom: '24px'
          }}>
            <div style={{
              padding: '16px 20px',
              borderRadius: '20px 20px 20px 4px',
              background: 'rgba(255,255,255,0.1)',
              color: '#9ca3af',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: '#60a5fa',
                animation: 'pulse 1.5s ease-in-out infinite'
              }} />
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: '#60a5fa',
                animation: 'pulse 1.5s ease-in-out infinite 0.2s'
              }} />
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: '#60a5fa',
                animation: 'pulse 1.5s ease-in-out infinite 0.4s'
              }} />
              <span style={{ marginLeft: '8px' }}>AI is thinking...</span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{
        padding: '20px',
        borderTop: '1px solid rgba(255,255,255,0.1)',
        background: 'rgba(255,255,255,0.02)'
      }}>
        <div style={{
          display: 'flex',
          gap: '12px',
          alignItems: 'flex-end'
        }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
              placeholder={`Ask ${currentDataset === 'ai_scholar' ? 'AI Scholar' : 'Quant Scholar'} anything...`}
              disabled={isLoading}
              style={{
                width: '100%',
                minHeight: '50px',
                maxHeight: '150px',
                padding: '15px',
                background: 'rgba(255,255,255,0.1)',
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: '12px',
                color: 'white',
                fontSize: '14px',
                resize: 'none',
                outline: 'none',
                fontFamily: 'inherit'
              }}
            />
          </div>
          <button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            style={{
              padding: '15px',
              background: (input.trim() && !isLoading)
                ? 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)'
                : 'rgba(156, 163, 175, 0.3)',
              border: 'none',
              borderRadius: '12px',
              color: 'white',
              cursor: (input.trim() && !isLoading) ? 'pointer' : 'not-allowed',
              transition: 'all 0.2s ease',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            {isLoading ? (
              <RefreshCw size={20} style={{ animation: 'spin 1s linear infinite' }} />
            ) : (
              <Send size={20} />
            )}
          </button>
        </div>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 1; }
        }
        
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

// I'll continue with the other components in the next part...
// This is getting long, so I'll create the main App component that uses all these pieces

const App: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentView, setCurrentView] = useState<ViewType>('chat');
  const [user] = useState<User | null>(mockUser);
  const [currentDataset, setCurrentDataset] = useState<DatasetType>('ai_scholar');
  const [currentModel, setCurrentModel] = useState('llama3.1:8b');
  const [isLoading, setIsLoading] = useState(false);
  
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hello! I\'m your AI Scholar assistant with advanced research capabilities. I can help you with scientific literature, data analysis, and research insights. How can I assist you today?',
      sender: 'assistant',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const { toasts, removeToast, showSuccess, showError, showInfo } = useToast();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setIsLoading(true);

    try {
      // First try to switch dataset if needed
      await fetch('/api/chat/switch-dataset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset: currentDataset })
      });

      // Switch model if needed
      await fetch('/api/models/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: currentModel })
      });

      // Send the actual message
      const response = await fetch('/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: currentInput,
          context: { 
            dataset: currentDataset,
            model: currentModel
          }
        })
      });

      const data = await response.json();
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.response || 'Sorry, I couldn\'t process your request.',
        sender: 'assistant',
        timestamp: new Date(),
        confidence: data.confidence,
        sources: data.sources
      };

      setMessages(prev => [...prev, assistantMessage]);
      showSuccess('Message sent successfully!');
    } catch (error) {
      showError('Failed to send message. Please try again.');
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDatasetChange = async (dataset: DatasetType) => {
    setCurrentDataset(dataset);
    showInfo(`Switched to ${dataset === 'ai_scholar' ? 'AI Scholar' : 'Quant Scholar'} dataset`);
  };

  const handleModelChange = async (model: string) => {
    setCurrentModel(model);
    showInfo(`Switched to ${model} model`);
  };

  // Simplified sidebar for now - we can expand this later
  const Sidebar = () => {
    const menuItems = [
      { id: 'chat' as ViewType, icon: MessageSquare, label: 'Chat', color: '#60a5fa' },
      { id: 'documents' as ViewType, icon: FileText, label: 'Documents', color: '#34d399' },
      { id: 'analytics' as ViewType, icon: BarChart3, label: 'Analytics', color: '#f59e0b' },
      { id: 'workflows' as ViewType, icon: Zap, label: 'Workflows', color: '#8b5cf6' },
      { id: 'integrations' as ViewType, icon: Puzzle, label: 'Integrations', color: '#ef4444' },
      { id: 'security' as ViewType, icon: Shield, label: 'Security', color: '#10b981' },
      { id: 'settings' as ViewType, icon: Settings, label: 'Settings', color: '#6b7280' }
    ];

    if (!sidebarOpen) return null;

    return (
      <div style={{
        width: '280px',
        background: 'linear-gradient(180deg, #1a1a2e 0%, #16213e 100%)',
        borderRight: '1px solid rgba(255,255,255,0.1)',
        height: '100vh',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Header */}
        <div style={{
          padding: '20px',
          borderBottom: '1px solid rgba(255,255,255,0.1)'
        }}>
          <h2 style={{
            color: 'white',
            margin: 0,
            fontSize: '20px',
            fontWeight: '700'
          }}>
            🤖 AI Scholar
          </h2>
          <p style={{
            color: '#9ca3af',
            margin: '5px 0 0 0',
            fontSize: '14px'
          }}>
            Enterprise Research Assistant
          </p>
        </div>

        {/* Navigation */}
        <nav style={{ flex: 1, padding: '20px 0' }}>
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => setCurrentView(item.id)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '12px 20px',
                  background: isActive ? 'rgba(96, 165, 250, 0.1)' : 'transparent',
                  border: 'none',
                  borderLeft: isActive ? `3px solid ${item.color}` : '3px solid transparent',
                  color: isActive ? 'white' : '#9ca3af',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                    e.currentTarget.style.color = 'white';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.color = '#9ca3af';
                  }
                }}
              >
                <Icon size={20} />
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* User Info */}
        {user && (
          <div style={{
            padding: '20px',
            borderTop: '1px solid rgba(255,255,255,0.1)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}>
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontWeight: '600'
              }}>
                {user.name.charAt(0)}
              </div>
              <div>
                <div style={{
                  color: 'white',
                  fontSize: '14px',
                  fontWeight: '500'
                }}>
                  {user.name}
                </div>
                <div style={{
                  color: '#9ca3af',
                  fontSize: '12px'
                }}>
                  {user.role}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'chat':
        return (
          <ChatView
            messages={messages}
            input={input}
            setInput={setInput}
            sendMessage={sendMessage}
            messagesEndRef={messagesEndRef}
            currentDataset={currentDataset}
            onDatasetChange={handleDatasetChange}
            currentModel={currentModel}
            onModelChange={handleModelChange}
            isLoading={isLoading}
          />
        );
      case 'documents':
        return <DocumentsView />;
      case 'analytics':
        return <AnalyticsView />;
      case 'workflows':
        return <WorkflowsView />;
      case 'integrations':
        return <IntegrationsView />;
      case 'security':
        return <SecurityView />;
      case 'settings':
        return <SettingsView />;
      default:
        return (
          <div style={{ 
            padding: '40px', 
            textAlign: 'center', 
            color: 'white',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '20px' }}>🚧</div>
            <h2 style={{ marginBottom: '10px' }}>
              {currentView.charAt(0).toUpperCase() + currentView.slice(1)} View
            </h2>
            <p style={{ color: '#9ca3af', marginBottom: '20px' }}>
              Advanced {currentView} functionality is being developed...
            </p>
            <button
              onClick={() => setCurrentView('chat')}
              style={{
                padding: '10px 20px',
                background: 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)',
                border: 'none',
                borderRadius: '8px',
                color: 'white',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              Return to Chat
            </button>
          </div>
        );
    }
  };

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      background: 'linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%)',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      {/* Header */}
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        height: '60px',
        background: 'rgba(26, 26, 46, 0.95)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        display: 'flex',
        alignItems: 'center',
        padding: '0 20px',
        zIndex: 100
      }}>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          style={{
            background: 'none',
            border: 'none',
            color: 'white',
            cursor: 'pointer',
            padding: '8px',
            borderRadius: '6px',
            transition: 'background-color 0.2s ease'
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
          onMouseLeave={(e) => e.currentTarget.style.background = 'none'}
        >
          <Menu size={20} />
        </button>
        
        <div style={{ marginLeft: '20px' }}>
          <h1 style={{
            color: 'white',
            margin: 0,
            fontSize: '18px',
            fontWeight: '600'
          }}>
            AI Scholar - {currentView.charAt(0).toUpperCase() + currentView.slice(1)}
          </h1>
        </div>

        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            color: '#9ca3af'
          }}>
            <Database size={14} />
            <span>{currentDataset === 'ai_scholar' ? 'AI Scholar' : 'Quant Scholar'}</span>
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            color: '#9ca3af'
          }}>
            <Brain size={14} />
            <span>{currentModel}</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{
        display: 'flex',
        width: '100%',
        marginTop: '60px'
      }}>
        <Sidebar />
        
        <main style={{
          flex: 1,
          height: 'calc(100vh - 60px)',
          overflow: 'hidden'
        }}>
          {renderCurrentView()}
        </main>
      </div>

      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  );
};

export default App;