import React from 'react';

function TestApp() {
  return (
    <div style={{ padding: '20px', background: 'black', color: 'white', minHeight: '100vh' }}>
      <h1>React App is Working!</h1>
      <div style={{ position: 'fixed', top: '10px', right: '10px', background: 'red', padding: '10px', borderRadius: '5px' }}>
        🔧 Test Bypass Login Button
      </div>
      <div style={{ position: 'fixed', bottom: '10px', right: '10px', background: 'blue', padding: '10px', borderRadius: '5px' }}>
        Auth: NO | User: None
      </div>
    </div>
  );
}

export default TestApp;