import React, { useState, useRef } from 'react';
import { Send, Menu, MessageSquare, FileText, BarChart3, Settings, User, Shield, Zap, Puzzle, Brain, LogIn, UserPlus, LogOut } from 'lucide-react';
import { ToastContainer, useToast } from './components/ToastNotification';

type ViewType = 'chat' | 'documents' | 'analytics' | 'workflows' | 'integrations' | 'security' | 'settings';

interface User {
  name: string;
  email: string;
  role: string;
}

const mockUser: User = {
  name: 'Administrator',
  email: 'Administrator',
  role: 'Administrator'
};

// Sidebar Component
const Sidebar: React.FC<{
  sidebarOpen: boolean;
  currentView: ViewType;
  setCurrentView: (view: ViewType) => void;
  user: User | null;
}> = ({ sidebarOpen, currentView, setCurrentView, user }) => {
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

// Chat Component
const ChatView: React.FC<{
  messages: any[];
  input: string;
  setInput: (value: string) => void;
  sendMessage: () => void;
  messagesEndRef: React.RefObject<HTMLDivElement>;
}> = ({ messages, input, setInput, sendMessage, messagesEndRef }) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%'
    }}>
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
              marginBottom: '20px',
              display: 'flex',
              justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start'
            }}
          >
            <div style={{
              maxWidth: '70%',
              padding: '15px 20px',
              borderRadius: '15px',
              background: message.sender === 'user' 
                ? 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)'
                : 'rgba(255,255,255,0.1)',
              color: 'white',
              fontSize: '14px',
              lineHeight: '1.5'
            }}>
              {message.content}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{
        padding: '20px',
        borderTop: '1px solid rgba(255,255,255,0.1)'
      }}>
        <div style={{
          display: 'flex',
          gap: '12px',
          alignItems: 'flex-end'
        }}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder="Ask me anything..."
            style={{
              flex: 1,
              minHeight: '50px',
              maxHeight: '150px',
              padding: '15px',
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '12px',
              color: 'white',
              fontSize: '14px',
              resize: 'none',
              outline: 'none'
            }}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim()}
            style={{
              padding: '15px',
              background: input.trim() 
                ? 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)'
                : 'rgba(156, 163, 175, 0.3)',
              border: 'none',
              borderRadius: '12px',
              color: 'white',
              cursor: input.trim() ? 'pointer' : 'not-allowed',
              transition: 'all 0.2s ease'
            }}
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
};

// Simple placeholder components for other views
const DocumentsView: React.FC = () => (
  <div style={{ padding: '40px', textAlign: 'center', color: 'white' }}>
    <FileText size={48} style={{ marginBottom: '20px', color: '#34d399' }} />
    <h2>Documents</h2>
    <p style={{ color: '#9ca3af' }}>Document management coming soon...</p>
  </div>
);

const AnalyticsView: React.FC = () => (
  <div style={{ padding: '40px', textAlign: 'center', color: 'white' }}>
    <BarChart3 size={48} style={{ marginBottom: '20px', color: '#f59e0b' }} />
    <h2>Analytics</h2>
    <p style={{ color: '#9ca3af' }}>Analytics dashboard coming soon...</p>
  </div>
);

const WorkflowsView: React.FC = () => (
  <div style={{ padding: '40px', textAlign: 'center', color: 'white' }}>
    <Zap size={48} style={{ marginBottom: '20px', color: '#8b5cf6' }} />
    <h2>Workflows</h2>
    <p style={{ color: '#9ca3af' }}>Workflow automation coming soon...</p>
  </div>
);

const IntegrationsView: React.FC = () => (
  <div style={{ padding: '40px', textAlign: 'center', color: 'white' }}>
    <Puzzle size={48} style={{ marginBottom: '20px', color: '#ef4444' }} />
    <h2>Integrations</h2>
    <p style={{ color: '#9ca3af' }}>Third-party integrations coming soon...</p>
  </div>
);

const SecurityView: React.FC = () => (
  <div style={{ padding: '40px', textAlign: 'center', color: 'white' }}>
    <Shield size={48} style={{ marginBottom: '20px', color: '#10b981' }} />
    <h2>Security</h2>
    <p style={{ color: '#9ca3af' }}>Security monitoring coming soon...</p>
  </div>
);

const SettingsView: React.FC = () => (
  <div style={{ padding: '40px', textAlign: 'center', color: 'white' }}>
    <Settings size={48} style={{ marginBottom: '20px', color: '#6b7280' }} />
    <h2>Settings</h2>
    <p style={{ color: '#9ca3af' }}>Application settings coming soon...</p>
  </div>
);

// Main App Component
const App: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentView, setCurrentView] = useState<ViewType>('chat');
  const [user] = useState<User | null>(mockUser);
  const [messages, setMessages] = useState([
    {
      id: '1',
      content: 'Hello! I\'m your AI Scholar assistant. How can I help you today?',
      sender: 'assistant' as const,
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const { toasts, removeToast, showSuccess, showError } = useToast();

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = {
      id: Date.now().toString(),
      content: input,
      sender: 'user' as const,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      const response = await fetch('/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          context: { dataset: 'ai_scholar' }
        })
      });

      const data = await response.json();
      
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        content: data.response || 'Sorry, I couldn\'t process your request.',
        sender: 'assistant' as const,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
      showSuccess('Message sent successfully!');
    } catch (error) {
      showError('Failed to send message. Please try again.');
    }
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
        return <ChatView messages={messages} input={input} setInput={setInput} sendMessage={sendMessage} messagesEndRef={messagesEndRef} />;
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
      </div>

      {/* Main Content */}
      <div style={{
        display: 'flex',
        width: '100%',
        marginTop: '60px'
      }}>
        <Sidebar
          sidebarOpen={sidebarOpen}
          currentView={currentView}
          setCurrentView={setCurrentView}
          user={user}
        />
        
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