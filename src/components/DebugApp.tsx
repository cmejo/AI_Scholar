import React from 'react';

const DebugApp: React.FC = () => {
  console.log('DebugApp is rendering');
  
  return (
    <div style={{ 
      padding: '20px', 
      backgroundColor: '#1a1a1a', 
      color: 'white', 
      minHeight: '100vh',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1>🚀 AI Scholar Debug Mode</h1>
      <p>If you can see this, React is working!</p>
      
      <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#333', borderRadius: '8px' }}>
        <h2>System Status:</h2>
        <ul>
          <li>✅ React is rendering</li>
          <li>✅ TypeScript is compiling</li>
          <li>✅ CSS is loading</li>
          <li>✅ Components are working</li>
        </ul>
      </div>
      
      <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#2a4a2a', borderRadius: '8px' }}>
        <h2>Next Steps:</h2>
        <ol>
          <li>Check browser console for any errors</li>
          <li>Verify all dependencies are installed</li>
          <li>Test individual components</li>
          <li>Switch back to main App when ready</li>
        </ol>
      </div>
      
      <button 
        onClick={() => {
          console.log('Button clicked!');
          alert('Button works!');
        }}
        style={{
          marginTop: '20px',
          padding: '10px 20px',
          backgroundColor: '#4CAF50',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer'
        }}
      >
        Test Button
      </button>
    </div>
  );
};

export default DebugApp;