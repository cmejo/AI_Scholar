# 🚀 AI Scholar API - Getting Started

## Welcome to the AI Scholar API

The AI Scholar API provides programmatic access to all platform features, enabling developers to integrate AI-powered research capabilities into their applications, build custom tools, and automate research workflows.

## 🔑 **Authentication**

### **API Key Setup**

1. **Generate API Key**
   ```bash
   # Via AI Scholar CLI
   ai-scholar auth generate-key --name "My Research App" --scope "research,analysis"
   
   # Returns: sk_live_1234567890abcdef...
   ```

2. **Environment Configuration**
   ```bash
   # Set environment variable
   export AI_SCHOLAR_API_KEY="sk_live_1234567890abcdef..."
   
   # Or create .env file
   echo "AI_SCHOLAR_API_KEY=sk_live_1234567890abcdef..." > .env
   ```

3. **Authentication Headers**
   ```http
   Authorization: Bearer sk_live_1234567890abcdef...
   Content-Type: application/json
   ```

### **SDK Installation**

```bash
# Python SDK
pip install ai-scholar-sdk

# Node.js SDK  
npm install @ai-scholar/sdk

# R SDK
install.packages("aischolar")

# Julia SDK
using Pkg; Pkg.add("AIScholar")
```

## 📚 **Quick Start Examples**

### **Python SDK**

```python
from ai_scholar import AIScholar

# Initialize client
client = AIScholar(api_key="your_api_key_here")

# Conduct literature review
review = await client.research.literature_review(
    topic="quantum machine learning",
    depth=3,
    languages=["en", "zh", "de"],
    max_papers=500
)

print(f"Found {len(review.papers)} papers")
print(f"Key findings: {review.key_findings}")
print(f"Research gaps: {review.research_gaps}")

# Generate research proposal
proposal = await client.research.generate_proposal(
    interests=["quantum computing", "healthcare"],
    career_level="postdoc",
    timeline="2_years",
    budget_range="100k-500k"
)

print(f"Proposal: {proposal.title}")
print(f"Novelty score: {proposal.novelty_score}")
print(f"Feasibility: {proposal.feasibility_score}")

# Translate research paper
translation = await client.translate.paper(
    file_path="paper.pdf",
    source_language="zh",
    target_language="en",
    preserve_formatting=True
)

print(f"Translation completed: {translation.output_path}")
print(f"Quality score: {translation.quality_score}")
```

### **Node.js SDK**

```javascript
import { AIScholar } from '@ai-scholar/sdk';

// Initialize client
const client = new AIScholar({
  apiKey: process.env.AI_SCHOLAR_API_KEY
});

// Conduct research analysis
const analysis = await client.research.analyzeText({
  text: "Your research text here...",
  analysisTypes: ['sentiment', 'entities', 'topics', 'citations'],
  includeVisualization: true
});

console.log('Analysis results:', analysis.results);
console.log('Detected topics:', analysis.topics);
console.log('Citation network:', analysis.citations);

// Real-time collaboration
const collaboration = await client.collaboration.createSession({
  projectId: 'quantum-ml-2024',
  participants: ['user1@example.com', 'user2@example.com'],
  features: ['real_time_editing', 'voice_chat', 'screen_sharing']
});

console.log('Collaboration session:', collaboration.sessionId);
console.log('Join URL:', collaboration.joinUrl);
```

### **R SDK**

```r
library(aischolar)

# Initialize client
client <- AIScholar$new(api_key = Sys.getenv("AI_SCHOLAR_API_KEY"))

# Analyze research data
analysis <- client$analyze_data(
  data = research_dataset,
  analysis_type = "statistical",
  include_visualization = TRUE,
  export_format = "pdf"
)

print(paste("Analysis completed:", analysis$status))
print(paste("P-values:", analysis$p_values))
print(paste("Effect sizes:", analysis$effect_sizes))

# Generate research insights
insights <- client$generate_insights(
  data = analysis$results,
  research_question = "What factors predict treatment success?",
  methodology = "regression_analysis"
)

print(insights$key_findings)
print(insights$recommendations)
```

## 🔍 **Core API Endpoints**

### **Research Assistant API**

```http
POST /api/v1/research/literature-review
Content-Type: application/json
Authorization: Bearer {api_key}

{
  "topic": "quantum machine learning",
  "depth": 3,
  "languages": ["en", "zh", "de"],
  "time_range": {
    "start": "2020-01-01",
    "end": "2024-12-31"
  },
  "max_papers": 500,
  "include_analysis": true
}
```

**Response:**
```json
{
  "review_id": "rev_1234567890",
  "status": "completed",
  "papers_analyzed": 347,
  "processing_time": "00:15:23",
  "key_findings": [
    {
      "finding": "Quantum advantage demonstrated in specific ML tasks",
      "confidence": 0.92,
      "supporting_papers": 23
    }
  ],
  "research_gaps": [
    {
      "gap": "Limited real-world applications",
      "priority": "high",
      "potential_impact": 0.87
    }
  ],
  "download_url": "https://api.aischolar.com/downloads/rev_1234567890.pdf"
}
```

### **Translation API**

```http
POST /api/v1/translate/paper
Content-Type: multipart/form-data
Authorization: Bearer {api_key}

file: paper.pdf
source_language: zh
target_language: en
preserve_formatting: true
include_cultural_context: true
```

**Response:**
```json
{
  "translation_id": "trans_9876543210",
  "status": "completed",
  "quality_score": 0.96,
  "processing_time": "00:02:45",
  "cultural_adaptations": [
    {
      "original_concept": "集体主义研究方法",
      "adapted_translation": "collectivist research methodology",
      "cultural_note": "Emphasizes community-based research approaches common in East Asian academic culture"
    }
  ],
  "download_url": "https://api.aischolar.com/downloads/trans_9876543210.pdf"
}
```

### **Blockchain Verification API**

```http
POST /api/v1/blockchain/verify-research
Content-Type: application/json
Authorization: Bearer {api_key}

{
  "research_id": "research_abc123",
  "verification_type": "authorship",
  "digital_signature": "0x7f9a2b8c3d4e5f6a...",
  "metadata": {
    "title": "Quantum ML for Drug Discovery",
    "authors": ["Dr. Sarah Chen", "Dr. James Wilson"],
    "institution": "MIT",
    "timestamp": "2024-08-15T14:30:00Z"
  }
}
```

**Response:**
```json
{
  "verification_id": "verify_def456",
  "status": "verified",
  "blockchain_hash": "0x8a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c",
  "verification_score": 1.0,
  "timestamp": "2024-08-15T14:30:15Z",
  "immutable_record_url": "https://blockchain.aischolar.com/verify/verify_def456"
}
```

## 🔧 **Advanced Features**

### **Webhook Integration**

```python
from flask import Flask, request
import hmac
import hashlib

app = Flask(__name__)

@app.route('/webhook/ai-scholar', methods=['POST'])
def handle_webhook():
    # Verify webhook signature
    signature = request.headers.get('X-AI-Scholar-Signature')
    payload = request.get_data()
    
    expected_signature = hmac.new(
        webhook_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        return 'Invalid signature', 401
    
    # Process webhook event
    event = request.json
    
    if event['type'] == 'research.analysis.completed':
        analysis_id = event['data']['analysis_id']
        results = event['data']['results']
        
        # Handle completed analysis
        process_analysis_results(analysis_id, results)
    
    elif event['type'] == 'collaboration.session.started':
        session_id = event['data']['session_id']
        participants = event['data']['participants']
        
        # Handle new collaboration session
        notify_participants(session_id, participants)
    
    return 'OK', 200
```

### **Streaming API**

```python
import asyncio
from ai_scholar import AIScholar

async def stream_analysis():
    client = AIScholar(api_key="your_api_key")
    
    # Stream real-time analysis results
    async for result in client.research.stream_analysis(
        topic="quantum computing",
        analysis_types=["trend_detection", "gap_analysis"],
        update_interval=30  # seconds
    ):
        print(f"New insight: {result.insight}")
        print(f"Confidence: {result.confidence}")
        print(f"Timestamp: {result.timestamp}")
        
        # Process real-time results
        await process_insight(result)

# Run streaming analysis
asyncio.run(stream_analysis())
```

### **Batch Processing**

```python
from ai_scholar import AIScholar
import asyncio

async def batch_process_papers():
    client = AIScholar(api_key="your_api_key")
    
    # Prepare batch of papers for analysis
    papers = [
        {"id": "paper1", "url": "https://arxiv.org/abs/2401.12345"},
        {"id": "paper2", "url": "https://arxiv.org/abs/2401.12346"},
        {"id": "paper3", "url": "https://arxiv.org/abs/2401.12347"},
        # ... up to 100 papers per batch
    ]
    
    # Submit batch job
    batch_job = await client.research.submit_batch_analysis(
        papers=papers,
        analysis_types=["summary", "methodology", "results", "citations"],
        priority="high",
        callback_url="https://your-app.com/webhook/batch-complete"
    )
    
    print(f"Batch job submitted: {batch_job.job_id}")
    print(f"Estimated completion: {batch_job.estimated_completion}")
    
    # Monitor batch progress
    while not batch_job.is_complete():
        status = await client.research.get_batch_status(batch_job.job_id)
        print(f"Progress: {status.progress}% ({status.completed}/{status.total})")
        await asyncio.sleep(30)
    
    # Retrieve results
    results = await client.research.get_batch_results(batch_job.job_id)
    return results
```

## 📊 **Rate Limits and Quotas**

### **API Rate Limits**

```
Tier: Research Pro
├─ Requests per minute: 1,000
├─ Requests per hour: 50,000  
├─ Requests per day: 1,000,000
└─ Concurrent connections: 100

Tier: Institution
├─ Requests per minute: 5,000
├─ Requests per hour: 250,000
├─ Requests per day: 5,000,000
└─ Concurrent connections: 500

Tier: Enterprise
├─ Requests per minute: Unlimited
├─ Requests per hour: Unlimited
├─ Requests per day: Unlimited
└─ Concurrent connections: Unlimited
```

### **Usage Monitoring**

```python
from ai_scholar import AIScholar

client = AIScholar(api_key="your_api_key")

# Check current usage
usage = await client.account.get_usage()

print(f"Requests this month: {usage.requests_current}/{usage.requests_limit}")
print(f"Analysis minutes used: {usage.analysis_minutes}/{usage.analysis_limit}")
print(f"Storage used: {usage.storage_gb}/{usage.storage_limit} GB")
print(f"Rate limit remaining: {usage.rate_limit_remaining}")

# Set up usage alerts
await client.account.set_usage_alert(
    threshold=0.8,  # Alert at 80% usage
    notification_email="admin@yourorg.com",
    webhook_url="https://your-app.com/webhook/usage-alert"
)
```

## 🔒 **Security Best Practices**

### **API Key Management**

```python
import os
from cryptography.fernet import Fernet

class SecureAPIKeyManager:
    def __init__(self):
        # Generate or load encryption key
        self.key = os.environ.get('ENCRYPTION_KEY') or Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API key for secure storage"""
        return self.cipher.encrypt(api_key.encode()).decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt API key for use"""
        return self.cipher.decrypt(encrypted_key.encode()).decode()
    
    def rotate_api_key(self, old_key: str) -> str:
        """Rotate API key securely"""
        from ai_scholar import AIScholar
        
        client = AIScholar(api_key=old_key)
        new_key = client.auth.rotate_key()
        
        # Update all configurations with new key
        self.update_configurations(new_key)
        
        return new_key

# Usage
key_manager = SecureAPIKeyManager()
encrypted_key = key_manager.encrypt_api_key("sk_live_1234567890abcdef...")
```

### **Request Signing**

```python
import hmac
import hashlib
import time
import json

def sign_request(method: str, url: str, body: dict, api_secret: str) -> str:
    """Generate request signature for enhanced security"""
    
    timestamp = str(int(time.time()))
    
    # Create signature payload
    payload = f"{method}\n{url}\n{timestamp}\n{json.dumps(body, sort_keys=True)}"
    
    # Generate HMAC signature
    signature = hmac.new(
        api_secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"{timestamp}.{signature}"

# Usage in requests
headers = {
    'Authorization': f'Bearer {api_key}',
    'X-AI-Scholar-Signature': sign_request('POST', '/api/v1/research/analyze', request_body, api_secret),
    'Content-Type': 'application/json'
}
```

## 🚀 **Performance Optimization**

### **Connection Pooling**

```python
import aiohttp
import asyncio
from ai_scholar import AIScholar

class OptimizedAIScholarClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = None
    
    async def __aenter__(self):
        # Create connection pool
        connector = aiohttp.TCPConnector(
            limit=100,  # Total connection pool size
            limit_per_host=30,  # Connections per host
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
            keepalive_timeout=30
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=300),
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def analyze_papers_concurrent(self, papers: list, max_concurrent: int = 10):
        """Analyze multiple papers concurrently with connection pooling"""
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_single_paper(paper):
            async with semaphore:
                async with self.session.post(
                    'https://api.aischolar.com/v1/research/analyze-paper',
                    json={'paper_url': paper['url'], 'analysis_types': ['summary', 'methodology']}
                ) as response:
                    return await response.json()
        
        # Execute concurrent analysis
        tasks = [analyze_single_paper(paper) for paper in papers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return results

# Usage
async def main():
    papers = [{'url': f'https://arxiv.org/abs/240{i}.12345'} for i in range(1, 21)]
    
    async with OptimizedAIScholarClient(api_key="your_key") as client:
        results = await client.analyze_papers_concurrent(papers, max_concurrent=5)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Paper {i} failed: {result}")
            else:
                print(f"Paper {i} analyzed: {result['summary'][:100]}...")

asyncio.run(main())
```

### **Caching Strategy**

```python
import redis
import json
import hashlib
from datetime import timedelta

class AIScholarCache:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url)
        self.default_ttl = timedelta(hours=24)
    
    def _generate_cache_key(self, endpoint: str, params: dict) -> str:
        """Generate consistent cache key"""
        key_data = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        return f"ai_scholar:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    async def get_cached_result(self, endpoint: str, params: dict):
        """Retrieve cached result if available"""
        cache_key = self._generate_cache_key(endpoint, params)
        cached_data = self.redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        return None
    
    async def cache_result(self, endpoint: str, params: dict, result: dict, ttl: timedelta = None):
        """Cache API result"""
        cache_key = self._generate_cache_key(endpoint, params)
        ttl = ttl or self.default_ttl
        
        self.redis_client.setex(
            cache_key,
            int(ttl.total_seconds()),
            json.dumps(result)
        )
    
    async def cached_api_call(self, client, endpoint: str, params: dict, ttl: timedelta = None):
        """Make API call with caching"""
        
        # Check cache first
        cached_result = await self.get_cached_result(endpoint, params)
        if cached_result:
            return cached_result
        
        # Make API call
        if endpoint == "literature_review":
            result = await client.research.literature_review(**params)
        elif endpoint == "analyze_paper":
            result = await client.research.analyze_paper(**params)
        else:
            raise ValueError(f"Unknown endpoint: {endpoint}")
        
        # Cache result
        await self.cache_result(endpoint, params, result.dict(), ttl)
        
        return result

# Usage
cache = AIScholarCache()
client = AIScholar(api_key="your_key")

# Cached literature review
result = await cache.cached_api_call(
    client,
    "literature_review",
    {"topic": "quantum machine learning", "depth": 3},
    ttl=timedelta(hours=12)
)
```

## 📈 **Monitoring and Analytics**

### **API Usage Analytics**

```python
import logging
import time
from functools import wraps
from ai_scholar import AIScholar

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_scholar_api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('ai_scholar_api')

def monitor_api_calls(func):
    """Decorator to monitor API call performance"""
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            
            # Log successful call
            duration = time.time() - start_time
            logger.info(f"API call successful: {func.__name__} - Duration: {duration:.2f}s")
            
            return result
            
        except Exception as e:
            # Log failed call
            duration = time.time() - start_time
            logger.error(f"API call failed: {func.__name__} - Duration: {duration:.2f}s - Error: {str(e)}")
            raise
    
    return wrapper

class MonitoredAIScholarClient:
    def __init__(self, api_key: str):
        self.client = AIScholar(api_key=api_key)
    
    @monitor_api_calls
    async def literature_review(self, **kwargs):
        return await self.client.research.literature_review(**kwargs)
    
    @monitor_api_calls
    async def analyze_paper(self, **kwargs):
        return await self.client.research.analyze_paper(**kwargs)
    
    @monitor_api_calls
    async def translate_paper(self, **kwargs):
        return await self.client.translate.paper(**kwargs)

# Usage
client = MonitoredAIScholarClient(api_key="your_key")

# All calls will be automatically monitored and logged
review = await client.literature_review(
    topic="quantum computing",
    depth=2
)
```

### **Health Checks and Circuit Breaker**

```python
import asyncio
import aiohttp
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout)
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

class ResilientAIScholarClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30)
    
    async def _make_api_call(self, endpoint: str, **kwargs):
        """Make API call with error handling"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.aischolar.com/v1/{endpoint}",
                headers={'Authorization': f'Bearer {self.api_key}'},
                json=kwargs,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                if response.status >= 400:
                    raise aiohttp.ClientError(f"API error: {response.status}")
                
                return await response.json()
    
    async def literature_review(self, **kwargs):
        """Resilient literature review with circuit breaker"""
        return await self.circuit_breaker.call(
            self._make_api_call,
            "research/literature-review",
            **kwargs
        )

# Usage
client = ResilientAIScholarClient(api_key="your_key")

try:
    review = await client.literature_review(topic="quantum computing")
    print("Review completed successfully")
except Exception as e:
    print(f"Review failed: {e}")
```

---

## 🎉 **Next Steps**

Now that you understand the AI Scholar API basics, explore these advanced topics:

1. **[API Reference](api-reference.md)** - Complete endpoint documentation
2. **[SDK Documentation](sdk-documentation.md)** - Language-specific SDK guides  
3. **[Integration Examples](integration-examples.md)** - Real-world integration patterns
4. **[Webhook Guide](webhook-guide.md)** - Event-driven integrations
5. **[Performance Guide](performance-guide.md)** - Optimization best practices

**Ready to build amazing research applications? Start coding with the AI Scholar API today!**