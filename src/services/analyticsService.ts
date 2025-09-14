interface AnalyticsData {
  totalUsers: number;
  activeUsers: number;
  totalMessages: number;
  avgResponseTime: number;
  userGrowth: number;
  messageGrowth: number;
  dailyActivity: Array<{ date: string; users: number; messages: number }>;
  topContent: Array<{ title: string; views: number; engagement: number }>;
  performanceMetrics: {
    uptime: number;
    errorRate: number;
    avgLoadTime: number;
  };
}

class AnalyticsService {
  private baseUrl = '/api/analytics';

  async getAnalytics(timeRange: string): Promise<AnalyticsData> {
    try {
      const token = localStorage.getItem('auth_token');
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${this.baseUrl}/dashboard?range=${timeRange}`, {
        headers,
      });

      if (!response.ok) {
        // If unauthorized, try demo endpoint
        if (response.status === 401) {
          const demoResponse = await fetch(`${this.baseUrl}/demo/dashboard`);
          if (demoResponse.ok) {
            return demoResponse.json();
          }
        }
        throw new Error('Failed to fetch analytics data');
      }

      return response.json();
    } catch (error) {
      console.warn('Using mock analytics data:', error);
      // Return mock data as fallback
      return this.getMockAnalytics(timeRange);
    }
  }

  async exportAnalytics(timeRange: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/export?range=${timeRange}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to export analytics data');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analytics-${timeRange}-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export failed:', error);
      throw error;
    }
  }

  async getUserMetrics(userId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/users/${userId}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch user metrics');
    }

    return response.json();
  }

  async getContentMetrics(contentId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/content/${contentId}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch content metrics');
    }

    return response.json();
  }

  async trackEvent(event: string, properties: Record<string, any>): Promise<void> {
    try {
      await fetch(`${this.baseUrl}/events`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify({
          event,
          properties,
          timestamp: new Date().toISOString(),
        }),
      });
    } catch (error) {
      console.error('Failed to track event:', error);
    }
  }

  private getMockAnalytics(timeRange: string): AnalyticsData {
    const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90;
    
    // Generate mock daily activity data
    const dailyActivity = Array.from({ length: days }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (days - 1 - i));
      
      return {
        date: date.toISOString().split('T')[0],
        users: Math.floor(Math.random() * 200) + 50,
        messages: Math.floor(Math.random() * 500) + 100,
      };
    });

    // Generate mock content data
    const topContent = [
      { title: 'AI Research Paper Analysis', views: 1250, engagement: 85 },
      { title: 'Machine Learning Discussion', views: 980, engagement: 72 },
      { title: 'Data Science Workflow', views: 856, engagement: 68 },
      { title: 'Natural Language Processing', views: 743, engagement: 91 },
      { title: 'Computer Vision Tutorial', views: 692, engagement: 64 },
      { title: 'Deep Learning Concepts', views: 587, engagement: 78 },
      { title: 'Statistical Analysis Guide', views: 534, engagement: 56 },
      { title: 'Research Methodology', views: 489, engagement: 82 },
      { title: 'Academic Writing Tips', views: 445, engagement: 59 },
      { title: 'Citation Management', views: 398, engagement: 73 },
    ];

    const totalUsers = dailyActivity.reduce((sum, day) => sum + day.users, 0);
    const totalMessages = dailyActivity.reduce((sum, day) => sum + day.messages, 0);
    const activeUsers = Math.floor(totalUsers * 0.7);

    return {
      totalUsers: Math.floor(totalUsers / days * 30), // Extrapolate to monthly
      activeUsers: Math.floor(activeUsers / days * 30),
      totalMessages: Math.floor(totalMessages / days * 30),
      avgResponseTime: Math.floor(Math.random() * 100) + 150,
      userGrowth: Math.floor(Math.random() * 20) + 5,
      messageGrowth: Math.floor(Math.random() * 30) + 10,
      dailyActivity,
      topContent,
      performanceMetrics: {
        uptime: 99.8 + Math.random() * 0.2,
        errorRate: Math.random() * 0.3,
        avgLoadTime: Math.floor(Math.random() * 100) + 150,
      },
    };
  }
}

export const analyticsService = new AnalyticsService();