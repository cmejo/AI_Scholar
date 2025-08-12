/**
 * Tree shaking optimization utilities
 */

/**
 * Optimized imports for commonly used libraries
 * These imports help with tree shaking by importing only what's needed
 */

// Lucide React - Import only specific icons instead of the entire library
export {
    Activity, AlertCircle, AlertTriangle, ArrowLeft,
    ArrowRight,
    // Analytics icons
    BarChart3, Bell,
    // AI/Tech icons
    Brain,
    // Status icons
    Check, ChevronDown, ChevronLeft,
    ChevronRight,
    ChevronUp, Clock, Copy, Download, Edit, Eye,

    // Content icons
    FileText, Filter, Globe, Image, Info, Lightbulb, Loader2,
    // Navigation icons
    Menu,
    // Communication icons
    MessageCircle,
    Mic,
    MicOff, Music, Network, Quote, Save,
    // UI icons
    Search,
    // Action icons
    Send, Settings, Share,
    // System icons
    Shield, Target, Trash2, TrendingDown, TrendingUp, Upload, User, Video, Workflow, X, Zap
} from 'lucide-react';

/**
 * Utility functions that are tree-shakeable
 */

// Date utilities - only import what's needed
export const formatDate = (date: Date): string => {
  return date.toLocaleDateString();
};

export const formatTime = (date: Date): string => {
  return date.toLocaleTimeString();
};

export const formatDateTime = (date: Date): string => {
  return date.toLocaleString();
};

// String utilities
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
};

export const capitalizeFirst = (text: string): string => {
  return text.charAt(0).toUpperCase() + text.slice(1);
};

export const slugify = (text: string): string => {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
};

// Number utilities
export const formatBytes = (bytes: number): string => {
  const KB = 1024;
  const MB = KB * 1024;
  const GB = MB * 1024;

  if (bytes >= GB) {
    return `${(bytes / GB).toFixed(2)} GB`;
  } else if (bytes >= MB) {
    return `${(bytes / MB).toFixed(2)} MB`;
  } else if (bytes >= KB) {
    return `${(bytes / KB).toFixed(2)} KB`;
  } else {
    return `${bytes} B`;
  }
};

export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat().format(num);
};

export const formatPercentage = (value: number, total: number): string => {
  const percentage = (value / total) * 100;
  return `${percentage.toFixed(1)}%`;
};

// Array utilities
export const chunk = <T>(array: T[], size: number): T[][] => {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
};

export const unique = <T>(array: T[]): T[] => {
  return Array.from(new Set(array));
};

export const groupBy = <T, K extends keyof T>(
  array: T[],
  key: K
): Record<string, T[]> => {
  return array.reduce((groups, item) => {
    const group = String(item[key]);
    if (!groups[group]) {
      groups[group] = [];
    }
    groups[group].push(item);
    return groups;
  }, {} as Record<string, T[]>);
};

// Object utilities
export const pick = <T, K extends keyof T>(
  obj: T,
  keys: K[]
): Pick<T, K> => {
  const result = {} as Pick<T, K>;
  keys.forEach(key => {
    if (key in obj) {
      result[key] = obj[key];
    }
  });
  return result;
};

export const omit = <T, K extends keyof T>(
  obj: T,
  keys: K[]
): Omit<T, K> => {
  const result = { ...obj };
  keys.forEach(key => {
    delete result[key];
  });
  return result;
};

// Validation utilities
export const isEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const isUrl = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

export const isEmpty = (value: unknown): boolean => {
  if (value == null) return true;
  if (typeof value === 'string') return value.trim().length === 0;
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
};

// Performance utilities
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

// Color utilities
export const hexToRgb = (hex: string): { r: number; g: number; b: number } | null => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null;
};

export const rgbToHex = (r: number, g: number, b: number): string => {
  return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
};

// Storage utilities
export const safeLocalStorage = {
  getItem: (key: string): string | null => {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  },
  setItem: (key: string, value: string): boolean => {
    try {
      localStorage.setItem(key, value);
      return true;
    } catch {
      return false;
    }
  },
  removeItem: (key: string): boolean => {
    try {
      localStorage.removeItem(key);
      return true;
    } catch {
      return false;
    }
  },
};

export const safeSessionStorage = {
  getItem: (key: string): string | null => {
    try {
      return sessionStorage.getItem(key);
    } catch {
      return null;
    }
  },
  setItem: (key: string, value: string): boolean => {
    try {
      sessionStorage.setItem(key, value);
      return true;
    } catch {
      return false;
    }
  },
  removeItem: (key: string): boolean => {
    try {
      sessionStorage.removeItem(key);
      return true;
    } catch {
      return false;
    }
  },
};

/**
 * Tree shaking analyzer - helps identify unused exports
 */
export class TreeShakingAnalyzer {
  private usedExports = new Set<string>();
  private availableExports = new Set<string>();

  /**
   * Register an export as available
   */
  registerExport(exportName: string): void {
    this.availableExports.add(exportName);
  }

  /**
   * Register an export as used
   */
  markAsUsed(exportName: string): void {
    this.usedExports.add(exportName);
  }

  /**
   * Get unused exports
   */
  getUnusedExports(): string[] {
    return Array.from(this.availableExports).filter(
      exportName => !this.usedExports.has(exportName)
    );
  }

  /**
   * Get usage statistics
   */
  getUsageStats(): {
    totalExports: number;
    usedExports: number;
    unusedExports: number;
    usagePercentage: number;
  } {
    const totalExports = this.availableExports.size;
    const usedExports = this.usedExports.size;
    const unusedExports = totalExports - usedExports;
    const usagePercentage = totalExports > 0 ? (usedExports / totalExports) * 100 : 0;

    return {
      totalExports,
      usedExports,
      unusedExports,
      usagePercentage,
    };
  }

  /**
   * Generate tree shaking report
   */
  generateReport(): {
    summary: ReturnType<TreeShakingAnalyzer['getUsageStats']>;
    unusedExports: string[];
    recommendations: string[];
  } {
    const summary = this.getUsageStats();
    const unusedExports = this.getUnusedExports();
    const recommendations: string[] = [];

    if (summary.usagePercentage < 50) {
      recommendations.push('Consider splitting large utility modules into smaller, focused modules');
    }

    if (unusedExports.length > 10) {
      recommendations.push('Remove unused exports to improve tree shaking effectiveness');
    }

    if (summary.usagePercentage > 90) {
      recommendations.push('Good tree shaking! Most exports are being used');
    }

    return {
      summary,
      unusedExports,
      recommendations,
    };
  }
}

// Create singleton analyzer
export const treeShakingAnalyzer = new TreeShakingAnalyzer();

// Register all exports for analysis
if (process.env.NODE_ENV === 'development') {
  // Register utility functions
  treeShakingAnalyzer.registerExport('formatDate');
  treeShakingAnalyzer.registerExport('formatTime');
  treeShakingAnalyzer.registerExport('formatDateTime');
  treeShakingAnalyzer.registerExport('truncateText');
  treeShakingAnalyzer.registerExport('capitalizeFirst');
  treeShakingAnalyzer.registerExport('slugify');
  treeShakingAnalyzer.registerExport('formatBytes');
  treeShakingAnalyzer.registerExport('formatNumber');
  treeShakingAnalyzer.registerExport('formatPercentage');
  treeShakingAnalyzer.registerExport('chunk');
  treeShakingAnalyzer.registerExport('unique');
  treeShakingAnalyzer.registerExport('groupBy');
  treeShakingAnalyzer.registerExport('pick');
  treeShakingAnalyzer.registerExport('omit');
  treeShakingAnalyzer.registerExport('isEmail');
  treeShakingAnalyzer.registerExport('isUrl');
  treeShakingAnalyzer.registerExport('isEmpty');
  treeShakingAnalyzer.registerExport('debounce');
  treeShakingAnalyzer.registerExport('throttle');
  treeShakingAnalyzer.registerExport('hexToRgb');
  treeShakingAnalyzer.registerExport('rgbToHex');
  treeShakingAnalyzer.registerExport('safeLocalStorage');
  treeShakingAnalyzer.registerExport('safeSessionStorage');
}