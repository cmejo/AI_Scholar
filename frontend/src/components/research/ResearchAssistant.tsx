import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Button,
  TextField,
  Chip,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress,
  Alert,
  Rating,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Science as ScienceIcon,
  MenuBook as BookIcon,
  Assignment as AssignmentIcon,
  Analytics as AnalyticsIcon,
  Search as SearchIcon,
  Download as DownloadIcon,
  Share as ShareIcon,
  Bookmark as BookmarkIcon
} from '@mui/icons-material';
import { useApi } from '../../hooks/useApi';
import { useNotification } from '../../hooks/useNotification';

interface ResearchTopic {
  id: string;
  title: string;
  description: string;
  keywords: string[];
  domain: string;
  research_questions: string[];
  significance: string;
  novelty_score: number;
  feasibility_score: number;
  impact_potential: number;
  related_topics: string[];
  suggested_methodologies: string[];
  estimated_timeline: Record<string, number>;
  resources_needed: string[];
}

interface LiteratureReview {
  id: string;
  topic: string;
  research_questions: string[];
  search_strategy: any;
  sources: any[];
  themes: any[];
  gaps_identified: string[];
  synthesis: string;
  recommendations: string[];
  quality_assessment: any;
  created_at: string;
}

interface ResearchProposal {
  id: string;
  title: string;
  abstract: string;
  introduction: string;
  research_questions: string[];
  hypotheses: string[];
  methodology: any;
  timeline: any;
  budget: any;
  expected_outcomes: string[];
  significance: string;
  limitations: string[];
  ethical_considerations: string;
  created_at: string;
}

interface MethodologyRecommendation {
  methodology: string;
  suitability_score: number;
  rationale: string;
  advantages: string[];
  disadvantages: string[];
  requirements: string[];
  estimated_duration: number;
  complexity_level: string;
  sample_size_guidance: string;
  data_collection_methods: string[];
  analysis_methods: string[];
  tools_recommended: string[];
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
      id={`research-tabpanel-${index}`}
      aria-labelledby={`research-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const ResearchAssistant: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [researchTopics, setResearchTopics] = useState<ResearchTopic[]>([]);
  const [literatureReview, setLiteratureReview] = useState<LiteratureReview | null>(null);
  const [researchProposal, setResearchProposal] = useState<ResearchProposal | null>(null);
  const [methodologyAdvice, setMethodologyAdvice] = useState<any>(null);
  const [dataAnalysisGuidance, setDataAnalysisGuidance] = useState<any>(null);
  
  // Form states
  const [topicForm, setTopicForm] = useState({
    domain: '',
    keywords: '',
    num_topics: 5
  });
  
  const [reviewForm, setReviewForm] = useState({
    topic: '',
    research_questions: '',
    scope: 'comprehensive',
    max_sources: 50
  });
  
  const [proposalForm, setProposalForm] = useState({
    topic: '',
    research_questions: '',
    methodology_preference: ''
  });
  
  const [methodologyForm, setMethodologyForm] = useState({
    research_questions: '',
    domain: '',
    constraints: {}
  });
  
  const [analysisForm, setAnalysisForm] = useState({
    research_question: '',
    data_description: '',
    sample_size: 100,
    data_type: 'mixed'
  });

  const { apiCall } = useApi();
  const { showNotification } = useNotification();

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const generateResearchTopics = async () => {
    setLoading(true);
    try {
      const keywords = topicForm.keywords ? topicForm.keywords.split(',').map(k => k.trim()) : undefined;
      const response = await apiCall('/api/research/topics/generate', 'POST', {
        domain: topicForm.domain || undefined,
        keywords,
        num_topics: topicForm.num_topics
      });
      
      setResearchTopics(response);
      showNotification('Research topics generated successfully', 'success');
    } catch (error) {
      showNotification('Failed to generate research topics', 'error');
    } finally {
      setLoading(false);
    }
  };

  const generateLiteratureReview = async () => {
    setLoading(true);
    try {
      const research_questions = reviewForm.research_questions.split('\n').map(q => q.trim()).filter(q => q);
      const response = await apiCall('/api/research/literature-review/generate', 'POST', {
        topic: reviewForm.topic,
        research_questions,
        scope: reviewForm.scope,
        max_sources: reviewForm.max_sources
      });
      
      setLiteratureReview(response);
      showNotification('Literature review generated successfully', 'success');
    } catch (error) {
      showNotification('Failed to generate literature review', 'error');
    } finally {
      setLoading(false);
    }
  };

  const generateResearchProposal = async () => {
    setLoading(true);
    try {
      const research_questions = proposalForm.research_questions.split('\n').map(q => q.trim()).filter(q => q);
      const response = await apiCall('/api/research/proposal/generate', 'POST', {
        topic: proposalForm.topic,
        research_questions,
        methodology_preference: proposalForm.methodology_preference || undefined
      });
      
      setResearchProposal(response);
      showNotification('Research proposal generated successfully', 'success');
    } catch (error) {
      showNotification('Failed to generate research proposal', 'error');
    } finally {
      setLoading(false);
    }
  };

  const getMethodologyAdvice = async () => {
    setLoading(true);
    try {
      const research_questions = methodologyForm.research_questions.split('\n').map(q => q.trim()).filter(q => q);
      const response = await apiCall('/api/research/methodology/advice', 'POST', {
        research_questions,
        domain: methodologyForm.domain,
        constraints: methodologyForm.constraints
      });
      
      setMethodologyAdvice(response);
      showNotification('Methodology advice generated successfully', 'success');
    } catch (error) {
      showNotification('Failed to get methodology advice', 'error');
    } finally {
      setLoading(false);
    }
  };

  const getDataAnalysisGuidance = async () => {
    setLoading(true);
    try {
      const response = await apiCall('/api/research/data-analysis/guidance', 'POST', {
        research_question: analysisForm.research_question,
        data_description: analysisForm.data_description,
        sample_size: analysisForm.sample_size,
        data_type: analysisForm.data_type
      });
      
      setDataAnalysisGuidance(response);
      showNotification('Data analysis guidance generated successfully', 'success');
    } catch (error) {
      showNotification('Failed to get data analysis guidance', 'error');
    } finally {
      setLoading(false);
    }
  };

  const renderResearchTopics = () => (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Generate Research Topics
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Research Domain"
                value={topicForm.domain}
                onChange={(e) => setTopicForm({ ...topicForm, domain: e.target.value })}
                placeholder="e.g., Computer Science, Medicine"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Keywords (comma-separated)"
                value={topicForm.keywords}
                onChange={(e) => setTopicForm({ ...topicForm, keywords: e.target.value })}
                placeholder="e.g., machine learning, healthcare"
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                type="number"
                label="Number of Topics"
                value={topicForm.num_topics}
                onChange={(e) => setTopicForm({ ...topicForm, num_topics: parseInt(e.target.value) })}
                inputProps={{ min: 1, max: 10 }}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <Button
                fullWidth
                variant="contained"
                onClick={generateResearchTopics}
                disabled={loading}
                sx={{ height: '56px' }}
              >
                {loading ? <CircularProgress size={24} /> : 'Generate'}
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {researchTopics.length > 0 && (
        <Box>
          <Typography variant="h6" gutterBottom>
            Generated Research Topics
          </Typography>
          {researchTopics.map((topic, index) => (
            <Card key={topic.id} sx={{ mb: 2 }}>
              <CardContent>
                <Box display="flex" justifyContent="between" alignItems="start" mb={2}>
                  <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                    {topic.title}
                  </Typography>
                  <Box display="flex" gap={1}>
                    <Tooltip title="Bookmark Topic">
                      <IconButton size="small">
                        <BookmarkIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Share Topic">
                      <IconButton size="small">
                        <ShareIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>
                
                <Typography variant="body2" color="text.secondary" paragraph>
                  {topic.description}
                </Typography>
                
                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom>Keywords:</Typography>
                  <Box display="flex" flexWrap="wrap" gap={0.5}>
                    {topic.keywords.map((keyword, idx) => (
                      <Chip key={idx} label={keyword} size="small" />
                    ))}
                  </Box>
                </Box>
                
                <Grid container spacing={2} mb={2}>
                  <Grid item xs={4}>
                    <Typography variant="subtitle2">Novelty Score</Typography>
                    <Rating value={topic.novelty_score} readOnly precision={0.1} />
                  </Grid>
                  <Grid item xs={4}>
                    <Typography variant="subtitle2">Feasibility Score</Typography>
                    <Rating value={topic.feasibility_score} readOnly precision={0.1} />
                  </Grid>
                  <Grid item xs={4}>
                    <Typography variant="subtitle2">Impact Potential</Typography>
                    <Rating value={topic.impact_potential} readOnly precision={0.1} />
                  </Grid>
                </Grid>
                
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle2">Research Questions</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      {topic.research_questions.map((question, idx) => (
                        <ListItem key={idx}>
                          <ListItemText primary={`${idx + 1}. ${question}`} />
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
                
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle2">Suggested Methodologies & Timeline</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Typography variant="body2" gutterBottom><strong>Methodologies:</strong></Typography>
                        {topic.suggested_methodologies.map((method, idx) => (
                          <Chip key={idx} label={method.replace('_', ' ')} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                        ))}
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2" gutterBottom><strong>Estimated Timeline:</strong></Typography>
                        {Object.entries(topic.estimated_timeline).map(([phase, months]) => (
                          <Typography key={phase} variant="body2">
                            {phase.replace('_', ' ')}: {months} months
                          </Typography>
                        ))}
                      </Grid>
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}
    </Box>
  );

  const renderLiteratureReview = () => (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Generate Literature Review
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Research Topic"
                value={reviewForm.topic}
                onChange={(e) => setReviewForm({ ...reviewForm, topic: e.target.value })}
                placeholder="Enter your research topic"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                select
                label="Review Scope"
                value={reviewForm.scope}
                onChange={(e) => setReviewForm({ ...reviewForm, scope: e.target.value })}
                SelectProps={{ native: true }}
              >
                <option value="comprehensive">Comprehensive</option>
                <option value="focused">Focused</option>
                <option value="brief">Brief</option>
              </TextField>
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                type="number"
                label="Max Sources"
                value={reviewForm.max_sources}
                onChange={(e) => setReviewForm({ ...reviewForm, max_sources: parseInt(e.target.value) })}
                inputProps={{ min: 10, max: 100 }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Research Questions (one per line)"
                value={reviewForm.research_questions}
                onChange={(e) => setReviewForm({ ...reviewForm, research_questions: e.target.value })}
                placeholder="What is the impact of...?&#10;How does X affect Y?&#10;Why do researchers..."
              />
            </Grid>
            <Grid item xs={12}>
              <Button
                variant="contained"
                onClick={generateLiteratureReview}
                disabled={loading || !reviewForm.topic || !reviewForm.research_questions}
                startIcon={loading ? <CircularProgress size={20} /> : <BookIcon />}
              >
                Generate Literature Review
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {literatureReview && (
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
              <Typography variant="h6">Literature Review: {literatureReview.topic}</Typography>
              <Box>
                <Button startIcon={<DownloadIcon />} size="small" sx={{ mr: 1 }}>
                  Export
                </Button>
                <Button startIcon={<ShareIcon />} size="small">
                  Share
                </Button>
              </Box>
            </Box>
            
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1">Synthesis</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="body2" paragraph>
                  {literatureReview.synthesis}
                </Typography>
              </AccordionDetails>
            </Accordion>
            
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1">Key Themes ({literatureReview.themes.length})</Typography>
              </AccordionSummary>
              <AccordionDetails>
                {literatureReview.themes.map((theme, idx) => (
                  <Paper key={idx} sx={{ p: 2, mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>{theme.name}</Typography>
                    <Typography variant="body2" paragraph>{theme.description}</Typography>
                    <Box>
                      <Typography variant="caption">Keywords: </Typography>
                      {theme.keywords.slice(0, 5).map((keyword: string, kidx: number) => (
                        <Chip key={kidx} label={keyword} size="small" sx={{ mr: 0.5 }} />
                      ))}
                    </Box>
                  </Paper>
                ))}
              </AccordionDetails>
            </Accordion>
            
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1">Research Gaps Identified</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <List>
                  {literatureReview.gaps_identified.map((gap, idx) => (
                    <ListItem key={idx}>
                      <ListItemText primary={gap} />
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
            
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1">Recommendations</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <List>
                  {literatureReview.recommendations.map((rec, idx) => (
                    <ListItem key={idx}>
                      <ListItemText primary={rec} />
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
            
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1">Sources ({literatureReview.sources.length})</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="body2" gutterBottom>
                  Quality Assessment: {literatureReview.quality_assessment.overall_quality} 
                  (Average Score: {literatureReview.quality_assessment.average_score?.toFixed(2)})
                </Typography>
                <List>
                  {literatureReview.sources.slice(0, 10).map((source, idx) => (
                    <ListItem key={idx}>
                      <ListItemText 
                        primary={source.title}
                        secondary={`Relevance: ${source.relevance_score?.toFixed(2)} | Quality: ${source.quality_score?.toFixed(2)}`}
                      />
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
          </CardContent>
        </Card>
      )}
    </Box>
  );

  const renderResearchProposal = () => (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Generate Research Proposal
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Research Topic"
                value={proposalForm.topic}
                onChange={(e) => setProposalForm({ ...proposalForm, topic: e.target.value })}
                placeholder="Enter your research topic"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Methodology Preference (optional)"
                value={proposalForm.methodology_preference}
                onChange={(e) => setProposalForm({ ...proposalForm, methodology_preference: e.target.value })}
                placeholder="e.g., quantitative, qualitative, mixed_methods"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Research Questions (one per line)"
                value={proposalForm.research_questions}
                onChange={(e) => setProposalForm({ ...proposalForm, research_questions: e.target.value })}
                placeholder="What is the relationship between...?&#10;How does X influence Y?&#10;What are the factors..."
              />
            </Grid>
            <Grid item xs={12}>
              <Button
                variant="contained"
                onClick={generateResearchProposal}
                disabled={loading || !proposalForm.topic || !proposalForm.research_questions}
                startIcon={loading ? <CircularProgress size={20} /> : <AssignmentIcon />}
              >
                Generate Research Proposal
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {researchProposal && (
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
              <Typography variant="h5">{researchProposal.title}</Typography>
              <Box>
                <Button startIcon={<DownloadIcon />} size="small" sx={{ mr: 1 }}>
                  Export PDF
                </Button>
                <Button startIcon={<ShareIcon />} size="small">
                  Share
                </Button>
              </Box>
            </Box>
            
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">Abstract</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="body1" paragraph>
                  {researchProposal.abstract}
                </Typography>
              </AccordionDetails>
            </Accordion>
            
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">Introduction</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="body1" paragraph>
                  {researchProposal.introduction}
                </Typography>
              </AccordionDetails>
            </Accordion>
            
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">Research Questions & Hypotheses</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="subtitle1" gutterBottom>Research Questions:</Typography>
                <List>
                  {researchProposal.research_questions.map((question, idx) => (
                    <ListItem key={idx}>
                      <ListItemText primary={`${idx + 1}. ${question}`} />
                    </ListItem>
                  ))}
                </List>
                
                <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>Hypotheses:</Typography>
                <List>
                  {researchProposal.hypotheses.map((hypothesis, idx) => (
                    <ListItem key={idx}>
                      <ListItemText primary={`${idx + 1}. ${hypothesis}`} />
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
            
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">Methodology</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1" gutterBottom>Approach:</Typography>
                    <Typography variant="body2" paragraph>
                      {researchProposal.methodology.approach}
                    </Typography>
                    
                    <Typography variant="subtitle1" gutterBottom>Design:</Typography>
                    <Typography variant="body2" paragraph>
                      {researchProposal.methodology.design}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1" gutterBottom>Data Collection:</Typography>
                    <List dense>
                      {researchProposal.methodology.data_collection?.methods?.map((method: string, idx: number) => (
                        <ListItem key={idx}>
                          <ListItemText primary={method} />
                        </ListItem>
                      ))}
                    </List>
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
            
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">Timeline & Budget</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1" gutterBottom>Timeline:</Typography>
                    <Typography variant="body2" gutterBottom>
                      Total Duration: {researchProposal.timeline.total_duration_months} months
                    </Typography>
                    {researchProposal.timeline.phases?.map((phase: any, idx: number) => (
                      <Paper key={idx} sx={{ p: 1, mb: 1 }}>
                        <Typography variant="body2">
                          <strong>{phase.phase}:</strong> Months {phase.start_month}-{phase.end_month}
                        </Typography>
                      </Paper>
                    ))}
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1" gutterBottom>Budget:</Typography>
                    <Typography variant="body2" gutterBottom>
                      Total Estimated: ${researchProposal.budget.total_estimated?.toLocaleString()}
                    </Typography>
                    {Object.entries(researchProposal.budget.categories || {}).map(([category, details]: [string, any]) => (
                      <Paper key={category} sx={{ p: 1, mb: 1 }}>
                        <Typography variant="body2">
                          <strong>{category.replace('_', ' ').toUpperCase()}:</strong> ${details.amount?.toLocaleString()}
                        </Typography>
                        <Typography variant="caption">{details.description}</Typography>
                      </Paper>
                    ))}
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
            
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">Expected Outcomes & Limitations</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="subtitle1" gutterBottom>Expected Outcomes:</Typography>
                <List>
                  {researchProposal.expected_outcomes.map((outcome, idx) => (
                    <ListItem key={idx}>
                      <ListItemText primary={outcome} />
                    </ListItem>
                  ))}
                </List>
                
                <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>Limitations:</Typography>
                <List>
                  {researchProposal.limitations.map((limitation, idx) => (
                    <ListItem key={idx}>
                      <ListItemText primary={limitation} />
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
            
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">Ethical Considerations</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="body1">
                  {researchProposal.ethical_considerations}
                </Typography>
              </AccordionDetails>
            </Accordion>
          </CardContent>
        </Card>
      )}
    </Box>
  );

  const renderMethodologyAdvice = () => (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Get Methodology Advice
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Research Domain"
                value={methodologyForm.domain}
                onChange={(e) => setMethodologyForm({ ...methodologyForm, domain: e.target.value })}
                placeholder="e.g., Computer Science, Psychology"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Research Questions (one per line)"
                value={methodologyForm.research_questions}
                onChange={(e) => setMethodologyForm({ ...methodologyForm, research_questions: e.target.value })}
                placeholder="What is the effect of...?&#10;How do users respond to...?&#10;What factors influence..."
              />
            </Grid>
            <Grid item xs={12}>
              <Button
                variant="contained"
                onClick={getMethodologyAdvice}
                disabled={loading || !methodologyForm.domain || !methodologyForm.research_questions}
                startIcon={loading ? <CircularProgress size={20} /> : <ScienceIcon />}
              >
                Get Methodology Advice
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {methodologyAdvice && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Methodology Recommendations</Typography>
            
            <Alert severity="info" sx={{ mb: 2 }}>
              {methodologyAdvice.detailed_advice?.overview}
            </Alert>
            
            <Typography variant="subtitle1" gutterBottom>Top Recommendations:</Typography>
            {methodologyAdvice.recommendations?.slice(0, 3).map((rec: any, idx: number) => (
              <Card key={idx} variant="outlined" sx={{ mb: 2 }}>
                <CardContent>
                  <Box display="flex" justifyContent="between" alignItems="center" mb={1}>
                    <Typography variant="h6">
                      {rec.methodology.replace('_', ' ').toUpperCase()}
                    </Typography>
                    <Chip 
                      label={`${(rec.suitability_score * 100).toFixed(0)}% suitable`}
                      color={rec.suitability_score > 0.7 ? 'success' : rec.suitability_score > 0.5 ? 'warning' : 'default'}
                    />
                  </Box>
                  
                  <Typography variant="body2" paragraph>
                    {rec.rationale}
                  </Typography>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" color="success.main">Advantages:</Typography>
                      <List dense>
                        {rec.advantages.map((adv: string, aidx: number) => (
                          <ListItem key={aidx} sx={{ py: 0 }}>
                            <ListItemText primary={`• ${adv}`} />
                          </ListItem>
                        ))}
                      </List>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" color="warning.main">Disadvantages:</Typography>
                      <List dense>
                        {rec.disadvantages.map((dis: string, didx: number) => (
                          <ListItem key={didx} sx={{ py: 0 }}>
                            <ListItemText primary={`• ${dis}`} />
                          </ListItem>
                        ))}
                      </List>
                    </Grid>
                  </Grid>
                  
                  <Divider sx={{ my: 2 }} />
                  
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2">
                        <strong>Duration:</strong> {rec.estimated_duration} months
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2">
                        <strong>Complexity:</strong> {rec.complexity_level}
                      </Typography>
                    </Grid>
                  </Grid>
                  
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    <strong>Sample Size Guidance:</strong> {rec.sample_size_guidance}
                  </Typography>
                  
                  <Box mt={2}>
                    <Typography variant="subtitle2" gutterBottom>Recommended Tools:</Typography>
                    <Box display="flex" flexWrap="wrap" gap={0.5}>
                      {rec.tools_recommended.map((tool: string, tidx: number) => (
                        <Chip key={tidx} label={tool} size="small" />
                      ))}
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            ))}
          </CardContent>
        </Card>
      )}
    </Box>
  );

  const renderDataAnalysisGuidance = () => (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Get Data Analysis Guidance
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Research Question"
                value={analysisForm.research_question}
                onChange={(e) => setAnalysisForm({ ...analysisForm, research_question: e.target.value })}
                placeholder="What is the relationship between X and Y?"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Data Description"
                value={analysisForm.data_description}
                onChange={(e) => setAnalysisForm({ ...analysisForm, data_description: e.target.value })}
                placeholder="Survey responses, experimental data, etc."
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                type="number"
                label="Sample Size"
                value={analysisForm.sample_size}
                onChange={(e) => setAnalysisForm({ ...analysisForm, sample_size: parseInt(e.target.value) })}
                inputProps={{ min: 1 }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                select
                label="Data Type"
                value={analysisForm.data_type}
                onChange={(e) => setAnalysisForm({ ...analysisForm, data_type: e.target.value })}
                SelectProps={{ native: true }}
              >
                <option value="mixed">Mixed</option>
                <option value="quantitative">Quantitative</option>
                <option value="qualitative">Qualitative</option>
                <option value="categorical">Categorical</option>
                <option value="continuous">Continuous</option>
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <Button
                variant="contained"
                onClick={getDataAnalysisGuidance}
                disabled={loading || !analysisForm.research_question || !analysisForm.data_description}
                startIcon={loading ? <CircularProgress size={20} /> : <AnalyticsIcon />}
              >
                Get Analysis Guidance
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {dataAnalysisGuidance && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Data Analysis Guidance</Typography>
            
            <Typography variant="subtitle1" gutterBottom>Research Question:</Typography>
            <Typography variant="body1" paragraph>
              {dataAnalysisGuidance.research_question}
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" gutterBottom>Recommended Methods:</Typography>
                <Box display="flex" flexWrap="wrap" gap={0.5} mb={2}>
                  {dataAnalysisGuidance.recommended_methods?.map((method: string, idx: number) => (
                    <Chip key={idx} label={method.replace('_', ' ')} />
                  ))}
                </Box>
                
                <Typography variant="subtitle1" gutterBottom>Statistical Tests:</Typography>
                <List dense>
                  {dataAnalysisGuidance.statistical_tests?.map((test: string, idx: number) => (
                    <ListItem key={idx}>
                      <ListItemText primary={test} />
                    </ListItem>
                  ))}
                </List>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" gutterBottom>Software Tools:</Typography>
                <Box display="flex" flexWrap="wrap" gap={0.5} mb={2}>
                  {dataAnalysisGuidance.software_tools?.map((tool: string, idx: number) => (
                    <Chip key={idx} label={tool} variant="outlined" />
                  ))}
                </Box>
                
                <Typography variant="subtitle1" gutterBottom>Visualization Suggestions:</Typography>
                <List dense>
                  {dataAnalysisGuidance.visualization_suggestions?.map((viz: string, idx: number) => (
                    <ListItem key={idx}>
                      <ListItemText primary={viz} />
                    </ListItem>
                  ))}
                </List>
              </Grid>
            </Grid>
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="subtitle1" gutterBottom>Statistical Assumptions:</Typography>
            <List dense>
              {dataAnalysisGuidance.assumptions?.map((assumption: string, idx: number) => (
                <ListItem key={idx}>
                  <ListItemText primary={assumption} />
                </ListItem>
              ))}
            </List>
            
            <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>Interpretation Guidelines:</Typography>
            <Typography variant="body2" paragraph>
              {dataAnalysisGuidance.interpretation_guidelines}
            </Typography>
            
            <Typography variant="subtitle1" gutterBottom>Reporting Standards:</Typography>
            <List dense>
              {dataAnalysisGuidance.reporting_standards?.map((standard: string, idx: number) => (
                <ListItem key={idx}>
                  <ListItemText primary={standard} />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}
    </Box>
  );

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h4" gutterBottom>
        Research Assistant
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Get comprehensive research assistance including topic generation, literature reviews, 
        research proposals, methodology advice, and data analysis guidance.
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="research assistant tabs">
          <Tab label="Research Topics" icon={<ScienceIcon />} />
          <Tab label="Literature Review" icon={<BookIcon />} />
          <Tab label="Research Proposal" icon={<AssignmentIcon />} />
          <Tab label="Methodology Advice" icon={<ScienceIcon />} />
          <Tab label="Data Analysis" icon={<AnalyticsIcon />} />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        {renderResearchTopics()}
      </TabPanel>
      <TabPanel value={tabValue} index={1}>
        {renderLiteratureReview()}
      </TabPanel>
      <TabPanel value={tabValue} index={2}>
        {renderResearchProposal()}
      </TabPanel>
      <TabPanel value={tabValue} index={3}>
        {renderMethodologyAdvice()}
      </TabPanel>
      <TabPanel value={tabValue} index={4}>
        {renderDataAnalysisGuidance()}
      </TabPanel>
    </Box>
  );
};

export default ResearchAssistant;