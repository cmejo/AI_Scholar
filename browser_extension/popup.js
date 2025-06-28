/**
 * AI Scholar Browser Extension - Popup Script
 * Handles popup UI interactions and settings management
 */

// DOM elements
const elements = {
  authStatus: document.getElementById('auth-status'),
  apiKeyInput: document.getElementById('api-key'),
  toggleKeyVisibility: document.getElementById('toggle-key-visibility'),
  saveApiKey: document.getElementById('save-api-key'),
  testConnection: document.getElementById('test-connection'),
  getApiKeyLink: document.getElementById('get-api-key-link'),
  
  autoShowResults: document.getElementById('auto-show-results'),
  enableNotifications: document.getElementById('enable-notifications'),
  resultPosition: document.getElementById('result-position'),
  theme: document.getElementById('theme'),
  
  totalActions: document.getElementById('total-actions'),
  todayActions: document.getElementById('today-actions'),
  avgResponseTime: document.getElementById('avg-response-time'),
  
  loadingOverlay: document.getElementById('loading-overlay'),
  toastContainer: document.getElementById('toast-container'),
  
  helpLink: document.getElementById('help-link'),
  feedbackLink: document.getElementById('feedback-link'),
  privacyLink: document.getElementById('privacy-link')
};

// Configuration
const CONFIG = {
  API_BASE_URL: 'http://localhost:5000',
  STORAGE_KEYS: {
    API_KEY: 'ai_scholar_api_key',
    USER_SETTINGS: 'ai_scholar_settings'
  }
};

/**
 * Initialize popup
 */
async function initializePopup() {
  console.log('Initializing AI Scholar popup');
  
  // Load saved data
  await loadApiKey();
  await loadSettings();
  await loadUsageStats();
  
  // Set up event listeners
  setupEventListeners();
  
  // Check authentication status
  await checkAuthStatus();
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
  // API Key management
  elements.toggleKeyVisibility.addEventListener('click', toggleKeyVisibility);
  elements.saveApiKey.addEventListener('click', saveApiKey);
  elements.testConnection.addEventListener('click', testConnection);
  elements.getApiKeyLink.addEventListener('click', openApiKeyHelp);
  
  // Settings
  elements.autoShowResults.addEventListener('change', saveSettings);
  elements.enableNotifications.addEventListener('change', saveSettings);
  elements.resultPosition.addEventListener('change', saveSettings);
  elements.theme.addEventListener('change', saveSettings);
  
  // Quick actions
  document.querySelectorAll('.action-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const action = e.currentTarget.dataset.action;
      triggerQuickAction(action);
    });
  });
  
  // Footer links
  elements.helpLink.addEventListener('click', openHelp);
  elements.feedbackLink.addEventListener('click', openFeedback);
  elements.privacyLink.addEventListener('click', openPrivacy);
  
  // Keyboard shortcuts
  document.addEventListener('keydown', handleKeyboardShortcuts);
}

/**
 * Load API key from storage
 */
async function loadApiKey() {
  try {
    const result = await chrome.storage.sync.get(CONFIG.STORAGE_KEYS.API_KEY);
    const apiKey = result[CONFIG.STORAGE_KEYS.API_KEY];
    
    if (apiKey) {
      elements.apiKeyInput.value = apiKey;
      updateAuthStatus('online', 'Connected');
    } else {
      updateAuthStatus('offline', 'Not connected');
    }
  } catch (error) {
    console.error('Error loading API key:', error);
    updateAuthStatus('offline', 'Error loading key');
  }
}

/**
 * Load settings from storage
 */
async function loadSettings() {
  try {
    const result = await chrome.storage.sync.get(CONFIG.STORAGE_KEYS.USER_SETTINGS);
    const settings = result[CONFIG.STORAGE_KEYS.USER_SETTINGS] || {};
    
    // Apply settings to UI
    elements.autoShowResults.checked = settings.autoShowResults !== false;
    elements.enableNotifications.checked = settings.notifications !== false;
    elements.resultPosition.value = settings.resultPosition || 'bottom-right';
    elements.theme.value = settings.theme || 'auto';
  } catch (error) {
    console.error('Error loading settings:', error);
  }
}

/**
 * Load usage statistics
 */
async function loadUsageStats() {
  try {
    const apiKey = await getStoredApiKey();
    if (!apiKey) {
      return;
    }
    
    const response = await fetch(`${CONFIG.API_BASE_URL}/api/extension/stats`, {
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      const stats = await response.json();
      
      elements.totalActions.textContent = stats.total_actions || 0;
      elements.todayActions.textContent = stats.today_actions || 0;
      elements.avgResponseTime.textContent = stats.avg_response_time ? 
        `${stats.avg_response_time.toFixed(1)}s` : '0s';
    }
  } catch (error) {
    console.error('Error loading usage stats:', error);
  }
}

/**
 * Toggle API key visibility
 */
function toggleKeyVisibility() {
  const input = elements.apiKeyInput;
  const button = elements.toggleKeyVisibility;
  
  if (input.type === 'password') {
    input.type = 'text';
    button.textContent = '🙈';
    button.title = 'Hide';
  } else {
    input.type = 'password';
    button.textContent = '👁️';
    button.title = 'Show';
  }
}

/**
 * Save API key
 */
async function saveApiKey() {
  const apiKey = elements.apiKeyInput.value.trim();
  
  if (!apiKey) {
    showToast('Please enter an API key', 'error');
    return;
  }
  
  try {
    showLoading(true);
    
    // Save to storage
    await chrome.storage.sync.set({
      [CONFIG.STORAGE_KEYS.API_KEY]: apiKey
    });
    
    // Test the key
    const isValid = await testApiKey(apiKey);
    
    if (isValid) {
      updateAuthStatus('online', 'Connected');
      showToast('API key saved successfully', 'success');
      await loadUsageStats();
    } else {
      updateAuthStatus('offline', 'Invalid API key');
      showToast('Invalid API key', 'error');
    }
  } catch (error) {
    console.error('Error saving API key:', error);
    showToast('Error saving API key', 'error');
    updateAuthStatus('offline', 'Error saving key');
  } finally {
    showLoading(false);
  }
}

/**
 * Test connection
 */
async function testConnection() {
  const apiKey = elements.apiKeyInput.value.trim();
  
  if (!apiKey) {
    showToast('Please enter an API key first', 'error');
    return;
  }
  
  try {
    updateAuthStatus('testing', 'Testing...');
    showLoading(true);
    
    const isValid = await testApiKey(apiKey);
    
    if (isValid) {
      updateAuthStatus('online', 'Connection successful');
      showToast('Connection test successful', 'success');
    } else {
      updateAuthStatus('offline', 'Connection failed');
      showToast('Connection test failed', 'error');
    }
  } catch (error) {
    console.error('Error testing connection:', error);
    updateAuthStatus('offline', 'Connection error');
    showToast('Connection test error', 'error');
  } finally {
    showLoading(false);
  }
}

/**
 * Test API key validity
 */
async function testApiKey(apiKey) {
  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}/api/extension/test`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        test_message: 'Extension connection test'
      })
    });
    
    return response.ok;
  } catch (error) {
    console.error('API key test error:', error);
    return false;
  }
}

/**
 * Save settings
 */
async function saveSettings() {
  try {
    const settings = {
      autoShowResults: elements.autoShowResults.checked,
      notifications: elements.enableNotifications.checked,
      resultPosition: elements.resultPosition.value,
      theme: elements.theme.value
    };
    
    await chrome.storage.sync.set({
      [CONFIG.STORAGE_KEYS.USER_SETTINGS]: settings
    });
    
    showToast('Settings saved', 'success');
  } catch (error) {
    console.error('Error saving settings:', error);
    showToast('Error saving settings', 'error');
  }
}

/**
 * Trigger quick action
 */
async function triggerQuickAction(action) {
  try {
    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab) {
      showToast('No active tab found', 'error');
      return;
    }
    
    // Check if API key is configured
    const apiKey = await getStoredApiKey();
    if (!apiKey) {
      showToast('Please configure your API key first', 'error');
      return;
    }
    
    // Send message to content script
    await chrome.tabs.sendMessage(tab.id, {
      type: 'TRIGGER_ACTION',
      action: action
    });
    
    showToast(`${action.charAt(0).toUpperCase() + action.slice(1)} action triggered`, 'success');
    
    // Close popup
    window.close();
    
  } catch (error) {
    console.error('Error triggering quick action:', error);
    showToast('Error triggering action', 'error');
  }
}

/**
 * Update authentication status
 */
function updateAuthStatus(status, message) {
  const statusIndicator = elements.authStatus.querySelector('.status-indicator');
  const statusText = elements.authStatus.querySelector('span');
  
  statusIndicator.className = `status-indicator ${status}`;
  statusText.textContent = message;
}

/**
 * Show/hide loading overlay
 */
function showLoading(show) {
  if (show) {
    elements.loadingOverlay.classList.remove('hidden');
  } else {
    elements.loadingOverlay.classList.add('hidden');
  }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  
  elements.toastContainer.appendChild(toast);
  
  // Auto-remove after 3 seconds
  setTimeout(() => {
    if (toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
  }, 3000);
}

/**
 * Get stored API key
 */
async function getStoredApiKey() {
  try {
    const result = await chrome.storage.sync.get(CONFIG.STORAGE_KEYS.API_KEY);
    return result[CONFIG.STORAGE_KEYS.API_KEY];
  } catch (error) {
    console.error('Error getting stored API key:', error);
    return null;
  }
}

/**
 * Check authentication status
 */
async function checkAuthStatus() {
  const apiKey = await getStoredApiKey();
  
  if (apiKey) {
    const isValid = await testApiKey(apiKey);
    if (isValid) {
      updateAuthStatus('online', 'Connected');
    } else {
      updateAuthStatus('offline', 'Invalid API key');
    }
  } else {
    updateAuthStatus('offline', 'Not connected');
  }
}

/**
 * Handle keyboard shortcuts
 */
function handleKeyboardShortcuts(e) {
  // Ctrl/Cmd + S to save API key
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault();
    saveApiKey();
  }
  
  // Ctrl/Cmd + T to test connection
  if ((e.ctrlKey || e.metaKey) && e.key === 't') {
    e.preventDefault();
    testConnection();
  }
}

/**
 * Open API key help
 */
function openApiKeyHelp(e) {
  e.preventDefault();
  chrome.tabs.create({
    url: `${CONFIG.API_BASE_URL}/help/api-keys`
  });
}

/**
 * Open help page
 */
function openHelp(e) {
  e.preventDefault();
  chrome.tabs.create({
    url: `${CONFIG.API_BASE_URL}/help/extension`
  });
}

/**
 * Open feedback page
 */
function openFeedback(e) {
  e.preventDefault();
  chrome.tabs.create({
    url: `${CONFIG.API_BASE_URL}/feedback`
  });
}

/**
 * Open privacy page
 */
function openPrivacy(e) {
  e.preventDefault();
  chrome.tabs.create({
    url: `${CONFIG.API_BASE_URL}/privacy`
  });
}

// Initialize popup when DOM is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializePopup);
} else {
  initializePopup();
}