# AI Scholar RAG API Documentation

## Overview

The AI Scholar RAG API provides advanced retrieval-augmented generation capabilities with hierarchical document processing, knowledge graph integration, memory management, intelligent reasoning, and personalization features.

**Base URL**: `http://localhost:8000` (development) / `https://api.your-domain.com` (production)

**API Version**: 1.0.0

## Authentication

All API endpoints require authentication using Bearer tokens.

### Headers
```
Authorization: Bearer <your-jwt-token>
Content-Type: application/json
```

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Login
```http
POST /api/auth/login
```

**Request Body (Form Data):**
```
email: user@example.com
password: secure_password
```

**Response:**
```json
{
  "access_token": "jwt-token-here",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## Document Management

### Upload Document
```http
POST /api/documents/upload
```

**Request (Multipart Form):**
- `file`: Document file (PDF, TXT, DOCX)
- `chunking_strategy`: `hierarchical` | `fixed` | `adaptive` (optional, default: `hierarchical`)

**Response:**
```json
{
  "id": "document-uuid",
  "filename": "document.pdf",
  "size": 1024000,
  "content_type": "application/pdf",
  "chunks_count": 25,
  "processing_status": "completed",
  "created_at": "2024-01-01T00:00:00Z",
  "metadata": {
    "pages": 10,
    "language": "en",
    "complexity_score": 0.7
  }
}
```

### Batch Upload Documents
```http
POST /api/documents/batch-upload
```

**Request (Multipart Form):**
- `files`: Array of document files (max 10)
- `chunking_strategy`: Chunking strategy for all files

**Response:**
```json
{
  "successful_uploads": [
    {
      "id": "doc1-uuid",
      "filename": "doc1.pdf",
      "chunks_count": 15
    }
  ],
  "failed_uploads": [
    {
      "filename": "invalid.txt",
      "error": "Unsupported file type"
    }
  ],
  "summary": {
    "total_files": 5,
    "successful": 4,
    "failed": 1
  }
}
```

### Get User Documents
```http
GET /api/documents
```

**Response:**
```json
[
  {
    "id": "document-uuid",
    "filename": "document.pdf",
    "size": 1024000,
    "chunks_count": 25,
    "created_at": "2024-01-01T00:00:00Z",
    "last_accessed": "2024-01-02T00:00:00Z"
  }
]
```

### Delete Document
```http
DELETE /api/documents/{document_id}
```

**Response:**
```json
{
  "success": true
}
```

## Chat and RAG

### Basic Chat (Legacy)
```http
POST /api/chat/message
```

**Request:**
```json
{
  "message": "What is machine learning?",
  "conversation_id": "conv-uuid",
  "use_chain_of_thought": false,
  "citation_mode": "inline"
}
```

**Response:**
```json
{
  "response": "Machine learning is a subset of artificial intelligence...",
  "sources": [
    {
      "document_id": "doc-uuid",
      "chunk_id": "chunk-uuid",
      "content": "relevant chunk content",
      "page_number": 5,
      "relevance_score": 0.95
    }
  ],
  "processing_time": 1.2,
  "model": "mistral",
  "conversation_id": "conv-uuid"
}
```

### Enhanced Chat
```http
POST /api/chat/enhanced
```

**Request:**
```json
{
  "message": "Explain the relationship between neural networks and deep learning",
  "conversation_id": "conv-uuid",
  "use_chain_of_thought": true,
  "citation_mode": "detailed",
  "enable_reasoning": true,
  "enable_memory": true,
  "personalization_level": 0.8,
  "max_sources": 5
}
```

**Response:**
```json
{
  "response": "Neural networks and deep learning are closely related...",
  "sources": [
    {
      "document_id": "doc-uuid",
      "chunk_id": "chunk-uuid",
      "content": "relevant content",
      "page_number": 3,
      "relevance_score": 0.92,
      "uncertainty_score": 0.15
    }
  ],
  "reasoning_steps": [
    {
      "step": 1,
      "type": "causal_reasoning",
      "description": "Identifying causal relationships",
      "result": "Neural networks are the foundation of deep learning"
    }
  ],
  "uncertainty_score": 0.12,
  "confidence_level": "high",
  "knowledge_graph_used": true,
  "memory_context_used": true,
  "personalization_applied": true,
  "processing_time": 2.1,
  "model": "mistral"
}
```

### Document Comparison
```http
POST /api/documents/compare
```

**Request:**
```json
{
  "document_ids": ["doc1-uuid", "doc2-uuid"],
  "query": "Compare the approaches to machine learning",
  "comparison_type": "detailed"
}
```

**Response:**
```json
{
  "comparison_summary": "Document 1 focuses on supervised learning while Document 2 emphasizes unsupervised approaches...",
  "similarities": [
    {
      "topic": "Neural Networks",
      "similarity_score": 0.85,
      "common_concepts": ["backpropagation", "gradient descent"]
    }
  ],
  "differences": [
    {
      "aspect": "Learning Paradigm",
      "doc1_approach": "Supervised learning focus",
      "doc2_approach": "Unsupervised learning focus"
    }
  ],
  "detailed_analysis": {
    "doc1_strengths": ["Clear examples", "Mathematical rigor"],
    "doc2_strengths": ["Practical applications", "Case studies"]
  }
}
```

## Search

### Semantic Search
```http
GET /api/search/semantic?query=machine%20learning&limit=10&enable_personalization=true
```

**Response:**
```json
{
  "results": [
    {
      "document_id": "doc-uuid",
      "chunk_id": "chunk-uuid",
      "content": "Machine learning algorithms...",
      "relevance_score": 0.95,
      "uncertainty_score": 0.1,
      "page_number": 3,
      "metadata": {
        "document_title": "AI Fundamentals",
        "section": "Introduction"
      }
    }
  ],
  "personalization_applied": true,
  "search_strategy": "adaptive_user_preference",
  "total_results": 8
}
```

## Knowledge Graph

### Get Document Knowledge Graph
```http
GET /api/knowledge-graph/{document_id}?include_relationships=true&max_depth=2&min_confidence=0.5
```

**Response:**
```json
{
  "nodes": [
    {
      "id": "entity-uuid",
      "name": "Machine Learning",
      "type": "concept",
      "importance_score": 0.9,
      "description": "A subset of artificial intelligence",
      "metadata": {
        "frequency": 15,
        "first_mention_page": 1
      }
    }
  ],
  "edges": [
    {
      "id": "rel-uuid",
      "source": "entity1-uuid",
      "target": "entity2-uuid",
      "relationship_type": "is_part_of",
      "confidence_score": 0.85,
      "context": "Machine learning is part of artificial intelligence"
    }
  ],
  "visualization": {
    "layout": "force_directed",
    "clusters": [
      {
        "id": "cluster1",
        "name": "AI Concepts",
        "nodes": ["entity1-uuid", "entity2-uuid"]
      }
    ]
  },
  "statistics": {
    "total_entities": 25,
    "total_relationships": 40,
    "confidence_distribution": {
      "high": 15,
      "medium": 20,
      "low": 5
    }
  }
}
```

## Analytics

### Get Analytics Dashboard
```http
GET /api/analytics/dashboard?time_range=7d&include_insights=true
```

**Response:**
```json
{
  "query_analytics": {
    "total_queries": 150,
    "avg_response_time": 1.8,
    "success_rate": 0.95,
    "popular_topics": ["machine learning", "neural networks", "AI ethics"]
  },
  "document_analytics": {
    "total_documents": 25,
    "most_accessed": [
      {
        "document_id": "doc-uuid",
        "title": "AI Fundamentals",
        "access_count": 45
      }
    ],
    "upload_trend": [
      {"date": "2024-01-01", "count": 3},
      {"date": "2024-01-02", "count": 5}
    ]
  },
  "knowledge_graph_stats": {
    "total_entities": 500,
    "total_relationships": 800,
    "graph_density": 0.32,
    "most_connected_entities": ["Machine Learning", "Neural Networks"]
  },
  "memory_stats": {
    "conversations_stored": 20,
    "avg_conversation_length": 8.5,
    "memory_usage_mb": 15.2
  },
  "insights": [
    {
      "type": "usage_pattern",
      "title": "Peak Usage Hours",
      "description": "Most queries occur between 9-11 AM",
      "recommendation": "Consider optimizing performance during peak hours"
    }
  ],
  "time_range": "7d",
  "generated_at": "2024-01-01T12:00:00Z"
}
```

## Advanced Features

### Memory Management
```http
GET /api/memory/conversations/{conversation_id}
POST /api/memory/conversations/{conversation_id}/compress
DELETE /api/memory/conversations/{conversation_id}
```

### User Profile
```http
GET /api/profile
PUT /api/profile
GET /api/profile/preferences
PUT /api/profile/preferences
```

### Feedback
```http
POST /api/feedback
GET /api/feedback/history
```

### Auto-tagging
```http
GET /api/documents/{document_id}/tags
POST /api/documents/{document_id}/tags
```

### Trend Analysis
```http
GET /api/analytics/trends
GET /api/analytics/document-relationships
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid authentication credentials"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error occurred"
}
```

## Rate Limiting

- **Standard endpoints**: 100 requests per minute
- **Upload endpoints**: 10 requests per minute
- **Analytics endpoints**: 20 requests per minute

## WebSocket Support

Real-time features are available via WebSocket connections:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat/{conversation_id}');
```

## SDK Examples

### Python
```python
import requests

# Authentication
response = requests.post('http://localhost:8000/api/auth/login', 
                        data={'email': 'user@example.com', 'password': 'password'})
token = response.json()['access_token']

# Headers for authenticated requests
headers = {'Authorization': f'Bearer {token}'}

# Enhanced chat
chat_response = requests.post('http://localhost:8000/api/chat/enhanced',
                             json={
                                 'message': 'What is machine learning?',
                                 'enable_reasoning': True,
                                 'enable_memory': True
                             },
                             headers=headers)
```

### JavaScript
```javascript
// Authentication
const loginResponse = await fetch('/api/auth/login', {
  method: 'POST',
  body: new FormData([
    ['email', 'user@example.com'],
    ['password', 'password']
  ])
});
const { access_token } = await loginResponse.json();

// Enhanced chat
const chatResponse = await fetch('/api/chat/enhanced', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: 'What is machine learning?',
    enable_reasoning: true,
    enable_memory: true
  })
});
```

## Monitoring and Health

### Health Check
```http
GET /
```

### Metrics
```http
GET /metrics
```

### System Status
```http
GET /api/monitoring/system-status
GET /api/monitoring/performance-metrics
```

For more detailed information about specific endpoints, refer to the interactive API documentation at `/docs` when running the server.