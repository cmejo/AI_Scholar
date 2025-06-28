/**
 * Background Service Worker for AI Scholar Extension
 * Handles context menus, API calls, and extension lifecycle
 */

// Configuration
const API_BASE_URL = 'http://localhost:5000'; // Change for production
const EXTENSION_VERSION = '1.0.0';

// Context menu items
const CONTEXT_MENU_ITEMS = [
  {
    id: 'explain',
    title: 'Explain with AI Scholar',
    contexts: ['selection']
  },
  {
    id: 'summarize',
    title: 'Summarize with AI Scholar',
    contexts: ['selection']
  },
  {
    id: 'rewrite',
    title: 'Rewrite with AI Scholar',
    contexts: ['selection']
  },
  {
    id: 'translate',
    title: 'Translate with AI Scholar',
    contexts: ['selection']
  },
  {
    id: 'analyze',
    title: 'Analyze with AI Scholar',
    contexts: ['selection']
  },
  {
    id: 'separator1',
    type: 'separator',
    contexts: ['selection']
  },
  {
    id: 'chat',
    title: 'Chat about this page',
    contexts: ['page']
  }
];

// Extension installation/startup
chrome.runtime.onInstalled.addListener(async (details) => {
  console.log('AI Scholar Extension installed/updated');
  
  // Create context menu items
  createContextMenus();
  
  // Set default settings
  await setDefaultSettings();
  
  // Show welcome message on first install
  if (details.reason === 'install') {
    chrome.tabs.create({
      url: chrome.runtime.getURL('welcome.html')
    });
  }
});

chrome.runtime.onStartup.addListener(() => {
  console.log('AI Scholar Extension started');
  createContextMenus();
});

// Create context menu items
function createContextMenus() {
  // Remove existing menus
  chrome.contextMenus.removeAll(() => {
    // Create new menus
    CONTEXT_MENU_ITEMS.forEach(item => {
      chrome.contextMenus.create(item);
    });
  });
}

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  console.log('Context menu clicked:', info.menuItemId);
  
  try {
    // Get user settings
    const settings = await getSettings();
    
    if (!settings.apiKey) {
      // Show setup popup if no API key
      showSetupNotification();
      return;
    }
    
    // Handle different menu actions
    switch (info.menuItemId) {
      case 'explain':
        await handleTextAction(tab, info.selectionText, 'explain');
        break;
      case 'summarize':
        await handleTextAction(tab, info.selectionText, 'summarize');
        break;
      case 'rewrite':
        await handleTextAction(tab, info.selectionText, 'rewrite');
        break;
      case 'translate':
        await handleTextAction(tab, info.selectionText, 'translate');
        break;
      case 'analyze':
        await handleTextAction(tab, info.selectionText, 'analyze');
        break;
      case 'chat':
        await handlePageChat(tab);
        break;
    }
  } catch (error) {
    console.error('Error handling context menu:', error);
    showErrorNotification('Failed to process request');
  }
});

// Handle text-based actions
async function handleTextAction(tab, selectedText, action) {
  if (!selectedText || selectedText.trim().length === 0) {
    showErrorNotification('Please select some text first');
    return;
  }
  
  // Show loading indicator
  await showLoadingIndicator(tab);
  
  try {
    // Get AI response
    const response = await callAIAPI(selectedText, action, {
      url: tab.url,
      title: tab.title
    });
    
    // Show result in sidebar
    await showResultSidebar(tab, {
      action,
      selectedText,
      response,
      url: tab.url
    });
    
    // Track usage
    await trackUsage(action, selectedText, response);
    
  } catch (error) {
    console.error('Error processing text action:', error);
    await hideLoadingIndicator(tab);
    showErrorNotification(`Failed to ${action} text: ${error.message}`);
  }
}

// Handle page chat
async function handlePageChat(tab) {
  try {
    // Extract page content
    const pageContent = await extractPageContent(tab);
    
    // Show chat interface
    await showChatInterface(tab, pageContent);
    
  } catch (error) {
    console.error('Error starting page chat:', error);
    showErrorNotification('Failed to start chat about this page');
  }
}

// Call AI API
async function callAIAPI(text, action, context = {}) {
  const settings = await getSettings();
  
  const prompt = buildPrompt(text, action, context);
  
  const response = await fetch(`${API_BASE_URL}/api/extension/process`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${settings.apiKey}`,
      'X-Extension-Version': EXTENSION_VERSION
    },
    body: JSON.stringify({
      text,
      action,
      prompt,
      context,
      settings: {
        model: settings.preferredModel || 'llama2:7b-chat',
        temperature: settings.temperature || 0.7,
        maxTokens: settings.maxTokens || 500
      }
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || `HTTP ${response.status}`);
  }
  
  return await response.json();
}

// Build prompt based on action
function buildPrompt(text, action, context) {
  const prompts = {
    explain: `Please explain the following text in simple terms. Provide context and background information where helpful:\n\n"${text}"`,
    
    summarize: `Please provide a concise summary of the following text, highlighting the key points:\n\n"${text}"`,
    
    rewrite: `Please rewrite the following text to be clearer, more engaging, and better structured while maintaining the original meaning:\n\n"${text}"`,
    
    translate: `Please translate the following text to English (if it's not already in English) or ask the user which language they'd like it translated to:\n\n"${text}"`,
    
    analyze: `Please analyze the following text, providing insights about its tone, style, key themes, and any notable patterns or implications:\n\n"${text}"`
  };
  
  let prompt = prompts[action] || `Please help with the following text:\n\n"${text}"`;
  
  // Add context if available
  if (context.url) {
    prompt += `\n\nContext: This text is from ${context.url}`;
  }
  if (context.title) {
    prompt += ` (${context.title})`;
  }
  
  return prompt;
}

// Extract page content for chat
async function extractPageContent(tab) {
  const results = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    function: () => {
      // Extract main content
      const content = {
        title: document.title,
        url: window.location.href,
        text: '',
        headings: [],
        links: []
      };
      
      // Get main text content
      const article = document.querySelector('article') || 
                     document.querySelector('main') || 
                     document.querySelector('.content') ||
                     document.querySelector('#content') ||
                     document.body;
      
      if (article) {
        content.text = article.innerText.slice(0, 5000); // Limit to 5000 chars
      }
      
      // Get headings
      const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
      content.headings = Array.from(headings).map(h => ({
        level: parseInt(h.tagName.charAt(1)),
        text: h.innerText.trim()
      })).slice(0, 20); // Limit to 20 headings
      
      // Get important links
      const links = document.querySelectorAll('a[href]');
      content.links = Array.from(links)
        .filter(link => link.innerText.trim().length > 0)
        .map(link => ({
          text: link.innerText.trim(),
          href: link.href
        }))
        .slice(0, 10); // Limit to 10 links
      
      return content;
    }
  });
  
  return results[0].result;
}

// Show loading indicator
async function showLoadingIndicator(tab) {
  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    function: () => {
      // Create loading indicator
      const loader = document.createElement('div');
      loader.id = 'ai-scholar-loader';
      loader.innerHTML = `
        <div style="
          position: fixed;
          top: 20px;
          right: 20px;
          background: #1f2937;
          color: white;
          padding: 12px 20px;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
          z-index: 10000;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          font-size: 14px;
          display: flex;
          align-items: center;
          gap: 10px;
        ">
          <div style="
            width: 16px;
            height: 16px;
            border: 2px solid #3b82f6;
            border-top: 2px solid transparent;
            border-radius: 50%;
            animation: spin 1s linear infinite;
          "></div>
          AI Scholar is thinking...
        </div>
        <style>
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        </style>
      `;
      document.body.appendChild(loader);
    }
  });
}

// Hide loading indicator
async function hideLoadingIndicator(tab) {
  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    function: () => {
      const loader = document.getElementById('ai-scholar-loader');
      if (loader) {
        loader.remove();
      }
    }
  });
}

// Show result sidebar
async function showResultSidebar(tab, data) {
  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    function: (data) => {
      // Remove existing sidebar
      const existing = document.getElementById('ai-scholar-sidebar');
      if (existing) {
        existing.remove();
      }
      
      // Create sidebar
      const sidebar = document.createElement('div');
      sidebar.id = 'ai-scholar-sidebar';
      sidebar.innerHTML = `
        <div style="
          position: fixed;
          top: 0;
          right: 0;
          width: 400px;
          height: 100vh;
          background: white;
          border-left: 1px solid #e5e7eb;
          box-shadow: -4px 0 12px rgba(0,0,0,0.1);
          z-index: 10000;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          display: flex;
          flex-direction: column;
          transform: translateX(100%);
          transition: transform 0.3s ease;
        ">
          <div style="
            padding: 20px;
            border-bottom: 1px solid #e5e7eb;
            background: #f9fafb;
            display: flex;
            justify-content: space-between;
            align-items: center;
          ">
            <h3 style="margin: 0; font-size: 18px; font-weight: 600; color: #1f2937;">
              AI Scholar - ${data.action.charAt(0).toUpperCase() + data.action.slice(1)}
            </h3>
            <button id="ai-scholar-close" style="
              background: none;
              border: none;
              font-size: 20px;
              cursor: pointer;
              color: #6b7280;
              padding: 4px;
            ">×</button>
          </div>
          
          <div style="flex: 1; overflow-y: auto; padding: 20px;">
            <div style="margin-bottom: 20px;">
              <h4 style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600; color: #374151;">
                Selected Text:
              </h4>
              <div style="
                background: #f3f4f6;
                padding: 12px;
                border-radius: 6px;
                font-size: 13px;
                color: #4b5563;
                border-left: 3px solid #3b82f6;
                max-height: 120px;
                overflow-y: auto;
              ">
                ${data.selectedText}
              </div>
            </div>
            
            <div>
              <h4 style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600; color: #374151;">
                AI Response:
              </h4>
              <div style="
                background: #ffffff;
                padding: 16px;
                border-radius: 6px;
                font-size: 14px;
                line-height: 1.6;
                color: #1f2937;
                border: 1px solid #e5e7eb;
              ">
                ${data.response.response || data.response.answer || 'No response received'}
              </div>
            </div>
            
            <div style="margin-top: 20px; display: flex; gap: 8px;">
              <button id="ai-scholar-copy" style="
                background: #3b82f6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                cursor: pointer;
                flex: 1;
              ">Copy Response</button>
              <button id="ai-scholar-rate" style="
                background: #f3f4f6;
                color: #374151;
                border: 1px solid #d1d5db;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                cursor: pointer;
                flex: 1;
              ">Rate</button>
            </div>
          </div>
        </div>
      `;
      
      document.body.appendChild(sidebar);
      
      // Animate in
      setTimeout(() => {
        sidebar.firstElementChild.style.transform = 'translateX(0)';
      }, 10);
      
      // Add event listeners
      document.getElementById('ai-scholar-close').addEventListener('click', () => {
        sidebar.firstElementChild.style.transform = 'translateX(100%)';
        setTimeout(() => sidebar.remove(), 300);
      });
      
      document.getElementById('ai-scholar-copy').addEventListener('click', () => {
        navigator.clipboard.writeText(data.response.response || data.response.answer);
        const btn = document.getElementById('ai-scholar-copy');
        const originalText = btn.textContent;
        btn.textContent = 'Copied!';
        btn.style.background = '#10b981';
        setTimeout(() => {
          btn.textContent = originalText;
          btn.style.background = '#3b82f6';
        }, 2000);
      });
      
      document.getElementById('ai-scholar-rate').addEventListener('click', () => {
        // Show rating interface
        alert('Rating feature coming soon!');
      });
      
      // Close on escape key
      const handleEscape = (e) => {
        if (e.key === 'Escape') {
          document.getElementById('ai-scholar-close').click();
          document.removeEventListener('keydown', handleEscape);
        }
      };
      document.addEventListener('keydown', handleEscape);
    },
    args: [data]
  });
  
  // Hide loading indicator
  await hideLoadingIndicator(tab);
}

// Show chat interface
async function showChatInterface(tab, pageContent) {
  // Implementation for chat interface
  console.log('Chat interface not yet implemented');
}

// Track usage
async function trackUsage(action, selectedText, response) {
  try {
    const settings = await getSettings();
    
    await fetch(`${API_BASE_URL}/api/extension/usage`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${settings.apiKey}`
      },
      body: JSON.stringify({
        action,
        selectedTextLength: selectedText.length,
        responseLength: response.response?.length || 0,
        timestamp: new Date().toISOString(),
        extensionVersion: EXTENSION_VERSION
      })
    });
  } catch (error) {
    console.error('Failed to track usage:', error);
  }
}

// Settings management
async function getSettings() {
  const result = await chrome.storage.sync.get([
    'apiKey',
    'preferredModel',
    'temperature',
    'maxTokens',
    'autoTranslate',
    'showNotifications'
  ]);
  
  return {
    apiKey: result.apiKey || '',
    preferredModel: result.preferredModel || 'llama2:7b-chat',
    temperature: result.temperature || 0.7,
    maxTokens: result.maxTokens || 500,
    autoTranslate: result.autoTranslate || false,
    showNotifications: result.showNotifications !== false
  };
}

async function setDefaultSettings() {
  const current = await getSettings();
  
  // Only set defaults for missing values
  const defaults = {
    preferredModel: 'llama2:7b-chat',
    temperature: 0.7,
    maxTokens: 500,
    autoTranslate: false,
    showNotifications: true
  };
  
  const updates = {};
  for (const [key, value] of Object.entries(defaults)) {
    if (current[key] === undefined) {
      updates[key] = value;
    }
  }
  
  if (Object.keys(updates).length > 0) {
    await chrome.storage.sync.set(updates);
  }
}

// Notifications
function showSetupNotification() {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon48.png',
    title: 'AI Scholar Setup Required',
    message: 'Please configure your API key in the extension popup to use AI features.'
  });
}

function showErrorNotification(message) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon48.png',
    title: 'AI Scholar Error',
    message: message
  });
}

// Message handling from popup/content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.type) {
    case 'getSettings':
      getSettings().then(sendResponse);
      return true;
    
    case 'saveSettings':
      chrome.storage.sync.set(message.settings).then(() => {
        sendResponse({ success: true });
      });
      return true;
    
    case 'testApiKey':
      testApiKey(message.apiKey).then(sendResponse);
      return true;
    
    default:
      sendResponse({ error: 'Unknown message type' });
  }
});

// Test API key
async function testApiKey(apiKey) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: {
        'Authorization': `Bearer ${apiKey}`
      }
    });
    
    if (response.ok) {
      const user = await response.json();
      return { valid: true, user };
    } else {
      return { valid: false, error: 'Invalid API key' };
    }
  } catch (error) {
    return { valid: false, error: error.message };
  }
}