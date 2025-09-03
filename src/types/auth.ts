// Enhanced Authentication and User Types
export interface User {
  id: string;
  name: string;
  email: string;
  role?: 'admin' | 'user' | 'researcher' | 'student';
  avatar?: string;
  preferences?: UserPreferences;
  createdAt?: Date;
  lastLoginAt?: Date;
  isActive?: boolean;
  permissions?: string[];
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  notifications: NotificationSettings;
  accessibility?: AccessibilitySettings;
}

export interface NotificationSettings {
  email: boolean;
  push: boolean;
  inApp: boolean;
  frequency: 'immediate' | 'daily' | 'weekly';
}

export interface AccessibilitySettings {
  highContrast: boolean;
  fontSize: 'small' | 'medium' | 'large';
  screenReader: boolean;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  token?: string;
  refreshToken?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegisterData extends LoginCredentials {
  name: string;
  confirmPassword: string;
  acceptTerms: boolean;
}

export interface AuthResponse {
  user: User;
  token: string;
  refreshToken: string;
  expiresAt: Date;
}

export interface AuthError {
  code: string;
  message: string;
  details?: Record<string, any>;
}
