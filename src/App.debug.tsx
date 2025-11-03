import React, { useState } from 'react';
import { Send, Menu, MessageSquare } from 'lucide-react';

// Step 1: Minimal App with just basic imports
const App: React.FC = () => {
  const [message, setMessage] = useState('');

  return (
    <div style={{
      fontFamily: 'Arial, sans-serif',
      backgroundColor: '#1a1a1a',
      color: 'white',
      minHeight: '100vh',
      padding: '20px'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto'
      }}>
        <h1>🤖 AI Scholar - Debug Version</h1>
        <p>✅ Step 1: Basic React + Lucide icons working</p>
        
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          marginTop: '20px'
        }}>
          <Menu size={24} />
          <MessageSquare size={24} />
          <Send size={24} />
          <span>Icons loaded successfully</span>
        </div>

        <div style={{
          marginTop: '20px',
          padding: '20px',
          backgroundColor: '#2a2a2a',
          borderRadius: '10px'
        }}>
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Test input..."
            style={{
              width: '100%',
              padding: '10px',
              backgroundColor: '#3a3a3a',
              border: '1px solid #555',
              borderRadius: '5px',
              color: 'white'
            }}
          />
          <p style={{ marginTop: '10px' }}>
            You typed: {message}
          </p>
        </div>
      </div>
    </div>
  );
};

export default App;