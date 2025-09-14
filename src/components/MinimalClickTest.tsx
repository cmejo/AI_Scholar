/**
 * MinimalClickTest - Absolute minimal test to isolate click issues
 */
import React, { useState } from 'react';

export const MinimalClickTest: React.FC = () => {
  const [count, setCount] = useState(0);

  console.log('MinimalClickTest rendered, count:', count);

  const handleClick = () => {
    console.log('Button clicked! Current count:', count);
    setCount(prev => {
      const newCount = prev + 1;
      console.log('Setting count to:', newCount);
      return newCount;
    });
  };

  const handleDirectClick = () => {
    console.log('Direct click handler called');
    alert('Direct click works!');
  };

  return (
    <div style={{ 
      padding: '20px', 
      backgroundColor: '#1f2937', 
      color: 'white', 
      minHeight: '100vh',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1>🔧 Minimal Click Test</h1>
      <p>Testing the most basic button interactions</p>
      
      <div style={{ marginBottom: '20px' }}>
        <h2>Count: <span style={{ color: '#10b981', fontSize: '2em' }}>{count}</span></h2>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxWidth: '300px' }}>
        <button
          onClick={handleClick}
          style={{
            padding: '12px 24px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          Click Me (Count: {count})
        </button>

        <button
          onClick={handleDirectClick}
          style={{
            padding: '12px 24px',
            backgroundColor: '#ef4444',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          Alert Test
        </button>

        <button
          onClick={() => {
            console.log('Inline handler called');
            setCount(999);
          }}
          style={{
            padding: '12px 24px',
            backgroundColor: '#10b981',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          Set to 999
        </button>

        <div
          onClick={() => {
            console.log('Div clicked');
            setCount(prev => prev + 10);
          }}
          style={{
            padding: '12px 24px',
            backgroundColor: '#8b5cf6',
            color: 'white',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '16px',
            textAlign: 'center'
          }}
        >
          Clickable Div (+10)
        </div>
      </div>

      <div style={{ marginTop: '30px', padding: '15px', backgroundColor: '#374151', borderRadius: '8px' }}>
        <h3>Debug Info:</h3>
        <ul>
          <li>Component rendered: ✅</li>
          <li>Current count: {count}</li>
          <li>React state working: {count > 0 ? '✅' : '❓'}</li>
          <li>Console logging: Check browser console</li>
        </ul>
      </div>

      <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}>
        <h3>Instructions:</h3>
        <ol>
          <li>Open browser console (F12)</li>
          <li>Click any button above</li>
          <li>Check if console shows click events</li>
          <li>Check if count increases</li>
          <li>If nothing happens, there's a fundamental React/JS issue</li>
        </ol>
      </div>
    </div>
  );
};