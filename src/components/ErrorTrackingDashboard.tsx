import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  AlertTriangle, 
  Activity, 
  Users, 
  TrendingUp, 
  Clock, 
  CheckCircle,
  XCircle,
  AlertCircle,
  BarChart3,
  Settings,
  RefreshCw
} from 'lucide-react';

interface ErrorReport {
  id: string;
  error_type: string;
  error_message: string;
  severity: string;
  category: string;
  feature_name?: string;
  occurrence_count: number;
  resolved: boolean;
  first_seen: string;
  last_seen: string;
}

interface Incident {
  id: string;
  title: string;
  description: string;
  severity: string;
  status: string;
  category: string;
  affected_features: string[];
  created_at: string;
  updated_at: string;
}

interface UserFeedback {
  id: string;
  feedback_type: string;
  title: string;
  description: string;
  severity: string;
  status: string;
  created_at: string;
}

interface SystemHealth {
  overall_status: string;
  components: Record<string, {
    status: string;
    metrics: Record<string, any>;
    last_check: string;
  }>;
  last_updated: string;
}

interface Analytics {
  error_analytics: {
    total_errors: number;
    by_severity: Record<string, number>;
    by_category: Record<string, number>;
    by_feature: Record<string, number>;
  };
  incident_analytics: {
    total_incidents: number;
    by_severity: Record<string, number>;
    by_status: Record<string, number>;
    average_resolution_time_minutes: number;
  };
  health_analytics: {
    total_health_checks: number;
    overall_health_score: number;
  };
}

const ErrorTrackingDashboard: React.FC = () => {
  const [errors, setErrors] = useState<ErrorReport[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [feedback, setFeedback] = useState<UserFeedback[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadDashboardData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load all dashboard data in parallel
      const [
        errorsResponse,
        incidentsResponse,
        feedbackResponse,
        healthResponse,
        analyticsResponse
      ] = await Promise.all([
        fetch('/api/error-tracking/errors?limit=50'),
        fetch('/api/error-tracking/incidents?limit=20'),
        fetch('/api/error-tracking/feedback?limit=30'),
        fetch('/api/error-tracking/health'),
        fetch('/api/error-tracking/analytics?days=7')
      ]);

      if (errorsResponse.ok) {
        const errorsData = await errorsResponse.json();
        setErrors(errorsData);
      }

      if (incidentsResponse.ok) {
        const incidentsData = await incidentsResponse.json();
        setIncidents(incidentsData.incidents || []);
      }

      if (feedbackResponse.ok) {
        const feedbackData = await feedbackResponse.json();
        setFeedback(feedbackData.feedback || []);
      }

      if (healthResponse.ok) {
        const healthData = await healthResponse.json();
        setSystemHealth(healthData);
      }

      if (analyticsResponse.ok) {
        const analyticsData = await analyticsResponse.json();
        setAnalytics(analyticsData);
      }

    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy': return 'text-green-600';
      case 'degraded': return 'text-yellow-600';
      case 'unhealthy': return 'text-red-600';
      case 'resolved': return 'text-green-600';
      case 'open': return 'text-red-600';
      case 'investigating': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const resolveError = async (errorId: string) => {
    try {
      const response = await fetch(`/api/error-tracking/errors/${errorId}/resolve`, {
        method: 'PUT'
      });

      if (response.ok) {
        // Refresh data
        loadDashboardData();
      }
    } catch (error) {
      console.error('Error resolving error:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading dashboard...</span>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Error Tracking & Alerting Dashboard</h1>
        <Button onClick={loadDashboardData} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="errors">Errors</TabsTrigger>
          <TabsTrigger value="incidents">Incidents</TabsTrigger>
          <TabsTrigger value="health">System Health</TabsTrigger>
          <TabsTrigger value="feedback">User Feedback</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Errors</CardTitle>
                <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {analytics?.error_analytics.total_errors || 0}
                </div>
                <p className="text-xs text-muted-foreground">Last 7 days</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Open Incidents</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {incidents.filter(i => i.status === 'open').length}
                </div>
                <p className="text-xs text-muted-foreground">Requires attention</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">System Health</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${getStatusColor(systemHealth?.overall_status || 'unknown')}`}>
                  {systemHealth?.overall_status || 'Unknown'}
                </div>
                <p className="text-xs text-muted-foreground">
                  {analytics?.health_analytics.overall_health_score?.toFixed(1) || 0}% uptime
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">User Feedback</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{feedback.length}</div>
                <p className="text-xs text-muted-foreground">
                  {feedback.filter(f => f.feedback_type === 'bug_report').length} bug reports
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Recent Critical Issues */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <AlertCircle className="h-5 w-5 mr-2 text-red-500" />
                Critical Issues
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {errors
                  .filter(error => error.severity === 'critical' && !error.resolved)
                  .slice(0, 5)
                  .map(error => (
                    <div key={error.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex-1">
                        <div className="font-medium">{error.error_type}</div>
                        <div className="text-sm text-gray-600 truncate">{error.error_message}</div>
                        <div className="text-xs text-gray-500">
                          {error.feature_name && `${error.feature_name} • `}
                          {error.occurrence_count} occurrences • {formatTimeAgo(error.last_seen)}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge className={getSeverityColor(error.severity)}>
                          {error.severity}
                        </Badge>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => resolveError(error.id)}
                        >
                          Resolve
                        </Button>
                      </div>
                    </div>
                  ))}
                {errors.filter(error => error.severity === 'critical' && !error.resolved).length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-500" />
                    No critical issues at the moment
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="errors" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Errors</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {errors.slice(0, 20).map(error => (
                  <div key={error.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex-1">
                      <div className="font-medium">{error.error_type}</div>
                      <div className="text-sm text-gray-600 truncate">{error.error_message}</div>
                      <div className="text-xs text-gray-500">
                        {error.feature_name && `${error.feature_name} • `}
                        {error.category} • {error.occurrence_count} occurrences
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge className={getSeverityColor(error.severity)}>
                        {error.severity}
                      </Badge>
                      {error.resolved ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => resolveError(error.id)}
                        >
                          Resolve
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="incidents" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Incidents</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {incidents.map(incident => (
                  <div key={incident.id} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="font-medium">{incident.title}</div>
                      <div className="flex items-center space-x-2">
                        <Badge className={getSeverityColor(incident.severity)}>
                          {incident.severity}
                        </Badge>
                        <Badge variant="outline" className={getStatusColor(incident.status)}>
                          {incident.status}
                        </Badge>
                      </div>
                    </div>
                    <div className="text-sm text-gray-600 mb-2">{incident.description}</div>
                    <div className="text-xs text-gray-500">
                      {incident.affected_features.length > 0 && (
                        <>Affected: {incident.affected_features.join(', ')} • </>
                      )}
                      Created {formatTimeAgo(incident.created_at)}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="health" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>System Health Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <div className="font-medium">Overall Status</div>
                    <div className="text-sm text-gray-600">System-wide health</div>
                  </div>
                  <Badge className={`${getStatusColor(systemHealth?.overall_status || 'unknown')} font-medium`}>
                    {systemHealth?.overall_status || 'Unknown'}
                  </Badge>
                </div>

                {systemHealth?.components && Object.entries(systemHealth.components).map(([component, data]) => (
                  <div key={component} className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <div className="font-medium capitalize">{component.replace('_', ' ')}</div>
                      <div className="text-sm text-gray-600">
                        Last check: {formatTimeAgo(data.last_check)}
                      </div>
                    </div>
                    <Badge className={`${getStatusColor(data.status)} font-medium`}>
                      {data.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="feedback" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>User Feedback</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {feedback.map(item => (
                  <div key={item.id} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="font-medium">{item.title}</div>
                      <div className="flex items-center space-x-2">
                        <Badge variant="outline">
                          {item.feedback_type.replace('_', ' ')}
                        </Badge>
                        <Badge className={getSeverityColor(item.severity)}>
                          {item.severity}
                        </Badge>
                      </div>
                    </div>
                    <div className="text-sm text-gray-600 mb-2">{item.description}</div>
                    <div className="text-xs text-gray-500">
                      Status: {item.status} • {formatTimeAgo(item.created_at)}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ErrorTrackingDashboard;