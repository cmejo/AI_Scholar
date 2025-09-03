// Authentication Service
// TODO: Implement proper authentication integration

import { User, AuthResponse, LoginCredentials, RegisterData } from '../types/auth';

class AuthService {
  private baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  
  async getCurrentUser(): Promise<User | null> {
    try {
      const token = localStorage.getItem('authToken');
      if (!token) {
        return null;
      }
      
      const response = await fetch(`${this.baseURL}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          // Token expired or invalid
          this.logout();
          return null;
        }
        throw new Error('Failed to get current user');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting current user:', error);
      return null;
    }
  }
  
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await fetch(`${this.baseURL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(credentials)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Login failed');
    }
    
    const authResponse: AuthResponse = await response.json();
    
    // Store tokens
    localStorage.setItem('authToken', authResponse.token);
    localStorage.setItem('refreshToken', authResponse.refreshToken);
    
    return authResponse;
  }
  
  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await fetch(`${this.baseURL}/api/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Registration failed');
    }
    
    const authResponse: AuthResponse = await response.json();
    
    // Store tokens
    localStorage.setItem('authToken', authResponse.token);
    localStorage.setItem('refreshToken', authResponse.refreshToken);
    
    return authResponse;
  }
  
  logout(): void {
    localStorage.removeItem('authToken');
    localStorage.removeItem('refreshToken');
    // Redirect to login page or update app state
    window.location.href = '/login';
  }
  
  async refreshToken(): Promise<string | null> {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        return null;
      }
      
      const response = await fetch(`${this.baseURL}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refreshToken })
      });
      
      if (!response.ok) {
        this.logout();
        return null;
      }
      
      const { token } = await response.json();
      localStorage.setItem('authToken', token);
      
      return token;
    } catch (error) {
      console.error('Error refreshing token:', error);
      this.logout();
      return null;
    }
  }
}

export const authService = new AuthService();
export default authService;
