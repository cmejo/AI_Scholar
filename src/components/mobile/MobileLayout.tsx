import React, { useEffect, useState } from 'react';
import { useMobileDetection } from '../../hooks/useMobileDetection';
import { MobileLayoutProps } from '../../types/ui';
import { MobileGestureHandler } from './MobileGestureHandler';
import { MobileHeader } from './MobileHeader';
import { MobileNavigation } from './MobileNavigation';

// MobileLayoutProps is now imported from types/ui.ts

export const MobileLayout: React.FC<MobileLayoutProps> = ({
  children,
  currentView,
  onViewChange,
  user,
  voiceEnabled,
  onToggleVoice
}) => {
  const [navOpen, setNavOpen] = useState(false);
  const [isKeyboardOpen, setIsKeyboardOpen] = useState(false);
  const { isMobile, isTablet, orientation } = useMobileDetection();

  // Handle keyboard visibility on mobile
  useEffect(() => {
    if (!isMobile) return;

    const handleResize = () => {
      const viewportHeight = window.visualViewport?.height || window.innerHeight;
      const windowHeight = window.screen.height;
      const keyboardThreshold = windowHeight * 0.75;
      
      setIsKeyboardOpen(viewportHeight < keyboardThreshold);
    };

    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', handleResize);
      return () => window.visualViewport?.removeEventListener('resize', handleResize);
    } else {
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
    }
  }, [isMobile]);

  // Close navigation when view changes
  useEffect(() => {
    setNavOpen(false);
  }, [currentView]);

  const handleSwipeGesture = (direction: 'left' | 'right' | 'up' | 'down') => {
    switch (direction) {
      case 'right':
        // Only open nav if swipe starts from left edge
        if (!navOpen && window.innerWidth > 0) {
          setNavOpen(true);
        }
        break;
      case 'left':
        // Close nav on left swipe
        if (navOpen) {
          setNavOpen(false);
        }
        break;
      case 'up':
        // Could implement pull-to-refresh or minimize keyboard
        if (isKeyboardOpen) {
          // Try to blur active input to hide keyboard
          const activeElement = document.activeElement as HTMLElement;
          if (activeElement && activeElement.blur) {
            activeElement.blur();
          }
        }
        break;
      case 'down':
        // Could implement pull-to-refresh
        break;
    }
  };

  return (
    <MobileGestureHandler onSwipe={handleSwipeGesture}>
      <div 
        className={`
          safe-area-inset bg-gray-900 text-white flex flex-col overflow-hidden
          ${orientation === 'landscape' ? 'landscape-mode' : 'portrait-mode'}
          ${isKeyboardOpen ? 'keyboard-open' : ''}
        `}
        role="application"
        aria-label="AI Scholar Mobile Application"
      >
        {/* Mobile Header */}
        <header role="banner">
          <MobileHeader
            currentView={currentView}
            user={user}
            onToggleNav={() => setNavOpen(!navOpen)}
            voiceEnabled={voiceEnabled}
            onToggleVoice={onToggleVoice}
            isNavOpen={navOpen}
          />
        </header>

        {/* Main Content Area */}
        <div className="flex-1 relative overflow-hidden">
          {/* Navigation Overlay */}
          <nav 
            role="navigation" 
            aria-label="Main navigation"
            id="navigation"
          >
            <MobileNavigation
              isOpen={navOpen}
              onClose={() => setNavOpen(false)}
              currentView={currentView}
              onViewChange={onViewChange}
              user={user}
            />
          </nav>

          {/* Content */}
          <main 
            className={`
              h-full transition-transform duration-300 ease-in-out overflow-hidden
              ${navOpen ? 'transform translate-x-80 scale-95 pointer-events-none' : 'transform translate-x-0'}
              ${isKeyboardOpen ? 'keyboard-adjusted' : ''}
            `}
            role="main"
            aria-label={`${currentView} content`}
            id="main-content"
          >
            <div className={`h-full overflow-auto scrollbar-hide ${navOpen ? 'pointer-events-none' : 'pointer-events-auto'}`}>
              {children}
            </div>
          </main>

          {/* Navigation Backdrop */}
          {navOpen && (
            <div
              className="absolute inset-0 bg-black bg-opacity-50 z-40 transition-opacity duration-300"
              onClick={() => setNavOpen(false)}
              style={{ transform: 'translateX(min(320px, 85vw))' }}
              aria-hidden="true"
            />
          )}
        </div>


      </div>
    </MobileGestureHandler>
  );
};