# 🤖 AI Agents & Personas Features

This document describes the new AI Agents and Customizable Personas features implemented in the AI Scholar Chatbot.

## 🎯 Overview

### 1. AI Agents & Tool Use
AI Agents give the chatbot the ability to use external tools to answer questions, making it far more powerful than a traditional language model.

### 2. Customizable Personas & System Prompts
Personas allow users to define the AI's personality, expertise, and behavior through custom system prompts.

## 🤖 AI Agents & Tool Use

### What It Does
- **Web Search**: Get real-time information from the internet
- **Calculator**: Perform precise mathematical calculations
- **Python Executor**: Run Python code safely for data analysis and plotting
- **Stock Price**: Look up current stock prices (extensible to real APIs)

### How It Works
1. **Agent Reasoning**: The AI analyzes the user's question and decides which tools to use
2. **Tool Execution**: Tools are executed safely in sandboxed environments
3. **Result Integration**: Tool results are integrated into the AI's response
4. **Multi-step Reasoning**: The agent can chain multiple tool uses together

### Available Tools

#### 🔍 Web Search Tool
```python
# Usage example
"What was the stock price of NVDA at closing today?"
# Agent will use web search to get real-time information
```

**Features:**
- Uses DuckDuckGo API for instant answers
- Fallback search capabilities
- Safe, rate-limited requests

#### 🧮 Calculator Tool
```python
# Usage example
"Calculate the compound interest on $10,000 at 5% for 10 years"
# Agent will use calculator for precise mathematical computation
```

**Features:**
- Safe mathematical expression evaluation
- Support for trigonometry, logarithms, and common functions
- Protection against code injection

#### 🐍 Python Executor Tool
```python
# Usage example
"Create a plot showing the relationship between x and x^2 for x from 0 to 10"
# Agent will write and execute Python code to generate the plot
```

**Features:**
- Sandboxed Python execution
- Support for matplotlib, numpy, pandas
- 30-second timeout protection
- Output capture and error handling

#### 📈 Stock Price Tool
```python
# Usage example
"What's the current price of Apple stock?"
# Agent will look up stock information
```

**Features:**
- Extensible to real financial APIs
- Symbol validation
- Timestamp tracking

### API Usage

#### Agent Chat Endpoint
```http
POST /api/agent/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "What is the square root of 144 plus the current time?",
  "session_id": 123,
  "model": "llama2",
  "enable_tools": true
}
```

**Response:**
```json
{
  "success": true,
  "response": "The square root of 144 is 12. The current time is...",
  "agent_mode": true,
  "tool_calls": [
    {
      "tool": "calculator",
      "input": "sqrt(144)",
      "result": 12,
      "success": true,
      "execution_time": 0.05
    }
  ],
  "iterations": 2,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Get Available Tools
```http
GET /api/agent/tools
Authorization: Bearer <token>
```

**Response:**
```json
{
  "tools": ["web_search", "calculator", "python_executor", "stock_price"],
  "description": "- web_search: Search the web for current information...\n- calculator: Perform mathematical calculations..."
}
```

## 👤 Customizable Personas & System Prompts

### Built-in Personas

#### 🎓 Socratic Tutor
- **Purpose**: Educational AI that teaches through questioning
- **Behavior**: Asks probing questions instead of giving direct answers
- **Use Cases**: Learning, education, critical thinking

#### 🔍 Code Reviewer
- **Purpose**: Meticulous code analysis and review
- **Behavior**: Critical analysis of code quality, security, and best practices
- **Use Cases**: Code review, debugging, security analysis

#### ✨ Creative Writer
- **Purpose**: Imaginative assistant for creative writing
- **Behavior**: Inspiring, descriptive, encourages creative exploration
- **Use Cases**: Creative writing, storytelling, brainstorming

#### 💼 Business Analyst
- **Purpose**: Strategic business insights and analysis
- **Behavior**: Analytical, data-driven, professional
- **Use Cases**: Business analysis, strategy, market research

#### 🧠 Research Scientist
- **Purpose**: Evidence-based reasoning and research
- **Behavior**: Methodical, precise, considers multiple hypotheses
- **Use Cases**: Research, scientific analysis, data interpretation

#### 😄 Witty Comedian
- **Purpose**: Humorous and entertaining conversations
- **Behavior**: Witty, playful, uses wordplay and clever observations
- **Use Cases**: Entertainment, mood lifting, light conversation

#### 📝 Minimalist Assistant
- **Purpose**: Concise, direct responses
- **Behavior**: Brief, efficient, focuses on essential information
- **Use Cases**: Quick answers, summaries, time-sensitive queries

#### 🤔 Philosophical Thinker
- **Purpose**: Deep thinking and ethical considerations
- **Behavior**: Contemplative, explores multiple perspectives
- **Use Cases**: Philosophical discussions, ethical analysis, deep thinking

### API Usage

#### Get Available Personas
```http
GET /api/personas
Authorization: Bearer <token>
```

**Response:**
```json
{
  "personas": {
    "socratic_tutor": {
      "name": "Socratic Tutor",
      "description": "An educational AI that teaches through questioning",
      "personality_traits": ["questioning", "patient", "encouraging"],
      "use_cases": ["learning", "education", "critical thinking"],
      "type": "built-in"
    },
    "custom_123": {
      "name": "My Custom Persona",
      "description": "A custom persona I created",
      "type": "custom"
    }
  }
}
```

#### Create Custom Persona
```http
POST /api/personas
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Technical Mentor",
  "description": "A patient technical mentor for programming",
  "system_prompt": "You are a patient technical mentor. Help users learn programming by explaining concepts clearly and providing guided practice. Always encourage learning and growth.",
  "personality_traits": ["patient", "encouraging", "technical"],
  "use_cases": ["programming education", "mentoring"],
  "temperature": 0.6,
  "max_tokens": 2048
}
```

#### Apply Persona to Session
```http
POST /api/sessions/123/persona
Authorization: Bearer <token>
Content-Type: application/json

{
  "persona_key": "socratic_tutor"
}
```

Or with custom system prompt:
```json
{
  "custom_system_prompt": "You are a helpful assistant specialized in data science. Always provide practical examples and explain concepts clearly."
}
```

## 🔧 Implementation Details

### Agent Service Architecture
```
User Question → Agent Service → Tool Selection → Tool Execution → Result Integration → Response
```

1. **Question Analysis**: LLM analyzes the user's question
2. **Tool Selection**: Agent decides which tools are needed
3. **Tool Execution**: Tools run in sandboxed environments
4. **Result Integration**: Tool outputs are incorporated into the response
5. **Iterative Process**: Agent can use multiple tools in sequence

### Persona Service Architecture
```
User Session → Persona Selection → System Prompt Application → Model Parameter Adjustment → Enhanced Response
```

1. **Persona Selection**: User chooses or creates a persona
2. **System Prompt**: Custom system prompt is applied to the session
3. **Parameter Tuning**: Model parameters are adjusted for the persona
4. **Response Generation**: AI responds according to the persona's characteristics

### Safety Features

#### Agent Safety
- **Sandboxed Execution**: All code execution is isolated
- **Timeout Protection**: 30-second limits on tool execution
- **Input Validation**: Dangerous patterns are blocked
- **Rate Limiting**: Prevents abuse of external APIs

#### Persona Safety
- **Prompt Validation**: System prompts are validated for safety
- **Parameter Limits**: Model parameters are constrained to safe ranges
- **Content Filtering**: Inappropriate content is filtered

## 🚀 Getting Started

### 1. Enable Agent Mode
```javascript
// Frontend example
const response = await fetch('/api/agent/chat', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: "What's 15% of 250 and what's the weather like today?",
    enable_tools: true
  })
});
```

### 2. Create a Custom Persona
```javascript
// Create a custom persona
const persona = await fetch('/api/personas', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: "Data Science Mentor",
    description: "A helpful data science mentor",
    system_prompt: "You are an expert data scientist. Help users learn data science concepts through practical examples and clear explanations.",
    personality_traits: ["expert", "helpful", "practical"],
    temperature: 0.6
  })
});
```

### 3. Apply Persona to Session
```javascript
// Apply persona to a chat session
await fetch(`/api/sessions/${sessionId}/persona`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    persona_key: "socratic_tutor"
  })
});
```

## 🧪 Testing

Run the test suite to verify the features:

```bash
python test_agent_persona_features.py
```

This will test:
- Agent service functionality
- Tool execution
- Persona management
- Database integration
- API endpoints

## 🔮 Future Enhancements

### Additional Tools
- **File System**: Read and write files safely
- **Database Query**: Query databases with natural language
- **API Integrations**: Connect to external services
- **Image Generation**: Create images with AI
- **Email/Notifications**: Send communications

### Advanced Personas
- **Learning Personas**: Personas that adapt based on user interactions
- **Domain-Specific**: Specialized personas for specific industries
- **Multi-Modal**: Personas that handle text, images, and audio
- **Collaborative**: Personas that work together on complex tasks

### Enhanced Agent Capabilities
- **Multi-Agent Systems**: Multiple agents working together
- **Long-term Memory**: Agents that remember across sessions
- **Planning**: Agents that can plan multi-step tasks
- **Learning**: Agents that improve over time

## 📚 Examples

### Example 1: Research Assistant
```
User: "Research the latest developments in quantum computing and create a summary with key points"

Agent Process:
1. Uses web_search to find recent quantum computing news
2. Uses python_executor to analyze and structure the information
3. Creates a comprehensive summary with key points
```

### Example 2: Data Analysis
```
User: "Analyze this dataset and create visualizations"

Agent Process:
1. Uses python_executor to load and examine the data
2. Performs statistical analysis
3. Creates multiple visualizations
4. Provides insights and recommendations
```

### Example 3: Educational Tutor
```
User: "Help me understand calculus derivatives"

Socratic Tutor Persona:
- Asks: "What do you think a derivative represents?"
- Guides through discovery rather than giving direct answers
- Encourages critical thinking and understanding
```

## 🤝 Contributing

To add new tools or personas:

1. **New Tool**: Extend the `BaseTool` class in `services/agent_service.py`
2. **New Persona**: Add to the built-in personas in `services/persona_service.py`
3. **Test**: Add tests to `test_agent_persona_features.py`
4. **Document**: Update this documentation

## 📞 Support

For questions or issues with the Agent and Persona features:

1. Check the test results: `python test_agent_persona_features.py`
2. Review the logs for error messages
3. Ensure all dependencies are installed
4. Verify the database migration was applied

---

*These features transform the AI chatbot from a simple language model into a powerful reasoning engine with customizable personalities. Enjoy exploring the enhanced capabilities!* 🚀