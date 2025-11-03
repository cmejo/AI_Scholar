import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, Menu, MessageSquare, FileText, BarChart3, Settings, User, Shield, 
  Zap, Puzzle, Brain, LogIn, UserPlus, LogOut, ChevronDown, Database,
  Cpu, Activity, Upload, Download, Search, Filter, Plus, Edit, Trash2,
  Play, Pause, RefreshCw, Eye, EyeOff, Lock, Unlock, Bell, X
} from 'lucide-react';
import { ToastContainer, useToast } from './components/ToastNotification';

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

interface Document {
  id: string;
  name: string;
  size: string;
  uploadDate: Date;
  status: 'processing' | 'ready' | 'error';
  type: string;
}

interface Workflow {
  id: number;
  title: string;
  description: string;
  status: 'Active' | 'Draft' | 'Inactive';
  color: string;
  lastRun: string;
}

interface Integration {
  id: number;
  name: string;
  icon: string;
  status: 'Connected' | 'Available' | 'Error';
  description: string;
  apiKey?: string;
}

const mockUser: User = {
  name: 'Administrator',
  email: 'admin@aischolar.com',
  role: 'Administrator'
};

const availableModels: Model[] = [
  { name: 'llama3.1:8b', description: 'Fast and efficient 8B model - good for general tasks', size: '4.7GB', status: 'available' },
  { name: 'llama3.1:70b', description: 'Large 70B model - excellent for complex reasoning', size: '40GB', status: 'available' },
  { name: 'qwen2:72b', description: 'Advanced 72B model - superior reasoning capabilities', size: '41GB', status: 'available' },
  { name: 'codellama:34b', description: 'Specialized 34B model - optimized for code and technical content', size: '19GB', status: 'available' }
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