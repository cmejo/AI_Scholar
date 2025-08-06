/**
 * Mobile Synchronization Service
 * Handles offline data storage, sync, and conflict resolution
 */

interface SyncableData {
  id: string;
  type: 'document' | 'conversation' | 'preference' | 'search' | 'annotation';
  data: any;
  lastModified: number;
  version: number;
  userId: string;
  deviceId: string;
  syncStatus: 'pending' | 'synced' | 'conflict' | 'error';
  hash?: string;
}

interface SyncConflict {
  id: string;
  localData: SyncableData;
  remoteData: SyncableData;
  conflictType: 'version' | 'concurrent' | 'deleted';
  timestamp: number;
}

interface SyncStats {
  totalItems: number;
  pendingSync: number;
  conflicts: number;
  lastSyncTime: number;
  syncInProgress: boolean;
}

interface PushNotificationData {
  title: string;
  body: string;
  icon?: string;
  badge?: string;
  data?: any;
  actions?: Array<{
    action: string;
    title: string;
    icon?: string;
  }>;
}

class MobileSyncService {
  private db: IDBDatabase | null = null;
  private deviceId: string;
  private userId: string = '';
  private syncInProgress = false;
  private syncQueue: SyncableData[] = [];
  private conflictQueue: SyncConflict[] = [];
  private eventListeners: Map<string, Function[]> = new Map();
  private pushSubscription: PushSubscription | null = null;

  constructor() {
    this.deviceId = this.generateDeviceId();
    this.initializeDatabase();
    this.setupEventListeners();
  }

  private generateDeviceId(): string {
    let deviceId = localStorage.getItem('device_id');
    if (!deviceId) {
      deviceId = 'device_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('device_id', deviceId);
    }
    return deviceId;
  }

  private async initializeDatabase(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('ai_scholar_mobile_sync', 3);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        this.setupDatabaseEventHandlers();
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        
        // Syncable data store
        if (!db.objectStoreNames.contains('syncable_data')) {
          const store = db.createObjectStore('syncable_data', { keyPath: 'id' });
          store.createIndex('type', 'type', { unique: false });
          store.createIndex('userId', 'userId', { unique: false });
          store.createIndex('syncStatus', 'syncStatus', { unique: false });
          store.createIndex('lastModified', 'lastModified', { unique: false });
        }

        // Sync conflicts store
        if (!db.objectStoreNames.contains('sync_conflicts')) {
          const store = db.createObjectStore('sync_conflicts', { keyPath: 'id' });
          store.createIndex('timestamp', 'timestamp', { unique: false });
        }

        // Cached documents store
        if (!db.objectStoreNames.contains('cached_documents')) {
          const store = db.createObjectStore('cached_documents', { keyPath: 'id' });
          store.createIndex('lastAccessed', 'lastAccessed', { unique: false });
          store.createIndex('size', 'size', { unique: false });
        }

        // User preferences store
        if (!db.objectStoreNames.contains('user_preferences')) {
          const store = db.createObjectStore('user_preferences', { keyPath: 'key' });
        }

        // Sync metadata store
        if (!db.objectStoreNames.contains('sync_metadata')) {
          const store = db.createObjectStore('sync_metadata', { keyPath: 'key' });
        }
      };
    });
  }

  private setupDatabaseEventHandlers(): void {
    if (!this.db) return;

    this.db.addEventListener('versionchange', () => {
      this.db?.close();
      this.db = null;
      // Reinitialize database
      this.initializeDatabase();
    });
  }

  private setupEventListeners(): void {
    // Online/offline events
    window.addEventListener('online', () => {
      this.handleOnlineEvent();
    });

    window.addEventListener('offline', () => {
      this.handleOfflineEvent();
    });

    // Visibility change for background sync
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && navigator.onLine) {
        this.performBackgroundSync();
      }
    });

    // Page unload - save pending changes
    window.addEventListener('beforeunload', () => {
      this.savePendingChanges();
    });
  }

  // Public API Methods

  async setUserId(userId: string): Promise<void> {
    this.userId = userId;
    await this.saveMetadata('userId', userId);
  }

  async saveData(type: SyncableData['type'], id: string, data: any): Promise<void> {
    if (!this.db) await this.initializeDatabase();

    const syncableData: SyncableData = {
      id: `${type}_${id}`,
      type,
      data,
      lastModified: Date.now(),
      version: await this.getNextVersion(id),
      userId: this.userId,
      deviceId: this.deviceId,
      syncStatus: 'pending',
      hash: await this.generateHash(data)
    };

    await this.storeData('syncable_data', syncableData);
    this.addToSyncQueue(syncableData);
    this.emit('dataChanged', { type, id, data });

    // Attempt immediate sync if online
    if (navigator.onLine) {
      this.performSync();
    }
  }

  async getData(type: SyncableData['type'], id: string): Promise<any | null> {
    if (!this.db) await this.initializeDatabase();

    const fullId = `${type}_${id}`;
    const data = await this.retrieveData('syncable_data', fullId);
    return data?.data || null;
  }

  async getAllData(type: SyncableData['type']): Promise<any[]> {
    if (!this.db) await this.initializeDatabase();

    const transaction = this.db!.transaction(['syncable_data'], 'readonly');
    const store = transaction.objectStore('syncable_data');
    const index = store.index('type');
    
    return new Promise((resolve, reject) => {
      const request = index.getAll(type);
      request.onsuccess = () => {
        const results = request.result.map(item => item.data);
        resolve(results);
      };
      request.onerror = () => reject(request.error);
    });
  }

  async deleteData(type: SyncableData['type'], id: string): Promise<void> {
    if (!this.db) await this.initializeDatabase();

    const fullId = `${type}_${id}`;
    
    // Mark as deleted instead of actually deleting for sync purposes
    const deletedData: SyncableData = {
      id: fullId,
      type,
      data: null,
      lastModified: Date.now(),
      version: await this.getNextVersion(id),
      userId: this.userId,
      deviceId: this.deviceId,
      syncStatus: 'pending',
      hash: 'deleted'
    };

    await this.storeData('syncable_data', deletedData);
    this.addToSyncQueue(deletedData);
    this.emit('dataDeleted', { type, id });

    if (navigator.onLine) {
      this.performSync();
    }
  }

  async performSync(): Promise<void> {
    if (this.syncInProgress || !navigator.onLine) return;

    this.syncInProgress = true;
    this.emit('syncStarted');

    try {
      // Get pending items
      const pendingItems = await this.getPendingItems();
      
      // Push local changes to server
      await this.pushLocalChanges(pendingItems);
      
      // Pull remote changes from server
      await this.pullRemoteChanges();
      
      // Update sync metadata
      await this.saveMetadata('lastSyncTime', Date.now());
      
      this.emit('syncCompleted', { itemsProcessed: pendingItems.length });
    } catch (error) {
      console.error('Sync failed:', error);
      this.emit('syncError', error);
    } finally {
      this.syncInProgress = false;
    }
  }

  async getSyncStats(): Promise<SyncStats> {
    if (!this.db) await this.initializeDatabase();

    const [totalItems, pendingItems, conflicts, lastSyncTime] = await Promise.all([
      this.countItems('syncable_data'),
      this.countItemsByStatus('pending'),
      this.countItems('sync_conflicts'),
      this.getMetadata('lastSyncTime') || 0
    ]);

    return {
      totalItems,
      pendingSync: pendingItems,
      conflicts,
      lastSyncTime,
      syncInProgress: this.syncInProgress
    };
  }

  async resolveConflict(conflictId: string, resolution: 'local' | 'remote' | 'merge'): Promise<void> {
    const conflict = await this.retrieveData('sync_conflicts', conflictId);
    if (!conflict) return;

    let resolvedData: SyncableData;

    switch (resolution) {
      case 'local':
        resolvedData = conflict.localData;
        break;
      case 'remote':
        resolvedData = conflict.remoteData;
        break;
      case 'merge':
        resolvedData = await this.mergeConflictData(conflict.localData, conflict.remoteData);
        break;
    }

    // Update resolved data
    resolvedData.syncStatus = 'synced';
    await this.storeData('syncable_data', resolvedData);
    
    // Remove conflict
    await this.deleteFromStore('sync_conflicts', conflictId);
    
    this.emit('conflictResolved', { conflictId, resolution });
  }

  async getConflicts(): Promise<SyncConflict[]> {
    if (!this.db) await this.initializeDatabase();

    const transaction = this.db!.transaction(['sync_conflicts'], 'readonly');
    const store = transaction.objectStore('sync_conflicts');
    
    return new Promise((resolve, reject) => {
      const request = store.getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  // Push Notification Methods

  async requestNotificationPermission(): Promise<boolean> {
    if (!('Notification' in window)) return false;

    const permission = await Notification.requestPermission();
    return permission === 'granted';
  }

  async subscribeToPushNotifications(): Promise<boolean> {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      return false;
    }

    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.getVapidPublicKey()
      });

      this.pushSubscription = subscription;
      
      // Send subscription to server
      await this.sendSubscriptionToServer(subscription);
      
      return true;
    } catch (error) {
      console.error('Failed to subscribe to push notifications:', error);
      return false;
    }
  }

  async sendPushNotification(data: PushNotificationData): Promise<void> {
    if (!this.pushSubscription) return;

    // This would typically be sent to your server to trigger the push
    // For demo purposes, we'll show a local notification
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(data.title, {
        body: data.body,
        icon: data.icon || '/icons/icon-192x192.png',
        badge: data.badge || '/icons/badge-72x72.png',
        data: data.data
      });
    }
  }

  // Cache Management

  async cacheDocument(documentId: string, documentData: any, size: number): Promise<void> {
    if (!this.db) await this.initializeDatabase();

    const cachedDoc = {
      id: documentId,
      data: documentData,
      lastAccessed: Date.now(),
      size,
      cacheTime: Date.now()
    };

    await this.storeData('cached_documents', cachedDoc);
    
    // Manage cache size
    await this.manageCacheSize();
  }

  async getCachedDocument(documentId: string): Promise<any | null> {
    if (!this.db) await this.initializeDatabase();

    const cachedDoc = await this.retrieveData('cached_documents', documentId);
    
    if (cachedDoc) {
      // Update last accessed time
      cachedDoc.lastAccessed = Date.now();
      await this.storeData('cached_documents', cachedDoc);
      return cachedDoc.data;
    }
    
    return null;
  }

  private async manageCacheSize(): Promise<void> {
    const maxCacheSize = 50 * 1024 * 1024; // 50MB
    const transaction = this.db!.transaction(['cached_documents'], 'readwrite');
    const store = transaction.objectStore('cached_documents');
    
    // Get all cached documents sorted by last accessed
    const index = store.index('lastAccessed');
    const request = index.getAll();
    
    request.onsuccess = () => {
      const docs = request.result.sort((a, b) => a.lastAccessed - b.lastAccessed);
      let totalSize = docs.reduce((sum, doc) => sum + doc.size, 0);
      
      // Remove oldest documents if cache is too large
      let i = 0;
      while (totalSize > maxCacheSize && i < docs.length) {
        store.delete(docs[i].id);
        totalSize -= docs[i].size;
        i++;
      }
    };
  }

  // Private Helper Methods

  private async storeData(storeName: string, data: any): Promise<void> {
    if (!this.db) return;

    const transaction = this.db.transaction([storeName], 'readwrite');
    const store = transaction.objectStore(storeName);
    
    return new Promise((resolve, reject) => {
      const request = store.put(data);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  private async retrieveData(storeName: string, id: string): Promise<any | null> {
    if (!this.db) return null;

    const transaction = this.db.transaction([storeName], 'readonly');
    const store = transaction.objectStore(storeName);
    
    return new Promise((resolve, reject) => {
      const request = store.get(id);
      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(request.error);
    });
  }

  private async deleteFromStore(storeName: string, id: string): Promise<void> {
    if (!this.db) return;

    const transaction = this.db.transaction([storeName], 'readwrite');
    const store = transaction.objectStore(storeName);
    
    return new Promise((resolve, reject) => {
      const request = store.delete(id);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  private async countItems(storeName: string): Promise<number> {
    if (!this.db) return 0;

    const transaction = this.db.transaction([storeName], 'readonly');
    const store = transaction.objectStore(storeName);
    
    return new Promise((resolve, reject) => {
      const request = store.count();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  private async countItemsByStatus(status: string): Promise<number> {
    if (!this.db) return 0;

    const transaction = this.db.transaction(['syncable_data'], 'readonly');
    const store = transaction.objectStore('syncable_data');
    const index = store.index('syncStatus');
    
    return new Promise((resolve, reject) => {
      const request = index.count(status);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  private async getPendingItems(): Promise<SyncableData[]> {
    if (!this.db) return [];

    const transaction = this.db.transaction(['syncable_data'], 'readonly');
    const store = transaction.objectStore('syncable_data');
    const index = store.index('syncStatus');
    
    return new Promise((resolve, reject) => {
      const request = index.getAll('pending');
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  private async pushLocalChanges(items: SyncableData[]): Promise<void> {
    for (const item of items) {
      try {
        // Simulate API call to push data to server
        const response = await fetch('/api/sync/push', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
          },
          body: JSON.stringify(item)
        });

        if (response.ok) {
          item.syncStatus = 'synced';
          await this.storeData('syncable_data', item);
        } else {
          throw new Error(`Push failed: ${response.status}`);
        }
      } catch (error) {
        console.error('Failed to push item:', item.id, error);
        item.syncStatus = 'error';
        await this.storeData('syncable_data', item);
      }
    }
  }

  private async pullRemoteChanges(): Promise<void> {
    try {
      const lastSyncTime = await this.getMetadata('lastSyncTime') || 0;
      
      const response = await fetch(`/api/sync/pull?since=${lastSyncTime}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (!response.ok) {
        throw new Error(`Pull failed: ${response.status}`);
      }

      const remoteChanges: SyncableData[] = await response.json();
      
      for (const remoteItem of remoteChanges) {
        await this.handleRemoteChange(remoteItem);
      }
    } catch (error) {
      console.error('Failed to pull remote changes:', error);
      throw error;
    }
  }

  private async handleRemoteChange(remoteItem: SyncableData): Promise<void> {
    const localItem = await this.retrieveData('syncable_data', remoteItem.id);
    
    if (!localItem) {
      // New remote item
      await this.storeData('syncable_data', remoteItem);
    } else if (localItem.version < remoteItem.version) {
      // Remote is newer
      if (localItem.syncStatus === 'pending') {
        // Conflict: local changes pending but remote is newer
        await this.createConflict(localItem, remoteItem, 'concurrent');
      } else {
        // Safe to update
        await this.storeData('syncable_data', remoteItem);
      }
    } else if (localItem.version > remoteItem.version) {
      // Local is newer - this shouldn't happen in normal sync
      console.warn('Local version newer than remote:', localItem.id);
    }
    // If versions are equal, no action needed
  }

  private async createConflict(localData: SyncableData, remoteData: SyncableData, conflictType: SyncConflict['conflictType']): Promise<void> {
    const conflict: SyncConflict = {
      id: `conflict_${localData.id}_${Date.now()}`,
      localData,
      remoteData,
      conflictType,
      timestamp: Date.now()
    };

    await this.storeData('sync_conflicts', conflict);
    this.emit('conflictDetected', conflict);
  }

  private async mergeConflictData(localData: SyncableData, remoteData: SyncableData): Promise<SyncableData> {
    // Simple merge strategy - in practice, this would be more sophisticated
    const mergedData = {
      ...localData,
      data: { ...remoteData.data, ...localData.data },
      version: Math.max(localData.version, remoteData.version) + 1,
      lastModified: Date.now(),
      hash: await this.generateHash({ ...remoteData.data, ...localData.data })
    };

    return mergedData;
  }

  private async getNextVersion(id: string): Promise<number> {
    const existing = await this.retrieveData('syncable_data', id);
    return existing ? existing.version + 1 : 1;
  }

  private async generateHash(data: any): Promise<string> {
    const encoder = new TextEncoder();
    const dataString = JSON.stringify(data);
    const dataBuffer = encoder.encode(dataString);
    const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  private async saveMetadata(key: string, value: any): Promise<void> {
    await this.storeData('sync_metadata', { key, value });
  }

  private async getMetadata(key: string): Promise<any> {
    const metadata = await this.retrieveData('sync_metadata', key);
    return metadata?.value;
  }

  private addToSyncQueue(data: SyncableData): void {
    this.syncQueue.push(data);
  }

  private async performBackgroundSync(): Promise<void> {
    if ('serviceWorker' in navigator) {
      const registration = await navigator.serviceWorker.ready;
      if ('sync' in registration) {
        await registration.sync.register('background-sync');
      }
    }
  }

  private handleOnlineEvent(): void {
    this.emit('online');
    this.performSync();
  }

  private handleOfflineEvent(): void {
    this.emit('offline');
  }

  private savePendingChanges(): void {
    // Save any pending changes before page unload
    if (this.syncQueue.length > 0) {
      localStorage.setItem('pending_sync_queue', JSON.stringify(this.syncQueue));
    }
  }

  private getVapidPublicKey(): Uint8Array {
    // This should be your actual VAPID public key
    const vapidPublicKey = 'BEl62iUYgUivxIkv69yViEuiBIa40HI80NM9f8HnKJuOmLsOBJXoXVqNOXNy6EqTXJBHI9aJ64BpfgROv9mU8EC';
    const padding = '='.repeat((4 - vapidPublicKey.length % 4) % 4);
    const base64 = (vapidPublicKey + padding).replace(/\-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    return new Uint8Array([...rawData].map(char => char.charCodeAt(0)));
  }

  private async sendSubscriptionToServer(subscription: PushSubscription): Promise<void> {
    await fetch('/api/push/subscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify({
        subscription,
        userId: this.userId,
        deviceId: this.deviceId
      })
    });
  }

  // Event System

  on(event: string, callback: Function): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event)!.push(callback);
  }

  off(event: string, callback: Function): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  private emit(event: string, data?: any): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.forEach(callback => callback(data));
    }
  }
}

// Create and export singleton instance
export const mobileSyncService = new MobileSyncService();

// Export types
export type { SyncableData, SyncConflict, SyncStats, PushNotificationData };