/**
 * UltraMinimalTest - The most basic possible test to isolate click issues
 */
import React, { useState } from 'react';

export const UltraMinimalTest: React.FC = () => {
  const [count, setCount] = useState(0);

  console.log('UltraMinimalTest rendered, count:', count);

  // Force alert on render to confirm component is loading
  React.useEffect(() => {
    console.log('UltraMinimalTest mounted!');
    // Uncomment this line if you want an alert to confirm the component loaded
    // alert('UltraMinimalTest component loaded!');
  }, []);

  return (
    <div style={{ 
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      backgroundColor: '#ff0000', // Bright red background
      color: '#fff',
      padding: '20px',
      zIndex: 99999, // Even higher z-index
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <h1 style={{ fontSize: '48px', marginBottom: '20px' }}>🔴 ULTRA MINIMAL TEST 🔴</h1>
      <p style={{ fontSize: '32px', marginBottom: '20px' }}>Count: {count}</p>
      
      <button
        onClick={() => {
          console.log('RED BUTTON CLICKED!');
          alert('RED BUTTON WORKS!');
          setCount(c => c + 1);
        }}
        style={{
          padding: '30px 60px',
          fontSize: '24px',
          backgroundColor: '#000',
          color: '#fff',
          border: '5px solid #fff',
          cursor: 'pointer',
          margin: '20px',
          borderRadius: '10px'
        }}
      >
        🔴 CLICK ME ({count}) 🔴
      </button>

      <div
        onClick={() => {
          console.log('GREEN DIV CLICKED!');
          alert('GREEN DIV WORKS!');
          setCount(c => c + 5);
        }}
        style={{
          padding: '30px 60px',
          fontSize: '24px',
          backgroundColor: '#00ff00',
          color: '#000',
          cursor: 'pointer',
          margin: '20px',
          display: 'inline-block',
          border: '5px solid #000',
          borderRadius: '10px'
        }}
      >
        🟢 CLICK DIV ({count}) 🟢
      </div>

      <div style={{ marginTop: '40px', textAlign: 'center' }}>
        <p style={{ fontSize: '18px' }}>🚨 If you can see this red screen but buttons don't work:</p>
        <p style={{ fontSize: '18px' }}>There's a fundamental click/event handling issue!</p>
        <p style={{ fontSize: '16px' }}>Check browser console (F12) for click events.</p>
      </div>

      {/* Debug info overlay */}
      <div style={{
        position: 'absolute',
        top: '20px',
        right: '20px',
        background: 'rgba(0,0,0,0.8)',
        color: 'white',
        padding: '15px',
        borderRadius: '10px',
        fontSize: '14px'
      }}>
        <div>Component: LOADED ✅</div>
        <div>Count: {count}</div>
        <div>React: WORKING ✅</div>
      </div>
    </div>
  );
};