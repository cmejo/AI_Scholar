import React from 'react';

function AbsoluteMinimal() {
  return React.createElement('div', {
    style: {
      padding: '50px',
      background: '#000',
      color: '#fff',
      fontSize: '30px',
      textAlign: 'center',
      minHeight: '100vh'
    }
  }, 'HELLO WORLD - REACT IS WORKING!');
}

export default AbsoluteMinimal;