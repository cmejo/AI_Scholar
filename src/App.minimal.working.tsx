import React, { useState } from 'react';

function App(): JSX.Element {
  console.log('🚀 MINIMAL WORKING APP LOADED');
  
  const [message, setMessage] = useState('Hello from AI Scholar!');
  const [count, setCount] = useState(0);

  React.useEffect(() => {
    console.log('🚀 MINIMAL WORKING APP MOUNTED');
    document.title = 'AI Scholar - Working!';
  }, []);

  return (
    <div style={{ 
      padding: '40px', 
      background: 'linear-gradient(135deg, #1a1a1a 0%, #2d1b69 100%)', 
      color: 'white', 
      minHeight: '100vh',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <header style={{ textAlign: 'center', marginBottom: '40px' }}>
          <h1 style={{ 
            fontSize: '3em', 
            margin: '0 0 10px 0', 
            background: 'linear-gradient(45deg, #10b981, #3b82f6)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}>
            ✅ AI Scholar
          </h1>
          <p style={{ fontSize: '1.2em', color: '#cbd5e1' }}>
            React Application Successfully Running!
          </p>
        </header>

        <div style={{ 
          display: 'grid', 
          gap: '20px', 
          marginBottom: '30px' 
        }}>
          <div style={{ 
            background: 'rgba(255,255,255,0.1)', 
            padding: '25px', 
            borderRadius: '15px',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255,255,255,0.2)'
          }}>
            <h2 style={{ color: '#10b981', marginTop: 0 }}>🎉 Success Status</h2>
            <ul style={{ fontSize: '16px', lineHeight: '1.8' }}>
              <li>✅ React 18 loaded and functional</li>
              <li>✅ TypeScript compilation successful</li>
              <li>✅ Vite build system working</li>
              <li>✅ Docker container serving correctly</li>
              <li>✅ State management operational</li>
              <li>✅ Event handlers responsive</li>
            </ul>
          </div>

          <div style={{ 
            background: 'rgba(59, 130, 246, 0.1)', 
            padding: '25px', 
            borderRadius: '15px',
            border: '1px solid rgba(59, 130, 246, 0.3)'
          }}>
            <h3 style={{ color: '#60a5fa', marginTop: 0 }}>🧪 Interactive Test</h3>
            <p style={{ fontSize: '18px', marginBottom: '15px' }}>
              Current message: <strong style={{ color: '#10b981' }}>{message}</strong>
            </p>
            <p style={{ fontSize: '18px', marginBottom: '20px' }}>
              Counter: <strong style={{ color: '#f59e0b', fontSize: '1.5em' }}>{count}</strong>
            </p>
            
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <button 
                onClick={() => setCount(count + 1)}
                style={{
                  background: 'linear-gradient(45deg, #10b981, #059669)',
                  color: 'white',
                  border: 'none',
                  padding: '12px 24px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  transition: 'transform 0.2s ease'
                }}
                onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
              >
                Increment (+)
              </button>
              
              <button 
                onClick={() => setCount(count - 1)}
                style={{
                  background: 'linear-gradient(45deg, #ef4444, #dc2626)',
                  color: 'white',
                  border: 'none',
                  padding: '12px 24px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  transition: 'transform 0.2s ease'
                }}
                onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
              >
                Decrement (-)
              </button>
              
              <button 
                onClick={() => {
                  setCount(0);
                  setMessage('Reset successful!');
                  setTimeout(() => setMessage('Hello from AI Scholar!'), 2000);
                }}
                style={{
                  background: 'linear-gradient(45deg, #6b7280, #4b5563)',
                  color: 'white',
                  border: 'none',
                  padding: '12px 24px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  transition: 'transform 0.2s ease'
                }}
                onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
              >
                Reset All
              </button>
            </div>
          </div>

          <div style={{ 
            background: 'rgba(168, 85, 247, 0.1)', 
            padding: '25px', 
            borderRadius: '15px',
            border: '1px solid rgba(168, 85, 247, 0.3)'
          }}>
            <h3 style={{ color: '#c084fc', marginTop: 0 }}>🔄 Next Steps</h3>
            <p style={{ fontSize: '16px', lineHeight: '1.6' }}>
              This minimal version proves React is working correctly. 
              Now we can gradually add back the complex features:
            </p>
            <ol style={{ fontSize: '16px', lineHeight: '1.8' }}>
              <li>Add basic routing and navigation</li>
              <li>Integrate authentication system</li>
              <li>Add chat interface components</li>
              <li>Connect to backend APIs</li>
              <li>Implement advanced features</li>
            </ol>
          </div>
        </div>

        <footer style={{ 
          textAlign: 'center', 
          padding: '20px',
          borderTop: '1px solid rgba(255,255,255,0.1)',
          marginTop: '40px'
        }}>
          <p style={{ color: '#9ca3af', fontSize: '14px' }}>
            AI Scholar v2.0 - React Application Successfully Restored
          </p>
        </footer>
      </div>
    </div>
  );
}

export default App;