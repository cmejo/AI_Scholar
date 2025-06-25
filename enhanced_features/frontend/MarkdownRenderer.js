// Enhanced Markdown Renderer with Code Highlighting and Advanced Features
import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus, vs } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeRaw from 'rehype-raw';
import 'katex/dist/katex.min.css';

// Enhanced Code Block Component
const EnhancedCodeBlock = ({ 
  children, 
  className, 
  inline, 
  showLineNumbers = true,
  showCopyButton = true,
  theme = 'dark',
  maxHeight = '400px'
}) => {
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const codeRef = useRef(null);
  
  const match = /language-(\w+)/.exec(className || '');
  const language = match ? match[1] : 'text';
  const codeString = String(children).replace(/\n$/, '');
  
  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(codeString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  };

  const downloadCode = () => {
    const blob = new Blob([codeString], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `code.${language}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (inline) {
    return (
      <code className="inline-code bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-sm font-mono">
        {children}
      </code>
    );
  }

  const isLongCode = codeString.split('\n').length > 20;
  const displayHeight = isExpanded ? 'auto' : maxHeight;

  return (
    <div className="code-block-container relative my-4 rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
      {/* Code Block Header */}
      <div className="code-header bg-gray-100 dark:bg-gray-800 px-4 py-2 flex justify-between items-center text-sm">
        <div className="flex items-center space-x-2">
          <span className="language-badge bg-blue-500 text-white px-2 py-1 rounded text-xs">
            {language.toUpperCase()}
          </span>
          <span className="text-gray-600 dark:text-gray-400">
            {codeString.split('\n').length} lines
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          {isLongCode && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="expand-button text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
              title={isExpanded ? 'Collapse' : 'Expand'}
            >
              {isExpanded ? '📄' : '📋'}
            </button>
          )}
          
          <button
            onClick={downloadCode}
            className="download-button text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
            title="Download code"
          >
            💾
          </button>
          
          {showCopyButton && (
            <button
              onClick={copyToClipboard}
              className="copy-button text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
              title="Copy code"
            >
              {copied ? '✅' : '📋'}
            </button>
          )}
        </div>
      </div>

      {/* Code Content */}
      <div 
        className="code-content relative overflow-auto"
        style={{ maxHeight: displayHeight }}
        ref={codeRef}
      >
        <SyntaxHighlighter
          language={language}
          style={theme === 'dark' ? vscDarkPlus : vs}
          showLineNumbers={showLineNumbers}
          customStyle={{
            margin: 0,
            padding: '1rem',
            background: 'transparent'
          }}
          lineNumberStyle={{
            minWidth: '3em',
            paddingRight: '1em',
            color: '#6b7280',
            userSelect: 'none'
          }}
        >
          {codeString}
        </SyntaxHighlighter>
        
        {isLongCode && !isExpanded && (
          <div className="code-fade absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-white dark:from-gray-900 to-transparent pointer-events-none" />
        )}
      </div>
    </div>
  );
};

// Enhanced Table Component
const EnhancedTable = ({ children, ...props }) => {
  const [sortColumn, setSortColumn] = useState(null);
  const [sortDirection, setSortDirection] = useState('asc');
  const [searchTerm, setSearchTerm] = useState('');
  const [showSearch, setShowSearch] = useState(false);

  return (
    <div className="enhanced-table-container my-4">
      {/* Table Controls */}
      <div className="table-controls mb-2 flex justify-between items-center">
        <button
          onClick={() => setShowSearch(!showSearch)}
          className="search-toggle text-sm text-blue-500 hover:text-blue-700"
        >
          🔍 {showSearch ? 'Hide' : 'Show'} Search
        </button>
      </div>

      {/* Search Input */}
      {showSearch && (
        <div className="table-search mb-2">
          <input
            type="text"
            placeholder="Search table..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full p-2 border rounded text-sm"
          />
        </div>
      )}

      {/* Table */}
      <div className="table-wrapper overflow-x-auto border rounded-lg">
        <table className="enhanced-table w-full border-collapse" {...props}>
          {children}
        </table>
      </div>
    </div>
  );
};

// Enhanced List Component with Checkboxes
const EnhancedList = ({ children, ordered, ...props }) => {
  const [checkedItems, setCheckedItems] = useState(new Set());

  const toggleCheck = (index) => {
    const newChecked = new Set(checkedItems);
    if (newChecked.has(index)) {
      newChecked.delete(index);
    } else {
      newChecked.add(index);
    }
    setCheckedItems(newChecked);
  };

  const ListComponent = ordered ? 'ol' : 'ul';

  return (
    <ListComponent className="enhanced-list space-y-1" {...props}>
      {React.Children.map(children, (child, index) => {
        if (React.isValidElement(child) && child.type === 'li') {
          const content = child.props.children;
          const isTaskItem = typeof content === 'string' && 
            (content.startsWith('[ ]') || content.startsWith('[x]'));

          if (isTaskItem) {
            const isChecked = content.startsWith('[x]') || checkedItems.has(index);
            const taskText = content.replace(/^\[[ x]\]\s*/, '');

            return (
              <li key={index} className="task-item flex items-start space-x-2">
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => toggleCheck(index)}
                  className="mt-1 rounded"
                />
                <span className={isChecked ? 'line-through text-gray-500' : ''}>
                  {taskText}
                </span>
              </li>
            );
          }
        }
        return child;
      })}
    </ListComponent>
  );
};

// Math Component for LaTeX rendering
const MathComponent = ({ value, inline }) => {
  return inline ? (
    <span className="math-inline">{value}</span>
  ) : (
    <div className="math-block my-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg overflow-x-auto">
      {value}
    </div>
  );
};

// Enhanced Blockquote Component
const EnhancedBlockquote = ({ children, ...props }) => {
  return (
    <blockquote 
      className="enhanced-blockquote border-l-4 border-blue-500 pl-4 py-2 my-4 bg-blue-50 dark:bg-blue-900/20 italic"
      {...props}
    >
      <div className="quote-icon text-blue-500 text-2xl mb-2">"</div>
      {children}
    </blockquote>
  );
};

// Enhanced Link Component with Preview
const EnhancedLink = ({ href, children, ...props }) => {
  const [showPreview, setShowPreview] = useState(false);
  const [previewData, setPreviewData] = useState(null);

  const handleMouseEnter = async () => {
    if (href && href.startsWith('http')) {
      setShowPreview(true);
      // You could implement link preview fetching here
    }
  };

  return (
    <span className="relative inline-block">
      <a
        href={href}
        className="enhanced-link text-blue-500 hover:text-blue-700 underline"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={() => setShowPreview(false)}
        target="_blank"
        rel="noopener noreferrer"
        {...props}
      >
        {children}
      </a>
      
      {showPreview && (
        <div className="link-preview absolute z-10 bottom-full left-0 mb-2 p-2 bg-white dark:bg-gray-800 border rounded shadow-lg text-sm max-w-xs">
          <div className="text-gray-600 dark:text-gray-400">
            🔗 {href}
          </div>
        </div>
      )}
    </span>
  );
};

// Main Enhanced Markdown Renderer
export const EnhancedMarkdownRenderer = ({ 
  content, 
  theme = 'light',
  showLineNumbers = true,
  enableMath = true,
  enableTables = true,
  enableTaskLists = true,
  className = '',
  onLinkClick = null
}) => {
  const [isDark, setIsDark] = useState(theme === 'dark');

  useEffect(() => {
    setIsDark(theme === 'dark');
  }, [theme]);

  const components = {
    // Code blocks
    code: ({ node, inline, className, children, ...props }) => (
      <EnhancedCodeBlock
        className={className}
        inline={inline}
        showLineNumbers={showLineNumbers && !inline}
        theme={isDark ? 'dark' : 'light'}
        {...props}
      >
        {children}
      </EnhancedCodeBlock>
    ),

    // Tables
    table: enableTables ? EnhancedTable : 'table',
    
    // Lists
    ul: enableTaskLists ? (props) => <EnhancedList {...props} /> : 'ul',
    ol: enableTaskLists ? (props) => <EnhancedList ordered {...props} /> : 'ol',

    // Blockquotes
    blockquote: EnhancedBlockquote,

    // Links
    a: ({ href, children, ...props }) => (
      <EnhancedLink 
        href={href} 
        onClick={onLinkClick}
        {...props}
      >
        {children}
      </EnhancedLink>
    ),

    // Headings with anchor links
    h1: ({ children, ...props }) => (
      <h1 className="text-3xl font-bold mt-6 mb-4 text-gray-900 dark:text-gray-100" {...props}>
        {children}
      </h1>
    ),
    h2: ({ children, ...props }) => (
      <h2 className="text-2xl font-semibold mt-5 mb-3 text-gray-900 dark:text-gray-100" {...props}>
        {children}
      </h2>
    ),
    h3: ({ children, ...props }) => (
      <h3 className="text-xl font-medium mt-4 mb-2 text-gray-900 dark:text-gray-100" {...props}>
        {children}
      </h3>
    ),

    // Paragraphs
    p: ({ children, ...props }) => (
      <p className="mb-4 leading-relaxed text-gray-700 dark:text-gray-300" {...props}>
        {children}
      </p>
    ),

    // Images with enhanced features
    img: ({ src, alt, ...props }) => (
      <div className="image-container my-4">
        <img
          src={src}
          alt={alt}
          className="max-w-full h-auto rounded-lg shadow-md"
          loading="lazy"
          {...props}
        />
        {alt && (
          <div className="image-caption text-sm text-gray-600 dark:text-gray-400 mt-2 text-center italic">
            {alt}
          </div>
        )}
      </div>
    ),

    // Horizontal rules
    hr: (props) => (
      <hr className="my-6 border-gray-300 dark:border-gray-600" {...props} />
    )
  };

  const remarkPlugins = [
    remarkGfm, // GitHub Flavored Markdown
    ...(enableMath ? [remarkMath] : [])
  ];

  const rehypePlugins = [
    rehypeRaw, // Allow raw HTML
    ...(enableMath ? [rehypeKatex] : [])
  ];

  return (
    <div className={`enhanced-markdown-renderer ${className} ${isDark ? 'dark' : ''}`}>
      <ReactMarkdown
        components={components}
        remarkPlugins={remarkPlugins}
        rehypePlugins={rehypePlugins}
        className="prose prose-lg max-w-none dark:prose-invert"
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

// Markdown Editor Component (bonus feature)
export const MarkdownEditor = ({ 
  value, 
  onChange, 
  placeholder = "Type your markdown here...",
  showPreview = true 
}) => {
  const [activeTab, setActiveTab] = useState('edit');
  const [isFullscreen, setIsFullscreen] = useState(false);

  return (
    <div className={`markdown-editor ${isFullscreen ? 'fixed inset-0 z-50 bg-white' : 'relative'}`}>
      {/* Editor Header */}
      <div className="editor-header bg-gray-100 dark:bg-gray-800 p-2 flex justify-between items-center border-b">
        <div className="tabs flex space-x-2">
          <button
            onClick={() => setActiveTab('edit')}
            className={`tab px-3 py-1 rounded ${
              activeTab === 'edit' 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            ✏️ Edit
          </button>
          {showPreview && (
            <button
              onClick={() => setActiveTab('preview')}
              className={`tab px-3 py-1 rounded ${
                activeTab === 'preview' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              👁️ Preview
            </button>
          )}
        </div>
        
        <button
          onClick={() => setIsFullscreen(!isFullscreen)}
          className="fullscreen-toggle text-gray-600 hover:text-gray-800"
          title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
        >
          {isFullscreen ? '🗗' : '🗖'}
        </button>
      </div>

      {/* Editor Content */}
      <div className="editor-content h-96">
        {activeTab === 'edit' ? (
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            className="w-full h-full p-4 border-none resize-none focus:outline-none font-mono text-sm"
          />
        ) : (
          <div className="preview-content h-full overflow-y-auto p-4">
            <EnhancedMarkdownRenderer content={value} />
          </div>
        )}
      </div>
    </div>
  );
};

// CSS for enhanced markdown rendering
export const markdownStyles = `
.enhanced-markdown-renderer {
  line-height: 1.6;
}

.enhanced-markdown-renderer.dark {
  color: #e5e7eb;
}

.inline-code {
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
}

.code-block-container {
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
}

.code-header {
  font-size: 0.875rem;
}

.language-badge {
  font-weight: 600;
  letter-spacing: 0.05em;
}

.copy-button, .download-button, .expand-button {
  transition: all 0.2s ease-in-out;
  cursor: pointer;
}

.copy-button:hover, .download-button:hover, .expand-button:hover {
  transform: scale(1.1);
}

.code-fade {
  pointer-events: none;
}

.enhanced-table {
  border-collapse: collapse;
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
}

.enhanced-blockquote {
  position: relative;
}

.quote-icon {
  position: absolute;
  left: -0.5rem;
  top: -0.5rem;
  font-size: 2rem;
  opacity: 0.3;
}

.enhanced-link {
  transition: color 0.2s ease-in-out;
}

.link-preview {
  animation: fadeIn 0.2s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}

.image-container {
  text-align: center;
}

.image-container img {
  transition: transform 0.2s ease-in-out;
}

.image-container img:hover {
  transform: scale(1.02);
}

.markdown-editor {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  overflow: hidden;
}

.markdown-editor.fixed {
  background: white;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.editor-header {
  border-bottom: 1px solid #e5e7eb;
}

.tab {
  transition: all 0.2s ease-in-out;
  font-size: 0.875rem;
}

.editor-content textarea {
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  line-height: 1.5;
}

.preview-content {
  background: #fafafa;
}

.dark .preview-content {
  background: #1f2937;
}

/* Math rendering */
.math-inline {
  display: inline;
}

.math-block {
  text-align: center;
}

/* Responsive design */
@media (max-width: 768px) {
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
}
`;

export default EnhancedMarkdownRenderer;