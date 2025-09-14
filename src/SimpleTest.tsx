import React from 'react';

// Ultra-simple test component
const SimpleTest: React.FC = () => {
  console.log('SimpleTest component rendered');
  
  const handleClick = () => {
    console.log('Button clicked in SimpleTest');
    alert('SimpleTest button works!');
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      backgroundColor: '#00ff00',
      color: '#000',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '24px',
      zIndex: 99999
    }}>
      <h1>🟢 SIMPLE TEST COMPONENT 🟢</h1>
      <p>If you see this, React is working!</p>
      
      <button
        onClick={handleClick}
        style={{
          padding: '20px 40px',
          fontSize: '20px',
          backgroundColor: '#ff0000',
          color: '#fff',
          border: 'none',
          cursor: 'pointer',
          margin: '20px'
        }}
      >
        CLICK ME
      </button>
      
      <p>Current time: {new Date().toLocaleTimeString()}</p>
    </div>
  );
};

export default SimpleTest;