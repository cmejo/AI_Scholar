import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  List,
  ListItem,
  ListItemText,
  Avatar,
  Paper,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert,
  Divider,
  Tooltip,
  Badge
} from '@mui/material';
import {
  Send as SendIcon,
  Psychology as PsychologyIcon,
  Person as PersonIcon,
  MoreVert as MoreVertIcon,
  Add as AddIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  QuestionAnswer as QuestionAnswerIcon,
  Lightbulb as LightbulbIcon,
  BookmarkBorder as BookmarkIcon,
  Share as ShareIcon
} from '@mui/icons-material';
import { useApi } from '../../hooks/useApi';
import { useNotification } from '../../hooks/useNotification';

interface ChatMessage {
  id: string;
  message_type: string;
  content: string;
  context?: string;
  timestamp: string;
  confidence_score?: number;
  sources?: string[];
  suggestions?: string[];
  metadata?: any;
}

interface ChatSession {
  id: string;
  title: string;
  context: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  message_count: number;
  messages: ChatMessage[];
}

interface ResearchAnswer {
  answer: string;
  confidence: number;
  sources: string[];
  related_concepts: string[];
  follow_up_questions: string[];
  methodology_suggestions: string[];
  context: string;
}

const RESEARCH_CONTEXTS = {
  'general_research': { name: 'General Research', icon: '🔬', color: '#1976d2' },
  'literature_review': { name: 'Literature Review', icon: '📚', color: '#388e3c' },
  'methodology_design': { name: 'Methodology Design', icon: '⚙️', color: '#f57c00' },
  'data_analysis': { name: 'Data Analysis', icon: '📊', color: '#7b1fa2' },
  'hypothesis_testing': { name: 'Hypothesis Testing', icon: '🧪', color: '#d32f2f' },
  'concept_exploration': { name: 'Concept Exploration', icon: '💡', color: '#0288d1' }
};

const AIResearchChat: React.FC = () => {
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [sessions, setSessions] = useState<any[]>([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [contextMenuAnchor, setContextMenuAnchor] = useState<null | HTMLElement>(null);
  const [newSessionDialog, setNewSessionDialog] = useState(false);
  const [selectedContext, setSelectedContext] = useState('general_research');
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { apiCall } = useApi();
  const { showNotification } = useNotification();

  useEffect(() => {
    loadUserSessions();
    loadSuggestedQuestions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [currentSession?.messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadUserSessions = async () => {
    try {
      const userSessions = await apiCall('/api/chat/sessions', 'GET');
      setSessions(userSessions);
      
      // If no current session and sessions exist, load the most recent one
      if (!currentSession && userSessions.length > 0) {
        await loadSession(userSessions[0].id);
      }
    } catch (error) {
      showNotification('Failed to load chat sessions', 'error');
    }
  };

  const loadSession = async (sessionId: string) => {
    try {
      setLoading(true);
      const session = await apiCall(`/api/chat/session/${sessionId}`, 'GET');
      setCurrentSession(session);
    } catch (error) {
      showNotification('Failed to load chat session', 'error');
    } finally {
      setLoading(false);
    }
  };

  const startNewSession = async () => {
    try {
      setLoading(true);
      const session = await apiCall('/api/chat/start', 'POST', {
        context: selectedContext,
        title: `${RESEARCH_CONTEXTS[selectedContext as keyof typeof RESEARCH_CONTEXTS]?.name} Chat`
      });
      
      setCurrentSession(session);
      setSessions(prev => [session, ...prev]);
      setNewSessionDialog(false);
      showNotification('New chat session started', 'success');
    } catch (error) {
      showNotification('Failed to start new session', 'error');
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!message.trim() || !currentSession || loading) return;

    const userMessage = message;
    setMessage('');
    setLoading(true);

    try {
      const answer = await apiCall('/api/chat/ask', 'POST', {
        session_id: currentSession.id,
        question: userMessage
      });

      // Reload the session to get updated messages
      await loadSession(currentSession.id);
      
      // Update suggestions if provided
      if (answer.follow_up_questions?.length > 0) {
        setSuggestedQuestions(answer.follow_up_questions);
        setShowSuggestions(true);
      }

    } catch (error) {
      showNotification('Failed to send message', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadSuggestedQuestions = async () => {
    try {
      const suggestions = await apiCall('/api/chat/suggest-questions', 'POST', selectedContext);
      setSuggestedQuestions(suggestions);
    } catch (error) {
      console.warn('Failed to load suggested questions');
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setMessage(suggestion);
    setShowSuggestions(false);
  };

  const formatMessageContent = (content: string) => {
    // Simple markdown-like formatting
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br/>');
  };

  const renderMessage = (msg: ChatMessage, index: number) => {
    const isUser = msg.message_type === 'user_question';
    const isSystem = msg.message_type === 'system_message';
    
    return (
      <ListItem
        key={msg.id}
        sx={{
          flexDirection: 'column',
          alignItems: isUser ? 'flex-end' : 'flex-start',
          mb: 2
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'flex-start',
            maxWidth: '80%',
            flexDirection: isUser ? 'row-reverse' : 'row'
          }}
        >
          <Avatar
            sx={{
              bgcolor: isUser ? 'primary.main' : isSystem ? 'grey.500' : 'secondary.main',
              mx: 1,
              width: 32,
              height: 32
            }}
          >
            {isUser ? <PersonIcon /> : <PsychologyIcon />}
          </Avatar>
          
          <Paper
            elevation={1}
            sx={{
              p: 2,
              bgcolor: isUser ? 'primary.light' : isSystem ? 'grey.100' : 'background.paper',
              color: isUser ? 'primary.contrastText' : 'text.primary',
              borderRadius: 2,
              maxWidth: '100%'
            }}
          >
            <Typography
              variant="body1"
              dangerouslySetInnerHTML={{
                __html: formatMessageContent(msg.content)
              }}
            />
            
            {msg.confidence_score && (
              <Box mt={1}>
                <Chip
                  size="small"
                  label={`Confidence: ${(msg.confidence_score * 100).toFixed(0)}%`}
                  color={msg.confidence_score > 0.7 ? 'success' : 'warning'}
                />
              </Box>
            )}
            
            {msg.sources && msg.sources.length > 0 && (
              <Box mt={1}>
                <Typography variant="caption" color="text.secondary">
                  Sources: {msg.sources.join(', ')}
                </Typography>
              </Box>
            )}
            
            {msg.suggestions && msg.suggestions.length > 0 && (
              <Box mt={1}>
                <Typography variant="caption" color="text.secondary" gutterBottom>
                  Follow-up questions:
                </Typography>
                {msg.suggestions.map((suggestion, idx) => (
                  <Chip
                    key={idx}
                    size="small"
                    label={suggestion}
                    onClick={() => handleSuggestionClick(suggestion)}
                    sx={{ mr: 0.5, mb: 0.5, cursor: 'pointer' }}
                    variant="outlined"
                  />
                ))}
              </Box>
            )}
            
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              {new Date(msg.timestamp).toLocaleTimeString()}
            </Typography>
          </Paper>
        </Box>
      </ListItem>
    );
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex' }}>
      {/* Sidebar */}
      <Box sx={{ width: 300, borderRight: 1, borderColor: 'divider', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Button
            fullWidth
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setNewSessionDialog(true)}
          >
            New Chat
          </Button>
        </Box>
        
        <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
          <List>
            {sessions.map((session) => (
              <ListItem
                key={session.id}
                button
                selected={currentSession?.id === session.id}
                onClick={() => loadSession(session.id)}
                sx={{
                  borderRadius: 1,
                  mx: 1,
                  mb: 0.5
                }}
              >
                <ListItemText
                  primary={session.title}
                  secondary={
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        {RESEARCH_CONTEXTS[session.context as keyof typeof RESEARCH_CONTEXTS]?.name}
                      </Typography>
                      <br />
                      <Typography variant="caption" color="text.secondary">
                        {session.message_count} messages
                      </Typography>
                    </Box>
                  }
                />
                <Badge
                  badgeContent={session.message_count}
                  color="primary"
                  sx={{ mr: 1 }}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      </Box>

      {/* Main Chat Area */}
      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        {currentSession ? (
          <>
            {/* Chat Header */}
            <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider', display: 'flex', alignItems: 'center' }}>
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="h6">
                  {RESEARCH_CONTEXTS[currentSession.context as keyof typeof RESEARCH_CONTEXTS]?.icon}{' '}
                  {currentSession.title}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {currentSession.message_count} messages • Active since {new Date(currentSession.created_at).toLocaleDateString()}
                </Typography>
              </Box>
              
              <IconButton
                onClick={(e) => setContextMenuAnchor(e.currentTarget)}
              >
                <MoreVertIcon />
              </IconButton>
              
              <Menu
                anchorEl={contextMenuAnchor}
                open={Boolean(contextMenuAnchor)}
                onClose={() => setContextMenuAnchor(null)}
              >
                <MenuItem onClick={() => setContextMenuAnchor(null)}>
                  <BookmarkIcon sx={{ mr: 1 }} />
                  Bookmark Session
                </MenuItem>
                <MenuItem onClick={() => setContextMenuAnchor(null)}>
                  <ShareIcon sx={{ mr: 1 }} />
                  Share Session
                </MenuItem>
                <MenuItem onClick={() => setContextMenuAnchor(null)}>
                  <HistoryIcon sx={{ mr: 1 }} />
                  Export History
                </MenuItem>
              </Menu>
            </Box>

            {/* Messages */}
            <Box sx={{ flexGrow: 1, overflow: 'auto', p: 1 }}>
              <List>
                {currentSession.messages.map((msg, index) => renderMessage(msg, index))}
                {loading && (
                  <ListItem sx={{ justifyContent: 'center' }}>
                    <CircularProgress size={24} />
                    <Typography variant="body2" sx={{ ml: 1 }}>
                      AI is thinking...
                    </Typography>
                  </ListItem>
                )}
              </List>
              <div ref={messagesEndRef} />
            </Box>

            {/* Suggestions */}
            {showSuggestions && suggestedQuestions.length > 0 && (
              <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', bgcolor: 'grey.50' }}>
                <Typography variant="subtitle2" gutterBottom>
                  <LightbulbIcon sx={{ fontSize: 16, mr: 0.5 }} />
                  Suggested questions:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {suggestedQuestions.slice(0, 3).map((suggestion, index) => (
                    <Chip
                      key={index}
                      label={suggestion}
                      onClick={() => handleSuggestionClick(suggestion)}
                      size="small"
                      variant="outlined"
                      sx={{ cursor: 'pointer' }}
                    />
                  ))}
                </Box>
              </Box>
            )}

            {/* Message Input */}
            <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  multiline
                  maxRows={4}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me anything about your research..."
                  disabled={loading}
                  variant="outlined"
                  size="small"
                />
                <Button
                  variant="contained"
                  onClick={sendMessage}
                  disabled={!message.trim() || loading}
                  sx={{ minWidth: 'auto', px: 2 }}
                >
                  <SendIcon />
                </Button>
              </Box>
            </Box>
          </>
        ) : (
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
            <Card sx={{ maxWidth: 400, textAlign: 'center' }}>
              <CardContent>
                <PsychologyIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
                <Typography variant="h5" gutterBottom>
                  AI Research Assistant
                </Typography>
                <Typography variant="body1" color="text.secondary" paragraph>
                  Start a new conversation to get help with your research questions, methodology, literature reviews, and more.
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => setNewSessionDialog(true)}
                >
                  Start New Chat
                </Button>
              </CardContent>
            </Card>
          </Box>
        )}
      </Box>

      {/* New Session Dialog */}
      <Dialog open={newSessionDialog} onClose={() => setNewSessionDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Start New Research Chat</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" paragraph>
            Choose a research context to get specialized assistance:
          </Typography>
          
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 1, mt: 2 }}>
            {Object.entries(RESEARCH_CONTEXTS).map(([key, context]) => (
              <Card
                key={key}
                sx={{
                  cursor: 'pointer',
                  border: selectedContext === key ? 2 : 1,
                  borderColor: selectedContext === key ? 'primary.main' : 'divider',
                  '&:hover': { borderColor: 'primary.main' }
                }}
                onClick={() => setSelectedContext(key)}
              >
                <CardContent sx={{ textAlign: 'center', py: 2 }}>
                  <Typography variant="h4" sx={{ mb: 1 }}>
                    {context.icon}
                  </Typography>
                  <Typography variant="subtitle2">
                    {context.name}
                  </Typography>
                </CardContent>
              </Card>
            ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewSessionDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={startNewSession}
            disabled={loading}
          >
            {loading ? <CircularProgress size={20} /> : 'Start Chat'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AIResearchChat;