// API Service for backend integration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

class ApiService {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.token = localStorage.getItem('auth_token');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        ...options.headers,
      };

      if (this.token) {
        headers.Authorization = `Bearer ${this.token}`;
      }

      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.detail || data.message || 'Request failed',
        };
      }

      return {
        success: true,
        data,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  // Authentication APIs
  async login(email: string, password: string): Promise<ApiResponse<{ token: string; user: any }>> {
    const response = await this.request<{ access_token: string; user: any }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    if (response.success && response.data) {
      this.token = response.data.access_token;
      localStorage.setItem('auth_token', this.token);
      return {
        success: true,
        data: {
          token: response.data.access_token,
          user: response.data.user,
        },
      };
    }

    return response;
  }

  async register(userData: {
    email: string;
    password: string;
    username: string;
  }): Promise<ApiResponse<{ user: any }>> {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async logout(): Promise<ApiResponse> {
    const response = await this.request('/auth/logout', {
      method: 'POST',
    });
    
    this.token = null;
    localStorage.removeItem('auth_token');
    return response;
  }

  async getCurrentUser(): Promise<ApiResponse<any>> {
    return this.request('/auth/me');
  }

  // Chat/RAG APIs
  async sendChatMessage(message: string, context?: any): Promise<ApiResponse<{
    response: string;
    sources?: any[];
    reasoning?: string;
  }>> {
    return this.request('/chat/message', {
      method: 'POST',
      body: JSON.stringify({ message, context }),
    });
  }

  async getChatHistory(limit: number = 50): Promise<ApiResponse<any[]>> {
    return this.request(`/chat/history?limit=${limit}`);
  }

  // Document Processing APIs
  async uploadDocument(file: File): Promise<ApiResponse<{
    document_id: string;
    filename: string;
    status: string;
  }>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request('/documents/upload', {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set Content-Type for FormData
    });
  }

  async getDocuments(): Promise<ApiResponse<any[]>> {
    return this.request('/documents');
  }

  async deleteDocument(documentId: string): Promise<ApiResponse> {
    return this.request(`/documents/${documentId}`, {
      method: 'DELETE',
    });
  }

  async searchDocuments(query: string): Promise<ApiResponse<{
    results: any[];
    total: number;
  }>> {
    return this.request('/documents/search', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  }

  // Analytics APIs
  async getAnalytics(timeRange: string = '7d'): Promise<ApiResponse<{
    queries: number;
    users: number;
    documents: number;
    performance: any;
  }>> {
    return this.request(`/analytics?range=${timeRange}`);
  }

  async logUserAction(action: string, metadata?: any): Promise<ApiResponse> {
    return this.request('/analytics/action', {
      method: 'POST',
      body: JSON.stringify({ action, metadata, timestamp: new Date().toISOString() }),
    });
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string; timestamp: string }>> {
    return this.request('/health');
  }

  // Set authentication token
  setToken(token: string) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  // Clear authentication token
  clearToken() {
    this.token = null;
    localStorage.removeItem('auth_token');
  }
}

export const apiService = new ApiService();
export default apiService;