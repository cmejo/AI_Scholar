/**
 * Progressive Web App Service
 * Manages PWA functionality, service worker, and offline capabilities
 */

class PWAService {
  constructor() {
    this.isOnline = navigator.onLine;
    this.serviceWorkerRegistration = null;
    this.deferredPrompt = null;
    this.installPromptShown = false;
    
    // Initialize PWA features
    this.init();
  }
  
  async init() {
    // Register service worker
    await this.registerServiceWorker();
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Check for app updates
    this.checkForUpdates();
    
    // Handle install prompt
    this.handleInstallPrompt();
    
    // Initialize offline storage
    await this.initializeOfflineStorage();
  }
  
  async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js', {
          scope: '/'
        });
        
        this.serviceWorkerRegistration = registration;
        console.log('Service Worker registered successfully:', registration);
        
        // Handle service worker updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New service worker is available
              this.showUpdateAvailableNotification();
            }
          });
        });
        
        return registration;
      } catch (error) {
        console.error('Service Worker registration failed:', error);
        throw error;
      }
    } else {
      console.warn('Service Workers are not supported in this browser');
      return null;
    }
  }
  
  setupEventListeners() {
    // Online/offline status
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.handleOnlineStatusChange(true);
    });
    
    window.addEventListener('offline', () => {
      this.isOnline = false;
      this.handleOnlineStatusChange(false);
    });
    
    // Before install prompt
    window.addEventListener('beforeinstallprompt', (event) => {
      event.preventDefault();
      this.deferredPrompt = event;
      this.showInstallPrompt();
    });
    
    // App installed
    window.addEventListener('appinstalled', () => {
      console.log('PWA was installed');
      this.deferredPrompt = null;
      this.trackEvent('pwa_installed');
    });
    
    // Visibility change (for background sync)
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && this.isOnline) {
        this.syncOfflineActions();
      }
    });
  }
  
  handleOnlineStatusChange(isOnline) {
    console.log('Connection status changed:', isOnline ? 'online' : 'offline');
    
    // Dispatch custom event
    window.dispatchEvent(new CustomEvent('connectionchange', {
      detail: { isOnline }
    }));
    
    if (isOnline) {
      // Sync offline actions when coming back online
      this.syncOfflineActions();
      this.showConnectionRestoredNotification();
    } else {
      this.showOfflineNotification();
    }
  }
  
  async showInstallPrompt() {
    if (this.installPromptShown || !this.deferredPrompt) {
      return;
    }
    
    // Check if user has dismissed install prompt recently
    const lastDismissed = localStorage.getItem('pwa_install_dismissed');
    if (lastDismissed) {
      const daysSinceDismissed = (Date.now() - parseInt(lastDismissed)) / (1000 * 60 * 60 * 24);
      if (daysSinceDismissed < 7) {
        return; // Don't show again for 7 days
      }
    }
    
    this.installPromptShown = true;
    
    // Create custom install prompt
    const installBanner = this.createInstallBanner();
    document.body.appendChild(installBanner);
  }
  
  createInstallBanner() {
    const banner = document.createElement('div');
    banner.className = 'pwa-install-banner';
    banner.innerHTML = `
      <div class="pwa-install-content">
        <div class="pwa-install-icon">📱</div>
        <div class="pwa-install-text">
          <h3>Install AI Scholar</h3>
          <p>Get the full app experience with offline access and faster loading</p>
        </div>
        <div class="pwa-install-actions">
          <button class="pwa-install-btn" id="pwa-install">Install</button>
          <button class="pwa-dismiss-btn" id="pwa-dismiss">Not now</button>
        </div>
      </div>
    `;
    
    // Add styles
    const style = document.createElement('style');
    style.textContent = `
      .pwa-install-banner {
        position: fixed;
        bottom: 20px;
        left: 20px;
        right: 20px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideUp 0.3s ease-out;
      }
      
      .pwa-install-content {
        display: flex;
        align-items: center;
        padding: 16px;
        gap: 12px;
      }
      
      .pwa-install-icon {
        font-size: 24px;
        flex-shrink: 0;
      }
      
      .pwa-install-text {
        flex: 1;
      }
      
      .pwa-install-text h3 {
        margin: 0 0 4px 0;
        font-size: 16px;
        font-weight: 600;
      }
      
      .pwa-install-text p {
        margin: 0;
        font-size: 14px;
        color: #666;
      }
      
      .pwa-install-actions {
        display: flex;
        gap: 8px;
        flex-shrink: 0;
      }
      
      .pwa-install-btn, .pwa-dismiss-btn {
        padding: 8px 16px;
        border: none;
        border-radius: 6px;
        font-size: 14px;
        cursor: pointer;
        transition: background-color 0.2s;
      }
      
      .pwa-install-btn {
        background: #1976d2;
        color: white;
      }
      
      .pwa-install-btn:hover {
        background: #1565c0;
      }
      
      .pwa-dismiss-btn {
        background: #f5f5f5;
        color: #666;
      }
      
      .pwa-dismiss-btn:hover {
        background: #e0e0e0;
      }
      
      @keyframes slideUp {
        from {
          transform: translateY(100%);
          opacity: 0;
        }
        to {
          transform: translateY(0);
          opacity: 1;
        }
      }
      
      @media (max-width: 600px) {
        .pwa-install-banner {
          left: 10px;
          right: 10px;
          bottom: 10px;
        }
        
        .pwa-install-content {
          flex-direction: column;
          text-align: center;
        }
        
        .pwa-install-actions {
          width: 100%;
          justify-content: center;
        }
      }
    `;
    document.head.appendChild(style);
    
    // Add event listeners
    banner.querySelector('#pwa-install').addEventListener('click', () => {
      this.installApp();
      banner.remove();
    });
    
    banner.querySelector('#pwa-dismiss').addEventListener('click', () => {
      localStorage.setItem('pwa_install_dismissed', Date.now().toString());
      banner.remove();
    });
    
    return banner;
  }
  
  async installApp() {
    if (!this.deferredPrompt) {
      return;
    }
    
    try {
      // Show the install prompt
      this.deferredPrompt.prompt();
      
      // Wait for the user to respond
      const { outcome } = await this.deferredPrompt.userChoice;
      
      console.log('Install prompt outcome:', outcome);
      this.trackEvent('pwa_install_prompt', { outcome });
      
      // Clear the deferred prompt
      this.deferredPrompt = null;
    } catch (error) {
      console.error('Error during app installation:', error);
    }
  }
  
  async checkForUpdates() {
    if (!this.serviceWorkerRegistration) {
      return;
    }
    
    try {
      await this.serviceWorkerRegistration.update();
    } catch (error) {
      console.error('Error checking for updates:', error);
    }
  }
  
  showUpdateAvailableNotification() {
    // Create update notification
    const notification = document.createElement('div');
    notification.className = 'pwa-update-notification';
    notification.innerHTML = `
      <div class="pwa-update-content">
        <span>🔄 A new version is available!</span>
        <button id="pwa-update-btn">Update</button>
        <button id="pwa-update-dismiss">Later</button>
      </div>
    `;
    
    // Add styles
    const style = document.createElement('style');
    style.textContent = `
      .pwa-update-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background: #4caf50;
        color: white;
        padding: 12px 16px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        z-index: 10001;
        animation: slideDown 0.3s ease-out;
      }
      
      .pwa-update-content {
        display: flex;
        align-items: center;
        gap: 12px;
      }
      
      .pwa-update-content button {
        background: rgba(255,255,255,0.2);
        border: none;
        color: white;
        padding: 4px 12px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
      }
      
      .pwa-update-content button:hover {
        background: rgba(255,255,255,0.3);
      }
      
      @keyframes slideDown {
        from {
          transform: translateY(-100%);
          opacity: 0;
        }
        to {
          transform: translateY(0);
          opacity: 1;
        }
      }
    `;
    document.head.appendChild(style);
    
    // Add event listeners
    notification.querySelector('#pwa-update-btn').addEventListener('click', () => {
      this.applyUpdate();
      notification.remove();
    });
    
    notification.querySelector('#pwa-update-dismiss').addEventListener('click', () => {
      notification.remove();
    });
    
    document.body.appendChild(notification);
    
    // Auto-dismiss after 10 seconds
    setTimeout(() => {
      if (notification.parentNode) {
        notification.remove();
      }
    }, 10000);
  }
  
  async applyUpdate() {
    if (!this.serviceWorkerRegistration || !this.serviceWorkerRegistration.waiting) {
      return;
    }
    
    // Tell the waiting service worker to skip waiting
    this.serviceWorkerRegistration.waiting.postMessage({ type: 'SKIP_WAITING' });
    
    // Reload the page to activate the new service worker
    window.location.reload();
  }
  
  async initializeOfflineStorage() {
    try {
      // Initialize IndexedDB for offline storage
      const db = await this.openOfflineDatabase();
      console.log('Offline database initialized');
      return db;
    } catch (error) {
      console.error('Failed to initialize offline storage:', error);
    }
  }
  
  openOfflineDatabase() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('ai-scholar-offline', 1);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // Create object stores
        if (!db.objectStoreNames.contains('pending_actions')) {
          const store = db.createObjectStore('pending_actions', { keyPath: 'id' });
          store.createIndex('timestamp', 'timestamp', { unique: false });
        }
        
        if (!db.objectStoreNames.contains('cached_documents')) {
          const store = db.createObjectStore('cached_documents', { keyPath: 'id' });
          store.createIndex('lastAccessed', 'lastAccessed', { unique: false });
        }
        
        if (!db.objectStoreNames.contains('user_preferences')) {
          db.createObjectStore('user_preferences', { keyPath: 'key' });
        }
      };
    });
  }
  
  async addOfflineAction(action) {
    try {
      const db = await this.openOfflineDatabase();
      const transaction = db.transaction(['pending_actions'], 'readwrite');
      const store = transaction.objectStore('pending_actions');
      
      const actionWithId = {
        ...action,
        id: Date.now().toString(),
        timestamp: new Date().toISOString()
      };
      
      await store.add(actionWithId);
      console.log('Offline action added:', actionWithId);
      
      // Try to sync immediately if online
      if (this.isOnline) {
        this.syncOfflineActions();
      }
    } catch (error) {
      console.error('Failed to add offline action:', error);
    }
  }
  
  async syncOfflineActions() {
    if (!this.isOnline) {
      return;
    }
    
    try {
      const db = await this.openOfflineDatabase();
      const transaction = db.transaction(['pending_actions'], 'readwrite');
      const store = transaction.objectStore('pending_actions');
      const actions = await store.getAll();
      
      for (const action of actions) {
        try {
          await this.executeOfflineAction(action);
          await store.delete(action.id);
          console.log('Synced offline action:', action);
        } catch (error) {
          console.error('Failed to sync action:', action, error);
        }
      }
    } catch (error) {
      console.error('Failed to sync offline actions:', error);
    }
  }
  
  async executeOfflineAction(action) {
    const { type, data, endpoint } = action;
    
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      throw new Error(`Sync failed: ${response.status}`);
    }
    
    return response.json();
  }
  
  showOfflineNotification() {
    // Show a subtle offline indicator
    this.showNotification('You\'re offline', 'Some features may be limited', 'info');
  }
  
  showConnectionRestoredNotification() {
    this.showNotification('Connection restored', 'Syncing your data...', 'success');
  }
  
  showNotification(title, message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `pwa-notification pwa-notification-${type}`;
    notification.innerHTML = `
      <div class="pwa-notification-content">
        <strong>${title}</strong>
        <p>${message}</p>
      </div>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
      if (notification.parentNode) {
        notification.remove();
      }
    }, 3000);
  }
  
  trackEvent(eventName, data = {}) {
    // Track PWA events for analytics
    if (window.gtag) {
      window.gtag('event', eventName, data);
    }
    
    console.log('PWA Event:', eventName, data);
  }
  
  // Public API methods
  isInstalled() {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone === true;
  }
  
  isOnlineStatus() {
    return this.isOnline;
  }
  
  async clearCache() {
    if (this.serviceWorkerRegistration) {
      const messageChannel = new MessageChannel();
      
      return new Promise((resolve) => {
        messageChannel.port1.onmessage = (event) => {
          resolve(event.data.success);
        };
        
        this.serviceWorkerRegistration.active.postMessage(
          { type: 'CLEAR_CACHE' },
          [messageChannel.port2]
        );
      });
    }
  }
  
  async getVersion() {
    if (this.serviceWorkerRegistration) {
      const messageChannel = new MessageChannel();
      
      return new Promise((resolve) => {
        messageChannel.port1.onmessage = (event) => {
          resolve(event.data.version);
        };
        
        this.serviceWorkerRegistration.active.postMessage(
          { type: 'GET_VERSION' },
          [messageChannel.port2]
        );
      });
    }
  }
}

// Create and export singleton instance
const pwaService = new PWAService();
export default pwaService;