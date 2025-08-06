import { useState, useEffect } from 'react';

interface MobileDetectionState {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  orientation: 'portrait' | 'landscape';
  screenSize: 'small' | 'medium' | 'large' | 'xlarge';
  touchSupported: boolean;
  devicePixelRatio: number;
}

export const useMobileDetection = (): MobileDetectionState => {
  const [state, setState] = useState<MobileDetectionState>(() => {
    // Initial state based on window properties
    if (typeof window === 'undefined') {
      return {
        isMobile: false,
        isTablet: false,
        isDesktop: true,
        orientation: 'landscape',
        screenSize: 'large',
        touchSupported: false,
        devicePixelRatio: 1
      };
    }

    return getDeviceInfo();
  });

  function getDeviceInfo(): MobileDetectionState {
    const width = window.innerWidth;
    const height = window.innerHeight;
    const userAgent = navigator.userAgent.toLowerCase();
    const touchSupported = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    const devicePixelRatio = window.devicePixelRatio || 1;

    // Detect device type based on screen size and user agent
    const isMobileUA = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent);
    const isTabletUA = /ipad|android(?!.*mobile)|tablet/i.test(userAgent);
    
    // Screen size breakpoints
    const isMobileSize = width < 768;
    const isTabletSize = width >= 768 && width < 1024;
    const isDesktopSize = width >= 1024;

    // Combine UA and size detection
    const isMobile = (isMobileUA && !isTabletUA) || (isMobileSize && touchSupported);
    const isTablet = isTabletUA || (isTabletSize && touchSupported && !isMobile);
    const isDesktop = !isMobile && !isTablet;

    // Determine orientation
    const orientation = height > width ? 'portrait' : 'landscape';

    // Determine screen size category
    let screenSize: 'small' | 'medium' | 'large' | 'xlarge';
    if (width < 640) {
      screenSize = 'small';
    } else if (width < 1024) {
      screenSize = 'medium';
    } else if (width < 1280) {
      screenSize = 'large';
    } else {
      screenSize = 'xlarge';
    }

    return {
      isMobile,
      isTablet,
      isDesktop,
      orientation,
      screenSize,
      touchSupported,
      devicePixelRatio
    };
  }

  useEffect(() => {
    const handleResize = () => {
      setState(getDeviceInfo());
    };

    const handleOrientationChange = () => {
      // Small delay to ensure dimensions are updated
      setTimeout(() => {
        setState(getDeviceInfo());
      }, 100);
    };

    // Listen for resize events
    window.addEventListener('resize', handleResize);
    
    // Listen for orientation changes
    window.addEventListener('orientationchange', handleOrientationChange);
    
    // Listen for device pixel ratio changes (zoom)
    const mediaQuery = window.matchMedia('(resolution: 1dppx)');
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleResize);
    } else {
      // Fallback for older browsers
      mediaQuery.addListener(handleResize);
    }

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleOrientationChange);
      
      if (mediaQuery.removeEventListener) {
        mediaQuery.removeEventListener('change', handleResize);
      } else {
        mediaQuery.removeListener(handleResize);
      }
    };
  }, []);

  return state;
};

// Utility functions for responsive design
export const useResponsiveValue = <T>(values: {
  mobile?: T;
  tablet?: T;
  desktop?: T;
  default: T;
}): T => {
  const { isMobile, isTablet } = useMobileDetection();
  
  if (isMobile && values.mobile !== undefined) {
    return values.mobile;
  }
  
  if (isTablet && values.tablet !== undefined) {
    return values.tablet;
  }
  
  if (values.desktop !== undefined) {
    return values.desktop;
  }
  
  return values.default;
};

// Hook for media queries
export const useMediaQuery = (query: string): boolean => {
  const [matches, setMatches] = useState(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);
    
    const handleChange = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
    } else {
      // Fallback for older browsers
      mediaQuery.addListener(handleChange);
    }

    return () => {
      if (mediaQuery.removeEventListener) {
        mediaQuery.removeEventListener('change', handleChange);
      } else {
        mediaQuery.removeListener(handleChange);
      }
    };
  }, [query]);

  return matches;
};