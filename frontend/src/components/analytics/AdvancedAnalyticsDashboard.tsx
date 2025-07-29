import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Tabs,
  Tab,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Chip,
  Paper,
  List,
  ListItem,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  Tooltip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Analytics as AnalyticsIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  Timeline as TimelineIcon,
  Share as ShareIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Insights as InsightsIcon,
  AccountTree as NetworkIcon,
  BarChart as ChartIcon,
  PieChart as PieChartIcon
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  Area,
  AreaChart
} from 'recharts';
import { useApi } from '../../hooks/useApi';
import { useNotification } from '../../hooks/useNotification';

interface AnalyticsMetric {
  name: string;
  value: any;
  metric_type: string;
  description: string;
  unit?: string;
  trend?: number;
  benchmark?: number;
  timestamp?: string;
}

interface VisualizationData {
  chart_type: string;
  title: string;
  data: any;
  config: any;
  description: string;
  insights: string[];
}

interface InsightReport {
  id: string;
  title: string;
  summary: string;
  metrics: AnalyticsMetric[];
  visualizations: VisualizationData[];
  recommendations: string[];
  timeframe: string;
  generated_at: string;
  confidence_score: number;
}

interface DocumentRelationship {
  source_doc_id: string;
  target_doc_id: string;
  relationship_type: string;
  strength: number;
  shared_concepts: string[];
  similarity_score: number;
}

interface KnowledgePattern {
  pattern_id: string;
  pattern_type: string;
  entities: string[];
  relationships: string[];
  frequency: number;
  confidence: number;
  examples: string[];
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analytics-tabpanel-${index}`}
      aria-labelledby={`analytics-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

const AdvancedAnalyticsDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [timeframe, setTimeframe] = useState('week');
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [comprehensiveReport, setComprehensiveReport] = useState<InsightReport | null>(null);
  const [documentRelationships, setDocumentRelationships] = useState<DocumentRelationship[]>([]);
  const [knowledgePatterns, setKnowledgePatterns] = useState<KnowledgePattern[]>([]);
  const [usageInsights, setUsageInsights] = useState<any>(null);
  const [contentAnalytics, setContentAnalytics] = useState<any>(null);
  const [knowledgeMap, setKnowledgeMap] = useState<VisualizationData | null>(null);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);

  const { apiCall } = useApi();
  const { showNotification } = useNotification();

  useEffect(() => {
    loadDashboardData();
  }, [timeframe]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const data = await apiCall(`/api/analytics/dashboard/data?timeframe=${timeframe}`, 'GET');
      setDashboardData(data);
      setUsageInsights(data.usage_insights);
      setContentAnalytics(data.content_analytics);
      setDocumentRelationships(data.document_relationships || []);
      setKnowledgePatterns(data.knowledge_patterns || []);
      setKnowledgeMap(data.knowledge_map);
    } catch (error) {
      showNotification('Failed to load dashboard data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const generateComprehensiveReport = async () => {
    setLoading(true);
    try {
      const report = await apiCall('/api/analytics/report/comprehensive', 'POST', {
        timeframe,
        include_predictions: true
      });
      setComprehensiveReport(report);
      showNotification('Comprehensive report generated successfully', 'success');
    } catch (error) {
      showNotification('Failed to generate comprehensive report', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadDocumentRelationships = async () => {
    setLoading(true);
    try {
      const relationships = await apiCall('/api/analytics/documents/relationships', 'POST', {
        min_similarity: 0.3,
        max_relationships: 100
      });
      setDocumentRelationships(relationships);
    } catch (error) {
      showNotification('Failed to load document relationships', 'error');
    } finally {
      setLoading(false);
    }
  };

  const discoverKnowledgePatterns = async () => {
    setLoading(true);
    try {
      const patterns = await apiCall('/api/analytics/knowledge/patterns', 'POST', {
        min_frequency: 3,
        confidence_threshold: 0.7
      });
      setKnowledgePatterns(patterns);
    } catch (error) {
      showNotification('Failed to discover knowledge patterns', 'error');
    } finally {
      setLoading(false);
    }
  };

  const createKnowledgeMap = async () => {
    setLoading(true);
    try {
      const map = await apiCall('/api/analytics/knowledge/map', 'POST', {
        layout_algorithm: 'spring',
        max_nodes: 100
      });
      setKnowledgeMap(map);
    } catch (error) {
      showNotification('Failed to create knowledge map', 'error');
    } finally {
      setLoading(false);
    }
  };

  const renderMetricCard = (metric: AnalyticsMetric) => (
    <Card key={metric.name} sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" component="div" gutterBottom>
          {metric.name}
        </Typography>
        <Typography variant="h4" color="primary" gutterBottom>
          {typeof metric.value === 'number' ? metric.value.toLocaleString() : metric.value}
          {metric.unit && <Typography variant="caption" sx={{ ml: 1 }}>{metric.unit}</Typography>}
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          {metric.description}
        </Typography>
        {metric.trend !== undefined && (
          <Box display="flex" alignItems="center">
            <TrendingUpIcon 
              color={metric.trend > 0 ? 'success' : metric.trend < 0 ? 'error' : 'disabled'} 
              sx={{ mr: 1 }} 
            />
            <Typography 
              variant="body2" 
              color={metric.trend > 0 ? 'success.main' : metric.trend < 0 ? 'error.main' : 'text.secondary'}
            >
              {metric.trend > 0 ? '+' : ''}{metric.trend?.toFixed(1)}%
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );

  const renderVisualization = (viz: VisualizationData) => {
    const { chart_type, title, data, description, insights } = viz;

    const renderChart = () => {
      switch (chart_type) {
        case 'line_chart':
          return (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.values || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <RechartsTooltip />
                <Legend />
                <Line type="monotone" dataKey="value" stroke="#8884d8" />
              </LineChart>
            </ResponsiveContainer>
          );

        case 'bar_chart':
          const barData = data.labels?.map((label: string, index: number) => ({
            name: label,
            value: data.values?.[index] || 0
          })) || [];
          
          return (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <RechartsTooltip />
                <Bar dataKey="value" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          );

        case 'pie_chart':
          const pieData = data.labels?.map((label: string, index: number) => ({
            name: label,
            value: data.values?.[index] || 0
          })) || [];
          
          return (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ResponsiveContainer>
          );

        case 'network_graph':
          return (
            <Box sx={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Typography variant="body1" color="text.secondary">
                Interactive network visualization would be rendered here
              </Typography>
            </Box>
          );

        default:
          return (
            <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Typography variant="body1" color="text.secondary">
                Visualization type: {chart_type}
              </Typography>
            </Box>
          );
      }
    };

    return (
      <Card key={title} sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {title}
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            {description}
          </Typography>
          
          {renderChart()}
          
          {insights.length > 0 && (
            <Box mt={2}>
              <Typography variant="subtitle2" gutterBottom>
                Key Insights:
              </Typography>
              <List dense>
                {insights.map((insight, index) => (
                  <ListItem key={index}>
                    <ListItemText primary={`• ${insight}`} />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderOverviewTab = () => (
    <Box>
      <Box display="flex" justifyContent="between" alignItems="center" mb={3}>
        <Typography variant="h5">Analytics Overview</Typography>
        <Box>
          <FormControl sx={{ mr: 2, minWidth: 120 }}>
            <InputLabel>Timeframe</InputLabel>
            <Select
              value={timeframe}
              label="Timeframe"
              onChange={(e) => setTimeframe(e.target.value)}
            >
              <MenuItem value="day">Last Day</MenuItem>
              <MenuItem value="week">Last Week</MenuItem>
              <MenuItem value="month">Last Month</MenuItem>
              <MenuItem value="quarter">Last Quarter</MenuItem>
              <MenuItem value="year">Last Year</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadDashboardData}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {dashboardData && (
        <>
          {/* Usage Insights */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Usage Summary
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="primary">
                      {usageInsights?.total_events || 0}
                    </Typography>
                    <Typography variant="body2">Total Events</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="secondary">
                      {Object.keys(usageInsights?.event_types || {}).length}
                    </Typography>
                    <Typography variant="body2">Feature Types Used</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="success.main">
                      {usageInsights?.session_analysis?.total_sessions || 0}
                    </Typography>
                    <Typography variant="body2">Total Sessions</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="warning.main">
                      {usageInsights?.session_analysis?.average_duration?.toFixed(1) || 0}
                    </Typography>
                    <Typography variant="body2">Avg Session (min)</Typography>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Content Analytics */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Content Overview
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="primary">
                      {contentAnalytics?.document_stats?.total_documents || 0}
                    </Typography>
                    <Typography variant="body2">Total Documents</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="secondary">
                      {contentAnalytics?.content_analysis?.total_words?.toLocaleString() || 0}
                    </Typography>
                    <Typography variant="body2">Total Words</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="success.main">
                      {(contentAnalytics?.quality_metrics?.processing_success_rate * 100)?.toFixed(1) || 0}%
                    </Typography>
                    <Typography variant="body2">Success Rate</Typography>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={3}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<AssessmentIcon />}
                    onClick={generateComprehensiveReport}
                    disabled={loading}
                  >
                    Generate Report
                  </Button>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<NetworkIcon />}
                    onClick={createKnowledgeMap}
                    disabled={loading}
                  >
                    Knowledge Map
                  </Button>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<InsightsIcon />}
                    onClick={discoverKnowledgePatterns}
                    disabled={loading}
                  >
                    Find Patterns
                  </Button>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<ShareIcon />}
                    onClick={() => setExportDialogOpen(true)}
                  >
                    Export Data
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </>
      )}
    </Box>
  );

  const renderComprehensiveReportTab = () => (
    <Box>
      <Box display="flex" justifyContent="between" alignItems="center" mb={3}>
        <Typography variant="h5">Comprehensive Report</Typography>
        <Button
          variant="contained"
          startIcon={<AssessmentIcon />}
          onClick={generateComprehensiveReport}
          disabled={loading}
        >
          {loading ? <CircularProgress size={20} /> : 'Generate Report'}
        </Button>
      </Box>

      {comprehensiveReport && (
        <Box>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {comprehensiveReport.title}
              </Typography>
              <Typography variant="body1" paragraph>
                {comprehensiveReport.summary}
              </Typography>
              <Box display="flex" alignItems="center" gap={2}>
                <Chip 
                  label={`Timeframe: ${comprehensiveReport.timeframe}`} 
                  color="primary" 
                />
                <Chip 
                  label={`Confidence: ${(comprehensiveReport.confidence_score * 100).toFixed(1)}%`} 
                  color="secondary" 
                />
                <Typography variant="caption" color="text.secondary">
                  Generated: {new Date(comprehensiveReport.generated_at).toLocaleString()}
                </Typography>
              </Box>
            </CardContent>
          </Card>

          {/* Metrics */}
          <Typography variant="h6" gutterBottom>
            Key Metrics
          </Typography>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            {comprehensiveReport.metrics.map((metric) => (
              <Grid item xs={12} md={6} lg={4} key={metric.name}>
                {renderMetricCard(metric)}
              </Grid>
            ))}
          </Grid>

          {/* Visualizations */}
          <Typography variant="h6" gutterBottom>
            Visualizations
          </Typography>
          {comprehensiveReport.visualizations.map((viz) => renderVisualization(viz))}

          {/* Recommendations */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recommendations
              </Typography>
              <List>
                {comprehensiveReport.recommendations.map((rec, index) => (
                  <ListItem key={index}>
                    <ListItemText primary={`${index + 1}. ${rec}`} />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Box>
      )}
    </Box>
  );

  const renderDocumentRelationshipsTab = () => (
    <Box>
      <Box display="flex" justifyContent="between" alignItems="center" mb={3}>
        <Typography variant="h5">Document Relationships</Typography>
        <Button
          variant="contained"
          startIcon={<NetworkIcon />}
          onClick={loadDocumentRelationships}
          disabled={loading}
        >
          {loading ? <CircularProgress size={20} /> : 'Analyze Relationships'}
        </Button>
      </Box>

      {documentRelationships.length > 0 && (
        <Grid container spacing={2}>
          {documentRelationships.map((rel, index) => (
            <Grid item xs={12} md={6} key={index}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {rel.relationship_type.replace('_', ' ').toUpperCase()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Similarity: {(rel.similarity_score * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    Strength: {rel.strength.toFixed(3)}
                  </Typography>
                  
                  {rel.shared_concepts.length > 0 && (
                    <Box mt={2}>
                      <Typography variant="subtitle2" gutterBottom>
                        Shared Concepts:
                      </Typography>
                      <Box display="flex" flexWrap="wrap" gap={0.5}>
                        {rel.shared_concepts.map((concept, idx) => (
                          <Chip key={idx} label={concept} size="small" />
                        ))}
                      </Box>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {documentRelationships.length === 0 && !loading && (
        <Alert severity="info">
          No document relationships found. Try analyzing your documents first.
        </Alert>
      )}
    </Box>
  );

  const renderKnowledgePatternsTab = () => (
    <Box>
      <Box display="flex" justifyContent="between" alignItems="center" mb={3}>
        <Typography variant="h5">Knowledge Patterns</Typography>
        <Button
          variant="contained"
          startIcon={<InsightsIcon />}
          onClick={discoverKnowledgePatterns}
          disabled={loading}
        >
          {loading ? <CircularProgress size={20} /> : 'Discover Patterns'}
        </Button>
      </Box>

      {knowledgePatterns.length > 0 && (
        <Box>
          {knowledgePatterns.map((pattern) => (
            <Accordion key={pattern.pattern_id} sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box display="flex" alignItems="center" width="100%">
                  <Typography variant="h6" sx={{ flexGrow: 1 }}>
                    {pattern.pattern_type.replace('_', ' ').toUpperCase()}
                  </Typography>
                  <Chip 
                    label={`Frequency: ${pattern.frequency}`} 
                    size="small" 
                    sx={{ mr: 1 }} 
                  />
                  <Chip 
                    label={`Confidence: ${(pattern.confidence * 100).toFixed(1)}%`} 
                    size="small" 
                    color="secondary" 
                  />
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      Entities:
                    </Typography>
                    <Box display="flex" flexWrap="wrap" gap={0.5} mb={2}>
                      {pattern.entities.map((entity, idx) => (
                        <Chip key={idx} label={entity} size="small" />
                      ))}
                    </Box>
                    
                    <Typography variant="subtitle2" gutterBottom>
                      Relationships:
                    </Typography>
                    <Box display="flex" flexWrap="wrap" gap={0.5}>
                      {pattern.relationships.map((rel, idx) => (
                        <Chip key={idx} label={rel} size="small" variant="outlined" />
                      ))}
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      Examples:
                    </Typography>
                    <List dense>
                      {pattern.examples.map((example, idx) => (
                        <ListItem key={idx}>
                          <ListItemText primary={example} />
                        </ListItem>
                      ))}
                    </List>
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      )}

      {knowledgePatterns.length === 0 && !loading && (
        <Alert severity="info">
          No knowledge patterns discovered. Try adding more documents to build richer patterns.
        </Alert>
      )}
    </Box>
  );

  const renderKnowledgeMapTab = () => (
    <Box>
      <Box display="flex" justifyContent="between" alignItems="center" mb={3}>
        <Typography variant="h5">Knowledge Map</Typography>
        <Button
          variant="contained"
          startIcon={<NetworkIcon />}
          onClick={createKnowledgeMap}
          disabled={loading}
        >
          {loading ? <CircularProgress size={20} /> : 'Generate Map'}
        </Button>
      </Box>

      {knowledgeMap && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {knowledgeMap.title}
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              {knowledgeMap.description}
            </Typography>
            
            {/* Placeholder for network visualization */}
            <Box 
              sx={{ 
                height: 500, 
                border: '1px dashed #ccc', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                mb: 2
              }}
            >
              <Typography variant="body1" color="text.secondary">
                Interactive Knowledge Graph Visualization
                <br />
                (Would render with D3.js or similar library)
              </Typography>
            </Box>
            
            {knowledgeMap.insights.length > 0 && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Key Insights:
                </Typography>
                <List dense>
                  {knowledgeMap.insights.map((insight, index) => (
                    <ListItem key={index}>
                      <ListItemText primary={`• ${insight}`} />
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {!knowledgeMap && !loading && (
        <Alert severity="info">
          No knowledge map available. Generate one to visualize your knowledge graph.
        </Alert>
      )}
    </Box>
  );

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h4" gutterBottom>
        Advanced Analytics Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Comprehensive insights into your content, usage patterns, and knowledge relationships.
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="analytics dashboard tabs">
          <Tab label="Overview" icon={<AnalyticsIcon />} />
          <Tab label="Comprehensive Report" icon={<AssessmentIcon />} />
          <Tab label="Document Relationships" icon={<NetworkIcon />} />
          <Tab label="Knowledge Patterns" icon={<InsightsIcon />} />
          <Tab label="Knowledge Map" icon={<TimelineIcon />} />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        {renderOverviewTab()}
      </TabPanel>
      <TabPanel value={tabValue} index={1}>
        {renderComprehensiveReportTab()}
      </TabPanel>
      <TabPanel value={tabValue} index={2}>
        {renderDocumentRelationshipsTab()}
      </TabPanel>
      <TabPanel value={tabValue} index={3}>
        {renderKnowledgePatternsTab()}
      </TabPanel>
      <TabPanel value={tabValue} index={4}>
        {renderKnowledgeMapTab()}
      </TabPanel>

      {/* Export Dialog */}
      <Dialog open={exportDialogOpen} onClose={() => setExportDialogOpen(false)}>
        <DialogTitle>Export Analytics Data</DialogTitle>
        <DialogContent>
          <Typography variant="body2" paragraph>
            Choose the format for exporting your analytics data:
          </Typography>
          <Box display="flex" flexDirection="column" gap={2}>
            <Button variant="outlined" startIcon={<DownloadIcon />}>
              Export as JSON
            </Button>
            <Button variant="outlined" startIcon={<DownloadIcon />}>
              Export as CSV
            </Button>
            <Button variant="outlined" startIcon={<DownloadIcon />}>
              Export as PDF Report
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialogOpen(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AdvancedAnalyticsDashboard;