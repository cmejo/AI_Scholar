#!/usr/bin/env python3
"""
Real-time Knowledge Integration for RAG
Integrates live data sources, web scraping, and API feeds
"""

import asyncio
import aiohttp
import feedparser
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import hashlib
from dataclasses import dataclass
import schedule
import time
import threading

@dataclass
class KnowledgeSource:
    name: str
    source_type: str  # 'rss', 'api', 'web', 'database'
    url: str
    update_frequency: int  # minutes
    last_updated: datetime
    is_active: bool
    metadata: Dict

@dataclass
class LiveKnowledgeItem:
    source: str
    title: str
    content: str
    url: str
    published_date: datetime
    relevance_score: float
    tags: List[str]
    content_hash: str

class RealTimeKnowledgeIntegrator:
    def __init__(self):
        self.knowledge_sources = []
        self.knowledge_cache = {}
        self.update_scheduler = None
        self.is_running = False
        
        # Default sources for different domains
        self.default_sources = {
            'academic': [
                {
                    'name': 'arXiv Recent Papers',
                    'source_type': 'rss',
                    'url': 'http://export.arxiv.org/rss/cs.AI',
                    'update_frequency': 60
                },
                {
                    'name': 'Google Scholar Alerts',
                    'source_type': 'rss',
                    'url': 'https://scholar.google.com/scholar_alerts',
                    'update_frequency': 120
                }
            ],
            'business': [
                {
                    'name': 'Business News RSS',
                    'source_type': 'rss',
                    'url': 'https://feeds.bloomberg.com/markets/news.rss',
                    'update_frequency': 30
                },
                {
                    'name': 'Market Data API',
                    'source_type': 'api',
                    'url': 'https://api.marketdata.com/v1/news',
                    'update_frequency': 15
                }
            ],
            'technology': [
                {
                    'name': 'Hacker News',
                    'source_type': 'api',
                    'url': 'https://hacker-news.firebaseio.com/v0/topstories.json',
                    'update_frequency': 30
                },
                {
                    'name': 'GitHub Trending',
                    'source_type': 'api',
                    'url': 'https://api.github.com/search/repositories',
                    'update_frequency': 60
                }
            ]
        }
    
    def add_knowledge_source(self, source: KnowledgeSource):
        """Add a new knowledge source"""
        self.knowledge_sources.append(source)
        
    def setup_domain_sources(self, domain: str):
        """Setup default sources for a specific domain"""
        if domain in self.default_sources:
            for source_config in self.default_sources[domain]:
                source = KnowledgeSource(
                    name=source_config['name'],
                    source_type=source_config['source_type'],
                    url=source_config['url'],
                    update_frequency=source_config['update_frequency'],
                    last_updated=datetime.now() - timedelta(hours=1),
                    is_active=True,
                    metadata={}
                )
                self.add_knowledge_source(source)
    
    async def fetch_rss_content(self, source: KnowledgeSource) -> List[LiveKnowledgeItem]:
        """Fetch content from RSS feeds"""
        try:
            feed = feedparser.parse(source.url)
            items = []
            
            for entry in feed.entries[:10]:  # Limit to 10 most recent
                content = entry.get('summary', entry.get('description', ''))
                content_hash = hashlib.md5(content.encode()).hexdigest()
                
                # Skip if we've already processed this content
                if content_hash in self.knowledge_cache:
                    continue
                
                item = LiveKnowledgeItem(
                    source=source.name,
                    title=entry.get('title', ''),
                    content=content,
                    url=entry.get('link', ''),
                    published_date=datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now(),
                    relevance_score=0.5,  # Will be calculated later
                    tags=self._extract_tags(content),
                    content_hash=content_hash
                )
                
                items.append(item)
                self.knowledge_cache[content_hash] = item
            
            return items
            
        except Exception as e:
            print(f"Error fetching RSS from {source.name}: {e}")
            return []
    
    async def fetch_api_content(self, source: KnowledgeSource) -> List[LiveKnowledgeItem]:
        """Fetch content from API endpoints"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(source.url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_api_response(data, source)
                    else:
                        print(f"API request failed for {source.name}: {response.status}")
                        return []
        except Exception as e:
            print(f"Error fetching API data from {source.name}: {e}")
            return []
    
    async def fetch_web_content(self, source: KnowledgeSource) -> List[LiveKnowledgeItem]:
        """Fetch content from web pages"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(source.url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract main content (this would need customization per site)
                        content = self._extract_main_content(soup)
                        content_hash = hashlib.md5(content.encode()).hexdigest()
                        
                        if content_hash not in self.knowledge_cache:
                            item = LiveKnowledgeItem(
                                source=source.name,
                                title=soup.find('title').text if soup.find('title') else '',
                                content=content,
                                url=source.url,
                                published_date=datetime.now(),
                                relevance_score=0.5,
                                tags=self._extract_tags(content),
                                content_hash=content_hash
                            )
                            
                            self.knowledge_cache[content_hash] = item
                            return [item]
                        
                        return []
                    else:
                        print(f"Web request failed for {source.name}: {response.status}")
                        return []
        except Exception as e:
            print(f"Error fetching web content from {source.name}: {e}")
            return []
    
    def _parse_api_response(self, data: Dict, source: KnowledgeSource) -> List[LiveKnowledgeItem]:
        """Parse API response based on source type"""
        items = []
        
        if source.name == 'Hacker News':
            # Handle Hacker News API format
            for item_id in data[:10]:  # Top 10 stories
                item_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
                try:
                    item_response = requests.get(item_url)
                    if item_response.status_code == 200:
                        item_data = item_response.json()
                        
                        content = item_data.get('text', item_data.get('title', ''))
                        content_hash = hashlib.md5(content.encode()).hexdigest()
                        
                        if content_hash not in self.knowledge_cache:
                            live_item = LiveKnowledgeItem(
                                source=source.name,
                                title=item_data.get('title', ''),
                                content=content,
                                url=item_data.get('url', ''),
                                published_date=datetime.fromtimestamp(item_data.get('time', 0)),
                                relevance_score=0.5,
                                tags=self._extract_tags(content),
                                content_hash=content_hash
                            )
                            
                            items.append(live_item)
                            self.knowledge_cache[content_hash] = live_item
                            
                except Exception as e:
                    print(f"Error processing Hacker News item {item_id}: {e}")
                    continue
        
        elif source.name == 'GitHub Trending':
            # Handle GitHub API format
            search_params = {
                'q': 'created:>2023-01-01',
                'sort': 'stars',
                'order': 'desc'
            }
            
            # This would need proper API key and pagination
            for repo in data.get('items', [])[:10]:
                content = f"{repo.get('description', '')} {repo.get('readme', '')}"
                content_hash = hashlib.md5(content.encode()).hexdigest()
                
                if content_hash not in self.knowledge_cache:
                    live_item = LiveKnowledgeItem(
                        source=source.name,
                        title=repo.get('full_name', ''),
                        content=content,
                        url=repo.get('html_url', ''),
                        published_date=datetime.fromisoformat(repo.get('created_at', '').replace('Z', '+00:00')),
                        relevance_score=0.5,
                        tags=repo.get('topics', []),
                        content_hash=content_hash
                    )
                    
                    items.append(live_item)
                    self.knowledge_cache[content_hash] = live_item
        
        return items
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try to find main content areas
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
        
        if main_content:
            return main_content.get_text(strip=True)
        else:
            # Fallback to body text
            return soup.get_text(strip=True)[:2000]  # Limit to 2000 chars
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extract relevant tags from content"""
        # Simple keyword extraction (could be enhanced with NLP)
        import re
        
        # Common technical and academic terms
        tag_patterns = [
            r'\b(machine learning|ML|artificial intelligence|AI|deep learning)\b',
            r'\b(python|javascript|java|react|node\.js)\b',
            r'\b(research|study|analysis|paper|journal)\b',
            r'\b(blockchain|cryptocurrency|bitcoin)\b',
            r'\b(cloud|AWS|Azure|GCP)\b'
        ]
        
        tags = []
        content_lower = content.lower()
        
        for pattern in tag_patterns:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            tags.extend(matches)
        
        return list(set(tags))[:5]  # Limit to 5 tags
    
    async def update_all_sources(self):
        """Update all active knowledge sources"""
        tasks = []
        
        for source in self.knowledge_sources:
            if not source.is_active:
                continue
                
            # Check if it's time to update
            time_since_update = datetime.now() - source.last_updated
            if time_since_update.total_seconds() < source.update_frequency * 60:
                continue
            
            # Create update task based on source type
            if source.source_type == 'rss':
                task = self.fetch_rss_content(source)
            elif source.source_type == 'api':
                task = self.fetch_api_content(source)
            elif source.source_type == 'web':
                task = self.fetch_web_content(source)
            else:
                continue
            
            tasks.append(task)
        
        # Execute all tasks concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            new_items = []
            for result in results:
                if isinstance(result, list):
                    new_items.extend(result)
                elif isinstance(result, Exception):
                    print(f"Update task failed: {result}")
            
            return new_items
        
        return []
    
    def start_real_time_updates(self):
        """Start the real-time update scheduler"""
        if self.is_running:
            return
        
        self.is_running = True
        
        def run_updates():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            while self.is_running:
                try:
                    new_items = loop.run_until_complete(self.update_all_sources())
                    if new_items:
                        print(f"Updated knowledge base with {len(new_items)} new items")
                        # Here you would integrate with your RAG system
                        self._integrate_with_rag(new_items)
                    
                    time.sleep(300)  # Check every 5 minutes
                    
                except Exception as e:
                    print(f"Error in update cycle: {e}")
                    time.sleep(60)  # Wait 1 minute before retrying
        
        # Start update thread
        self.update_thread = threading.Thread(target=run_updates, daemon=True)
        self.update_thread.start()
    
    def stop_real_time_updates(self):
        """Stop the real-time update scheduler"""
        self.is_running = False
    
    def _integrate_with_rag(self, new_items: List[LiveKnowledgeItem]):
        """Integrate new knowledge items with the RAG system"""
        # This would integrate with your existing RAG service
        for item in new_items:
            # Calculate relevance score based on current context
            item.relevance_score = self._calculate_relevance_score(item)
            
            # Add to vector database
            # rag_service.add_document(item.content, item.metadata)
            
            print(f"Added to RAG: {item.title[:50]}... (relevance: {item.relevance_score:.2f})")
    
    def _calculate_relevance_score(self, item: LiveKnowledgeItem) -> float:
        """Calculate relevance score for a knowledge item"""
        score = 0.5  # Base score
        
        # Recency bonus
        age_hours = (datetime.now() - item.published_date).total_seconds() / 3600
        if age_hours < 24:
            score += 0.3
        elif age_hours < 168:  # 1 week
            score += 0.1
        
        # Tag relevance bonus
        if item.tags:
            score += min(len(item.tags) * 0.05, 0.2)
        
        # Content length bonus (longer content often more valuable)
        if len(item.content) > 500:
            score += 0.1
        
        return min(score, 1.0)
    
    def search_live_knowledge(self, query: str, max_results: int = 5) -> List[LiveKnowledgeItem]:
        """Search through live knowledge items"""
        query_lower = query.lower()
        scored_items = []
        
        for item in self.knowledge_cache.values():
            score = 0
            
            # Title matching
            if query_lower in item.title.lower():
                score += 0.5
            
            # Content matching
            if query_lower in item.content.lower():
                score += 0.3
            
            # Tag matching
            for tag in item.tags:
                if query_lower in tag.lower():
                    score += 0.2
            
            if score > 0:
                scored_items.append((item, score))
        
        # Sort by score and return top results
        scored_items.sort(key=lambda x: x[1], reverse=True)
        return [item for item, score in scored_items[:max_results]]
    
    def get_trending_topics(self, time_window_hours: int = 24) -> List[Dict]:
        """Get trending topics from recent knowledge items"""
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        recent_items = [
            item for item in self.knowledge_cache.values()
            if item.published_date > cutoff_time
        ]
        
        # Count tag frequencies
        tag_counts = {}
        for item in recent_items:
            for tag in item.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Sort by frequency
        trending = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {
                'topic': tag,
                'mentions': count,
                'trend_score': count / len(recent_items) if recent_items else 0
            }
            for tag, count in trending[:10]
        ]

# Usage example
async def implement_realtime_knowledge():
    """Example implementation of real-time knowledge integration"""
    integrator = RealTimeKnowledgeIntegrator()
    
    # Setup for academic domain
    integrator.setup_domain_sources('academic')
    integrator.setup_domain_sources('technology')
    
    # Add custom source
    custom_source = KnowledgeSource(
        name='Custom Research Feed',
        source_type='rss',
        url='https://example.com/research-feed.xml',
        update_frequency=30,
        last_updated=datetime.now() - timedelta(hours=1),
        is_active=True,
        metadata={'domain': 'research', 'quality': 'high'}
    )
    integrator.add_knowledge_source(custom_source)
    
    # Start real-time updates
    integrator.start_real_time_updates()
    
    # Example search
    await asyncio.sleep(2)  # Wait for some updates
    results = integrator.search_live_knowledge("machine learning")
    trending = integrator.get_trending_topics()
    
    return {
        'sources_count': len(integrator.knowledge_sources),
        'cached_items': len(integrator.knowledge_cache),
        'search_results': len(results),
        'trending_topics': trending
    }

if __name__ == "__main__":
    # Run the example
    result = asyncio.run(implement_realtime_knowledge())
    print(json.dumps(result, indent=2))