import React, { useState, useRef } from 'react';
import { Send, Menu, MessageSquare, FileText, BarChart3, Settings, User, Shield, Zap, Puzzle, Brain, LogIn, UserPlus, LogOut } from 'lucide-react';
import ScientificRAG from './components/ScientificRAG';

type ViewType = 'chat' | 'documents' | 'analytics' | 'workflows' | 'integrations' | 'security' | 'rag' | 'profile' | 'settings';

const App: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentView, setCurrentView] = useState<ViewType>('chat');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<{ name: string; email: string } | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [messages, setMessages] = useState([
    {
      id: '1',
      content: 'Hello! I\'m your AI Scholar assistant with advanced workflow and integration capabilities. How can I help you today?',
      sender: 'assistant' as const,
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [showEditProfile, setShowEditProfile] = useState(false);
  const [editProfileData, setEditProfileData] = useState({ name: '', email: '', bio: '' });
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const generateIntelligentResponse = (userInput: string, conversationHistory: any[]) => {
    const lowerInput = userInput.toLowerCase();
    
    // Get the last few messages for context
    const recentMessages = conversationHistory.slice(-10);
    const lastAssistantMessage = recentMessages.filter(m => m.sender === 'assistant').pop();
    const lastUserMessage = recentMessages.filter(m => m.sender === 'user').slice(-2, -1)[0]; // Previous user message
    
    // Enhanced context detection
    const isInIntegrationContext = lastAssistantMessage?.content.includes('integration selected') || 
                                   lastAssistantMessage?.content.includes('workflow activated') ||
                                   lastAssistantMessage?.content.includes('Let\'s set up') ||
                                   lastAssistantMessage?.content.includes('Step 1:') ||
                                   lastAssistantMessage?.content.includes('What type of');
    
    const isInSetupContext = lastAssistantMessage?.content.includes('Step 1:') ||
                            lastAssistantMessage?.content.includes('Step 2:') ||
                            lastAssistantMessage?.content.includes('configuration') ||
                            lastAssistantMessage?.content.includes('Which type of');
    
    const isInQuestionContext = lastAssistantMessage?.content.includes('?') &&
                               (lastAssistantMessage?.content.includes('What') ||
                                lastAssistantMessage?.content.includes('Which') ||
                                lastAssistantMessage?.content.includes('How') ||
                                lastAssistantMessage?.content.includes('Would you like'));
    
    // Enhanced contextual responses for follow-up questions
    if (isInQuestionContext && !lowerInput.match(/^(yes|no|help|what|how|which)/)) {
      // Handle specific answers to questions
      if (lastAssistantMessage?.content.includes('Which type of AI model interests you')) {
        if (lowerInput.includes('text') || lowerInput.includes('generation') || lowerInput.includes('writing')) {
          return "📝 **Text Generation Models - Perfect Choice!**\n\n**Recommended Models:**\n• **GPT-2** - Great for creative writing and completion\n• **T5** - Excellent for text-to-text tasks\n• **BART** - Perfect for summarization and paraphrasing\n• **DialoGPT** - Specialized for conversational AI\n\n**Setup Process:**\n1. **Model Selection**: I recommend starting with GPT-2 for simplicity\n2. **API Configuration**: Set up your Hugging Face token\n3. **Testing**: We'll run a simple text generation test\n4. **Integration**: Connect to your application\n\n**Next Steps:**\n• Configure API endpoints\n• Set generation parameters (temperature, max_length)\n• Test with sample prompts\n\nShall I help you configure GPT-2 for text generation?";
        }
        if (lowerInput.includes('image') || lowerInput.includes('vision') || lowerInput.includes('visual')) {
          return "🖼️ **Image Analysis Models - Excellent Choice!**\n\n**Recommended Models:**\n• **CLIP** - Image and text understanding\n• **BLIP** - Image captioning and VQA\n• **DETR** - Object detection\n• **ViT** - Vision transformer for classification\n\n**Capabilities:**\n• Image classification and tagging\n• Object detection and counting\n• Image captioning and description\n• Visual question answering\n• Content moderation\n\n**Setup Process:**\n1. **Model Selection**: CLIP is most versatile for beginners\n2. **Image Processing**: Configure input formats\n3. **Testing**: Upload sample images\n4. **Integration**: Connect to your workflow\n\nWould you like to start with CLIP for image analysis?";
        }
        if (lowerInput.includes('sentiment') || lowerInput.includes('emotion') || lowerInput.includes('analysis')) {
          return "😊 **Sentiment Analysis Models - Great Choice!**\n\n**Recommended Models:**\n• **RoBERTa-sentiment** - High accuracy sentiment detection\n• **VADER** - Social media sentiment analysis\n• **TextBlob** - Simple sentiment scoring\n• **DistilBERT** - Fast and efficient analysis\n\n**Use Cases:**\n• Customer feedback analysis\n• Social media monitoring\n• Product review analysis\n• Content moderation\n• Market research\n\n**Setup Process:**\n1. **Model Selection**: RoBERTa for best accuracy\n2. **Text Preprocessing**: Clean and prepare data\n3. **Testing**: Analyze sample texts\n4. **Integration**: Connect to your data sources\n\nShall I help you set up RoBERTa for sentiment analysis?";
        }
      }
      
      if (lastAssistantMessage?.content.includes('What\'s your primary use case for OpenAI')) {
        if (lowerInput.includes('code') || lowerInput.includes('programming') || lowerInput.includes('development')) {
          return "💻 **Code Assistant Setup - Perfect!**\n\n**OpenAI Code Features:**\n• Code completion and suggestions\n• Bug detection and fixing\n• Code explanation and documentation\n• Language translation (Python ↔ JavaScript, etc.)\n• Code review and optimization\n\n**Recommended Configuration:**\n• **Model**: GPT-4 (best for code)\n• **Temperature**: 0.2 (more deterministic)\n• **Max tokens**: 1500 (good for code blocks)\n• **System prompt**: \"You are a helpful coding assistant\"\n\n**Integration Options:**\n• VS Code extension\n• API integration in your IDE\n• Command-line tool\n• Web-based code editor\n\nWhich development environment do you use? (VS Code, PyCharm, etc.)";
        }
        if (lowerInput.includes('content') || lowerInput.includes('writing') || lowerInput.includes('blog')) {
          return "✍️ **Content Creation Setup - Excellent!**\n\n**OpenAI Content Features:**\n• Blog post generation\n• Marketing copy creation\n• Social media content\n• Email templates\n• Creative writing assistance\n\n**Recommended Configuration:**\n• **Model**: GPT-4 or GPT-3.5-turbo\n• **Temperature**: 0.7 (balanced creativity)\n• **Max tokens**: 2000 (longer content)\n• **System prompt**: \"You are a creative writing assistant\"\n\n**Content Types:**\n• Blog articles and posts\n• Product descriptions\n• Social media captions\n• Email newsletters\n• Creative stories\n\nWhat type of content do you create most often?";
        }
      }
      
      // Handle specific technology/tool mentions
      if (lowerInput.includes('python') || lowerInput.includes('javascript') || lowerInput.includes('react')) {
        return `🔧 **${lowerInput.includes('python') ? 'Python' : lowerInput.includes('javascript') ? 'JavaScript' : 'React'} Integration - Great Choice!**\n\nI can help you integrate AI capabilities into your ${lowerInput.includes('python') ? 'Python' : lowerInput.includes('javascript') ? 'JavaScript' : 'React'} project:\n\n**Integration Options:**\n• REST API calls to AI services\n• SDK and library integration\n• Real-time processing\n• Batch processing workflows\n\n**Code Examples:**\n• API authentication setup\n• Request/response handling\n• Error handling and retries\n• Data preprocessing\n\nWould you like me to show you specific code examples for ${lowerInput.includes('python') ? 'Python' : lowerInput.includes('javascript') ? 'JavaScript' : 'React'}?`;
      }
    }

    // Positive responses
    if (lowerInput.match(/^(yes|yeah|yep|sure|ok|okay|sounds good|let's do it|go ahead|proceed|continue|start|begin|setup|configure|install|connect)$/)) {
      if (isInIntegrationContext || isInSetupContext) {
        if (lastAssistantMessage?.content.includes('Hugging Face')) {
          return "🤗 Excellent! Let's set up Hugging Face integration:\n\n**Step 1: API Setup**\n• Visit https://huggingface.co/settings/tokens\n• Create a new access token\n• Copy your token for configuration\n\n**Step 2: Model Selection**\n• Browse 100,000+ models at https://huggingface.co/models\n• Popular choices: BERT, GPT-2, T5, CLIP\n• Filter by task: text-generation, sentiment-analysis, etc.\n\n**Step 3: Integration**\n• I'll help you connect the API\n• Test with a simple model first\n• Scale to production models\n\nWhich type of AI model interests you most? (text generation, image analysis, sentiment analysis, etc.)";
        }
        if (lastAssistantMessage?.content.includes('OpenAI')) {
          return "🤖 Perfect! Let's configure OpenAI GPT integration:\n\n**Step 1: API Key Setup**\n• Get your API key from https://platform.openai.com/api-keys\n• Choose your model: GPT-4, GPT-3.5-turbo, or GPT-4-turbo\n• Set usage limits and billing\n\n**Step 2: Configuration**\n• Temperature: 0.7 (balanced creativity)\n• Max tokens: 2000 (response length)\n• System prompts for specific tasks\n\n**Step 3: Use Cases**\n• Text generation and completion\n• Code assistance and debugging\n• Content analysis and summarization\n• Creative writing and brainstorming\n\nWhat's your primary use case for OpenAI integration?";
        }
        if (lastAssistantMessage?.content.includes('Slack')) {
          return "🔗 Great choice! Let's set up Slack AI integration:\n\n**Step 1: Slack App Creation**\n• Go to https://api.slack.com/apps\n• Create new app for your workspace\n• Configure bot permissions and scopes\n\n**Step 2: AI Features**\n• Smart message responses\n• Automated workflow triggers\n• Meeting summary generation\n• Task and reminder management\n\n**Step 3: Deployment**\n• Install app to your workspace\n• Configure channels and permissions\n• Test AI responses and commands\n\nWhich Slack channels should the AI monitor? (general, support, dev, etc.)";
        }
        if (lastAssistantMessage?.content.includes('workflow')) {
          return "⚡ Fantastic! Let's build your AI workflow:\n\n**Step 1: Define Inputs**\n• What triggers the workflow? (file upload, schedule, API call)\n• What data formats? (PDF, images, text, etc.)\n• Any specific requirements or constraints?\n\n**Step 2: Processing Steps**\n• AI analysis and extraction\n• Data transformation and enrichment\n• Quality checks and validation\n\n**Step 3: Outputs**\n• Where should results go? (database, email, Slack)\n• What format? (JSON, CSV, reports)\n• Any notifications or alerts needed?\n\nWhat type of data will you be processing with this workflow?";
        }
        return "🚀 Excellent! I'm ready to help you set this up. Let me guide you through the configuration process step by step. What specific aspect would you like to start with first?";
      }
      return "Great! I'm here to help. What would you like to work on? I can assist with:\n\n• Setting up AI integrations (OpenAI, Hugging Face, etc.)\n• Creating automated workflows\n• Analyzing documents and data\n• Building custom AI solutions\n\nWhat interests you most?";
    }
    
    // Negative responses
    if (lowerInput.match(/^(no|nope|not now|maybe later|cancel|stop|exit|quit)$/)) {
      return "No problem! I'm here whenever you're ready. Feel free to explore the other integrations and workflows, or ask me any questions about AI Scholar's capabilities.";
    }
    
    // Help requests
    if (lowerInput.includes('help') || lowerInput.includes('how') || lowerInput.includes('what')) {
      if (lowerInput.includes('integration')) {
        return "🔌 **AI Integrations Help:**\n\nI can help you connect with 18+ AI services:\n\n**Popular Integrations:**\n• 🤖 OpenAI GPT - Advanced language models\n• 🧠 Anthropic Claude - Safe AI conversations\n• 🤗 Hugging Face - 100,000+ open-source models\n• ☁️ AWS Bedrock - Enterprise AI models\n\n**Setup Process:**\n1. Choose an integration from the Integrations tab\n2. I'll guide you through API setup\n3. Configure settings for your use case\n4. Test and deploy\n\nWhich integration would you like to explore?";
      }
      if (lowerInput.includes('workflow')) {
        return "⚡ **AI Workflows Help:**\n\nI can help you create 16+ automated workflows:\n\n**Popular Workflows:**\n• 🤖 Smart Document Processing - OCR & analysis\n• 🧠 Research Pipeline - Automated research\n• 💬 Customer Support - AI ticket management\n• 📊 Content Analytics - Intelligent insights\n\n**Creation Process:**\n1. Select a workflow template\n2. Configure inputs and triggers\n3. Set up AI processing steps\n4. Define outputs and notifications\n\nWhat type of workflow interests you?";
      }
      return "🤖 **AI Scholar Help:**\n\nI'm your AI assistant for:\n\n**🔌 Integrations:** Connect with 18+ AI services\n**⚡ Workflows:** Create 16+ automated processes\n**📄 Documents:** Upload, analyze, and manage files\n**📊 Analytics:** View performance and insights\n**🛡️ Security:** Monitor and protect your data\n\nWhat would you like help with?";
    }
    
    // Specific integration questions
    if (lowerInput.includes('openai') || lowerInput.includes('gpt')) {
      return "🤖 **OpenAI GPT Integration:**\n\n**Capabilities:**\n• Text generation and completion\n• Code assistance and debugging\n• Language translation\n• Content analysis and summarization\n\n**Models Available:**\n• GPT-4 - Most capable, best for complex tasks\n• GPT-3.5-turbo - Fast and cost-effective\n• GPT-4-turbo - Latest with improved performance\n\n**Pricing:** Pay-per-use, starting at $0.002/1K tokens\n\nWould you like me to help you set up OpenAI integration?";
    }
    
    if (lowerInput.includes('hugging face') || lowerInput.includes('models')) {
      return "🤗 **Hugging Face Integration:**\n\n**What You Get:**\n• 100,000+ pre-trained AI models\n• Open-source and free options\n• Custom model fine-tuning\n• Datasets and model hosting\n\n**Popular Models:**\n• BERT - Text understanding\n• GPT-2 - Text generation\n• CLIP - Image and text\n• T5 - Text-to-text tasks\n\n**Perfect For:** Research, experimentation, custom AI solutions\n\nInterested in exploring specific model types?";
    }
    
    // File upload and document-specific responses
    if (lowerInput.includes('upload') || lowerInput.includes('file') || lowerInput.includes('document') || lowerInput.includes('pdf') || lowerInput.includes('ocr')) {
      return "📄 **Document Upload & Processing:**\n\n**Supported File Types:**\n• 📄 PDF - Text extraction, OCR, table analysis\n• 📝 Word (.doc, .docx) - Content analysis, structure extraction\n• 📊 Excel (.xls, .xlsx) - Data analysis, chart extraction\n• 📄 Text (.txt, .csv) - NLP analysis, data processing\n• 🖼️ Images (.jpg, .png, .gif) - OCR, object detection\n\n**What I can do with your files:**\n• Extract and summarize content\n• Analyze data and generate insights\n• Create knowledge graphs from documents\n• Search across multiple files\n• Compare and contrast documents\n• Generate reports and summaries\n\n**To get started:**\n• Drag & drop files into the chat\n• Click the 📎 icon to select files\n• Upload up to 10MB per file\n\nTry uploading a document and I'll analyze it for you!";
    }
    
    // File analysis responses
    if (lowerInput.includes('analyze') || lowerInput.includes('extract') || lowerInput.includes('summarize') || lowerInput.includes('content')) {
      const hasFiles = conversationHistory.some(m => m.content.includes('Files Uploaded Successfully'));
      if (hasFiles) {
        return "🔍 **File Analysis Options:**\n\n**Content Analysis:**\n• Extract key topics and themes\n• Identify important entities (people, places, organizations)\n• Generate executive summaries\n• Create bullet-point highlights\n\n**Data Analysis:**\n• Statistical analysis of numerical data\n• Chart and graph generation\n• Trend identification\n• Comparative analysis\n\n**Advanced Features:**\n• Sentiment analysis of text content\n• Knowledge graph creation\n• Cross-document search\n• Citation and reference extraction\n\nWhat type of analysis would you like me to perform on your uploaded files?";
      }
      return "📊 I can analyze various types of content! Upload some files first, and I'll help you:\n\n• Extract key information\n• Generate summaries\n• Identify patterns and insights\n• Create visualizations\n• Compare multiple documents\n\nDrag & drop files or click the 📎 icon to get started!";
    }

    // Search and query responses
    if (lowerInput.includes('search') || lowerInput.includes('find') || lowerInput.includes('look for')) {
      const hasFiles = conversationHistory.some(m => m.content.includes('Files Uploaded Successfully'));
      if (hasFiles) {
        return "🔍 **Smart Search Capabilities:**\n\n**What I can search for:**\n• Specific keywords or phrases\n• Concepts and topics\n• Names, dates, and locations\n• Technical terms and definitions\n• Data patterns and trends\n\n**Search Examples:**\n• \"Find all mentions of budget\"\n• \"What are the key findings?\"\n• \"Show me the methodology section\"\n• \"Extract all contact information\"\n• \"Find similar documents\"\n\nWhat would you like me to search for in your uploaded files?";
      }
      return "🔍 I can perform intelligent searches across your documents! Upload some files first, and I'll help you find:\n\n• Specific information and keywords\n• Related concepts and topics\n• Important data points\n• Cross-references between documents\n\nUpload files to enable smart search!";
    }

    // Default intelligent response based on context
    if (isInIntegrationContext) {
      return "I understand you're interested in this integration. Here are some next steps:\n\n• **Setup Guide:** I can walk you through the configuration\n• **Use Cases:** Explore practical applications\n• **Best Practices:** Learn optimization tips\n• **Troubleshooting:** Get help with common issues\n\nWhat specific aspect would you like to explore?";
    }
    
    // General intelligent responses
    const responses = [
      "That's interesting! Could you tell me more about what you're trying to accomplish? I can suggest the best AI integrations or workflows for your needs.",
      "I'd be happy to help with that! Are you looking to automate a specific process, analyze data, or integrate with particular AI services?",
      "Great question! Based on your needs, I can recommend specific integrations or workflows. What's your main goal with AI Scholar?",
      "I can definitely assist with that. Would you like to explore our AI integrations, create automated workflows, or analyze some documents?",
      "Excellent! Let me help you find the right solution. Are you interested in text analysis, document processing, or perhaps setting up AI automations?"
    ];
    
    return responses[Math.floor(Math.random() * responses.length)];
  };

  const sendMessage = () => {
    if (!input.trim()) return;
    
    const userMessage = {
      id: Date.now().toString(),
      content: input,
      sender: 'user' as const,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    
    // Generate intelligent response
    setTimeout(() => {
      const intelligentResponse = generateIntelligentResponse(currentInput, messages);
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        content: intelligentResponse,
        sender: 'assistant' as const,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
    }, 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // File upload handlers
  const handleFileUpload = async (files: FileList | File[]) => {
    const fileArray = Array.from(files);
    const validFiles = fileArray.filter(file => {
      const validTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp'
      ];
      return validTypes.includes(file.type) && file.size <= 10 * 1024 * 1024; // 10MB limit
    });

    if (validFiles.length === 0) {
      alert('Please upload valid files (PDF, Word, Excel, Text, Images) under 10MB');
      return;
    }

    setIsUploading(true);
    setUploadedFiles(prev => [...prev, ...validFiles]);

    // Simulate file processing
    setTimeout(() => {
      const fileNames = validFiles.map(f => f.name).join(', ');
      const fileTypes = [...new Set(validFiles.map(f => f.type.split('/')[1]))].join(', ');
      
      const analysisMessage = {
        id: Date.now().toString(),
        content: `📄 **Files Uploaded Successfully!**\n\n**Files:** ${fileNames}\n**Types:** ${fileTypes}\n**Total Size:** ${(validFiles.reduce((acc, f) => acc + f.size, 0) / 1024 / 1024).toFixed(2)} MB\n\n🤖 **AI Analysis Complete:**\n\n${generateFileAnalysis(validFiles)}\n\n**What would you like me to do with these files?**\n• Extract and summarize content\n• Analyze data and generate insights\n• Create knowledge graphs\n• Search for specific information\n• Compare documents\n\nJust ask me anything about your uploaded files!`,
        sender: 'assistant' as const,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, analysisMessage]);
      setIsUploading(false);
    }, 2000);
  };

  const generateFileAnalysis = (files: File[]) => {
    const analyses = files.map(file => {
      const type = file.type;
      const name = file.name;
      
      if (type.includes('pdf')) {
        return `📄 **${name}**\n• Document type: PDF\n• Estimated pages: ${Math.ceil(file.size / 50000)}\n• Content detected: Text, possible images/tables\n• OCR ready for text extraction`;
      } else if (type.includes('word')) {
        return `📝 **${name}**\n• Document type: Word Document\n• Estimated content: ${Math.ceil(file.size / 2000)} words\n• Structure: Headers, paragraphs, formatting\n• Ready for content analysis`;
      } else if (type.includes('excel') || type.includes('csv')) {
        return `📊 **${name}**\n• Document type: Spreadsheet\n• Estimated rows: ${Math.ceil(file.size / 100)}\n• Data analysis ready\n• Can extract tables, charts, formulas`;
      } else if (type.includes('image')) {
        return `🖼️ **${name}**\n• Image type: ${type.split('/')[1].toUpperCase()}\n• Size: ${(file.size / 1024).toFixed(0)} KB\n• OCR ready for text extraction\n• Object detection available`;
      } else if (type.includes('text')) {
        return `📄 **${name}**\n• Document type: Plain Text\n• Estimated content: ${Math.ceil(file.size / 5)} words\n• Ready for NLP analysis\n• Sentiment and topic analysis available`;
      }
      return `📁 **${name}**\n• File type: ${type}\n• Size: ${(file.size / 1024).toFixed(0)} KB\n• Processing available`;
    });
    
    return analyses.join('\n\n');
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFileUpload(files);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files);
    }
    // Reset input
    e.target.value = '';
  };

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  // Profile management functions
  const refreshProfile = async () => {
    if (!isAuthenticated) return;
    
    setIsLoadingProfile(true);
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('http://localhost:8080/api/auth/profile', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser({
          name: userData.name || userData.full_name || 'Admin User',
          email: userData.email || 'admin@redditaeo.com'
        });
        
        // Add success message to chat
        const successMessage = {
          id: Date.now().toString(),
          content: '✅ Profile refreshed successfully! Your latest information is now displayed.',
          sender: 'assistant' as const,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, successMessage]);
      } else {
        throw new Error('Failed to fetch profile');
      }
    } catch (error) {
      console.error('Profile refresh error:', error);
      const errorMessage = {
        id: Date.now().toString(),
        content: '❌ Failed to refresh profile. Please try logging in again.',
        sender: 'assistant' as const,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoadingProfile(false);
    }
  };

  const updateProfile = async () => {
    if (!isAuthenticated) return;
    
    setIsLoadingProfile(true);
    try {
      const token = localStorage.getItem('auth_token');
      
      // Validate input
      if (!editProfileData.name.trim() || !editProfileData.email.trim()) {
        throw new Error('Name and email are required');
      }
      
      const response = await fetch('http://localhost:8080/api/auth/profile', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: editProfileData.name.trim(),
          email: editProfileData.email.trim(),
          bio: editProfileData.bio.trim() || undefined
        })
      });
      
      if (response.ok) {
        // Update user state with new data
        setUser({
          name: editProfileData.name.trim(),
          email: editProfileData.email.trim()
        });
        
        // Close modal
        setShowEditProfile(false);
        
        // Add success message to chat
        const successMessage = {
          id: Date.now().toString(),
          content: `✅ Profile updated successfully! Your information has been saved.\n\n**Updated:**\n• Name: ${editProfileData.name}\n• Email: ${editProfileData.email}\n• Bio: ${editProfileData.bio || 'Not specified'}`,
          sender: 'assistant' as const,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, successMessage]);
        
        // Switch to chat view to show the message
        setCurrentView('chat');
      } else {
        // If backend fails, still update the UI (demo mode)
        console.warn('Backend update failed, updating UI only');
        
        // Update user state with new data anyway
        setUser({
          name: editProfileData.name.trim(),
          email: editProfileData.email.trim()
        });
        
        // Close modal
        setShowEditProfile(false);
        
        // Add success message to chat
        const successMessage = {
          id: Date.now().toString(),
          content: `✅ Profile updated locally! Your information has been updated in the interface.\n\n**Updated:**\n• Name: ${editProfileData.name}\n• Email: ${editProfileData.email}\n• Bio: ${editProfileData.bio || 'Not specified'}\n\n*Note: Changes are saved locally. For persistent storage, ensure backend connection.*`,
          sender: 'assistant' as const,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, successMessage]);
        
        // Switch to chat view to show the message
        setCurrentView('chat');
      }
    } catch (error) {
      console.error('Profile update error:', error);
      
      // Show error message in chat
      const errorMessage = {
        id: Date.now().toString(),
        content: `❌ Failed to update profile: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`,
        sender: 'assistant' as const,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      
      // Close modal and switch to chat to show error
      setShowEditProfile(false);
      setCurrentView('chat');
    } finally {
      setIsLoadingProfile(false);
    }
  };

  const openEditProfile = () => {
    setEditProfileData({
      name: user?.name || '',
      email: user?.email || '',
      bio: ''
    });
    setShowEditProfile(true);
  };

  // Auto-scroll to bottom when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleLogin = async () => {
    try {
      // Simulate login API call
      const response = await fetch('http://localhost:8080/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'admin@redditaeo.com',
          password: 'Admin123!'
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setIsAuthenticated(true);
        setUser({ name: data.user?.name || 'Admin User', email: data.user?.email || 'admin@redditaeo.com' });
        setShowAuthModal(false);
        
        // Add success message
        const successMessage = {
          id: Date.now().toString(),
          content: '✅ Successfully logged in! You now have access to all AI Scholar features.',
          sender: 'assistant' as const,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, successMessage]);
      } else {
        alert('Login failed. Please try again.');
      }
    } catch (error) {
      alert('Login error. Please check your connection.');
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setUser(null);
    setCurrentView('chat');
    
    // Add logout message
    const logoutMessage = {
      id: Date.now().toString(),
      content: '👋 You have been logged out. Some features may be limited.',
      sender: 'assistant' as const,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, logoutMessage]);
  };

  const renderSidebar = () => (
    <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-gray-800 transform ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0`}>
      <div className="flex items-center justify-center h-16 bg-gray-900">
        <h1 className="text-xl font-bold text-white">🚀 AI Scholar</h1>
      </div>
      
      {/* User Status */}
      <div className="px-4 py-3 bg-gray-700 border-b border-gray-600">
        {isAuthenticated ? (
          <div className="flex items-center">
            <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
              {user?.name?.charAt(0) || 'U'}
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-white">{user?.name}</p>
              <p className="text-xs text-gray-400">{user?.email}</p>
            </div>
          </div>
        ) : (
          <div className="text-center">
            <p className="text-sm text-gray-400">Not logged in</p>
          </div>
        )}
      </div>

      <nav className="mt-5 px-2">
        <div className="space-y-1">
          {/* Main Navigation */}
          {[
            { id: 'chat', name: 'Chat', icon: MessageSquare, requiresAuth: false },
            { id: 'rag', name: 'Scientific RAG', icon: Brain, requiresAuth: false },
            { id: 'documents', name: 'Documents', icon: FileText, requiresAuth: false },
            { id: 'analytics', name: 'Analytics', icon: BarChart3, requiresAuth: false },
            { id: 'workflows', name: 'Workflows', icon: Zap, requiresAuth: false },
            { id: 'integrations', name: 'Integrations', icon: Puzzle, requiresAuth: false },
            { id: 'security', name: 'Security', icon: Shield, requiresAuth: true },
            { id: 'profile', name: 'Profile', icon: User, requiresAuth: true },
            { id: 'settings', name: 'Settings', icon: Settings, requiresAuth: false }
          ].map((item) => {
            const Icon = item.icon;
            const isDisabled = item.requiresAuth && !isAuthenticated;
            return (
              <button
                key={item.id}
                onClick={() => {
                  console.log(`Sidebar button clicked: ${item.name} (${item.id})`);
                  if (isDisabled) {
                    setShowAuthModal(true);
                    return;
                  }
                  setCurrentView(item.id as ViewType);
                  setSidebarOpen(false);
                }}
                className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md w-full ${
                  currentView === item.id
                    ? 'bg-gray-900 text-white'
                    : isDisabled
                    ? 'text-gray-500 cursor-not-allowed'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
                disabled={isDisabled}
              >
                <Icon className="mr-3 h-5 w-5" />
                {item.name}
                {isDisabled && <span className="ml-auto text-xs">🔒</span>}
              </button>
            );
          })}
        </div>

        {/* Authentication Section */}
        <div className="mt-8 pt-4 border-t border-gray-600">
          <div className="space-y-1">
            {!isAuthenticated ? (
              <>
                <button
                  onClick={() => {
                    setAuthMode('login');
                    setShowAuthModal(true);
                  }}
                  className="group flex items-center px-2 py-2 text-sm font-medium rounded-md w-full text-gray-300 hover:bg-gray-700 hover:text-white"
                >
                  <LogIn className="mr-3 h-5 w-5" />
                  Sign In
                </button>
                <button
                  onClick={() => {
                    setAuthMode('register');
                    setShowAuthModal(true);
                  }}
                  className="group flex items-center px-2 py-2 text-sm font-medium rounded-md w-full text-gray-300 hover:bg-gray-700 hover:text-white"
                >
                  <UserPlus className="mr-3 h-5 w-5" />
                  Sign Up
                </button>
              </>
            ) : (
              <button
                onClick={handleLogout}
                className="group flex items-center px-2 py-2 text-sm font-medium rounded-md w-full text-gray-300 hover:bg-gray-700 hover:text-white"
              >
                <LogOut className="mr-3 h-5 w-5" />
                Sign Out
              </button>
            )}
          </div>
        </div>
      </nav>
    </div>
  );

  const renderHeader = () => (
    <div className="bg-gray-800 shadow-sm lg:static lg:overflow-y-visible">
      <div className="mx-auto px-4 sm:px-6 lg:px-8">
        <div className="relative flex justify-between xl:grid xl:grid-cols-12 lg:gap-8">
          <div className="flex md:absolute md:left-0 md:inset-y-0 lg:static xl:col-span-2">
            <div className="flex-shrink-0 flex items-center">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-purple-500 lg:hidden"
              >
                <Menu className="h-6 w-6" />
              </button>
            </div>
          </div>
          <div className="min-w-0 flex-1 md:px-8 lg:px-0 xl:col-span-6">
            <div className="flex items-center px-6 py-4 md:max-w-3xl md:mx-auto lg:max-w-none lg:mx-0 xl:px-0">
              <div className="w-full">
                <h1 className="text-lg font-medium text-white">
                  {currentView === 'chat' && 'AI Chat Assistant'}
                  {currentView === 'rag' && 'Scientific RAG'}
                  {currentView === 'documents' && 'Document Manager'}
                  {currentView === 'analytics' && 'Analytics Dashboard'}
                  {currentView === 'workflows' && 'AI Workflows'}
                  {currentView === 'integrations' && 'AI Integrations'}
                  {currentView === 'security' && 'Security Dashboard'}
                  {currentView === 'settings' && 'Settings'}
                  {currentView === 'profile' && 'User Profile'}
                </h1>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderChatView = () => (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.sender === 'user'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-700 text-gray-100'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              <p className="text-xs mt-1 opacity-70">
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        
        {/* Loading indicator */}
        {isUploading && (
          <div className="flex justify-start">
            <div className="bg-gray-700 text-gray-100 max-w-xs lg:max-w-md px-4 py-3 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-purple-500 border-t-transparent"></div>
                <span className="text-sm">Processing your files...</span>
              </div>
            </div>
          </div>
        )}
        
        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </div>
      
      <div 
        className={`p-4 border-t border-gray-700 relative ${dragActive ? 'bg-purple-900/20 border-purple-500' : ''}`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        {/* Uploaded Files Display */}
        {uploadedFiles.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-2">
            {uploadedFiles.map((file, index) => (
              <div key={index} className="flex items-center bg-gray-700 rounded-lg px-3 py-1 text-sm">
                <span className="mr-2">
                  {file.type.includes('pdf') && '📄'}
                  {file.type.includes('word') && '📝'}
                  {file.type.includes('excel') && '📊'}
                  {file.type.includes('csv') && '📊'}
                  {file.type.includes('image') && '🖼️'}
                  {file.type.includes('text') && '📄'}
                </span>
                <span className="text-gray-300 truncate max-w-32">{file.name}</span>
                <button
                  onClick={() => removeFile(index)}
                  className="ml-2 text-gray-400 hover:text-red-400 transition-colors"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Drag & Drop Overlay */}
        {dragActive && (
          <div className="absolute inset-0 bg-purple-600/20 border-2 border-dashed border-purple-500 rounded-lg flex items-center justify-center z-10">
            <div className="text-center text-purple-300">
              <div className="text-4xl mb-2">📁</div>
              <p className="text-lg font-medium">Drop files here to upload</p>
              <p className="text-sm">PDF, Word, Excel, Images, Text files</p>
            </div>
          </div>
        )}

        <div className="flex space-x-2 mb-2">
          <div className="flex-1 relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask me about documents, or drag & drop files to upload..."
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 pr-12 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              disabled={isUploading}
            />
            
            {/* File Upload Button */}
            <label className="absolute right-2 top-1/2 transform -translate-y-1/2 cursor-pointer">
              <input
                type="file"
                multiple
                accept=".pdf,.doc,.docx,.txt,.csv,.xls,.xlsx,.jpg,.jpeg,.png,.gif,.webp"
                onChange={handleFileInputChange}
                className="hidden"
                disabled={isUploading}
              />
              <div className={`p-1 rounded hover:bg-gray-700 transition-colors ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}>
                {isUploading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-purple-500 border-t-transparent"></div>
                ) : (
                  <svg className="w-4 h-4 text-gray-400 hover:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                  </svg>
                )}
              </div>
            </label>
          </div>
          
          <button
            onClick={sendMessage}
            disabled={isUploading || (!input.trim() && uploadedFiles.length === 0)}
            className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white p-2 rounded-lg transition-colors"
          >
            {isUploading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Help Text */}
        <div className="text-xs text-gray-500 flex items-center justify-between">
          <span>📎 Drag & drop files or click 📎 to upload • Supports: PDF, Word, Excel, Images, Text</span>
          <span>Enter to send • Shift+Enter for new line</span>
        </div>
      </div>
    </div>
  );

  const renderAuthModal = () => {
    if (!showAuthModal) return null;

    return (
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
          <div className="fixed inset-0 transition-opacity" onClick={() => setShowAuthModal(false)}>
            <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
          </div>

          <div className="inline-block align-bottom bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
            <div className="bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <div className="sm:flex sm:items-start">
                <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                  <h3 className="text-lg leading-6 font-medium text-white mb-4">
                    {authMode === 'login' ? 'Sign In to AI Scholar' : 'Create AI Scholar Account'}
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300">Email</label>
                      <input
                        type="email"
                        defaultValue="admin@redditaeo.com"
                        className="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="Enter your email"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-300">Password</label>
                      <input
                        type="password"
                        defaultValue="Admin123!"
                        className="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="Enter your password"
                      />
                    </div>

                    {authMode === 'register' && (
                      <div>
                        <label className="block text-sm font-medium text-gray-300">Full Name</label>
                        <input
                          type="text"
                          className="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                          placeholder="Enter your full name"
                        />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                onClick={handleLogin}
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-purple-600 text-base font-medium text-white hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 sm:ml-3 sm:w-auto sm:text-sm"
              >
                {authMode === 'login' ? 'Sign In' : 'Create Account'}
              </button>
              <button
                onClick={() => setShowAuthModal(false)}
                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-600 shadow-sm px-4 py-2 bg-gray-800 text-base font-medium text-gray-300 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
              >
                Cancel
              </button>
            </div>
            
            <div className="bg-gray-700 px-4 py-2 text-center">
              <button
                onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}
                className="text-sm text-purple-400 hover:text-purple-300"
              >
                {authMode === 'login' ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'chat':
        return renderChatView();
      case 'rag':
        return <ScientificRAG />;
      case 'documents':
        return (
          <div className="p-6 text-white">
            <h2 className="text-2xl font-bold mb-4">📄 Document Manager</h2>
            <p>Upload, analyze, and manage your research documents with AI-powered insights.</p>
            
            <div className="mt-6 mb-6 flex space-x-4">
              <button
                onClick={() => {
                  alert('📤 Upload Document feature activated!');
                  const message = {
                    id: Date.now().toString(),
                    content: '📤 Document Upload ready! I can process PDFs, Word docs, images, and more. Upload your documents and I\'ll extract text, analyze content, and provide intelligent insights. What would you like to upload?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                📤 Upload Documents
              </button>
              
              <button
                onClick={() => {
                  alert('🔍 AI Analysis feature activated!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🔍 AI Document Analysis activated! I can analyze document sentiment, extract key topics, identify entities, and generate summaries. Ready to analyze your documents with AI?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                🔍 AI Analysis
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <button
                onClick={() => {
                  alert('📋 Recent Documents opened!');
                  const message = {
                    id: Date.now().toString(),
                    content: '📋 Recent Documents: research_paper.pdf (analyzed), meeting_notes.docx (processed), data_report.xlsx (insights ready). Which document would you like to work with?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">📋 Recent Documents</h3>
                <p className="text-sm text-gray-400">View and manage recently processed files</p>
                <div className="mt-3 text-xs text-purple-400">View All →</div>
              </button>

              <button
                onClick={() => {
                  alert('🏷️ Smart Tags opened!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🏷️ Smart Tags: AI has automatically tagged your documents - Research (23), Legal (8), Technical (15), Financial (12). Want to explore documents by category?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🏷️ Smart Tags</h3>
                <p className="text-sm text-gray-400">AI-generated document categories and tags</p>
                <div className="mt-3 text-xs text-purple-400">Browse Tags →</div>
              </button>

              <button
                onClick={() => {
                  alert('🔍 Search & Insights opened!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🔍 Search & Insights: Semantic search across all documents enabled! Ask me questions like "Find documents about AI ethics" or "Show financial projections from Q3". What are you looking for?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🔍 Search & Insights</h3>
                <p className="text-sm text-gray-400">Semantic search and AI-powered insights</p>
                <div className="mt-3 text-xs text-purple-400">Search Now →</div>
              </button>
            </div>

            {!isAuthenticated && (
              <div className="mt-6 p-4 bg-gray-800 rounded-lg">
                <p className="text-gray-400">Sign in to access document management features and upload files.</p>
                <button
                  onClick={() => setShowAuthModal(true)}
                  className="mt-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded text-sm"
                >
                  Sign In to Upload
                </button>
              </div>
            )}
          </div>
        );
      case 'analytics':
        return (
          <div className="p-6 text-white">
            <h2 className="text-2xl font-bold mb-4">📊 Analytics Dashboard</h2>
            <p>View insights, performance metrics, and usage analytics for your AI workflows.</p>
            
            <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-2xl font-bold text-purple-400">1,247</h3>
                <p className="text-sm text-gray-400">Total Workflows</p>
              </div>
              <div className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-2xl font-bold text-green-400">98.5%</h3>
                <p className="text-sm text-gray-400">Success Rate</p>
              </div>
              <div className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-2xl font-bold text-blue-400">24.7s</h3>
                <p className="text-sm text-gray-400">Avg Processing</p>
              </div>
              <div className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-2xl font-bold text-yellow-400">15</h3>
                <p className="text-sm text-gray-400">Active Integrations</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <button
                onClick={() => {
                  alert('📈 Performance Analytics opened!');
                  const message = {
                    id: Date.now().toString(),
                    content: '📈 Performance Analytics: Your workflows are running at 98.5% success rate! Top performing workflow: Smart Document Processing (2.3s avg). Would you like detailed performance insights?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-6 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">📈 Performance Analytics</h3>
                <p className="text-sm text-gray-400">Workflow execution metrics and optimization insights</p>
                <div className="mt-3 text-xs text-purple-400">View Details →</div>
              </button>

              <button
                onClick={() => {
                  alert('👥 User Activity opened!');
                  const message = {
                    id: Date.now().toString(),
                    content: '👥 User Activity: 47 active users this week, 312 workflow executions, peak usage at 2-4 PM. Most popular feature: AI Chat Assistant. Need user engagement insights?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-6 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">👥 User Activity</h3>
                <p className="text-sm text-gray-400">User engagement and usage patterns</p>
                <div className="mt-3 text-xs text-purple-400">View Details →</div>
              </button>
            </div>

            {!isAuthenticated && (
              <div className="mt-6 p-4 bg-gray-800 rounded-lg">
                <p className="text-gray-400">Sign in to access detailed analytics and custom reports.</p>
                <button
                  onClick={() => setShowAuthModal(true)}
                  className="mt-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded text-sm"
                >
                  Sign In for Full Access
                </button>
              </div>
            )}
          </div>
        );
      case 'workflows':
        return (
          <div className="p-6 text-white">
            <h2 className="text-2xl font-bold mb-4">⚡ AI Workflows</h2>
            <p>Create, manage, and optimize AI-powered automation workflows.</p>
            
            <div className="mt-6 mb-6">
              <button
                onClick={() => {
                  alert('🚀 Creating new workflow! This would open the workflow builder.');
                  const message = {
                    id: Date.now().toString(),
                    content: '🚀 Workflow Builder activated! I can help you create AI-powered workflows for document processing, research automation, and content analysis.',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                + Create New Workflow
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Document & Content Processing */}
              <button
                onClick={() => {
                  alert('🤖 Smart Document Processing workflow selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🤖 Smart Document Processing workflow activated! This workflow can automatically extract text from PDFs, classify documents, and analyze content using AI. Would you like me to set this up for you?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🤖 Smart Document Processing</h3>
                <p className="text-sm text-gray-400">Automated OCR, classification, and analysis</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-green-400">⭐ Popular</span>
                  <span className="text-xs text-purple-400">Activate →</span>
                </div>
              </button>

              <button
                onClick={() => {
                  alert('📄 PDF Intelligence workflow selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '📄 PDF Intelligence workflow activated! Extract tables, images, metadata, and structured data from PDFs. Includes form recognition, signature detection, and multi-language support. Ready to process PDFs?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">📄 PDF Intelligence</h3>
                <p className="text-sm text-gray-400">Advanced PDF extraction & analysis</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-blue-400">📋 Forms</span>
                  <span className="text-xs text-purple-400">Activate →</span>
                </div>
              </button>

              <button
                onClick={() => {
                  alert('📊 Content Analytics workflow selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '📊 Content Analytics workflow activated! This workflow analyzes content patterns, sentiment, and engagement metrics. Let me help you set up intelligent content insights!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">📊 Content Analytics</h3>
                <p className="text-sm text-gray-400">Intelligent content insights</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-yellow-400">📈 Analytics</span>
                  <span className="text-xs text-purple-400">Activate →</span>
                </div>
              </button>

              {/* Research & Knowledge */}
              <button
                onClick={() => {
                  alert('🧠 Research Pipeline workflow selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🧠 Research Pipeline workflow activated! This workflow can automatically gather research data, analyze sources, and generate insights. Ready to set up your research automation?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🧠 Research Pipeline</h3>
                <p className="text-sm text-gray-400">AI-powered research automation</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-green-400">🔬 Research</span>
                  <span className="text-xs text-purple-400">Activate →</span>
                </div>
              </button>

              <button
                onClick={() => {
                  alert('🕸️ Knowledge Graph Builder workflow selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🕸️ Knowledge Graph Builder workflow activated! Automatically extract entities, relationships, and build knowledge graphs from your documents. Perfect for research synthesis and discovery!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🕸️ Knowledge Graph Builder</h3>
                <p className="text-sm text-gray-400">Entity extraction & relationship mapping</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-purple-400">🔗 Connections</span>
                  <span className="text-xs text-purple-400">Activate →</span>
                </div>
              </button>

              <button
                onClick={() => {
                  alert('📚 Literature Review Automation workflow selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '📚 Literature Review Automation workflow activated! Automatically search academic databases, analyze papers, extract key findings, and generate comprehensive literature reviews. Accelerate your research!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">📚 Literature Review Automation</h3>
                <p className="text-sm text-gray-400">Academic paper analysis & synthesis</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-blue-400">🎓 Academic</span>
                  <span className="text-xs text-purple-400">Activate →</span>
                </div>
              </button>

              {/* Communication & Social */}
              <button
                onClick={() => {
                  alert('💬 Smart Customer Support workflow selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '💬 Smart Customer Support workflow activated! AI-powered ticket classification, sentiment analysis, auto-responses, and escalation management. Enhance your customer service with AI!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">💬 Smart Customer Support</h3>
                <p className="text-sm text-gray-400">AI-powered ticket management</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-green-400">🎯 Support</span>
                  <span className="text-xs text-purple-400">Activate →</span>
                </div>
              </button>

              <button
                onClick={() => {
                  alert('📱 Social Media Intelligence workflow selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '📱 Social Media Intelligence workflow activated! Monitor mentions, analyze sentiment, track trends, and generate automated responses across social platforms. Boost your social presence!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">📱 Social Media Intelligence</h3>
                <p className="text-sm text-gray-400">Social monitoring & engagement</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-pink-400">📢 Social</span>
                  <span className="text-xs text-purple-400">Activate →</span>
                </div>
              </button>

              <button
                onClick={() => {
                  alert('📧 Email Intelligence workflow selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '📧 Email Intelligence workflow activated! Smart email classification, priority detection, auto-responses, and follow-up reminders. Transform your email productivity with AI!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">📧 Email Intelligence</h3>
                <p className="text-sm text-gray-400">Smart email management & automation</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-blue-400">📬 Productivity</span>
                  <span className="text-xs text-purple-400">Activate →</span>
                </div>
              </button>

              {/* Business & Finance */}
              <button
                onClick={() => {
                  alert('💰 Financial Document Analysis workflow selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '💰 Financial Document Analysis workflow activated! Extract data from invoices, receipts, financial statements, and contracts. Includes fraud detection and compliance checking. Automate your finance workflows!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">💰 Financial Document Analysis</h3>
                <p className="text-sm text-gray-400">Invoice, receipt & contract processing</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-green-400">💵 Finance</span>
                  <span className="text-xs text-purple-400">Activate →</span>
                </div>
              </button>

              <button
                onClick={() => {
                  alert('📈 Market Intelligence workflow selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '📈 Market Intelligence workflow activated! Monitor market trends, analyze competitor data, track news sentiment, and generate market reports. Stay ahead with AI-powered market insights!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">📈 Market Intelligence</h3>
                <p className="text-sm text-gray-400">Competitive analysis & trend monitoring</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-yellow-400">📊 Business</span>
                  <span className="text-xs text-purple-400">Activate →</span>
                </div>
              </button>

              {/* Development & Technical */}
              <button
                onClick={() => {
                  alert('🔧 Code Review Automation workflow selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🔧 Code Review Automation workflow activated! Automated code analysis, security scanning, performance optimization suggestions, and documentation generation. Enhance your development workflow!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🔧 Code Review Automation</h3>
                <p className="text-sm text-gray-400">AI-powered code analysis & optimization</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-green-400">💻 DevOps</span>
                  <span className="text-xs text-purple-400">Activate →</span>
                </div>
              </button>

              <button
                onClick={() => {
                  alert('🚨 Security Monitoring workflow selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🚨 Security Monitoring workflow activated! Real-time threat detection, vulnerability scanning, incident response automation, and security report generation. Protect your systems with AI!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🚨 Security Monitoring</h3>
                <p className="text-sm text-gray-400">Threat detection & incident response</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-red-400">🛡️ Security</span>
                  <span className="text-xs text-purple-400">Activate →</span>
                </div>
              </button>

              {/* Creative & Media */}
              <button
                onClick={() => {
                  alert('🎨 Creative Content Generator workflow selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🎨 Creative Content Generator workflow activated! Generate blog posts, social media content, marketing copy, and creative assets using AI. Includes image generation and video scripting!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🎨 Creative Content Generator</h3>
                <p className="text-sm text-gray-400">AI-powered content creation</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-pink-400">🎭 Creative</span>
                  <span className="text-xs text-purple-400">Activate →</span>
                </div>
              </button>

              <button
                onClick={() => {
                  alert('🎬 Video Intelligence workflow selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🎬 Video Intelligence workflow activated! Automatic video transcription, scene detection, object recognition, and content moderation. Extract insights from video content with AI!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🎬 Video Intelligence</h3>
                <p className="text-sm text-gray-400">Video analysis & content extraction</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-red-400">🎥 Media</span>
                  <span className="text-xs text-purple-400">Activate →</span>
                </div>
              </button>
            </div>
          </div>
        );
      case 'integrations':
        return (
          <div className="p-6 text-white">
            <h2 className="text-2xl font-bold mb-4">🔌 AI Integrations</h2>
            <p>Connect with powerful AI services and tools to enhance your workflows.</p>
            
            <div className="mt-6 mb-6">
              <button
                onClick={() => {
                  alert('🔍 Opening Integration Catalog! Browse 50+ AI integrations.');
                  const message = {
                    id: Date.now().toString(),
                    content: '🔍 Integration Catalog opened! I can help you connect with OpenAI, Anthropic Claude, AWS Bedrock, Slack, and 50+ other AI services. Which integration interests you most?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                🔍 Browse All Integrations
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* AI & Machine Learning */}
              <button
                onClick={() => {
                  alert('🤖 OpenAI GPT integration selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🤖 OpenAI GPT integration selected! This provides access to GPT-4, text generation, code completion, and analysis. Would you like me to help you set up the API connection?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🤖 OpenAI GPT</h3>
                <p className="text-sm text-gray-400">Advanced language models</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-green-400">✅ Popular</span>
                  <span className="text-xs text-purple-400">Connect →</span>
                </div>
              </button>

              <button
                onClick={() => {
                  alert('🧠 Anthropic Claude integration selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🧠 Anthropic Claude integration selected! Constitutional AI for safe, helpful conversations. Perfect for content analysis, research assistance, and ethical AI interactions. Ready to connect?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🧠 Anthropic Claude</h3>
                <p className="text-sm text-gray-400">Constitutional AI assistant</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-green-400">🛡️ Safe AI</span>
                  <span className="text-xs text-purple-400">Connect →</span>
                </div>
              </button>

              <button
                onClick={() => {
                  alert('🤗 Hugging Face integration selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🤗 Hugging Face integration selected! Access 100,000+ open-source AI models, datasets, and spaces. Perfect for custom model deployment and experimentation. Want to explore models?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🤗 Hugging Face</h3>
                <p className="text-sm text-gray-400">Open-source AI models</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-orange-400">🔓 Open Source</span>
                  <span className="text-xs text-purple-400">Connect →</span>
                </div>
              </button>

              <button
                onClick={() => {
                  alert('🔵 Google AI Studio integration selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🔵 Google AI Studio integration selected! Access Gemini models, multimodal AI, and Google\'s latest AI capabilities. Includes vision, code generation, and reasoning. Set up Google AI?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🔵 Google AI Studio</h3>
                <p className="text-sm text-gray-400">Gemini models & multimodal AI</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-blue-400">🎯 Multimodal</span>
                  <span className="text-xs text-purple-400">Connect →</span>
                </div>
              </button>

              {/* Cloud & Enterprise */}
              <button
                onClick={() => {
                  alert('☁️ AWS Bedrock integration selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '☁️ AWS Bedrock integration selected! This provides enterprise-grade AI models with enhanced security and compliance. Shall I guide you through the AWS setup process?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">☁️ AWS Bedrock</h3>
                <p className="text-sm text-gray-400">Enterprise AI models</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-yellow-400">🏢 Enterprise</span>
                  <span className="text-xs text-purple-400">Connect →</span>
                </div>
              </button>

              <button
                onClick={() => {
                  alert('🔷 Azure OpenAI integration selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🔷 Azure OpenAI integration selected! Enterprise OpenAI models on Microsoft Azure with enhanced security, compliance, and content filtering. Ready for enterprise deployment?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🔷 Azure OpenAI</h3>
                <p className="text-sm text-gray-400">Enterprise OpenAI on Azure</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-blue-400">🏢 Enterprise</span>
                  <span className="text-xs text-purple-400">Connect →</span>
                </div>
              </button>

              {/* Communication & Collaboration */}
              <button
                onClick={() => {
                  alert('🔗 Slack Integration selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🔗 Slack Integration selected! This enables AI-powered team communication, smart notifications, and workflow automation in Slack. Ready to connect your workspace?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🔗 Slack Integration</h3>
                <p className="text-sm text-gray-400">Team communication</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-blue-400">💼 Business</span>
                  <span className="text-xs text-purple-400">Connect →</span>
                </div>
              </button>

              <button
                onClick={() => {
                  alert('💬 Discord AI Bot integration selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '💬 Discord AI Bot integration selected! Create intelligent Discord bots with AI chat, auto-moderation, voice commands, and game integration. Perfect for community management!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">💬 Discord AI Bot</h3>
                <p className="text-sm text-gray-400">Intelligent Discord automation</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-purple-400">🎮 Gaming</span>
                  <span className="text-xs text-purple-400">Connect →</span>
                </div>
              </button>

              <button
                onClick={() => {
                  alert('📧 Gmail AI Assistant integration selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '📧 Gmail AI Assistant integration selected! Smart email management with AI-powered responses, email classification, priority detection, and automated workflows. Boost your email productivity!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">📧 Gmail AI Assistant</h3>
                <p className="text-sm text-gray-400">Smart email management</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-green-400">📬 Productivity</span>
                  <span className="text-xs text-purple-400">Connect →</span>
                </div>
              </button>

              {/* Data & Analytics */}
              <button
                onClick={() => {
                  alert('🌲 Pinecone Vector DB integration selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🌲 Pinecone Vector DB integration selected! High-performance vector database for AI applications, semantic search, and RAG systems. Perfect for building intelligent search experiences!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🌲 Pinecone Vector DB</h3>
                <p className="text-sm text-gray-400">Vector database for AI</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-green-400">🔍 Search</span>
                  <span className="text-xs text-purple-400">Connect →</span>
                </div>
              </button>

              <button
                onClick={() => {
                  alert('🕸️ Weaviate Vector DB integration selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🕸️ Weaviate Vector DB integration selected! Open-source vector database with GraphQL API, multi-modal search, and auto-classification. Great for semantic search and knowledge graphs!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🕸️ Weaviate Vector DB</h3>
                <p className="text-sm text-gray-400">Open-source vector database</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-orange-400">🔓 Open Source</span>
                  <span className="text-xs text-purple-400">Connect →</span>
                </div>
              </button>

              {/* Automation & Productivity */}
              <button
                onClick={() => {
                  alert('⚡ Zapier AI Automation integration selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '⚡ Zapier AI Automation integration selected! Connect 5000+ apps with AI-powered workflows, smart triggers, and natural language automation. Automate everything with AI!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">⚡ Zapier AI Automation</h3>
                <p className="text-sm text-gray-400">5000+ app integrations</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-yellow-400">🔗 No-Code</span>
                  <span className="text-xs text-purple-400">Connect →</span>
                </div>
              </button>

              <button
                onClick={() => {
                  alert('🎯 Make AI Scenarios integration selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🎯 Make AI Scenarios integration selected! Visual automation platform with AI-powered scenario building, complex workflows, and advanced error handling. Build sophisticated automations!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🎯 Make AI Scenarios</h3>
                <p className="text-sm text-gray-400">Visual automation platform</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-blue-400">🎨 Visual</span>
                  <span className="text-xs text-purple-400">Connect →</span>
                </div>
              </button>

              <button
                onClick={() => {
                  alert('📝 Notion AI integration selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '📝 Notion AI integration selected! AI-powered workspace for notes, docs, and project management. Smart templates, content generation, and database automation. Enhance your productivity!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">📝 Notion AI</h3>
                <p className="text-sm text-gray-400">AI-powered workspace</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-gray-400">📋 Productivity</span>
                  <span className="text-xs text-purple-400">Connect →</span>
                </div>
              </button>

              {/* Development Tools */}
              <button
                onClick={() => {
                  alert('👨‍💻 GitHub Copilot integration selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '👨‍💻 GitHub Copilot integration selected! AI pair programmer for code completion, generation, documentation, and test writing. Boost your development productivity with AI!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">👨‍💻 GitHub Copilot</h3>
                <p className="text-sm text-gray-400">AI pair programmer</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-green-400">💻 Development</span>
                  <span className="text-xs text-purple-400">Connect →</span>
                </div>
              </button>

              <button
                onClick={() => {
                  alert('🔧 Replit AI integration selected!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🔧 Replit AI integration selected! AI-powered online IDE with code generation, debugging, explanation, and refactoring. Perfect for rapid prototyping and learning!',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🔧 Replit AI</h3>
                <p className="text-sm text-gray-400">AI-powered online IDE</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-blue-400">🌐 Online</span>
                  <span className="text-xs text-purple-400">Connect →</span>
                </div>
              </button>
            </div>
          </div>
        );
      case 'security':
        return (
          <div className="p-6 text-white">
            <h2 className="text-2xl font-bold mb-4">🛡️ Security Dashboard</h2>
            {isAuthenticated ? (
              <div>
                <p>Monitor security events, manage access controls, and view audit logs.</p>
                
                <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="bg-gray-800 p-4 rounded-lg">
                    <h3 className="text-2xl font-bold text-green-400">✅ Secure</h3>
                    <p className="text-sm text-gray-400">System Status</p>
                  </div>
                  <div className="bg-gray-800 p-4 rounded-lg">
                    <h3 className="text-2xl font-bold text-blue-400">47</h3>
                    <p className="text-sm text-gray-400">Active Sessions</p>
                  </div>
                  <div className="bg-gray-800 p-4 rounded-lg">
                    <h3 className="text-2xl font-bold text-yellow-400">0</h3>
                    <p className="text-sm text-gray-400">Security Alerts</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <button
                    onClick={() => {
                      alert('🔐 Access Control opened!');
                      const message = {
                        id: Date.now().toString(),
                        content: '🔐 Access Control: Managing permissions for 47 users. Admin (3), Editor (12), Viewer (32). Recent activity: 2 new user registrations, 1 permission update. Need to modify access levels?',
                        sender: 'assistant' as const,
                        timestamp: new Date()
                      };
                      setMessages(prev => [...prev, message]);
                      setCurrentView('chat');
                    }}
                    className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
                  >
                    <h3 className="font-semibold mb-2">🔐 Access Control</h3>
                    <p className="text-sm text-gray-400">Manage user permissions and roles</p>
                    <div className="mt-3 text-xs text-purple-400">Manage Access →</div>
                  </button>
                  
                  <button
                    onClick={() => {
                      alert('📋 Audit Logs opened!');
                      const message = {
                        id: Date.now().toString(),
                        content: '📋 Audit Logs: Latest events - User login (admin@redditaeo.com, 2 min ago), Workflow executed (Document Processing, 5 min ago), Integration connected (OpenAI, 1 hour ago). View detailed logs?',
                        sender: 'assistant' as const,
                        timestamp: new Date()
                      };
                      setMessages(prev => [...prev, message]);
                      setCurrentView('chat');
                    }}
                    className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
                  >
                    <h3 className="font-semibold mb-2">📋 Audit Logs</h3>
                    <p className="text-sm text-gray-400">Security event tracking and monitoring</p>
                    <div className="mt-3 text-xs text-purple-400">View Logs →</div>
                  </button>

                  <button
                    onClick={() => {
                      alert('🔒 Session Management opened!');
                      const message = {
                        id: Date.now().toString(),
                        content: '🔒 Session Management: 47 active sessions detected. 3 admin sessions, 44 user sessions. Average session duration: 2.5 hours. Want to review or terminate any sessions?',
                        sender: 'assistant' as const,
                        timestamp: new Date()
                      };
                      setMessages(prev => [...prev, message]);
                      setCurrentView('chat');
                    }}
                    className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
                  >
                    <h3 className="font-semibold mb-2">🔒 Session Management</h3>
                    <p className="text-sm text-gray-400">Monitor and control user sessions</p>
                    <div className="mt-3 text-xs text-purple-400">Manage Sessions →</div>
                  </button>

                  <button
                    onClick={() => {
                      alert('⚠️ Threat Monitor opened!');
                      const message = {
                        id: Date.now().toString(),
                        content: '⚠️ Threat Monitor: System secure! 0 active threats detected. Last scan: 5 minutes ago. Blocked 12 suspicious login attempts this week. Security status: EXCELLENT. Need threat details?',
                        sender: 'assistant' as const,
                        timestamp: new Date()
                      };
                      setMessages(prev => [...prev, message]);
                      setCurrentView('chat');
                    }}
                    className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
                  >
                    <h3 className="font-semibold mb-2">⚠️ Threat Monitor</h3>
                    <p className="text-sm text-gray-400">Real-time security threat detection</p>
                    <div className="mt-3 text-xs text-purple-400">View Threats →</div>
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center">
                <p className="text-gray-400 mb-4">Authentication required to access security features.</p>
                <button
                  onClick={() => setShowAuthModal(true)}
                  className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg"
                >
                  Sign In
                </button>
              </div>
            )}
          </div>
        );
      case 'settings':
        return (
          <div className="p-6 text-white">
            <h2 className="text-2xl font-bold mb-4">⚙️ Settings</h2>
            <p>Configure your AI Scholar preferences and application settings.</p>
            
            <div className="mt-6 space-y-4">
              <button
                onClick={() => {
                  alert('🎨 Appearance settings opened!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🎨 Appearance Settings: Current theme is Dark Mode. Available options: Dark, Light, Auto (system). Color schemes: Purple (current), Blue, Green. Would you like to change your theme?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="w-full bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🎨 Appearance</h3>
                <p className="text-sm text-gray-400">Theme and display preferences</p>
                <div className="mt-3 text-xs text-purple-400">Customize →</div>
              </button>
              
              <button
                onClick={() => {
                  alert('🔔 Notification settings opened!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🔔 Notification Settings: Email notifications (ON), Push notifications (ON), Workflow alerts (ON), Security alerts (ON). Would you like to modify your notification preferences?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="w-full bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🔔 Notifications</h3>
                <p className="text-sm text-gray-400">Manage notification settings</p>
                <div className="mt-3 text-xs text-purple-400">Configure →</div>
              </button>

              <button
                onClick={() => {
                  alert('🤖 AI Preferences opened!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🤖 AI Preferences: Default model: GPT-4, Temperature: 0.7, Max tokens: 2000, Chain of thought: Enabled. Voice settings: Enabled, Language: English. Want to adjust AI behavior?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="w-full bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🤖 AI Preferences</h3>
                <p className="text-sm text-gray-400">Configure AI model settings and behavior</p>
                <div className="mt-3 text-xs text-purple-400">Configure →</div>
              </button>

              <button
                onClick={() => {
                  alert('🔐 Privacy & Security opened!');
                  const message = {
                    id: Date.now().toString(),
                    content: '🔐 Privacy & Security: Two-factor auth (Enabled), Data encryption (AES-256), Session timeout (4 hours), API access (Restricted). Need to update security settings?',
                    sender: 'assistant' as const,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, message]);
                  setCurrentView('chat');
                }}
                className="w-full bg-gray-800 hover:bg-gray-700 p-4 rounded-lg text-left transition-colors"
              >
                <h3 className="font-semibold mb-2">🔐 Privacy & Security</h3>
                <p className="text-sm text-gray-400">Manage privacy and security settings</p>
                <div className="mt-3 text-xs text-purple-400">Manage →</div>
              </button>
            </div>
          </div>
        );
      case 'profile':
        return (
          <div className="p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold">👤 User Profile</h2>
              {isAuthenticated && (
                <div className="flex space-x-2">
                  <button
                    onClick={refreshProfile}
                    disabled={isLoadingProfile}
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors flex items-center"
                  >
                    {isLoadingProfile ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                    ) : (
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    )}
                    Refresh
                  </button>
                  <button
                    onClick={openEditProfile}
                    className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    Edit Profile
                  </button>
                </div>
              )}
            </div>
            
            {isAuthenticated ? (
              <div>
                <div className="bg-gray-800 p-6 rounded-lg mb-6">
                  <div className="flex items-center mb-4">
                    <div className="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                      {user?.name?.charAt(0) || 'U'}
                    </div>
                    <div className="ml-4">
                      <h3 className="text-xl font-semibold">{user?.name}</h3>
                      <p className="text-gray-400">{user?.email}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <p><strong>Account Type:</strong> Premium</p>
                      <p><strong>Member Since:</strong> January 2024</p>
                      <p><strong>Last Login:</strong> {new Date().toLocaleDateString()}</p>
                    </div>
                    <div className="space-y-2">
                      <p><strong>Total Workflows:</strong> 12</p>
                      <p><strong>Active Integrations:</strong> 5</p>
                      <p><strong>Documents Processed:</strong> 247</p>
                    </div>
                  </div>
                </div>

                {/* Recent Activity */}
                <div className="bg-gray-800 p-6 rounded-lg">
                  <h3 className="text-lg font-semibold mb-4">📊 Recent Activity</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-gray-700 rounded">
                      <div className="flex items-center">
                        <span className="text-green-400 mr-3">✅</span>
                        <span>Document uploaded and analyzed</span>
                      </div>
                      <span className="text-gray-400 text-sm">2 minutes ago</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-700 rounded">
                      <div className="flex items-center">
                        <span className="text-blue-400 mr-3">🔗</span>
                        <span>OpenAI integration configured</span>
                      </div>
                      <span className="text-gray-400 text-sm">1 hour ago</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-700 rounded">
                      <div className="flex items-center">
                        <span className="text-purple-400 mr-3">⚡</span>
                        <span>Workflow executed successfully</span>
                      </div>
                      <span className="text-gray-400 text-sm">3 hours ago</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center">
                <p className="text-gray-400 mb-4">Please sign in to view your profile.</p>
                <button
                  onClick={() => setShowAuthModal(true)}
                  className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg"
                >
                  Sign In
                </button>
              </div>
            )}

            {/* Edit Profile Modal */}
            {showEditProfile && (
              <div className="fixed inset-0 z-50 overflow-y-auto">
                <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                  <div className="fixed inset-0 transition-opacity" onClick={() => setShowEditProfile(false)}>
                    <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
                  </div>

                  <div className="inline-block align-bottom bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                    <div className="bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                      <div className="sm:flex sm:items-start">
                        <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                          <h3 className="text-lg leading-6 font-medium text-white mb-4">
                            Edit Profile
                          </h3>
                          
                          <div className="space-y-4">
                            <div>
                              <label className="block text-sm font-medium text-gray-300">Name</label>
                              <input
                                type="text"
                                value={editProfileData.name}
                                onChange={(e) => setEditProfileData(prev => ({ ...prev, name: e.target.value }))}
                                className="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                                placeholder="Enter your name"
                              />
                            </div>
                            
                            <div>
                              <label className="block text-sm font-medium text-gray-300">Email</label>
                              <input
                                type="email"
                                value={editProfileData.email}
                                onChange={(e) => setEditProfileData(prev => ({ ...prev, email: e.target.value }))}
                                className="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                                placeholder="Enter your email"
                              />
                            </div>

                            <div>
                              <label className="block text-sm font-medium text-gray-300">Bio</label>
                              <textarea
                                value={editProfileData.bio}
                                onChange={(e) => setEditProfileData(prev => ({ ...prev, bio: e.target.value }))}
                                rows={3}
                                className="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                                placeholder="Tell us about yourself"
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                      <button
                        onClick={updateProfile}
                        disabled={isLoadingProfile}
                        className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-purple-600 text-base font-medium text-white hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 sm:ml-3 sm:w-auto sm:text-sm disabled:bg-gray-600"
                      >
                        {isLoadingProfile ? 'Updating...' : 'Update Profile'}
                      </button>
                      <button
                        onClick={() => setShowEditProfile(false)}
                        className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-600 shadow-sm px-4 py-2 bg-gray-800 text-base font-medium text-gray-300 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        );
      default:
        return renderChatView();
    }
  };

  return (
    <div className="h-screen bg-gray-900 flex overflow-hidden">
      {renderSidebar()}
      
      <div className="flex flex-col w-0 flex-1 overflow-hidden">
        {renderHeader()}
        
        <main className="flex-1 relative overflow-y-auto focus:outline-none">
          {renderCurrentView()}
        </main>
      </div>

      {/* Overlay for mobile sidebar */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        >
          <div className="absolute inset-0 bg-gray-600 opacity-75"></div>
        </div>
      )}

      {/* Auth Modal */}
      {renderAuthModal()}
    </div>
  );
};

export default App;