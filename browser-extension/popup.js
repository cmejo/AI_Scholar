/**
 * Popup Script for AI Scholar Extension
 * Handles popup UI interactions and settings management
 */

// DOM elements
let elements = {};

// State
let currentUser = null;
let settings = {};
let usageStats = {};

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
  console.log('AI Scholar popup loaded');
  
  // Get DOM elements
  initializeElements();
  
  // Load settings and user data
  await loadInitialData();
  
  // Setup event listeners
  setupEventListeners();
  
  // Update UI based on current state
  updateUI();
});

// Initialize DOM elements
function initializeElements() {
  elements = {
    // Sections
    setupSection: document.getElementById('setup-section'),
    mainSection: document.getElementById('main-section'),
    settingsSection: document.getElementById('settings-section'),
    
    // Setup elements
    apiKeyInput: document.getElementById('api-key-input'),
    toggleApiKey: document.getElementById('toggle-api-key'),
    testApiKey: document.getElementById('test-api-key'),
    saveApiKey: document.getElementById('save-api-key'),
    apiTestResult: document.getElementById('api-test-result'),
    dashboardLink: document.getElementById('dashboard-link'),
    
    // Main section elements
    userName: document.getElementById('user-name'),
    userStatus: document.getElementById('user-status'),
    settingsBtn: document.getElementById('settings-btn'),
    todayRequests: document.getElementById('today-requests'),
    todayWords: document.getElementById('today-words'),
    activityList: document.getElementById('activity-list'),
    openDashboard: document.getElementById('open-dashboard'),
    helpBtn: document.getElementById('help-btn'),
    
    // Settings elements
    backToMain: document.getElementById('back-to-main'),
    modelSelect: document.getElementById('model-select'),
    temperatureSlider: document.getElementById('temperature-slider'),
    temperatureValue: document.getElementById('temperature-value'),
    maxTokensInput: document.getElementById('max-tokens-input'),
    autoTranslate: document.getElementById('auto-translate'),
    showNotifications: document.getElementById('show-notifications'),
    floatingButton: document.getElementById('floating-button'),
    apiKeySettings: document.getElementById('api-key-settings'),
    toggleApiKeySettings: document.getElementById('toggle-api-key-settings'),
    apiEndpoint: document.getElementById('api-endpoint'),
    usageAnalytics: document.getElementById('usage-analytics'),
    clearData: document.getElementById('clear-data'),
    exportData: document.getElementById('export-data'),
    saveSettings: document.getElementById('save-settings'),
    
    // UI elements
    loadingOverlay: document.getElementById('loading-overlay'),
    toastContainer: document.getElementById('toast-container')
  };
  
  // Set dashboard link
  elements.dashboardLink.href = 'http://localhost:5000'; // Update for production
}

// Load initial data
async function loadInitialData() {
  try {
    showLoading(true);
    
    // Load settings from storage
    settings = await getSettings();
    
    // Load usage stats
    usageStats = await getUsageStats();
    
    // If API key is configured, load user data
    if (settings.apiKey) {
      await loadUserData();
    }
    
  } catch (error) {
    console.error('Error loading initial data:', error);
    showToast('Failed to load extension data', 'error');
  } finally {
    showLoading(false);
  }
}

// Setup event listeners
function setupEventListeners() {
  // Setup section
  elements.toggleApiKey?.addEventListener('click', () => togglePasswordVisibility('api-key-input', 'toggle-api-key'));
  elements.testApiKey?.addEventListener('click', testApiConnection);
  elements.saveApiKey?.addEventListener('click', saveApiKey);
  
  // Main section
  elements.settingsBtn?.addEventListener('click', () => showSection('settings'));
  elements.openDashboard?.addEventListener('click', openDashboard);
  elements.helpBtn?.addEventListener('click', openHelp);
  
  // Quick actions
  document.querySelectorAll('.action-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const action = btn.getAttribute('data-action');
      executeQuickAction(action);
    });
  });
  
  // Settings section
  elements.backToMain?.addEventListener('click', () => showSection('main'));
  elements.toggleApiKeySettings?.addEventListener('click', () => togglePasswordVisibility('api-key-settings', 'toggle-api-key-settings'));
  elements.temperatureSlider?.addEventListener('input', updateTemperatureValue);
  elements.clearData?.addEventListener('click', clearAllData);
  elements.exportData?.addEventListener('click', exportUserData);
  elements.saveSettings?.addEventListener('click', saveAllSettings);
}

// Get settings from storage
async function getSettings() {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ type: 'getSettings' }, (response) => {
      resolve(response || {});
    });
  });
}

// Save settings to storage
async function saveSettings(newSettings) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ 
      type: 'saveSettings', 
      settings: newSettings 
    }, (response) => {
      resolve(response);
    });
  });
}

// Load user data
async function loadUserData() {
  try {
    const response = await fetch('http://localhost:5000/api/auth/me', {
      headers: {
        'Authorization': `Bearer ${settings.apiKey}`
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      currentUser = data.user;
      
      // Load usage stats
      await loadUsageStats();
      
    } else {
      throw new Error('Failed to load user data');
    }
  } catch (error) {
    console.error('Error loading user data:', error);
    // API key might be invalid
    settings.apiKey = '';
    await saveSettings(settings);
  }
}

// Load usage stats
async function loadUsageStats() {
  try {
    const response = await fetch('http://localhost:5000/api/extension/stats', {
      headers: {
        'Authorization': `Bearer ${settings.apiKey}`
      }
    });
    
    if (response.ok) {
      usageStats = await response.json();
    }
  } catch (error) {
    console.error('Error loading usage stats:', error);
  }
}

// Get usage stats from storage
async function getUsageStats() {
  return new Promise((resolve) => {
    chrome.storage.local.get(['usageStats'], (result) => {
      resolve(result.usageStats || {
        todayRequests: 0,
        todayWords: 0,
        recentActivity: []
      });
    });
  });
}

// Update UI based on current state
function updateUI() {
  if (settings.apiKey && currentUser) {
    showSection('main');
    updateMainSection();
  } else {
    showSection('setup');
  }
  
  updateSettingsSection();
}

// Show specific section
function showSection(sectionName) {
  // Hide all sections
  elements.setupSection.style.display = 'none';
  elements.mainSection.style.display = 'none';
  elements.settingsSection.style.display = 'none';
  
  // Show requested section
  switch (sectionName) {
    case 'setup':
      elements.setupSection.style.display = 'block';
      break;
    case 'main':
      elements.mainSection.style.display = 'block';
      break;
    case 'settings':
      elements.settingsSection.style.display = 'block';
      break;
  }
}

// Update main section
function updateMainSection() {
  if (currentUser) {
    elements.userName.textContent = currentUser.username || 'User';
    elements.userStatus.textContent = 'Connected';
  }
  
  // Update usage stats
  elements.todayRequests.textContent = usageStats.todayRequests || 0;
  elements.todayWords.textContent = usageStats.todayWords || 0;
  
  // Update recent activity
  updateRecentActivity();
}

// Update recent activity
function updateRecentActivity() {
  const activities = usageStats.recentActivity || [];
  
  if (activities.length === 0) {
    elements.activityList.innerHTML = `
      <div class="activity-item">
        <span class="activity-icon">📝</span>
        <span class="activity-text">No recent activity</span>
        <span class="activity-time">-</span>
      </div>
    `;
    return;
  }
  
  elements.activityList.innerHTML = activities
    .slice(0, 5) // Show last 5 activities
    .map(activity => `
      <div class="activity-item">
        <span class="activity-icon">${getActionIcon(activity.action)}</span>
        <span class="activity-text">${activity.description}</span>
        <span class="activity-time">${formatTimeAgo(activity.timestamp)}</span>
      </div>
    `).join('');
}

// Update settings section
function updateSettingsSection() {
  if (elements.modelSelect) {
    elements.modelSelect.value = settings.preferredModel || 'llama2:7b-chat';
  }
  
  if (elements.temperatureSlider) {
    elements.temperatureSlider.value = settings.temperature || 0.7;
    updateTemperatureValue();
  }
  
  if (elements.maxTokensInput) {
    elements.maxTokensInput.value = settings.maxTokens || 500;
  }
  
  if (elements.autoTranslate) {
    elements.autoTranslate.checked = settings.autoTranslate || false;
  }
  
  if (elements.showNotifications) {
    elements.showNotifications.checked = settings.showNotifications !== false;
  }
  
  if (elements.floatingButton) {
    elements.floatingButton.checked = settings.floatingButton !== false;
  }
  
  if (elements.apiKeySettings && settings.apiKey) {
    elements.apiKeySettings.value = '••••••••••••••••';
  }
  
  if (elements.apiEndpoint) {
    elements.apiEndpoint.value = settings.apiEndpoint || 'http://localhost:5000';
  }
  
  if (elements.usageAnalytics) {
    elements.usageAnalytics.checked = settings.usageAnalytics !== false;
  }
}

// Test API connection
async function testApiConnection() {
  const apiKey = elements.apiKeyInput.value.trim();
  
  if (!apiKey) {
    showTestResult('Please enter an API key', 'error');
    return;
  }
  
  try {
    showLoading(true);
    
    const response = await chrome.runtime.sendMessage({
      type: 'testApiKey',
      apiKey: apiKey
    });
    
    if (response.valid) {
      showTestResult(`✅ Connected as ${response.user.user.username}`, 'success');
    } else {
      showTestResult(`❌ ${response.error}`, 'error');
    }
    
  } catch (error) {
    showTestResult(`❌ Connection failed: ${error.message}`, 'error');
  } finally {
    showLoading(false);
  }
}

// Save API key
async function saveApiKey() {
  const apiKey = elements.apiKeyInput.value.trim();
  
  if (!apiKey) {
    showToast('Please enter an API key', 'error');
    return;
  }
  
  try {
    showLoading(true);
    
    // Test the API key first
    const testResponse = await chrome.runtime.sendMessage({
      type: 'testApiKey',
      apiKey: apiKey
    });
    
    if (!testResponse.valid) {
      showToast(`Invalid API key: ${testResponse.error}`, 'error');
      return;
    }
    
    // Save the API key
    settings.apiKey = apiKey;
    await saveSettings(settings);
    
    // Load user data
    await loadUserData();
    
    showToast('API key saved successfully!', 'success');
    
    // Switch to main section
    setTimeout(() => {
      updateUI();
    }, 1000);
    
  } catch (error) {
    console.error('Error saving API key:', error);
    showToast('Failed to save API key', 'error');
  } finally {
    showLoading(false);
  }
}

// Execute quick action
async function executeQuickAction(action) {
  try {
    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    // Send message to content script
    const response = await chrome.tabs.sendMessage(tab.id, {
      type: 'executeAction',
      action: action
    });
    
    if (response?.success) {
      showToast(`${action} action triggered`, 'success');
      
      // Update usage stats
      usageStats.todayRequests = (usageStats.todayRequests || 0) + 1;
      await chrome.storage.local.set({ usageStats });
      updateMainSection();
    } else {
      showToast('Please select some text on the page first', 'warning');
    }
    
  } catch (error) {
    console.error('Error executing quick action:', error);
    showToast('Failed to execute action. Make sure you have text selected.', 'error');
  }
}

// Save all settings
async function saveAllSettings() {
  try {
    showLoading(true);
    
    // Collect all settings
    const newSettings = {
      ...settings,
      preferredModel: elements.modelSelect.value,
      temperature: parseFloat(elements.temperatureSlider.value),
      maxTokens: parseInt(elements.maxTokensInput.value),
      autoTranslate: elements.autoTranslate.checked,
      showNotifications: elements.showNotifications.checked,
      floatingButton: elements.floatingButton.checked,
      apiEndpoint: elements.apiEndpoint.value,
      usageAnalytics: elements.usageAnalytics.checked
    };
    
    // Update API key if changed
    const newApiKey = elements.apiKeySettings.value;
    if (newApiKey && newApiKey !== '••••••••••••••••') {
      newSettings.apiKey = newApiKey;
    }
    
    // Save settings
    await saveSettings(newSettings);
    settings = newSettings;
    
    showToast('Settings saved successfully!', 'success');
    
    // Go back to main section
    setTimeout(() => {
      showSection('main');
    }, 1000);
    
  } catch (error) {
    console.error('Error saving settings:', error);
    showToast('Failed to save settings', 'error');
  } finally {
    showLoading(false);
  }
}

// Clear all data
async function clearAllData() {
  if (!confirm('Are you sure you want to clear all extension data? This cannot be undone.')) {
    return;
  }
  
  try {
    showLoading(true);
    
    // Clear storage
    await chrome.storage.sync.clear();
    await chrome.storage.local.clear();
    
    // Reset state
    settings = {};
    currentUser = null;
    usageStats = {};
    
    showToast('All data cleared successfully', 'success');
    
    // Go back to setup
    setTimeout(() => {
      updateUI();
    }, 1000);
    
  } catch (error) {
    console.error('Error clearing data:', error);
    showToast('Failed to clear data', 'error');
  } finally {
    showLoading(false);
  }
}

// Export user data
async function exportUserData() {
  try {
    const exportData = {
      settings: settings,
      usageStats: usageStats,
      exportDate: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ai-scholar-data-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    
    URL.revokeObjectURL(url);
    
    showToast('Data exported successfully', 'success');
    
  } catch (error) {
    console.error('Error exporting data:', error);
    showToast('Failed to export data', 'error');
  }
}

// Open dashboard
function openDashboard() {
  chrome.tabs.create({
    url: settings.apiEndpoint || 'http://localhost:5000'
  });
}

// Open help
function openHelp() {
  chrome.tabs.create({
    url: 'https://github.com/your-repo/ai-scholar-extension#readme'
  });
}

// Utility functions
function togglePasswordVisibility(inputId, buttonId) {
  const input = document.getElementById(inputId);
  const button = document.getElementById(buttonId);
  
  if (input.type === 'password') {
    input.type = 'text';
    button.textContent = '🙈';
  } else {
    input.type = 'password';
    button.textContent = '👁️';
  }
}

function updateTemperatureValue() {
  const value = elements.temperatureSlider.value;
  elements.temperatureValue.textContent = value;
}

function showTestResult(message, type) {
  elements.apiTestResult.textContent = message;
  elements.apiTestResult.className = `test-result ${type}`;
  elements.apiTestResult.style.display = 'block';
  
  // Hide after 5 seconds
  setTimeout(() => {
    elements.apiTestResult.style.display = 'none';
  }, 5000);
}

function showLoading(show) {
  elements.loadingOverlay.style.display = show ? 'flex' : 'none';
}

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  
  elements.toastContainer.appendChild(toast);
  
  // Auto-remove after 3 seconds
  setTimeout(() => {
    toast.remove();
  }, 3000);
}

function getActionIcon(action) {
  const icons = {
    explain: '💡',
    summarize: '📝',
    rewrite: '✏️',
    translate: '🌐',
    analyze: '🔍'
  };
  return icons[action] || '🤖';
}

function formatTimeAgo(timestamp) {
  const now = new Date();
  const time = new Date(timestamp);
  const diffMs = now - time;
  const diffMins = Math.floor(diffMs / 60000);
  
  if (diffMins < 1) return 'now';
  if (diffMins < 60) return `${diffMins}m ago`;
  
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}