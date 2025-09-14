import React from 'react';

export const DebugInfo: React.FC = () => {
  console.log('DebugInfo component rendered');
  
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      backgroundColor: '#00ff00',
      color: '#000',
      padding: '20px',
      zIndex: 99999,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '24px'
    }}>
      <h1>🟢 DEBUG INFO COMPONENT 🟢</h1>
      <p>This component is rendering successfully!</p>
      <p>Current time: {new Date().toLocaleTimeString()}</p>
      <p>React is working!</p>
      
      <div style={{ marginTop: '20px' }}>
        <p>If you can see this green screen, React components are loading.</p>
        <p>The issue might be with the specific UltraMinimalTest component.</p>
      </div>
    </div>
  );
};