/**
 * AI Scholar Browser Extension - Background Service Worker
 * Handles context menus, API calls, and extension lifecycle
 */

// Configuration
const CONFIG = {
  API_BASE_URL: 'http://localhost:5000',
  STORAGE_KEYS: {
    API_KEY: 'ai_scholar_api_key',
    USER_SETTINGS: 'ai_scholar_settings',
    SESSION_TOKEN: 'ai_scholar_session'
  }
};

// Context menu items
const CONTEXT_MENU_ITEMS = [
  {
    id: 'explain',
    title: 'Explain with AI Scholar',
    contexts: ['selection'],
    icon: '🤔'
  },
  {
    id: 'summarize',
    title: 'Summarize with AI Scholar',
    contexts: ['selection'],
    icon: '📝'
  },
  {
    id: 'rewrite',
    title: 'Rewrite with AI Scholar',
    contexts: ['selection'],
    icon: '✏️'
  },
  {
    id: 'translate',
    title: 'Translate with AI Scholar',
    contexts: ['selection'],
    icon: '🌐'
  },
  {
    id: 'analyze',
    title: 'Analyze with AI Scholar',
    contexts: ['selection'],
    icon: '🔍'
  }
];

/**
 * Extension installation and startup
 */
chrome.runtime.onInstalled.addListener(async (details) => {
  console.log('AI Scholar Extension installed:', details);
  
  // Create context menu items
  createContextMenus();
  
  // Initialize default settings
  await initializeSettings();
  
  // Show welcome notification
  if (details.reason === 'install') {
    showWelcomeNotification();
  }
});

/**
 * Create context menu items
 */
function createContextMenus() {
  // Remove existing menus
  chrome.contextMenus.removeAll(() => {
    // Create parent menu
    chrome.contextMenus.create({
      id: 'ai-scholar-parent',
      title: 'AI Scholar Assistant',
      contexts: ['selection']
    });
    
    // Create action menus
    CONTEXT_MENU_ITEMS.forEach(item => {
      chrome.contextMenus.create({
        id: item.id,
        parentId: 'ai-scholar-parent',
        title: `${item.icon} ${item.title}`,
        contexts: item.contexts
      });
    });
  });
}

/**
 * Handle context menu clicks
 */
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (CONTEXT_MENU_ITEMS.some(item => item.id === info.menuItemId)) {
    await handleAIAction(info.menuItemId, info.selectionText, tab);
  }
});

/**
 * Handle AI action requests
 */
async function handleAIAction(action, selectedText, tab) {
  try {
    // Check if user is authenticated
    const apiKey = await getStoredApiKey();
    if (!apiKey) {
      await showAuthenticationRequired(tab.id);
      return;
    }
    
    // Show loading indicator
    await showLoadingIndicator(tab.id, action);
    
    // Make API request
    const startTime = Date.now();
    const response = await makeAIRequest(action, selectedText, tab.url, apiKey);
    const responseTime = (Date.now() - startTime) / 1000;
    
    if (response.success) {
      // Show result
      await showAIResult(tab.id, {
        action,
        selectedText,
        response: response.response,
        responseTime,
        sourceUrl: tab.url
      });
      
      // Track usage
      await trackUsage(action, selectedText, response.response, responseTime, tab.url, apiKey);
    } else {
      await showError(tab.id, response.error || 'Failed to get AI response');
    }
    
  } catch (error) {
    console.error('AI action error:', error);
    await showError(tab.id, 'An error occurred while processing your request');
  }
}

/**
 * Make API request to AI Scholar backend
 */
async function makeAIRequest(action, text, sourceUrl, apiKey) {
  const prompts = {
    explain: `Please explain the following text in simple terms:\n\n${text}`,
    summarize: `Please provide a concise summary of the following text:\n\n${text}`,
    rewrite: `Please rewrite the following text to be clearer and more engaging:\n\n${text}`,
    translate: `Please translate the following text to English (or if already in English, to Spanish):\n\n${text}`,
    analyze: `Please analyze the following text and provide insights:\n\n${text}`
  };
  
  const response = await fetch(`${CONFIG.API_BASE_URL}/api/extension/ai-action`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
      'X-Extension-Version': chrome.runtime.getManifest().version
    },
    body: JSON.stringify({
      action,
      prompt: prompts[action],
      selected_text: text,
      source_url: sourceUrl,
      browser_info: {
        userAgent: navigator.userAgent,
        language: navigator.language,
        platform: navigator.platform
      }
    })
  });
  
  return await response.json();
}

/**
 * Track extension usage
 */
async function trackUsage(action, selectedText, aiResponse, responseTime, sourceUrl, apiKey) {
  try {
    const sessionToken = await getSessionToken();
    
    await fetch(`${CONFIG.API_BASE_URL}/api/extension/track-usage`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        action_type: action,
        selected_text: selectedText.substring(0, 1000), // Limit text length
        ai_response: aiResponse.substring(0, 2000), // Limit response length
        response_time: responseTime,
        source_url: sourceUrl,
        source_domain: new URL(sourceUrl).hostname,
        session_token: sessionToken,
        browser_info: {
          userAgent: navigator.userAgent,
          language: navigator.language,
          platform: navigator.platform,
          extensionVersion: chrome.runtime.getManifest().version
        }
      })
    });
  } catch (error) {
    console.error('Usage tracking error:', error);
  }
}

/**
 * Show loading indicator in content script
 */
async function showLoadingIndicator(tabId, action) {
  await chrome.tabs.sendMessage(tabId, {
    type: 'SHOW_LOADING',
    action
  });
}

/**
 * Show AI result in content script
 */
async function showAIResult(tabId, data) {
  await chrome.tabs.sendMessage(tabId, {
    type: 'SHOW_RESULT',
    data
  });
}

/**
 * Show error message
 */
async function showError(tabId, error) {
  await chrome.tabs.sendMessage(tabId, {
    type: 'SHOW_ERROR',
    error
  });
}

/**
 * Show authentication required message
 */
async function showAuthenticationRequired(tabId) {
  await chrome.tabs.sendMessage(tabId, {
    type: 'SHOW_AUTH_REQUIRED'
  });
}

/**
 * Get stored API key
 */
async function getStoredApiKey() {
  const result = await chrome.storage.sync.get(CONFIG.STORAGE_KEYS.API_KEY);
  return result[CONFIG.STORAGE_KEYS.API_KEY];
}

/**
 * Get or create session token
 */
async function getSessionToken() {
  let result = await chrome.storage.local.get(CONFIG.STORAGE_KEYS.SESSION_TOKEN);
  let sessionToken = result[CONFIG.STORAGE_KEYS.SESSION_TOKEN];
  
  if (!sessionToken) {
    sessionToken = generateSessionToken();
    await chrome.storage.local.set({
      [CONFIG.STORAGE_KEYS.SESSION_TOKEN]: sessionToken
    });
  }
  
  return sessionToken;
}

/**
 * Generate session token
 */
function generateSessionToken() {
  return 'ext_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

/**
 * Initialize default settings
 */
async function initializeSettings() {
  const result = await chrome.storage.sync.get(CONFIG.STORAGE_KEYS.USER_SETTINGS);
  
  if (!result[CONFIG.STORAGE_KEYS.USER_SETTINGS]) {
    const defaultSettings = {
      autoShowResults: true,
      resultPosition: 'bottom-right',
      theme: 'auto',
      shortcuts: {
        explain: 'Alt+E',
        summarize: 'Alt+S',
        rewrite: 'Alt+R'
      },
      notifications: true
    };
    
    await chrome.storage.sync.set({
      [CONFIG.STORAGE_KEYS.USER_SETTINGS]: defaultSettings
    });
  }
}

/**
 * Show welcome notification
 */
function showWelcomeNotification() {
  chrome.action.setBadgeText({ text: 'NEW' });
  chrome.action.setBadgeBackgroundColor({ color: '#4CAF50' });
  
  // Clear badge after 5 seconds
  setTimeout(() => {
    chrome.action.setBadgeText({ text: '' });
  }, 5000);
}

/**
 * Handle messages from content script and popup
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.type) {
    case 'GET_API_KEY':
      getStoredApiKey().then(sendResponse);
      return true;
      
    case 'SET_API_KEY':
      chrome.storage.sync.set({
        [CONFIG.STORAGE_KEYS.API_KEY]: message.apiKey
      }).then(() => sendResponse({ success: true }));
      return true;
      
    case 'GET_SETTINGS':
      chrome.storage.sync.get(CONFIG.STORAGE_KEYS.USER_SETTINGS).then(result => {
        sendResponse(result[CONFIG.STORAGE_KEYS.USER_SETTINGS]);
      });
      return true;
      
    case 'SET_SETTINGS':
      chrome.storage.sync.set({
        [CONFIG.STORAGE_KEYS.USER_SETTINGS]: message.settings
      }).then(() => sendResponse({ success: true }));
      return true;
      
    case 'MANUAL_AI_ACTION':
      handleAIAction(message.action, message.text, sender.tab);
      sendResponse({ success: true });
      return true;
  }
});

/**
 * Handle extension icon click
 */
chrome.action.onClicked.addListener(async (tab) => {
  // This will open the popup, but we can also handle direct actions here
  console.log('Extension icon clicked on tab:', tab.url);
});