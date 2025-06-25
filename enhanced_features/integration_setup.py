#!/usr/bin/env python3
"""
Enhanced UX Features Integration Setup
Complete setup script for streaming chat, markdown rendering, and chat history management
"""

import os
import sys
from pathlib import Path
import shutil
import json

def print_status(message, status="INFO"):
    """Print colored status messages"""
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m", 
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "RESET": "\033[0m"
    }
    print(f"{colors.get(status, '')}{status}: {message}{colors['RESET']}")

def setup_backend_integration():
    """Setup backend integration for enhanced features"""
    print_status("Setting up backend integration...")
    
    # Check if main app.py exists
    if not os.path.exists('app.py'):
        print_status("app.py not found. Please run this from your project root.", "ERROR")
        return False
    
    # Create integration code for app.py
    integration_code = '''
# Enhanced UX Features Integration
from enhanced_features.streaming_chat import integrate_streaming_with_app
from enhanced_features.chat_history_management import setup_chat_history_management

# Add this after your app and socketio initialization
def setup_enhanced_features(app, socketio):
    """Setup all enhanced UX features"""
    try:
        # Setup streaming chat
        integrate_streaming_with_app(app, socketio)
        
        # Setup chat history management
        setup_chat_history_management(app)
        
        print("✅ Enhanced UX features integrated successfully!")
        return True
    except Exception as e:
        print(f"❌ Error setting up enhanced features: {e}")
        return False

# Call this function after creating your app and socketio
# setup_enhanced_features(app, socketio)
'''
    
    # Write integration instructions
    with open('enhanced_features_integration.py', 'w') as f:
        f.write(integration_code)
    
    print_status("Backend integration code created: enhanced_features_integration.py", "SUCCESS")
    return True

def setup_frontend_integration():
    """Setup frontend integration"""
    print_status("Setting up frontend integration...")
    
    # Check if frontend directory exists
    frontend_dir = Path('frontend/src')
    if not frontend_dir.exists():
        print_status("Frontend directory not found. Creating example structure...", "WARNING")
        frontend_dir.mkdir(parents=True, exist_ok=True)
    
    # Create enhanced components directory
    enhanced_components_dir = frontend_dir / 'components' / 'enhanced'
    enhanced_components_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy enhanced components
    enhanced_files = [
        'StreamingChatComponent.js',
        'MarkdownRenderer.js',
        'ChatHistoryComponents.js'
    ]
    
    for file_name in enhanced_files:
        src_file = Path('enhanced_features/frontend') / file_name
        dst_file = enhanced_components_dir / file_name
        
        if src_file.exists():
            shutil.copy2(src_file, dst_file)
            print_status(f"Copied {file_name} to frontend/src/components/enhanced/", "SUCCESS")
        else:
            print_status(f"Source file not found: {src_file}", "ERROR")
    
    # Create integration example
    integration_example = '''
// Enhanced Features Integration Example
// Add this to your main App.js or relevant components

import React from 'react';
import { EnhancedStreamingChatContainer } from './components/enhanced/StreamingChatComponent';
import { EnhancedMarkdownRenderer } from './components/enhanced/MarkdownRenderer';
import { EnhancedChatHistory } from './components/enhanced/ChatHistoryComponents';

// Example usage in your main chat component
export const EnhancedChatApp = () => {
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [showHistory, setShowHistory] = useState(false);

  return (
    <div className="enhanced-chat-app">
      {showHistory ? (
        <EnhancedChatHistory 
          onSelectSession={(sessionId) => {
            setCurrentSessionId(sessionId);
            setShowHistory(false);
          }}
        />
      ) : (
        <EnhancedStreamingChatContainer 
          sessionId={currentSessionId}
          onSessionChange={setCurrentSessionId}
        />
      )}
      
      <button 
        onClick={() => setShowHistory(!showHistory)}
        className="history-toggle"
      >
        {showHistory ? 'Back to Chat' : 'View History'}
      </button>
    </div>
  );
};

// For markdown rendering in messages
export const MessageWithMarkdown = ({ content }) => {
  return (
    <EnhancedMarkdownRenderer 
      content={content}
      theme="light"
      enableMath={true}
      enableTables={true}
    />
  );
};
'''
    
    with open(frontend_dir / 'enhanced_integration_example.js', 'w') as f:
        f.write(integration_example)
    
    print_status("Frontend integration example created", "SUCCESS")
    return True

def setup_dependencies():
    """Setup required dependencies"""
    print_status("Setting up dependencies...")
    
    # Backend dependencies
    backend_deps = [
        'flask-socketio>=5.3.0',
        'python-socketio>=5.8.0',
        'eventlet>=0.33.0'
    ]
    
    # Frontend dependencies (package.json additions)
    frontend_deps = {
        "react-markdown": "^8.0.7",
        "react-syntax-highlighter": "^15.5.0",
        "remark-gfm": "^3.0.1",
        "remark-math": "^5.1.1",
        "rehype-katex": "^6.0.3",
        "rehype-raw": "^6.1.1",
        "katex": "^0.16.8",
        "socket.io-client": "^4.7.2",
        "date-fns": "^2.30.0"
    }
    
    # Create requirements file for enhanced features
    with open('requirements-enhanced-ux.txt', 'w') as f:
        for dep in backend_deps:
            f.write(f"{dep}\n")
    
    print_status("Created requirements-enhanced-ux.txt", "SUCCESS")
    
    # Create package.json additions
    with open('frontend-dependencies-enhanced.json', 'w') as f:
        json.dump(frontend_deps, f, indent=2)
    
    print_status("Created frontend-dependencies-enhanced.json", "SUCCESS")
    
    print_status("Install backend dependencies with: pip install -r requirements-enhanced-ux.txt", "INFO")
    print_status("Add frontend dependencies to your package.json", "INFO")
    
    return True

def create_css_files():
    """Create CSS files for enhanced components"""
    print_status("Creating CSS files...")
    
    css_dir = Path('enhanced_features/css')
    css_dir.mkdir(exist_ok=True)
    
    # Combined CSS for all enhanced features
    combined_css = '''
/* Enhanced UX Features - Combined CSS */

/* Streaming Chat Styles */
.streaming-cursor {
  animation: blink 1s infinite;
  color: #3b82f6;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.message-bubble {
  word-wrap: break-word;
  transition: all 0.2s ease-in-out;
}

.user-message {
  display: flex;
  justify-content: flex-end;
}

.ai-message {
  display: flex;
  justify-content: flex-start;
}

.streaming-chat-message {
  position: relative;
}

.stream-metrics {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #e5e7eb;
}

.retry-button {
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  transition: color 0.2s ease-in-out;
}

.settings-panel {
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.enhanced-streaming-chat-container {
  height: 100vh;
  max-height: 100vh;
}

.messages-area {
  scroll-behavior: smooth;
}

.input-area textarea {
  transition: border-color 0.2s ease-in-out;
}

.input-area textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Markdown Renderer Styles */
.enhanced-markdown-renderer {
  line-height: 1.6;
}

.enhanced-markdown-renderer.dark {
  color: #e5e7eb;
}

.inline-code {
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  background-color: #f3f4f6;
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.875rem;
}

.dark .inline-code {
  background-color: #374151;
  color: #e5e7eb;
}

.code-block-container {
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  margin: 1rem 0;
  border-radius: 0.5rem;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}

.dark .code-block-container {
  border-color: #4b5563;
}

.code-header {
  background-color: #f9fafb;
  padding: 0.5rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  border-bottom: 1px solid #e5e7eb;
}

.dark .code-header {
  background-color: #374151;
  border-color: #4b5563;
}

.language-badge {
  background-color: #3b82f6;
  color: white;
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  font-size: 0.75rem;
}

.copy-button, .download-button, .expand-button {
  transition: all 0.2s ease-in-out;
  cursor: pointer;
  background: none;
  border: none;
  color: #6b7280;
}

.copy-button:hover, .download-button:hover, .expand-button:hover {
  transform: scale(1.1);
  color: #374151;
}

.dark .copy-button, .dark .download-button, .dark .expand-button {
  color: #9ca3af;
}

.dark .copy-button:hover, .dark .download-button:hover, .dark .expand-button:hover {
  color: #e5e7eb;
}

.code-fade {
  pointer-events: none;
  background: linear-gradient(to top, white, transparent);
  height: 3rem;
}

.dark .code-fade {
  background: linear-gradient(to top, #1f2937, transparent);
}

.enhanced-table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}

.enhanced-table th,
.enhanced-table td {
  border: 1px solid #e5e7eb;
  padding: 0.75rem;
  text-align: left;
}

.enhanced-table th {
  background-color: #f9fafb;
  font-weight: 600;
}

.dark .enhanced-table th {
  background-color: #374151;
  border-color: #4b5563;
}

.dark .enhanced-table td {
  border-color: #4b5563;
}

.task-item {
  list-style: none;
  margin-left: 0;
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}

.enhanced-blockquote {
  border-left: 4px solid #3b82f6;
  padding-left: 1rem;
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
  margin: 1rem 0;
  background-color: #eff6ff;
  font-style: italic;
  position: relative;
}

.dark .enhanced-blockquote {
  background-color: rgba(59, 130, 246, 0.1);
}

.quote-icon {
  position: absolute;
  left: -0.5rem;
  top: -0.5rem;
  font-size: 2rem;
  opacity: 0.3;
  color: #3b82f6;
}

.enhanced-link {
  color: #3b82f6;
  text-decoration: underline;
  transition: color 0.2s ease-in-out;
}

.enhanced-link:hover {
  color: #1d4ed8;
}

.link-preview {
  position: absolute;
  z-index: 10;
  bottom: 100%;
  left: 0;
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  font-size: 0.875rem;
  max-width: 20rem;
  animation: fadeIn 0.2s ease-in-out;
}

.dark .link-preview {
  background: #374151;
  border-color: #4b5563;
  color: #e5e7eb;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}

.image-container {
  text-align: center;
  margin: 1rem 0;
}

.image-container img {
  max-width: 100%;
  height: auto;
  border-radius: 0.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease-in-out;
}

.image-container img:hover {
  transform: scale(1.02);
}

.image-caption {
  font-size: 0.875rem;
  color: #6b7280;
  margin-top: 0.5rem;
  font-style: italic;
}

.dark .image-caption {
  color: #9ca3af;
}

/* Chat History Styles */
.session-card {
  transition: all 0.2s ease-in-out;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
}

.session-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.dark .session-card {
  background: #374151;
  border-color: #4b5563;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.search-component {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
}

.dark .search-component {
  background: #374151;
  border-color: #4b5563;
}

.search-component input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.filters-component {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
}

.dark .filters-component {
  background: #374151;
  border-color: #4b5563;
}

.filters-component select:focus,
.filters-component input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.bulk-actions {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
  animation: slideDown 0.3s ease-out;
}

.dark .bulk-actions {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.3);
}

.search-results {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  animation: fadeIn 0.3s ease-out;
}

.dark .search-results {
  background: #374151;
  border-color: #4b5563;
}

.sessions-grid {
  display: grid;
  gap: 1rem;
  animation: fadeIn 0.5s ease-out;
}

.loading {
  text-align: center;
  padding: 2rem;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.empty-state {
  text-align: center;
  padding: 3rem;
  animation: fadeIn 0.5s ease-out;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1.5rem;
}

.pagination button {
  padding: 0.5rem 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  background: white;
  color: #374151;
  transition: all 0.2s ease-in-out;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination button:not(:disabled):hover {
  background-color: #f3f4f6;
}

.dark .pagination button {
  background: #374151;
  border-color: #4b5563;
  color: #e5e7eb;
}

.dark .pagination button:not(:disabled):hover {
  background-color: #4b5563;
}

/* Responsive Design */
@media (max-width: 768px) {
  .enhanced-streaming-chat-container {
    height: 100vh;
  }
  
  .code-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .enhanced-table-container {
    overflow-x: auto;
  }
  
  .image-container img {
    max-width: 100%;
    height: auto;
  }
  
  .enhanced-chat-history {
    padding: 1rem;
  }
  
  .filters-component .grid {
    grid-template-columns: 1fr;
  }
  
  .session-card {
    padding: 0.75rem;
  }
  
  .search-component .flex {
    flex-direction: column;
    gap: 0.5rem;
  }
}

/* Dark mode utilities */
.dark {
  color-scheme: dark;
}

.dark * {
  border-color: #4b5563;
}

.dark input,
.dark textarea,
.dark select {
  background-color: #374151;
  color: #e5e7eb;
  border-color: #4b5563;
}

.dark input:focus,
.dark textarea:focus,
.dark select:focus {
  border-color: #3b82f6;
}

/* Utility classes */
.transition-all {
  transition: all 0.2s ease-in-out;
}

.hover-scale:hover {
  transform: scale(1.05);
}

.fade-in {
  animation: fadeIn 0.3s ease-out;
}

.slide-down {
  animation: slideDown 0.3s ease-out;
}
'''
    
    with open(css_dir / 'enhanced-ux.css', 'w') as f:
        f.write(combined_css)
    
    print_status("Created enhanced-ux.css", "SUCCESS")
    return True

def create_documentation():
    """Create comprehensive documentation"""
    print_status("Creating documentation...")
    
    docs_dir = Path('enhanced_features/docs')
    docs_dir.mkdir(exist_ok=True)
    
    # Main documentation
    main_doc = '''# Enhanced UX Features Documentation

## Overview

This package provides three major enhancements to your AI Scholar Chatbot:

1. **Streaming Chat Responses** - Real-time response streaming with WebSocket support
2. **Markdown and Code Block Rendering** - Advanced markdown rendering with syntax highlighting
3. **Advanced Chat History Management** - Comprehensive chat session management with search

## Quick Start

### Backend Integration

1. Install dependencies:
```bash
pip install -r requirements-enhanced-ux.txt
```

2. Add to your main app.py:
```python
from enhanced_features_integration import setup_enhanced_features

# After creating app and socketio
setup_enhanced_features(app, socketio)
```

### Frontend Integration

1. Install dependencies:
```bash
npm install react-markdown react-syntax-highlighter socket.io-client date-fns
```

2. Copy enhanced components to your frontend:
```bash
cp -r enhanced_features/frontend/* frontend/src/components/enhanced/
```

3. Import and use components:
```javascript
import { EnhancedStreamingChatContainer } from './components/enhanced/StreamingChatComponent';
import { EnhancedMarkdownRenderer } from './components/enhanced/MarkdownRenderer';
import { EnhancedChatHistory } from './components/enhanced/ChatHistoryComponents';
```

## Features

### 1. Streaming Chat Responses

**Benefits:**
- Real-time response streaming
- Improved perceived performance
- WebSocket and HTTP streaming support
- Cancellation support
- Performance metrics

**Usage:**
```javascript
const { isStreaming, streamingMessage, sendStreamingMessage } = useStreamingChat();

await sendStreamingMessage("Hello AI!", sessionId, {
  model: "llama2:7b-chat",
  systemPrompt: "You are a helpful assistant"
});
```

### 2. Markdown Rendering

**Benefits:**
- Syntax highlighting for code blocks
- Math equation rendering (LaTeX)
- Interactive tables
- Task lists with checkboxes
- Image handling with captions

**Usage:**
```javascript
<EnhancedMarkdownRenderer 
  content={messageContent}
  theme="light"
  enableMath={true}
  enableTables={true}
  showLineNumbers={true}
/>
```

### 3. Chat History Management

**Benefits:**
- Advanced search (content, semantic, session names)
- Bulk operations (delete multiple sessions)
- Session renaming and organization
- Export functionality (JSON, Markdown, Text)
- Usage analytics and statistics

**Usage:**
```javascript
const {
  sessions,
  searchHistory,
  updateSessionName,
  deleteSession,
  exportSession
} = useChatHistory();

// Search chat history
const results = await searchHistory("machine learning", "semantic");

// Rename session
await updateSessionName(sessionId, "New Session Name");
```

## API Endpoints

### Streaming Chat
- `POST /api/chat/stream` - Stream chat responses
- `GET /api/chat/stream/<id>/status` - Get stream status
- `POST /api/chat/stream/<id>/cancel` - Cancel stream

### Chat History
- `GET /api/chat/sessions` - Get sessions with filtering
- `PUT /api/chat/sessions/<id>` - Update session name
- `DELETE /api/chat/sessions/<id>` - Delete session
- `POST /api/chat/sessions/bulk-delete` - Delete multiple sessions
- `GET /api/chat/search` - Search chat history
- `GET /api/chat/sessions/<id>/export` - Export session
- `GET /api/chat/analytics` - Get usage analytics

## Configuration

### Environment Variables
```bash
# Streaming settings
STREAM_CHUNK_SIZE=1024
STREAM_TIMEOUT=30

# History settings
HISTORY_PAGE_SIZE=20
SEARCH_LIMIT=50
```

### Frontend Configuration
```javascript
// Configure streaming
const streamingConfig = {
  apiUrl: 'http://localhost:5000',
  useWebSocket: true,
  retryAttempts: 3
};

// Configure markdown
const markdownConfig = {
  theme: 'light',
  enableMath: true,
  enableTables: true,
  showLineNumbers: true
};
```

## Customization

### Themes
Both markdown renderer and chat components support light/dark themes:

```javascript
// Light theme
<EnhancedMarkdownRenderer theme="light" />

// Dark theme
<EnhancedMarkdownRenderer theme="dark" />
```

### Custom Styling
Include the enhanced-ux.css file or customize the CSS variables:

```css
:root {
  --primary-color: #3b82f6;
  --secondary-color: #6b7280;
  --background-color: #ffffff;
  --text-color: #1f2937;
}
```

## Performance Optimization

### Streaming
- Use WebSocket for better performance
- Implement connection pooling
- Add response caching

### Markdown
- Lazy load syntax highlighter
- Cache rendered content
- Optimize image loading

### History
- Implement virtual scrolling for large lists
- Use pagination for better performance
- Cache search results

## Troubleshooting

### Common Issues

1. **Streaming not working**
   - Check WebSocket connection
   - Verify CORS settings
   - Check firewall/proxy settings

2. **Markdown not rendering**
   - Verify react-markdown installation
   - Check syntax highlighter themes
   - Ensure proper CSS loading

3. **History search slow**
   - Add database indexes
   - Implement search caching
   - Use pagination

### Debug Mode
Enable debug logging:

```python
import logging
logging.getLogger('enhanced_features').setLevel(logging.DEBUG)
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

MIT License - see LICENSE file for details.
'''
    
    with open(docs_dir / 'README.md', 'w') as f:
        f.write(main_doc)
    
    print_status("Created comprehensive documentation", "SUCCESS")
    return True

def main():
    """Main setup function"""
    print_status("🚀 Enhanced UX Features Setup", "INFO")
    print_status("=" * 60, "INFO")
    
    success = True
    
    # Setup backend integration
    if not setup_backend_integration():
        success = False
    
    # Setup frontend integration
    if not setup_frontend_integration():
        success = False
    
    # Setup dependencies
    if not setup_dependencies():
        success = False
    
    # Create CSS files
    if not create_css_files():
        success = False
    
    # Create documentation
    if not create_documentation():
        success = False
    
    if success:
        print_status("=" * 60, "SUCCESS")
        print_status("🎉 Enhanced UX Features setup completed successfully!", "SUCCESS")
        print_status("=" * 60, "SUCCESS")
        
        print("\n📋 Next steps:")
        print("1. Install backend dependencies: pip install -r requirements-enhanced-ux.txt")
        print("2. Install frontend dependencies from frontend-dependencies-enhanced.json")
        print("3. Add integration code from enhanced_features_integration.py to your app.py")
        print("4. Copy enhanced components to your frontend")
        print("5. Include enhanced-ux.css in your frontend")
        print("6. Test the enhanced features!")
        
        print("\n🔧 Available features:")
        print("- ⚡ Streaming chat responses with real-time typing")
        print("- 📝 Advanced markdown rendering with code highlighting")
        print("- 📚 Comprehensive chat history management")
        print("- 🔍 Advanced search capabilities")
        print("- 📊 Usage analytics and statistics")
        print("- 🎨 Dark/light theme support")
        
        print("\n📚 Documentation:")
        print("- Main docs: enhanced_features/docs/README.md")
        print("- Integration guide: enhanced_features_integration.py")
        print("- Frontend examples: frontend/src/enhanced_integration_example.js")
        
    else:
        print_status("❌ Setup encountered some issues. Please check the errors above.", "ERROR")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_status("\nSetup interrupted by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        print_status(f"Setup failed with error: {e}", "ERROR")
        sys.exit(1)