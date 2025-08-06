import React, { useRef, useCallback, useEffect } from 'react';

interface MobileGestureHandlerProps {
  children: React.ReactNode;
  onSwipe?: (direction: 'left' | 'right' | 'up' | 'down') => void;
  onPinch?: (scale: number) => void;
  onTap?: (event: TouchEvent) => void;
  onLongPress?: (event: TouchEvent) => void;
  swipeThreshold?: number;
  pinchThreshold?: number;
  longPressDelay?: number;
}

export const MobileGestureHandler: React.FC<MobileGestureHandlerProps> = ({
  children,
  onSwipe,
  onPinch,
  onTap,
  onLongPress,
  swipeThreshold = 50,
  pinchThreshold = 0.1,
  longPressDelay = 500
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const touchStartRef = useRef<{ x: number; y: number; time: number } | null>(null);
  const touchEndRef = useRef<{ x: number; y: number; time: number } | null>(null);
  const initialDistanceRef = useRef<number>(0);
  const longPressTimerRef = useRef<number | null>(null);
  const isLongPressRef = useRef<boolean>(false);

  // Calculate distance between two touch points
  const getDistance = useCallback((touch1: Touch, touch2: Touch) => {
    const dx = touch1.clientX - touch2.clientX;
    const dy = touch1.clientY - touch2.clientY;
    return Math.sqrt(dx * dx + dy * dy);
  }, []);

  // Handle touch start
  const handleTouchStart = useCallback((event: TouchEvent) => {
    const touch = event.touches[0];
    const now = Date.now();

    touchStartRef.current = {
      x: touch.clientX,
      y: touch.clientY,
      time: now
    };

    isLongPressRef.current = false;

    // Handle multi-touch for pinch gestures
    if (event.touches.length === 2) {
      initialDistanceRef.current = getDistance(event.touches[0], event.touches[1]);
    }

    // Start long press timer
    if (onLongPress && event.touches.length === 1) {
      longPressTimerRef.current = window.setTimeout(() => {
        isLongPressRef.current = true;
        onLongPress(event);
      }, longPressDelay);
    }
  }, [onLongPress, longPressDelay, getDistance]);

  // Handle touch move
  const handleTouchMove = useCallback((event: TouchEvent) => {
    // Cancel long press if finger moves
    if (longPressTimerRef.current) {
      window.clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }

    // Handle pinch gestures
    if (onPinch && event.touches.length === 2) {
      const currentDistance = getDistance(event.touches[0], event.touches[1]);
      const scale = currentDistance / initialDistanceRef.current;
      
      if (Math.abs(scale - 1) > pinchThreshold) {
        onPinch(scale);
      }
    }
  }, [onPinch, getDistance, pinchThreshold]);

  // Handle touch end
  const handleTouchEnd = useCallback((event: TouchEvent) => {
    // Clear long press timer
    if (longPressTimerRef.current) {
      window.clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }

    // Don't process swipe if it was a long press
    if (isLongPressRef.current) {
      return;
    }

    const touch = event.changedTouches[0];
    const now = Date.now();

    touchEndRef.current = {
      x: touch.clientX,
      y: touch.clientY,
      time: now
    };

    if (!touchStartRef.current || !touchEndRef.current) {
      return;
    }

    const deltaX = touchEndRef.current.x - touchStartRef.current.x;
    const deltaY = touchEndRef.current.y - touchStartRef.current.y;
    const deltaTime = touchEndRef.current.time - touchStartRef.current.time;
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

    // Handle tap gesture
    if (onTap && distance < 10 && deltaTime < 300) {
      onTap(event);
      return;
    }

    // Handle swipe gestures
    if (onSwipe && distance > swipeThreshold && deltaTime < 1000) {
      const absDeltaX = Math.abs(deltaX);
      const absDeltaY = Math.abs(deltaY);

      if (absDeltaX > absDeltaY) {
        // Horizontal swipe
        onSwipe(deltaX > 0 ? 'right' : 'left');
      } else {
        // Vertical swipe
        onSwipe(deltaY > 0 ? 'down' : 'up');
      }
    }
  }, [onSwipe, onTap, swipeThreshold]);

  // Prevent default touch behaviors that might interfere
  const handleTouchCancel = useCallback(() => {
    if (longPressTimerRef.current) {
      window.clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }
  }, []);

  // Set up event listeners
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Add touch event listeners
    container.addEventListener('touchstart', handleTouchStart, { passive: false });
    container.addEventListener('touchmove', handleTouchMove, { passive: false });
    container.addEventListener('touchend', handleTouchEnd, { passive: false });
    container.addEventListener('touchcancel', handleTouchCancel, { passive: false });

    // Prevent default behaviors that might interfere with gestures
    const preventDefaults = (e: TouchEvent) => {
      // Allow scrolling but prevent other default behaviors
      if (e.touches.length > 1) {
        e.preventDefault();
      }
    };

    container.addEventListener('touchstart', preventDefaults, { passive: false });

    return () => {
      container.removeEventListener('touchstart', handleTouchStart);
      container.removeEventListener('touchmove', handleTouchMove);
      container.removeEventListener('touchend', handleTouchEnd);
      container.removeEventListener('touchcancel', handleTouchCancel);
      container.removeEventListener('touchstart', preventDefaults);
    };
  }, [handleTouchStart, handleTouchMove, handleTouchEnd, handleTouchCancel]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (longPressTimerRef.current) {
        window.clearTimeout(longPressTimerRef.current);
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="touch-manipulation select-none"
      style={{
        touchAction: 'pan-x pan-y', // Allow panning but prevent other touch actions
        WebkitTouchCallout: 'none', // Disable callout on iOS
        WebkitUserSelect: 'none', // Disable text selection on iOS
        userSelect: 'none' // Disable text selection
      }}
    >
      {children}
    </div>
  );
};