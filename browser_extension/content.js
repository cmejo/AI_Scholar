/**
 * AI Scholar Browser Extension - Content Script
 * Handles UI injection, text selection, and user interactions on web pages
 */

// Global state
let aiScholarWidget = null;
let isWidgetVisible = false;
let currentSelection = '';
let selectionPosition = { x: 0, y: 0 };

/**
 * Initialize content script
 */
function initializeContentScript() {
  console.log('AI Scholar content script loaded on:', window.location.href);
  
  // Create widget container
  createWidget();
  
  // Set up event listeners
  setupEventListeners();
  
  // Set up keyboard shortcuts
  setupKeyboardShortcuts();
}

/**
 * Create the AI Scholar widget
 */
function createWidget() {
  // Create widget container
  aiScholarWidget = document.createElement('div');
  aiScholarWidget.id = 'ai-scholar-widget';
  aiScholarWidget.className = 'ai-scholar-widget hidden';
  
  // Widget HTML structure
  aiScholarWidget.innerHTML = `
    <div class="ai-scholar-header">
      <div class="ai-scholar-logo">
        <span class="ai-scholar-icon">🤖</span>
        <span class="ai-scholar-title">AI Scholar</span>
      </div>
      <div class="ai-scholar-controls">
        <button class="ai-scholar-minimize" title="Minimize">−</button>
        <button class="ai-scholar-close" title="Close">×</button>
      </div>
    </div>
    
    <div class="ai-scholar-content">
      <div class="ai-scholar-loading hidden">
        <div class="ai-scholar-spinner"></div>
        <span class="ai-scholar-loading-text">Processing...</span>
      </div>
      
      <div class="ai-scholar-error hidden">
        <div class="ai-scholar-error-icon">⚠️</div>
        <div class="ai-scholar-error-message"></div>
        <button class="ai-scholar-retry-btn">Retry</button>
      </div>
      
      <div class="ai-scholar-auth-required hidden">
        <div class="ai-scholar-auth-icon">🔐</div>
        <div class="ai-scholar-auth-message">
          <p>Please configure your AI Scholar API key to use this extension.</p>
          <button class="ai-scholar-setup-btn">Setup API Key</button>
        </div>
      </div>
      
      <div class="ai-scholar-result hidden">
        <div class="ai-scholar-result-header">
          <span class="ai-scholar-action-icon"></span>
          <span class="ai-scholar-action-title"></span>
          <div class="ai-scholar-result-controls">
            <button class="ai-scholar-copy-btn" title="Copy to clipboard">📋</button>
            <button class="ai-scholar-rate-btn" title="Rate this response">⭐</button>
          </div>
        </div>
        
        <div class="ai-scholar-selected-text">
          <div class="ai-scholar-selected-label">Selected text:</div>
          <div class="ai-scholar-selected-content"></div>
        </div>
        
        <div class="ai-scholar-response">
          <div class="ai-scholar-response-label">AI Response:</div>
          <div class="ai-scholar-response-content"></div>
        </div>
        
        <div class="ai-scholar-footer">
          <div class="ai-scholar-response-time"></div>
          <div class="ai-scholar-actions">
            <button class="ai-scholar-action-btn" data-action="explain">🤔 Explain</button>
            <button class="ai-scholar-action-btn" data-action="summarize">📝 Summarize</button>
            <button class="ai-scholar-action-btn" data-action="rewrite">✏️ Rewrite</button>
          </div>
        </div>
      </div>
    </div>
    
    <div class="ai-scholar-resize-handle"></div>
  `;
  
  // Add widget to page
  document.body.appendChild(aiScholarWidget);
  
  // Set up widget event listeners
  setupWidgetEventListeners();
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
  // Text selection handling
  document.addEventListener('mouseup', handleTextSelection);
  document.addEventListener('keyup', handleTextSelection);
  
  // Selection toolbar
  document.addEventListener('mousedown', handleMouseDown);
  
  // Escape key to hide widget
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isWidgetVisible) {
      hideWidget();
    }
  });
}

/**
 * Set up keyboard shortcuts
 */
function setupKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    // Only trigger if text is selected
    if (!getSelectedText()) return;
    
    // Alt + E for Explain
    if (e.altKey && e.key === 'e') {
      e.preventDefault();
      triggerAIAction('explain');
    }
    
    // Alt + S for Summarize
    if (e.altKey && e.key === 's') {
      e.preventDefault();
      triggerAIAction('summarize');
    }
    
    // Alt + R for Rewrite
    if (e.altKey && e.key === 'r') {
      e.preventDefault();
      triggerAIAction('rewrite');
    }
  });
}

/**
 * Set up widget event listeners
 */
function setupWidgetEventListeners() {
  // Close button
  aiScholarWidget.querySelector('.ai-scholar-close').addEventListener('click', hideWidget);
  
  // Minimize button
  aiScholarWidget.querySelector('.ai-scholar-minimize').addEventListener('click', minimizeWidget);
  
  // Action buttons
  aiScholarWidget.querySelectorAll('.ai-scholar-action-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const action = e.target.dataset.action;
      triggerAIAction(action);
    });
  });
  
  // Copy button
  aiScholarWidget.querySelector('.ai-scholar-copy-btn').addEventListener('click', copyResponse);
  
  // Rate button
  aiScholarWidget.querySelector('.ai-scholar-rate-btn').addEventListener('click', showRatingDialog);
  
  // Setup button
  aiScholarWidget.querySelector('.ai-scholar-setup-btn').addEventListener('click', openSetup);
  
  // Retry button
  aiScholarWidget.querySelector('.ai-scholar-retry-btn').addEventListener('click', retryLastAction);
  
  // Make widget draggable
  makeWidgetDraggable();
  
  // Make widget resizable
  makeWidgetResizable();
}

/**
 * Handle text selection
 */
function handleTextSelection(e) {
  const selectedText = getSelectedText();
  
  if (selectedText && selectedText.length > 5) {
    currentSelection = selectedText;
    
    // Get selection position
    const selection = window.getSelection();
    if (selection.rangeCount > 0) {
      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      selectionPosition = {
        x: rect.left + rect.width / 2,
        y: rect.bottom + window.scrollY
      };
    }
    
    // Show selection toolbar after a short delay
    setTimeout(() => {
      if (getSelectedText() === selectedText) {
        showSelectionToolbar();
      }
    }, 300);
  } else {
    hideSelectionToolbar();
  }
}

/**
 * Get selected text
 */
function getSelectedText() {
  const selection = window.getSelection();
  return selection.toString().trim();
}

/**
 * Show selection toolbar
 */
function showSelectionToolbar() {
  // Remove existing toolbar
  const existingToolbar = document.getElementById('ai-scholar-selection-toolbar');
  if (existingToolbar) {
    existingToolbar.remove();
  }
  
  // Create toolbar
  const toolbar = document.createElement('div');
  toolbar.id = 'ai-scholar-selection-toolbar';
  toolbar.className = 'ai-scholar-selection-toolbar';
  
  toolbar.innerHTML = `
    <button class="ai-scholar-toolbar-btn" data-action="explain" title="Explain">🤔</button>
    <button class="ai-scholar-toolbar-btn" data-action="summarize" title="Summarize">📝</button>
    <button class="ai-scholar-toolbar-btn" data-action="rewrite" title="Rewrite">✏️</button>
    <button class="ai-scholar-toolbar-btn" data-action="translate" title="Translate">🌐</button>
    <button class="ai-scholar-toolbar-btn" data-action="analyze" title="Analyze">🔍</button>
  `;
  
  // Position toolbar
  toolbar.style.left = `${selectionPosition.x}px`;
  toolbar.style.top = `${selectionPosition.y + 10}px`;
  
  // Add event listeners
  toolbar.querySelectorAll('.ai-scholar-toolbar-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const action = e.target.dataset.action;
      triggerAIAction(action);
      hideSelectionToolbar();
    });
  });
  
  document.body.appendChild(toolbar);
  
  // Auto-hide after 5 seconds
  setTimeout(() => {
    hideSelectionToolbar();
  }, 5000);
}

/**
 * Hide selection toolbar
 */
function hideSelectionToolbar() {
  const toolbar = document.getElementById('ai-scholar-selection-toolbar');
  if (toolbar) {
    toolbar.remove();
  }
}

/**
 * Trigger AI action
 */
function triggerAIAction(action) {
  const selectedText = currentSelection || getSelectedText();
  
  if (!selectedText) {
    showError('Please select some text first');
    return;
  }
  
  // Send message to background script
  chrome.runtime.sendMessage({
    type: 'MANUAL_AI_ACTION',
    action,
    text: selectedText
  });
}

/**
 * Show widget
 */
function showWidget() {
  aiScholarWidget.classList.remove('hidden');
  isWidgetVisible = true;
  
  // Position widget
  positionWidget();
}

/**
 * Hide widget
 */
function hideWidget() {
  aiScholarWidget.classList.add('hidden');
  isWidgetVisible = false;
  hideSelectionToolbar();
}

/**
 * Position widget
 */
function positionWidget() {
  const widget = aiScholarWidget;
  const windowWidth = window.innerWidth;
  const windowHeight = window.innerHeight;
  
  // Default position (bottom-right)
  let left = windowWidth - 420;
  let top = windowHeight - 300;
  
  // Ensure widget stays within viewport
  left = Math.max(20, Math.min(left, windowWidth - 420));
  top = Math.max(20, Math.min(top, windowHeight - 300));
  
  widget.style.left = `${left}px`;
  widget.style.top = `${top}px`;
}

/**
 * Make widget draggable
 */
function makeWidgetDraggable() {
  const header = aiScholarWidget.querySelector('.ai-scholar-header');
  let isDragging = false;
  let dragOffset = { x: 0, y: 0 };
  
  header.addEventListener('mousedown', (e) => {
    isDragging = true;
    const rect = aiScholarWidget.getBoundingClientRect();
    dragOffset.x = e.clientX - rect.left;
    dragOffset.y = e.clientY - rect.top;
    
    document.addEventListener('mousemove', handleDrag);
    document.addEventListener('mouseup', stopDrag);
  });
  
  function handleDrag(e) {
    if (!isDragging) return;
    
    const left = e.clientX - dragOffset.x;
    const top = e.clientY - dragOffset.y;
    
    aiScholarWidget.style.left = `${left}px`;
    aiScholarWidget.style.top = `${top}px`;
  }
  
  function stopDrag() {
    isDragging = false;
    document.removeEventListener('mousemove', handleDrag);
    document.removeEventListener('mouseup', stopDrag);
  }
}

/**
 * Make widget resizable
 */
function makeWidgetResizable() {
  const resizeHandle = aiScholarWidget.querySelector('.ai-scholar-resize-handle');
  let isResizing = false;
  
  resizeHandle.addEventListener('mousedown', (e) => {
    isResizing = true;
    document.addEventListener('mousemove', handleResize);
    document.addEventListener('mouseup', stopResize);
  });
  
  function handleResize(e) {
    if (!isResizing) return;
    
    const rect = aiScholarWidget.getBoundingClientRect();
    const width = e.clientX - rect.left;
    const height = e.clientY - rect.top;
    
    aiScholarWidget.style.width = `${Math.max(300, width)}px`;
    aiScholarWidget.style.height = `${Math.max(200, height)}px`;
  }
  
  function stopResize() {
    isResizing = false;
    document.removeEventListener('mousemove', handleResize);
    document.removeEventListener('mouseup', stopResize);
  }
}

/**
 * Handle messages from background script
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.type) {
    case 'SHOW_LOADING':
      showLoading(message.action);
      break;
      
    case 'SHOW_RESULT':
      showResult(message.data);
      break;
      
    case 'SHOW_ERROR':
      showError(message.error);
      break;
      
    case 'SHOW_AUTH_REQUIRED':
      showAuthRequired();
      break;
  }
});

/**
 * Show loading state
 */
function showLoading(action) {
  showWidget();
  
  // Hide other states
  aiScholarWidget.querySelector('.ai-scholar-result').classList.add('hidden');
  aiScholarWidget.querySelector('.ai-scholar-error').classList.add('hidden');
  aiScholarWidget.querySelector('.ai-scholar-auth-required').classList.add('hidden');
  
  // Show loading
  const loading = aiScholarWidget.querySelector('.ai-scholar-loading');
  loading.classList.remove('hidden');
  loading.querySelector('.ai-scholar-loading-text').textContent = `Processing ${action}...`;
}

/**
 * Show result
 */
function showResult(data) {
  showWidget();
  
  // Hide other states
  aiScholarWidget.querySelector('.ai-scholar-loading').classList.add('hidden');
  aiScholarWidget.querySelector('.ai-scholar-error').classList.add('hidden');
  aiScholarWidget.querySelector('.ai-scholar-auth-required').classList.add('hidden');
  
  // Show result
  const result = aiScholarWidget.querySelector('.ai-scholar-result');
  result.classList.remove('hidden');
  
  // Update content
  const actionIcons = {
    explain: '🤔',
    summarize: '📝',
    rewrite: '✏️',
    translate: '🌐',
    analyze: '🔍'
  };
  
  result.querySelector('.ai-scholar-action-icon').textContent = actionIcons[data.action] || '🤖';
  result.querySelector('.ai-scholar-action-title').textContent = data.action.charAt(0).toUpperCase() + data.action.slice(1);
  result.querySelector('.ai-scholar-selected-content').textContent = data.selectedText;
  result.querySelector('.ai-scholar-response-content').textContent = data.response;
  result.querySelector('.ai-scholar-response-time').textContent = `Response time: ${data.responseTime.toFixed(2)}s`;
  
  // Store current result for actions
  aiScholarWidget.currentResult = data;
}

/**
 * Show error
 */
function showError(error) {
  showWidget();
  
  // Hide other states
  aiScholarWidget.querySelector('.ai-scholar-loading').classList.add('hidden');
  aiScholarWidget.querySelector('.ai-scholar-result').classList.add('hidden');
  aiScholarWidget.querySelector('.ai-scholar-auth-required').classList.add('hidden');
  
  // Show error
  const errorDiv = aiScholarWidget.querySelector('.ai-scholar-error');
  errorDiv.classList.remove('hidden');
  errorDiv.querySelector('.ai-scholar-error-message').textContent = error;
}

/**
 * Show authentication required
 */
function showAuthRequired() {
  showWidget();
  
  // Hide other states
  aiScholarWidget.querySelector('.ai-scholar-loading').classList.add('hidden');
  aiScholarWidget.querySelector('.ai-scholar-result').classList.add('hidden');
  aiScholarWidget.querySelector('.ai-scholar-error').classList.add('hidden');
  
  // Show auth required
  aiScholarWidget.querySelector('.ai-scholar-auth-required').classList.remove('hidden');
}

/**
 * Copy response to clipboard
 */
async function copyResponse() {
  const responseContent = aiScholarWidget.querySelector('.ai-scholar-response-content').textContent;
  
  try {
    await navigator.clipboard.writeText(responseContent);
    
    // Show feedback
    const copyBtn = aiScholarWidget.querySelector('.ai-scholar-copy-btn');
    const originalText = copyBtn.textContent;
    copyBtn.textContent = '✅';
    setTimeout(() => {
      copyBtn.textContent = originalText;
    }, 1000);
  } catch (error) {
    console.error('Failed to copy:', error);
  }
}

/**
 * Show rating dialog
 */
function showRatingDialog() {
  // Simple rating implementation
  const rating = prompt('Rate this response (1-5 stars):');
  if (rating && rating >= 1 && rating <= 5) {
    // Send rating to background script
    // Implementation would depend on backend API
    console.log('User rating:', rating);
  }
}

/**
 * Open setup (extension popup)
 */
function openSetup() {
  chrome.runtime.sendMessage({ type: 'OPEN_SETUP' });
}

/**
 * Retry last action
 */
function retryLastAction() {
  if (currentSelection) {
    // Get the last action from the widget state
    const lastAction = aiScholarWidget.dataset.lastAction || 'explain';
    triggerAIAction(lastAction);
  }
}

/**
 * Minimize widget
 */
function minimizeWidget() {
  aiScholarWidget.classList.toggle('minimized');
}

/**
 * Handle mouse down for hiding selection toolbar
 */
function handleMouseDown(e) {
  // Hide selection toolbar if clicking outside
  const toolbar = document.getElementById('ai-scholar-selection-toolbar');
  if (toolbar && !toolbar.contains(e.target)) {
    hideSelectionToolbar();
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeContentScript);
} else {
  initializeContentScript();
}