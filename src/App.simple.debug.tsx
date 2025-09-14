import React from 'react';

function App(): JSX.Element {
  console.log('🚀 SIMPLE DEBUG APP LOADED');
  
  React.useEffect(() => {
    console.log('🚀 SIMPLE DEBUG APP MOUNTED');
    document.title = 'AI Scholar - Debug Mode';
  }, []);

  const [count, setCount] = React.useState(0);

  return (
    <div style={{ 
      padding: '40px', 
      background: '#1a1a1a', 
      color: 'white', 
      minHeight: '100vh',
      fontFamily: 'Arial, sans-serif'
    }}>
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <h1 style={{ color: '#10b981', fontSize: '2.5em', marginBottom: '20px' }}>
          ✅ AI Scholar - React Debug Mode
        </h1>
        
        <div style={{ 
          background: '#374151', 
          padding: '20px', 
          borderRadius: '12px', 
          marginBottom: '20px' 
        }}>
          <h2 style={{ color: '#60a5fa', marginTop: 0 }}>🔧 React Status Check</h2>
          <ul style={{ fontSize: '16px', lineHeight: '1.6' }}>
            <li>✅ React component loaded successfully</li>
            <li>✅ JSX rendering correctly</li>
            <li>✅ React hooks working (useState, useEffect)</li>
            <li>✅ Event handlers functional</li>
            <li>✅ Styles applied correctly</li>
          </ul>
        </div>

        <div style={{ 
          background: '#4c1d95', 
          padding: '20px', 
          borderRadius: '12px', 
          marginBottom: '20px' 
        }}>
          <h3 style={{ marginTop: 0, color: '#c4b5fd' }}>🧪 Interactive Test</h3>
          <p>Counter: <strong style={{ color: '#10b981', fontSize: '1.5em' }}>{count}</strong></p>
          <div style={{ display: 'flex', gap: '10px', marginTop: '15px' }}>
            <button 
              onClick={() => setCount(count + 1)}
              style={{
                background: '#10b981',
                color: 'white',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: 'bold'
              }}
            >
              Increment (+)
            </button>
            <button 
              onClick={() => setCount(count - 1)}
              style={{
                background: '#ef4444',
                color: 'white',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: 'bold'
              }}
            >
              Decrement (-)
            </button>
            <button 
              onClick={() => setCount(0)}
              style={{
                background: '#6b7280',
                color: 'white',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: 'bold'
              }}
            >
              Reset
            </button>
          </div>
        </div>

        <div style={{ 
          background: '#065f46', 
          padding: '20px', 
          borderRadius: '12px', 
          marginBottom: '20px' 
        }}>
          <h3 style={{ marginTop: 0, color: '#6ee7b7' }}>🎉 Success!</h3>
          <p style={{ fontSize: '18px', lineHeight: '1.6' }}>
            If you can see this page and interact with the buttons above, 
            React is working perfectly! The issue with the main application 
            is likely in the complex component structure or dependencies.
          </p>
        </div>

        <div style={{ 
          background: '#1e3a8a', 
          padding: '20px', 
          borderRadius: '12px' 
        }}>
          <h3 style={{ marginTop: 0, color: '#93c5fd' }}>🔄 Next Steps</h3>
          <p>To restore the full AI Scholar application:</p>
          <ol style={{ fontSize: '16px', lineHeight: '1.6' }}>
            <li>Verify this debug version works completely</li>
            <li>Gradually add back complex components</li>
            <li>Identify which component is causing the issue</li>
            <li>Fix the problematic component</li>
          </ol>
        </div>
      </div>
    </div>
  );
}

export default App;