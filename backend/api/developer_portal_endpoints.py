"""
Developer portal endpoints
Provides comprehensive API documentation, testing tools, and SDK generation
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from services.auth_service import AuthService
from services.oauth_server import OAuthServer
from services.api_key_service import APIKeyService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/docs", tags=["developer-portal"])

# Initialize services
auth_service = AuthService()
oauth_server = OAuthServer()
api_key_service = APIKeyService()

# Security
security = HTTPBearer()

# Pydantic models
class APIEndpoint(BaseModel):
    path: str
    method: str
    summary: str
    description: str
    parameters: List[Dict[str, Any]]
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]]
    authentication: List[str]
    scopes: List[str] = []
    rate_limit: Optional[str] = None
    examples: List[Dict[str, Any]] = []

class SDKGenerationRequest(BaseModel):
    language: str
    package_name: str
    version: str = "1.0.0"
    endpoints: List[str] = []

class APITestRequest(BaseModel):
    endpoint: str
    method: str
    headers: Dict[str, str] = {}
    parameters: Dict[str, Any] = {}
    body: Optional[Dict[str, Any]] = None

class DeveloperPortalResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# Authentication dependency (optional for public docs)
async def get_current_user_optional(request: Request):
    """Get current user if authenticated, otherwise return None"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        user = await auth_service.verify_token(token)
        return user
    except:
        return None

# API Documentation Endpoints

@router.get("/", response_class=HTMLResponse)
async def developer_portal_home():
    """Developer portal home page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Scholar API Developer Portal</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }
            .section { margin: 30px 0; }
            .card { background: #f8f9fa; padding: 20px; border-radius: 6px; margin: 15px 0; border-left: 4px solid #007bff; }
            .btn { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 5px; }
            .btn:hover { background: #0056b3; }
            .code { background: #f1f1f1; padding: 10px; border-radius: 4px; font-family: monospace; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 AI Scholar API Developer Portal</h1>
            
            <div class="section">
                <h2>Welcome to the AI Scholar API</h2>
                <p>Build powerful research applications with our comprehensive API. Access advanced RAG capabilities, voice processing, educational tools, and enterprise features.</p>
            </div>

            <div class="section">
                <h2>🔧 Quick Start</h2>
                <div class="grid">
                    <div class="card">
                        <h3>1. Authentication</h3>
                        <p>Get started with OAuth 2.0 or API keys</p>
                        <a href="/api/docs/authentication" class="btn">Auth Guide</a>
                    </div>
                    <div class="card">
                        <h3>2. API Reference</h3>
                        <p>Explore all available endpoints</p>
                        <a href="/api/docs/reference" class="btn">API Reference</a>
                    </div>
                    <div class="card">
                        <h3>3. Interactive Testing</h3>
                        <p>Test APIs directly in your browser</p>
                        <a href="/api/docs/playground" class="btn">API Playground</a>
                    </div>
                    <div class="card">
                        <h3>4. SDKs & Libraries</h3>
                        <p>Download SDKs for popular languages</p>
                        <a href="/api/docs/sdks" class="btn">Get SDKs</a>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>📚 Features</h2>
                <div class="grid">
                    <div class="card">
                        <h3>🧠 Advanced RAG</h3>
                        <p>Intelligent document processing and retrieval</p>
                    </div>
                    <div class="card">
                        <h3>🎤 Voice Processing</h3>
                        <p>Speech-to-text and voice commands</p>
                    </div>
                    <div class="card">
                        <h3>📱 Mobile Support</h3>
                        <p>PWA and mobile synchronization</p>
                    </div>
                    <div class="card">
                        <h3>🔗 Integrations</h3>
                        <p>Connect with Zotero, Notion, and more</p>
                    </div>
                    <div class="card">
                        <h3>🎓 Educational Tools</h3>
                        <p>Quizzes, spaced repetition, progress tracking</p>
                    </div>
                    <div class="card">
                        <h3>🏢 Enterprise Features</h3>
                        <p>Compliance monitoring and institutional management</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🚀 Example Request</h2>
                <div class="code">
curl -X POST "https://api.aischolar.com/api/v1/features/execute" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "feature": "voice",
    "action": "speech_to_text",
    "parameters": {
      "audio_data": "base64_encoded_audio"
    }
  }'
                </div>
            </div>

            <div class="section">
                <h2>📞 Support</h2>
                <p>Need help? Check out our resources:</p>
                <a href="/api/docs/tutorials" class="btn">Tutorials</a>
                <a href="/api/docs/examples" class="btn">Code Examples</a>
                <a href="/api/docs/support" class="btn">Support</a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/reference", response_model=DeveloperPortalResponse)
async def get_api_reference():
    """Get comprehensive API reference documentation"""
    try:
        # Define all API endpoints with documentation
        endpoints = [
            # Unified API
            {
                "path": "/api/v1/features/execute",
                "method": "POST",
                "summary": "Execute Feature Action",
                "description": "Execute a specific feature action through unified interface",
                "parameters": [],
                "request_body": {
                    "type": "object",
                    "properties": {
                        "feature": {"type": "string", "description": "Feature name"},
                        "action": {"type": "string", "description": "Action to execute"},
                        "parameters": {"type": "object", "description": "Action parameters"}
                    }
                },
                "responses": {
                    "200": {"description": "Success", "schema": {"type": "object"}},
                    "400": {"description": "Bad Request"},
                    "401": {"description": "Unauthorized"}
                },
                "authentication": ["Bearer Token", "API Key"],
                "scopes": ["read", "write"],
                "rate_limit": "1000/hour",
                "examples": [
                    {
                        "name": "Voice Processing",
                        "request": {
                            "feature": "voice",
                            "action": "speech_to_text",
                            "parameters": {"audio_data": "base64_encoded_audio"}
                        }
                    }
                ]
            },
            # GraphQL
            {
                "path": "/api/v1/graphql",
                "method": "POST",
                "summary": "GraphQL Query",
                "description": "Execute GraphQL queries for flexible data retrieval",
                "parameters": [],
                "request_body": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "GraphQL query"},
                        "variables": {"type": "object", "description": "Query variables"}
                    }
                },
                "responses": {
                    "200": {"description": "Success", "schema": {"type": "object"}}
                },
                "authentication": ["Bearer Token"],
                "examples": [
                    {
                        "name": "Get User Quizzes",
                        "request": {
                            "query": "query { userQuizzes(userId: \"123\") { id title questions } }"
                        }
                    }
                ]
            },
            # Authentication
            {
                "path": "/api/auth/oauth/token",
                "method": "POST",
                "summary": "OAuth Token Exchange",
                "description": "Exchange authorization code for access token",
                "parameters": [],
                "request_body": {
                    "type": "object",
                    "properties": {
                        "grant_type": {"type": "string"},
                        "code": {"type": "string"},
                        "client_id": {"type": "string"},
                        "client_secret": {"type": "string"}
                    }
                },
                "responses": {
                    "200": {"description": "Token response"}
                },
                "authentication": ["Client Credentials"]
            },
            # Webhooks
            {
                "path": "/api/webhooks-notifications/webhooks",
                "method": "POST",
                "summary": "Register Webhook",
                "description": "Register a webhook endpoint for event notifications",
                "parameters": [],
                "request_body": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "events": {"type": "array", "items": {"type": "string"}},
                        "secret": {"type": "string"}
                    }
                },
                "responses": {
                    "200": {"description": "Webhook registered"}
                },
                "authentication": ["Bearer Token"]
            }
        ]
        
        return DeveloperPortalResponse(
            success=True,
            data={
                "endpoints": endpoints,
                "total": len(endpoints),
                "categories": [
                    "unified-api", "graphql", "authentication", 
                    "webhooks", "voice", "education", "enterprise"
                ]
            }
        )
    except Exception as e:
        logger.error(f"Failed to get API reference: {e}")
        return DeveloperPortalResponse(
            success=False,
            error=f"Failed to get API reference: {str(e)}"
        )

@router.get("/authentication", response_class=HTMLResponse)
async def authentication_guide():
    """Authentication guide page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authentication Guide - AI Scholar API</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1, h2 { color: #333; }
            .code { background: #f1f1f1; padding: 15px; border-radius: 4px; font-family: monospace; margin: 10px 0; overflow-x: auto; }
            .method { background: #e7f3ff; padding: 20px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #007bff; }
            .warning { background: #fff3cd; padding: 15px; border-radius: 4px; border-left: 4px solid #ffc107; margin: 15px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 Authentication Guide</h1>
            
            <p>The AI Scholar API supports two authentication methods: OAuth 2.0 and API Keys. Choose the method that best fits your application.</p>

            <div class="method">
                <h2>Method 1: OAuth 2.0 (Recommended)</h2>
                <p>OAuth 2.0 is recommended for applications that act on behalf of users.</p>
                
                <h3>Step 1: Register Your Application</h3>
                <div class="code">
POST /api/auth/oauth/register
{
  "name": "My Research App",
  "description": "A research application",
  "redirect_uris": ["https://myapp.com/callback"],
  "scopes": ["read", "write"],
  "client_type": "confidential"
}
                </div>

                <h3>Step 2: Authorization Flow</h3>
                <div class="code">
# Redirect user to:
GET /api/auth/oauth/authorize?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&scope=read+write&state=random_state
                </div>

                <h3>Step 3: Exchange Code for Token</h3>
                <div class="code">
POST /api/auth/oauth/token
{
  "grant_type": "authorization_code",
  "code": "AUTHORIZATION_CODE",
  "redirect_uri": "YOUR_REDIRECT_URI",
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET"
}
                </div>

                <h3>Step 4: Use Access Token</h3>
                <div class="code">
curl -H "Authorization: Bearer ACCESS_TOKEN" https://api.aischolar.com/api/v1/features/execute
                </div>
            </div>

            <div class="method">
                <h2>Method 2: API Keys</h2>
                <p>API Keys are simpler and suitable for server-to-server communication.</p>
                
                <h3>Step 1: Create API Key</h3>
                <div class="code">
POST /api/auth/api-keys
{
  "name": "My Server App",
  "description": "Server-to-server integration",
  "scopes": ["read", "write"],
  "rate_limit": 1000
}
                </div>

                <h3>Step 2: Use API Key</h3>
                <div class="code">
curl -H "X-API-Key: YOUR_API_KEY" https://api.aischolar.com/api/v1/features/execute
                </div>
            </div>

            <div class="warning">
                <strong>Security Best Practices:</strong>
                <ul>
                    <li>Never expose client secrets or API keys in client-side code</li>
                    <li>Use HTTPS for all API requests</li>
                    <li>Implement proper token refresh logic</li>
                    <li>Store credentials securely</li>
                    <li>Monitor API usage and implement rate limiting</li>
                </ul>
            </div>

            <h2>Scopes</h2>
            <p>The following scopes are available:</p>
            <ul>
                <li><strong>read</strong>: Read access to user data</li>
                <li><strong>write</strong>: Write access to user data</li>
                <li><strong>voice</strong>: Access to voice processing features</li>
                <li><strong>education</strong>: Access to educational features</li>
                <li><strong>enterprise</strong>: Access to enterprise features</li>
                <li><strong>webhooks</strong>: Manage webhooks</li>
            </ul>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/playground", response_class=HTMLResponse)
async def api_playground():
    """Interactive API testing playground"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Playground - AI Scholar API</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .form-group { margin: 15px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace; }
            textarea { height: 150px; }
            .btn { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .btn:hover { background: #0056b3; }
            .response { background: #f8f9fa; padding: 15px; border-radius: 4px; margin-top: 20px; border-left: 4px solid #28a745; }
            .error { border-left-color: #dc3545; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            pre { background: #f1f1f1; padding: 10px; border-radius: 4px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧪 API Playground</h1>
            <p>Test AI Scholar API endpoints directly in your browser.</p>

            <div class="grid">
                <div>
                    <h2>Request</h2>
                    <form id="apiForm">
                        <div class="form-group">
                            <label for="endpoint">Endpoint:</label>
                            <select id="endpoint">
                                <option value="/api/v1/features/execute">Execute Feature</option>
                                <option value="/api/v1/graphql">GraphQL Query</option>
                                <option value="/api/auth/api-keys">Create API Key</option>
                                <option value="/api/webhooks-notifications/webhooks">Register Webhook</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label for="method">Method:</label>
                            <select id="method">
                                <option value="GET">GET</option>
                                <option value="POST" selected>POST</option>
                                <option value="PUT">PUT</option>
                                <option value="DELETE">DELETE</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label for="auth">Authorization:</label>
                            <input type="text" id="auth" placeholder="Bearer token or API key">
                        </div>

                        <div class="form-group">
                            <label for="headers">Headers (JSON):</label>
                            <textarea id="headers" placeholder='{"Content-Type": "application/json"}'></textarea>
                        </div>

                        <div class="form-group">
                            <label for="body">Request Body (JSON):</label>
                            <textarea id="body" placeholder='{"feature": "voice", "action": "speech_to_text", "parameters": {}}'></textarea>
                        </div>

                        <button type="submit" class="btn">Send Request</button>
                    </form>
                </div>

                <div>
                    <h2>Response</h2>
                    <div id="response" class="response" style="display: none;">
                        <h3>Status: <span id="status"></span></h3>
                        <h4>Headers:</h4>
                        <pre id="responseHeaders"></pre>
                        <h4>Body:</h4>
                        <pre id="responseBody"></pre>
                    </div>
                </div>
            </div>

            <h2>📝 Example Requests</h2>
            <div class="grid">
                <div>
                    <h3>Voice Processing</h3>
                    <pre>{
  "feature": "voice",
  "action": "speech_to_text",
  "parameters": {
    "audio_data": "base64_encoded_audio"
  }
}</pre>
                </div>
                <div>
                    <h3>Generate Quiz</h3>
                    <pre>{
  "feature": "education",
  "action": "generate_quiz",
  "parameters": {
    "content": "Machine learning is...",
    "difficulty": "medium"
  }
}</pre>
                </div>
            </div>
        </div>

        <script>
            document.getElementById('apiForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const endpoint = document.getElementById('endpoint').value;
                const method = document.getElementById('method').value;
                const auth = document.getElementById('auth').value;
                const headers = document.getElementById('headers').value;
                const body = document.getElementById('body').value;
                
                try {
                    const requestHeaders = headers ? JSON.parse(headers) : {};
                    if (auth) {
                        if (auth.startsWith('ak_')) {
                            requestHeaders['X-API-Key'] = auth;
                        } else {
                            requestHeaders['Authorization'] = auth.startsWith('Bearer ') ? auth : 'Bearer ' + auth;
                        }
                    }
                    
                    const requestOptions = {
                        method: method,
                        headers: requestHeaders
                    };
                    
                    if (body && (method === 'POST' || method === 'PUT')) {
                        requestOptions.body = body;
                    }
                    
                    const response = await fetch(endpoint, requestOptions);
                    const responseText = await response.text();
                    
                    document.getElementById('status').textContent = response.status + ' ' + response.statusText;
                    document.getElementById('responseHeaders').textContent = JSON.stringify(Object.fromEntries(response.headers), null, 2);
                    document.getElementById('responseBody').textContent = responseText;
                    
                    const responseDiv = document.getElementById('response');
                    responseDiv.style.display = 'block';
                    responseDiv.className = response.ok ? 'response' : 'response error';
                    
                } catch (error) {
                    document.getElementById('status').textContent = 'Error';
                    document.getElementById('responseHeaders').textContent = '';
                    document.getElementById('responseBody').textContent = error.message;
                    
                    const responseDiv = document.getElementById('response');
                    responseDiv.style.display = 'block';
                    responseDiv.className = 'response error';
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.post("/test", response_model=DeveloperPortalResponse)
async def test_api_endpoint(
    request: APITestRequest,
    user = Depends(get_current_user_optional)
):
    """Test an API endpoint with provided parameters"""
    try:
        # This would make an internal API call to test the endpoint
        # For now, return a mock response
        
        test_result = {
            "endpoint": request.endpoint,
            "method": request.method,
            "status": "success",
            "response_time": "150ms",
            "mock_response": {
                "success": True,
                "data": {"message": "Test successful"},
                "timestamp": datetime.now().isoformat()
            }
        }
        
        return DeveloperPortalResponse(
            success=True,
            data=test_result
        )
    except Exception as e:
        logger.error(f"API test failed: {e}")
        return DeveloperPortalResponse(
            success=False,
            error=f"API test failed: {str(e)}"
        )

@router.get("/sdks", response_model=DeveloperPortalResponse)
async def list_available_sdks():
    """List available SDKs and libraries"""
    try:
        sdks = [
            {
                "language": "Python",
                "name": "aischolar-python",
                "version": "1.0.0",
                "description": "Official Python SDK for AI Scholar API",
                "install_command": "pip install aischolar-python",
                "documentation": "/api/docs/sdks/python",
                "examples": [
                    {
                        "name": "Basic Usage",
                        "code": """
from aischolar import AIScholarClient

client = AIScholarClient(api_key="your_api_key")
result = client.voice.speech_to_text(audio_data)
print(result.text)
                        """
                    }
                ]
            },
            {
                "language": "JavaScript",
                "name": "aischolar-js",
                "version": "1.0.0",
                "description": "Official JavaScript SDK for AI Scholar API",
                "install_command": "npm install aischolar-js",
                "documentation": "/api/docs/sdks/javascript",
                "examples": [
                    {
                        "name": "Basic Usage",
                        "code": """
import { AIScholarClient } from 'aischolar-js';

const client = new AIScholarClient({ apiKey: 'your_api_key' });
const result = await client.voice.speechToText(audioData);
console.log(result.text);
                        """
                    }
                ]
            },
            {
                "language": "cURL",
                "name": "HTTP Examples",
                "version": "1.0.0",
                "description": "Direct HTTP API examples using cURL",
                "documentation": "/api/docs/sdks/curl",
                "examples": [
                    {
                        "name": "Execute Feature",
                        "code": """
curl -X POST "https://api.aischolar.com/api/v1/features/execute" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"feature": "voice", "action": "speech_to_text", "parameters": {"audio_data": "..."}}'
                        """
                    }
                ]
            }
        ]
        
        return DeveloperPortalResponse(
            success=True,
            data={
                "sdks": sdks,
                "total": len(sdks),
                "supported_languages": ["Python", "JavaScript", "TypeScript", "Go", "Java", "PHP", "Ruby"]
            }
        )
    except Exception as e:
        logger.error(f"Failed to list SDKs: {e}")
        return DeveloperPortalResponse(
            success=False,
            error=f"Failed to list SDKs: {str(e)}"
        )

@router.post("/sdks/generate", response_model=DeveloperPortalResponse)
async def generate_sdk(
    request: SDKGenerationRequest,
    user = Depends(get_current_user_optional)
):
    """Generate SDK for specified language"""
    try:
        # This would generate actual SDK code
        # For now, return a mock response
        
        sdk_info = {
            "language": request.language,
            "package_name": request.package_name,
            "version": request.version,
            "generated_at": datetime.now().isoformat(),
            "download_url": f"/api/docs/sdks/download/{request.language}/{request.package_name}",
            "files": [
                f"{request.package_name}/__init__.py",
                f"{request.package_name}/client.py",
                f"{request.package_name}/models.py",
                f"{request.package_name}/exceptions.py",
                "setup.py",
                "README.md",
                "requirements.txt"
            ],
            "size": "45KB"
        }
        
        return DeveloperPortalResponse(
            success=True,
            data=sdk_info
        )
    except Exception as e:
        logger.error(f"SDK generation failed: {e}")
        return DeveloperPortalResponse(
            success=False,
            error=f"SDK generation failed: {str(e)}"
        )

@router.get("/examples", response_model=DeveloperPortalResponse)
async def get_code_examples():
    """Get code examples for common use cases"""
    try:
        examples = [
            {
                "title": "Voice Processing Integration",
                "description": "Process speech input and get text output",
                "language": "python",
                "code": """
import asyncio
from aischolar import AIScholarClient

async def process_voice():
    client = AIScholarClient(api_key="your_api_key")
    
    # Convert speech to text
    with open("audio.wav", "rb") as audio_file:
        audio_data = audio_file.read()
    
    result = await client.voice.speech_to_text(
        audio_data=audio_data,
        language="en"
    )
    
    print(f"Transcribed text: {result.text}")
    print(f"Confidence: {result.confidence}")
    
    # Convert text to speech
    speech_result = await client.voice.text_to_speech(
        text="Hello, this is AI Scholar",
        voice_config={"language": "en", "voice": "neural"}
    )
    
    with open("output.wav", "wb") as output_file:
        output_file.write(speech_result.audio_data)

asyncio.run(process_voice())
                """
            },
            {
                "title": "Educational Quiz Generation",
                "description": "Generate quizzes from document content",
                "language": "javascript",
                "code": """
import { AIScholarClient } from 'aischolar-js';

const client = new AIScholarClient({ apiKey: 'your_api_key' });

async function generateQuiz() {
    const content = `
        Machine learning is a subset of artificial intelligence that 
        enables computers to learn and make decisions from data without 
        being explicitly programmed for every task.
    `;
    
    const quiz = await client.education.generateQuiz({
        content: content,
        difficulty: 'medium',
        questionCount: 5,
        questionTypes: ['multiple_choice', 'short_answer']
    });
    
    console.log('Generated Quiz:', quiz.title);
    quiz.questions.forEach((question, index) => {
        console.log(`${index + 1}. ${question.text}`);
        if (question.options) {
            question.options.forEach((option, optIndex) => {
                console.log(`   ${String.fromCharCode(65 + optIndex)}. ${option}`);
            });
        }
    });
}

generateQuiz();
                """
            },
            {
                "title": "Webhook Integration",
                "description": "Set up webhooks for real-time notifications",
                "language": "python",
                "code": """
import hmac
import hashlib
from flask import Flask, request, jsonify
from aischolar import AIScholarClient

app = Flask(__name__)
client = AIScholarClient(api_key="your_api_key")

# Register webhook
webhook = client.webhooks.register(
    url="https://yourapp.com/webhook",
    events=["document.uploaded", "quiz.completed", "progress.updated"],
    secret="your_webhook_secret"
)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # Verify webhook signature
    signature = request.headers.get('X-Webhook-Signature')
    payload = request.get_data()
    
    expected_signature = hmac.new(
        webhook.secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(f"sha256={expected_signature}", signature):
        return jsonify({"error": "Invalid signature"}), 401
    
    # Process webhook event
    event = request.json
    event_type = event['event']['event_type']
    
    if event_type == 'document.uploaded':
        print(f"Document uploaded: {event['event']['data']['document_id']}")
    elif event_type == 'quiz.completed':
        print(f"Quiz completed: {event['event']['data']['quiz_id']}")
    elif event_type == 'progress.updated':
        print(f"Progress updated: {event['event']['data']['user_id']}")
    
    return jsonify({"status": "received"})

if __name__ == '__main__':
    app.run(debug=True)
                """
            }
        ]
        
        return DeveloperPortalResponse(
            success=True,
            data={
                "examples": examples,
                "total": len(examples),
                "categories": ["voice", "education", "webhooks", "authentication", "mobile"]
            }
        )
    except Exception as e:
        logger.error(f"Failed to get code examples: {e}")
        return DeveloperPortalResponse(
            success=False,
            error=f"Failed to get code examples: {str(e)}"
        )

@router.get("/tutorials", response_class=HTMLResponse)
async def tutorials_page():
    """Tutorials and guides page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tutorials - AI Scholar API</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .tutorial { background: #f8f9fa; padding: 20px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #007bff; }
            .difficulty { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
            .beginner { background: #d4edda; color: #155724; }
            .intermediate { background: #fff3cd; color: #856404; }
            .advanced { background: #f8d7da; color: #721c24; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📚 Tutorials & Guides</h1>
            <p>Learn how to build amazing applications with the AI Scholar API.</p>

            <div class="grid">
                <div class="tutorial">
                    <h3>Getting Started <span class="difficulty beginner">Beginner</span></h3>
                    <p>Learn the basics of authentication and making your first API call.</p>
                    <ul>
                        <li>Setting up authentication</li>
                        <li>Making your first request</li>
                        <li>Understanding responses</li>
                        <li>Error handling</li>
                    </ul>
                </div>

                <div class="tutorial">
                    <h3>Voice Processing App <span class="difficulty intermediate">Intermediate</span></h3>
                    <p>Build a voice-enabled research assistant application.</p>
                    <ul>
                        <li>Recording audio input</li>
                        <li>Speech-to-text conversion</li>
                        <li>Processing voice commands</li>
                        <li>Text-to-speech output</li>
                    </ul>
                </div>

                <div class="tutorial">
                    <h3>Educational Platform <span class="difficulty intermediate">Intermediate</span></h3>
                    <p>Create an educational platform with quizzes and progress tracking.</p>
                    <ul>
                        <li>Document processing</li>
                        <li>Quiz generation</li>
                        <li>Spaced repetition</li>
                        <li>Progress analytics</li>
                    </ul>
                </div>

                <div class="tutorial">
                    <h3>Mobile Integration <span class="difficulty advanced">Advanced</span></h3>
                    <p>Build a mobile app with offline capabilities and sync.</p>
                    <ul>
                        <li>PWA implementation</li>
                        <li>Offline data storage</li>
                        <li>Background sync</li>
                        <li>Push notifications</li>
                    </ul>
                </div>

                <div class="tutorial">
                    <h3>Enterprise Integration <span class="difficulty advanced">Advanced</span></h3>
                    <p>Integrate with enterprise systems and compliance monitoring.</p>
                    <ul>
                        <li>OAuth 2.0 setup</li>
                        <li>Webhook configuration</li>
                        <li>Compliance monitoring</li>
                        <li>Role management</li>
                    </ul>
                </div>

                <div class="tutorial">
                    <h3>External Integrations <span class="difficulty intermediate">Intermediate</span></h3>
                    <p>Connect with external tools like Zotero, Notion, and more.</p>
                    <ul>
                        <li>Reference manager sync</li>
                        <li>Note-taking integration</li>
                        <li>Academic database search</li>
                        <li>Writing tool integration</li>
                    </ul>
                </div>
            </div>

            <h2>🎯 Quick Start Checklist</h2>
            <ol>
                <li>✅ Create an account and get API credentials</li>
                <li>✅ Choose authentication method (OAuth or API Key)</li>
                <li>✅ Make your first API call</li>
                <li>✅ Explore the API playground</li>
                <li>✅ Download SDK for your language</li>
                <li>✅ Build your first integration</li>
                <li>✅ Set up webhooks for real-time updates</li>
                <li>✅ Deploy to production</li>
            </ol>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/health", response_model=DeveloperPortalResponse)
async def developer_portal_health():
    """Health check for developer portal"""
    try:
        return DeveloperPortalResponse(
            success=True,
            data={
                "status": "healthy",
                "services": {
                    "documentation": "available",
                    "playground": "available",
                    "sdk_generation": "available",
                    "examples": "available"
                },
                "endpoints": {
                    "reference": "/api/docs/reference",
                    "playground": "/api/docs/playground",
                    "authentication": "/api/docs/authentication",
                    "sdks": "/api/docs/sdks",
                    "examples": "/api/docs/examples",
                    "tutorials": "/api/docs/tutorials"
                }
            }
        )
    except Exception as e:
        logger.error(f"Developer portal health check failed: {e}")
        return DeveloperPortalResponse(
            success=False,
            error=f"Health check failed: {str(e)}"
        )