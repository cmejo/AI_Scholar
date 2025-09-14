import React from 'react';

const UltraSimpleTest = () => {
  return (
    <div style={{ 
      padding: '50px', 
      background: '#1a1a1a', 
      color: 'white', 
      minHeight: '100vh',
      fontSize: '24px',
      textAlign: 'center'
    }}>
      <h1 style={{ color: '#6b46c1', marginBottom: '30px' }}>
        🚀 Ultra Simple Test
      </h1>
      <p>If you can see this text, React is working!</p>
      <p style={{ marginTop: '20px', color: '#10b981' }}>
        ✅ JavaScript is executing
      </p>
      <p style={{ marginTop: '20px', color: '#f59e0b' }}>
        ✅ React is rendering
      </p>
      <p style={{ marginTop: '20px', color: '#ef4444' }}>
        ✅ Styles are applied
      </p>
    </div>
  );
};

export default UltraSimpleTest;