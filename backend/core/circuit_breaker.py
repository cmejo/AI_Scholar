"""
Circuit Breaker Pattern Implementation for AI Scholar
Provides resilience and fault tolerance for external service calls
"""

import asyncio
import time
from enum import Enum
from typing import Callable, Any, Optional, Dict, List
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls are failing
    HALF_OPEN = "half_open"  # Testing if service is back

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5          # Number of failures before opening
    success_threshold: int = 3          # Number of successes to close from half-open
    timeout: int = 60                   # Seconds to wait before trying half-open
    reset_timeout: int = 300            # Seconds to reset failure count
    expected_exception: type = Exception # Exception type that triggers circuit

@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    circuit_opened_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0

class CircuitBreaker:
    """Circuit breaker implementation with async support"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self.last_failure_time: Optional[float] = None
        self.lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self.lock:
            # Check if we should attempt the call
            if not self._should_attempt_call():
                raise CircuitBreakerOpenException(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Last failure: {self.last_failure_time}"
                )
        
        # Record the call attempt
        self.stats.total_calls += 1
        
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Record success
            await self._record_success()
            return result
            
        except self.config.expected_exception as e:
            # Record failure
            await self._record_failure()
            raise
        except Exception as e:
            # Unexpected exception - don't count as circuit breaker failure
            logger.warning(f"Unexpected exception in circuit breaker '{self.name}': {e}")
            raise
    
    def _should_attempt_call(self) -> bool:
        """Determine if we should attempt the call based on current state"""
        current_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            return True
        
        elif self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if (self.last_failure_time and 
                current_time - self.last_failure_time >= self.config.timeout):
                self.state = CircuitState.HALF_OPEN
                self.stats.consecutive_successes = 0
                logger.info(f"Circuit breaker '{self.name}' moved to HALF_OPEN")
                return True
            return False
        
        elif self.state == CircuitState.HALF_OPEN:
            return True
        
        return False
    
    async def _record_success(self):
        """Record a successful call"""
        async with self.lock:
            self.stats.successful_calls += 1
            self.stats.consecutive_successes += 1
            self.stats.consecutive_failures = 0
            self.stats.last_success_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                if self.stats.consecutive_successes >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    logger.info(f"Circuit breaker '{self.name}' moved to CLOSED")
    
    async def _record_failure(self):
        """Record a failed call"""
        async with self.lock:
            self.stats.failed_calls += 1
            self.stats.consecutive_failures += 1
            self.stats.consecutive_successes = 0
            self.last_failure_time = time.time()
            self.stats.last_failure_time = self.last_failure_time
            
            if (self.state == CircuitState.CLOSED and 
                self.stats.consecutive_failures >= self.config.failure_threshold):
                
                self.state = CircuitState.OPEN
                self.stats.circuit_opened_count += 1
                logger.warning(f"Circuit breaker '{self.name}' moved to OPEN after {self.stats.consecutive_failures} failures")
            
            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker '{self.name}' moved back to OPEN from HALF_OPEN")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        success_rate = (self.stats.successful_calls / max(self.stats.total_calls, 1)) * 100
        
        return {
            "name": self.name,
            "state": self.state.value,
            "total_calls": self.stats.total_calls,
            "successful_calls": self.stats.successful_calls,
            "failed_calls": self.stats.failed_calls,
            "success_rate": round(success_rate, 2),
            "consecutive_failures": self.stats.consecutive_failures,
            "consecutive_successes": self.stats.consecutive_successes,
            "circuit_opened_count": self.stats.circuit_opened_count,
            "last_failure_time": self.stats.last_failure_time,
            "last_success_time": self.stats.last_success_time
        }
    
    async def reset(self):
        """Manually reset the circuit breaker"""
        async with self.lock:
            self.state = CircuitState.CLOSED
            self.stats.consecutive_failures = 0
            self.stats.consecutive_successes = 0
            self.last_failure_time = None
            logger.info(f"Circuit breaker '{self.name}' manually reset")

class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class CircuitBreakerManager:
    """Manages multiple circuit breakers"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def get_circuit_breaker(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Get or create a circuit breaker"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, config)
        return self.circuit_breakers[name]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        return {name: cb.get_stats() for name, cb in self.circuit_breakers.items()}
    
    async def reset_all(self):
        """Reset all circuit breakers"""
        for cb in self.circuit_breakers.values():
            await cb.reset()

# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()

class GracefulDegradation:
    """Implements graceful degradation patterns"""
    
    def __init__(self):
        self.fallback_strategies: Dict[str, List[Callable]] = {}
    
    def register_fallback(self, service_name: str, fallback_func: Callable, priority: int = 0):
        """Register a fallback function for a service"""
        if service_name not in self.fallback_strategies:
            self.fallback_strategies[service_name] = []
        
        self.fallback_strategies[service_name].append((priority, fallback_func))
        # Sort by priority (higher priority first)
        self.fallback_strategies[service_name].sort(key=lambda x: x[0], reverse=True)
    
    async def call_with_fallback(self, service_name: str, primary_func: Callable, *args, **kwargs) -> Any:
        """Call primary function with fallback strategies"""
        
        # Get circuit breaker for this service
        cb = circuit_breaker_manager.get_circuit_breaker(
            service_name,
            CircuitBreakerConfig(failure_threshold=3, timeout=30)
        )
        
        # Try primary function with circuit breaker
        try:
            return await cb.call(primary_func, *args, **kwargs)
        
        except (CircuitBreakerOpenException, Exception) as e:
            logger.warning(f"Primary service '{service_name}' failed: {e}")
            
            # Try fallback strategies
            if service_name in self.fallback_strategies:
                for priority, fallback_func in self.fallback_strategies[service_name]:
                    try:
                        logger.info(f"Trying fallback for '{service_name}' with priority {priority}")
                        
                        if asyncio.iscoroutinefunction(fallback_func):
                            return await fallback_func(*args, **kwargs)
                        else:
                            return fallback_func(*args, **kwargs)
                    
                    except Exception as fallback_error:
                        logger.warning(f"Fallback failed for '{service_name}': {fallback_error}")
                        continue
            
            # If all fallbacks fail, raise the original exception
            raise e

# Global graceful degradation instance
graceful_degradation = GracefulDegradation()

# AI Service Resilience Implementation
class AIServiceResilience:
    """Resilience patterns specifically for AI services"""
    
    def __init__(self):
        self.degradation = graceful_degradation
        self._setup_ai_fallbacks()
    
    def _setup_ai_fallbacks(self):
        """Set up fallback strategies for AI services"""
        
        # OpenAI fallbacks
        self.degradation.register_fallback("openai_embeddings", self._fallback_local_embeddings, priority=1)
        self.degradation.register_fallback("openai_chat", self._fallback_simple_response, priority=1)
        
        # RAG fallbacks
        self.degradation.register_fallback("rag_service", self._fallback_keyword_search, priority=1)
        
        # Document processing fallbacks
        self.degradation.register_fallback("document_analysis", self._fallback_basic_analysis, priority=1)
    
    async def get_ai_response_with_fallback(self, query: str, context: str = "") -> Dict[str, Any]:
        """Get AI response with multiple fallback strategies"""
        
        async def primary_ai_service(query: str, context: str = "") -> Dict[str, Any]:
            # This would be your primary AI service call
            # Simulate potential failure
            import random
            if random.random() < 0.1:  # 10% failure rate for testing
                raise Exception("AI service temporarily unavailable")
            
            return {
                "answer": f"AI response to: {query}",
                "confidence": 0.9,
                "source": "primary_ai",
                "context_used": bool(context)
            }
        
        return await self.degradation.call_with_fallback(
            "ai_chat_service", 
            primary_ai_service, 
            query, 
            context
        )
    
    async def _fallback_local_embeddings(self, text: str) -> List[float]:
        """Fallback to local embedding generation"""
        logger.info("Using local embeddings fallback")
        # Simple hash-based embeddings as fallback
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to 384-dimensional vector
        embeddings = []
        for i in range(384):
            byte_index = i % len(hash_bytes)
            embeddings.append(float(hash_bytes[byte_index]) / 255.0)
        
        return embeddings
    
    async def _fallback_simple_response(self, query: str, context: str = "") -> Dict[str, Any]:
        """Simple rule-based response fallback"""
        logger.info("Using simple response fallback")
        
        # Basic keyword matching
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["what", "define", "explain"]):
            answer = f"Based on available information, here's what I can tell you about your query: {query}"
        elif any(word in query_lower for word in ["how", "steps", "process"]):
            answer = f"Here's a general approach to: {query}"
        elif any(word in query_lower for word in ["why", "reason", "because"]):
            answer = f"There are several reasons related to: {query}"
        else:
            answer = f"I understand you're asking about: {query}. Let me provide some general information."
        
        return {
            "answer": answer,
            "confidence": 0.3,
            "source": "fallback_simple",
            "context_used": bool(context)
        }
    
    async def _fallback_keyword_search(self, query: str, documents: List[Dict] = None) -> Dict[str, Any]:
        """Keyword-based search fallback"""
        logger.info("Using keyword search fallback")
        
        documents = documents or []
        query_words = set(query.lower().split())
        
        # Simple keyword matching
        matches = []
        for doc in documents:
            content = doc.get("content", "").lower()
            title = doc.get("title", "").lower()
            
            # Count keyword matches
            content_matches = sum(1 for word in query_words if word in content)
            title_matches = sum(1 for word in query_words if word in title) * 2  # Title matches worth more
            
            total_score = content_matches + title_matches
            if total_score > 0:
                matches.append({
                    "document": doc,
                    "score": total_score,
                    "matches": content_matches + title_matches
                })
        
        # Sort by score
        matches.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "results": matches[:5],  # Top 5 matches
            "total_matches": len(matches),
            "source": "fallback_keyword_search",
            "confidence": 0.4 if matches else 0.1
        }
    
    async def _fallback_basic_analysis(self, document: Dict) -> Dict[str, Any]:
        """Basic document analysis fallback"""
        logger.info("Using basic analysis fallback")
        
        content = document.get("content", "")
        words = content.split()
        
        return {
            "word_count": len(words),
            "character_count": len(content),
            "estimated_reading_time": len(words) / 200,  # Assume 200 WPM
            "basic_stats": {
                "sentences": content.count('.') + content.count('!') + content.count('?'),
                "paragraphs": content.count('\n\n') + 1
            },
            "source": "fallback_basic_analysis",
            "confidence": 0.6
        }

# Global AI service resilience
ai_service_resilience = AIServiceResilience()

# Convenience functions
async def resilient_ai_call(service_name: str, func: Callable, *args, **kwargs) -> Any:
    """Make a resilient AI service call"""
    return await graceful_degradation.call_with_fallback(service_name, func, *args, **kwargs)

def circuit_breaker(name: str, config: CircuitBreakerConfig = None):
    """Decorator for circuit breaker protection"""
    def decorator(func: Callable) -> Callable:
        cb = circuit_breaker_manager.get_circuit_breaker(name, config)
        
        async def wrapper(*args, **kwargs):
            return await cb.call(func, *args, **kwargs)
        
        return wrapper
    return decorator

# Usage examples
if __name__ == "__main__":
    async def test_circuit_breaker():
        # Test circuit breaker
        @circuit_breaker("test_service", CircuitBreakerConfig(failure_threshold=2, timeout=5))
        async def unreliable_service():
            import random
            if random.random() < 0.7:  # 70% failure rate
                raise Exception("Service failed")
            return "Success!"
        
        # Test multiple calls
        for i in range(10):
            try:
                result = await unreliable_service()
                print(f"Call {i+1}: {result}")
            except Exception as e:
                print(f"Call {i+1}: Failed - {e}")
            
            await asyncio.sleep(0.5)
        
        # Print circuit breaker stats
        stats = circuit_breaker_manager.get_all_stats()
        print(f"Circuit Breaker Stats: {stats}")
        
        # Test AI service resilience
        response = await ai_service_resilience.get_ai_response_with_fallback(
            "What is machine learning?",
            "Context about ML"
        )
        print(f"AI Response: {response}")
    
    # Run test
    asyncio.run(test_circuit_breaker())