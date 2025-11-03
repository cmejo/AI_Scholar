import React, { useState } from 'react';

const SimpleApp: React.FC = () => {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!message.trim()) return;
    
    setLoading(true);
    try {
      const res = await fetch('/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          context: { dataset: 'ai_scholar' }
        })
      });
      
      const data = await res.json();
      setResponse(data.response || 'No response received');
    } catch (error) {
      setResponse('Error: ' + (error as Error).message);
    }
    setLoading(false);
    setMessage('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  return (
    <div style={{
      fontFamily: 'Arial, sans-serif',
      margin: '20px',
      backgroundColor: '#1a1a1a',
      color: 'white',
      minHeight: '100vh'
    }}>
      <div style={{
        maxWidth: '800px',
        margin: '0 auto',
        padding: '20px',
        backgroundColor: '#2a2a2a',
        borderRadius: '10px'
      }}>
        <h1>🤖 AI Scholar - Simple Version</h1>
        <p>✅ React is working! This is a minimal version to test functionality.</p>
        
        <div>
          <input
            type="text"
            style={{
              width: '100%',
              padding: '10px',
              margin: '10px 0',
              border: '1px solid #555',
              borderRadius: '5px',
              backgroundColor: '#3a3a3a',
              color: 'white'
            }}
            placeholder="Ask me anything..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <button 
            style={{
              padding: '10px 20px',
              backgroundColor: '#007acc',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
            onClick={sendMessage}
            disabled={loading}
          >
            {loading ? 'Thinking...' : 'Send Message'}
          </button>
        </div>
        
        {response && (
          <div style={{
            backgroundColor: '#3a3a3a',
            padding: '15px',
            borderRadius: '5px',
            marginTop: '20px',
            whiteSpace: 'pre-wrap'
          }}>
            <strong>AI Response:</strong><br/>
            {response}
          </div>
        )}
        
        <div style={{marginTop: '20px', fontSize: '14px', color: '#888'}}>
          <p><strong>Status:</strong></p>
          <p>✅ React: Working</p>
          <p>✅ TypeScript: Compiled</p>
          <p>✅ Components: Rendering</p>
          <p>✅ State: Functional</p>
          <p>🔄 API: Testing with chat endpoint</p>
        </div>
      </div>
    </div>
  );
};

export default SimpleApp;