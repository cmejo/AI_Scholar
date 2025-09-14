import React from 'react';

function SimpleApp() {
  return (
    <div style={{
      minHeight: '100vh',
      background: '#1a1a1a',
      color: 'white',
      padding: '20px',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1>🚀 AI Scholar - Working App!</h1>
      <p>If you can see this, the app is working correctly!</p>
      
      <button
        onClick={() => {
          console.log('Button clicked!');
          alert('Button works!');
        }}
        style={{
          background: '#059669',
          color: 'white',
          padding: '12px 24px',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer',
          fontSize: '16px',
          marginTop: '20px'
        }}
      >
        Test Button
      </button>
      
      <div style={{ marginTop: '20px' }}>
        <p>✅ React is working</p>
        <p>✅ Components are rendering</p>
        <p>✅ Click events are working</p>
      </div>
    </div>
  );
}

export default SimpleApp;