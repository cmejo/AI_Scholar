// This will create a simple HTML string without React
const SimpleHTML = () => {
  // Just return a simple div with inline HTML
  return (
    <div 
      dangerouslySetInnerHTML={{
        __html: `
          <div style="padding: 50px; background: #1a1a1a; color: white; min-height: 100vh; font-size: 24px; text-align: center;">
            <h1 style="color: #6b46c1; margin-bottom: 30px;">🚀 Simple HTML Test</h1>
            <p>This is raw HTML inside React</p>
            <p style="margin-top: 20px; color: #10b981;">✅ No complex React features</p>
            <p style="margin-top: 20px; color: #f59e0b;">✅ Just basic rendering</p>
            <button 
              onclick="alert('HTML button works!')"
              style="margin-top: 30px; padding: 15px 30px; background: #6b46c1; color: white; border: none; border-radius: 8px; font-size: 18px; cursor: pointer;"
            >
              Test HTML Button
            </button>
          </div>
        `
      }}
    />
  );
};

export default SimpleHTML;