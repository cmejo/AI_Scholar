/**
 * Voice Navigation Service for voice-controlled navigation and research assistance
 */

import voiceCommandService, { VoiceCommand, CommandResult } from './voiceCommandService';

export interface NavigationCommand {
  destination: string;
  action: 'navigate' | 'open' | 'show' | 'close' | 'toggle';
  parameters?: Record<string, any>;
}

export interface VoiceShortcut {
  id: string;
  phrase: string;
  action: () => void | Promise<void>;
  description: string;
  category: 'navigation' | 'research' | 'document' | 'system';
  enabled: boolean;
}

export interface AccessibilityFeature {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  settings: Record<string, any>;
}

class VoiceNavigationService {
  private shortcuts: Map<string, VoiceShortcut> = new Map();
  private accessibilityFeatures: Map<string, AccessibilityFeature> = new Map();
  private navigationHistory: string[] = [];
  private currentPage: string = '';
  private isNavigationEnabled: boolean = true;

  constructor() {
    this.initializeVoiceShortcuts();
    this.initializeAccessibilityFeatures();
    this.setupEventListeners();
  }

  /**
   * Initialize voice shortcuts for common research operations
   */
  private initializeVoiceShortcuts(): void {
    const shortcuts: VoiceShortcut[] = [
      // Navigation shortcuts
      {
        id: 'nav_home',
        phrase: 'go home',
        action: () => this.navigateTo('/'),
        description: 'Navigate to home page',
        category: 'navigation',
        enabled: true
      },
      {
        id: 'nav_documents',
        phrase: 'show documents',
        action: () => this.navigateTo('/documents'),
        description: 'Open documents page',
        category: 'navigation',
        enabled: true
      },
      {
        id: 'nav_chat',
        phrase: 'open chat',
        action: () => this.navigateTo('/chat'),
        description: 'Open chat interface',
        category: 'navigation',
        enabled: true
      },
      {
        id: 'nav_analytics',
        phrase: 'show analytics',
        action: () => this.navigateTo('/analytics'),
        description: 'Open analytics dashboard',
        category: 'navigation',
        enabled: true
      },
      {
        id: 'nav_settings',
        phrase: 'open settings',
        action: () => this.navigateTo('/settings'),
        description: 'Open settings page',
        category: 'navigation',
        enabled: true
      },

      // Research shortcuts
      {
        id: 'research_search',
        phrase: 'start search',
        action: () => this.focusSearchBox(),
        description: 'Focus on search input',
        category: 'research',
        enabled: true
      },
      {
        id: 'research_upload',
        phrase: 'upload document',
        action: () => this.triggerFileUpload(),
        description: 'Open file upload dialog',
        category: 'research',
        enabled: true
      },
      {
        id: 'research_new_chat',
        phrase: 'new conversation',
        action: () => this.startNewConversation(),
        description: 'Start new chat conversation',
        category: 'research',
        enabled: true
      },
      {
        id: 'research_knowledge_graph',
        phrase: 'show knowledge graph',
        action: () => this.openKnowledgeGraph(),
        description: 'Open knowledge graph visualization',
        category: 'research',
        enabled: true
      },

      // Document shortcuts
      {
        id: 'doc_next',
        phrase: 'next document',
        action: () => this.navigateDocument('next'),
        description: 'Go to next document',
        category: 'document',
        enabled: true
      },
      {
        id: 'doc_previous',
        phrase: 'previous document',
        action: () => this.navigateDocument('previous'),
        description: 'Go to previous document',
        category: 'document',
        enabled: true
      },
      {
        id: 'doc_close',
        phrase: 'close document',
        action: () => this.closeCurrentDocument(),
        description: 'Close current document',
        category: 'document',
        enabled: true
      },

      // System shortcuts
      {
        id: 'sys_help',
        phrase: 'show help',
        action: () => this.showHelp(),
        description: 'Show help information',
        category: 'system',
        enabled: true
      },
      {
        id: 'sys_back',
        phrase: 'go back',
        action: () => this.goBack(),
        description: 'Go back to previous page',
        category: 'system',
        enabled: true
      },
      {
        id: 'sys_forward',
        phrase: 'go forward',
        action: () => this.goForward(),
        description: 'Go forward to next page',
        category: 'system',
        enabled: true
      },
      {
        id: 'sys_refresh',
        phrase: 'refresh page',
        action: () => this.refreshPage(),
        description: 'Refresh current page',
        category: 'system',
        enabled: true
      }
    ];

    shortcuts.forEach(shortcut => {
      this.shortcuts.set(shortcut.id, shortcut);
    });
  }

  /**
   * Initialize accessibility features for visually impaired users
   */
  private initializeAccessibilityFeatures(): void {
    const features: AccessibilityFeature[] = [
      {
        id: 'screen_reader',
        name: 'Screen Reader Support',
        description: 'Enhanced screen reader compatibility with ARIA labels and descriptions',
        enabled: true,
        settings: {
          announceNavigation: true,
          announceContent: true,
          announceActions: true,
          verbosityLevel: 'medium'
        }
      },
      {
        id: 'voice_feedback',
        name: 'Voice Feedback',
        description: 'Spoken feedback for navigation and actions',
        enabled: false,
        settings: {
          feedbackLevel: 'essential',
          voice: 'default',
          rate: 1.0,
          volume: 0.8
        }
      },
      {
        id: 'keyboard_navigation',
        name: 'Enhanced Keyboard Navigation',
        description: 'Improved keyboard navigation with voice commands',
        enabled: true,
        settings: {
          skipLinks: true,
          focusIndicators: true,
          customShortcuts: true
        }
      },
      {
        id: 'high_contrast',
        name: 'High Contrast Mode',
        description: 'High contrast visual theme for better visibility',
        enabled: false,
        settings: {
          contrastLevel: 'high',
          colorScheme: 'dark'
        }
      },
      {
        id: 'text_scaling',
        name: 'Text Scaling',
        description: 'Adjustable text size for better readability',
        enabled: false,
        settings: {
          scaleFactor: 1.2,
          lineHeight: 1.5,
          letterSpacing: 'normal'
        }
      }
    ];

    features.forEach(feature => {
      this.accessibilityFeatures.set(feature.id, feature);
    });
  }

  /**
   * Setup event listeners for voice commands
   */
  private setupEventListeners(): void {
    // Listen for voice navigation events
    window.addEventListener('voiceNavigate', this.handleVoiceNavigation.bind(this));
    window.addEventListener('voiceSearch', this.handleVoiceSearch.bind(this));
    window.addEventListener('voiceDocumentAction', this.handleVoiceDocumentAction.bind(this));
    window.addEventListener('voiceOpenSettings', this.handleVoiceOpenSettings.bind(this));
    window.addEventListener('voiceStop', this.handleVoiceStop.bind(this));

    // Listen for keyboard navigation
    document.addEventListener('keydown', this.handleKeyboardNavigation.bind(this));

    // Listen for route changes to update current page
    window.addEventListener('popstate', this.updateCurrentPage.bind(this));
  }

  /**
   * Handle voice navigation commands
   */
  private async handleVoiceNavigation(event: CustomEvent): Promise<void> {
    const { destination, command, context } = event.detail;

    try {
      // Find matching shortcut
      const shortcut = this.findShortcutByPhrase(destination);
      
      if (shortcut && shortcut.enabled) {
        await shortcut.action();
        this.announceAction(`Navigating to ${destination}`);
      } else {
        // Try direct navigation
        const route = this.parseDestinationToRoute(destination);
        if (route) {
          await this.navigateTo(route);
          this.announceAction(`Navigating to ${destination}`);
        } else {
          this.announceError(`I don't know how to navigate to "${destination}"`);
        }
      }
    } catch (error) {
      this.announceError(`Navigation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Handle voice search commands
   */
  private async handleVoiceSearch(event: CustomEvent): Promise<void> {
    const { query, command, context } = event.detail;

    try {
      // Navigate to search page if not already there
      if (!window.location.pathname.includes('/search')) {
        await this.navigateTo('/search');
      }

      // Focus search box and set query
      await this.focusSearchBox();
      await this.setSearchQuery(query);
      
      this.announceAction(`Searching for "${query}"`);
    } catch (error) {
      this.announceError(`Search failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Handle voice document actions
   */
  private async handleVoiceDocumentAction(event: CustomEvent): Promise<void> {
    const { action, documentName, command, context } = event.detail;

    try {
      switch (action) {
        case 'upload':
        case 'add':
        case 'import':
          await this.triggerFileUpload();
          this.announceAction('Opening file upload dialog');
          break;
        
        case 'open':
        case 'view':
        case 'read':
          if (documentName) {
            await this.openDocument(documentName);
            this.announceAction(`Opening document "${documentName}"`);
          } else {
            await this.navigateTo('/documents');
            this.announceAction('Opening documents page');
          }
          break;
        
        case 'delete':
        case 'remove':
          if (documentName) {
            await this.deleteDocument(documentName);
            this.announceAction(`Deleting document "${documentName}"`);
          } else {
            this.announceError('Please specify which document to delete');
          }
          break;
        
        case 'summarize':
          if (documentName) {
            await this.summarizeDocument(documentName);
            this.announceAction(`Summarizing document "${documentName}"`);
          } else {
            await this.summarizeCurrentDocument();
            this.announceAction('Summarizing current document');
          }
          break;
        
        default:
          this.announceError(`Unknown document action: ${action}`);
      }
    } catch (error) {
      this.announceError(`Document action failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Handle voice settings commands
   */
  private async handleVoiceOpenSettings(event: CustomEvent): Promise<void> {
    try {
      await this.navigateTo('/settings');
      this.announceAction('Opening settings');
    } catch (error) {
      this.announceError(`Failed to open settings: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Handle voice stop commands
   */
  private async handleVoiceStop(event: CustomEvent): Promise<void> {
    try {
      // Stop voice recognition
      const stopEvent = new CustomEvent('stopVoiceRecognition');
      window.dispatchEvent(stopEvent);
      
      this.announceAction('Voice commands stopped');
    } catch (error) {
      this.announceError(`Failed to stop voice commands: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Handle keyboard navigation
   */
  private handleKeyboardNavigation(event: KeyboardEvent): void {
    // Only handle if accessibility keyboard navigation is enabled
    const keyboardFeature = this.accessibilityFeatures.get('keyboard_navigation');
    if (!keyboardFeature?.enabled) return;

    // Handle custom keyboard shortcuts
    if (event.altKey) {
      switch (event.key) {
        case 'h':
          event.preventDefault();
          this.navigateTo('/');
          break;
        case 'd':
          event.preventDefault();
          this.navigateTo('/documents');
          break;
        case 'c':
          event.preventDefault();
          this.navigateTo('/chat');
          break;
        case 's':
          event.preventDefault();
          this.focusSearchBox();
          break;
        case 'u':
          event.preventDefault();
          this.triggerFileUpload();
          break;
      }
    }
  }

  /**
   * Navigate to a specific route
   */
  private async navigateTo(route: string): Promise<void> {
    // Add to navigation history
    if (this.currentPage && this.currentPage !== route) {
      this.navigationHistory.push(this.currentPage);
      
      // Keep history limited to 50 entries
      if (this.navigationHistory.length > 50) {
        this.navigationHistory = this.navigationHistory.slice(-50);
      }
    }

    // Update current page
    this.currentPage = route;

    // Perform navigation (this would integrate with your routing system)
    if (typeof window !== 'undefined') {
      // For React Router or similar
      const navigationEvent = new CustomEvent('navigate', {
        detail: { route }
      });
      window.dispatchEvent(navigationEvent);
      
      // Fallback to direct navigation
      if (window.history && window.history.pushState) {
        window.history.pushState({}, '', route);
        
        // Trigger popstate to update components
        const popstateEvent = new PopStateEvent('popstate', { state: {} });
        window.dispatchEvent(popstateEvent);
      }
    }
  }

  /**
   * Focus on search box
   */
  private async focusSearchBox(): Promise<void> {
    const searchInput = document.querySelector('input[type="search"], input[placeholder*="search" i], #search-input, .search-input') as HTMLInputElement;
    
    if (searchInput) {
      searchInput.focus();
      searchInput.select();
    } else {
      // If no search box found, navigate to search page
      await this.navigateTo('/search');
      
      // Try again after navigation
      setTimeout(() => {
        const searchInput = document.querySelector('input[type="search"], input[placeholder*="search" i], #search-input, .search-input') as HTMLInputElement;
        if (searchInput) {
          searchInput.focus();
          searchInput.select();
        }
      }, 100);
    }
  }

  /**
   * Set search query
   */
  private async setSearchQuery(query: string): Promise<void> {
    const searchInput = document.querySelector('input[type="search"], input[placeholder*="search" i], #search-input, .search-input') as HTMLInputElement;
    
    if (searchInput) {
      searchInput.value = query;
      
      // Trigger input event
      const inputEvent = new Event('input', { bubbles: true });
      searchInput.dispatchEvent(inputEvent);
      
      // Trigger search
      const searchEvent = new CustomEvent('search', {
        detail: { query }
      });
      window.dispatchEvent(searchEvent);
    }
  }

  /**
   * Trigger file upload dialog
   */
  private async triggerFileUpload(): Promise<void> {
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    if (fileInput) {
      fileInput.click();
    } else {
      // Navigate to upload page or trigger upload modal
      const uploadEvent = new CustomEvent('openUploadDialog');
      window.dispatchEvent(uploadEvent);
    }
  }

  /**
   * Start new conversation
   */
  private async startNewConversation(): Promise<void> {
    const newChatEvent = new CustomEvent('startNewConversation');
    window.dispatchEvent(newChatEvent);
  }

  /**
   * Open knowledge graph
   */
  private async openKnowledgeGraph(): Promise<void> {
    const kgEvent = new CustomEvent('openKnowledgeGraph');
    window.dispatchEvent(kgEvent);
  }

  /**
   * Navigate document (next/previous)
   */
  private async navigateDocument(direction: 'next' | 'previous'): Promise<void> {
    const navEvent = new CustomEvent('navigateDocument', {
      detail: { direction }
    });
    window.dispatchEvent(navEvent);
  }

  /**
   * Close current document
   */
  private async closeCurrentDocument(): Promise<void> {
    const closeEvent = new CustomEvent('closeCurrentDocument');
    window.dispatchEvent(closeEvent);
  }

  /**
   * Open specific document
   */
  private async openDocument(documentName: string): Promise<void> {
    const openEvent = new CustomEvent('openDocument', {
      detail: { documentName }
    });
    window.dispatchEvent(openEvent);
  }

  /**
   * Delete document
   */
  private async deleteDocument(documentName: string): Promise<void> {
    const deleteEvent = new CustomEvent('deleteDocument', {
      detail: { documentName }
    });
    window.dispatchEvent(deleteEvent);
  }

  /**
   * Summarize document
   */
  private async summarizeDocument(documentName: string): Promise<void> {
    const summarizeEvent = new CustomEvent('summarizeDocument', {
      detail: { documentName }
    });
    window.dispatchEvent(summarizeEvent);
  }

  /**
   * Summarize current document
   */
  private async summarizeCurrentDocument(): Promise<void> {
    const summarizeEvent = new CustomEvent('summarizeCurrentDocument');
    window.dispatchEvent(summarizeEvent);
  }

  /**
   * Show help
   */
  private async showHelp(): Promise<void> {
    const helpEvent = new CustomEvent('showHelp');
    window.dispatchEvent(helpEvent);
  }

  /**
   * Go back in navigation history
   */
  private async goBack(): Promise<void> {
    if (this.navigationHistory.length > 0) {
      const previousPage = this.navigationHistory.pop()!;
      await this.navigateTo(previousPage);
    } else if (window.history) {
      window.history.back();
    }
  }

  /**
   * Go forward in navigation history
   */
  private async goForward(): Promise<void> {
    if (window.history) {
      window.history.forward();
    }
  }

  /**
   * Refresh current page
   */
  private async refreshPage(): Promise<void> {
    if (window.location) {
      window.location.reload();
    }
  }

  /**
   * Find shortcut by phrase
   */
  private findShortcutByPhrase(phrase: string): VoiceShortcut | undefined {
    const normalizedPhrase = phrase.toLowerCase().trim();
    
    for (const shortcut of this.shortcuts.values()) {
      if (shortcut.phrase.toLowerCase() === normalizedPhrase) {
        return shortcut;
      }
    }
    
    // Try partial matching
    for (const shortcut of this.shortcuts.values()) {
      if (normalizedPhrase.includes(shortcut.phrase.toLowerCase()) || 
          shortcut.phrase.toLowerCase().includes(normalizedPhrase)) {
        return shortcut;
      }
    }
    
    return undefined;
  }

  /**
   * Parse destination to route
   */
  private parseDestinationToRoute(destination: string): string | null {
    const normalizedDest = destination.toLowerCase().trim();
    
    const routeMap: Record<string, string> = {
      'home': '/',
      'dashboard': '/',
      'documents': '/documents',
      'files': '/documents',
      'papers': '/documents',
      'chat': '/chat',
      'conversation': '/chat',
      'analytics': '/analytics',
      'stats': '/analytics',
      'statistics': '/analytics',
      'settings': '/settings',
      'preferences': '/settings',
      'configuration': '/settings',
      'search': '/search',
      'find': '/search',
      'help': '/help',
      'support': '/help'
    };
    
    return routeMap[normalizedDest] || null;
  }

  /**
   * Update current page
   */
  private updateCurrentPage(): void {
    if (typeof window !== 'undefined' && window.location) {
      this.currentPage = window.location.pathname;
    }
  }

  /**
   * Announce action for accessibility
   */
  private announceAction(message: string): void {
    const voiceFeedback = this.accessibilityFeatures.get('voice_feedback');
    const screenReader = this.accessibilityFeatures.get('screen_reader');
    
    // Voice feedback
    if (voiceFeedback?.enabled) {
      const speakEvent = new CustomEvent('voiceSpeak', {
        detail: { 
          content: message,
          settings: voiceFeedback.settings
        }
      });
      window.dispatchEvent(speakEvent);
    }
    
    // Screen reader announcement
    if (screenReader?.enabled && screenReader.settings.announceActions) {
      this.announceToScreenReader(message);
    }
    
    console.log(`Voice Navigation: ${message}`);
  }

  /**
   * Announce error for accessibility
   */
  private announceError(message: string): void {
    const voiceFeedback = this.accessibilityFeatures.get('voice_feedback');
    const screenReader = this.accessibilityFeatures.get('screen_reader');
    
    // Voice feedback
    if (voiceFeedback?.enabled) {
      const speakEvent = new CustomEvent('voiceSpeak', {
        detail: { 
          content: `Error: ${message}`,
          settings: voiceFeedback.settings
        }
      });
      window.dispatchEvent(speakEvent);
    }
    
    // Screen reader announcement
    if (screenReader?.enabled) {
      this.announceToScreenReader(`Error: ${message}`, 'assertive');
    }
    
    console.error(`Voice Navigation Error: ${message}`);
  }

  /**
   * Announce to screen reader
   */
  private announceToScreenReader(message: string, priority: 'polite' | 'assertive' = 'polite'): void {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    // Remove after announcement
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  }

  /**
   * Get available shortcuts
   */
  getAvailableShortcuts(): VoiceShortcut[] {
    return Array.from(this.shortcuts.values()).filter(shortcut => shortcut.enabled);
  }

  /**
   * Get shortcuts by category
   */
  getShortcutsByCategory(category: string): VoiceShortcut[] {
    return Array.from(this.shortcuts.values()).filter(
      shortcut => shortcut.category === category && shortcut.enabled
    );
  }

  /**
   * Enable/disable shortcut
   */
  setShortcutEnabled(shortcutId: string, enabled: boolean): void {
    const shortcut = this.shortcuts.get(shortcutId);
    if (shortcut) {
      shortcut.enabled = enabled;
    }
  }

  /**
   * Get accessibility features
   */
  getAccessibilityFeatures(): AccessibilityFeature[] {
    return Array.from(this.accessibilityFeatures.values());
  }

  /**
   * Enable/disable accessibility feature
   */
  setAccessibilityFeatureEnabled(featureId: string, enabled: boolean): void {
    const feature = this.accessibilityFeatures.get(featureId);
    if (feature) {
      feature.enabled = enabled;
      
      // Apply feature changes
      this.applyAccessibilityFeature(feature);
    }
  }

  /**
   * Update accessibility feature settings
   */
  updateAccessibilityFeatureSettings(featureId: string, settings: Record<string, any>): void {
    const feature = this.accessibilityFeatures.get(featureId);
    if (feature) {
      feature.settings = { ...feature.settings, ...settings };
      
      // Apply feature changes
      this.applyAccessibilityFeature(feature);
    }
  }

  /**
   * Apply accessibility feature
   */
  private applyAccessibilityFeature(feature: AccessibilityFeature): void {
    switch (feature.id) {
      case 'high_contrast':
        if (feature.enabled) {
          document.body.classList.add('high-contrast');
        } else {
          document.body.classList.remove('high-contrast');
        }
        break;
        
      case 'text_scaling':
        if (feature.enabled) {
          document.documentElement.style.fontSize = `${feature.settings.scaleFactor * 100}%`;
          document.documentElement.style.lineHeight = feature.settings.lineHeight;
          document.documentElement.style.letterSpacing = feature.settings.letterSpacing;
        } else {
          document.documentElement.style.fontSize = '';
          document.documentElement.style.lineHeight = '';
          document.documentElement.style.letterSpacing = '';
        }
        break;
    }
  }

  /**
   * Get navigation history
   */
  getNavigationHistory(): string[] {
    return [...this.navigationHistory];
  }

  /**
   * Get current page
   */
  getCurrentPage(): string {
    return this.currentPage;
  }

  /**
   * Enable/disable navigation
   */
  setNavigationEnabled(enabled: boolean): void {
    this.isNavigationEnabled = enabled;
  }

  /**
   * Check if navigation is enabled
   */
  isNavigationEnabledCheck(): boolean {
    return this.isNavigationEnabled;
  }
}

export default new VoiceNavigationService();