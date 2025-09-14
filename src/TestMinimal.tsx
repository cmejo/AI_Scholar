import React from 'react';

function TestMinimal(): JSX.Element {
  console.log('🧪 MINIMAL TEST COMPONENT LOADED');
  
  React.useEffect(() => {
    console.log('🧪 MINIMAL TEST COMPONENT MOUNTED');
    document.title = 'AI Scholar - Test Mode';
  }, []);

  return (
    <div style={{ 
      padding: '20px', 
      background: '#1a1a1a', 
      color: 'white', 
      minHeight: '100vh',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1 style={{ color: '#10b981' }}>✅ React is Working!</h1>
      <p>If you can see this, React is successfully mounting and rendering.</p>
      <div style={{ 
        background: '#374151', 
        padding: '15px', 
        borderRadius: '8px', 
        margin: '20px 0' 
      }}>
        <h3>🔧 Test Results:</h3>
        <ul>
          <li>✅ React component loaded</li>
          <li>✅ JSX rendering correctly</li>
          <li>✅ Hooks working (useEffect)</li>
          <li>✅ Styles applied</li>
        </ul>
      </div>
      <button 
        onClick={() => alert('Button click works!')}
        style={{
          background: '#6366f1',
          color: 'white',
          border: 'none',
          padding: '10px 20px',
          borderRadius: '6px',
          cursor: 'pointer'
        }}
      >
        Test Button
      </button>
    </div>
  );
}

export default TestMinimal;