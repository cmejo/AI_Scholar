/**
 * Authentication Storage Utilities
 * Handles persistent vs session-based authentication storage
 */

export interface AuthTokens {
  token: string;
  refreshToken: string;
  expiresAt?: string;
}

export class AuthStorage {
  private static readonly TOKEN_KEY = 'auth_token';
  private static readonly REFRESH_TOKEN_KEY = 'refresh_token';
  private static readonly REMEMBER_ME_KEY = 'remember_me';
  private static readonly EXPIRES_AT_KEY = 'auth_expires_at';

  /**
   * Store authentication tokens
   */
  static storeTokens(tokens: AuthTokens, rememberMe: boolean = false): void {
    const storage = rememberMe ? localStorage : sessionStorage;
    
    storage.setItem(this.TOKEN_KEY, tokens.token);
    storage.setItem(this.REFRESH_TOKEN_KEY, tokens.refreshToken);
    
    // Always store remember me preference in localStorage
    localStorage.setItem(this.REMEMBER_ME_KEY, rememberMe.toString());
    
    if (tokens.expiresAt) {
      storage.setItem(this.EXPIRES_AT_KEY, tokens.expiresAt);
    }
    
    console.log('AuthStorage: Tokens stored', {
      storage: rememberMe ? 'localStorage' : 'sessionStorage',
      rememberMe,
      hasToken: !!tokens.token,
      hasRefreshToken: !!tokens.refreshToken
    });
  }

  /**
   * Get stored authentication tokens
   */
  static getTokens(): AuthTokens | null {
    // Check localStorage first, then sessionStorage
    const token = localStorage.getItem(this.TOKEN_KEY) || sessionStorage.getItem(this.TOKEN_KEY);
    const refreshToken = localStorage.getItem(this.REFRESH_TOKEN_KEY) || sessionStorage.getItem(this.REFRESH_TOKEN_KEY);
    const expiresAt = localStorage.getItem(this.EXPIRES_AT_KEY) || sessionStorage.getItem(this.EXPIRES_AT_KEY);
    
    if (!token || !refreshToken) {
      return null;
    }
    
    return {
      token,
      refreshToken,
      expiresAt: expiresAt || undefined
    };
  }

  /**
   * Get remember me preference
   */
  static getRememberMe(): boolean {
    return localStorage.getItem(this.REMEMBER_ME_KEY) === 'true';
  }

  /**
   * Check if tokens are expired
   */
  static isTokenExpired(): boolean {
    const expiresAt = localStorage.getItem(this.EXPIRES_AT_KEY) || sessionStorage.getItem(this.EXPIRES_AT_KEY);
    
    if (!expiresAt) {
      return false; // If no expiry date, assume not expired
    }
    
    const expiryDate = new Date(expiresAt);
    const now = new Date();
    
    // Add 5 minute buffer before actual expiry
    const bufferTime = 5 * 60 * 1000; // 5 minutes in milliseconds
    return now.getTime() > (expiryDate.getTime() - bufferTime);
  }

  /**
   * Clear all authentication storage
   */
  static clearTokens(): void {
    // Clear from both storage types
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.REMEMBER_ME_KEY);
    localStorage.removeItem(this.EXPIRES_AT_KEY);
    
    sessionStorage.removeItem(this.TOKEN_KEY);
    sessionStorage.removeItem(this.REFRESH_TOKEN_KEY);
    sessionStorage.removeItem(this.EXPIRES_AT_KEY);
    
    console.log('AuthStorage: All tokens cleared');
  }

  /**
   * Get the current token (for API requests)
   */
  static getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY) || sessionStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * Get the current refresh token
   */
  static getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY) || sessionStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  /**
   * Check if user has valid authentication
   */
  static hasValidAuth(): boolean {
    const tokens = this.getTokens();
    return !!(tokens?.token && tokens?.refreshToken) && !this.isTokenExpired();
  }

  /**
   * Get storage type being used
   */
  static getStorageType(): 'localStorage' | 'sessionStorage' | null {
    if (localStorage.getItem(this.TOKEN_KEY)) {
      return 'localStorage';
    } else if (sessionStorage.getItem(this.TOKEN_KEY)) {
      return 'sessionStorage';
    }
    return null;
  }
}

/**
 * Auto-refresh token utility
 */
export class TokenRefreshManager {
  private static refreshTimer: NodeJS.Timeout | null = null;
  private static refreshCallback: (() => Promise<void>) | null = null;

  /**
   * Set up automatic token refresh
   */
  static setupAutoRefresh(refreshCallback: () => Promise<void>): void {
    this.refreshCallback = refreshCallback;
    this.scheduleNextRefresh();
  }

  /**
   * Clear automatic token refresh
   */
  static clearAutoRefresh(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
    this.refreshCallback = null;
  }

  /**
   * Schedule the next token refresh
   */
  private static scheduleNextRefresh(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    const tokens = AuthStorage.getTokens();
    if (!tokens?.expiresAt || !this.refreshCallback) {
      return;
    }

    const expiryDate = new Date(tokens.expiresAt);
    const now = new Date();
    const timeUntilExpiry = expiryDate.getTime() - now.getTime();
    
    // Refresh 10 minutes before expiry, but at least 1 minute from now
    const refreshTime = Math.max(timeUntilExpiry - (10 * 60 * 1000), 60 * 1000);

    if (refreshTime > 0) {
      this.refreshTimer = setTimeout(async () => {
        try {
          await this.refreshCallback!();
          this.scheduleNextRefresh(); // Schedule next refresh after successful refresh
        } catch (error) {
          console.error('Auto token refresh failed:', error);
          // Don't schedule next refresh if this one failed
        }
      }, refreshTime);

      console.log('TokenRefreshManager: Next refresh scheduled in', Math.round(refreshTime / 1000 / 60), 'minutes');
    }
  }

  /**
   * Force immediate token refresh
   */
  static async forceRefresh(): Promise<void> {
    if (this.refreshCallback) {
      await this.refreshCallback();
      this.scheduleNextRefresh();
    }
  }
}