/**
 * Personalized Research Dashboard for AI Scholar
 * AI-powered insights and recommendations for researchers
 */
import {
    ArcElement,
    BarElement,
    CategoryScale,
    Chart as ChartJS,
    Legend,
    LinearScale,
    LineElement,
    PointElement,
    Title,
    Tooltip,
} from 'chart.js';
import { AlertCircle, BookOpen, CheckCircle, Lightbulb, Target, TrendingUp, Users } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { Doughnut, Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface ResearchInsight {
  id: string;
  type: 'trend' | 'opportunity' | 'recommendation' | 'alert';
  title: string;
  description: string;
  confidence: number;
  actionable: boolean;
  data?: any;
}

interface ResearchProgress {
  projectId: string;
  projectName: string;
  progress: number;
  milestones: {
    name: string;
    completed: boolean;
    dueDate: string;
  }[];
  nextSteps: string[];
  predictedCompletion: string;
}

interface ResearchMetrics {
  papersRead: number;
  citationsFound: number;
  collaborations: number;
  projectsActive: number;
  weeklyProgress: number[];
  topicDistribution: { [key: string]: number };
  impactScore: number;
}

interface PersonalizedDashboardProps {
  userId: string;
  userProfile: {
    name: string;
    interests: string[];
    currentProjects: string[];
    researchLevel: 'undergraduate' | 'graduate' | 'postdoc' | 'faculty';
  };
}

const PersonalizedDashboard: React.FC<PersonalizedDashboardProps> = ({
  userId,
  userProfile
}) => {
  const [insights, setInsights] = useState<ResearchInsight[]>([]);
  const [progress, setProgress] = useState<ResearchProgress[]>([]);
  const [metrics, setMetrics] = useState<ResearchMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTimeframe, setSelectedTimeframe] = useState<'week' | 'month' | 'quarter'>('month');

  // Fetch personalized data
  useEffect(() => {
    fetchDashboardData();
  }, [userId, selectedTimeframe]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // Fetch insights
      const insightsResponse = await fetch(`/api/research/insights/${userId}?timeframe=${selectedTimeframe}`);
      const insightsData = await insightsResponse.json();
      setInsights(insightsData.insights || []);

      // Fetch progress
      const progressResponse = await fetch(`/api/research/progress/${userId}`);
      const progressData = await progressResponse.json();
      setProgress(progressData.projects || []);

      // Fetch metrics
      const metricsResponse = await fetch(`/api/research/metrics/${userId}?timeframe=${selectedTimeframe}`);
      const metricsData = await metricsResponse.json();
      setMetrics(metricsData.metrics || null);

    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      // Set mock data for development
      setMockData();
    } finally {
      setLoading(false);
    }
  };

  const setMockData = () => {
    setInsights([
      {
        id: '1',
        type: 'trend',
        title: 'Emerging Trend in Your Field',
        description: 'Multi-modal AI is gaining significant traction in computer vision research. Consider exploring this area.',
        confidence: 0.87,
        actionable: true,
        data: { trendGrowth: 45, relatedPapers: 127 }
      },
      {
        id: '2',
        type: 'opportunity',
        title: 'Collaboration Opportunity',
        description: 'Dr. Sarah Chen at MIT is working on similar problems. High potential for collaboration.',
        confidence: 0.92,
        actionable: true,
        data: { matchScore: 0.92, sharedInterests: ['neural networks', 'computer vision'] }
      },
      {
        id: '3',
        type: 'recommendation',
        title: 'Recommended Reading',
        description: 'Based on your recent activity, you might find "Attention Is All You Need" highly relevant.',
        confidence: 0.78,
        actionable: true,
        data: { relevanceScore: 0.78, citationCount: 15420 }
      }
    ]);

    setProgress([
      {
        projectId: 'proj1',
        projectName: 'Multi-Modal Learning for Medical Imaging',
        progress: 65,
        milestones: [
          { name: 'Literature Review', completed: true, dueDate: '2024-01-15' },
          { name: 'Data Collection', completed: true, dueDate: '2024-02-01' },
          { name: 'Model Development', completed: false, dueDate: '2024-03-15' },
          { name: 'Evaluation', completed: false, dueDate: '2024-04-01' }
        ],
        nextSteps: [
          'Complete CNN architecture implementation',
          'Run initial experiments on dataset',
          'Analyze preliminary results'
        ],
        predictedCompletion: '2024-04-15'
      }
    ]);

    setMetrics({
      papersRead: 47,
      citationsFound: 312,
      collaborations: 8,
      projectsActive: 3,
      weeklyProgress: [12, 18, 15, 22, 19, 25, 21],
      topicDistribution: {
        'Machine Learning': 35,
        'Computer Vision': 28,
        'Natural Language Processing': 20,
        'Data Science': 17
      },
      impactScore: 78
    });
  };

  const getInsightIcon = (type: ResearchInsight['type']) => {
    switch (type) {
      case 'trend': return <TrendingUp className="w-5 h-5 text-blue-500" />;
      case 'opportunity': return <Target className="w-5 h-5 text-green-500" />;
      case 'recommendation': return <Lightbulb className="w-5 h-5 text-yellow-500" />;
      case 'alert': return <AlertCircle className="w-5 h-5 text-red-500" />;
      default: return <BookOpen className="w-5 h-5 text-gray-500" />;
    }
  };

  const getInsightColor = (type: ResearchInsight['type']) => {
    switch (type) {
      case 'trend': return 'border-blue-200 bg-blue-50';
      case 'opportunity': return 'border-green-200 bg-green-50';
      case 'recommendation': return 'border-yellow-200 bg-yellow-50';
      case 'alert': return 'border-red-200 bg-red-50';
      default: return 'border-gray-200 bg-gray-50';
    }
  };

  // Chart configurations
  const progressChartData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'Research Activity',
        data: metrics?.weeklyProgress || [],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
      },
    ],
  };

  const topicDistributionData = {
    labels: Object.keys(metrics?.topicDistribution || {}),
    datasets: [
      {
        data: Object.values(metrics?.topicDistribution || {}),
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
        ],
        borderWidth: 2,
        borderColor: '#fff',
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Welcome back, {userProfile.name}
            </h1>
            <p className="text-gray-600 mt-1">
              Here's your personalized research dashboard
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <select
              value={selectedTimeframe}
              onChange={(e) => setSelectedTimeframe(e.target.value as any)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value="week">This Week</option>
              <option value="month">This Month</option>
              <option value="quarter">This Quarter</option>
            </select>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <BookOpen className="w-8 h-8 text-blue-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Papers Read</p>
              <p className="text-2xl font-bold text-gray-900">{metrics?.papersRead || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <TrendingUp className="w-8 h-8 text-green-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Citations Found</p>
              <p className="text-2xl font-bold text-gray-900">{metrics?.citationsFound || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <Users className="w-8 h-8 text-purple-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Collaborations</p>
              <p className="text-2xl font-bold text-gray-900">{metrics?.collaborations || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <Target className="w-8 h-8 text-orange-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Impact Score</p>
              <p className="text-2xl font-bold text-gray-900">{metrics?.impactScore || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Research Activity Chart */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Research Activity</h3>
          <Line data={progressChartData} options={chartOptions} />
        </div>

        {/* Topic Distribution */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Research Topics</h3>
          <div className="h-64 flex items-center justify-center">
            <Doughnut data={topicDistributionData} />
          </div>
        </div>
      </div>

      {/* AI Insights */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">AI-Powered Insights</h3>
        <div className="space-y-4">
          {insights.map((insight) => (
            <div
              key={insight.id}
              className={`border rounded-lg p-4 ${getInsightColor(insight.type)}`}
            >
              <div className="flex items-start space-x-3">
                {getInsightIcon(insight.type)}
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-gray-900">{insight.title}</h4>
                    <span className="text-xs text-gray-500">
                      {Math.round(insight.confidence * 100)}% confidence
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{insight.description}</p>
                  {insight.actionable && (
                    <button className="mt-2 text-sm text-blue-600 hover:text-blue-800 font-medium">
                      Take Action →
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Research Progress */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Research Progress</h3>
        <div className="space-y-6">
          {progress.map((project) => (
            <div key={project.projectId} className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-gray-900">{project.projectName}</h4>
                <span className="text-sm text-gray-500">
                  {project.progress}% complete
                </span>
              </div>
              
              {/* Progress Bar */}
              <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${project.progress}%` }}
                ></div>
              </div>

              {/* Milestones */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h5 className="text-sm font-medium text-gray-700 mb-2">Milestones</h5>
                  <div className="space-y-2">
                    {project.milestones.map((milestone, index) => (
                      <div key={index} className="flex items-center space-x-2">
                        {milestone.completed ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : (
                          <div className="w-4 h-4 border-2 border-gray-300 rounded-full"></div>
                        )}
                        <span className={`text-sm ${milestone.completed ? 'text-gray-900' : 'text-gray-500'}`}>
                          {milestone.name}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h5 className="text-sm font-medium text-gray-700 mb-2">Next Steps</h5>
                  <ul className="space-y-1">
                    {project.nextSteps.map((step, index) => (
                      <li key={index} className="text-sm text-gray-600">
                        • {step}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-sm text-gray-500">
                  Predicted completion: <span className="font-medium">{project.predictedCompletion}</span>
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors">
            <BookOpen className="w-6 h-6 text-gray-400 mr-2" />
            <span className="text-gray-600">Upload New Paper</span>
          </button>
          
          <button className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors">
            <Users className="w-6 h-6 text-gray-400 mr-2" />
            <span className="text-gray-600">Find Collaborators</span>
          </button>
          
          <button className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors">
            <Target className="w-6 h-6 text-gray-400 mr-2" />
            <span className="text-gray-600">Start New Project</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default PersonalizedDashboard;