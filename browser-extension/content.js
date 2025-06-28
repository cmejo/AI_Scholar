/**
 * Content Script for AI Scholar Extension
 * Handles text selection, UI injection, and page interaction
 */

// Global state
let isExtensionActive = false;
let selectedText = '';
let selectionRange = null;

// Initialize content script
function initializeContentScript() {
  console.log('AI Scholar content script loaded');
  
  // Add selection event listeners
  document.addEventListener('mouseup', handleTextSelection);
  document.addEventListener('keyup', handleTextSelection);
  
  // Add keyboard shortcuts
  document.addEventListener('keydown', handleKeyboardShortcuts);
  
  // Listen for messages from background script
  chrome.runtime.onMessage.addListener(handleMessage);
  
  // Add floating action button styles
  addFloatingButtonStyles();
}

// Handle text selection
function handleTextSelection(event) {
  setTimeout(() => {
    const selection = window.getSelection();
    const text = selection.toString().trim();
    
    if (text.length > 0 && text.length <= 5000) {
      selectedText = text;
      selectionRange = selection.getRangeAt(0);
      showFloatingActionButton(event);
    } else {
      hideFloatingActionButton();
      selectedText = '';
      selectionRange = null;
    }
  }, 10);
}

// Handle keyboard shortcuts
function handleKeyboardShortcuts(event) {
  // Ctrl/Cmd + Shift + E = Explain
  if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'E') {
    event.preventDefault();
    if (selectedText) {
      processTextWithAI('explain');
    }
  }
  
  // Ctrl/Cmd + Shift + S = Summarize
  if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'S') {
    event.preventDefault();
    if (selectedText) {
      processTextWithAI('summarize');
    }
  }
  
  // Ctrl/Cmd + Shift + R = Rewrite
  if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'R') {
    event.preventDefault();
    if (selectedText) {
      processTextWithAI('rewrite');
    }
  }
  
  // Escape = Close any open AI Scholar UI
  if (event.key === 'Escape') {
    closeAllAIScholarUI();
  }
}

// Show floating action button
function showFloatingActionButton(event) {
  hideFloatingActionButton(); // Remove existing button
  
  const button = document.createElement('div');
  button.id = 'ai-scholar-floating-button';
  button.className = 'ai-scholar-floating-button';
  
  // Position near the selection
  const rect = selectionRange.getBoundingClientRect();
  const buttonTop = rect.bottom + window.scrollY + 5;
  const buttonLeft = rect.left + window.scrollX;
  
  button.style.top = `${buttonTop}px`;
  button.style.left = `${buttonLeft}px`;
  
  button.innerHTML = `
    <div class="ai-scholar-button-content">
      <div class="ai-scholar-logo">🤖</div>
      <div class="ai-scholar-actions">
        <button class="ai-scholar-action" data-action="explain" title="Explain (Ctrl+Shift+E)">
          💡 Explain
        </button>
        <button class="ai-scholar-action" data-action="summarize" title="Summarize (Ctrl+Shift+S)">
          📝 Summarize
        </button>
        <button class="ai-scholar-action" data-action="rewrite" title="Rewrite (Ctrl+Shift+R)">
          ✏️ Rewrite
        </button>
        <button class="ai-scholar-action" data-action="translate" title="Translate">
          🌐 Translate
        </button>
      </div>
    </div>
  `;
  
  document.body.appendChild(button);
  
  // Add event listeners
  button.querySelectorAll('.ai-scholar-action').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const action = btn.getAttribute('data-action');
      processTextWithAI(action);
    });
  });
  
  // Auto-hide after 10 seconds
  setTimeout(() => {
    hideFloatingActionButton();
  }, 10000);
  
  // Hide on click outside
  setTimeout(() => {
    document.addEventListener('click', hideFloatingButtonOnClickOutside, { once: true });
  }, 100);
}

// Hide floating action button
function hideFloatingActionButton() {
  const button = document.getElementById('ai-scholar-floating-button');
  if (button) {
    button.remove();
  }
}

// Hide floating button on click outside
function hideFloatingButtonOnClickOutside(event) {
  const button = document.getElementById('ai-scholar-floating-button');
  if (button && !button.contains(event.target)) {
    hideFloatingActionButton();
  }
}

// Process text with AI
async function processTextWithAI(action) {
  if (!selectedText) {
    showNotification('Please select some text first', 'warning');
    return;
  }
  
  hideFloatingActionButton();
  showLoadingIndicator();
  
  try {
    // Send message to background script
    const response = await chrome.runtime.sendMessage({
      type: 'processText',
      text: selectedText,
      action: action,
      context: {
        url: window.location.href,
        title: document.title,
        domain: window.location.hostname
      }
    });
    
    if (response.success) {
      showResultModal(action, selectedText, response.data);
    } else {
      throw new Error(response.error || 'Failed to process text');
    }
  } catch (error) {
    console.error('Error processing text:', error);
    showNotification(`Failed to ${action} text: ${error.message}`, 'error');
  } finally {
    hideLoadingIndicator();
  }
}

// Show loading indicator
function showLoadingIndicator() {
  const loader = document.createElement('div');
  loader.id = 'ai-scholar-loader';
  loader.className = 'ai-scholar-loader';
  loader.innerHTML = `
    <div class="ai-scholar-loader-content">
      <div class="ai-scholar-spinner"></div>
      <div class="ai-scholar-loader-text">AI Scholar is thinking...</div>
    </div>
  `;
  
  document.body.appendChild(loader);
}

// Hide loading indicator
function hideLoadingIndicator() {
  const loader = document.getElementById('ai-scholar-loader');
  if (loader) {
    loader.remove();
  }
}

// Show result modal
function showResultModal(action, originalText, response) {
  const modal = document.createElement('div');
  modal.id = 'ai-scholar-result-modal';
  modal.className = 'ai-scholar-modal';
  
  modal.innerHTML = `
    <div class="ai-scholar-modal-overlay"></div>
    <div class="ai-scholar-modal-content">
      <div class="ai-scholar-modal-header">
        <h3>AI Scholar - ${action.charAt(0).toUpperCase() + action.slice(1)}</h3>
        <button class="ai-scholar-close-button" title="Close (Esc)">×</button>
      </div>
      
      <div class="ai-scholar-modal-body">
        <div class="ai-scholar-original-text">
          <h4>Original Text:</h4>
          <div class="ai-scholar-text-content">${originalText}</div>
        </div>
        
        <div class="ai-scholar-ai-response">
          <h4>AI Response:</h4>
          <div class="ai-scholar-response-content">${response.response || response.answer || 'No response received'}</div>
        </div>
      </div>
      
      <div class="ai-scholar-modal-footer">
        <button class="ai-scholar-button ai-scholar-button-secondary" id="ai-scholar-copy-btn">
          📋 Copy Response
        </button>
        <button class="ai-scholar-button ai-scholar-button-secondary" id="ai-scholar-insert-btn">
          📝 Insert Below Selection
        </button>
        <button class="ai-scholar-button ai-scholar-button-primary" id="ai-scholar-close-modal-btn">
          Close
        </button>
      </div>
    </div>
  `;
  
  document.body.appendChild(modal);
  
  // Add event listeners
  const closeModal = () => {
    modal.remove();
    document.removeEventListener('keydown', handleModalKeydown);
  };
  
  const handleModalKeydown = (e) => {
    if (e.key === 'Escape') {
      closeModal();
    }
  };
  
  modal.querySelector('.ai-scholar-close-button').addEventListener('click', closeModal);
  modal.querySelector('#ai-scholar-close-modal-btn').addEventListener('click', closeModal);
  modal.querySelector('.ai-scholar-modal-overlay').addEventListener('click', closeModal);
  document.addEventListener('keydown', handleModalKeydown);
  
  // Copy response
  modal.querySelector('#ai-scholar-copy-btn').addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(response.response || response.answer);
      showNotification('Response copied to clipboard!', 'success');
    } catch (error) {
      console.error('Failed to copy:', error);
      showNotification('Failed to copy response', 'error');
    }
  });
  
  // Insert response below selection
  modal.querySelector('#ai-scholar-insert-btn').addEventListener('click', () => {
    insertResponseBelowSelection(response.response || response.answer);
    closeModal();
    showNotification('Response inserted below selection', 'success');
  });
  
  // Focus management
  modal.querySelector('.ai-scholar-close-button').focus();
}

// Insert response below selection
function insertResponseBelowSelection(responseText) {
  if (!selectionRange) return;
  
  try {
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(selectionRange);
    
    // Create a new element with the response
    const responseElement = document.createElement('div');
    responseElement.className = 'ai-scholar-inserted-response';
    responseElement.style.cssText = `
      margin: 10px 0;
      padding: 12px;
      background: #f0f9ff;
      border-left: 4px solid #3b82f6;
      border-radius: 4px;
      font-family: inherit;
      font-size: 14px;
      line-height: 1.5;
    `;
    responseElement.innerHTML = `
      <div style="font-weight: 600; color: #1e40af; margin-bottom: 8px;">
        🤖 AI Scholar Response:
      </div>
      <div>${responseText}</div>
    `;
    
    // Insert after the selection
    const range = selectionRange.cloneRange();
    range.collapse(false); // Move to end of selection
    range.insertNode(responseElement);
    
    // Clear selection
    selection.removeAllRanges();
    
  } catch (error) {
    console.error('Failed to insert response:', error);
    showNotification('Failed to insert response', 'error');
  }
}

// Show notification
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `ai-scholar-notification ai-scholar-notification-${type}`;
  notification.textContent = message;
  
  document.body.appendChild(notification);
  
  // Auto-remove after 3 seconds
  setTimeout(() => {
    notification.remove();
  }, 3000);
}

// Close all AI Scholar UI elements
function closeAllAIScholarUI() {
  hideFloatingActionButton();
  hideLoadingIndicator();
  
  const modal = document.getElementById('ai-scholar-result-modal');
  if (modal) {
    modal.remove();
  }
}

// Add floating button styles
function addFloatingButtonStyles() {
  if (document.getElementById('ai-scholar-styles')) return;
  
  const styles = document.createElement('style');
  styles.id = 'ai-scholar-styles';
  styles.textContent = `
    .ai-scholar-floating-button {
      position: absolute;
      z-index: 10000;
      background: white;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 13px;
      max-width: 300px;
      animation: ai-scholar-fade-in 0.2s ease;
    }
    
    .ai-scholar-button-content {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px;
    }
    
    .ai-scholar-logo {
      font-size: 16px;
      padding: 4px;
    }
    
    .ai-scholar-actions {
      display: flex;
      gap: 4px;
      flex-wrap: wrap;
    }
    
    .ai-scholar-action {
      background: #f3f4f6;
      border: 1px solid #d1d5db;
      border-radius: 4px;
      padding: 4px 8px;
      font-size: 11px;
      cursor: pointer;
      transition: all 0.2s;
      white-space: nowrap;
    }
    
    .ai-scholar-action:hover {
      background: #3b82f6;
      color: white;
      border-color: #3b82f6;
    }
    
    .ai-scholar-loader {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10001;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    .ai-scholar-loader-content {
      background: white;
      padding: 24px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      gap: 12px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    .ai-scholar-spinner {
      width: 20px;
      height: 20px;
      border: 2px solid #3b82f6;
      border-top: 2px solid transparent;
      border-radius: 50%;
      animation: ai-scholar-spin 1s linear infinite;
    }
    
    .ai-scholar-modal {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      z-index: 10002;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    .ai-scholar-modal-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
    }
    
    .ai-scholar-modal-content {
      position: relative;
      background: white;
      margin: 5% auto;
      width: 90%;
      max-width: 600px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      max-height: 80vh;
      display: flex;
      flex-direction: column;
    }
    
    .ai-scholar-modal-header {
      padding: 20px;
      border-bottom: 1px solid #e5e7eb;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .ai-scholar-modal-header h3 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      color: #1f2937;
    }
    
    .ai-scholar-close-button {
      background: none;
      border: none;
      font-size: 24px;
      cursor: pointer;
      color: #6b7280;
      padding: 0;
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 4px;
    }
    
    .ai-scholar-close-button:hover {
      background: #f3f4f6;
    }
    
    .ai-scholar-modal-body {
      padding: 20px;
      overflow-y: auto;
      flex: 1;
    }
    
    .ai-scholar-original-text,
    .ai-scholar-ai-response {
      margin-bottom: 20px;
    }
    
    .ai-scholar-original-text h4,
    .ai-scholar-ai-response h4 {
      margin: 0 0 8px 0;
      font-size: 14px;
      font-weight: 600;
      color: #374151;
    }
    
    .ai-scholar-text-content {
      background: #f3f4f6;
      padding: 12px;
      border-radius: 6px;
      font-size: 13px;
      color: #4b5563;
      border-left: 3px solid #3b82f6;
      max-height: 120px;
      overflow-y: auto;
    }
    
    .ai-scholar-response-content {
      background: #ffffff;
      padding: 16px;
      border-radius: 6px;
      font-size: 14px;
      line-height: 1.6;
      color: #1f2937;
      border: 1px solid #e5e7eb;
    }
    
    .ai-scholar-modal-footer {
      padding: 20px;
      border-top: 1px solid #e5e7eb;
      display: flex;
      gap: 8px;
      justify-content: flex-end;
    }
    
    .ai-scholar-button {
      padding: 8px 16px;
      border-radius: 6px;
      font-size: 13px;
      cursor: pointer;
      border: 1px solid;
      transition: all 0.2s;
    }
    
    .ai-scholar-button-primary {
      background: #3b82f6;
      color: white;
      border-color: #3b82f6;
    }
    
    .ai-scholar-button-primary:hover {
      background: #2563eb;
      border-color: #2563eb;
    }
    
    .ai-scholar-button-secondary {
      background: #f3f4f6;
      color: #374151;
      border-color: #d1d5db;
    }
    
    .ai-scholar-button-secondary:hover {
      background: #e5e7eb;
      border-color: #9ca3af;
    }
    
    .ai-scholar-notification {
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 12px 20px;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 500;
      z-index: 10003;
      animation: ai-scholar-slide-in 0.3s ease;
      max-width: 300px;
    }
    
    .ai-scholar-notification-success {
      background: #10b981;
      color: white;
    }
    
    .ai-scholar-notification-error {
      background: #ef4444;
      color: white;
    }
    
    .ai-scholar-notification-warning {
      background: #f59e0b;
      color: white;
    }
    
    .ai-scholar-notification-info {
      background: #3b82f6;
      color: white;
    }
    
    .ai-scholar-inserted-response {
      user-select: text;
    }
    
    @keyframes ai-scholar-fade-in {
      from { opacity: 0; transform: scale(0.95); }
      to { opacity: 1; transform: scale(1); }
    }
    
    @keyframes ai-scholar-spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    
    @keyframes ai-scholar-slide-in {
      from { transform: translateX(100%); }
      to { transform: translateX(0); }
    }
  `;
  
  document.head.appendChild(styles);
}

// Handle messages from background script
function handleMessage(message, sender, sendResponse) {
  switch (message.type) {
    case 'getPageContent':
      sendResponse(getPageContent());
      break;
    
    case 'highlightText':
      highlightText(message.text);
      sendResponse({ success: true });
      break;
    
    case 'showNotification':
      showNotification(message.message, message.type);
      sendResponse({ success: true });
      break;
    
    default:
      sendResponse({ error: 'Unknown message type' });
  }
}

// Get page content for AI analysis
function getPageContent() {
  return {
    title: document.title,
    url: window.location.href,
    domain: window.location.hostname,
    text: document.body.innerText.slice(0, 5000), // Limit to 5000 chars
    headings: Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'))
      .map(h => ({
        level: parseInt(h.tagName.charAt(1)),
        text: h.innerText.trim()
      }))
      .slice(0, 20),
    links: Array.from(document.querySelectorAll('a[href]'))
      .filter(link => link.innerText.trim().length > 0)
      .map(link => ({
        text: link.innerText.trim(),
        href: link.href
      }))
      .slice(0, 10)
  };
}

// Highlight text on page
function highlightText(text) {
  // Simple text highlighting implementation
  const walker = document.createTreeWalker(
    document.body,
    NodeFilter.SHOW_TEXT,
    null,
    false
  );
  
  const textNodes = [];
  let node;
  
  while (node = walker.nextNode()) {
    if (node.textContent.includes(text)) {
      textNodes.push(node);
    }
  }
  
  textNodes.forEach(textNode => {
    const parent = textNode.parentNode;
    const content = textNode.textContent;
    const index = content.indexOf(text);
    
    if (index !== -1) {
      const before = content.substring(0, index);
      const match = content.substring(index, index + text.length);
      const after = content.substring(index + text.length);
      
      const beforeNode = document.createTextNode(before);
      const highlightNode = document.createElement('mark');
      highlightNode.style.backgroundColor = '#fef3c7';
      highlightNode.style.color = '#92400e';
      highlightNode.textContent = match;
      const afterNode = document.createTextNode(after);
      
      parent.insertBefore(beforeNode, textNode);
      parent.insertBefore(highlightNode, textNode);
      parent.insertBefore(afterNode, textNode);
      parent.removeChild(textNode);
    }
  });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeContentScript);
} else {
  initializeContentScript();
}