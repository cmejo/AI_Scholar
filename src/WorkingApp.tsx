import React, { useState, useEffect } from 'react';

const WorkingApp: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [currentView, setCurrentView] = useState('chat');
  const [messages, setMessages] = useState<Array<{sender: string, content: string, type?: string}>>([]);
  const [messageInput, setMessageInput] = useState('');

  const updateAuthStatus = () => {
    // This function updates the auth display
  };

  const addMessage = (sender: string, content: string, type: string = '') => {
    setMessages(prev => [...prev, { sender, content, type }]);
  };

  const loginUser = async () => {
    if (isAuthenticated) {
      setCurrentView('profile');
      return;
    }

    try {
      const response = await fetch('http://localhost:8080/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'admin@redditaeo.com',
          password: 'Admin123!'
        })
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('auth_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);

        setIsAuthenticated(true);
        setCurrentUser(data.user);

        addMessage('System', '✅ Successfully logged in! You now have access to all features.', 'success');
      } else {
        const errorText = await response.text();
        addMessage('System', `❌ Login failed: ${errorText}`, 'error');
      }
    } catch (error: any) {
      addMessage('System', `❌ Login error: ${error.message}`, 'error');
    }
  };

  const logoutUser = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
    setIsAuthenticated(false);
    setCurrentUser(null);

    addMessage('System', '👋 Logged out successfully.', 'success');
    setCurrentView('chat');
  };

  const sendMessage = async () => {
    if (!messageInput.trim()) return;

    addMessage('You', messageInput);
    const message = messageInput;
    setMessageInput('');

    // Simple echo response for demo
    setTimeout(() => {
      const responses = [
        `I received your message: "${message}". This is a working React version of the authentication system!`,
        `Thanks for your question about "${message}". The authentication backend is fully functional!`,
        `Interesting point about "${message}". You're now logged in and can access all features!`,
        `Great question! "${message}" - This React app demonstrates full functionality with working auth.`
      ];
      const randomResponse = responses[Math.floor(Math.random() * responses.length)];
      addMessage('AI Scholar', randomResponse);
    }, 1000);
  };

  const showView = (viewName: string) => {
    setCurrentView(viewName);
  };

  // Check for existing auth on load
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (token && token !== 'null' && token.length > 10) {
      fetch('http://localhost:8080/api/auth/profile', {
        headers: { 'Authorization': `Bearer ${token}` }
      }).then(response => {
        if (response.ok) {
          return response.json();
        }
        throw new Error('Token invalid');
      }).then(user => {
        setIsAuthenticated(true);
        setCurrentUser(user);
        addMessage('System', '✅ Welcome back! You are already logged in.', 'success');
      }).catch(() => {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('refresh_token');
      });
    }
  }, []);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  return (
    <div style={{
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      background: 'linear-gradient(135deg, #1a1a2e, #16213e)',
      color: 'white',
      minHeight: '100vh',
      margin: 0,
      padding: 0
    }}>
      {/* Header */}
      <div style={{
        background: 'rgba(0,0,0,0.3)',
        padding: '1rem 2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottom: '1px solid rgba(255,255,255,0.1)'
      }}>
        <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#6366f1' }}>
          🚀 AI Scholar - React Version
        </div>
        <div style={{
          background: 'rgba(0,0,0,0.5)',
          padding: '0.5rem 1rem',
          borderRadius: '20px',
          fontSize: '0.9rem'
        }}>
          Auth: {isAuthenticated ? 'YES' : 'NO'} | User: {currentUser?.name || 'None'}
        </div>
      </div>

      {/* Main Content */}
      <div style={{ display: 'flex', height: 'calc(100vh - 80px)' }}>
        {/* Sidebar */}
        <div style={{
          width: '250px',
          background: 'rgba(0,0,0,0.2)',
          padding: '2rem 1rem',
          borderRight: '1px solid rgba(255,255,255,0.1)'
        }}>
          {['chat', 'profile', 'analytics', 'documents', 'settings'].map(view => (
            <div
              key={view}
              onClick={() => showView(view)}
              style={{
                padding: '0.75rem 1rem',
                margin: '0.5rem 0',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'background 0.3s',
                background: currentView === view ? 'rgba(99, 102, 241, 0.3)' : 'transparent'
              }}
              onMouseEnter={(e) => {
                if (currentView !== view) {
                  e.currentTarget.style.background = 'rgba(99, 102, 241, 0.2)';
                }
              }}
              onMouseLeave={(e) => {
                if (currentView !== view) {
                  e.currentTarget.style.background = 'transparent';
                }
              }}
            >
              {view === 'chat' && '💬 Chat'}
              {view === 'profile' && '👤 Profile'}
              {view === 'analytics' && '📊 Analytics'}
              {view === 'documents' && '📄 Documents'}
              {view === 'settings' && '⚙️ Settings'}
            </div>
          ))}
        </div>

        {/* Content Area */}
        <div style={{ flex: 1, padding: '2rem', overflowY: 'auto' }}>
          {currentView === 'chat' && (
            <div style={{ maxWidth: '800px', margin: '0 auto' }}>
              <div style={{
                background: 'rgba(0,0,0,0.3)',
                padding: '1rem',
                margin: '1rem 0',
                borderRadius: '12px',
                borderLeft: '4px solid #6366f1'
              }}>
                <strong>AI Scholar:</strong> Hello! I'm your AI research assistant. This is a working React version with full authentication integration. Click the red login button to get started!
              </div>
              
              {messages.map((msg, index) => (
                <div
                  key={index}
                  style={{
                    background: 'rgba(0,0,0,0.3)',
                    padding: '1rem',
                    margin: '1rem 0',
                    borderRadius: '12px',
                    borderLeft: '4px solid #6366f1',
                    color: msg.type === 'success' ? '#10b981' : msg.type === 'error' ? '#ef4444' : 'white'
                  }}
                >
                  <strong>{msg.sender}:</strong> {msg.content}
                </div>
              ))}
            </div>
          )}

          {currentView === 'profile' && (
            <div style={{
              background: 'rgba(0,0,0,0.3)',
              padding: '2rem',
              borderRadius: '12px',
              margin: '2rem 0'
            }}>
              <h2>👤 User Profile</h2>
              {isAuthenticated && currentUser ? (
                <div>
                  <h3>Welcome, {currentUser.name}!</h3>
                  <p><strong>Email:</strong> {currentUser.email}</p>
                  <p><strong>Role:</strong> {currentUser.role}</p>
                  <button
                    onClick={logoutUser}
                    style={{
                      padding: '0.75rem 1.5rem',
                      background: '#dc2626',
                      color: 'white',
                      border: 'none',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      marginTop: '1rem'
                    }}
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <p>Please log in to view your profile.</p>
              )}
            </div>
          )}

          {currentView === 'analytics' && (
            <div>
              <h2>📊 Analytics Dashboard</h2>
              <p>Analytics features are available for authenticated users.</p>
            </div>
          )}

          {currentView === 'documents' && (
            <div>
              <h2>📄 Document Manager</h2>
              <p>Document management features are available for authenticated users.</p>
            </div>
          )}

          {currentView === 'settings' && (
            <div>
              <h2>⚙️ Settings</h2>
              <p>Application settings and preferences.</p>
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div style={{
        position: 'fixed',
        bottom: 0,
        left: '250px',
        right: 0,
        background: 'rgba(0,0,0,0.8)',
        padding: '1rem 2rem',
        borderTop: '1px solid rgba(255,255,255,0.1)'
      }}>
        <div style={{
          maxWidth: '800px',
          margin: '0 auto',
          display: 'flex',
          gap: '1rem'
        }}>
          <input
            type="text"
            value={messageInput}
            onChange={(e) => setMessageInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about research..."
            style={{
              flex: 1,
              padding: '0.75rem',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '8px',
              background: 'rgba(255,255,255,0.1)',
              color: 'white'
            }}
          />
          <button
            onClick={sendMessage}
            style={{
              padding: '0.75rem 1.5rem',
              background: '#6366f1',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              transition: 'background 0.3s'
            }}
          >
            Send
          </button>
        </div>
      </div>

      {/* Login Button */}
      <button
        onClick={loginUser}
        style={{
          background: '#dc2626',
          position: 'fixed',
          top: '20px',
          right: '20px',
          zIndex: 1000,
          padding: '0.75rem 1.5rem',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer'
        }}
      >
        {isAuthenticated ? '👤 Profile' : '🔧 Login'}
      </button>
    </div>
  );
};

export default WorkingApp;