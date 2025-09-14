// Ultra minimal test without any imports
const PureJSTest = () => {
  // Use React from global scope (should be available after bundle loads)
  const React = (window as any).React || { createElement: () => null };
  
  return React.createElement('div', {
    style: {
      padding: '50px',
      background: '#1a1a1a',
      color: 'white',
      minHeight: '100vh',
      fontSize: '24px',
      textAlign: 'center'
    }
  }, [
    React.createElement('h1', {
      key: 'title',
      style: { color: '#6b46c1', marginBottom: '30px' }
    }, '🚀 Pure JS Test'),
    React.createElement('p', { key: 'p1' }, 'This uses React.createElement directly'),
    React.createElement('p', { 
      key: 'p2',
      style: { marginTop: '20px', color: '#10b981' }
    }, '✅ No imports required'),
    React.createElement('p', { 
      key: 'p3',
      style: { marginTop: '20px', color: '#f59e0b' }
    }, '✅ Pure JavaScript'),
    React.createElement('button', {
      key: 'button',
      style: {
        marginTop: '30px',
        padding: '15px 30px',
        background: '#6b46c1',
        color: 'white',
        border: 'none',
        borderRadius: '8px',
        fontSize: '18px',
        cursor: 'pointer'
      },
      onClick: () => alert('Button works!')
    }, 'Test Button')
  ]);
};

export default PureJSTest;