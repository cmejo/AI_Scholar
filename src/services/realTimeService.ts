/**
 * Real-Time Service for AI Scholar
 * Provides WebSocket-based real-time features including document collaboration,
 * AI progress updates, and live notifications
 */

interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: number;
  id: string;
}

interface ConnectionConfig {
  url: string;
  reconnectInterval: number;
  maxReconnectAttempts: number;
  heartbeatInterval: number;
  timeout: number;
}

interface SubscriptionCallback {
  (data: any): void;
}

interface DocumentUpdate {
  documentId: string;
  userId: string;
  type: 'content' | 'annotation' | 'metadata';
  changes: any;
  timestamp: number;
}

interface AIProgressUpdate {
  queryId: string;
  stage: 'processing' | 'embedding' | 'searching' | 'generating' | 'complete' | 'error';
  progress: number;
  message?: string;
  result?: any;
  error?: string;
}

interface NotificationUpdate {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: number;
  persistent?: boolean;
}

class RealTimeService {
  private ws: WebSocket | null = null;
  private config: ConnectionConfig;
  private subscriptions: Map<string, Set<SubscriptionCallback>> = new Map();
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private isConnecting = false;
  private messageQueue: WebSocketMessage[] = [];
  private connectionPromise: Promise<void> | null = null;

  constructor(config?: Partial<ConnectionConfig>) {
    this.config = {
      url: this.getWebSocketUrl(),
      reconnectInterval: 3000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
      timeout: 10000,
      ...config
    };
  }

  private getWebSocketUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/ws`;
  }

  async connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return Promise.resolve();
    }

    if (this.connectionPromise) {
      return this.connectionPromise;
    }

    this.connectionPromise = this.establishConnection();
    return this.connectionPromise;
  }

  private async establishConnection(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.isConnecting) {
        return;
      }

      this.isConnecting = true;
      console.log(`🔌 Connecting to WebSocket: ${this.config.url}`);

      try {
        this.ws = new WebSocket(this.config.url);

        const timeout = setTimeout(() => {
          if (this.ws?.readyState !== WebSocket.OPEN) {
            this.ws?.close();
            reject(new Error('WebSocket connection timeout'));
          }
        }, this.config.timeout);

        this.ws.onopen = () => {
          clearTimeout(timeout);
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.connectionPromise = null;
          
          console.log('✅ WebSocket connected successfully');
          
          // Start heartbeat
          this.startHeartbeat();
          
          // Send queued messages
          this.flushMessageQueue();
          
          // Notify subscribers
          this.notifySubscribers('connection', { status: 'connected' });
          
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event);
        };

        this.ws.onclose = (event) => {
          clearTimeout(timeout);
          this.isConnecting = false;
          this.connectionPromise = null;
          
          console.log(`🔌 WebSocket closed: ${event.code} - ${event.reason}`);
          
          this.stopHeartbeat();
          this.notifySubscribers('connection', { status: 'disconnected', code: event.code });
          
          // Attempt reconnection if not a clean close
          if (event.code !== 1000 && this.reconnectAttempts < this.config.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          clearTimeout(timeout);
          this.isConnecting = false;
          this.connectionPromise = null;
          
          console.error('❌ WebSocket error:', error);
          this.notifySubscribers('connection', { status: 'error', error });
          
          reject(error);
        };

      } catch (error) {
        this.isConnecting = false;
        this.connectionPromise = null;
        reject(error);
      }
    });
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    const delay = Math.min(
      this.config.reconnectInterval * Math.pow(2, this.reconnectAttempts),
      30000 // Max 30 seconds
    );

    console.log(`🔄 Scheduling reconnect in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect().catch(error => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send('heartbeat', { timestamp: Date.now() });
      }
    }, this.config.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      // Handle heartbeat responses
      if (message.type === 'heartbeat_response') {
        return;
      }

      console.log('📨 Received message:', message.type, message.payload);
      
      // Notify subscribers
      this.notifySubscribers(message.type, message.payload);
      
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }

  private notifySubscribers(type: string, data: any): void {
    const callbacks = this.subscriptions.get(type);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in subscription callback for ${type}:`, error);
        }
      });
    }
  }

  private send(type: string, payload: any): void {
    const message: WebSocketMessage = {
      type,
      payload,
      timestamp: Date.now(),
      id: this.generateMessageId()
    };

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      // Queue message for later
      this.messageQueue.push(message);
      
      // Attempt to connect if not already connecting
      if (!this.isConnecting && this.ws?.readyState !== WebSocket.CONNECTING) {
        this.connect().catch(error => {
          console.error('Failed to connect for queued message:', error);
        });
      }
    }
  }

  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      const message = this.messageQueue.shift();
      if (message) {
        this.ws.send(JSON.stringify(message));
      }
    }
  }

  private generateMessageId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  // Public subscription methods
  subscribe(type: string, callback: SubscriptionCallback): () => void {
    if (!this.subscriptions.has(type)) {
      this.subscriptions.set(type, new Set());
    }
    
    this.subscriptions.get(type)!.add(callback);
    
    // Return unsubscribe function
    return () => {
      const callbacks = this.subscriptions.get(type);
      if (callbacks) {
        callbacks.delete(callback);
        if (callbacks.size === 0) {
          this.subscriptions.delete(type);
        }
      }
    };
  }

  // Document collaboration methods
  async subscribeToDocumentUpdates(documentId: string, callback: (update: DocumentUpdate) => void): Promise<() => void> {
    await this.connect();
    
    // Subscribe to document updates
    const unsubscribe = this.subscribe('document_update', (data: DocumentUpdate) => {
      if (data.documentId === documentId) {
        callback(data);
      }
    });

    // Join document room
    this.send('join_document', { documentId });

    return () => {
      // Leave document room
      this.send('leave_document', { documentId });
      unsubscribe();
    };
  }

  async sendDocumentUpdate(documentId: string, update: Partial<DocumentUpdate>): Promise<void> {
    await this.connect();
    
    this.send('document_update', {
      documentId,
      ...update,
      timestamp: Date.now()
    });
  }

  // AI progress tracking methods
  async subscribeToAIProgress(queryId: string, callback: (progress: AIProgressUpdate) => void): Promise<() => void> {
    await this.connect();
    
    const unsubscribe = this.subscribe('ai_progress', (data: AIProgressUpdate) => {
      if (data.queryId === queryId) {
        callback(data);
      }
    });

    // Subscribe to AI progress for this query
    this.send('subscribe_ai_progress', { queryId });

    return () => {
      this.send('unsubscribe_ai_progress', { queryId });
      unsubscribe();
    };
  }

  async startAIQuery(queryId: string, query: string, options?: any): Promise<void> {
    await this.connect();
    
    this.send('start_ai_query', {
      queryId,
      query,
      options: options || {}
    });
  }

  // Notification methods
  subscribeToNotifications(callback: (notification: NotificationUpdate) => void): () => void {
    return this.subscribe('notification', callback);
  }

  async sendNotification(notification: Omit<NotificationUpdate, 'id' | 'timestamp'>): Promise<void> {
    await this.connect();
    
    this.send('notification', {
      ...notification,
      id: this.generateMessageId(),
      timestamp: Date.now()
    });
  }

  // Presence methods
  async updatePresence(documentId: string, presence: any): Promise<void> {
    await this.connect();
    
    this.send('presence_update', {
      documentId,
      presence,
      timestamp: Date.now()
    });
  }

  subscribeToPresence(documentId: string, callback: (presence: any) => void): () => void {
    return this.subscribe('presence_update', (data: any) => {
      if (data.documentId === documentId) {
        callback(data);
      }
    });
  }

  // Connection management
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    this.stopHeartbeat();

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.subscriptions.clear();
    this.messageQueue.length = 0;
    this.reconnectAttempts = 0;
  }

  getConnectionState(): string {
    if (!this.ws) return 'disconnected';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'connecting';
      case WebSocket.OPEN: return 'connected';
      case WebSocket.CLOSING: return 'closing';
      case WebSocket.CLOSED: return 'disconnected';
      default: return 'unknown';
    }
  }

  getStats(): any {
    return {
      connectionState: this.getConnectionState(),
      reconnectAttempts: this.reconnectAttempts,
      subscriptions: Array.from(this.subscriptions.keys()),
      queuedMessages: this.messageQueue.length,
      config: this.config
    };
  }
}

// Collaborative editing service
class CollaborativeEditor {
  private realTimeService: RealTimeService;
  private activeDocuments: Map<string, any> = new Map();

  constructor(realTimeService: RealTimeService) {
    this.realTimeService = realTimeService;
  }

  async shareDocument(documentId: string, users: string[]): Promise<void> {
    await this.realTimeService.connect();
    
    this.realTimeService.send('share_document', {
      documentId,
      users,
      timestamp: Date.now()
    });
  }

  async syncAnnotations(documentId: string, annotations: any[]): Promise<void> {
    await this.realTimeService.sendDocumentUpdate(documentId, {
      type: 'annotation',
      changes: { annotations },
      userId: 'current_user', // This should come from auth context
      timestamp: Date.now()
    });
  }

  async subscribeToCollaboration(
    documentId: string, 
    onUpdate: (update: DocumentUpdate) => void,
    onPresence: (presence: any) => void
  ): Promise<() => void> {
    
    const unsubscribeUpdates = await this.realTimeService.subscribeToDocumentUpdates(
      documentId, 
      onUpdate
    );
    
    const unsubscribePresence = this.realTimeService.subscribeToPresence(
      documentId,
      onPresence
    );

    // Track active document
    this.activeDocuments.set(documentId, {
      unsubscribeUpdates,
      unsubscribePresence
    });

    return () => {
      unsubscribeUpdates();
      unsubscribePresence();
      this.activeDocuments.delete(documentId);
    };
  }

  async updateCursor(documentId: string, position: any): Promise<void> {
    await this.realTimeService.updatePresence(documentId, {
      type: 'cursor',
      position,
      userId: 'current_user' // This should come from auth context
    });
  }

  async updateSelection(documentId: string, selection: any): Promise<void> {
    await this.realTimeService.updatePresence(documentId, {
      type: 'selection',
      selection,
      userId: 'current_user' // This should come from auth context
    });
  }
}

// AI Progress Tracker
class AIProgressTracker {
  private realTimeService: RealTimeService;
  private activeQueries: Map<string, any> = new Map();

  constructor(realTimeService: RealTimeService) {
    this.realTimeService = realTimeService;
  }

  async trackQuery(
    queryId: string, 
    query: string, 
    onProgress: (progress: AIProgressUpdate) => void,
    options?: any
  ): Promise<() => void> {
    
    const unsubscribe = await this.realTimeService.subscribeToAIProgress(
      queryId,
      onProgress
    );

    // Start the AI query
    await this.realTimeService.startAIQuery(queryId, query, options);

    // Track active query
    this.activeQueries.set(queryId, {
      query,
      startTime: Date.now(),
      unsubscribe
    });

    return () => {
      unsubscribe();
      this.activeQueries.delete(queryId);
    };
  }

  getActiveQueries(): string[] {
    return Array.from(this.activeQueries.keys());
  }

  getQueryInfo(queryId: string): any {
    return this.activeQueries.get(queryId);
  }
}

// Create global instances
export const realTimeService = new RealTimeService();
export const collaborativeEditor = new CollaborativeEditor(realTimeService);
export const aiProgressTracker = new AIProgressTracker(realTimeService);

// Auto-connect on module load
realTimeService.connect().catch(error => {
  console.warn('Initial WebSocket connection failed:', error);
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  realTimeService.disconnect();
});

export default realTimeService;