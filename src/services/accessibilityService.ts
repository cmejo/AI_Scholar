/**
 * Accessibility Service
 * Manages accessibility features, preferences, and compliance
 */

interface AccessibilityPreferences {
  screenReaderEnabled: boolean;
  highContrastMode: boolean;
  reducedMotion: boolean;
  fontSize: 'small' | 'medium' | 'large' | 'xlarge';
  keyboardNavigationOnly: boolean;
  voiceAnnouncements: boolean;
  focusIndicators: boolean;
  colorBlindnessSupport: 'none' | 'protanopia' | 'deuteranopia' | 'tritanopia';
}

interface AccessibilityAnnouncement {
  message: string;
  priority: 'polite' | 'assertive';
  delay?: number;
}

class AccessibilityService {
  private preferences: AccessibilityPreferences;
  private announcer: HTMLElement | null = null;
  private focusHistory: HTMLElement[] = [];
  private keyboardNavigationActive = false;

  constructor() {
    this.preferences = this.loadPreferences();
    this.initializeService();
  }

  private loadPreferences(): AccessibilityPreferences {
    const stored = localStorage.getItem('accessibility_preferences');
    const defaults: AccessibilityPreferences = {
      screenReaderEnabled: this.detectScreenReader(),
      highContrastMode: window.matchMedia('(prefers-contrast: high)').matches,
      reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
      fontSize: 'medium',
      keyboardNavigationOnly: false,
      voiceAnnouncements: true,
      focusIndicators: true,
      colorBlindnessSupport: 'none'
    };

    return stored ? { ...defaults, ...JSON.parse(stored) } : defaults;
  }

  private savePreferences(): void {
    localStorage.setItem('accessibility_preferences', JSON.stringify(this.preferences));
  }

  private detectScreenReader(): boolean {
    // Check for common screen reader indicators
    return !!(
      navigator.userAgent.includes('NVDA') ||
      navigator.userAgent.includes('JAWS') ||
      navigator.userAgent.includes('VoiceOver') ||
      window.speechSynthesis ||
      document.querySelector('[aria-live]')
    );
  }

  private initializeService(): void {
    this.createAnnouncer();
    this.setupKeyboardNavigation();
    this.applyPreferences();
    this.setupMediaQueryListeners();
  }

  private createAnnouncer(): void {
    this.announcer = document.createElement('div');
    this.announcer.setAttribute('aria-live', 'polite');
    this.announcer.setAttribute('aria-atomic', 'true');
    this.announcer.className = 'sr-only';
    this.announcer.style.cssText = `
      position: absolute !important;
      width: 1px !important;
      height: 1px !important;
      padding: 0 !important;
      margin: -1px !important;
      overflow: hidden !important;
      clip: rect(0, 0, 0, 0) !important;
      white-space: nowrap !important;
      border: 0 !important;
    `;
    document.body.appendChild(this.announcer);
  }

  private setupKeyboardNavigation(): void {
    // Track keyboard usage
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Tab') {
        this.keyboardNavigationActive = true;
        document.body.classList.add('keyboard-navigation');
      }
      
      // Handle global keyboard shortcuts
      this.handleGlobalKeyboardShortcuts(event);
    });

    // Track mouse usage
    document.addEventListener('mousedown', () => {
      this.keyboardNavigationActive = false;
      document.body.classList.remove('keyboard-navigation');
    });

    // Handle escape key for modal/overlay dismissal
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        this.handleEscapeKey();
      }
    });

    // Skip links functionality
    this.createSkipLinks();
    
    // Add keyboard navigation helpers
    this.setupArrowKeyNavigation();
    this.setupFocusManagement();
  }

  private createSkipLinks(): void {
    const skipLinks = document.createElement('div');
    skipLinks.className = 'skip-links';
    skipLinks.innerHTML = `
      <a href="#main-content" class="skip-link">Skip to main content</a>
      <a href="#main-sidebar" class="skip-link">Skip to navigation</a>
      <a href="#chat-input" class="skip-link">Skip to search</a>
      <a href="#accessibility-settings" class="skip-link">Skip to accessibility settings</a>
    `;
    
    // Add skip link functionality
    skipLinks.addEventListener('click', (event) => {
      const target = event.target as HTMLAnchorElement;
      if (target.classList.contains('skip-link')) {
        event.preventDefault();
        const targetId = target.getAttribute('href')?.substring(1);
        const targetElement = targetId ? document.getElementById(targetId) : null;
        if (targetElement) {
          targetElement.focus();
          targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
          this.announce(`Skipped to ${target.textContent}`);
        }
      }
    });
    
    document.body.insertBefore(skipLinks, document.body.firstChild);
  }

  private setupMediaQueryListeners(): void {
    // High contrast mode
    const contrastQuery = window.matchMedia('(prefers-contrast: high)');
    contrastQuery.addEventListener('change', (e) => {
      this.updatePreference('highContrastMode', e.matches);
    });

    // Reduced motion
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    motionQuery.addEventListener('change', (e) => {
      this.updatePreference('reducedMotion', e.matches);
    });
  }

  private applyPreferences(): void {
    const root = document.documentElement;
    
    // Apply font size
    root.style.setProperty('--font-size-multiplier', this.getFontSizeMultiplier());
    
    // Apply high contrast mode
    if (this.preferences.highContrastMode) {
      document.body.classList.add('high-contrast');
    } else {
      document.body.classList.remove('high-contrast');
    }
    
    // Apply reduced motion
    if (this.preferences.reducedMotion) {
      document.body.classList.add('reduced-motion');
    } else {
      document.body.classList.remove('reduced-motion');
    }
    
    // Apply color blindness support
    if (this.preferences.colorBlindnessSupport !== 'none') {
      document.body.classList.add(`colorblind-${this.preferences.colorBlindnessSupport}`);
    }
    
    // Apply focus indicators
    if (this.preferences.focusIndicators) {
      document.body.classList.add('enhanced-focus');
    }
  }

  private getFontSizeMultiplier(): string {
    const multipliers = {
      small: '0.875',
      medium: '1',
      large: '1.125',
      xlarge: '1.25'
    };
    return multipliers[this.preferences.fontSize];
  }

  private handleEscapeKey(): void {
    // Close modals, dropdowns, etc.
    const activeModal = document.querySelector('[role="dialog"][aria-hidden="false"]');
    if (activeModal) {
      const closeButton = activeModal.querySelector('[aria-label*="close"], [aria-label*="Close"]');
      if (closeButton instanceof HTMLElement) {
        closeButton.click();
      }
    }

    // Close dropdowns
    const openDropdowns = document.querySelectorAll('[aria-expanded="true"]');
    openDropdowns.forEach(dropdown => {
      if (dropdown instanceof HTMLElement) {
        dropdown.click();
      }
    });
  }

  // Public API methods
  announce(message: string, priority: 'polite' | 'assertive' = 'polite', delay = 0): void {
    if (!this.announcer || !this.preferences.voiceAnnouncements) return;

    setTimeout(() => {
      if (this.announcer) {
        this.announcer.setAttribute('aria-live', priority);
        this.announcer.textContent = message;
        
        // Clear after announcement
        setTimeout(() => {
          if (this.announcer) {
            this.announcer.textContent = '';
          }
        }, 1000);
      }
    }, delay);
  }

  updatePreference<K extends keyof AccessibilityPreferences>(
    key: K, 
    value: AccessibilityPreferences[K]
  ): void {
    this.preferences[key] = value;
    this.savePreferences();
    this.applyPreferences();
    
    // Announce preference change
    this.announce(`${key.replace(/([A-Z])/g, ' $1').toLowerCase()} ${value ? 'enabled' : 'disabled'}`);
  }

  getPreferences(): AccessibilityPreferences {
    return { ...this.preferences };
  }

  // Focus management
  saveFocus(): void {
    const activeElement = document.activeElement as HTMLElement;
    if (activeElement && activeElement !== document.body) {
      this.focusHistory.push(activeElement);
    }
  }

  restoreFocus(): void {
    const lastFocused = this.focusHistory.pop();
    if (lastFocused && document.contains(lastFocused)) {
      lastFocused.focus();
    }
  }

  // ARIA helpers
  setAriaLabel(element: HTMLElement, label: string): void {
    element.setAttribute('aria-label', label);
  }

  setAriaDescribedBy(element: HTMLElement, describedById: string): void {
    element.setAttribute('aria-describedby', describedById);
  }

  setAriaExpanded(element: HTMLElement, expanded: boolean): void {
    element.setAttribute('aria-expanded', expanded.toString());
  }

  setAriaHidden(element: HTMLElement, hidden: boolean): void {
    element.setAttribute('aria-hidden', hidden.toString());
  }

  setAriaPressed(element: HTMLElement, pressed: boolean): void {
    element.setAttribute('aria-pressed', pressed.toString());
  }

  setAriaSelected(element: HTMLElement, selected: boolean): void {
    element.setAttribute('aria-selected', selected.toString());
  }

  setAriaChecked(element: HTMLElement, checked: boolean): void {
    element.setAttribute('aria-checked', checked.toString());
  }

  setAriaDisabled(element: HTMLElement, disabled: boolean): void {
    element.setAttribute('aria-disabled', disabled.toString());
  }

  setAriaInvalid(element: HTMLElement, invalid: boolean): void {
    element.setAttribute('aria-invalid', invalid.toString());
  }

  setAriaRequired(element: HTMLElement, required: boolean): void {
    element.setAttribute('aria-required', required.toString());
  }

  setAriaLive(element: HTMLElement, live: 'off' | 'polite' | 'assertive'): void {
    element.setAttribute('aria-live', live);
  }

  setAriaAtomic(element: HTMLElement, atomic: boolean): void {
    element.setAttribute('aria-atomic', atomic.toString());
  }

  setAriaRelevant(element: HTMLElement, relevant: string): void {
    element.setAttribute('aria-relevant', relevant);
  }

  setAriaBusy(element: HTMLElement, busy: boolean): void {
    element.setAttribute('aria-busy', busy.toString());
  }

  setAriaControls(element: HTMLElement, controlsId: string): void {
    element.setAttribute('aria-controls', controlsId);
  }

  setAriaOwns(element: HTMLElement, ownsId: string): void {
    element.setAttribute('aria-owns', ownsId);
  }

  setAriaFlowTo(element: HTMLElement, flowToId: string): void {
    element.setAttribute('aria-flowto', flowToId);
  }

  setAriaLevel(element: HTMLElement, level: number): void {
    element.setAttribute('aria-level', level.toString());
  }

  setAriaSetSize(element: HTMLElement, setSize: number): void {
    element.setAttribute('aria-setsize', setSize.toString());
  }

  setAriaPosInSet(element: HTMLElement, posInSet: number): void {
    element.setAttribute('aria-posinset', posInSet.toString());
  }

  setRole(element: HTMLElement, role: string): void {
    element.setAttribute('role', role);
  }

  // Comprehensive ARIA labeling for complex components
  labelComplexComponent(element: HTMLElement, config: {
    label?: string;
    describedBy?: string;
    role?: string;
    expanded?: boolean;
    selected?: boolean;
    checked?: boolean;
    disabled?: boolean;
    invalid?: boolean;
    required?: boolean;
    level?: number;
    setSize?: number;
    posInSet?: number;
    controls?: string;
    owns?: string;
    flowTo?: string;
  }): void {
    if (config.label) this.setAriaLabel(element, config.label);
    if (config.describedBy) this.setAriaDescribedBy(element, config.describedBy);
    if (config.role) this.setRole(element, config.role);
    if (config.expanded !== undefined) this.setAriaExpanded(element, config.expanded);
    if (config.selected !== undefined) this.setAriaSelected(element, config.selected);
    if (config.checked !== undefined) this.setAriaChecked(element, config.checked);
    if (config.disabled !== undefined) this.setAriaDisabled(element, config.disabled);
    if (config.invalid !== undefined) this.setAriaInvalid(element, config.invalid);
    if (config.required !== undefined) this.setAriaRequired(element, config.required);
    if (config.level !== undefined) this.setAriaLevel(element, config.level);
    if (config.setSize !== undefined) this.setAriaSetSize(element, config.setSize);
    if (config.posInSet !== undefined) this.setAriaPosInSet(element, config.posInSet);
    if (config.controls) this.setAriaControls(element, config.controls);
    if (config.owns) this.setAriaOwns(element, config.owns);
    if (config.flowTo) this.setAriaFlowTo(element, config.flowTo);
  }

  // Keyboard navigation helpers
  trapFocus(container: HTMLElement): () => void {
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    ) as NodeListOf<HTMLElement>;
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return;

      if (event.shiftKey) {
        if (document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    };

    container.addEventListener('keydown', handleTabKey);
    
    // Focus first element
    firstElement?.focus();

    // Return cleanup function
    return () => {
      container.removeEventListener('keydown', handleTabKey);
    };
  }

  // Color contrast helpers
  checkColorContrast(foreground: string, background: string): {
    ratio: number;
    wcagAA: boolean;
    wcagAAA: boolean;
  } {
    const getLuminance = (color: string): number => {
      // Simplified luminance calculation
      const rgb = this.hexToRgb(color);
      if (!rgb) return 0;
      
      const [r, g, b] = [rgb.r, rgb.g, rgb.b].map(c => {
        c = c / 255;
        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
      });
      
      return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };

    const l1 = getLuminance(foreground);
    const l2 = getLuminance(background);
    const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);

    return {
      ratio,
      wcagAA: ratio >= 4.5,
      wcagAAA: ratio >= 7
    };
  }

  private hexToRgb(hex: string): { r: number; g: number; b: number } | null {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : null;
  }

  // Screen reader detection
  isScreenReaderActive(): boolean {
    return this.preferences.screenReaderEnabled;
  }

  // Keyboard navigation detection
  isKeyboardNavigationActive(): boolean {
    return this.keyboardNavigationActive;
  }

  // Enhanced keyboard navigation methods
  private handleGlobalKeyboardShortcuts(event: KeyboardEvent): void {
    // Alt + 1-9 for quick navigation
    if (event.altKey && event.key >= '1' && event.key <= '9') {
      event.preventDefault();
      const shortcutNumber = parseInt(event.key);
      this.handleNavigationShortcut(shortcutNumber);
    }

    // F1 for help (override browser default)
    if (event.key === 'F1') {
      event.preventDefault();
      this.showKeyboardShortcuts();
    }

    // Alt + A for accessibility settings
    if (event.altKey && event.key.toLowerCase() === 'a') {
      event.preventDefault();
      this.openAccessibilitySettings();
    }

    // Alt + S for search/chat input
    if (event.altKey && event.key.toLowerCase() === 's') {
      event.preventDefault();
      const searchInput = document.getElementById('chat-input') as HTMLInputElement;
      if (searchInput) {
        searchInput.focus();
        this.announce('Focused on search input');
      }
    }

    // Alt + M for main content
    if (event.altKey && event.key.toLowerCase() === 'm') {
      event.preventDefault();
      const mainContent = document.getElementById('main-content');
      if (mainContent) {
        mainContent.focus();
        this.announce('Focused on main content');
      }
    }

    // Alt + N for navigation/sidebar
    if (event.altKey && event.key.toLowerCase() === 'n') {
      event.preventDefault();
      const sidebar = document.getElementById('main-sidebar');
      if (sidebar) {
        const firstButton = sidebar.querySelector('button') as HTMLElement;
        if (firstButton) {
          firstButton.focus();
          this.announce('Focused on navigation');
        }
      }
    }

    // Alt + H for help/keyboard shortcuts
    if (event.altKey && event.key.toLowerCase() === 'h') {
      event.preventDefault();
      this.showKeyboardShortcuts();
    }

    // Ctrl + Plus/Minus for font size
    if (event.ctrlKey && (event.key === '+' || event.key === '=')) {
      event.preventDefault();
      this.increaseFontSize();
    }

    if (event.ctrlKey && event.key === '-') {
      event.preventDefault();
      this.decreaseFontSize();
    }

    // Ctrl + Alt + C for high contrast toggle
    if (event.ctrlKey && event.altKey && event.key.toLowerCase() === 'c') {
      event.preventDefault();
      this.updatePreference('highContrastMode', !this.preferences.highContrastMode);
    }

    // Ctrl + Alt + M for reduced motion toggle
    if (event.ctrlKey && event.altKey && event.key.toLowerCase() === 'm') {
      event.preventDefault();
      this.updatePreference('reducedMotion', !this.preferences.reducedMotion);
    }
  }

  private handleNavigationShortcut(number: number): void {
    const navigationItems = document.querySelectorAll('[role="navigation"] button, nav button');
    const targetItem = navigationItems[number - 1] as HTMLElement;
    if (targetItem) {
      targetItem.focus();
      targetItem.click();
      this.announce(`Navigated to ${targetItem.textContent}`);
    }
  }

  private openAccessibilitySettings(): void {
    // Trigger accessibility settings modal
    const settingsButton = document.querySelector('[aria-label*="accessibility"], [aria-label*="Accessibility"]') as HTMLElement;
    if (settingsButton) {
      settingsButton.click();
      this.announce('Opened accessibility settings');
    }
  }

  private setupArrowKeyNavigation(): void {
    document.addEventListener('keydown', (event) => {
      // Only handle arrow keys when not in input fields
      const activeElement = document.activeElement;
      if (activeElement && (
        activeElement.tagName === 'INPUT' ||
        activeElement.tagName === 'TEXTAREA' ||
        activeElement.contentEditable === 'true'
      )) {
        return;
      }

      const focusableElements = this.getFocusableElements();
      const currentIndex = Array.from(focusableElements).indexOf(activeElement as HTMLElement);

      switch (event.key) {
        case 'ArrowDown':
        case 'ArrowRight':
          event.preventDefault();
          this.focusNextElement(focusableElements, currentIndex);
          break;
        case 'ArrowUp':
        case 'ArrowLeft':
          event.preventDefault();
          this.focusPreviousElement(focusableElements, currentIndex);
          break;
        case 'Home':
          event.preventDefault();
          this.focusFirstElement(focusableElements);
          break;
        case 'End':
          event.preventDefault();
          this.focusLastElement(focusableElements);
          break;
      }
    });
  }

  private setupFocusManagement(): void {
    // Enhanced focus indicators
    document.addEventListener('focusin', (event) => {
      const target = event.target as HTMLElement;
      if (target && this.preferences.focusIndicators) {
        target.classList.add('focus-visible');
        
        // Announce focused element for screen readers
        if (this.preferences.screenReaderEnabled) {
          const label = this.getElementLabel(target);
          if (label) {
            this.announce(`Focused on ${label}`, 'polite', 100);
          }
        }
      }
    });

    document.addEventListener('focusout', (event) => {
      const target = event.target as HTMLElement;
      if (target) {
        target.classList.remove('focus-visible');
      }
    });
  }

  private getFocusableElements(): NodeListOf<HTMLElement> {
    return document.querySelectorAll(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"]):not([disabled]), [role="button"]:not([disabled]), [role="link"]:not([disabled])'
    );
  }

  private focusNextElement(elements: NodeListOf<HTMLElement>, currentIndex: number): void {
    const nextIndex = currentIndex < elements.length - 1 ? currentIndex + 1 : 0;
    elements[nextIndex].focus();
  }

  private focusPreviousElement(elements: NodeListOf<HTMLElement>, currentIndex: number): void {
    const prevIndex = currentIndex > 0 ? currentIndex - 1 : elements.length - 1;
    elements[prevIndex].focus();
  }

  private focusFirstElement(elements: NodeListOf<HTMLElement>): void {
    if (elements.length > 0) {
      elements[0].focus();
    }
  }

  private focusLastElement(elements: NodeListOf<HTMLElement>): void {
    if (elements.length > 0) {
      elements[elements.length - 1].focus();
    }
  }

  private getElementLabel(element: HTMLElement): string {
    return (
      element.getAttribute('aria-label') ||
      element.getAttribute('title') ||
      element.textContent?.trim() ||
      element.tagName.toLowerCase()
    );
  }

  // High contrast mode enhancements
  enableHighContrastMode(): void {
    document.body.classList.add('high-contrast');
    this.updatePreference('highContrastMode', true);
    this.announce('High contrast mode enabled');
  }

  disableHighContrastMode(): void {
    document.body.classList.remove('high-contrast');
    this.updatePreference('highContrastMode', false);
    this.announce('High contrast mode disabled');
  }

  // Font size adjustment methods
  increaseFontSize(): void {
    const sizes: Array<AccessibilityPreferences['fontSize']> = ['small', 'medium', 'large', 'xlarge'];
    const currentIndex = sizes.indexOf(this.preferences.fontSize);
    if (currentIndex < sizes.length - 1) {
      this.updatePreference('fontSize', sizes[currentIndex + 1]);
      this.announce(`Font size increased to ${sizes[currentIndex + 1]}`);
    }
  }

  decreaseFontSize(): void {
    const sizes: Array<AccessibilityPreferences['fontSize']> = ['small', 'medium', 'large', 'xlarge'];
    const currentIndex = sizes.indexOf(this.preferences.fontSize);
    if (currentIndex > 0) {
      this.updatePreference('fontSize', sizes[currentIndex - 1]);
      this.announce(`Font size decreased to ${sizes[currentIndex - 1]}`);
    }
  }

  // Screen reader specific enhancements
  announcePageChange(pageName: string): void {
    this.announce(`Navigated to ${pageName} page`, 'assertive');
  }

  announceError(errorMessage: string): void {
    this.announce(`Error: ${errorMessage}`, 'assertive');
  }

  announceSuccess(successMessage: string): void {
    this.announce(`Success: ${successMessage}`, 'polite');
  }

  // Keyboard shortcuts help
  showKeyboardShortcuts(): void {
    const shortcuts = [
      'Alt + 1-9: Quick navigation to menu items',
      'Alt + A: Open accessibility settings',
      'Alt + S: Focus search/chat input',
      'Alt + M: Focus main content area',
      'Alt + N: Focus navigation sidebar',
      'Alt + H: Show this help',
      'Ctrl + Plus/Minus: Increase/decrease font size',
      'Ctrl + Alt + C: Toggle high contrast mode',
      'Ctrl + Alt + M: Toggle reduced motion',
      'Arrow keys: Navigate between elements',
      'Home/End: Jump to first/last element',
      'Escape: Close modals and dropdowns',
      'Tab: Navigate forward',
      'Shift + Tab: Navigate backward',
      'Enter/Space: Activate buttons and links'
    ];
    
    // Create a more accessible help dialog
    this.createKeyboardShortcutsDialog(shortcuts);
  }

  private createKeyboardShortcutsDialog(shortcuts: string[]): void {
    // Remove existing dialog if present
    const existingDialog = document.getElementById('keyboard-shortcuts-dialog');
    if (existingDialog) {
      existingDialog.remove();
    }

    const dialog = document.createElement('div');
    dialog.id = 'keyboard-shortcuts-dialog';
    dialog.setAttribute('role', 'dialog');
    dialog.setAttribute('aria-modal', 'true');
    dialog.setAttribute('aria-labelledby', 'shortcuts-title');
    dialog.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';

    dialog.innerHTML = `
      <div class="bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div class="p-6 border-b border-gray-700 flex items-center justify-between">
          <h2 id="shortcuts-title" class="text-xl font-semibold text-white">Keyboard Shortcuts</h2>
          <button id="close-shortcuts" class="p-2 hover:bg-gray-700 rounded-lg transition-colors focus-ring" aria-label="Close keyboard shortcuts dialog">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="p-6">
          <div class="space-y-3">
            ${shortcuts.map(shortcut => {
              const [keys, description] = shortcut.split(': ');
              return `
                <div class="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
                  <span class="text-gray-300">${description}</span>
                  <kbd class="px-2 py-1 bg-gray-600 rounded text-sm font-mono text-white">${keys}</kbd>
                </div>
              `;
            }).join('')}
          </div>
          <div class="mt-6 p-4 bg-blue-900/20 border border-blue-700 rounded-lg">
            <p class="text-blue-300 text-sm">
              <strong>Tip:</strong> These shortcuts work from anywhere in the application. 
              Press Alt + H anytime to show this help dialog.
            </p>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(dialog);

    // Set up event handlers
    const closeButton = dialog.querySelector('#close-shortcuts') as HTMLElement;
    const closeDialog = () => {
      dialog.remove();
      this.announce('Keyboard shortcuts dialog closed', 'polite');
    };

    closeButton.addEventListener('click', closeDialog);
    dialog.addEventListener('click', (e) => {
      if (e.target === dialog) closeDialog();
    });
    dialog.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeDialog();
    });

    // Focus the close button
    closeButton.focus();
    this.announce('Keyboard shortcuts dialog opened. Press Escape to close.', 'assertive');
  }

  // Semantic HTML structure validation and enhancement
  validateSemanticStructure(): {
    issues: Array<{
      type: string;
      element: string;
      message: string;
      severity: 'error' | 'warning' | 'info';
    }>;
    score: number;
  } {
    const issues: Array<{
      type: string;
      element: string;
      message: string;
      severity: 'error' | 'warning' | 'info';
    }> = [];

    // Check for main landmark
    const mainElements = document.querySelectorAll('main, [role="main"]');
    if (mainElements.length === 0) {
      issues.push({
        type: 'landmark',
        element: 'main',
        message: 'Page should have a main landmark',
        severity: 'error'
      });
    } else if (mainElements.length > 1) {
      issues.push({
        type: 'landmark',
        element: 'main',
        message: 'Page should have only one main landmark',
        severity: 'warning'
      });
    }

    // Check for navigation landmark
    const navElements = document.querySelectorAll('nav, [role="navigation"]');
    if (navElements.length === 0) {
      issues.push({
        type: 'landmark',
        element: 'nav',
        message: 'Page should have navigation landmarks',
        severity: 'warning'
      });
    }

    // Check heading structure
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    const headingLevels = Array.from(headings).map(h => parseInt(h.tagName[1]));
    
    if (headingLevels.length > 0) {
      // Check if starts with h1
      if (headingLevels[0] !== 1) {
        issues.push({
          type: 'heading',
          element: 'h1',
          message: 'Page should start with h1',
          severity: 'error'
        });
      }

      // Check for skipped levels
      for (let i = 1; i < headingLevels.length; i++) {
        if (headingLevels[i] > headingLevels[i-1] + 1) {
          issues.push({
            type: 'heading',
            element: `h${headingLevels[i]}`,
            message: `Heading level skipped from h${headingLevels[i-1]} to h${headingLevels[i]}`,
            severity: 'warning'
          });
        }
      }
    }

    // Check for images without alt text
    const images = document.querySelectorAll('img');
    images.forEach((img, index) => {
      const alt = img.getAttribute('alt');
      if (alt === null) {
        issues.push({
          type: 'image',
          element: `img[${index}]`,
          message: 'Image missing alt attribute',
          severity: 'error'
        });
      } else if (alt === '' && !this.isDecorativeImage(img)) {
        issues.push({
          type: 'image',
          element: `img[${index}]`,
          message: 'Non-decorative image has empty alt text',
          severity: 'warning'
        });
      }
    });

    // Check for form inputs without labels
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach((input, index) => {
      const id = input.getAttribute('id');
      const ariaLabel = input.getAttribute('aria-label');
      const ariaLabelledby = input.getAttribute('aria-labelledby');
      
      let hasLabel = false;
      if (id) {
        const label = document.querySelector(`label[for="${id}"]`);
        if (label) hasLabel = true;
      }
      
      if (!hasLabel && !ariaLabel && !ariaLabelledby) {
        issues.push({
          type: 'form',
          element: `${input.tagName.toLowerCase()}[${index}]`,
          message: 'Form control missing accessible label',
          severity: 'error'
        });
      }
    });

    // Check for buttons without accessible names
    const buttons = document.querySelectorAll('button, [role="button"]');
    buttons.forEach((button, index) => {
      const ariaLabel = button.getAttribute('aria-label');
      const ariaLabelledby = button.getAttribute('aria-labelledby');
      const textContent = button.textContent?.trim();
      
      if (!ariaLabel && !ariaLabelledby && !textContent) {
        issues.push({
          type: 'button',
          element: `button[${index}]`,
          message: 'Button missing accessible name',
          severity: 'error'
        });
      }
    });

    // Calculate score based on issues
    const errorCount = issues.filter(i => i.severity === 'error').length;
    const warningCount = issues.filter(i => i.severity === 'warning').length;
    const maxScore = 100;
    const score = Math.max(0, maxScore - (errorCount * 10) - (warningCount * 5));

    return { issues, score };
  }

  private isDecorativeImage(img: HTMLImageElement): boolean {
    // Check if image is likely decorative based on context
    const parent = img.parentElement;
    if (!parent) return false;
    
    const parentClasses = parent.className.toLowerCase();
    const imgClasses = img.className.toLowerCase();
    
    const decorativeKeywords = ['decoration', 'background', 'icon', 'avatar', 'logo'];
    return decorativeKeywords.some(keyword => 
      parentClasses.includes(keyword) || imgClasses.includes(keyword)
    );
  }

  // Enhance semantic structure
  enhanceSemanticStructure(): void {
    // Add missing landmarks
    this.addMissingLandmarks();
    
    // Enhance form accessibility
    this.enhanceFormAccessibility();
    
    // Enhance button accessibility
    this.enhanceButtonAccessibility();
    
    // Add skip links if missing
    this.ensureSkipLinks();
    
    // Enhance table accessibility
    this.enhanceTableAccessibility();
    
    this.announce('Semantic structure enhanced', 'polite');
  }

  private addMissingLandmarks(): void {
    // Add main landmark if missing
    const mainElements = document.querySelectorAll('main, [role="main"]');
    if (mainElements.length === 0) {
      const contentArea = document.querySelector('#main-content, .main-content, .content');
      if (contentArea && !contentArea.hasAttribute('role')) {
        contentArea.setAttribute('role', 'main');
        contentArea.setAttribute('aria-label', 'Main content');
      }
    }

    // Add navigation landmarks
    const navElements = document.querySelectorAll('nav');
    navElements.forEach((nav, index) => {
      if (!nav.hasAttribute('aria-label') && !nav.hasAttribute('aria-labelledby')) {
        nav.setAttribute('aria-label', `Navigation ${index + 1}`);
      }
    });

    // Add banner landmark to header if missing
    const headers = document.querySelectorAll('header');
    headers.forEach(header => {
      if (!header.hasAttribute('role')) {
        header.setAttribute('role', 'banner');
      }
    });

    // Add contentinfo landmark to footer if missing
    const footers = document.querySelectorAll('footer');
    footers.forEach(footer => {
      if (!footer.hasAttribute('role')) {
        footer.setAttribute('role', 'contentinfo');
      }
    });
  }

  private enhanceFormAccessibility(): void {
    const inputs = document.querySelectorAll('input, select, textarea');
    
    inputs.forEach((input, index) => {
      const element = input as HTMLInputElement;
      
      // Add IDs if missing
      if (!element.id) {
        element.id = `form-input-${index}`;
      }

      // Check for associated label
      const label = document.querySelector(`label[for="${element.id}"]`);
      if (!label && !element.getAttribute('aria-label')) {
        // Try to find nearby text that could serve as a label
        const placeholder = element.getAttribute('placeholder');
        const name = element.getAttribute('name');
        
        if (placeholder) {
          element.setAttribute('aria-label', placeholder);
        } else if (name) {
          element.setAttribute('aria-label', name.replace(/[-_]/g, ' '));
        } else {
          element.setAttribute('aria-label', `Input field ${index + 1}`);
        }
      }

      // Add required indication
      if (element.hasAttribute('required') && !element.hasAttribute('aria-required')) {
        element.setAttribute('aria-required', 'true');
      }

      // Add invalid indication for validation
      if (element.validity && !element.validity.valid && !element.hasAttribute('aria-invalid')) {
        element.setAttribute('aria-invalid', 'true');
      }
    });
  }

  private enhanceButtonAccessibility(): void {
    const buttons = document.querySelectorAll('button, [role="button"]');
    
    buttons.forEach((button, index) => {
      const element = button as HTMLElement;
      const textContent = element.textContent?.trim();
      const ariaLabel = element.getAttribute('aria-label');
      
      // Add accessible name if missing
      if (!textContent && !ariaLabel) {
        // Try to infer purpose from context
        const icon = element.querySelector('svg, i, .icon');
        const parent = element.parentElement;
        
        if (icon) {
          // Common icon patterns
          const iconClasses = icon.className.toLowerCase();
          if (iconClasses.includes('close') || iconClasses.includes('x')) {
            element.setAttribute('aria-label', 'Close');
          } else if (iconClasses.includes('menu') || iconClasses.includes('hamburger')) {
            element.setAttribute('aria-label', 'Menu');
          } else if (iconClasses.includes('search')) {
            element.setAttribute('aria-label', 'Search');
          } else {
            element.setAttribute('aria-label', `Button ${index + 1}`);
          }
        } else {
          element.setAttribute('aria-label', `Button ${index + 1}`);
        }
      }

      // Add button role if missing
      if (element.tagName !== 'BUTTON' && !element.hasAttribute('role')) {
        element.setAttribute('role', 'button');
      }

      // Add tabindex if missing for non-button elements
      if (element.tagName !== 'BUTTON' && !element.hasAttribute('tabindex')) {
        element.setAttribute('tabindex', '0');
      }
    });
  }

  private ensureSkipLinks(): void {
    const existingSkipLinks = document.querySelector('.skip-links');
    if (existingSkipLinks) return;

    const skipLinks = document.createElement('div');
    skipLinks.className = 'skip-links';
    skipLinks.setAttribute('role', 'navigation');
    skipLinks.setAttribute('aria-label', 'Skip navigation');

    const skipLinksData = [
      { href: '#main-content', text: 'Skip to main content' },
      { href: '#main-sidebar', text: 'Skip to navigation' },
      { href: '#chat-input', text: 'Skip to search' }
    ];

    skipLinksData.forEach(linkData => {
      const link = document.createElement('a');
      link.href = linkData.href;
      link.className = 'skip-link';
      link.textContent = linkData.text;
      
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const target = document.querySelector(linkData.href);
        if (target) {
          (target as HTMLElement).focus();
          target.scrollIntoView({ behavior: 'smooth' });
          this.announce(`Skipped to ${linkData.text.toLowerCase()}`);
        }
      });
      
      skipLinks.appendChild(link);
    });

    document.body.insertBefore(skipLinks, document.body.firstChild);
  }

  private enhanceTableAccessibility(): void {
    const tables = document.querySelectorAll('table');
    
    tables.forEach((table, index) => {
      // Add table role if missing
      if (!table.hasAttribute('role')) {
        table.setAttribute('role', 'table');
      }

      // Add caption if missing
      if (!table.querySelector('caption') && !table.hasAttribute('aria-label')) {
        table.setAttribute('aria-label', `Data table ${index + 1}`);
      }

      // Enhance headers
      const headers = table.querySelectorAll('th');
      headers.forEach(header => {
        if (!header.hasAttribute('scope')) {
          // Determine scope based on position
          const row = header.closest('tr');
          const rowIndex = Array.from(table.querySelectorAll('tr')).indexOf(row!);
          const cellIndex = Array.from(row!.children).indexOf(header);
          
          if (rowIndex === 0) {
            header.setAttribute('scope', 'col');
          } else if (cellIndex === 0) {
            header.setAttribute('scope', 'row');
          }
        }
      });

      // Add row and column headers if missing
      const rows = table.querySelectorAll('tr');
      rows.forEach((row, rowIndex) => {
        const cells = row.querySelectorAll('td');
        cells.forEach((cell, cellIndex) => {
          // Add headers attribute if complex table
          if (headers.length > 0 && !cell.hasAttribute('headers')) {
            const columnHeader = table.querySelector(`th:nth-child(${cellIndex + 1})`);
            const rowHeader = row.querySelector('th');
            
            const headerIds: string[] = [];
            if (columnHeader?.id) headerIds.push(columnHeader.id);
            if (rowHeader?.id) headerIds.push(rowHeader.id);
            
            if (headerIds.length > 0) {
              cell.setAttribute('headers', headerIds.join(' '));
            }
          }
        });
      });
    });
  }
}

// Create and export singleton instance
export const accessibilityService = new AccessibilityService();

// Export types
export type { AccessibilityPreferences, AccessibilityAnnouncement };