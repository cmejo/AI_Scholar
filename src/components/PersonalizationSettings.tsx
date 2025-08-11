import {
    BarChart3,
    BookOpen,
    Brain,
    ChevronDown, ChevronUp,
    Clock,
    MessageSquare,
    RefreshCw,
    Save,
    Settings,
    Star,
    Target, TrendingUp,
    User
} from 'lucide-react';
import React, { useEffect, useState } from 'react';

interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  defaultModel: string;
  responseLength: 'concise' | 'detailed' | 'comprehensive';
  enableVoice: boolean;
  enableNotifications: boolean;
  responseStyle: 'balanced' | 'technical' | 'conversational';
  citationPreference: 'inline' | 'footnotes' | 'bibliography';
  reasoningDisplay: boolean;
  uncertaintyTolerance: number;
  domainAdaptation: boolean;
  enableAdaptiveRetrieval: boolean;
}

type DomainExpertise = Record<string, number>;

interface PersonalizationStats {
  totalSearches: number;
  personalizedSearches: number;
  personalizationRate: number;
  topDomains: Record<string, number>;
  avgResultsPerSearch: number;
  avgSatisfaction: number;
  satisfactionTrend: 'improving' | 'stable' | 'declining';
}

interface FeedbackHistory {
  id: string;
  timestamp: string;
  feedbackType: string;
  rating?: number;
  comment?: string;
  processed: boolean;
}

interface LearningInsights {
  totalQueries: number;
  favoriteTopics: string[];
  averageSessionLength: number;
  preferredResponseStyle: string;
  learningProgress: {
    month: string;
    queries: number;
    uniqueTopics: number;
    engagement: number;
  }[];
}

interface PersonalizationSettingsProps {
  userId: string;
  onClose?: () => void;
}

export const PersonalizationSettings: React.FC<PersonalizationSettingsProps> = ({
  userId,
  onClose
}) => {
  const [activeTab, setActiveTab] = useState<'preferences' | 'domains' | 'feedback' | 'insights'>('preferences');
  const [preferences, setPreferences] = useState<UserPreferences>({
    theme: 'dark',
    language: 'en',
    defaultModel: 'mistral',
    responseLength: 'detailed',
    enableVoice: false,
    enableNotifications: true,
    responseStyle: 'balanced',
    citationPreference: 'inline',
    reasoningDisplay: true,
    uncertaintyTolerance: 0.5,
    domainAdaptation: true,
    enableAdaptiveRetrieval: true
  });
  
  const [domainExpertise, setDomainExpertise] = useState<DomainExpertise>({});
  const [personalizationStats, setPersonalizationStats] = useState<PersonalizationStats | null>(null);
  const [feedbackHistory, setFeedbackHistory] = useState<FeedbackHistory[]>([]);
  const [learningInsights, setLearningInsights] = useState<LearningInsights | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['basic', 'response', 'personalization']));

  const loadPersonalizationData = useCallback(async () => {
    setLoading(true);
    try {
      // Load user preferences
      const preferencesResponse = await fetch(`/api/users/${userId}/preferences`);
      if (preferencesResponse.ok) {
        const preferencesData = await preferencesResponse.json() as UserPreferences;
        setPreferences(preferencesData);
      }

      // Load domain expertise
      const domainResponse = await fetch(`/api/users/${userId}/domain-expertise`);
      if (domainResponse.ok) {
        const domainData = await domainResponse.json() as DomainExpertise;
        setDomainExpertise(domainData);
      }

      // Load personalization stats
      const statsResponse = await fetch(`/api/users/${userId}/personalization-stats`);
      if (statsResponse.ok) {
        const statsData = await statsResponse.json() as PersonalizationStats;
        setPersonalizationStats(statsData);
      }

      // Load feedback history
      const feedbackResponse = await fetch(`/api/users/${userId}/feedback-history`);
      if (feedbackResponse.ok) {
        const feedbackData = await feedbackResponse.json() as FeedbackHistory[];
        setFeedbackHistory(feedbackData);
      }

      // Load learning insights
      const insightsResponse = await fetch(`/api/users/${userId}/learning-insights`);
      if (insightsResponse.ok) {
        const insightsData = await insightsResponse.json() as LearningInsights;
        setLearningInsights(insightsData);
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      console.error('Error loading personalization data:', errorMessage);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    loadPersonalizationData();
  }, [loadPersonalizationData]);

  const savePreferences = async (): Promise<void> => {
    setSaving(true);
    try {
      const response = await fetch(`/api/users/${userId}/preferences`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(preferences),
      });

      if (response.ok) {
        // Show success message
        console.log('Preferences saved successfully');
      } else {
        throw new Error('Failed to save preferences');
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      console.error('Error saving preferences:', errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const toggleSection = (section: string): void => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const renderPreferencesTab = () => (
    <div className="space-y-6">
      {/* Basic Preferences */}
      <div className="bg-gray-800 rounded-lg p-6">
        <button
          onClick={() => toggleSection('basic')}
          className="flex items-center justify-between w-full text-left"
        >
          <h3 className="text-lg font-semibold text-white flex items-center">
            <Settings className="mr-2" size={20} />
            Basic Preferences
          </h3>
          {expandedSections.has('basic') ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>
        
        {expandedSections.has('basic') && (
          <div className="mt-4 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Theme
                </label>
                <select
                  value={preferences.theme}
                  onChange={(e) => setPreferences({...preferences, theme: e.target.value as UserPreferences['theme']})}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="auto">Auto</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Language
                </label>
                <select
                  value={preferences.language}
                  onChange={(e) => setPreferences({...preferences, language: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Default Model
                </label>
                <select
                  value={preferences.defaultModel}
                  onChange={(e) => setPreferences({...preferences, defaultModel: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                >
                  <option value="mistral">Mistral</option>
                  <option value="llama">Llama</option>
                  <option value="gpt">GPT</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Response Length
                </label>
                <select
                  value={preferences.responseLength}
                  onChange={(e) => setPreferences({...preferences, responseLength: e.target.value as UserPreferences['responseLength']})}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                >
                  <option value="concise">Concise</option>
                  <option value="detailed">Detailed</option>
                  <option value="comprehensive">Comprehensive</option>
                </select>
              </div>
            </div>

            <div className="flex items-center space-x-6">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={preferences.enableVoice}
                  onChange={(e) => setPreferences({...preferences, enableVoice: e.target.checked})}
                  className="mr-2"
                />
                <span className="text-gray-300">Enable Voice</span>
              </label>
              
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={preferences.enableNotifications}
                  onChange={(e) => setPreferences({...preferences, enableNotifications: e.target.checked})}
                  className="mr-2"
                />
                <span className="text-gray-300">Enable Notifications</span>
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Response Preferences */}
      <div className="bg-gray-800 rounded-lg p-6">
        <button
          onClick={() => toggleSection('response')}
          className="flex items-center justify-between w-full text-left"
        >
          <h3 className="text-lg font-semibold text-white flex items-center">
            <MessageSquare className="mr-2" size={20} />
            Response Preferences
          </h3>
          {expandedSections.has('response') ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>
        
        {expandedSections.has('response') && (
          <div className="mt-4 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Response Style
                </label>
                <select
                  value={preferences.responseStyle}
                  onChange={(e) => setPreferences({...preferences, responseStyle: e.target.value as UserPreferences['responseStyle']})}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                >
                  <option value="balanced">Balanced</option>
                  <option value="technical">Technical</option>
                  <option value="conversational">Conversational</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Citation Preference
                </label>
                <select
                  value={preferences.citationPreference}
                  onChange={(e) => setPreferences({...preferences, citationPreference: e.target.value as UserPreferences['citationPreference']})}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                >
                  <option value="inline">Inline</option>
                  <option value="footnotes">Footnotes</option>
                  <option value="bibliography">Bibliography</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Uncertainty Tolerance: {Math.round(preferences.uncertaintyTolerance * 100)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={preferences.uncertaintyTolerance}
                onChange={(e) => setPreferences({...preferences, uncertaintyTolerance: parseFloat(e.target.value)})}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>Conservative</span>
                <span>Balanced</span>
                <span>Exploratory</span>
              </div>
            </div>

            <div className="flex items-center space-x-6">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={preferences.reasoningDisplay}
                  onChange={(e) => setPreferences({...preferences, reasoningDisplay: e.target.checked})}
                  className="mr-2"
                />
                <span className="text-gray-300">Show Reasoning Steps</span>
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Personalization Features */}
      <div className="bg-gray-800 rounded-lg p-6">
        <button
          onClick={() => toggleSection('personalization')}
          className="flex items-center justify-between w-full text-left"
        >
          <h3 className="text-lg font-semibold text-white flex items-center">
            <Brain className="mr-2" size={20} />
            Personalization Features
          </h3>
          {expandedSections.has('personalization') ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>
        
        {expandedSections.has('personalization') && (
          <div className="mt-4 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-gray-300 font-medium">Domain Adaptation</label>
                <p className="text-sm text-gray-400">Adapt responses based on your domain expertise</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={preferences.domainAdaptation}
                  onChange={(e) => setPreferences({...preferences, domainAdaptation: e.target.checked})}
                  className="sr-only peer"
                  aria-label="Domain Adaptation"
                />
                <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-gray-300 font-medium">Adaptive Retrieval</label>
                <p className="text-sm text-gray-400">Personalize search results based on your history</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={preferences.enableAdaptiveRetrieval}
                  onChange={(e) => setPreferences({...preferences, enableAdaptiveRetrieval: e.target.checked})}
                  className="sr-only peer"
                  aria-label="Adaptive Retrieval"
                />
                <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Save Button */}
      <div className="flex justify-end space-x-4">
        <button
          onClick={() => { void loadPersonalizationData(); }}
          disabled={loading}
          className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-500 disabled:opacity-50 flex items-center"
        >
          <RefreshCw className="mr-2" size={16} />
          Reset
        </button>
        <button
          onClick={() => { void savePreferences(); }}
          disabled={saving}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 disabled:opacity-50 flex items-center"
        >
          {saving ? (
            <>
              <RefreshCw className="mr-2 animate-spin" size={16} />
              Saving...
            </>
          ) : (
            <>
              <Save className="mr-2" size={16} />
              Save Preferences
            </>
          )}
        </button>
      </div>
    </div>
  );

  const renderDomainsTab = () => (
    <div className="space-y-6">
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <Target className="mr-2" size={20} />
          Domain Expertise
        </h3>
        
        {Object.keys(domainExpertise).length === 0 ? (
          <div className="text-center py-8">
            <BookOpen className="mx-auto mb-4 text-gray-400" size={48} />
            <p className="text-gray-400">No domain expertise detected yet.</p>
            <p className="text-sm text-gray-500 mt-2">
              Continue using the system to build your domain profile.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {Object.entries(domainExpertise)
              .sort(([, a], [, b]) => b - a)
              .map(([domain, score]) => (
                <div key={domain} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-white capitalize">{domain}</span>
                      <span className="text-sm text-gray-400">{Math.round(score * 100)}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${score * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>

      {personalizationStats != null && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <BarChart3 className="mr-2" size={20} />
            Personalization Effectiveness
          </h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">
                {Math.round(personalizationStats.personalizationRate * 100)}%
              </div>
              <div className="text-sm text-gray-400">Personalization Rate</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">
                {personalizationStats.totalSearches}
              </div>
              <div className="text-sm text-gray-400">Total Searches</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-400">
                {personalizationStats.avgResultsPerSearch.toFixed(1)}
              </div>
              <div className="text-sm text-gray-400">Avg Results</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-400">
                {(personalizationStats.avgSatisfaction ?? 0) > 0 ? (personalizationStats.avgSatisfaction * 100).toFixed(0) + '%' : 'N/A'}
              </div>
              <div className="text-sm text-gray-400">Satisfaction</div>
            </div>
          </div>

          <div>
            <h4 className="text-md font-medium text-white mb-3">Top Domains</h4>
            <div className="space-y-2">
              {Object.entries(personalizationStats.topDomains)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 5)
                .map(([domain, count]) => (
                  <div key={domain} className="flex items-center justify-between">
                    <span className="text-gray-300 capitalize">{domain}</span>
                    <span className="text-sm text-gray-400">{count} searches</span>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderFeedbackTab = (): JSX.Element => (
    <div className="space-y-6">
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <Star className="mr-2" size={20} />
          Feedback History
        </h3>
        
        {feedbackHistory.length === 0 ? (
          <div className="text-center py-8">
            <MessageSquare className="mx-auto mb-4 text-gray-400" size={48} />
            <p className="text-gray-400">No feedback history available.</p>
            <p className="text-sm text-gray-500 mt-2">
              Start providing feedback to help improve your experience.
            </p>
          </div>
        ) : (
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {feedbackHistory.map((feedback) => (
              <div key={feedback.id} className="border border-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-white capitalize">
                      {feedback.feedbackType}
                    </span>
                    {(feedback.rating ?? 0) > 0 && (
                      <div className="flex items-center">
                        <Star className="text-yellow-400 mr-1" size={14} />
                        <span className="text-sm text-gray-300">{feedback.rating}/5</span>
                      </div>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-400">
                      {new Date(feedback.timestamp).toLocaleDateString()}
                    </span>
                    {feedback.processed ? (
                      <span className="text-xs bg-green-600 text-white px-2 py-1 rounded">
                        Processed
                      </span>
                    ) : (
                      <span className="text-xs bg-yellow-600 text-white px-2 py-1 rounded">
                        Pending
                      </span>
                    )}
                  </div>
                </div>
                {(feedback.comment?.length ?? 0) > 0 && (
                  <p className="text-sm text-gray-300">{feedback.comment}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  const renderInsightsTab = (): JSX.Element => (
    <div className="space-y-6">
      {learningInsights != null && (
        <>
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
              <TrendingUp className="mr-2" size={20} />
              Learning Insights
            </h3>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">
                  {learningInsights.totalQueries}
                </div>
                <div className="text-sm text-gray-400">Total Queries</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">
                  {learningInsights.favoriteTopics.length}
                </div>
                <div className="text-sm text-gray-400">Favorite Topics</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-400">
                  {Math.round(learningInsights.averageSessionLength)}m
                </div>
                <div className="text-sm text-gray-400">Avg Session</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-400 capitalize">
                  {learningInsights.preferredResponseStyle}
                </div>
                <div className="text-sm text-gray-400">Response Style</div>
              </div>
            </div>

            <div className="mb-6">
              <h4 className="text-md font-medium text-white mb-3">Favorite Topics</h4>
              <div className="flex flex-wrap gap-2">
                {learningInsights.favoriteTopics.map((topic, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-blue-600 text-white text-sm rounded-full"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
              <Clock className="mr-2" size={20} />
              Learning Progress
            </h3>
            
            {learningInsights.learningProgress.length === 0 ? (
              <div className="text-center py-8">
                <BarChart3 className="mx-auto mb-4 text-gray-400" size={48} />
                <p className="text-gray-400">Not enough data for progress tracking.</p>
                <p className="text-sm text-gray-500 mt-2">
                  Continue using the system to see your learning progress.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {learningInsights.learningProgress
                  .slice(-6) // Show last 6 months
                  .map((progress) => (
                    <div key={progress.month} className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-white">{progress.month}</span>
                          <div className="text-sm text-gray-400">
                            {progress.queries} queries, {progress.uniqueTopics} topics
                          </div>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${Math.min(progress.engagement / 100 * 100, 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-gray-900 rounded-lg p-8 max-w-md w-full mx-4">
          <div className="flex items-center justify-center">
            <RefreshCw className="animate-spin mr-2" size={24} />
            <span className="text-white">Loading personalization settings...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-900 rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-xl font-semibold text-white flex items-center">
            <User className="mr-2" size={24} />
            Personalization Settings
          </h2>
          {onClose != null && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white"
            >
              ×
            </button>
          )}
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-700">
          {[
            { id: 'preferences', label: 'Preferences', icon: Settings },
            { id: 'domains', label: 'Domain Adaptation', icon: Target },
            { id: 'feedback', label: 'Feedback History', icon: Star },
            { id: 'insights', label: 'Learning Insights', icon: TrendingUp }
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id as typeof activeTab)}
              className={`flex items-center px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === id
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              <Icon className="mr-2" size={16} />
              {label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {activeTab === 'preferences' && renderPreferencesTab()}
          {activeTab === 'domains' && renderDomainsTab()}
          {activeTab === 'feedback' && renderFeedbackTab()}
          {activeTab === 'insights' && renderInsightsTab()}
        </div>
      </div>
    </div>
  );
};

export default PersonalizationSettings;