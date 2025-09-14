import { LoginCredentials, RegisterData, AuthResponse, User } from '../types/auth';
import { AuthStorage } from '../utils/authStorage';

class AuthService {
  private baseUrl = '/api/auth';

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    console.log('AuthService: Making login request to:', `${this.baseUrl}/login`);
    console.log('AuthService: Request credentials:', { email: credentials.email });
    
    const response = await fetch(`${this.baseUrl}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    console.log('AuthService: Response status:', response.status);
    console.log('AuthService: Response ok:', response.ok);

    if (!response.ok) {
      const error = await response.json();
      console.error('AuthService: Login error response:', error);
      throw new Error(error.message || 'Login failed');
    }

    const data = await response.json();
    console.log('AuthService: Login success response:', {
      hasAccessToken: !!data.access_token,
      hasRefreshToken: !!data.refresh_token,
      hasUser: !!data.user,
      userEmail: data.user?.email
    });
    
    // Map backend response to frontend format
    const authResponse = {
      user: data.user,
      token: data.access_token,
      refreshToken: data.refresh_token,
      expiresAt: new Date(Date.now() + (data.expires_in * 1000))
    };
    
    console.log('AuthService: Mapped response:', {
      hasToken: !!authResponse.token,
      hasRefreshToken: !!authResponse.refreshToken,
      hasUser: !!authResponse.user
    });
    
    return authResponse;
  }

  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await fetch(`${this.baseUrl}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Registration failed');
    }

    const responseData = await response.json();
    
    // Map backend response to frontend format
    return {
      user: responseData.user,
      token: responseData.access_token,
      refreshToken: responseData.refresh_token,
      expiresAt: new Date(Date.now() + (responseData.expires_in * 1000))
    };
  }

  async logout(): Promise<void> {
    const token = this.getStoredToken();
    if (token) {
      try {
        await fetch(`${this.baseUrl}/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      } catch (error) {
        console.log('Logout API call failed, but clearing local storage anyway:', error);
      }
    }
  }

  // Helper method to get token from storage
  private getStoredToken(): string | null {
    return AuthStorage.getToken();
  }

  // Helper method to get refresh token from storage
  private getStoredRefreshToken(): string | null {
    return AuthStorage.getRefreshToken();
  }

  async validateToken(token: string): Promise<User> {
    const response = await fetch(`${this.baseUrl}/validate`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Token validation failed');
    }

    const data = await response.json();
    return data.user;
  }

  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    const response = await fetch(`${this.baseUrl}/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      throw new Error('Token refresh failed');
    }

    const data = await response.json();
    
    // Map backend response to frontend format
    return {
      user: data.user,
      token: data.access_token,
      refreshToken: data.refresh_token,
      expiresAt: new Date(Date.now() + (data.expires_in * 1000))
    };
  }

  async updateProfile(userId: string, updates: Partial<User>): Promise<User> {
    const token = this.getStoredToken();
    console.log('UpdateProfile Debug:');
    console.log('- Token:', token ? `${token.substring(0, 20)}...` : 'Missing');
    console.log('- URL:', `${this.baseUrl}/profile`);
    console.log('- Updates:', updates);
    
    const response = await fetch(`${this.baseUrl}/profile`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(updates),
    });

    console.log('- Response status:', response.status);
    console.log('- Response URL:', response.url);

    if (!response.ok) {
      let errorMessage = 'Profile update failed';
      let responseText = '';
      try {
        responseText = await response.text();
        console.log('- Error response text:', responseText);
        const error = JSON.parse(responseText);
        errorMessage = error.message || error.detail || errorMessage;
      } catch (e) {
        console.log('- Failed to parse error as JSON:', e);
        console.log('- Raw response text:', responseText);
        errorMessage = responseText || response.statusText || errorMessage;
      }
      throw new Error(errorMessage);
    }

    const result = await response.json();
    console.log('- Success result:', result);
    return result;
  }

  async resetPassword(email: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/reset-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Password reset failed');
    }
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    const token = this.getStoredToken();
    const response = await fetch(`${this.baseUrl}/change-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ currentPassword, newPassword }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Password change failed');
    }
  }
}

export const authService = new AuthService();