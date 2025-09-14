// Mobile Optimization Utilities for Phase 7

interface TouchGesture {
  type: 'tap' | 'swipe' | 'pinch' | 'long-press';
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  duration: number;
  distance: number;
}

interface MobileOptimizationConfig {
  enableTouchGestures: boolean;
  enableHapticFeedback: boolean;
  enableSwipeNavigation: boolean;
  enablePullToRefresh: boolean;
  optimizeScrolling: boolean;
  enableVirtualKeyboard: boolean;
  touchTargetSize: number; // Minimum 44px for accessibility
}

class MobileOptimizer {
  private static instance: MobileOptimizer;
  private config: MobileOptimizationConfig;
  private touchStartTime: number = 0;
  private touchStartPos: { x: number; y: number } = { x: 0, y: 0 };
  private isScrolling: boolean = false;
  private pullToRefreshThreshold: number = 100;

  private constructor() {
    this.config = {
      enableTouchGestures: true,
      enableHapticFeedback: true,
      enableSwipeNavigation: true,
      enablePullToRefresh: true,
      optimizeScrolling: true,
      enableVirtualKeyboard: true,
      touchTargetSize: 44
    };

    this.initializeMobileOptimizations();
  }

  public static getInstance(): MobileOptimizer {
    if (!MobileOptimizer.instance) {
      MobileOptimizer.instance = new MobileOptimizer();
    }
    return MobileOptimizer.instance;
  }

  private initializeMobileOptimizations(): void {
    if (this.isMobileDevice()) {
      this.setupTouchGestures();
      this.optimizeViewport();
      this.setupVirtualKeyboardHandling();
      this.optimizeScrollPerformance();
      this.setupPullToRefresh();
      this.enhanceTouchTargets();
    }
  }

  private isMobileDevice(): boolean {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
           window.innerWidth <= 768;
  }

  private setupTouchGestures(): void {
    if (!this.config.enableTouchGestures) return;

    let touchStartX = 0;
    let touchStartY = 0;
    let touchStartTime = 0;

    document.addEventListener('touchstart', (e) => {
      const touch = e.touches[0];
      touchStartX = touch.clientX;
      touchStartY = touch.clientY;
      touchStartTime = Date.now();
      this.touchStartPos = { x: touchStartX, y: touchStartY };
      this.touchStartTime = touchStartTime;
    }, { passive: true });

    document.addEventListener('touchmove', (e) => {
      // Detect if user is scrolling
      const touch = e.touches[0];
      const deltaY = Math.abs(touch.clientY - touchStartY);
      const deltaX = Math.abs(touch.clientX - touchStartX);
      
      if (deltaY > deltaX && deltaY > 10) {
        this.isScrolling = true;
      }
    }, { passive: true });

    document.addEventListener('touchend', (e) => {
      const touch = e.changedTouches[0];
      const touchEndX = touch.clientX;
      const touchEndY = touch.clientY;
      const touchEndTime = Date.now();
      
      const gesture = this.analyzeGesture({
        startX: touchStartX,
        startY: touchStartY,
        endX: touchEndX,
        endY: touchEndY,
        duration: touchEndTime - touchStartTime,
        distance: Math.sqrt(
          Math.pow(touchEndX - touchStartX, 2) + 
          Math.pow(touchEndY - touchStartY, 2)
        )
      });

      this.handleGesture(gesture);
      this.isScrolling = false;
    }, { passive: true });
  }

  private analyzeGesture(touch: Omit<TouchGesture, 'type'>): TouchGesture {
    const { startX, startY, endX, endY, duration, distance } = touch;
    
    // Long press detection
    if (duration > 500 && distance < 10) {
      return { ...touch, type: 'long-press' };
    }
    
    // Swipe detection
    if (distance > 50 && duration < 300) {
      return { ...touch, type: 'swipe' };
    }
    
    // Pinch detection (would need multi-touch)
    if (distance > 100 && duration > 200) {
      return { ...touch, type: 'pinch' };
    }
    
    // Default to tap
    return { ...touch, type: 'tap' };
  }

  private handleGesture(gesture: TouchGesture): void {
    switch (gesture.type) {
      case 'swipe':
        this.handleSwipe(gesture);
        break;
      case 'long-press':
        this.handleLongPress(gesture);
        break;
      case 'tap':
        this.handleTap(gesture);
        break;
      case 'pinch':
        this.handlePinch(gesture);
        break;
    }
  }

  private handleSwipe(gesture: TouchGesture): void {
    if (!this.config.enableSwipeNavigation || this.isScrolling) return;

    const deltaX = gesture.endX - gesture.startX;
    const deltaY = gesture.endY - gesture.startY;
    
    // Horizontal swipe for navigation
    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      if (deltaX > 50) {
        // Swipe right - go back or open sidebar
        this.triggerHapticFeedback('light');
        this.dispatchCustomEvent('swipe-right', { gesture });
      } else if (deltaX < -50) {
        // Swipe left - go forward or close sidebar
        this.triggerHapticFeedback('light');
        this.dispatchCustomEvent('swipe-left', { gesture });
      }
    }
    
    // Vertical swipe
    if (Math.abs(deltaY) > Math.abs(deltaX)) {
      if (deltaY > 50) {
        // Swipe down - refresh or show notifications
        this.dispatchCustomEvent('swipe-down', { gesture });
      } else if (deltaY < -50) {
        // Swipe up - hide keyboard or show menu
        this.dispatchCustomEvent('swipe-up', { gesture });
      }
    }
  }

  private handleLongPress(gesture: TouchGesture): void {
    this.triggerHapticFeedback('medium');
    this.dispatchCustomEvent('long-press', { gesture });
  }

  private handleTap(gesture: TouchGesture): void {
    // Enhanced tap handling for better touch response
    this.triggerHapticFeedback('light');
    
    // Check if tap target is large enough
    const element = document.elementFromPoint(gesture.endX, gesture.endY);
    if (element && this.isTouchTargetTooSmall(element)) {
      console.warn('Touch target too small:', element);
    }
  }

  private handlePinch(gesture: TouchGesture): void {
    // Handle pinch-to-zoom or other pinch gestures
    this.dispatchCustomEvent('pinch', { gesture });
  }

  private triggerHapticFeedback(intensity: 'light' | 'medium' | 'heavy'): void {
    if (!this.config.enableHapticFeedback) return;

    if ('vibrate' in navigator) {
      const patterns = {
        light: [10],
        medium: [20],
        heavy: [30]
      };
      navigator.vibrate(patterns[intensity]);
    }
  }

  private dispatchCustomEvent(eventName: string, detail: any): void {
    const event = new CustomEvent(eventName, { detail });
    document.dispatchEvent(event);
  }

  private optimizeViewport(): void {
    // Set optimal viewport for mobile
    let viewport = document.querySelector('meta[name="viewport"]');
    if (!viewport) {
      viewport = document.createElement('meta');
      viewport.setAttribute('name', 'viewport');
      document.head.appendChild(viewport);
    }
    
    viewport.setAttribute('content', 
      'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes, viewport-fit=cover'
    );

    // Add safe area insets for notched devices
    document.documentElement.style.setProperty('--safe-area-inset-top', 'env(safe-area-inset-top)');
    document.documentElement.style.setProperty('--safe-area-inset-right', 'env(safe-area-inset-right)');
    document.documentElement.style.setProperty('--safe-area-inset-bottom', 'env(safe-area-inset-bottom)');
    document.documentElement.style.setProperty('--safe-area-inset-left', 'env(safe-area-inset-left)');
  }

  private setupVirtualKeyboardHandling(): void {
    if (!this.config.enableVirtualKeyboard) return;

    // Handle virtual keyboard appearance
    if ('visualViewport' in window) {
      const viewport = window.visualViewport!;
      
      viewport.addEventListener('resize', () => {
        const keyboardHeight = window.innerHeight - viewport.height;
        document.documentElement.style.setProperty('--keyboard-height', `${keyboardHeight}px`);
        
        if (keyboardHeight > 150) {
          document.body.classList.add('keyboard-visible');
          this.dispatchCustomEvent('keyboard-show', { height: keyboardHeight });
        } else {
          document.body.classList.remove('keyboard-visible');
          this.dispatchCustomEvent('keyboard-hide', {});
        }
      });
    }

    // Focus management for inputs
    document.addEventListener('focusin', (e) => {
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
        // Scroll input into view when keyboard appears
        setTimeout(() => {
          target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 300);
      }
    });
  }

  private optimizeScrollPerformance(): void {
    if (!this.config.optimizeScrolling) return;

    // Enable momentum scrolling on iOS
    document.body.style.webkitOverflowScrolling = 'touch';
    
    // Optimize scroll performance
    let ticking = false;
    
    const optimizeScroll = () => {
      // Throttle scroll events
      if (!ticking) {
        requestAnimationFrame(() => {
          // Scroll optimizations here
          ticking = false;
        });
        ticking = true;
      }
    };

    document.addEventListener('scroll', optimizeScroll, { passive: true });
    
    // Prevent overscroll bounce on body
    document.body.addEventListener('touchmove', (e) => {
      if (e.target === document.body) {
        e.preventDefault();
      }
    }, { passive: false });
  }

  private setupPullToRefresh(): void {
    if (!this.config.enablePullToRefresh) return;

    let startY = 0;
    let currentY = 0;
    let isPulling = false;

    document.addEventListener('touchstart', (e) => {
      if (window.scrollY === 0) {
        startY = e.touches[0].clientY;
        isPulling = true;
      }
    }, { passive: true });

    document.addEventListener('touchmove', (e) => {
      if (!isPulling) return;

      currentY = e.touches[0].clientY;
      const pullDistance = currentY - startY;

      if (pullDistance > 0 && window.scrollY === 0) {
        // Show pull to refresh indicator
        const pullProgress = Math.min(pullDistance / this.pullToRefreshThreshold, 1);
        this.dispatchCustomEvent('pull-to-refresh-progress', { progress: pullProgress });
        
        if (pullDistance > this.pullToRefreshThreshold) {
          this.triggerHapticFeedback('medium');
        }
      }
    }, { passive: true });

    document.addEventListener('touchend', () => {
      if (isPulling) {
        const pullDistance = currentY - startY;
        
        if (pullDistance > this.pullToRefreshThreshold) {
          this.dispatchCustomEvent('pull-to-refresh-trigger', {});
          this.triggerHapticFeedback('heavy');
        }
        
        isPulling = false;
        this.dispatchCustomEvent('pull-to-refresh-end', {});
      }
    }, { passive: true });
  }

  private enhanceTouchTargets(): void {
    // Ensure all interactive elements meet minimum touch target size
    const interactiveElements = document.querySelectorAll(
      'button, a, input, select, textarea, [role="button"], [tabindex]'
    );

    interactiveElements.forEach((element) => {
      if (this.isTouchTargetTooSmall(element)) {
        (element as HTMLElement).style.minHeight = `${this.config.touchTargetSize}px`;
        (element as HTMLElement).style.minWidth = `${this.config.touchTargetSize}px`;
        (element as HTMLElement).style.padding = '8px';
      }
    });
  }

  private isTouchTargetTooSmall(element: Element): boolean {
    const rect = element.getBoundingClientRect();
    return rect.width < this.config.touchTargetSize || rect.height < this.config.touchTargetSize;
  }

  // Public methods
  public enableFeature(feature: keyof MobileOptimizationConfig, enabled: boolean): void {
    this.config[feature] = enabled as any;
  }

  public setTouchTargetSize(size: number): void {
    this.config.touchTargetSize = Math.max(44, size); // Minimum 44px for accessibility
  }

  public addMobileStyles(): void {
    const styles = `
      /* Mobile-specific optimizations */
      @media (max-width: 768px) {
        * {
          -webkit-tap-highlight-color: rgba(16, 185, 129, 0.2);
          -webkit-touch-callout: none;
          -webkit-user-select: none;
          user-select: none;
        }
        
        input, textarea, select {
          -webkit-user-select: text;
          user-select: text;
          font-size: 16px; /* Prevent zoom on iOS */
        }
        
        button, [role="button"] {
          min-height: ${this.config.touchTargetSize}px;
          min-width: ${this.config.touchTargetSize}px;
          touch-action: manipulation;
        }
        
        .keyboard-visible {
          padding-bottom: var(--keyboard-height, 0);
        }
        
        /* Safe area support */
        .safe-area-top {
          padding-top: var(--safe-area-inset-top, 0);
        }
        
        .safe-area-bottom {
          padding-bottom: var(--safe-area-inset-bottom, 0);
        }
        
        .safe-area-left {
          padding-left: var(--safe-area-inset-left, 0);
        }
        
        .safe-area-right {
          padding-right: var(--safe-area-inset-right, 0);
        }
        
        /* Smooth scrolling */
        * {
          -webkit-overflow-scrolling: touch;
          scroll-behavior: smooth;
        }
        
        /* Prevent overscroll */
        body {
          overscroll-behavior: none;
        }
        
        /* Optimize animations for mobile */
        * {
          will-change: auto;
        }
        
        .animate-on-scroll {
          will-change: transform, opacity;
        }
      }
      
      /* High DPI displays */
      @media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
        .high-dpi-image {
          image-rendering: -webkit-optimize-contrast;
          image-rendering: crisp-edges;
        }
      }
      
      /* Landscape orientation */
      @media (orientation: landscape) and (max-height: 500px) {
        .landscape-optimize {
          height: 100vh;
          height: 100dvh; /* Dynamic viewport height */
        }
      }
      
      /* Dark mode support */
      @media (prefers-color-scheme: dark) {
        :root {
          color-scheme: dark;
        }
      }
      
      /* Reduced motion support */
      @media (prefers-reduced-motion: reduce) {
        * {
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
          transition-duration: 0.01ms !important;
        }
      }
    `;

    const styleSheet = document.createElement('style');
    styleSheet.textContent = styles;
    document.head.appendChild(styleSheet);
  }

  public getDeviceInfo(): {
    isMobile: boolean;
    isTablet: boolean;
    isIOS: boolean;
    isAndroid: boolean;
    hasNotch: boolean;
    screenSize: { width: number; height: number };
    pixelRatio: number;
    orientation: 'portrait' | 'landscape';
  } {
    const userAgent = navigator.userAgent;
    const isIOS = /iPad|iPhone|iPod/.test(userAgent);
    const isAndroid = /Android/.test(userAgent);
    const isMobile = this.isMobileDevice();
    const isTablet = /(iPad|tablet|playbook|silk)|(android(?!.*mobile))/i.test(userAgent);
    
    // Detect notch (simplified)
    const hasNotch = isIOS && window.screen.height >= 812;
    
    return {
      isMobile,
      isTablet,
      isIOS,
      isAndroid,
      hasNotch,
      screenSize: {
        width: window.screen.width,
        height: window.screen.height
      },
      pixelRatio: window.devicePixelRatio || 1,
      orientation: window.innerHeight > window.innerWidth ? 'portrait' : 'landscape'
    };
  }

  public cleanup(): void {
    // Remove event listeners and clean up
    document.removeEventListener('touchstart', () => {});
    document.removeEventListener('touchmove', () => {});
    document.removeEventListener('touchend', () => {});
  }
}

// Export singleton instance
export const mobileOptimizer = MobileOptimizer.getInstance();

// Initialize mobile optimizations
export const initializeMobileOptimizations = (): void => {
  const optimizer = mobileOptimizer;
  
  // Add mobile-specific styles
  optimizer.addMobileStyles();
  
  // Log device info in development
  if (window.location.hostname === 'localhost') {
    console.log('Mobile Device Info:', optimizer.getDeviceInfo());
  }
};

// Utility functions
export const isTouchDevice = (): boolean => {
  return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
};

export const getViewportSize = (): { width: number; height: number } => {
  return {
    width: Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0),
    height: Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0)
  };
};

export const isLandscape = (): boolean => {
  const viewport = getViewportSize();
  return viewport.width > viewport.height;
};

export const getScreenOrientation = (): string => {
  if ('orientation' in screen) {
    return (screen.orientation as any).type;
  }
  return isLandscape() ? 'landscape-primary' : 'portrait-primary';
};