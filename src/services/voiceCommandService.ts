/**
 * Enhanced Voice Command Service for natural language processing and command execution
 * Integrates with backend voice command router for advanced NLP and contextual conversation management
 */

export interface VoiceCommand {
  id: string;
  text: string;
  intent: CommandIntent;
  entities: Entity[];
  confidence: number;
  timestamp: number;
  language?: string;
}

export interface CommandIntent {
  name: string;
  confidence: number;
  parameters: Record<string, any>;
}

export interface Entity {
  type: string;
  value: string;
  confidence: number;
  start: number;
  end: number;
}

export interface CommandResult {
  success: boolean;
  message: string;
  data?: any;
  error?: string;
  execution_time?: number;
  follow_up_actions?: string[];
  context_updates?: Record<string, any>;
}

export interface ConversationContext {
  sessionId: string;
  history: VoiceCommand[];
  currentTopic?: string;
  userPreferences: Record<string, any>;
  lastCommand?: VoiceCommand;
  turnCount?: number;
  conversationFlow?: string[];
  contextVariables?: Record<string, any>;
}

export interface CommandExecution {
  executionId: string;
  command: VoiceCommand;
  status: 'pending' | 'executing' | 'completed' | 'failed' | 'cancelled';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  result?: CommandResult;
  error?: string;
}

export interface ConversationAnalytics {
  sessionId: string;
  turnCount: number;
  conversationDuration: number;
  intentDistribution: Record<string, number>;
  contextVariablesCount: number;
  pendingClarifications: number;
  lastActivity: string;
  isActive: boolean;
}

class VoiceCommandService {
  private baseUrl: string;
  private conversationContexts: Map<string, ConversationContext> = new Map();
  private activeExecutions: Map<string, CommandExecution> = new Map();
  private eventListeners: Map<string, Set<Function>> = new Map();
  private sessionId: string;
  private intentClassifier: Map<string, Function> = new Map();
  private entityExtractors: Map<string, Function> = new Map();
  private commandHandlers: Map<string, Function> = new Map();
  private commandPatterns: Map<string, RegExp[]> = new Map();

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    this.sessionId = this.generateSessionId();
    this.initializeEventListeners();
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private initializeEventListeners(): void {
    // Initialize event listener maps
    this.eventListeners.set('commandProcessed', new Set());
    this.eventListeners.set('executionStatusChanged', new Set());
    this.eventListeners.set('conversationUpdated', new Set());
    this.eventListeners.set('error', new Set());
  }

  /**
   * Add event listener for voice command events
   */
  public addEventListener(event: string, listener: Function): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, new Set());
    }
    this.eventListeners.get(event)!.add(listener);
  }

  /**
   * Remove event listener
   */
  public removeEventListener(event: string, listener: Function): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.delete(listener);
    }
  }

  /**
   * Emit event to all listeners
   */
  private emitEvent(event: string, data: any): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(data);
        } catch (error) {
          console.error(`Error in event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Initialize intent classifiers
   */
  private initializeIntentClassifiers(): void {
    this.intentClassifier.set('search', (text: string) => {
      const searchKeywords = ['search', 'find', 'look', 'show', 'what', 'tell', 'about'];
      const words = text.toLowerCase().split(/\s+/);
      const matches = words.filter(word => searchKeywords.includes(word)).length;
      return matches / words.length;
    });

    this.intentClassifier.set('navigate', (text: string) => {
      const navKeywords = ['go', 'open', 'navigate', 'take', 'page', 'section', 'tab'];
      const words = text.toLowerCase().split(/\s+/);
      const matches = words.filter(word => navKeywords.includes(word)).length;
      return matches / words.length;
    });

    this.intentClassifier.set('document', (text: string) => {
      const docKeywords = ['document', 'file', 'paper', 'upload', 'add', 'import', 'delete', 'remove', 'open', 'view', 'read', 'summarize'];
      const words = text.toLowerCase().split(/\s+/);
      const matches = words.filter(word => docKeywords.includes(word)).length;
      return matches / words.length;
    });

    this.intentClassifier.set('chat', (text: string) => {
      const chatKeywords = ['ask', 'question', 'query', 'explain', 'describe', 'compare', 'contrast'];
      const words = text.toLowerCase().split(/\s+/);
      const matches = words.filter(word => chatKeywords.includes(word)).length;
      return matches / words.length;
    });

    this.intentClassifier.set('system', (text: string) => {
      const systemKeywords = ['help', 'assistance', 'settings', 'preferences', 'stop', 'pause', 'cancel', 'quit', 'repeat'];
      const words = text.toLowerCase().split(/\s+/);
      const matches = words.filter(word => systemKeywords.includes(word)).length;
      return matches / words.length;
    });

    this.intentClassifier.set('voice_control', (text: string) => {
      const voiceKeywords = ['speak', 'read', 'say', 'louder', 'quieter', 'faster', 'slower', 'voice', 'mute', 'unmute'];
      const words = text.toLowerCase().split(/\s+/);
      const matches = words.filter(word => voiceKeywords.includes(word)).length;
      return matches / words.length;
    });
  }

  /**
   * Initialize entity extractors
   */
  private initializeEntityExtractors(): void {
    // Document name extractor
    this.entityExtractors.set('document_name', (text: string) => {
      const entities: Entity[] = [];
      const patterns = [
        /(?:document|file|paper)\s+(?:called|named|titled)\s+"([^"]+)"/gi,
        /(?:document|file|paper)\s+"([^"]+)"/gi,
        /"([^"]+)"(?:\s+(?:document|file|paper))?/gi
      ];

      patterns.forEach(pattern => {
        let match;
        while ((match = pattern.exec(text)) !== null) {
          entities.push({
            type: 'document_name',
            value: match[1],
            confidence: 0.9,
            start: match.index,
            end: match.index + match[0].length
          });
        }
      });

      return entities;
    });

    // Topic extractor
    this.entityExtractors.set('topic', (text: string) => {
      const entities: Entity[] = [];
      const topicPatterns = [
        /(?:about|regarding|concerning)\s+([a-zA-Z\s]+?)(?:\s+(?:in|from|with)|$)/gi,
        /(?:search|find|look for)\s+([a-zA-Z\s]+?)(?:\s+(?:in|from|with)|$)/gi
      ];

      topicPatterns.forEach(pattern => {
        let match;
        while ((match = pattern.exec(text)) !== null) {
          entities.push({
            type: 'topic',
            value: match[1].trim(),
            confidence: 0.8,
            start: match.index,
            end: match.index + match[0].length
          });
        }
      });

      return entities;
    });

    // Page/Section extractor
    this.entityExtractors.set('page_section', (text: string) => {
      const entities: Entity[] = [];
      const pagePatterns = [
        /(?:go to|open|show)\s+(?:the\s+)?([a-zA-Z\s]+?)(?:\s+(?:page|section|tab))/gi,
        /(?:page|section|tab)\s+([a-zA-Z\s]+)/gi
      ];

      pagePatterns.forEach(pattern => {
        let match;
        while ((match = pattern.exec(text)) !== null) {
          entities.push({
            type: 'page_section',
            value: match[1].trim(),
            confidence: 0.85,
            start: match.index,
            end: match.index + match[0].length
          });
        }
      });

      return entities;
    });

    // Number extractor
    this.entityExtractors.set('number', (text: string) => {
      const entities: Entity[] = [];
      const numberPattern = /\b(\d+(?:\.\d+)?)\b/g;
      
      let match;
      while ((match = numberPattern.exec(text)) !== null) {
        entities.push({
          type: 'number',
          value: match[1],
          confidence: 0.95,
          start: match.index,
          end: match.index + match[0].length
        });
      }

      return entities;
    });
  }

  /**
   * Initialize command handlers
   */
  private initializeCommandHandlers(): void {
    // Search command handler
    this.commandHandlers.set('search', async (command: VoiceCommand, context: ConversationContext) => {
      const topicEntity = command.entities.find(e => e.type === 'topic');
      const query = topicEntity?.value || command.text.replace(/^(search|find|look for|show me)\s+/i, '');

      try {
        // Trigger search in the application
        const searchEvent = new CustomEvent('voiceSearch', {
          detail: { query, command, context }
        });
        window.dispatchEvent(searchEvent);

        return {
          success: true,
          message: `Searching for "${query}"`,
          data: { query, type: 'search' }
        };
      } catch (error) {
        return {
          success: false,
          message: 'Search failed',
          error: error instanceof Error ? error.message : 'Unknown error'
        };
      }
    });

    // Navigation command handler
    this.commandHandlers.set('navigate', async (command: VoiceCommand, context: ConversationContext) => {
      const pageEntity = command.entities.find(e => e.type === 'page_section');
      const destination = pageEntity?.value || command.text.replace(/^(go to|open|navigate to|show me|take me to)\s+/i, '');

      try {
        // Trigger navigation in the application
        const navEvent = new CustomEvent('voiceNavigate', {
          detail: { destination, command, context }
        });
        window.dispatchEvent(navEvent);

        return {
          success: true,
          message: `Navigating to ${destination}`,
          data: { destination, type: 'navigate' }
        };
      } catch (error) {
        return {
          success: false,
          message: 'Navigation failed',
          error: error instanceof Error ? error.message : 'Unknown error'
        };
      }
    });

    // Document command handler
    this.commandHandlers.set('document', async (command: VoiceCommand, context: ConversationContext) => {
      const docEntity = command.entities.find(e => e.type === 'document_name');
      const action = command.text.match(/^(upload|add|import|delete|remove|open|view|read|summarize)/i)?.[1]?.toLowerCase();

      try {
        // Trigger document action in the application
        const docEvent = new CustomEvent('voiceDocumentAction', {
          detail: { 
            action, 
            documentName: docEntity?.value,
            command, 
            context 
          }
        });
        window.dispatchEvent(docEvent);

        return {
          success: true,
          message: `${action ? action.charAt(0).toUpperCase() + action.slice(1) : 'Processing'} document${docEntity ? ` "${docEntity.value}"` : ''}`,
          data: { action, documentName: docEntity?.value, type: 'document' }
        };
      } catch (error) {
        return {
          success: false,
          message: 'Document action failed',
          error: error instanceof Error ? error.message : 'Unknown error'
        };
      }
    });

    // Chat command handler
    this.commandHandlers.set('chat', async (command: VoiceCommand, context: ConversationContext) => {
      const query = command.text.replace(/^(ask|question|query|explain|describe|tell me)\s+/i, '');

      try {
        // Trigger chat in the application
        const chatEvent = new CustomEvent('voiceChat', {
          detail: { query, command, context }
        });
        window.dispatchEvent(chatEvent);

        return {
          success: true,
          message: `Processing your question: "${query}"`,
          data: { query, type: 'chat' }
        };
      } catch (error) {
        return {
          success: false,
          message: 'Chat processing failed',
          error: error instanceof Error ? error.message : 'Unknown error'
        };
      }
    });

    // System command handler
    this.commandHandlers.set('system', async (command: VoiceCommand, context: ConversationContext) => {
      const text = command.text.toLowerCase();

      if (text.includes('help') || text.includes('assistance')) {
        return {
          success: true,
          message: 'I can help you search documents, navigate the interface, upload files, and answer questions. Try saying "search for machine learning" or "open documents page".',
          data: { type: 'help' }
        };
      }

      if (text.includes('settings') || text.includes('preferences')) {
        const settingsEvent = new CustomEvent('voiceOpenSettings', {
          detail: { command, context }
        });
        window.dispatchEvent(settingsEvent);

        return {
          success: true,
          message: 'Opening settings',
          data: { type: 'settings' }
        };
      }

      if (text.includes('stop') || text.includes('cancel') || text.includes('quit')) {
        const stopEvent = new CustomEvent('voiceStop', {
          detail: { command, context }
        });
        window.dispatchEvent(stopEvent);

        return {
          success: true,
          message: 'Stopping voice commands',
          data: { type: 'stop' }
        };
      }

      if (text.includes('repeat') || text.includes('say again')) {
        const lastCommand = context.lastCommand;
        if (lastCommand) {
          return await this.executeCommand(lastCommand.text, context.sessionId);
        } else {
          return {
            success: false,
            message: 'No previous command to repeat',
            data: { type: 'repeat' }
          };
        }
      }

      return {
        success: true,
        message: 'System command processed',
        data: { type: 'system' }
      };
    });

    // Voice control command handler
    this.commandHandlers.set('voice_control', async (command: VoiceCommand, context: ConversationContext) => {
      const text = command.text.toLowerCase();

      if (text.includes('speak') || text.includes('read') || text.includes('say')) {
        const content = command.text.replace(/^(speak|read|say)\s+/i, '');
        const speakEvent = new CustomEvent('voiceSpeak', {
          detail: { content, command, context }
        });
        window.dispatchEvent(speakEvent);

        return {
          success: true,
          message: `Speaking: "${content}"`,
          data: { content, type: 'speak' }
        };
      }

      if (text.includes('louder') || text.includes('quieter') || text.includes('faster') || text.includes('slower')) {
        const adjustment = text.includes('louder') ? 'volume_up' :
                          text.includes('quieter') ? 'volume_down' :
                          text.includes('faster') ? 'speed_up' : 'speed_down';

        const adjustEvent = new CustomEvent('voiceAdjust', {
          detail: { adjustment, command, context }
        });
        window.dispatchEvent(adjustEvent);

        return {
          success: true,
          message: `Adjusting voice ${adjustment.replace('_', ' ')}`,
          data: { adjustment, type: 'adjust' }
        };
      }

      if (text.includes('change voice') || text.includes('switch voice')) {
        const voiceEvent = new CustomEvent('voiceChangeVoice', {
          detail: { command, context }
        });
        window.dispatchEvent(voiceEvent);

        return {
          success: true,
          message: 'Changing voice settings',
          data: { type: 'change_voice' }
        };
      }

      if (text.includes('mute') || text.includes('unmute') || text.includes('silence')) {
        const muteEvent = new CustomEvent('voiceMute', {
          detail: { 
            action: text.includes('unmute') ? 'unmute' : 'mute',
            command, 
            context 
          }
        });
        window.dispatchEvent(muteEvent);

        return {
          success: true,
          message: text.includes('unmute') ? 'Unmuting voice' : 'Muting voice',
          data: { action: text.includes('unmute') ? 'unmute' : 'mute', type: 'mute' }
        };
      }

      return {
        success: true,
        message: 'Voice control command processed',
        data: { type: 'voice_control' }
      };
    });
  }

  /**
   * Process voice command text using backend NLP service
   */
  async processCommand(text: string, sessionId: string = this.sessionId, language: string = 'en'): Promise<VoiceCommand> {
    try {
      const response = await fetch(`${this.baseUrl}/api/voice/process-command`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text.trim(),
          session_id: sessionId,
          language: language
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const command: VoiceCommand = await response.json();
      
      // Update local conversation context
      this.updateLocalConversationContext(sessionId, command);
      
      // Emit event
      this.emitEvent('commandProcessed', { command, sessionId });
      
      return command;
    } catch (error) {
      console.error('Error processing voice command:', error);
      
      // Fallback to local processing if backend is unavailable
      return this.processCommandLocally(text, sessionId);
    }
  }

  /**
   * Execute a voice command using backend router
   */
  async executeCommand(text: string, sessionId: string = this.sessionId, userId?: string): Promise<CommandResult> {
    try {
      const response = await fetch(`${this.baseUrl}/api/voice/execute-command`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text.trim(),
          session_id: sessionId,
          user_id: userId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: CommandResult = await response.json();
      
      // Handle follow-up actions
      if (result.follow_up_actions) {
        await this.handleFollowUpActions(result.follow_up_actions, result.data, sessionId);
      }
      
      // Update conversation context if provided
      if (result.context_updates) {
        await this.updateConversationContextFromResult(sessionId, result.context_updates);
      }
      
      // Emit event
      this.emitEvent('commandProcessed', { result, sessionId, text });
      
      return result;
    } catch (error) {
      console.error('Error executing voice command:', error);
      
      const errorResult: CommandResult = {
        success: false,
        message: 'Failed to execute voice command. Please try again.',
        error: error instanceof Error ? error.message : 'Unknown error'
      };
      
      this.emitEvent('error', { error: errorResult.error, sessionId, text });
      
      return errorResult;
    }
  }

  /**
   * Extract intent from text
   */
  private async extractIntent(text: string): Promise<CommandIntent> {
    let bestIntent = 'unknown';
    let bestConfidence = 0;
    const parameters: Record<string, any> = {};

    // Check pattern-based matching first
    for (const [intentName, patterns] of this.commandPatterns.entries()) {
      for (const pattern of patterns) {
        const match = text.match(pattern);
        if (match) {
          const confidence = 0.9; // High confidence for pattern matches
          if (confidence > bestConfidence) {
            bestIntent = intentName;
            bestConfidence = confidence;
            
            // Extract parameters from pattern match
            if (match.length > 1) {
              parameters.matched_groups = match.slice(1);
            }
          }
        }
      }
    }

    // Use classifier-based matching as fallback
    if (bestConfidence < 0.5) {
      for (const [intentName, classifier] of this.intentClassifier.entries()) {
        const confidence = classifier(text);
        if (confidence > bestConfidence) {
          bestIntent = intentName;
          bestConfidence = confidence;
        }
      }
    }

    return {
      name: bestIntent,
      confidence: bestConfidence,
      parameters
    };
  }

  /**
   * Extract entities from text
   */
  private async extractEntities(text: string): Promise<Entity[]> {
    const allEntities: Entity[] = [];

    for (const [entityType, extractor] of this.entityExtractors.entries()) {
      const entities = extractor(text);
      allEntities.push(...entities);
    }

    // Sort entities by confidence and remove overlaps
    return this.resolveEntityOverlaps(allEntities);
  }

  /**
   * Resolve overlapping entities by keeping the highest confidence ones
   */
  private resolveEntityOverlaps(entities: Entity[]): Entity[] {
    const sortedEntities = entities.sort((a, b) => b.confidence - a.confidence);
    const resolvedEntities: Entity[] = [];

    for (const entity of sortedEntities) {
      const hasOverlap = resolvedEntities.some(existing => 
        (entity.start >= existing.start && entity.start < existing.end) ||
        (entity.end > existing.start && entity.end <= existing.end) ||
        (entity.start <= existing.start && entity.end >= existing.end)
      );

      if (!hasOverlap) {
        resolvedEntities.push(entity);
      }
    }

    return resolvedEntities.sort((a, b) => a.start - b.start);
  }

  /**
   * Calculate overall confidence score
   */
  private calculateOverallConfidence(intent: CommandIntent, entities: Entity[]): number {
    const intentWeight = 0.7;
    const entityWeight = 0.3;

    const entityConfidence = entities.length > 0 
      ? entities.reduce((sum, entity) => sum + entity.confidence, 0) / entities.length
      : 0.5; // Neutral confidence if no entities

    return (intent.confidence * intentWeight) + (entityConfidence * entityWeight);
  }

  /**
   * Handle follow-up actions from command execution
   */
  private async handleFollowUpActions(actions: string[], data: any, sessionId: string): Promise<void> {
    for (const action of actions) {
      try {
        switch (action) {
          case 'display_search_results':
            this.emitEvent('searchResults', { results: data.results, query: data.query, sessionId });
            break;
          
          case 'navigate_to_page':
            this.emitEvent('navigate', { target: data.target, sessionId });
            break;
          
          case 'open_document':
            this.emitEvent('openDocument', { documentName: data.document_name, sessionId });
            break;
          
          case 'display_chat_response':
            this.emitEvent('chatResponse', { response: data.response, topic: data.topic, sessionId });
            break;
          
          case 'text_to_speech':
            this.emitEvent('textToSpeech', { content: data.content, sessionId });
            break;
          
          case 'adjust_voice_settings':
            this.emitEvent('adjustVoiceSettings', { adjustment: data.adjustment, sessionId });
            break;
          
          case 'open_settings':
            this.emitEvent('openSettings', { sessionId });
            break;
          
          case 'stop_voice_interface':
            this.emitEvent('stopVoiceInterface', { sessionId });
            break;
          
          case 'request_clarification':
            this.emitEvent('requestClarification', { message: data.message, sessionId });
            break;
          
          case 'provide_suggestions':
            this.emitEvent('provideSuggestions', { suggestions: data.suggestions, sessionId });
            break;
          
          case 'display_help':
            this.emitEvent('displayHelp', { helpContent: data, sessionId });
            break;
          
          default:
            console.warn(`Unknown follow-up action: ${action}`);
        }
      } catch (error) {
        console.error(`Error handling follow-up action ${action}:`, error);
      }
    }
  }

  /**
   * Update conversation context from command result
   */
  private async updateConversationContextFromResult(sessionId: string, contextUpdates: Record<string, any>): Promise<void> {
    try {
      const context = this.getLocalConversationContext(sessionId);
      
      if (context.contextVariables) {
        Object.assign(context.contextVariables, contextUpdates);
      } else {
        context.contextVariables = { ...contextUpdates };
      }
      
      this.conversationContexts.set(sessionId, context);
      this.emitEvent('conversationUpdated', { context, sessionId });
    } catch (error) {
      console.error('Error updating conversation context:', error);
    }
  }

  /**
   * Get or create local conversation context
   */
  private getLocalConversationContext(sessionId: string): ConversationContext {
    if (!this.conversationContexts.has(sessionId)) {
      this.conversationContexts.set(sessionId, {
        sessionId,
        history: [],
        userPreferences: {},
        currentTopic: undefined,
        lastCommand: undefined,
        turnCount: 0,
        conversationFlow: [],
        contextVariables: {}
      });
    }
    return this.conversationContexts.get(sessionId)!;
  }

  /**
   * Update local conversation context with new command
   */
  private updateLocalConversationContext(sessionId: string, command: VoiceCommand): void {
    const context = this.getLocalConversationContext(sessionId);
    
    // Add to history
    context.history.push(command);
    
    // Keep only last 20 commands in history
    if (context.history.length > 20) {
      context.history = context.history.slice(-20);
    }

    // Update current topic if relevant
    const topicEntity = command.entities.find(e => e.type === 'topic');
    if (topicEntity) {
      context.currentTopic = topicEntity.value;
    }

    // Update conversation flow
    if (context.conversationFlow) {
      context.conversationFlow.push(command.intent.name);
      if (context.conversationFlow.length > 20) {
        context.conversationFlow = context.conversationFlow.slice(-20);
      }
    }

    // Update turn count
    if (context.turnCount !== undefined) {
      context.turnCount++;
    }

    // Set last command
    context.lastCommand = command;

    this.conversationContexts.set(sessionId, context);
  }

  /**
   * Fallback local command processing when backend is unavailable
   */
  private async processCommandLocally(text: string, sessionId: string): Promise<VoiceCommand> {
    const command: VoiceCommand = {
      id: `cmd_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      text: text.trim(),
      intent: { name: 'unknown', confidence: 0.5, parameters: {} },
      entities: [],
      confidence: 0.5,
      timestamp: Date.now(),
      language: 'en'
    };

    // Simple local intent detection
    const textLower = text.toLowerCase();
    
    if (textLower.includes('search') || textLower.includes('find') || textLower.includes('look for')) {
      command.intent = { name: 'search', confidence: 0.8, parameters: {} };
    } else if (textLower.includes('go to') || textLower.includes('open') || textLower.includes('navigate')) {
      command.intent = { name: 'navigate', confidence: 0.8, parameters: {} };
    } else if (textLower.includes('document') || textLower.includes('file') || textLower.includes('upload')) {
      command.intent = { name: 'document', confidence: 0.8, parameters: {} };
    } else if (textLower.includes('help') || textLower.includes('what can you do')) {
      command.intent = { name: 'system', confidence: 0.9, parameters: {} };
    } else if (textLower.includes('explain') || textLower.includes('tell me') || textLower.includes('what is')) {
      command.intent = { name: 'chat', confidence: 0.7, parameters: {} };
    }

    // Update local context
    this.updateLocalConversationContext(sessionId, command);

    return command;
  }

  /**
   * Get conversation context from backend
   */
  async getConversationContext(sessionId: string = this.sessionId): Promise<ConversationContext | null> {
    try {
      const response = await fetch(`${this.baseUrl}/api/voice/conversation-context/${sessionId}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          return null; // No context found
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const context: ConversationContext = await response.json();
      
      // Update local context
      this.conversationContexts.set(sessionId, context);
      
      return context;
    } catch (error) {
      console.error('Error getting conversation context:', error);
      
      // Return local context as fallback
      return this.conversationContexts.get(sessionId) || null;
    }
  }

  /**
   * Get conversation history
   */
  getConversationHistory(sessionId: string = this.sessionId): VoiceCommand[] {
    const context = this.conversationContexts.get(sessionId);
    return context?.history || [];
  }

  /**
   * Clear conversation context
   */
  async clearConversationContext(sessionId: string = this.sessionId): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/voice/conversation-context/${sessionId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        // Clear local context
        this.conversationContexts.delete(sessionId);
        this.emitEvent('conversationCleared', { sessionId });
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Error clearing conversation context:', error);
      
      // Clear local context anyway
      this.conversationContexts.delete(sessionId);
      return false;
    }
  }

  /**
   * Get command suggestions based on partial text
   */
  async getCommandSuggestions(partialText: string, limit: number = 5): Promise<string[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/voice/command-suggestions?partial_text=${encodeURIComponent(partialText)}&limit=${limit}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.suggestions || [];
    } catch (error) {
      console.error('Error getting command suggestions:', error);
      
      // Return local suggestions as fallback
      return this.getLocalCommandSuggestions(partialText, limit);
    }
  }

  /**
   * Get local command suggestions as fallback
   */
  private getLocalCommandSuggestions(partialText: string, limit: number): string[] {
    const suggestions = [
      'search for documents',
      'find research papers',
      'go to documents page',
      'open settings',
      'upload a file',
      'help me',
      'what can you do',
      'explain this concept',
      'summarize document',
      'navigate to chat'
    ];

    const textLower = partialText.toLowerCase();
    const filtered = suggestions.filter(suggestion => 
      suggestion.toLowerCase().includes(textLower) || 
      textLower.split(' ').some(word => suggestion.toLowerCase().includes(word))
    );

    return filtered.slice(0, limit);
  }

  /**
   * Get conversation analytics
   */
  async getConversationAnalytics(sessionId: string = this.sessionId): Promise<ConversationAnalytics | null> {
    try {
      const response = await fetch(`${this.baseUrl}/api/voice/session-analytics/${sessionId}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting conversation analytics:', error);
      return null;
    }
  }

  /**
   * Get available command intents
   */
  getAvailableIntents(): string[] {
    return ['search', 'navigate', 'document', 'chat', 'system', 'voice_control'];
  }

  /**
   * Get command examples for help
   */
  getCommandExamples(): Record<string, string[]> {
    return {
      search: [
        'Search for machine learning papers',
        'Find documents about artificial intelligence',
        'What is neural network architecture?',
        'Tell me about deep learning techniques',
        'Look for research on natural language processing'
      ],
      navigate: [
        'Go to documents page',
        'Open settings panel',
        'Show me the chat interface',
        'Take me to analytics dashboard',
        'Navigate to research tools'
      ],
      document: [
        'Upload a new research paper',
        'Open document "thesis draft"',
        'Delete file "old notes"',
        'Summarize the current document',
        'Import PDF from my computer'
      ],
      chat: [
        'Ask about the research methodology',
        'Explain this statistical concept',
        'Compare these two research papers',
        'What does this technical term mean?',
        'Help me understand this algorithm'
      ],
      system: [
        'Help me with voice commands',
        'What can you do for me?',
        'Open system settings',
        'Stop voice recognition',
        'Show available commands'
      ],
      voice_control: [
        'Speak louder please',
        'Read this text aloud',
        'Change to a different voice',
        'Mute voice output',
        'Adjust speech speed'
      ]
    };
  }

  /**
   * Get current session ID
   */
  getCurrentSessionId(): string {
    return this.sessionId;
  }

  /**
   * Set session ID (useful for user authentication)
   */
  setSessionId(sessionId: string): void {
    this.sessionId = sessionId;
  }

  /**
   * Get execution status for a command
   */
  async getExecutionStatus(executionId: string): Promise<CommandExecution | null> {
    try {
      const response = await fetch(`${this.baseUrl}/api/voice/execution-status/${executionId}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting execution status:', error);
      return null;
    }
  }

  /**
   * Cancel a command execution
   */
  async cancelExecution(executionId: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/voice/cancel-execution/${executionId}`, {
        method: 'POST'
      });

      return response.ok;
    } catch (error) {
      console.error('Error canceling execution:', error);
      return false;
    }
  }

  /**
   * Test command processing (for debugging)
   */
  async testCommand(text: string, sessionId?: string): Promise<{ command: VoiceCommand; result: CommandResult }> {
    const testSessionId = sessionId || `test_${Date.now()}`;
    
    try {
      const command = await this.processCommand(text, testSessionId);
      const result = await this.executeCommand(text, testSessionId);
      
      return { command, result };
    } catch (error) {
      console.error('Error testing command:', error);
      
      // Return error result
      const errorCommand: VoiceCommand = {
        id: `error_${Date.now()}`,
        text,
        intent: { name: 'unknown', confidence: 0, parameters: {} },
        entities: [],
        confidence: 0,
        timestamp: Date.now()
      };
      
      const errorResult: CommandResult = {
        success: false,
        message: 'Test command failed',
        error: error instanceof Error ? error.message : 'Unknown error'
      };
      
      return { command: errorCommand, result: errorResult };
    }
  }

  /**
   * Health check for voice command service
   */
  async healthCheck(): Promise<{ status: string; details: any }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/voice/health`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const healthData = await response.json();
      
      return {
        status: 'healthy',
        details: {
          backend: healthData,
          frontend: {
            sessionId: this.sessionId,
            activeContexts: this.conversationContexts.size,
            activeExecutions: this.activeExecutions.size,
            eventListeners: Object.fromEntries(
              Array.from(this.eventListeners.entries()).map(([event, listeners]) => [event, listeners.size])
            )
          }
        }
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        details: {
          error: error instanceof Error ? error.message : 'Unknown error',
          frontend: {
            sessionId: this.sessionId,
            activeContexts: this.conversationContexts.size,
            activeExecutions: this.activeExecutions.size
          }
        }
      };
    }
  }

  /**
   * Cleanup resources
   */
  cleanup(): void {
    // Clear all contexts
    this.conversationContexts.clear();
    this.activeExecutions.clear();
    
    // Clear all event listeners
    this.eventListeners.clear();
    
    console.log('Voice command service cleaned up');
  }
}

export default new VoiceCommandService();